from pathlib import Path
import json,subprocess,sys
E=Path(__file__).parent;V=E/sys.argv[1]
plan=json.loads((V/'FINAL_VALIDATION_PLAN.json').read_text())
assert len(plan)==7
assert (V/'fixture-host/entry.tsx').is_file()
for name,args in plan.items():
 print('GATE_START',name,flush=True)
 result=subprocess.run([sys.executable,str(V/'gate.py'),name,*args])
 print('GATE_END',name,result.returncode,flush=True)
 if result.returncode:sys.exit(result.returncode)
for name in ['test_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 subprocess.run([sys.executable,str(V/name)],check=True)
print('FINAL_GATES_COMPLETE',str(V),flush=True)
