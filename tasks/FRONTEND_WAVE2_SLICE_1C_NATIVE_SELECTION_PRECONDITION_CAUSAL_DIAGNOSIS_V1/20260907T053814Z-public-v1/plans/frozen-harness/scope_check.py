import os,json,subprocess,hashlib,time
from pathlib import Path
E=Path(__file__).parent
W=Path('[LOCAL_FRONTEND_WORKTREE]')
def census(root,exclude_frontend=False):
 paths=subprocess.check_output(['git','--no-optional-locks','-C',str(root),'ls-files','-z','--cached','--others','--exclude-standard']).split(b'\0');d={}
 for raw in set(paths):
  if not raw:continue
  p=os.fsdecode(raw)
  if exclude_frontend and p.startswith('frontend/') and not p.startswith('frontend/dist/'):continue
  f=root/p
  if not f.exists() and not f.is_symlink():d[p]=None;continue
  b=os.fsencode(os.readlink(f)) if f.is_symlink() else f.read_bytes();d[p]=[hashlib.sha256(b).hexdigest(),f.lstat().st_mode]
 return d
def integrity():
 roots=[W,Path('[LOCAL_PRODUCT_REPOSITORY]'),W.parent/'frontend-i18n-foundation-v1',W.parent/'frontend-product-interaction-ux-wave-1']
 main=roots[1]
 roots += [main/'.worktrees'/n for n in ['ep19-entitlement-port-v1-working','ep14-delivery-mutation-v1-working','workflow-process-authority-bounded-implementation']]
 result={'lanes':{str(p):census(p,p==W) for p in roots},'refs':subprocess.check_output(['git','--no-optional-locks','-C',str(W),'show-ref']).decode(),'indexes':{}}
 for p in roots:
  index=Path(subprocess.check_output(['git','--no-optional-locks','-C',str(p),'rev-parse','--path-format=absolute','--git-path','index']).decode().strip())
  result['indexes'][str(p)]=hashlib.sha256(index.read_bytes()).hexdigest()
 return result
def check(label):
 b=json.loads((E/'BASELINE.json').read_text())['integrity'];a=integrity()
 changes={root:[p for p in set(a['lanes'][root])|set(old) if a['lanes'][root].get(p)!=old.get(p)] for root,old in b['lanes'].items()}
 r={'label':label,'time':time.time(),'changed':changes,'refs_unchanged':a['refs']==b['refs'],'indexes_unchanged':a['indexes']==b['indexes']}
 with (E/'SCOPE_TRIPWIRE.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
 assert not any(changes.values()) and r['refs_unchanged'] and r['indexes_unchanged'],r
 return r
if __name__=='__main__':print(json.dumps(check('manual-readback'),indent=2))
