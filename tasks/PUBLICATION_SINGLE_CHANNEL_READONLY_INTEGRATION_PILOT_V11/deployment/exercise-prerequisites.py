#!/usr/bin/env python3
"""Bounded prerequisite exercise only. Never starts Postiz or connects accounts."""
import json,subprocess
from pathlib import Path
import yaml
D=Path(__file__).resolve().parent
c=yaml.safe_load((D/'compose.yaml').read_text())
I=json.loads((D/'identity.json').read_text())
records=[]
def run(args,timeout=90):
    try:
        p=subprocess.run([str(D/'podman-isolated'),*args],text=True,capture_output=True,timeout=timeout)
        r={'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:
        r={'args':args,'exit':'TIMEOUT','stdout':(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout,'stderr':(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else e.stderr}
    records.append(r)
    (D/'runtime-exercise.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(r,indent=2),flush=True)
    return r
name=I['project']+'-egress-preflight'
r=run(['network','create','--internal','--label','audit.instance='+I['project'],name])
if r['exit']!=0: raise SystemExit(1)
r=run(['network','inspect',name])
assert r['exit']==0 and json.loads(r['stdout'])[0]['internal'] is True
image=c['services']['postiz-redis']['image']
r=run(['pull','--retry=0',image],timeout=180)
if r['exit']!=0:
    run(['network','rm',name])
    raise SystemExit(1)
# No DB/cache server started: shell inspects namespace route, not data.
r=run(['run','--rm','--name',I['project']+'-route-probe','--network',name,'--http-proxy=false','--cap-drop=NET_RAW','--cap-drop=NET_ADMIN','--security-opt=no-new-privileges','--entrypoint','sh',image,'-c','cat /proc/net/route; cat /proc/net/ipv6_route'],timeout=60)
run(['network','rm',name])
raise SystemExit(0 if r['exit']==0 else 1)
