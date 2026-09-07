from pathlib import Path
import subprocess,os,json,hashlib,tarfile,io
E=Path(__file__).resolve().parent;W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1');base=json.loads((E/'BASELINE.json').read_text());allow=json.loads((E/'ALLOWLIST.json').read_text())+json.loads((E/'DOCUMENTATION_ALLOWLIST.json').read_text())
PREVIOUS_OBJECTS='/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1/objects'
READ_ENV={**os.environ,'GIT_ALTERNATE_OBJECT_DIRECTORIES':PREVIOUS_OBJECTS,'GIT_OPTIONAL_LOCKS':'0'}
def g(*a,env=None):return subprocess.check_output(['git','-C',str(W),*a],env=env or READ_ENV)
assert g('rev-parse','HEAD').decode().strip()==base['head'];assert hashlib.sha256(Path(base['index_path']).read_bytes()).hexdigest()==base['index_sha256']
changed=[p for p,h in base['files'].items() if hashlib.sha256((W/p).read_bytes()).hexdigest()!=h]
assert set(changed)<=set(allow),changed
untracked=g('ls-files','--others','--exclude-standard').decode().splitlines();assert not untracked,untracked
O=E/'objects';O.mkdir(exist_ok=True);I=E/'final.index';assert not I.exists()
common=Path(g('rev-parse','--git-common-dir').decode().strip());common=common if common.is_absolute() else (W/common).resolve()
env={**os.environ,'GIT_INDEX_FILE':str(I),'GIT_OBJECT_DIRECTORY':str(O),'GIT_ALTERNATE_OBJECT_DIRECTORIES':PREVIOUS_OBJECTS+':'+str(common/'objects'),'GIT_OPTIONAL_LOCKS':'0'}
subprocess.run(['git','-C',str(W),'read-tree',base['tree']],env=env,check=True)
for p in changed:
 sha=subprocess.check_output(['git','-C',str(W),'hash-object','-w','--stdin'],input=(W/p).read_bytes(),env=env).decode().strip()
 mode=g('ls-files','--stage','--',p).decode().split()[0]
 subprocess.run(['git','-C',str(W),'update-index','--add','--cacheinfo',mode,sha,p],env=env,check=True)
tree=g('write-tree',env=env).decode().strip();(E/'FINAL_TREE.txt').write_text(tree+'\n')
(E/'TASK_DELTA.patch').write_bytes(g('diff','--binary',base['tree'],tree,env=env));(E/'COMPLETE_IMPLEMENTATION.patch').write_bytes(g('diff','--binary','HEAD',tree,env=env))
S=E/'snapshot';S.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(g('archive',tree,env=env))) as tf:tf.extractall(S,filter='data')
subprocess.run(['git','init','--quiet',str(S)],check=True)
(S/'.git/objects/info/alternates').write_text(str(O)+'\n'+PREVIOUS_OBJECTS+'\n'+str(common/'objects')+'\n')
subprocess.run(['git','-C',str(S),'read-tree',tree],check=True)
(S/'frontend/node_modules').symlink_to(W/'frontend/node_modules',target_is_directory=True)
rows=[]
for p in changed:
 d=E/'source'/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes((W/p).read_bytes())
 old=E/'before'/p;old.parent.mkdir(parents=True,exist_ok=True);old.write_bytes(g('show',base['tree']+':'+p,env=env))
 rows.append({'path':p,'before_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(d.read_bytes()).hexdigest()})
(E/'SOURCE_DELTA.json').write_text(json.dumps({'baseline_tree':base['tree'],'final_tree':tree,'paths':rows,'external_objects':str(O),'real_index_unchanged':True},indent=2));print(json.dumps({'tree':tree,'changed':changed},indent=2))
