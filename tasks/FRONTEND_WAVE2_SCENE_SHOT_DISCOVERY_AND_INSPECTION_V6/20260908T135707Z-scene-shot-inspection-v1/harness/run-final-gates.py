"""Execute final gates on a new external exact-tree materialization."""
from pathlib import Path
import json,shutil,subprocess,sys
T=Path(__file__).resolve().parent;V=T/sys.argv[1]
assert (T/'writer/REPORT.md').is_file(), 'Writer final report required'
V.mkdir(exist_ok=False)
for name in ['BASELINE_INSPECTION.json','ALLOWLIST.json','PRESERVATION_BEFORE.json','materialize.py','gate.py','test_accounting.py','lint_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 shutil.copy2(T/name,V/name)
plan=json.loads((T/'FINAL_VALIDATION_PLAN.json').read_text().replace(str(T),str(V)))
(V/'FINAL_VALIDATION_PLAN.json').write_text(json.dumps(plan,indent=2))
subprocess.run([sys.executable,str(V/'materialize.py')],check=True)
subprocess.run([sys.executable,str(T/'prepare_fixture_host.py'),str(V)],check=True)
for name,args in plan.items():
 print('GATE_START',name,flush=True)
 result=subprocess.run([sys.executable,str(V/'gate.py'),name,*args])
 print('GATE_END',name,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
for name in ['test_accounting.py','lint_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 subprocess.run([sys.executable,str(V/name)],check=True)
print('FINAL_GATES_COMPLETE',str(V),flush=True)
