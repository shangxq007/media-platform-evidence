from pathlib import Path
import json,sys,hashlib,subprocess
from execution import D,SHA,TREE,exact,environment,frontend_sandbox
from isolation import frontend_command,validate_output
from account import reconcile,canonical
B=D/'sources/backend';F=D/'sources/frontend';attempt=sys.argv[1];assert attempt.startswith('frontend-positive-') and '/' not in attempt and '..' not in attempt
Q=D/'qualification'/attempt;Q.mkdir()
OUT=D/'outputs/qualification'/attempt;OUT.mkdir(parents=True);(OUT/'stale-sentinel').write_text('synthetic stale build output')
external=D/'outputs/qualification/non-output-sentinel';external.write_text('must stay');env=environment('frontend');mods=F/'frontend/node_modules'
for p in [mods/'.vite',mods/'.vite-temp']:p.mkdir(exist_ok=True)
writes=[D/'cache/frontend',D/'tmp/frontend',D/'outputs/qualification',Q,mods/'.vite',mods/'.vite-temp']
exact(B);exact(F);receipts=[]
def call(name,argv):
 cmd=frontend_sandbox(argv,F/'frontend',writes)
 with (Q/(name+'.log')).open('xb') as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 receipts.append({'name':name,'command':cmd,'native_exit':r.returncode});(Q/'COMMANDS.json').write_text(json.dumps(receipts,indent=2))
 if r.returncode:raise RuntimeError(name+'_NATIVE_FAILURE')
call('RESOLVED',['node',str(D/'owned/vite_resolution.mjs'),str(F/'frontend'),str(OUT),str(Q/'RESOLVED.json')])
assert json.loads((Q/'RESOLVED.json').read_text())['outDir']==str(validate_output(OUT,D/'outputs',[B,F]))
call('BUILD',frontend_command(OUT))
assert not (OUT/'stale-sentinel').exists();assert external.read_text()=='must stay';exact(B);exact(F)
call('COLLECT',['node',str(D/'owned/collect_frontend.mjs'),str(F/'frontend'),str(Q/'COLLECTED.jsonl')])
expected=json.loads((D/'inputs/EXPECTED_IDENTITIES.json').read_text())['FRONTEND_TEST']['identities'];rows=[(canonical(json.loads(x)),'PASS') for x in (Q/'COLLECTED.jsonl').read_text().splitlines()];result=reconcile(expected,rows);assert result['result']=='PASS',result
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file()}
(Q/'RESULT.json').write_text(json.dumps({'result':'PASS_BOUNDED_QUALIFICATION','candidate':SHA,'tree':TREE,'formal_gate_execution':False,'build_cleanup_confined':True,'outside_sentinel_unchanged':True,'backend_and_frontend_tracked_bytes_exact':True,'structured_collection':result,'outputs':manifest,'harness':{str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),D/'owned/execution.py',D/'owned/isolation.py',D/'owned/vite_resolution.mjs',D/'owned/collect_frontend.mjs',D/'owned/account.py']}},indent=2))
print('FRONTEND_POSITIVE_QUALIFICATION=PASS;COLLECTED='+str(result['executed']))
