from pathlib import Path
import os,sys,json,subprocess,time,signal,socket,urllib.request,shutil
E=Path(__file__).resolve().parent;R=E/('browser-'+sys.argv[1]);R.mkdir(exist_ok=False)
for p in (E/'browser').iterdir():
 if p.is_file():shutil.copyfile(p,R/p.name)
A=Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1');py=str(A/'venv/bin/python3');chrome='/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
profile=R/'profile';profile.mkdir();home=R/'home';home.mkdir()
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--']
env={'PATH':'/usr/bin:/bin','HOME':str(home),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','I18N_BUILD_ROOT':str(Path(os.environ['V5_BUILD_ROOT'])),'I18N_FIXTURE_PORT':'4198'}
cmds={'fixture':base+[py,'-B',str(R/'fixture-server.py')],'chrome':base+[chrome,'--headless=new','--no-sandbox','--disable-gpu','--disable-background-networking','--disable-component-update','--no-first-run','--no-default-browser-check','--disable-sync','--metrics-recording-only','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1','--remote-debugging-port=9269','--user-data-dir='+str(profile),'about:blank'],'smoke':base+[py,'-B',str(R/'history_smoke.py')]}
for port in [4198,9269]:
 with socket.socket() as sock:
  sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',port))
(R/'PLAN.json').write_text(json.dumps({'commands':cmds,'environment':env,'scope':'task-owned outputs; all product and build read-only'},indent=2))
children=[]
def start(name):
 out=(R/(name+'.log')).open('w');p=subprocess.Popen(cmds[name],env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True);children.append((name,p,out));return p
def health(url,p):
 until=time.monotonic()+20
 while time.monotonic()<until:
  assert p.poll() is None
  try:return json.loads(urllib.request.urlopen(url,timeout=1).read())
  except Exception:time.sleep(.1)
 raise RuntimeError('health timeout '+url)
rc=None
try:
 f=start('fixture');fh=health('http://127.0.0.1:4198/__health',f);assert fh['buildExists']
 import hashlib
 build=Path(env['I18N_BUILD_ROOT']);served=[]
 for asset in sorted(build.rglob('*')):
  if not asset.is_file():continue
  path=str(asset.relative_to(build));response=urllib.request.urlopen('http://127.0.0.1:4198/'+path,timeout=10);data=response.read()
  expected=hashlib.sha256(asset.read_bytes()).hexdigest();actual=hashlib.sha256(data).hexdigest()
  served.append({'path':path,'status':response.status,'bytes':len(data),'disk_sha256':expected,'served_sha256':actual});assert expected==actual
 (R/'SERVED_ARTIFACTS.json').write_text(json.dumps({'build':str(build),'tree':fh['tree'],'files':served,'differences':0},indent=2))
 c=start('chrome');ch=health('http://127.0.0.1:9269/json/version',c)
 (R/'HEALTH.json').write_text(json.dumps({'fixture':fh,'browser':ch},indent=2))
 p=start('smoke');rc=p.wait(timeout=420)
finally:
 rows=[]
 for name,p,out in reversed(children):
  if name=='chrome' and p.poll() is None:
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:pass
  stopped=p.poll() is None
  if stopped:os.killpg(p.pid,signal.SIGTERM)
  try:code=p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);code=p.wait(timeout=10)
  out.close();rows.append({'name':name,'pid':p.pid,'exit':code,'terminated_by_task':stopped})
 remain=[4198,9269];until=time.monotonic()+5
 while remain and time.monotonic()<until:
  remain=[]
  for port in [4198,9269]:
   with socket.socket() as sock:
    if sock.connect_ex(('127.0.0.1',port))==0:remain.append(port)
  if remain:time.sleep(.05)
 (R/'TEARDOWN.json').write_text(json.dumps({'processes':rows,'remaining_ports':remain},indent=2));assert not remain
print('SMOKE_EXIT',rc);sys.exit(rc if rc is not None else 1)
