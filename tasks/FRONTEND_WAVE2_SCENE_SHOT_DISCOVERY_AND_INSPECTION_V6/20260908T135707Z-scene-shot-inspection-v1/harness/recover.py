from pathlib import Path
import os,json,subprocess,hashlib,datetime,shutil
E=Path(__file__).parent; V=E.parent/'FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V5'; W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
b=json.loads((V/'BASELINE_INSPECTION.json').read_text()); d=json.loads((V/'final-validation-03/SOURCE_DELTA.json').read_text()); T='f62687609a556dff204fc6939416c11abd45f945'
assert d['final_tree']==T
alts=[str(V/'final-validation-03/objects'),*b['object_alternates']]
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(alts)}
def g(*a):return subprocess.check_output(['git','-C',str(W),*a],env=env)
sha=lambda x:hashlib.sha256(x).hexdigest()
assert g('rev-parse','HEAD').decode().strip()==b['head']; assert g('symbolic-ref','HEAD').decode().strip()==b['branch']; assert sha(Path(b['index_path']).read_bytes())==b['index_sha256']
expected=dict(b['files'])
for r in d['paths']:expected[r['path']]=r['after_sha256']
paths=set(g('ls-files','-z','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in expected if not p.startswith('frontend/'))).decode().strip('\0').split('\0'))
rows={}
for x in g('ls-tree','-rz',T).split(b'\0'):
 if x:
  meta,p=x.split(b'\t');mode,kind,blob=meta.decode().split();rows[p.decode()]=(mode,blob)
errors=[];modes={}
for p in sorted(paths|set(expected)):
 if p not in expected or p not in paths:errors.append(['membership',p]);continue
 f=W/p; mode='100755' if f.stat().st_mode&0o111 else '100644'; data=f.read_bytes();modes[p]=mode
 if sha(data)!=expected[p] or rows[p][0]!=mode or g('hash-object','--stdin') if False else False:pass
 if sha(data)!=expected[p] or rows[p][0]!=mode:errors.append(['bytes/mode',p])
 if sha(g('cat-file','blob',rows[p][1]))!=expected[p]:errors.append(['tree',p])
report={'accepted_tree':T,'path_count':len(paths),'membership_match':paths==set(expected),'errors':errors,'real_index_unchanged':True,'v5_delta_paths':len(d['paths'])}
(E/'BASELINE_VERIFICATION.json').write_text(json.dumps(report,indent=2));assert not errors and paths==set(expected),errors
b.update(accepted_tree=T,files=expected,modes=modes,object_alternates=alts,captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_scope='V5 frontend plus predecessor-recorded supporting paths only; no parallel backend stationarity')
assert set(b['files'])==set(b['modes'])
(E/'BASELINE_INSPECTION.json').write_text(json.dumps(b,indent=2))
(E/'STATUS_AT_START.txt').write_bytes(g('status','--porcelain=v1','--untracked-files=all','--','frontend',*sorted(p for p in expected if not p.startswith('frontend/'))))
shutil.copy2(V/'final-validation-03/FULL_UNIT.json',E/'V5_FULL_UNIT.json')
j=json.loads((E/'V5_FULL_UNIT.json').read_text()); ids=[json.dumps([r['name'].split('/frontend/')[-1],a['ancestorTitles'],a['title']],ensure_ascii=False) for r in j['testResults'] for a in r['assertionResults']];assert len(ids)==len(set(ids))==724
(E/'BASELINE_TEST_REFERENCE.json').write_text(json.dumps({'unique':len(ids),'identities':ids,'original_sha256':sha((E/'V5_FULL_UNIT.json').read_bytes())},indent=2))
print(json.dumps(report))
