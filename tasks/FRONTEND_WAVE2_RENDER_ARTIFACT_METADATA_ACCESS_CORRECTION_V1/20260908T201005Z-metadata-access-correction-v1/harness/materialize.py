"""Reconstruct current authorized dirty implementation in external Git objects/index only."""
from pathlib import Path
import subprocess, os, json, hashlib, io, tarfile
E=Path(__file__).resolve().parent
W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
b=json.loads((E/'BASELINE_INSPECTION.json').read_text()); allow=set(json.loads((E/'ALLOWLIST.json').read_text()))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(b['object_alternates'])}
def g(*a,environment=None,data=None):return subprocess.check_output(['git','-C',str(W),*a],env=environment or env,input=data)
assert g('rev-parse','HEAD').decode().strip()==b['head']
assert g('symbolic-ref','HEAD').decode().strip()==b['branch']
assert sha(Path(b['index_path']))==b['index_sha256']
paths=set(g('ls-files','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in b['files'] if not p.startswith('frontend/'))).decode().splitlines())
changed=[]
for p in sorted(paths|set(b['files'])):
 f=W/p
 if not f.is_file():raise AssertionError('Deletion not authorized: '+p)
 mode='100755' if f.stat().st_mode&0o111 else '100644'
 if p not in b['files'] or sha(f)!=b['files'][p] or mode!=b['modes'][p]:changed.append(p)
assert changed and set(changed)<=allow, changed
O=E/'objects';O.mkdir(exist_ok=False);I=E/'final.index';assert not I.exists()
we={**env,'GIT_OBJECT_DIRECTORY':str(O),'GIT_INDEX_FILE':str(I)}
g('read-tree',b['accepted_tree'],environment=we)
rows=[]
for p in changed:
 f=W/p;data=f.read_bytes();blob=g('hash-object','-w','--stdin',environment=we,data=data).decode().strip();mode='100755' if f.stat().st_mode&0o111 else '100644'
 g('update-index','--add','--cacheinfo',mode,blob,p,environment=we)
 before=g('show',b['accepted_tree']+':'+p,environment=we) if p in b['files'] else None
 for directory,payload in [('source',data),('before-source',before)]:
  if payload is not None:
   out=E/directory/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(payload)
 rows.append({'path':p,'status':'M' if before is not None else 'A','before_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,'before_blob':g('rev-parse',b['accepted_tree']+':'+p,environment=we).decode().strip() if before is not None else None,'before_mode':b['modes'].get(p),'before_bytes':len(before) if before is not None else None,'after_sha256':sha(f),'after_bytes':len(data),'mode':mode,'blob':blob})
T=g('write-tree',environment=we).decode().strip();(E/'FINAL_TREE.txt').write_text(T+'\n')
(E/'TASK_DELTA.patch').write_bytes(g('diff','--binary','--full-index','--no-ext-diff','--no-textconv','--no-renames','--src-prefix=a/','--dst-prefix=b/',b['accepted_tree'],T,environment=we));(E/'FINAL_TREE_MANIFEST.txt').write_bytes(g('ls-tree','-r',T,environment=we))
S=E/'snapshot';S.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(g('archive',T,environment=we))) as archive:archive.extractall(S,filter='data')
subprocess.run(['git','init','--quiet',str(S)],check=True)
(S/'.git/objects/info/alternates').write_text('\n'.join([str(O)]+b['object_alternates'])+'\n')
subprocess.run(['git','-C',str(S),'read-tree',T],check=True)
(S/'frontend/node_modules').symlink_to(W/'frontend/node_modules',target_is_directory=True)
(E/'SOURCE_DELTA.json').write_text(json.dumps({'baseline_tree':b['accepted_tree'],'final_tree':T,'paths':rows,'real_index_unchanged':sha(Path(b['index_path']))==b['index_sha256']},indent=2)+'\n')
print(json.dumps({'tree':T,'changed':changed,'snapshot':str(S)},indent=2))
