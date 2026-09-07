#!/usr/bin/env python3
"""Rerunnable focused qualification; append-only attempts and native logs."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,uuid
D=Path(__file__).resolve().parents[1]
if '--child' not in sys.argv:
 q=D/'qualification'/('attempt-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]);q.mkdir()
 hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 before={str(p):hash_file(p) for p in (D/'executor').iterdir() if p.is_file()}
 before.update({str(p):hash_file(p) for p in (D/'qualification').glob('*.py')})
 argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--child']
 with (q/'native.log').open('xb') as log:r=subprocess.run(argv,env={**os.environ,'EP19_QUALIFICATION_ROOT':str(q),'PYTHONDONTWRITEBYTECODE':'1','EP19_REQUIRE_REAL_GRADLE':'1' if '--require-real-gradle' in sys.argv else '0'},stdout=log,stderr=subprocess.STDOUT,cwd=D)
 h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 drift=[p for p,v in before.items() if not Path(p).is_file() or h(Path(p))!=v]
 wrapper_exit=r.returncode or int(bool(drift))
 process={'source_drift':drift,'source_before':before,'wrapper_exit':wrapper_exit,'argv':argv,'native_exit':r.returncode,'raw_log':str(q/'native.log'),'log_sha256':h(q/'native.log'),'product_gate_execution':False}
 (q/'process.json').write_text(json.dumps(process,indent=2)+'\n')
 helpers={str(p):h(p) for p in (D/'executor').iterdir() if p.is_file()}
 files=[p for root in [q,D/'executor',D/'tools'] for p in root.rglob('*') if p.is_file() and not p.is_symlink()]
 for run in (D/'outputs/continuation-runs').glob('qualification-'+q.name+'*'):
  files += [p for p in run.glob('*.json') if p.is_file()]
  files += [p for p in (run/'sources').glob('*-clone.native.log') if p.is_file()]
  files += [p for p in (run/'runtime/gates').rglob('*') if p.is_file() and not p.is_symlink()]
 files += [D/'qualification/run.py',D/'qualification/cases.py',D/'qualification/red.py',D/'qualification/defect_c.py']
 # Native/fixture evidence and executable source closure; no historical results relabelled.
 gradle_blocked=bool(list(q.rglob('REAL_GRADLE_BLOCKED.json')))
 real_graphs=[json.loads(p.read_text()) for p in q.glob('test_B_real_gradle_generated_no_source_and_seal-*/run/runtime/gates/COMPILE/compile-graph.json')]
 gradle_status='PASS' if wrapper_exit==0 and real_graphs and all(not g.get('synthetic_fixture') for g in real_graphs) else ('BLOCKED_RUNTIME_SOCKET_DENIED' if gradle_blocked else 'NOT_QUALIFIED')
 qualification={'real_gradle_instrumentation':gradle_status,'schema':'ep19-output-corrections-v2','result':'PASS' if wrapper_exit==0 else 'FAIL','helpers':helpers,'dependencies':{str(p):h(p) for p in files},'qualification_program':str(D/'qualification/run.py'),'raw_log':str(q/'native.log'),'process_receipt':str(q/'process.json'),'result_receipt':str(q/'results.json'),'product_gate_execution':False,'independent_review':'REQUIRED/PENDING','areas':['run_isolation','artifact_copy','compile_completeness','vite_closure','packaging'],'formal_runtime_qualification':'NOT_RUN_PARENT_REQUIRED'}
 (q/'QUALIFICATION.json').write_text(json.dumps(qualification,indent=2)+'\n')
 if '--receipt-pointer' in sys.argv:
  pointer=Path(sys.argv[sys.argv.index('--receipt-pointer')+1]).absolute()
  if pointer.resolve()!=pointer or not pointer.is_relative_to(D):raise RuntimeError('POINTER_SCOPE')
  with pointer.open('x') as f:json.dump({'qualification':str(q/'QUALIFICATION.json'),'native_exit':r.returncode},f,indent=2)
 print(q);print((q/'native.log').read_text()[-9000:]);raise SystemExit(wrapper_exit)
import unittest
sys.path.insert(0,str(D/'executor'));sys.path.insert(0,str(D/'qualification'))
import cases, test_continuation, defect_c
q=Path(os.environ['EP19_QUALIFICATION_ROOT']);test_continuation.Q=q/'original-focused';test_continuation.Q.mkdir()
class Result(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.cases=[]
 def addSuccess(self,t):super().addSuccess(t);self.cases.append({'case':t.id(),'expected':t.shortDescription() or 'Original focused control passes','actual':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);self.cases.append({'case':t.id(),'expected':t.shortDescription() or 'PASS','actual':'FAIL','detail':self._exc_info_to_string(e,t)})
 def addError(self,t,e):super().addError(t,e);self.cases.append({'case':t.id(),'expected':t.shortDescription() or 'PASS','actual':'ERROR','detail':self._exc_info_to_string(e,t)})
 def addSubTest(self,t,sub,e):
  super().addSubTest(t,sub,e);self.cases.append({'case':sub.id(),'expected':'Control satisfies stated acceptance/rejection','actual':'PASS' if e is None else 'FAIL','detail':None if e is None else self._exc_info_to_string(e,t)})
suite=unittest.defaultTestLoader.loadTestsFromTestCase(cases.Cases)
suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(defect_c.SchemeControls))
# Existing original packaging and preservation controls, strictly synthetic fixtures.
for name in unittest.defaultTestLoader.getTestCaseNames(test_continuation.Controls):
 if name.startswith('test_packaging_') or name in ['test_primary_transient_index_write_strict','test_instruction_runtime_metadata_drift_rejects','test_shadow_permitted_actual_observe_acceptance','test_shadow_missing_reconciler_rejects','test_shadow_semantic_delta_rejects','test_backend_untagged_detached_child_remains_observed','test_fresh_native_failure_reject','test_new_unexpected_missing_stays_failure']:
  suite.addTest(test_continuation.Controls(name))
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
(q/'results.json').write_text(json.dumps({'result':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'cases':r.cases,'product_gate_execution':False},indent=2)+'\n')
raise SystemExit(not r.wasSuccessful())
