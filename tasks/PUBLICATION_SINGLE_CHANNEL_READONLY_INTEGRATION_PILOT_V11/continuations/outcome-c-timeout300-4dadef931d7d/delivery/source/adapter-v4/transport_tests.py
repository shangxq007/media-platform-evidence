"""Actual loopback HTTP unittests. NOT RUN or collected by offline authoring.

Python 3.11+ stdlib; unconditional tests, synthetic credentials, bounded threads,
socket resources and joins. All listeners use OS-assigned ephemeral loopback ports. No skips.
"""
import base64
import copy
import json
import select
import socket
import threading
import time
import unittest
from dataclasses import replace
from urllib.parse import urlencode
from boundary import Authority, LOCAL_HOST, identity, snapshot_target
from client import Client
from runtime_handle import _bound_handle
from model import Config, Failure, PENDING
from server import Server
from transport import Operation, connect, read_response, send
from wire import MAX_HEADERS, encode_response, parse_head
from test_model import raw_config, post, LOCAL, UPSTREAM, START, END

class SyntheticUpstream:
    def __init__(self):
        self.accounts = [{'id':'account1','name':'Synthetic channel','identifier':'synthetic','disabled':False}]
        self.posts = [post()]
        self.status = 200
        self.body_override = None
        self.extra = b''
        self.delay = 0
        self.drip = None
        self.suffix = b''
        self.hold_open = 0
        self.received = threading.Event()
        self.stop = threading.Event()
        self.calls = []
        self.errors = []
        self.listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.listener.bind((LOCAL_HOST,0))
        self.port = self.listener.getsockname()[1]
        self.listener.listen(4)
        self.listener.settimeout(0.05)
        self.thread = threading.Thread(target=self.serve,daemon=True)
        self.thread.start()

    def serve(self):
        while not self.stop.is_set():
            try:
                connection,_ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with connection:
                connection.settimeout(0.2)
                try:
                    deadline = time.monotonic()+3
                    raw = bytearray()
                    while not raw.endswith(b'\r\n\r\n'):
                        if len(raw) >= MAX_HEADERS or time.monotonic() >= deadline:
                            raise ValueError('synthetic request bound')
                        value = connection.recv(1)
                        if not value: raise ValueError('synthetic incomplete request')
                        raw.extend(value)
                    (method,target),headers = parse_head(bytes(raw))
                    # Store route and booleans only; no raw credentials in logs/errors.
                    self.calls.append({'method':method,'target':target,'raw_auth_ok':headers.get('authorization')==UPSTREAM,
                                       'local_absent':LOCAL not in raw.decode(),'body_absent':'content-length' not in headers})
                    self.received.set()
                    if self.stop.wait(self.delay): continue
                    payload = self.accounts if target.endswith('/integrations') else {'posts':self.posts}
                    body = self.body_override if self.body_override is not None else json.dumps(payload).encode()
                    if self.status != 200: body = b'PRIVATE_ERROR '+UPSTREAM.encode()
                    data = (f'HTTP/1.1 {self.status} Result\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n'.encode()+self.extra+b'\r\n'+body+self.suffix)
                    if self.drip == 'headers':
                        chunks = [bytes([b]) for b in data]
                    elif self.drip == 'body':
                        h,b = data.split(b'\r\n\r\n',1)
                        chunks = [h+b'\r\n\r\n']+[bytes([x]) for x in b]
                    else:
                        chunks = [data]
                    for chunk in chunks:
                        if self.stop.is_set() or time.monotonic() >= deadline: break
                        connection.sendall(chunk)
                        if self.drip and self.stop.wait(0.025): break
                    self.stop.wait(self.hold_open)
                except (OSError,ValueError,Failure):
                    # Broken pipes and deadline cancellation are expected synthetic IO.
                    pass

    def close(self):
        self.stop.set()
        self.listener.close()
        self.thread.join(4)
        if self.thread.is_alive(): raise AssertionError('synthetic thread did not stop')

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.up = SyntheticUpstream()
        self.addCleanup(self.up.close)
        self.config = Config.from_mapping(raw_config(base=f'http://127.0.0.1:{self.up.port}/public/v1',timeout_seconds=2))
        self.authority = Authority(self.config,LOCAL,UPSTREAM,'rev-http-1')
        self.server = Server(self.authority)
        self.thread = threading.Thread(target=self.server.serve,daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.assertTrue(self.server.ready.wait(2),'bounded listener startup')
        self.assertIsNone(self.server.start_error)

    def close_server(self):
        self.server.close()
        self.thread.join(3)
        self.assertFalse(self.thread.is_alive(),'bounded server teardown')
        self.assertEqual(self.server.active,0)

    def request_bytes(self,method='GET',target=None,token=LOCAL,ident=None,revision='rev-http-1',extra=b'',body=b''):
        if target is None: target = snapshot_target(self.config,'r1')
        if ident is None: ident = identity(self.config)
        raw = (f'{method} {target} HTTP/1.1\r\nHost: {self.server.handle.host_header}\r\n'
               f'Authorization: {token}\r\nX-Observation-Identity: '+json.dumps(ident,separators=(',',':'))+'\r\n').encode()
        if revision is not None: raw += f'X-Observation-Revision: {revision}\r\n'.encode()
        return raw+extra+b'\r\n'+body

    def exchange(self,raw):
        op = Operation(3,2*1048576)
        sock = connect(LOCAL_HOST,self.server.handle.port,op)
        try:
            send(sock,raw,op)
            status,_,body = read_response(sock,op,1048576)
            result = json.loads(body)
            self.assertNotIn(LOCAL,json.dumps(result))
            self.assertNotIn(UPSTREAM,json.dumps(result))
            return status,result
        finally:
            sock.close()

    def snapshot(self,**kwargs):
        return self.exchange(self.request_bytes(**kwargs))

    def assert_failure(self,code,status=502,**kwargs):
        actual,value = self.snapshot(**kwargs)
        self.assertEqual(actual,status)
        self.assertEqual(value['errorClass'],code)
        self.assertNotIn('snapshot',value)
        self.assertNotIn('PRIVATE',json.dumps(value))

    def test_normal_authenticated_client_roundtrip(self):
        client = Client(self.config,LOCAL,self.server.handle)
        result = client.read('r-normal')
        self.assertEqual(result,client.snapshot)
        self.assertEqual(result['receipt']['identity'],identity(self.config))
        self.assertEqual(result['coreContract'],PENDING)
        self.assertEqual(result['snapshot']['observations'][0]['scheduledAt'],'2026-09-09T12:00:00.000Z')
        self.assertEqual(len(self.up.calls),2)
        self.assertTrue(all(c['raw_auth_ok'] and c['local_absent'] and c['body_absent'] for c in self.up.calls))
        self.assertTrue(all(c['method']=='GET' for c in self.up.calls))
        self.assertEqual(self.up.calls[0]['target'],'/public/v1/integrations')
        self.assertEqual(self.up.calls[1]['target'],'/public/v1/posts?'+urlencode({'startDate':START,'endDate':'2026-09-30T23:59:59.999Z'}))

    def test_unauthenticated(self):
        self.assert_failure('LOCAL_AUTH_REQUIRED',401,token='incorrect')
        self.assertEqual(self.up.calls,[])

    def identity_denial(self,path):
        ident = identity(self.config)
        parent = ident
        for key in path[:-1]: parent = parent[key]
        parent[path[-1]] = 'wrong'
        self.assert_failure('IDENTITY_DENIED',403,ident=ident)
        self.assertEqual(self.up.calls,[])

    def test_principal_binding(self): self.identity_denial(('binding','scope','principalId'))
    def test_tenant_binding(self): self.identity_denial(('binding','scope','tenantId'))
    def test_session_binding(self): self.identity_denial(('binding','scope','sessionId'))
    def test_workspace_binding(self): self.identity_denial(('binding','scope','workspaceId'))
    def test_project_binding(self): self.identity_denial(('binding','scope','projectId'))
    def test_source_binding(self): self.identity_denial(('binding','scope','sourceId'))
    def test_owner_binding(self): self.identity_denial(('binding','ownerId'))
    def test_provider_binding(self): self.identity_denial(('provider',))
    def test_instance_binding(self): self.identity_denial(('instance',))
    def test_account_binding(self): self.identity_denial(('account',))
    def test_start_binding(self): self.identity_denial(('startInclusive',))
    def test_end_binding(self): self.identity_denial(('endExclusive',))

    def test_revision_binding(self):
        self.assert_failure('ACCESS_RETIRED',403,revision='old-revision')
        self.assertEqual(self.up.calls,[])

    def test_date_query_duplicates_and_arbitrary_url(self):
        target = snapshot_target(self.config,'r1')
        for altered in (target+'&requestId=x',target+'&url=http://127.0.0.1',target.replace('2026-10-01','2026-10-02')):
            with self.subTest(target_kind='altered'): self.assert_failure('QUERY_DENIED',403,target=altered)
        self.assertEqual(self.up.calls,[])

    def test_half_open_boundaries(self):
        self.up.posts = [post(id='a',publishDate=START),post(id='b',publishDate='2026-09-30T23:59:59.999Z'),post(id='c',publishDate=END),post(id='d',publishDate='2026-08-31T23:59:59.999Z')]
        status,result = self.snapshot()
        self.assertEqual(status,200)
        self.assertEqual([r['externalReferences']['post'] for r in result['snapshot']['observations']],['a','b'])
        self.assertEqual(result['snapshot']['omissions']['outsideWindow'],2)
        self.assertEqual(result['snapshot']['completeness'],'partial')

    def test_duplicate_post_ids(self):
        self.up.posts = [post(),post()]
        self.assert_failure('DUPLICATE_EXTERNAL_POST_ID',422)

    def test_account_missing_duplicate_disabled_and_foreign_posts(self):
        original = copy.deepcopy(self.up.accounts)
        for accounts in ([],original*2,[dict(original[0],disabled=True)]):
            self.up.accounts = accounts
            self.assert_failure('EXTERNAL_ACCOUNT_UNAVAILABLE',403)
        self.assertEqual(len(self.up.calls),3)
        self.up.accounts = original
        self.up.posts = [post(),post(id='other',integration={'id':'foreign'})]
        status,result = self.snapshot()
        self.assertEqual(status,200)
        self.assertEqual(len(result['snapshot']['observations']),1)

    def test_partial_recurrence_and_record_cap(self):
        self.up.posts = [post(id=f'p{i:03d}') for i in range(201)]+[post(id='recurring',intervalInDays=1)]
        status,result = self.snapshot()
        self.assertEqual(status,200)
        self.assertEqual(len(result['snapshot']['observations']),200)
        self.assertEqual(result['snapshot']['omissions'],{'recurrence':1,'outsideWindow':0,'recordCap':1})
        self.assertEqual(result['snapshot']['completeness'],'partial')

    def test_unknown_state_missing_values_and_unavailable_relations(self):
        self.up.posts = [post(state=None),post(id='novel',state='FUTURE'),post(id='published',state='PUBLISHED')]
        self.up.posts[0].pop('content')
        status,result = self.snapshot()
        self.assertEqual(status,200)
        for row in result['snapshot']['observations']:
            self.assertTrue(all(v=={'status':PENDING} for v in row['relationships'].values()))
            self.assertFalse({'id','publishedAt','attemptId','resultId','summary'} & set(row))
        self.assertEqual([r['displayStatus'] for r in result['snapshot']['observations']],['unknown','unknown','published'])
        self.up.posts = [post(integration={})]
        self.assert_failure('INVALID_IDENTIFIER',422)

    def upstream_status(self,status,code,safe):
        self.up.status = status
        self.assert_failure(code,safe)
        self.assertEqual(len(self.up.calls),1)
        self.assertEqual(self.authority.reads,2)

    def test_upstream_400(self): self.upstream_status(400,'UPSTREAM_BAD_REQUEST',502)
    def test_upstream_401(self): self.upstream_status(401,'UPSTREAM_AUTH',403)
    def test_upstream_403(self): self.upstream_status(403,'UPSTREAM_AUTH',403)
    def test_upstream_404(self): self.upstream_status(404,'UPSTREAM_NOT_FOUND',502)
    def test_upstream_429(self): self.upstream_status(429,'UPSTREAM_RATE_LIMIT',429)
    def test_upstream_500(self): self.upstream_status(500,'UPSTREAM_FAILURE',502)
    def test_upstream_503(self): self.upstream_status(503,'UPSTREAM_FAILURE',502)

    def test_redirect_is_not_followed(self):
        self.up.extra = b'Location: http://127.0.0.1:1/forbidden-write\r\n'
        self.upstream_status(302,'UPSTREAM_REDIRECT',502)

    def test_malformed_json(self):
        for body in (b'{',b'{"posts":[],"posts":[]}',b'NaN'):
            self.up.body_override = body
            self.assert_failure('INVALID_JSON',422)

    def test_upstream_headers_size(self):
        self.up.extra = b'X-Large: '+b'x'*MAX_HEADERS+b'\r\n'
        self.assert_failure('HEADERS_TOO_LARGE',431)

    def test_upstream_body_size(self):
        self.up.body_override = b'x'*(1048576+1)
        self.assert_failure('RESPONSE_TOO_LARGE',502)

    def test_upstream_ambiguous_framing_and_header_injection(self):
        for extra in (b'Content-Length: 2\r\n',b'Transfer-Encoding: chunked\r\n',b'X: a\nb\r\n',b'Content-Encoding: gzip\r\n'):
            self.up.extra = extra
            status,result = self.snapshot()
            self.assertIn(status,(400,502))
            self.assertNotIn('snapshot',result)
        self.assertEqual(len(self.up.calls),4)

    def test_upstream_trailing_body_is_rejected(self):
        self.up.suffix = b'HTTP/1.1 200 Second\r\n\r\n'
        self.assert_failure('INVALID_HTTP_FRAMING',502)

    def assert_bounded_no_publication(self):
        start = time.monotonic()
        try:
            status,result = self.snapshot()
        except Failure as error:
            self.assertIn(error.code,('INCOMPLETE_HTTP','DEADLINE_EXCEEDED'))
        else:
            self.assertNotEqual(status,200)
            self.assertNotIn('snapshot',result)
        self.assertLess(time.monotonic()-start,2.8)
        self.assertEqual(self.authority.published,0)

    def test_slowdrip_headers_absolute_deadline(self):
        self.up.drip = 'headers'
        self.assert_bounded_no_publication()

    def test_slowdrip_body_absolute_deadline(self):
        self.up.drip = 'body'
        self.assert_bounded_no_publication()

    def test_deadline_spans_both_upstream_reads(self):
        self.up.delay = 1.2
        self.assert_bounded_no_publication()
        self.assertEqual(len(self.up.calls),2)

    def test_peer_teardown_cannot_extend_deadline(self):
        self.up.hold_open = 4
        self.assert_bounded_no_publication()

    def wait_idle(self):
        end = time.monotonic()+2.8
        while self.server.active and time.monotonic()<end: time.sleep(0.01)
        self.assertEqual(self.server.active,0)

    def test_caller_disconnect_cancels_and_late_result_cannot_publish(self):
        self.up.delay = 0.4
        op = Operation(2,1048576)
        sock = connect(LOCAL_HOST,self.server.handle.port,op)
        try:
            send(sock,self.request_bytes(),op)
            self.assertTrue(self.up.received.wait(1))
        finally:
            sock.close()
        self.wait_idle()
        time.sleep(0.5)  # allow the synthetic late response; bounded within this test
        self.assertEqual(self.authority.published,0)
        self.assertEqual(len(self.up.calls),1)

    def test_server_retirement_rejects_late_result(self):
        self.up.delay = 0.4
        op = Operation(2,1048576)
        sock = connect(LOCAL_HOST,self.server.handle.port,op)
        try:
            send(sock,self.request_bytes(),op)
            self.assertTrue(self.up.received.wait(1))
            self.authority.retire()
            with self.assertRaises(Failure) as caught:
                read_response(sock,op,1048576)
            self.assertEqual(caught.exception.code,'INCOMPLETE_HTTP')  # active retirement closes without late publication
        finally:
            sock.close()
        self.wait_idle()
        self.assertEqual(self.authority.published,0)

    def test_client_retirement_closes_request_and_drops_late_result(self):
        self.up.delay = 0.4
        client = Client(self.config,LOCAL,self.server.handle)
        outcomes = []
        def run():
            try: outcomes.append(client.read('r-retire'))
            except Failure as error: outcomes.append(error.code)
        thread = threading.Thread(target=run,daemon=True)
        thread.start()
        try:
            self.assertTrue(self.up.received.wait(1))
            client.retire()
        finally:
            thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes,['CLIENT_RETIRED'])
        self.assertIsNone(client.snapshot)
        self.wait_idle()
        self.assertEqual(self.authority.published,1)  # access receipt only

    def test_forbidden_write_verbs_routes_bodies_and_headers(self):
        for method in ('POST','PUT','PATCH','DELETE','CONNECT','OPTIONS','HEAD','TRACE'):
            self.assert_failure('METHOD_DENIED',405,method=method)
        for target in ('/posts','/integrations','/observations/send','/observations/access?next=x'):
            self.assert_failure('ROUTE_DENIED',404,target=target)
        self.assert_failure('BODY_DENIED',400,extra=b'Content-Length: 1\r\n',body=b'x')
        self.assert_failure('BODY_DENIED',400,body=b'x')
        self.assert_failure('HEADER_DENIED',400,extra=b'X-Upstream-URL: http://127.0.0.1\r\n')
        self.assertEqual(self.up.calls,[])
        self.assertEqual(self.authority.reads,0)

    def test_local_ambiguous_headers_and_size(self):
        for extra in (f'Host: {self.server.handle.host_header}\r\n'.encode(),b'Transfer-Encoding: chunked\r\n',b'Content-Length: +1\r\n',b'X: bad\nInjected: yes\r\n'):
            status,result = self.snapshot(extra=extra)
            self.assertEqual(status,400)
            self.assertNotIn('snapshot',result)
        status,result = self.snapshot(extra=b'X-Large: '+b'x'*MAX_HEADERS+b'\r\n')
        self.assertEqual(status,431)
        self.assertEqual(self.up.calls,[])

    def test_repeat_reads_zero_writes_and_budget_no_retry(self):
        self.authority.config = replace(self.config,max_reads=4)
        for _ in range(2):
            status,result = self.snapshot()
            self.assertEqual(status,200)
            self.assertEqual(len(result['snapshot']['observations']),1)
        self.assert_failure('READ_BUDGET_EXHAUSTED',429)
        self.assertEqual(len(self.up.calls),4)
        self.assertEqual(self.authority.reads,4)
        self.assertTrue(all(c['method']=='GET' for c in self.up.calls))
        self.assertLessEqual(self.authority.bytes_read,3*(2*(1048576+MAX_HEADERS+1)+MAX_HEADERS))

    def test_keys_never_enter_projection_errors_or_request_urls(self):
        for secret in (LOCAL,UPSTREAM):
            for leaked in (secret,base64.b64encode(secret.encode()).decode(),secret.encode().hex()):
                self.up.accounts[0]['name'] = leaked
                self.assert_failure('UNSAFE_UPSTREAM_TEXT',422)
        self.assertTrue(all(LOCAL not in c['target'] and UPSTREAM not in c['target'] and c['raw_auth_ok'] and c['local_absent'] for c in self.up.calls))
        self.assertEqual(self.authority.published,0)

    def test_local_missing_auth_and_duplicate_authorization(self):
        raw = self.request_bytes().replace(('Authorization: '+LOCAL+'\r\n').encode(),b'')
        status,value = self.exchange(raw)
        self.assertEqual(status,401)
        self.assertEqual(value['errorClass'],'LOCAL_AUTH_REQUIRED')
        self.assert_failure('DUPLICATE_HEADER',400,extra=('Authorization: '+LOCAL+'\r\n').encode())
        self.assertEqual(self.up.calls,[])

    def test_read_volume_cap_on_real_http(self):
        op = Operation(2,32)
        sock = connect(LOCAL_HOST,self.server.handle.port,op)
        try:
            send(sock,self.request_bytes(target='/observations/access',revision=None),op)
            with self.assertRaises(Failure) as caught: read_response(sock,op,1048576)
            self.assertEqual(caught.exception.code,'READ_VOLUME_EXHAUSTED')
            self.assertLessEqual(op.volume,33)
        finally:
            sock.close()
        self.assertEqual(self.up.calls,[])

    def test_client_rejects_altered_wire_receipt_and_projection(self):
        # Malicious synthetic local peer exercises actual client receive/validation.
        self.server.close()
        self.thread.join(3)
        self.assertFalse(self.thread.is_alive())
        from model import PostizProjector
        receipt = Authority(self.config,LOCAL,UPSTREAM,'other-rev').receipt()
        snapshot = PostizProjector(self.config,LOCAL,UPSTREAM).project(self.up.accounts,{'posts':[post()]},'r1','2026-09-09T13:00:00Z')
        snapshot['evidence'] = 'synthetic-http-observation'
        for attack in ('identity','revision','provider','instance','account','request','window','access','contract','receipt-bool','echo-bool','receipt-lifetime'):
            with self.subTest(attack=attack):
                mutated = copy.deepcopy(receipt)
                projected = copy.deepcopy(snapshot)
                if attack == 'identity': mutated['identity']['binding']['scope']['projectId'] = 'foreign'
                if attack == 'revision': mutated['revision'] = 'stale'
                if attack in ('provider','instance','account'): projected['observations'][0]['externalReferences'][attack] = 'foreign'
                if attack == 'window': projected['window']['endExclusive'] = START
                if attack == 'access': projected['access']['list'] = 1
                if attack == 'contract': projected['contract'] = 'invented-core'
                if attack in ('receipt-bool','echo-bool'): mutated['list'] = 1
                if attack == 'receipt-lifetime': mutated['lifetimeSeconds'] = 1800.0
                envelope = {'contract':receipt['contract'],'kind':'owner-local-snapshot-envelope','coreContract':PENDING,
                            'receipt':mutated,'requestId':'foreign' if attack=='request' else 'r1','snapshot':projected}
                listener = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                listener.bind(('127.0.0.1',0)); listener.listen(2); listener.settimeout(0.5)
                peer_handle = _bound_handle(listener.getsockname(),receipt['revision'])
                stop = threading.Event()
                errors = []
                def peer():
                    try:
                        for payload in (mutated if attack in ('identity','receipt-bool','receipt-lifetime') else receipt,envelope):
                            if stop.is_set(): break
                            connection,_ = listener.accept()
                            with connection:
                                connection.settimeout(0.5)
                                raw = bytearray()
                                while not raw.endswith(b'\r\n\r\n'):
                                    if len(raw)>=MAX_HEADERS: raise ValueError('bounded test request')
                                    b = connection.recv(1)
                                    if not b: break
                                    raw.extend(b)
                                connection.sendall(encode_response(200,payload))
                    except (OSError,ValueError):
                        errors.append('bounded peer closed')
                thread = threading.Thread(target=peer,daemon=True)
                thread.start()
                client = Client(self.config,LOCAL,peer_handle)
                try:
                    with self.assertRaises(Failure) as caught: client.read('r1')
                    self.assertIn(caught.exception.code,('INVALID_LOCAL_RECEIPT','INVALID_LOCAL_ENVELOPE','INVALID_LOCAL_SNAPSHOT'))
                    self.assertIsNone(client.snapshot)
                finally:
                    stop.set(); listener.close(); thread.join(2)
                self.assertFalse(thread.is_alive())


    def test_ephemeral_handle_and_exact_actual_host(self):
        self.assertGreater(self.server.handle.port,0)
        self.assertGreater(self.up.port,0)
        self.assertNotEqual(self.server.handle.port,self.up.port)
        self.assertEqual(self.authority._handle,self.server.handle)
        raw = self.request_bytes()
        for host in ('localhost:'+str(self.server.handle.port),'127.0.0.1:0',
                     '127.0.0.1:'+str(self.up.port),self.server.handle.host_header+'.'):
            with self.subTest(host_kind='mismatch'):
                status,result = self.exchange(raw.replace(self.server.handle.host_header.encode(),host.encode(),1))
                self.assertEqual((status,result['errorClass']),(403,'HOST_DENIED'))
        self.assertEqual(self.up.calls,[])
        self.assertEqual(self.authority.reads,0)

    def test_client_invalid_request_id_has_zero_acquisitions(self):
        client = Client(self.config,LOCAL,self.server.handle)
        for request_id in (None,True,'','bad\r\nInjected: yes','x'*181):
            with self.subTest(kind=type(request_id).__name__),self.assertRaises(Failure):
                client.read(request_id)
        self.assertEqual(self.authority.published,0)
        self.assertEqual(self.authority.bytes_read,0)
        self.assertEqual(self.authority.reads,0)
        self.assertEqual(self.up.calls,[])
        self.assertIsNone(client.snapshot)

    def test_client_binding_is_detached_during_actual_roundtrip(self):
        client = Client(self.config,LOCAL,self.server.handle)
        original = identity(self.config)
        self.config.binding['scope']['projectId'] = 'mutated-owner-input'
        client.config.binding['ownerId'] = 'mutated-returned-view'
        result = client.read('r-detached')
        self.assertEqual(result['receipt']['identity'],original)
        self.assertEqual(len(self.up.calls),2)

    def test_newer_read_supersedes_inflight_http_and_discards_late_response(self):
        self.up.delay = 0.3
        client = Client(self.config,LOCAL,self.server.handle)
        outcomes = []
        def older():
            try: outcomes.append(client.read('r-old'))
            except Failure as error: outcomes.append(error.code)
        old_thread = threading.Thread(target=older,daemon=True)
        old_thread.start()
        try:
            self.assertTrue(self.up.received.wait(1))
            newer = client.read('r-new')
        finally:
            old_thread.join(3)
        self.assertFalse(old_thread.is_alive())
        self.assertEqual(outcomes,['READ_SUPERSEDED'])
        self.assertEqual(newer['requestId'],'r-new')
        self.assertEqual(client.snapshot,newer)
        self.assertEqual(len(self.up.calls),3)  # old integrations, new integrations + posts
        self.assertTrue(all(call['method']=='GET' for call in self.up.calls))

    def test_older_completed_http_cannot_overwrite_newer_publication(self):
        # Both reads use real HTTP. Only the pure acceptance boundary is paused
        # after the older response has arrived, making the late publication deterministic.
        from unittest.mock import patch
        import client as client_module
        original = client_module.validate_envelope
        arrived,release = threading.Event(),threading.Event()
        outcomes = []
        client = Client(self.config,LOCAL,self.server.handle)
        def pause_old(value,*args):
            result = original(value,*args)
            if value['requestId'] == 'r-old':
                arrived.set()
                if not release.wait(1.5): raise AssertionError('bounded publication barrier')
            return result
        def older():
            try: outcomes.append(client.read('r-old'))
            except Failure as error: outcomes.append(error.code)
        with patch.object(client_module,'validate_envelope',pause_old):
            old_thread = threading.Thread(target=older,daemon=True)
            old_thread.start()
            try:
                self.assertTrue(arrived.wait(1))
                newer = client.read('r-new')
                self.assertEqual(client.snapshot,newer)
            finally:
                release.set()
                old_thread.join(3)
        self.assertFalse(old_thread.is_alive())
        self.assertEqual(outcomes,['READ_SUPERSEDED'])
        self.assertEqual(client.snapshot['requestId'],'r-new')
        self.assertEqual(len(self.up.calls),4)
        self.assertTrue(all(call['method']=='GET' for call in self.up.calls))
        client.retire()
        self.assertIsNone(client.snapshot)

    def test_combined_owner_runner_passes_runtime_handle_and_closes(self):
        from owner_runner import run_once
        result = run_once(self.config,LOCAL,UPSTREAM,'r-combined')
        self.assertEqual(result['requestId'],'r-combined')
        self.assertEqual(result['coreContract'],PENDING)
        self.assertEqual(len(self.up.calls),2)
        self.assertEqual(self.authority.published,0)  # separate fixture listener unused
        self.assertTrue(all(call['method']=='GET' for call in self.up.calls))

if __name__ == '__main__':
    unittest.main()
