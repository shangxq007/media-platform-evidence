from pathlib import Path
import os,json,subprocess,hashlib,datetime
E=Path(__file__).parent;V=E.parent/'FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7';W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
b=json.loads((V/'BASELINE_INSPECTION.json').read_text());d=json.loads((V/'final-validation-01/SOURCE_DELTA.json').read_text());T='414d6ed80f6d4c01699d56403a043b84b390d1e7'
assert d['final_tree']==T
alts=[str(V/'final-validation-01/objects'),*b['object_alternates']]
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_ALTERNATE_OBJECT_DIRECTORIES':':'.join(alts)}
def g(*a):return subprocess.check_output(['git','-C',str(W),*a],env=env)
sha=lambda x:hashlib.sha256(x).hexdigest()
expected=dict(b['files'])
for r in d['paths']:expected[r['path']]=r['after_sha256']
paths=set(g('ls-files','-z','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in expected if not p.startswith('frontend/'))).decode().strip('\0').split('\0'))
rows={}
for x in g('ls-tree','-rz',T).split(b'\0'):
 if x:
  meta,p=x.split(b'\t');mode,kind,blob=meta.decode().split();rows[p.decode()]=(mode,blob)
errors=[];modes={};actual={}
for p in sorted(paths|set(expected)):
 if p not in expected or p not in paths:errors.append(['membership',p]);continue
 f=W/p;mode='100755' if f.stat().st_mode&0o111 else '100644';data=f.read_bytes();modes[p]=mode;actual[p]=sha(data)
 if sha(data)!=expected[p] or rows[p][0]!=mode:errors.append(['bytes/mode',p])
 if sha(g('cat-file','blob',rows[p][1]))!=expected[p]:errors.append(['tree',p])
head=g('rev-parse','HEAD').decode().strip();branch=g('symbolic-ref','HEAD').decode().strip();index=sha(Path(b['index_path']).read_bytes())
report={'accepted_tree':T,'path_count':len(paths),'membership_match':paths==set(expected),'drift':errors,'head':head,'branch':branch,'index_sha256':index,'index_matches_v7':index==b['index_sha256'],'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(E/'BASELINE_VERIFICATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
assert not errors and paths==set(expected),errors
assert branch=='refs/heads/agent/frontend-wave2-product-ux-v1'
b.update(accepted_tree=T,files=actual,modes=modes,object_alternates=alts,captured_at=report['captured_at'],head=head,branch=branch,index_sha256=index,source_scope='V7 frontend plus exact predecessor supporting paths; backend lane excluded')
(E/'BASELINE_INSPECTION.json').write_text(json.dumps(b,indent=2))
(E/'STATUS_AT_START.txt').write_bytes(g('status','--porcelain=v2','--untracked-files=all','--','frontend',*sorted(p for p in expected if not p.startswith('frontend/'))))
(E/'INDEX_AT_START.bin').write_bytes(Path(b['index_path']).read_bytes())
(E/'INDEX_ENTRIES_AT_START.txt').write_bytes(g('ls-files','--stage'))
(E/'STASH_AT_START.txt').write_bytes(g('stash','list'))
j=json.loads((V/'final-validation-01/FULL_UNIT.json').read_text());ids=[json.dumps([r['name'].split('/frontend/')[-1],a['ancestorTitles'],a['title']],ensure_ascii=False) for r in j['testResults'] for a in r['assertionResults']];assert len(ids)==len(set(ids))==789
(E/'V7_FULL_UNIT.json').write_bytes((V/'final-validation-01/FULL_UNIT.json').read_bytes())
(E/'BASELINE_TEST_REFERENCE.json').write_text(json.dumps({'unique':len(ids),'identities':ids,'original_sha256':sha((E/'V7_FULL_UNIT.json').read_bytes())},indent=2))
