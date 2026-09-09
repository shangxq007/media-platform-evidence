from pathlib import Path
import subprocess,json,datetime,sys,os,socket,time,urllib.request,hashlib,signal
R=Path(__file__).resolve().parent;O=R/sys.argv[1];O.mkdir(exist_ok=False)
py='/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1/venv/bin/python3'
chrome='/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--']
env={'PATH':'/usr/bin:/bin','HOME':str(O/'home'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','V9_RUN_DIR':str(O)}
(O/'home').mkdir();children=[];commands=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def start(name,args):
 cmd=base+args;f=(O/(name+'.log')).open('w');row={'name':name,'argv':cmd,'start':now()};p=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);row['pid']=p.pid;children.append((p,f,row));commands.append(row);return p
def health(url,p):
 end=time.monotonic()+30
 while time.monotonic()<end:
  assert p.poll() is None
  try:return json.loads(urllib.request.urlopen(url,timeout=1).read())
  except Exception:time.sleep(.1)
 raise RuntimeError('health failed')
for port in [4200,4201,9279]:
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);s.bind(('127.0.0.1',port))
rc=1
try:
 served=[]
 for name,port,build in [('fixture',4200,R/'build-continuation-01'),('ordinary',4201,R.parent/'validation-02/build')]:
  p=start(name,[py,'-B',str(R/'server.py'),str(build),str(port),str(O),name]);health('http://127.0.0.1:'+str(port)+'/__health',p)
  for a in sorted(build.rglob('*')):
   if not a.is_file():continue
   rel=str(a.relative_to(build));data=urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/'+rel).read();disk=hashlib.sha256(a.read_bytes()).hexdigest();wire=hashlib.sha256(data).hexdigest();served.append({'build':name,'path':rel,'bytes':len(data),'disk_sha256':disk,'served_sha256':wire});assert disk==wire
 (O/'SERVED_MANIFEST.json').write_text(json.dumps(served,indent=2))
 c=start('chrome',[chrome,'--headless=new','--no-sandbox','--disable-gpu','--disable-background-networking','--disable-component-update','--no-first-run','--no-default-browser-check','--disable-sync','--metrics-recording-only','--proxy-server=http://127.0.0.1:9','--proxy-bypass-list=127.0.0.1','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1','--remote-debugging-port=9279','--user-data-dir='+str(O/'profile'),'about:blank'])
 (O/'CHROME_VERSION.json').write_text(json.dumps(health('http://127.0.0.1:9279/json/version',c),indent=2))
 p=start('tests',[py,'-B',str(R/sys.argv[2])]);rc=p.wait(timeout=1200)
finally:
 for p,f,row in reversed(children):
  running=p.poll() is None
  if running:os.killpg(p.pid,signal.SIGTERM)
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=10)
  f.close();row.update(end=now(),exit=p.returncode,terminated_for_teardown=running)
 (O/'COMMANDS.json').write_text(json.dumps(commands,indent=2))
 time.sleep(.5)
 remain=[]
 for port in [4200,4201,9279]:
  with socket.socket() as s:
   if s.connect_ex(('127.0.0.1',port))==0:remain.append(port)
 (O/'TEARDOWN.json').write_text(json.dumps({'remaining_ports':remain,'children_exited':all(p.poll() is not None for p,_,_ in children)},indent=2))
 assert not remain
print('NATIVE_EXIT',rc);sys.exit(rc)
