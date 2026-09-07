"""Frontend UX-only fixture server. Never production/backend evidence."""
import http.server, json, pathlib, time, urllib.parse, os
from control import T,now
ROOT = pathlib.Path(os.environ['I18N_BUILD_ROOT'])
EVIDENCE = pathlib.Path(__file__).parent
REV = [dict(id=f'ux-r{i}', revisionNumber=i, parentRevisionId=None if i == 1 else 'ux-r1', source='UX_FIXTURE', message='Synthetic UX review fixture, not backend data', labels=[], authorUserId=None, createdAt='2026-09-05T00:00:00Z', isMerge=False) for i in (1, 2)]
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs): super().__init__(*args, directory=str(ROOT), **kwargs)
    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        mode_path = EVIDENCE/'fixture-mode.txt'
        if '/assets/WorkspaceCanvas-' in path and mode_path.exists() and mode_path.read_text().strip() == 'route-loading':
            time.sleep(6)
        if path == '/lifecycle-away':
            data=b'<!doctype html><title>External lifecycle fixture</title><p>Document navigation destination. No application Selection store.</p><a href="/w/ux-workspace/projects/ux-project/canvas">Return</a>'
            self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if path == '/__health':
            return self.reply(200, {'fixtureServer': True, 'buildExists': (ROOT/'index.html').exists()})
        if path.startswith('/i18n/v2026-09/'):
            mode_file = EVIDENCE/'remote-mode.txt'
            mode = mode_file.read_text().strip() if mode_file.exists() else 'success'
            with (EVIDENCE/'remote-requests.jsonl').open('a') as out:
                out.write(json.dumps({'IMPLEMENTATION_TREE':T,'VALIDATION_TIMESTAMP':now(),'COMMAND_OR_CHECK_ID':'native-http-request','RESULT':'OBSERVED','path': path, 'mode': mode, 'cookie_present': bool(self.headers.get('Cookie')), 'authorization_present': bool(self.headers.get('Authorization'))})+'\n')
            if mode == 'outage': return self.reply(503, {'fixture': 'remote unavailable'})
            if mode == 'invalid': return self.reply(200, {'schemaVersion': 999})
            if mode == 'slow': time.sleep(3)
            payload = EVIDENCE/'remote-fixtures'/path.removeprefix('/i18n/v2026-09/')
            if payload.is_file(): return self.reply(200, json.loads(payload.read_text()))
            return self.reply(404, {'fixture': 'no catalog'})
        if path.startswith('/api/'):

            mode_path = EVIDENCE/'fixture-mode.txt'
            mode = mode_path.read_text().strip() if mode_path.exists() else 'ready'
            if mode == 'loading': time.sleep(5)
            if mode == 'error': return self.reply(503, {'message': 'Deliberate UX fixture unavailable'})
            if path.endswith('/me/dashboard'):
                return self.reply(200, dict(tenantId=None, workspace=dict(id=(EVIDENCE/'fixture-workspace.txt').read_text().strip() if (EVIDENCE/'fixture-workspace.txt').exists() else 'ux-workspace', name='UX fixture workspace'), recentProjects=[dict(id='ux-project', name='UX fixture project')]))
            if path.endswith('/revisions/current'):
                return self.reply(200, dict(revisionId='ux-r2', revision=dict(revisionId='ux-r2', productId='ux-project', semanticContext=dict(timelineContentDigest='a'*64))))
            if path.endswith('/revisions/compare'):
                params=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                by_id={r['id']:r for r in REV}
                return self.reply(200, dict(fromRevision=by_id[params['from'][0]], toRevision=by_id[params['to'][0]], summary=dict(supported=True, clipsAdded=1), entityChanges=[dict(kind='CLIP', entityId='ux-clip', action='ADDED')]))
            if path.endswith('/revisions'):
                return self.reply(200, [] if mode == 'empty' else REV)
            if '/revisions/ux-r' in path:
                return self.reply(200, dict(revision=REV[1], changeSummary=dict(supported=True), patchOpCount=0))
            return self.reply(503, {'message':'No UX fixture configured; capability stays unavailable'})
        if path.startswith('/governance/agent-shell-convergence/'):
            self.directory = str(EVIDENCE.parents[1])
            return super().do_GET()
        file = ROOT/path.lstrip('/')
        if not file.is_file(): self.path='/index.html'
        return super().do_GET()
    def do_POST(self):
        with (EVIDENCE/'MUTATION_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'method':self.command,'path':self.path})+'\n')
        self.reply(403, {'message':'UX fixture server forbids all mutations'})
    do_PUT=do_POST
    do_PATCH=do_POST
    do_DELETE=do_POST
    def reply(self, status, body):
        data=json.dumps(body).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
http.server.ThreadingHTTPServer(('127.0.0.1', int(os.environ.get('I18N_FIXTURE_PORT', '4196'))), Handler).serve_forever()
