from pathlib import Path
import json,hashlib,subprocess,os
E=Path(__file__).resolve().parent;W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1');b=json.loads((E/'BASELINE_INSPECTION.json').read_text());a=set(json.loads((E/'ALLOWLIST.json').read_text()))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(W),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).decode().strip()
assert git('rev-parse','HEAD')==b['head'] and git('symbolic-ref','HEAD')==b['branch'] and sha(Path(b['index_path']))==b['index_sha256']
d=json.loads((E/'SOURCE_DELTA.json').read_text()); expected=dict(b['files']);modes=dict(b['modes'])
for row in d['paths']:expected[row['path']]=row['after_sha256'];modes[row['path']]=row['mode']
paths=set(git('ls-files','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in expected if not p.startswith('frontend/'))).splitlines())
errors=[]
for p in sorted(paths|set(expected)):
 f=W/p
 if p not in expected or not f.is_file() or sha(f)!=expected[p] or ('100755' if f.stat().st_mode&0o111 else '100644')!=modes[p]:errors.append(p)
assert paths==set(expected) and not errors,errors
pres=json.loads((E/'PRESERVATION_BEFORE.json').read_text());bad=[p for p,h in pres.items() if not Path(p).is_file() or sha(Path(p))!=h];assert not bad,bad
result={'head':b['head'],'branch':b['branch'],'final_tree':d['final_tree'],'real_index_unchanged':True,'final_scoped_paths':len(paths),'final_bytes_modes_membership_match':True,'unchanged_baseline_paths_outside_allowlist':len(set(b['files'])-a),'bounded_historical_and_dist_files':len(pres),'bounded_preservation_differences':bad,'product_git_mutations':0,'backend_task_checks':0,'scope':'Named frontend worktree and task-recorded predecessor public/build/receipt plus tracked frontend dist. No parallel backend or whole-system stationarity claim.'}
(E/'PRESERVATION_FINAL.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
