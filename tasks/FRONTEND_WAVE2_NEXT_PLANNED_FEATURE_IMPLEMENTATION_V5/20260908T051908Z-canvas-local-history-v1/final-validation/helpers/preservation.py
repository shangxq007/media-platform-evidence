from pathlib import Path
import json,hashlib,subprocess,os
E=Path(__file__).resolve().parent;W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1');b=json.loads((E/'BASELINE_INSPECTION.json').read_text());a=set(json.loads((E/'ALLOWLIST.json').read_text()))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*x):return subprocess.check_output(['git','--no-optional-locks','-C',str(W),*x],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).decode().strip()
assert git('rev-parse','HEAD')==b['head'] and git('symbolic-ref','HEAD')==b['branch'] and sha(Path(b['index_path']))==b['index_sha256']
unchanged=[p for p,h in b['files'].items() if p not in a and (not (W/p).is_file() or sha(W/p)!=h)];assert not unchanged,unchanged
pres=json.loads((E/'PRESERVATION_BEFORE.json').read_text());pres.update(json.loads((E/'PRESERVATION_SUPPLEMENT.json').read_text()));bad=[p for p,h in pres.items() if not Path(p).is_file() or sha(Path(p))!=h];assert not bad,bad
final=json.loads((E/'SOURCE_DELTA.json').read_text());assert all(sha(W/r['path'])==r['after_sha256'] for r in final['paths'])
result={'head':b['head'],'branch':b['branch'],'real_index_unchanged':True,'unchanged_baseline_paths_outside_allowlist':len(set(b['files'])-a),'unexpected_baseline_changes':unchanged,'bounded_historical_and_dist_files':len(pres),'bounded_preservation_differences':bad,'final_changed_paths_match':True,'product_git_mutations':0,'backend_task_checks':0,'scope':'Named frontend worktree and task-recorded predecessor public/build/receipt plus tracked frontend dist. No claim of parallel backend or whole-system stationarity.'}
(E/'PRESERVATION_FINAL.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
