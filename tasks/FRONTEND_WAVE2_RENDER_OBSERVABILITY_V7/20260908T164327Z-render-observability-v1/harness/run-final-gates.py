"""Exact-tree seven required gates with external-only build output."""
from pathlib import Path
import json,shutil,subprocess,sys
E=Path(__file__).parent;V=E/sys.argv[1]
assert (E/'WRITER_HANDOFF.md').is_file()
V.mkdir(exist_ok=False)
for name in ['BASELINE_INSPECTION.json','ALLOWLIST.json','PRESERVATION_BEFORE.json','BUILD_TARGET_PRESERVATION_BEFORE.json','materialize.py','gate.py','test_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 shutil.copy2(E/name,V/name)
plan=json.loads((E/'FINAL_VALIDATION_PLAN.json').read_text().replace(str(E),str(V)))
(V/'FINAL_VALIDATION_PLAN.json').write_text(json.dumps(plan,indent=2))
subprocess.run([sys.executable,str(V/'materialize.py')],check=True)
subprocess.run([sys.executable,str(E/'prepare_fixture_host.py'),str(V)],check=True)
for name,args in plan.items():
 print('GATE_START',name,flush=True)
 result=subprocess.run([sys.executable,str(V/'gate.py'),name,*args])
 print('GATE_END',name,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
for name in ['test_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 subprocess.run([sys.executable,str(V/name)],check=True)
print('FINAL_GATES_COMPLETE',str(V),flush=True)
