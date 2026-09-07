from pathlib import Path
H=Path('executor')
# The new entrypoint never imports these historical scripts with top-level effects.
for name in ['prepare.py','preflight.py','prepare_finalize.py','qualify_frontend.py']:
 (H/name).write_text('"""Retired historical entrypoint. Use runner.py or qualification/run.py."""\nif __name__ == "__main__":\n raise SystemExit("Use executor/runner.py; historical setup is never executable here")\n')
for name in ['bindings.py','coverage.py','parsers.py','engineering.py','runner.py']:
 p=H/name;s=p.read_text();s=s.replace('from execution import D,','from execution import D,O,H,').replace('D/\'owned\'','H')
 for part in ['inputs','PROTECTION_SCOPE.json','GATE_EXECUTION_MATRIX.json','qualification/CONTINUATION_PRESERVATION_CONTRACT.md','observations/BEFORE.json','owner-clarified-execution-20260907T1120Z']:
  s=s.replace("D/'"+part+"'","O/'"+part+"'")
 s=s.replace("D.parent/'EP19_","O.parent/'EP19_")
 p.write_text(s)
p=H/'execution.py';s=p.read_text().replace("D=Path(__file__).resolve().parents[1]","D=Path(__file__).resolve().parents[1]\nO=D.parent\nH=D/'executor'")
s=s.replace("GIT_NO_REPLACE_OBJECTS='1',H7_SOURCE_TREE", "GIT_NO_REPLACE_OBJECTS='1',GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',H7_SOURCE_TREE")
s=s.replace("[Path(run)/'runtime/cache/frontend'", "[Path(run)/'sources/frontend/frontend/node_modules',Path(run)/'runtime/cache/frontend'")
p.write_text(s)
p=H/'bindings.py';s=p.read_text();s=s.replace("substitutions={str(D/'outputs'):str(run/'runtime/outputs'),str(D/'cache'):str(run/'runtime/cache'),str(D/'tmp'):str(run/'runtime/tmp')}","substitutions={str(O/'sources'):str(run/'sources'),str(O/'owned'):str(H),str(O/'outputs'):str(run/'runtime/outputs'),str(O/'cache'):str(run/'runtime/cache'),str(O/'tmp'):str(run/'runtime/tmp')}")
s=s.replace("for field in ('cache','tmp')", "for field in ('cache','tmp','cwd','repository')")
s=s.replace("s['output_bindings']=output_bindings", "if name=='FRONTEND_BUILD':s['command']+=['--manifest']\n        if name=='COMPILE':s['command']+=['-I',str(H/'compile.init.gradle')]\n        s['output_bindings']=output_bindings")
s=s.replace("{p for p in scope['allowed'] if Path(p).is_relative_to(Path(s['repository']))}","{rewrite(p,substitutions) for p in scope['allowed'] if Path(rewrite(p,substitutions)).is_relative_to(Path(s['repository']))}")
p.write_text(s)
p=H/'engineering.py';s=p.read_text().replace('def source_recovery():','def source_recovery(root):').replace("root=D/'sources/backend';tracked=",'root=Path(root);tracked=');p.write_text(s)
