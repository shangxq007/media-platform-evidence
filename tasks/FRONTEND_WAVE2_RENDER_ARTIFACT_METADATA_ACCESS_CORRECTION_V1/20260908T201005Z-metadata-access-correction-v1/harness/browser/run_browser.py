from pathlib import Path
import os,sys,json,subprocess,time,signal,socket,urllib.request,shutil
E=Path(__file__).resolve().parent
import re,hashlib
assert len(sys.argv)==2 and re.fullmatch(r'[a-zA-Z0-9_-]+',sys.argv[1]), 'Unique attempt label required'
R=E/('browser-'+sys.argv[1]);R.mkdir(exist_ok=False)
inputs=json.loads((E/'FIXTURE_HOST_INPUTS.json').read_text())
assert inputs['FINAL_EXACT_IMPLEMENTATION_TREE']==(E.parent/'final-validation-01/FINAL_TREE.txt').read_text().strip()
S=Path(inputs['snapshot'])
for row in inputs['files']: assert hashlib.sha256((S/row['path']).read_bytes()).hexdigest()==row['sha256'], row['path']
assert [str(f.relative_to(S)) for f in sorted((S/'src').rglob('*')) if f.is_file()]==[r['path'] for r in inputs['files']], 'Snapshot source census changed'
assert (E/'build/index.html').is_file() and (E/'build/fixture.html').is_file(), 'Parent must build both entries'
binding=json.loads((E/'BUILD_BINDING.json').read_text())
assert binding['FINAL_EXACT_IMPLEMENTATION_TREE']==inputs['FINAL_EXACT_IMPLEMENTATION_TREE']
assert binding['fixture_input_sha256']==hashlib.sha256((E/'FIXTURE_HOST_INPUTS.json').read_bytes()).hexdigest()
for kind,root in [('host',E/'fixture-host'),('build',E/'build')]:
 actual=[{'path':str(f.relative_to(root)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(root.rglob('*')) if f.is_file() and 'node_modules' not in f.parts]
 assert actual==binding[kind],kind+' changed after build binding'
shutil.copyfile(E/'BUILD_BINDING.json',R/'BUILD_BINDING.json')
shutil.copyfile(E/'FIXTURE_HOST_INPUTS.json',R/'FIXTURE_HOST_INPUTS.json')

for p in (E/'browser').iterdir():
 if p.is_file():shutil.copyfile(p,R/p.name)
(R/'TREE_BINDING.json').write_text(json.dumps({'FINAL_EXACT_IMPLEMENTATION_TREE':(E.parent/'final-validation-01/FINAL_TREE.txt').read_text().strip()}))
A=Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1');py=str(A/'venv/bin/python3');chrome='/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
profile=R/'profile';profile.mkdir();home=R/'home';home.mkdir()
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--']
env={'PATH':'/usr/bin:/bin','HOME':str(home),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','I18N_BUILD_ROOT':str(E/'build'),'I18N_FIXTURE_PORT':'4198'}
cmds={'fixture':base+[py,'-B',str(R/'fixture-server.py')],'chrome':base+[chrome,'--headless=new','--no-sandbox','--disable-gpu','--disable-background-networking','--disable-component-update','--no-first-run','--no-default-browser-check','--disable-sync','--metrics-recording-only','--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1','--remote-debugging-port=9269','--user-data-dir='+str(profile),'about:blank'],'smoke':base+[py,'-B',str(R/'render_smoke.py')]}
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
  path=str(asset.relative_to(build));url='http://127.0.0.1:4198/'+urllib.parse.quote(path)+('?metadataFixture=1' if path=='fixture.html' else '');response=urllib.request.urlopen(url,timeout=10);data=response.read()
  expected=hashlib.sha256(asset.read_bytes()).hexdigest();actual=hashlib.sha256(data).hexdigest()
  served.append({'path':path,'status':response.status,'bytes':len(data),'disk_sha256':expected,'served_sha256':actual});assert expected==actual
 (R/'SERVED_ARTIFACTS.json').write_text(json.dumps({'build':str(build),'tree':fh['tree'],'files':served,'differences':0},indent=2))
 c=start('chrome');ch=health('http://127.0.0.1:9269/json/version',c)
 (R/'HEALTH.json').write_text(json.dumps({'fixture':fh,'browser':ch},indent=2))
 p=start('smoke');rc=p.wait(timeout=600)
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
