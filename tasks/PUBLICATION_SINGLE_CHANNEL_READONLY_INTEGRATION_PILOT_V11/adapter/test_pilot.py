"""Real loopback HTTP integration tests; all identities and secrets are synthetic."""
import asyncio
import json
import unittest
from pilot import Pilot, Config

SCOPE = dict(principalId='owner', tenantId=None, sessionId='session', workspaceId='w', projectId='p', sourceId='postiz-local')
BINDING = dict(scope=SCOPE, ownerId='host1')
START, END = '2026-09-01T00:00:00Z', '2026-09-30T23:59:59Z'

class BoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.calls = []
        self.status = 200
        self.extra_headers = ''
        self.delay = 0
        self.accounts = [dict(id='account1', name='Synthetic channel', identifier='synthetic', disabled=False), dict(id='other', name='PRIVATE_OTHER', identifier='x', disabled=False)]
        self.posts = [self.post()]
        self.upstream = await asyncio.start_server(self.up, '127.0.0.1', 0)
        port = self.upstream.sockets[0].getsockname()[1]
        self.config = Config(base=f'http://127.0.0.1:{port}/public/v1', approved_ip='127.0.0.1', version='v2.23.0', binding=BINDING, account_id='account1', start=START, end=END, organization_read_consent=True, synthetic=True, content_allowed=False)
        self.pilot = Pilot(self.config, 'synthetic-local-token', 'synthetic-upstream-key')
        self.server = await asyncio.start_server(self.pilot.handle, '127.0.0.1', 0)
        self.port = self.server.sockets[0].getsockname()[1]

    def post(self, **kw):
        return dict(dict(id='post1', content='PRIVATE_COPY', integration={'id':'account1'}, state='QUEUE', publishDate='2026-09-09T12:00:00Z', releaseURL='https://private.invalid/secret', releaseId='external-supplied', intervalInDays=None), **kw)

    async def asyncTearDown(self):
        self.server.close(); self.upstream.close()
        await self.server.wait_closed(); await self.upstream.wait_closed()

    async def up(self, reader, writer):
        try:
            raw = await reader.readuntil(b'\r\n\r\n')
            head = raw.decode(); self.calls.append(head)
            await asyncio.sleep(self.delay)
            body = json.dumps(self.accounts if head.startswith('GET /public/v1/integrations ') else {'posts':self.posts}).encode() if self.status == 200 else b'PRIVATE_ERROR synthetic-upstream-key'
            writer.write(f'HTTP/1.1 {self.status} X\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\n{self.extra_headers}\r\n'.encode()+body)
            await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close(); await writer.wait_closed()

    async def request(self, path='/pilot/access', method='GET', token='synthetic-local-token', binding=None, access=None, extra=''):
        r,w = await asyncio.open_connection('127.0.0.1', self.port)
        head = f'{method} {path} HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\nAuthorization: {token}\r\nX-Pilot-Binding: {json.dumps(binding or BINDING)}\r\nX-Pilot-Access: {access or self.pilot.revision}\r\n{extra}\r\n'
        w.write(head.encode()); await w.drain()
        data = await r.read(); w.close(); await w.wait_closed()
        h,b = data.split(b'\r\n\r\n',1)
        return int(h.split()[1]),json.loads(b)

    async def snapshot(self, **kw):
        from urllib.parse import urlencode
        return await self.request('/pilot/snapshot?'+urlencode(dict(startDate=START,endDate=END,requestId='r1')), **kw)

    async def test_auth_scope_and_read(self):
        status,access = await self.request(); self.assertEqual(status,200)
        self.assertEqual(access['binding'],BINDING)
        status,data = await self.snapshot(); self.assertEqual(status,200)
        self.assertEqual(data['records'][0]['scheduledAt'],'2026-09-09T12:00:00Z')
        self.assertEqual(data['completeness'],'bounded')
        self.assertNotIn('PRIVATE',json.dumps(data)); self.assertNotIn('releaseURL',json.dumps(data))
        self.assertEqual(len(self.calls),2)
        self.assertTrue(all('Authorization: synthetic-upstream-key\r\n' in c for c in self.calls))
        self.assertNotIn('Bearer', ''.join(self.calls))
        self.assertNotIn('limit=', ''.join(self.calls))
