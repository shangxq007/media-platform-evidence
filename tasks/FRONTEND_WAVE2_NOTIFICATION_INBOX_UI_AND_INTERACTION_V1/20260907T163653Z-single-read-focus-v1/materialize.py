"""Exact dirty-tree materialization; only external index/object writes."""
from pathlib import Path
import subprocess, os, json, hashlib, tarfile, io
E=Path(__file__).resolve().parent
W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
base=json.loads((E/'BASELINE.json').read_text())
allow=set(json.loads((E/'ALLOWLIST.json').read_text()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
env={**os.environ,'GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(base['object_alternates']),'GIT_OPTIONAL_LOCKS':'0'}
def g(*a,environment=None):return subprocess.check_output(['git','-C',str(W),*a],env=environment or env)
assert g('rev-parse','HEAD').decode().strip()==base['head']
assert g('symbolic-ref','HEAD').decode().strip()==base['branch']
assert sha(Path(base['index_path']))==base['index_sha256']
paths=set(g('ls-files','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in base['files'] if not p.startswith('frontend/'))).decode().splitlines())
assert paths==set(base['files']), 'Path membership changed'
changed=[]
for p,h in base['files'].items():
 f=W/p;assert f.is_file()
 mode='100755' if f.stat().st_mode&0o111 else '100644'
 if sha(f)!=h or mode!=base['modes'][p]:changed.append(p)
assert set(changed)<=allow,changed
assert changed, 'No correction delta: do not materialize replacement'
O=E/'objects';O.mkdir(exist_ok=False);I=E/'final.index';assert not I.exists()
writeenv={**env,'GIT_OBJECT_DIRECTORY':str(O),'GIT_INDEX_FILE':str(I)}
g('read-tree',base['tree'],environment=writeenv)
records=[]
for p in sorted(changed):
 f=W/p;data=f.read_bytes();blob=subprocess.check_output(['git','-C',str(W),'hash-object','-w','--stdin'],input=data,env=writeenv).decode().strip()
 mode='100755' if f.stat().st_mode&0o111 else '100644'
 g('update-index','--add','--cacheinfo',mode,blob,p,environment=writeenv)
 before=g('show',base['tree']+':'+p,environment=writeenv)
 for directory,payload in [('source',data),('before-source',before)]:
  out=E/directory/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(payload)
 records.append({'path':p,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(data).hexdigest(),'mode':mode,'blob':blob})
T=g('write-tree',environment=writeenv).decode().strip()
(E/'FINAL_TREE.txt').write_text(T+'\n')
(E/'TASK_DELTA.patch').write_bytes(g('diff','--binary',base['tree'],T,environment=writeenv))
(E/'FINAL_TREE_MANIFEST.txt').write_bytes(g('ls-tree','-r',T,environment=writeenv))
S=E/'snapshot';S.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(g('archive',T,environment=writeenv))) as archive:archive.extractall(S,filter='data')
subprocess.run(['git','init','--quiet',str(S)],check=True)
(S/'.git/objects/info/alternates').write_text('\n'.join([str(O)]+base['object_alternates'])+'\n')
subprocess.run(['git','-C',str(S),'read-tree',T],check=True)
(S/'frontend/node_modules').symlink_to(W/'frontend/node_modules',target_is_directory=True)
(E/'SOURCE_DELTA.json').write_text(json.dumps({'baseline_tree':base['tree'],'final_tree':T,'paths':records,'real_index_unchanged':sha(Path(base['index_path']))==base['index_sha256']},indent=2))
print(json.dumps({'tree':T,'changed':changed,'snapshot':str(S)},indent=2))
