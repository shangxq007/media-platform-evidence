from pathlib import Path
import subprocess,os,json,hashlib,tarfile,io
E=Path(__file__).resolve().parent
W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
base=json.loads((E/'BASELINE.json').read_text())
allow=json.loads((E/'ALLOWLIST.json').read_text())+json.loads((E/'DOCUMENTATION_ALLOWLIST.json').read_text())
alts=[E.parent/'FRONTEND_WAVE2_FOCUSED_REVIEW_UX_CONVERGENCE_V1/objects',E.parent/'FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1/objects',Path('/home/user/Documents/workspace/projects/media-platform/.git/objects')]
READ_ENV={**os.environ,'GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(map(str,alts)),'GIT_OPTIONAL_LOCKS':'0'}
def g(*a,env=None):return subprocess.check_output(['git','-C',str(W),*a],env=env or READ_ENV)
assert g('rev-parse','HEAD').decode().strip()==base['head']
assert g('symbolic-ref','HEAD').decode().strip()==base['branch']
assert hashlib.sha256(Path(base['index_path']).read_bytes()).hexdigest()==base['index_sha256']
changed=[p for p,h in base['files'].items() if not (W/p).is_file() or hashlib.sha256((W/p).read_bytes()).hexdigest()!=h]
new=g('ls-files','--others','--exclude-standard').decode().splitlines()
assert set(changed+new)<=set(allow),(changed,new)
assert not base['untracked']
changed=sorted(set(changed+new))
O=E/'objects';O.mkdir(exist_ok=True);I=E/'final.index';assert not I.exists()
env={**READ_ENV,'GIT_INDEX_FILE':str(I),'GIT_OBJECT_DIRECTORY':str(O)}
subprocess.run(['git','-C',str(W),'read-tree',base['tree']],env=env,check=True)
records=[]
for p in changed:
 f=W/p;assert f.is_file(),p
 data=f.read_bytes();sha=subprocess.check_output(['git','-C',str(W),'hash-object','-w','--stdin'],input=data,env=env).decode().strip()
 mode='100755' if f.stat().st_mode & 0o111 else '100644'
 subprocess.run(['git','-C',str(W),'update-index','--add','--cacheinfo',mode,sha,p],env=env,check=True)
 dest=E/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 before=None
 if p not in new:
  b=g('show',base['tree']+':'+p,env=env);dest=E/'before'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b);before=hashlib.sha256(b).hexdigest()
 records.append({'path':p,'new':p in new,'before_sha256':before,'after_sha256':hashlib.sha256(data).hexdigest(),'blob':sha,'mode':mode})
tree=g('write-tree',env=env).decode().strip();(E/'FINAL_TREE.txt').write_text(tree+'\n')
(E/'TASK_DELTA.patch').write_bytes(g('diff','--binary',base['tree'],tree,env=env))
(E/'COMPLETE_IMPLEMENTATION.patch').write_bytes(g('diff','--binary','HEAD',tree,env=env))
S=E/'snapshot';S.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(g('archive',tree,env=env))) as tf:tf.extractall(S,filter='data')
subprocess.run(['git','init','--quiet',str(S)],check=True)
(S/'.git/objects/info/alternates').write_text('\n'.join(map(str,[O]+alts))+'\n')
subprocess.run(['git','-C',str(S),'read-tree',tree],check=True)
(S/'frontend/node_modules').symlink_to(W/'frontend/node_modules',target_is_directory=True)
(E/'SOURCE_DELTA.json').write_text(json.dumps({'baseline_tree':base['tree'],'final_tree':tree,'paths':records,'real_index_unchanged':True},indent=2))
print(json.dumps({'tree':tree,'paths':changed},indent=2))
