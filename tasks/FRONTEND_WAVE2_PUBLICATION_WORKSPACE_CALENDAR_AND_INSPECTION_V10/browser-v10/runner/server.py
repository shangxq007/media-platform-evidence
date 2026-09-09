import http.server,json,pathlib,urllib.parse,sys
from control import now,T
ROOT=pathlib.Path(sys.argv[1]);OUT=pathlib.Path(sys.argv[3]);fixture=sys.argv[4]=='fixture'
def rev(n):return {'id':'revision-'+str(n),'revisionNumber':n,'createdAt':'2026-01-01T00:00:00Z','source':'EXPLICIT_FIXTURE','message':'Simulated revision '+str(n)}
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def send_response(self,status,message=None):
  with (OUT/('fixture-http.jsonl' if fixture else 'ordinary-http.jsonl')).open('a') as f:f.write(json.dumps({'time':now(),'method':self.command,'path':self.path,'status':status,'forwarded':False,'fixture':fixture})+'\n')
  super().send_response(status,message)
 def reply(self,status,body):
  data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_GET(self):
  u=urllib.parse.urlsplit(self.path);p=urllib.parse.unquote(u.path)
  if p=='/__health':return self.reply(200,{'tree':T,'fixture':fixture,'root':str(ROOT),'ready':True})
  if p.startswith('/api/'):
   return self.reply(503,{'message':'NO_BACKEND_LOCAL_ONLY'})
  target=(ROOT/p.lstrip('/')).resolve()
  if not target.is_relative_to(ROOT.resolve()):return self.reply(403,{'message':'scope denied'})
  if target.is_file():return super().do_GET()
  if p.startswith('/assets/') or '.' in p.rsplit('/',1)[-1]:return self.reply(404,{'message':'missing static asset'})
  if fixture and urllib.parse.parse_qs(u.query).get('publicationFixture')!=['1']:return self.reply(403,{'message':'Explicit opt-in required'})
  data=(ROOT/('fixture.html' if fixture else 'index.html')).read_bytes();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_POST(self):return self.reply(403,{'message':'ALL_MUTATIONS_BLOCKED_NOT_ZERO_ATTEMPTS'})
 do_PUT=do_POST
 do_PATCH=do_POST
 do_DELETE=do_POST
http.server.ThreadingHTTPServer(('127.0.0.1',int(sys.argv[2])),Handler).serve_forever()