from pathlib import Path
import os,sys,json,subprocess,time,signal,socket,urllib.request,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];A=ROOT.parent/'FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1';name=sys.argv[1];assert name in ['click','routes','lifecycle','supplement'];R=ROOT/'native'/name;R.mkdir(exist_ok=False);profile=R/'profile';profile.mkdir();(R/'home').mkdir()
for p in (ROOT/'harness').iterdir():
 if p.is_file():shutil.copyfile(p,R/p.name)
py=str(A/'venv/bin/python3');chrome='[LOCAL_HOME]/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome'
assert '149.0.7827.55' in subprocess.check_output([chrome,'--version']).decode()
env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(R/'home'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','GIT_OPTIONAL_LOCKS':'0','I18N_BUILD_ROOT':str(ROOT/'build'),'I18N_FIXTURE_PORT':'4196'}
base=['bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R)]
for p in (ROOT/'harness').iterdir():
 if p.is_file():base+=['--ro-bind',str(R/p.name),str(R/p.name)]
base+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--']
driver=[str(ROOT/'helpers/native_click_v1.py'),str(R)] if name=='click' else [str(ROOT/'helpers/native_supplement_v1.py'),str(R)] if name=='supplement' else [str(R/('native_routes.py' if name=='routes' else 'native_lifecycle.py'))]
commands={'fixture':base+[py,'-B',str(R/'fixture-server.py')],'chrome':base+[chrome,'--headless=new','--no-sandbox','--disable-gpu','--remote-debugging-port=9267','--user-data-dir='+str(profile),'about:blank'],'native':base+[py,'-B',*driver]}
(R/'PLAN.json').write_text(json.dumps({'commands':commands,'environment':env,'expected_exit':0,'write_scope':[str(R),'private tmp'],'helpers':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'helpers').iterdir() if p.is_file()},'no_backend_ref_invariant':True},indent=2))
for port in [4196,9267]:
 with socket.socket() as sock:sock.bind(('127.0.0.1',port))
proof=subprocess.check_output(base+[py,'-B','-c','import os,json;print(json.dumps({p:bool(os.statvfs(p).f_flag&os.ST_RDONLY) for p in '+repr([str(ROOT/'snapshot'),str(ROOT/'build'),str(A),'[LOCAL_FRONTEND_WORKTREE]'])+'}))'],env=env).decode();(R/'CONTAINMENT.json').write_text(proof);assert all(json.loads(proof).values())
children=[];rows=[]
def start(label):
 out=(R/(label+'.log')).open('w');p=subprocess.Popen(commands[label],env=env,stdout=out,stderr=subprocess.STDOUT,start_new_session=True);children.append((label,p,out));return p
def health(url,p):
 until=time.monotonic()+15
 while time.monotonic()<until:
  assert p.poll() is None
  try:return json.loads(urllib.request.urlopen(url,timeout=1).read())
  except Exception:time.sleep(.1)
 raise RuntimeError('task daemon health timeout')
rc=None
try:
 f=start('fixture');fh=health('http://127.0.0.1:4196/__health',f);b=start('chrome');bh=health('http://127.0.0.1:9267/json/version',b);assert bh['Browser']=='Chrome/149.0.7827.55';(R/'HEALTH.json').write_text(json.dumps({'fixture':fh,'browser':bh},indent=2));p=start('native');rc=p.wait(timeout=180);print(name,'NATIVE_EXIT',rc)
finally:
 for label,p,out in reversed(children):
  terminated=p.poll() is None
  if terminated:os.killpg(p.pid,signal.SIGTERM)
  try:c=p.wait(timeout=15)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);c=p.wait(timeout=10)
  out.close();rows.append({'label':label,'pid':p.pid,'exit':c,'terminated_by_task':terminated,'waited':True})
 remaining=[]
 for port in [4196,9267]:
  with socket.socket() as sock:
   if sock.connect_ex(('127.0.0.1',port))==0:remaining.append(port)
 (R/'TEARDOWN.json').write_text(json.dumps({'processes':rows,'remaining_ports':remaining,'native_exit':rc},indent=2));assert not remaining
