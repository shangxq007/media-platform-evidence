from pathlib import Path
import sys,json,shutil,subprocess
E=Path(__file__).parent;V=E/sys.argv[1];V.mkdir(exist_ok=False)
assert (E/'WRITER_HANDOFF.md').is_file()
for name in ['BASELINE_INSPECTION.json','ALLOWLIST.json','PRESERVATION_BEFORE.json','BUILD_TARGET_PRESERVATION_BEFORE.json','materialize.py','gate.py','test_accounting.py','verify_build.py','preservation.py','replay_patch.py']:
 shutil.copy2(E/name,V/name)
subprocess.run([sys.executable,str(V/'materialize.py')],check=True)
old=E.parent/'FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7'
plan=json.loads((old/'FINAL_VALIDATION_PLAN.json').read_text().replace(str(old),str(V)))
(V/'FINAL_VALIDATION_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
print('PREPARED',V)
