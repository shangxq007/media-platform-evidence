"""Fresh broader synthetic controls against the current executor; no evidence reuse."""
from pathlib import Path
import json,os,sys,unittest
D=Path(__file__).resolve().parents[1];sys.path.insert(0,str(D/'executor'))
import coverage
Q=Path(os.environ['EP19_QUALIFICATION_ROOT']);os.environ['EP19_QUALIFICATION_DIR']=str(Q/'controls')
import runtime_controls as owner, runtime_continuation as prior, orchestration_controls
prior.Q=Q/'continuation';prior.Q.mkdir()
class Result(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.rows=[]
 def addSuccess(self,t):super().addSuccess(t);self.rows.append({'case':t.id(),'actual':'PASS'})
 def addFailure(self,t,e):super().addFailure(t,e);self.rows.append({'case':t.id(),'actual':'FAIL'})
 def addError(self,t,e):super().addError(t,e);self.rows.append({'case':t.id(),'actual':'ERROR'})
 def addSubTest(self,t,s,e):super().addSubTest(t,s,e);self.rows.append({'case':s.id(),'actual':'PASS' if e is None else 'FAIL'})
suite=unittest.TestSuite()
for cls in [prior.Controls,owner.LaunchControls,owner.PreservationControls,orchestration_controls.Controls]:
 for n in unittest.defaultTestLoader.getTestCaseNames(cls):
  if n!='test_frontend_native_readonly_and_private_pid':suite.addTest(cls(n))
r=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
areas={
 'collector':[x for x in r.rows if '.test_collector_' in x['case']],
 'coverage':[x for x in r.rows if any(n in x['case'] for n in ['test_bindings_exact','test_detached_seal','test_deep_','test_instruction_','test_run_control_'])],
 'shadow':[x for x in r.rows if '.PreservationControls.' in x['case'] or '.test_shadow_' in x['case']],
 'packaging':[x for x in r.rows if '.test_packaging_' in x['case']],
 'freshness':[x for x in r.rows if '.test_fresh' in x['case'] or 'resolved_dependency' in x['case']],
 'dependency_preparation':[x for x in r.rows if x['case'].startswith('orchestration_controls.')],
 'launch':[x for x in r.rows if '.LaunchControls.' in x['case'] or 'test_failed_dependency_stops' in x['case']]}
coverage.put(Q/'results.json',{'result':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skipped':len(r.skipped),'cases':r.rows,'areas':{k:{'result':'PASS' if v and all(x['actual']=='PASS' for x in v) else 'FAIL','cases':v} for k,v in areas.items()},'product_gate_execution':False,'fixture_gate_bodies':'synthetic only; actual run_all/preflight/authorization/seal/identity/artifact acceptance','reuse':[]})
raise SystemExit(not r.wasSuccessful())
