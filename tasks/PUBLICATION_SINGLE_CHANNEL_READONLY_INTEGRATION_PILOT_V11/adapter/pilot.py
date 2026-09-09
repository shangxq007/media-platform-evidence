"""Owner-local Postiz v2.23.0 read pilot. Python 3.11+ stdlib; no product backend.
The config is owner-controlled, never accepted from a caller. No request/body logs.
"""
import argparse
import asyncio
import hmac
import ipaddress
import json
import os
import re
import ssl
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlencode, parse_qs

CONTRACT = 'postiz-owner-local-v1'
COMMIT = '1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9'
ID = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,179}$')
SCOPE_KEYS = {'principalId','tenantId','sessionId','workspaceId','projectId','sourceId'}

def identifier(value):
    if not isinstance(value,str) or not ID.fullmatch(value): raise Failure('INVALID_CONTRACT',422)
    return value

def instant(value):
    if not isinstance(value,str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?Z',value): raise Failure('INVALID_TIME',422)
    try: return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    except ValueError: raise Failure('INVALID_TIME',422) from None

def safe_text(value, secrets=()):
    if not isinstance(value,str) or len(value)>4000 or any(s and s in value for s in secrets): raise Failure('INVALID_CONTRACT',422)
    return value

class Failure(Exception):
    def __init__(self, code, status=502): self.code,self.status=code,status

@dataclass(frozen=True)
class Config:
    base: str
    approved_ip: str
    version: str
    binding: dict
    account_id: str
    start: str
    end: str
    organization_read_consent: bool = False
    synthetic: bool = False
    content_allowed: bool = False
    max_bytes: int = 1048576
    timeout: float = 5
    max_reads: int = 60
    ttl: int = 1800
    max_records: int = 200

    def validate(self):
        u = urlsplit(self.base)
        if self.version != 'v2.23.0' or not self.organization_read_consent: raise Failure('NOT_AUTHORIZED',403)
        if u.username or u.password or u.query or u.fragment or u.path not in ['/public/v1','/api/public/v1']: raise Failure('INVALID_DESTINATION',403)
        ip = ipaddress.ip_address(self.approved_ip)
        if self.synthetic:
            if u.scheme!='http' or u.hostname!='127.0.0.1' or str(ip)!='127.0.0.1': raise Failure('INVALID_DESTINATION',403)
        elif u.scheme!='https' or not u.hostname: raise Failure('INVALID_DESTINATION',403)
        if set(self.binding)!={'scope','ownerId'} or set(self.binding['scope'])!=SCOPE_KEYS: raise Failure('INVALID_BINDING',403)
        identifier(self.binding['ownerId']); identifier(self.account_id)
        for k,v in self.binding['scope'].items():
            if k!='tenantId' or v is not None: identifier(v)
        if not 0 < instant(self.end)-instant(self.start) <= 31*86400: raise Failure('INVALID_WINDOW',422)
        if not (1024<=self.max_bytes<=1048576 and 0<self.timeout<=10 and 1<=self.max_reads<=60 and 1<=self.ttl<=3600 and 1<=self.max_records<=200): raise Failure('INVALID_LIMITS',422)
        return self

class Pilot:
    def __init__(self, config, local_token, upstream_key):
        self.config=config.validate()
        if not local_token or not upstream_key or local_token==upstream_key or any('\r' in x or '\n' in x for x in [local_token,upstream_key]): raise Failure('INVALID_CREDENTIAL_CONFIGURATION',403)
        self.local_token,self.upstream_key=local_token,upstream_key
        self.revision='access-'+uuid.uuid4().hex
        self.expires=time.time()+config.ttl
        self.reads=0; self.busy=False

    def access(self):
        return dict(revision=self.revision, authority='owner-local-single-user', expiresAt=datetime.fromtimestamp(self.expires,timezone.utc).isoformat().replace('+00:00','Z'), list=True, content=self.config.content_allowed)

    def common(self):
        c=self.config
        return dict(contract=CONTRACT,binding=c.binding,access=self.access(),query=dict(startDate=c.start,endDate=c.end,accountId=c.account_id), evidence='synthetic-http' if c.synthetic else 'authorized-instance-read', version='v2.23.0', sourceCommit=COMMIT)

    async def upstream(self,path):
        # Only internally constructed semantic reads; no URL, redirects, proxies or DNS supplied by callers.
        c=self.config; u=urlsplit(c.base)
        if path not in ['/integrations','/posts?'+urlencode(dict(startDate=c.start,endDate=c.end))]: raise Failure('ROUTE_DENIED',403)
        if self.reads>=c.max_reads: raise Failure('READ_BUDGET_EXHAUSTED',429)
        self.reads+=1
        writer=None
        try:
            tls=ssl.create_default_context() if u.scheme=='https' else None
            reader,writer=await asyncio.open_connection(c.approved_ip,u.port or (443 if tls else 80),ssl=tls,server_hostname=u.hostname if tls else None,limit=16384)
            writer.write(f'GET {u.path}{path} HTTP/1.1\r\nHost: {u.netloc}\r\nAuthorization: {self.upstream_key}\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n'.encode())
            await writer.drain()
            raw=await reader.readuntil(b'\r\n\r\n')
            if len(raw)>16384: raise Failure('UPSTREAM_HEADERS_TOO_LARGE')
            lines=raw.decode('latin1').split('\r\n'); status=int(lines[0].split()[1]); headers={}
            for line in lines[1:]:
                if not line: continue
                k,v=line.split(':',1); k=k.lower()
                if k in headers: raise Failure('INVALID_UPSTREAM_HEADERS')
                headers[k]=v.strip()
            if status!=200: raise Failure(f'UPSTREAM_{status}',403 if status in [401,403] else 429 if status==429 else 502)
            if headers.get('content-encoding','identity')!='identity' or 'application/json' not in headers.get('content-type',''): raise Failure('INVALID_UPSTREAM_CONTENT')
            if 'transfer-encoding' in headers:
                if headers['transfer-encoding']!='chunked' or 'content-length' in headers: raise Failure('INVALID_UPSTREAM_FRAMING')
                body=bytearray()
                while True:
                    line=await reader.readuntil(b'\r\n'); size=int(line.split(b';')[0],16)
                    if size<0 or len(body)+size>c.max_bytes: raise Failure('RESPONSE_TOO_LARGE')
                    if size==0: break
                    body.extend(await reader.readexactly(size))
                    if await reader.readexactly(2)!=b'\r\n': raise Failure('INVALID_UPSTREAM_FRAMING')
            elif 'content-length' in headers:
                size=int(headers['content-length'])
                if size<0 or size>c.max_bytes: raise Failure('RESPONSE_TOO_LARGE')
                body=await reader.readexactly(size)
            else:
                body=bytearray()
                while chunk:=await reader.read(min(65536,c.max_bytes+1-len(body))):
                    body.extend(chunk)
                    if len(body)>c.max_bytes: raise Failure('RESPONSE_TOO_LARGE')
            return json.loads(body)
        except Failure: raise
        except (ValueError,UnicodeError,asyncio.IncompleteReadError,asyncio.LimitOverrunError): raise Failure('INVALID_UPSTREAM_RESPONSE') from None
        except (OSError,ssl.SSLError): raise Failure('UPSTREAM_NETWORK') from None
        finally:
            if writer:
                writer.close()
                try: await writer.wait_closed()
                except (ConnectionError,ssl.SSLError): pass

    async def snapshot(self,request_id):
        if self.busy: raise Failure('READ_IN_PROGRESS',429)
        self.busy=True
        try:
            accounts=await self.upstream('/integrations')
            if not isinstance(accounts,list): raise Failure('INVALID_CONTRACT',422)
            matches=[a for a in accounts if isinstance(a,dict) and a.get('id')==self.config.account_id]
            if len(matches)!=1 or matches[0].get('disabled') is not False: raise Failure('CHANNEL_UNAVAILABLE',403)
            a=matches[0]; secrets=(self.local_token,self.upstream_key)
            channel=dict(id=identifier(a['id']),name=safe_text(a.get('name'),secrets),platform=safe_text(a.get('identifier'),secrets))
            data=await self.upstream('/posts?'+urlencode(dict(startDate=self.config.start,endDate=self.config.end)))
            if not isinstance(data,dict) or not isinstance(data.get('posts'),list): raise Failure('INVALID_CONTRACT',422)
            records=[]; seen=set(); omissions=dict(recurrence=0,outsideWindow=0,capped=0)
            for p in data['posts']:
                if not isinstance(p,dict) or not isinstance(p.get('integration'),dict) or not isinstance(p['integration'].get('id'),str): raise Failure('INVALID_CONTRACT',422)
                if p['integration']['id']!=self.config.account_id: continue
                if p.get('intervalInDays') is not None or p.get('actualDate') is not None:
                    omissions['recurrence']+=1; continue
                pid=identifier(p.get('id'))
                if pid in seen: raise Failure('DUPLICATE_POST_ID',422)
                seen.add(pid)
                stamp=instant(p.get('publishDate'))
                if not instant(self.config.start)<=stamp<=instant(self.config.end): omissions['outsideWindow']+=1; continue
                raw=p.get('state'); states={'QUEUE':'scheduled','PUBLISHED':'published','ERROR':'failed','DRAFT':'draft'}
                if raw not in states: raise Failure('UNKNOWN_STATE',422)
                record=dict(id=pid,accountId=channel['id'],rawStatus=raw,status=states[raw],timeField='scheduledAt' if raw=='QUEUE' else 'unscheduled' if raw=='DRAFT' else 'unknown',relationshipStatus='not-supplied')
                if raw=='QUEUE': record['scheduledAt']=p['publishDate']
                if self.config.content_allowed: record['summary']=safe_text(p.get('content'),secrets)
                release=p.get('releaseId')
                if release not in [None,'','missing']: record['suppliedExternalReference']=safe_text(release,secrets)
                records.append(record)
            records.sort(key=lambda p:p['id']); omissions['capped']=max(0,len(records)-self.config.max_records)
            result=dict(self.common(),requestId=request_id,status='ok',observationId='read-'+uuid.uuid4().hex,observedAt=datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'),completeness='partial' if any(omissions.values()) else 'bounded',omissions=omissions,channel=channel,records=records[:self.config.max_records])
            # Never allow either credential to reappear through any projected field.
            encoded=json.dumps(result)
            if any(s in encoded for s in secrets): raise Failure('REDACTION_REJECTED',422)
            if len(encoded.encode())>self.config.max_bytes: raise Failure('RESPONSE_TOO_LARGE')
            return result
        finally: self.busy=False

    async def route(self,method,target,headers):
        c=self.config
        if method!='GET': raise Failure('METHOD_DENIED',405)
        if target.split('?')[0] not in ['/pilot/access','/pilot/snapshot'] or len(target)>4096: raise Failure('ROUTE_DENIED',404)
        if not hmac.compare_digest(headers.get('authorization',''),self.local_token): raise Failure('LOCAL_AUTH_REQUIRED',401)
        if time.time()>=self.expires: raise Failure('LOCAL_ACCESS_EXPIRED',403)
        try: binding=json.loads(headers.get('x-pilot-binding',''))
        except ValueError: raise Failure('BINDING_DENIED',403) from None
        if binding!=c.binding: raise Failure('BINDING_DENIED',403)
        if target=='/pilot/access': return self.common()
        if headers.get('x-pilot-access')!=self.revision: raise Failure('ACCESS_RETIRED',403)
        q=parse_qs(urlsplit(target).query,keep_blank_values=True)
        if set(q)!={'startDate','endDate','requestId'} or any(len(v)!=1 for v in q.values()) or q['startDate']!=[c.start] or q['endDate']!=[c.end]: raise Failure('QUERY_DENIED',403)
        return await self.snapshot(identifier(q['requestId'][0]))

    async def handle(self,reader,writer):
        task=gone=None
        try:
            raw=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),2)
            if len(raw)>16384: raise Failure('LOCAL_HEADERS_TOO_LARGE',431)
            lines=raw.decode('ascii').split('\r\n'); method,target,protocol=lines[0].split(); headers={}
            for line in lines[1:]:
                if not line: continue
                k,v=line.split(':',1); k=k.lower()
                if k in headers: raise Failure('DUPLICATE_HEADER',400)
                headers[k]=v.strip()
            port=writer.get_extra_info('sockname')[1]
            if headers.get('host')!=f'127.0.0.1:{port}' or headers.get('origin',f'http://127.0.0.1:{port}')!=f'http://127.0.0.1:{port}': raise Failure('ORIGIN_DENIED',403)
            if 'transfer-encoding' in headers or headers.get('content-length','0')!='0': raise Failure('BODY_DENIED',400)
            # Disconnect cancels in-flight upstream IO. Absolute timeout covers both upstream reads.
            task=asyncio.create_task(self.route(method,target,headers)); gone=asyncio.create_task(reader.read(1))
            done,_=await asyncio.wait([task,gone],timeout=self.config.timeout,return_when=asyncio.FIRST_COMPLETED)
            if gone in done: raise Failure('CALLER_CANCELLED',499)
            if task not in done: raise Failure('UPSTREAM_TIMEOUT',504)
            payload=task.result(); status=200
        except Failure as e:
            status=e.status; payload=dict(status='restricted' if status in [401,403] else 'invalid' if status in [400,422] else 'error',errorClass=e.code,message='The bounded read could not be completed.')
        except (ValueError,UnicodeError,asyncio.IncompleteReadError,asyncio.LimitOverrunError,TimeoutError):
            status=400; payload=dict(status='invalid',errorClass='INVALID_LOCAL_REQUEST',message='Invalid local read request.')
        except Exception:
            status=500; payload=dict(status='error',errorClass='INTERNAL_ERROR',message='The bounded read could not be completed.')
        finally:
            for pending in [task,gone]:
                if pending and not pending.done(): pending.cancel()
            await asyncio.gather(*(p for p in [task,gone] if p),return_exceptions=True)
        body=json.dumps(payload,separators=(',',':')).encode()
        try:
            writer.write(f'HTTP/1.1 {status} Result\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nConnection: close\r\n\r\n'.encode()+body); await writer.drain()
        except ConnectionError: pass
        finally:
            writer.close()
            try: await writer.wait_closed()
            except ConnectionError: pass

async def run(config_path,port):
    with open(config_path) as f: config=Config(**json.load(f))
    # Only explicit environment names, never credential discovery, files or persistence.
    pilot=Pilot(config,os.environ.get('PILOT_LOCAL_TOKEN',''),os.environ.get('PILOT_UPSTREAM_KEY',''))
    server=await asyncio.start_server(pilot.handle,'127.0.0.1',port)
    print('Owner-local bounded read adapter listening on loopback.',flush=True)
    async with server: await server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--config',required=True); parser.add_argument('--port',type=int,default=43119); args=parser.parse_args()
    try: asyncio.run(run(args.config,args.port))
    except Failure as e: raise SystemExit(e.code) from None
