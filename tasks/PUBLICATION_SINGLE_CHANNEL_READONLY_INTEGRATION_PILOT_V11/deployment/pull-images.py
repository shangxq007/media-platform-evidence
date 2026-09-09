#!/usr/bin/env python3
"""Bounded immutable image acquisition into task engine only."""
import json,subprocess,concurrent.futures
from pathlib import Path
import yaml
D=Path(__file__).resolve().parent
c=yaml.safe_load((D/'compose.yaml').read_text())
def pull(item):
    name,s=item
    args=[str(D/'podman-isolated'),'pull','--retry=0',s['image']]
    try:
        p=subprocess.run(args,text=True,capture_output=True,timeout=300)
        return {'service':name,'image':s['image'],'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    except subprocess.TimeoutExpired as e:
        return {'service':name,'image':s['image'],'exit':'TIMEOUT','stderr':(e.stderr or b'').decode() if isinstance(e.stderr,bytes) else e.stderr}
records=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    for result in ex.map(pull,[(n,s) for n,s in c['services'].items() if not s.get('profiles')]):
        records.append(result)
        (D/'image-pull-results.json').write_text(json.dumps(records,indent=2)+'\n')
        print(json.dumps({'service':result['service'],'exit':result['exit']}),flush=True)
raise SystemExit(0 if all(r['exit']==0 for r in records) else 1)
