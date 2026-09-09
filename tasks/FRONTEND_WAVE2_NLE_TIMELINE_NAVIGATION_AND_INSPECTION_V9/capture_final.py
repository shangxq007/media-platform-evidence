from pathlib import Path
import os,sys,subprocess,json,hashlib,tarfile,io
C=Path(__file__).resolve().parent; V=C/sys.argv[1];V.mkdir(exist_ok=False)
W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
b=json.loads((C/'RECOVERY.json').read_text());env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(b['alternates'])}
def g(*args,data=None,e=None):return subprocess.check_output(['git','-C',str(W),*args],env=e or env,input=data)
def sha(data):return hashlib.sha256(data).hexdigest()
assert g('symbolic-ref','HEAD').decode().strip()==b['branch']
assert g('rev-parse','HEAD').decode().strip()==b['head']
idx=Path(g('rev-parse','--git-path','index').decode().strip());assert sha(idx.read_bytes())==b['index_sha256']
paths=set(g('ls-files','--cached','--others','--exclude-standard','--','frontend','docs/architecture/governance').decode().splitlines())
changed=[]
for p in sorted(paths|set(b['files'])):
 f=W/p
 if not f.is_file():raise RuntimeError('Unexpected removal: '+p)
 if p not in b['files'] or sha(f.read_bytes())!=b['files'][p]['sha256'] or oct(f.stat().st_mode)!=b['files'][p]['mode']:changed.append(p)
allow={'frontend/governance/UX_WAVE_1_REVIEW.md', 'docs/architecture/governance/frontend-product-path-classification-v1.tsv', 'frontend/src/surfaces/FoundationPages.tsx', 'frontend/src/interaction/InteractionShell.test.tsx', 'frontend/src/localization/catalogs.ts', 'frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv', 'frontend/src/product/timeline/timeline-navigation.css', 'docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv', 'frontend/src/product/timeline/TimelineNavigation.test.tsx', 'frontend/src/product/timeline/NleWorkspace.tsx', 'frontend/src/product/timeline/TimelineNavigation.tsx', 'docs/architecture/governance/frontend-product-information-architecture-v1.md', 'frontend/src/localization/source-manifest.json', 'frontend/src/product/timeline/NleWorkspace.test.tsx', 'docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md', 'frontend/src/app/routeTree.test.tsx', 'frontend/src/product/timeline/navigation.ts'}
assert set(changed)<=allow,sorted(set(changed)-allow)
O=V/'objects';O.mkdir();e={**env,'GIT_OBJECT_DIRECTORY':str(O),'GIT_INDEX_FILE':str(V/'implementation.index')};g('read-tree',b['base'],e=e)
rows=[]
for p in changed:
 f=W/p;data=f.read_bytes();blob=g('hash-object','-w','--stdin',data=data,e=e).decode().strip();mode='100755' if f.stat().st_mode&0o111 else '100644'
 g('update-index','--add','--cacheinfo',mode,blob,p,e=e)
 before=g('show',b['base']+':'+p,e=e) if p in b['files'] else None
 for sub,content in [('source',data),('before-source',before)]:
  if content is not None:
   dest=V/sub/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
 rows.append({'path':p,'before_sha256':sha(before) if before is not None else None,'after_sha256':sha(data),'bytes':len(data),'blob':blob,'mode':mode})
T=g('write-tree',e=e).decode().strip();(V/'FINAL_TREE.txt').write_text(T+'\n')
(V/'TASK_DELTA.patch').write_bytes(g('diff','--binary','--full-index','--no-ext-diff','--no-textconv','--no-renames',b['base'],T,e=e))
(V/'FINAL_TREE_MANIFEST.txt').write_bytes(g('ls-tree','-r',T,e=e))
S=V/'snapshot';S.mkdir()
with tarfile.open(fileobj=io.BytesIO(g('archive',T,e=e))) as a:a.extractall(S,filter='data')
subprocess.run(['git','init','--quiet',str(S)],check=True)
(S/'.git/objects/info/alternates').write_text('\n'.join([str(O)]+b['alternates'])+'\n')
subprocess.run(['git','-C',str(S),'read-tree',T],check=True)
(S/'frontend/node_modules').symlink_to(W/'frontend/node_modules',target_is_directory=True)
(V/'SOURCE_DELTA.json').write_text(json.dumps({'baseline_tree':b['base'],'final_tree':T,'paths':rows,'real_index_unchanged':sha(idx.read_bytes())==b['index_sha256'],'preserved_paths':len(paths)-len(changed)},indent=2)+'\n')
print(json.dumps({'tree':T,'changed':changed,'snapshot':str(S)},indent=2))
