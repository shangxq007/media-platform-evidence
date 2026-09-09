"""Task-local static receiver. No API fixtures or proxy. All APIs unavailable; host provides only explicit in-memory projection."""
import http.server,json,pathlib,urllib.parse,os
from control import T,now
ROOT=pathlib.Path(os.environ['I18N_BUILD_ROOT']);E=pathlib.Path(__file__).parent
class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def record(self,status):
  u=urllib.parse.urlsplit(self.path)
  with (E/'HTTP_REQUESTS.jsonl').open('a') as f:f.write(json.dumps({'time':now(),'tree':T,'method':self.command,'path':u.path,'query':urllib.parse.parse_qs(u.query),'response_status':status,'receiver':'127.0.0.1 local fixture','forwarded':False})+'\n')
 def send_response(self,code,message=None):
  self.record(code);super().send_response(code,message)
 def do_GET(self):
  p=urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
  target=(ROOT/p.lstrip('/')).resolve()
  if not target.is_relative_to(ROOT.resolve()):return self.reply(403,{'message':'Outside bounded build root'})
  if p=='/fixture.html' and urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('workflowFixture')!=['1']:return self.reply(403,{'message':'Explicit fixture opt-in required'})
  if p=='/__health':return self.reply(200,{'fixtureServer':True,'buildExists':(ROOT/'index.html').exists(),'tree':T})
  if p.startswith('/api/'):
   return self.reply(503,{'message':'LOCAL_FIXTURE_UNCONFIGURED; no real access granted'})
  if p=='/vite.svg' and not (ROOT/'vite.svg').is_file():return self.reply(404,{'message':'historical optional favicon absent'})
  if p.startswith('/assets/') and not (ROOT/p.lstrip('/')).is_file():return self.reply(404,{'message':'missing asset'})
  if not (ROOT/p.lstrip('/')).is_file():
   # Preserve original request path in the HTTP log when serving SPA fallback.
   self.send_response(200);data=(ROOT/('fixture.html' if urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('workflowFixture')==['1'] else 'index.html')).read_bytes();self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
  return super().do_GET()
 def do_HEAD(self):
  return self.reply(405,{'message':'HEAD not supported by bounded receiver'})
 def do_POST(self):
  with (E/'MUTATION_ATTEMPTS.jsonl').open('a') as f:f.write(json.dumps({'time':now(),'tree':T,'method':self.command,'path':self.path,'response_status':403,'receiver':'127.0.0.1 mock only','forwarded':False})+'\n')
  self.reply(403,{'message':'Local fixture denies all HTTP mutations'})
 do_PUT=do_POST
 do_PATCH=do_POST
 do_DELETE=do_POST
 def reply(self,status,body):
  data=json.dumps(body).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
http.server.ThreadingHTTPServer(('127.0.0.1',int(os.environ['I18N_FIXTURE_PORT'])),Handler).serve_forever()
