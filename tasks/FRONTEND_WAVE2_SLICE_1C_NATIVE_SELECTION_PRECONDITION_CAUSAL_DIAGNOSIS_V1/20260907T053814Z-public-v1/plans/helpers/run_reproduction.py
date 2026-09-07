from pathlib import Path
import os,sys,json,subprocess,time,signal,socket,urllib.request,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];P=ROOT.parent/'FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1';L=ROOT.parent/'FRONTEND_WAVE2_SLICE_1C_FOUNDATIONPAGES_LINT_CORRECTION_AND_VALIDATION_CONTINUATION_V1'
name=sys.argv[1];assert name in ['R1','R2','R3'];R=ROOT/'runs'/name
assert not (R/'LAUNCH_STARTED.json').exists(),'No retry under same reproduction identity'
R.mkdir(exist_ok=True);(R/'home').mkdir(exist_ok=True);profile=ROOT/'profile'/name;profile.mkdir()
pins=json.loads((P/'BROWSER_INPUT_SEAL.json').read_text())['harness']
for f,h in pins.items():
 assert hashlib.sha256((P/'harness'/f).read_bytes()).hexdigest()==h
 shutil.copyfile(P/'harness'/f,R/f)
py=str(P/'venv/bin/python3');chrome='[LOCAL_BROWSER_CACHE]/chromium-1228/chrome-linux64/chrome'
env={'PATH':'/usr/local/bin:/usr/bin:/bin','HOME':str(R/'home'),'LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','GIT_OPTIONAL_LOCKS':'0','I18N_BUILD_ROOT':str(L/'build'),'I18N_FIXTURE_PORT':'4196'}
base=['/usr/bin/bwrap','--die-with-parent','--ro-bind','/','/','--bind',str(R),str(R),'--bind',str(profile),str(profile)]
for f in pins:base+=['--ro-bind',str(R/f),str(R/f)]
base+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir',str(R),'--']
commands={'containment':base+[py,'-B','-c',"import os,json;print(json.dumps({p:bool(os.statvfs(p).f_flag & os.ST_RDONLY) for p in "+repr([str(P),str(P/'venv'),str(L/'snapshot'),str(L/'build'),'[LOCAL_PRODUCT_REPOSITORY]','[LOCAL_FRONTEND_WORKTREE]',str(R/'native_routes.py')])+"}))"], 'fixture':base+[py,'-B',str(R/'fixture-server.py')], 'chrome':base+[chrome,'--headless=new','--no-sandbox','--disable-gpu','--remote-debugging-port=9267','--user-data-dir='+str(profile),'about:blank'], 'diagnostic':base+[py,'-B',str(ROOT/'helpers/bounded_driver.py'),str(R)]}
plan={'run':name,'commands':commands,'environment':env,'ports':[4196,9267],'expected_diagnostic_exit':1,'write_scope':[str(R),str(profile),'private /tmp'],'protected':'root read-only except task run/profile; frozen copied harness files individually read-only','process_control':'new session/process group per child; SIGTERM and wait only owned Popen process groups; fallback kill only after timeout','input_semantics':'unchanged selected() through inherited Browser.click()','checks_allowed':0,'helpers':{str(q.relative_to(ROOT)):hashlib.sha256(q.read_bytes()).hexdigest() for q in (ROOT/'helpers').iterdir() if q.is_file()}}
(R/'prospective-plan.json').write_text(json.dumps(plan,indent=2))
listeners=subprocess.check_output(['ss','-ltnp']);(R/'listeners-before.txt').write_bytes(listeners)
for port in [4196,9267]:
 with socket.socket() as s:s.bind(('127.0.0.1',port))
proof=subprocess.run(commands['containment'],env=env,capture_output=True,text=True);(R/'containment.txt').write_text(proof.stdout+proof.stderr);assert proof.returncode==0 and all(json.loads(proof.stdout).values()),proof
version=subprocess.check_output([chrome,'--version'],env=env,text=True);(R/'chrome-version.txt').write_text(version);assert '149.0.7827.55' in version
(R/'LAUNCH_STARTED.json').write_text(json.dumps({'time':time.time(),'owner_pid':os.getpid(),'run':name}))
children=[];receipts=[]
def launch(label):
 f=(R/(label+'.log')).open('w');p=subprocess.Popen(commands[label],env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);children.append((label,p,f));receipts.append({'label':label,'pid':p.pid,'pgid':os.getpgid(p.pid),'start':time.time(),'argv':commands[label]});return p
def health(url,proc):
 end=time.monotonic()+15
 while time.monotonic()<end:
  assert proc.poll() is None,('daemon exited',proc.returncode)
  try:return json.loads(urllib.request.urlopen(url,timeout=1).read())
  except Exception:time.sleep(.1)
 raise RuntimeError('health timeout '+url)
try:
 fixture=launch('fixture');fh=health('http://127.0.0.1:4196/__health',fixture)
 browser=launch('chrome');bh=health('http://127.0.0.1:9267/json/version',browser)
 (R/'health.json').write_text(json.dumps({'fixture':fh,'browser':bh},indent=2));assert bh['Browser']=='Chrome/149.0.7827.55'
 proc=launch('diagnostic');rc=proc.wait(timeout=60);receipts[-1].update(exit=rc,end=time.time());print(name,'DIAGNOSTIC_EXIT',rc)
finally:
 teardown=[]
 for label,proc,f in reversed(children):
  terminated=False
  if proc.poll() is None:
   os.killpg(proc.pid,signal.SIGTERM);terminated=True
  try:code=proc.wait(timeout=15)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);code=proc.wait(timeout=10)
  f.close();teardown.append({'label':label,'pid':proc.pid,'exit':code,'SIGTERM_issued':terminated,'waited':True,'time':time.time()})
 (R/'process-receipts.json').write_text(json.dumps(receipts,indent=2));(R/'teardown.json').write_text(json.dumps(teardown,indent=2));(R/'listeners-after.txt').write_bytes(subprocess.check_output(['ss','-ltnp']))
 remaining=[]
 for port in [4196,9267]:
  with socket.socket() as s:
   if s.connect_ex(('127.0.0.1',port))==0:remaining.append(port)
 (R/'port-cleanup.json').write_text(json.dumps({'remaining':remaining,'count':len(remaining)}));assert not remaining
