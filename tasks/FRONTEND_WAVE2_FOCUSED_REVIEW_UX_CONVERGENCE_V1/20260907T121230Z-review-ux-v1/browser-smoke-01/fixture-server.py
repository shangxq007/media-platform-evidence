"""Bounded Review-only mock HTTP; no backend or notification endpoints."""
import http.server,json,pathlib,urllib.parse,os
from control import T,now
ROOT=pathlib.Path(os.environ['I18N_BUILD_ROOT']);E=pathlib.Path(__file__).parent
REV=[dict(id='review-'+str(i)+'-'+'x'*44,revisionNumber=i,parentRevisionId=None,source='MOCK_REVIEW',message=('Opening edit — ' if i==1 else 'Refine pacing — ')+('Long projected revision label '*5),labels=['Synthetic read-only fixture'],authorUserId=None,createdAt='2026-09-07T10:00:00Z',isMerge=False) for i in (1,2,3)]
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def do_GET(self):
  u=urllib.parse.urlsplit(self.path);p=u.path
  if p=='/__health':return self.reply(200,{'fixtureServer':True,'buildExists':(ROOT/'index.html').exists(),'tree':T})
  if p.startswith('/api/'):
   mode=(E/'fixture-mode.txt').read_text().strip() if (E/'fixture-mode.txt').exists() else 'ready'
   with (E/'HTTP_REQUESTS.jsonl').open('a') as f:f.write(json.dumps({'time':now(),'tree':T,'method':'GET','path':p,'query':urllib.parse.parse_qs(u.query),'mode':mode})+'\n')
   if p.endswith('/me/dashboard'):return self.reply(200,dict(tenantId=None,workspace=dict(id='ux-workspace',name='Synthetic workspace'),recentProjects=[dict(id='ux-project',name='Synthetic review film')]))
   if p.endswith('/revisions/compare'):
    if mode=='unavailable':return self.reply(503,{'message':'MOCK_SERVER_UNAVAILABLE: comparison service offline'})
    if mode=='denied':return self.reply(403,{'message':'MOCK_SERVER_DENIED: no revision read access'})
    q=urllib.parse.parse_qs(u.query);m={r['id']:r for r in REV}
    if q.get('from',[''])[0] not in m or q.get('to',[''])[0] not in m:return self.reply(422,{'message':'MOCK_INVALID_PAIR'})
    summary=dict(supported=mode!='unsupported',tracksAdded=0,tracksRemoved=0,tracksModified=1,clipsAdded=1,clipsRemoved=0,clipsModified=0,assetsAdded=1,assetsRemoved=0)
    entities=[dict(kind='CLIP',entityId='fixture-added-clip-'+'L'*88,action='ADDED'),dict(kind='TRACK',entityId='fixture-modified-track',action='MODIFIED')]
    if mode in ('empty','unsupported'):summary={k:(False if k=='supported' else 0) for k in summary};summary['supported']=mode=='empty';entities=[]
    return self.reply(200,dict(fromRevision=m[q['from'][0]],toRevision=m[q['to'][0]],summary=summary,entityChanges=entities))
   if p.endswith('/revisions'):return self.reply(200,REV)
   return self.reply(503,{'message':'MOCK_UNCONFIGURED_READ; no capability is granted'})
  if p.startswith('/assets/') and not (ROOT/p.lstrip('/')).is_file():return self.reply(404,{'message':'missing build asset'})
  if not (ROOT/p.lstrip('/')).is_file():self.path='/index.html'
  return super().do_GET()
 def do_POST(self):
  with (E/'MUTATION_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'method':self.command,'path':self.path})+'\n')
  self.reply(403,{'message':'Mock fixture forbids mutations'})
 do_PUT=do_POST
 do_PATCH=do_POST
 do_DELETE=do_POST
 def reply(self,status,body):
  data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
http.server.ThreadingHTTPServer(('127.0.0.1',int(os.environ['I18N_FIXTURE_PORT'])),Handler).serve_forever()
