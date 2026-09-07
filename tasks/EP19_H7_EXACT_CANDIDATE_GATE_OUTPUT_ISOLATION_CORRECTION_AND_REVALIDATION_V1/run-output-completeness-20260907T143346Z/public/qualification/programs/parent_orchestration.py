#!/usr/bin/env python3
"""Append-only parent qualification/cache/decision orchestration. Never runs gates.

Adapted from owner-clarified-execution-20260907T1120Z/runtime-completion-1/
parent_orchestration.py and its native runtime/Lean source evidence.
"""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,time
D=Path(__file__).resolve().parents[1];sys.path.insert(0,str(D/'executor'))
import coverage,execution,runner
h=coverage.digest;put=coverage.put
SOURCE=execution.O/'owner-clarified-execution-20260907T1120Z'
MATERIALIZATION=SOURCE/'LEAN_CACHE_MATERIALIZATION.json'
AREAS=('collector','coverage','shadow','packaging','freshness','launch','dependency_preparation')

def load(p):return json.loads(Path(p).read_text())
def helpers():return coverage.seal(coverage.local_imports()[0])
def programs():return coverage.seal([p for p in (D/'qualification').glob('*.py')])
def exclusive(p):
 p=Path(p).absolute()
 if p.resolve()!=p or not p.is_relative_to(D):raise RuntimeError('OUTPUT_SCOPE')
 return p

def regular_inventory(root):
 root=Path(root)
 if root.resolve()!=root:raise RuntimeError('CACHE_ROOT_LINK')
 rows={}
 for p in root.rglob('*'):
  if p.is_symlink() or not (p.is_file() or p.is_dir()):raise RuntimeError('CACHE_LINK_OR_SPECIAL '+str(p))
  if p.is_file():
   if p.stat().st_nlink!=1:raise RuntimeError('CACHE_HARDLINK '+str(p))
   rows[str(p.relative_to(root))]=h(p)
 return rows

def copy_lean(run):
 run=exclusive(run)
 if (run/'baseline.json').exists():raise RuntimeError('CACHE_MUST_PRECEDE_BASELINE')
 mat=load(MATERIALIZATION);source=Path(mat['destination']);expected={x['path']:x['destination_sha256'] for x in mat['mapping']}
 if len(expected)!=4617 or any(x['source_sha256']!=x['destination_sha256'] for x in mat['mapping']):raise RuntimeError('LEAN_MATERIALIZATION_BINDING')
 if regular_inventory(source)!=expected:raise RuntimeError('LEAN_SOURCE_CHANGED')
 dest=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux'
 if dest.exists():raise RuntimeError('CACHE_ALREADY_EXISTS_NEW_RUN_REQUIRED')
 shutil.copytree(source,dest,symlinks=True)
 if regular_inventory(dest)!=expected:raise RuntimeError('LEAN_COPY_CHANGED')
 put(run/'lean-cache-preparation.json',{'source':str(source),'destination':str(dest),'files':expected,'materialization_sha256':h(MATERIALIZATION),'archive_reverified':False,'independent_byte_copy':True})
 return dest

def native(q,name,argv,env=None):
 before=helpers();sources=programs();log=q/(name+'.log');start=time.time();rc=None;error=None
 with log.open('xb') as f:
  try:rc=subprocess.run(argv,cwd=D,env=env,stdout=f,stderr=subprocess.STDOUT).returncode
  except OSError as ex:error=str(ex)
 outputs=q/('controls-run' if name=='controls' else name+'-runtime')
 evidence=[log]+([p for p in outputs.rglob('*') if p.is_file() and not p.is_symlink()] if outputs.exists() else [])
 if name=='focused' and (q/'focused-pointer.json').exists():
  evidence += [q/'focused-pointer.json',Path(load(q/'focused-pointer.json')['qualification'])]
 receipt={'evidence':coverage.seal(evidence),'argv':list(map(str,argv)),'native_exit':rc,'error':error,'raw_log':str(log),'log_sha256':h(log),'start':start,'end':time.time(),'helpers':before,'programs':sources,'product_gate_execution':False}
 drift=before!=helpers() or sources!=programs();receipt['source_drift']=drift
 put(q/(name+'-process.json'),receipt)
 if rc!=0 or drift:raise RuntimeError(name+' failed; native evidence retained at '+str(log))
 return receipt

def validate_stage(q,name):
 p=q/(name+'-process.json');r=load(p)
 if r.get('native_exit')!=0 or r.get('source_drift') is not False:raise RuntimeError('STAGE_NOT_PASS '+name)
 if r['helpers']!=helpers() or r['programs']!=programs():raise RuntimeError('CHANGED_HELPER_OR_PROGRAM_EVIDENCE '+name)
 if h(r['raw_log'])!=r['log_sha256']:raise RuntimeError('STAGE_LOG_CHANGED '+name)
 if not r.get('evidence'):raise RuntimeError('STAGE_EVIDENCE_MISSING '+name)
 coverage.check_seal(r['evidence'])
 return r

def assemble(q):
 # No legacy PASS labels or evidence are transplanted onto changed helpers.
 for stage in ('focused','controls','frontend','lean','formal'):validate_stage(q,stage)
 focused_path=Path(load(q/'focused-pointer.json')['qualification']);coverage.qualification_inputs(focused_path);focused=load(focused_path)
 if focused.get('real_gradle_instrumentation')!='PASS':raise RuntimeError('REAL_GRADLE_NOT_QUALIFIED')
 controls=load(q/'controls-run/results.json')
 if controls.get('result')!='PASS' or controls.get('skipped')!=0:raise RuntimeError('CONTROLS_NOT_PASS')
 for area in AREAS:
  evidence=controls['areas'].get(area,{})
  if evidence.get('result')!='PASS' or not evidence.get('cases') or any(x['actual']!='PASS' for x in evidence['cases']):raise RuntimeError('AREA_NOT_EXERCISED '+area)
 for area in ('frontend','lean','formal'):
  if load(q/(area+'-runtime/RESULT.json')).get('result')!='PASS':raise RuntimeError('RUNTIME_NOT_PASS '+area)
 front=load(q/'frontend-runtime/RESULT.json');lean=load(q/'lean-runtime/RESULT.json')
 if any(front.get(k)!='PASS' for k in ('readonly','private_pid','xdg_runtime')) or lean.get('strict_collector')!='PASS':raise RuntimeError('INCOMPLETE_RUNTIME')
 # Include all fixture evidence except explicitly recorded negative-fixture links.
 paths=[p for p in q.rglob('*') if p.is_file() and not p.is_symlink()]
 paths += [focused_path,MATERIALIZATION,*map(Path,programs())]
 # Actual synthetic launch gates live in exclusive executor run namespaces.
 for f in (q/'controls-run/controls/launch-data').glob('test_*/engineering-launch.json'):
  run=runner.runpath(load(f)['run_id']);paths += [p for p in run.rglob('*') if p.is_file() and not p.is_symlink()]
 links={str(p):str(p.readlink()) for p in q.rglob('*') if p.is_symlink()}
 put(q/'fixture-links.json',{'negative_fixture_links_not_followed':links});paths.append(q/'fixture-links.json')
 deps={**focused['dependencies'],**coverage.seal(paths),**helpers()}
 raw=q/'controls.log';process=q/'controls-process.json';result=q/'controls-run/results.json'
 receipt={**focused,'schema':'ep19-output-corrections-v2','helpers':helpers(),'dependencies':deps,
  'qualification_program':str(Path(__file__).resolve()),'raw_log':str(raw),'process_receipt':str(process),'result_receipt':str(result),
  **{area:'PASS' for area in AREAS},'frontend_boundary':'PASS','formal_boundary':'PASS','lean_runtime':'PASS',
  'formal_boundary_receipt':str(q/'formal-runtime/RESULT.json'),'lean_runtime_receipt':str(q/'lean-runtime/RESULT.json'),
  'formal_runtime_qualification':'PASS_SYNTHETIC_NATIVE_ONLY','runtime_area_receipts':{area:str(q/(area+'-runtime/RESULT.json')) for area in ('frontend','lean','formal')},
  'focused_qualification':str(focused_path),'reuse':[],'independent_review':'REQUIRED/PENDING','product_gate_execution':False}
 if not coverage.formal_boundary_qualified(receipt):raise RuntimeError('FORMAL_BOUNDARY_INCOMPLETE')
 put(q/'QUALIFICATION.json',receipt);coverage.qualification_inputs(q/'QUALIFICATION.json')
 print(q/'QUALIFICATION.json')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['init','focused','controls','frontend','lean','formal','assemble','cache','decision']);p.add_argument('--attempt',type=Path);p.add_argument('--run-id');a=p.parse_args()
 if a.stage in ('cache','decision'):
  if not a.run_id:p.error('--run-id required')
  run=runner.runpath(a.run_id)
  if not (run/'prepare.json').is_file():raise RuntimeError('RUN_NOT_PREPARED')
  if a.stage=='cache':print(copy_lean(run));return 0
  runner.owner_authorization();current=runner.preflight(run,write=False);recorded=load(run/'preflight.json')
  if current['result']!='ENGINEERING_READY' or recorded['result']!='ENGINEERING_READY' or recorded['engineering_blockers']!=[]:raise RuntimeError('NO_LAUNCH_DECISION '+repr(current['engineering_blockers']))
  for k,v in {'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,'base':runner.BASE}.items():
   if recorded[k]!=v:raise RuntimeError('RECORDED_PREFLIGHT_IDENTITY')
  decision={'engineering_execution_authorization':'OWNER_AUTHORIZED','owner_decision_sha256':runner.OWNER_SHA256,'independent_review':'PENDING',**runner.REVIEW_STATES,'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,'base':runner.BASE,'seal_sha256':h(run/'seal.json'),'preflight_sha256':h(run/'preflight.json')}
  put(run/'engineering-launch.json',decision);print(run/'engineering-launch.json');return 0
 if not a.attempt:p.error('--attempt required')
 q=exclusive(a.attempt)
 if not q.is_relative_to(D/'qualification'):raise RuntimeError('ATTEMPT_SCOPE')
 if a.stage=='init':
  q.mkdir();put(q/'INIT.json',{'helpers':helpers(),'programs':programs(),'independent_review':'REQUIRED/PENDING','product_gate_execution':False});return 0
 init=load(q/'INIT.json')
 if init['helpers']!=helpers() or init['programs']!=programs():raise RuntimeError('SOURCE_CHANGED_NEW_ATTEMPT_REQUIRED')
 if a.stage=='assemble':assemble(q);return 0
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 if a.stage=='focused':argv=[sys.executable,'-B',str(D/'qualification/run.py'),'--require-real-gradle','--receipt-pointer',str(q/'focused-pointer.json')]
 elif a.stage=='controls':
  dest=q/'controls-run';dest.mkdir();env['EP19_QUALIFICATION_ROOT']=str(dest);argv=[sys.executable,'-B',str(D/'qualification/runtime_suite.py')]
 else:argv=[sys.executable,'-B',str(D/'qualification/runtime_probe.py'),a.stage,'--output',str(q/(a.stage+'-runtime'))]
 native(q,a.stage,argv,env);print(a.stage+': native qualification completed');return 0
if __name__=='__main__':raise SystemExit(main())
