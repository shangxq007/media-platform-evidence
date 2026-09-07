from pathlib import Path
import subprocess,json,hashlib,os,sys,datetime
E=Path(__file__).resolve().parent;W=Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
b=json.loads((E/'BASELINE_INSPECTION.json').read_text());allow=set(json.loads((E/'ALLOWLIST.json').read_text()))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def g(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(W),*a])
paths=set(g('ls-files','--cached','--others','--exclude-standard','--','frontend',*sorted(p for p in b['files'] if not p.startswith('frontend/'))).decode().splitlines())
changes=[];missing=[]
for p in sorted(paths|set(b['files'])):
 f=W/p
 if not f.is_file():missing.append(p);continue
 mode='100755' if f.stat().st_mode&0o111 else '100644'
 if p not in b['files'] or sha(f)!=b['files'][p] or mode!=b['modes'][p]:changes.append(p)
nonfrontend=json.loads((E/'NON_FRONTEND_PRESERVATION_BEFORE.json').read_text());historical=json.loads((E/'HISTORICAL_PRESERVATION_BEFORE.json').read_text())
nonfront_delta=[p for p,h in nonfrontend.items() if not (W/p).is_file() or sha(W/p)!=h]
history_delta=[p for p,h in historical.items() if not Path(p).is_file() or sha(Path(p))!=h]
final_mismatch=[]
if (E/'SOURCE_DELTA.json').exists():
 delta=json.loads((E/'SOURCE_DELTA.json').read_text());expected={**b['files'],**{r['path']:r['after_sha256'] for r in delta['paths']}}
 final_mismatch=[p for p,h in expected.items() if not (W/p).is_file() or sha(W/p)!=h]
 final_mismatch+=sorted(paths-set(expected))
body_before=json.loads((E/'RUNTIME_BODIES_BEFORE.json').read_text());body_changes=[];metadata_changes=[]
for p,row in body_before.items():
 f=Path(p)
 if not f.is_file() or sha(f)!=row['sha256']:body_changes.append(p)
 elif f.stat().st_mtime_ns!=row['mtime_ns']:metadata_changes.append(p)
row={'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'branch':g('symbolic-ref','HEAD').decode().strip(),'head':g('rev-parse','HEAD').decode().strip(),'index_sha256':sha(Path(b['index_path'])),'changed_paths':changes,'missing':missing,'out_of_scope':sorted(set(changes)-allow),'non_frontend_bytes_changed':nonfront_delta,'historical_files_checked':len(historical),'historical_differences':history_delta,'final_tree_byte_differences':final_mismatch,'tracked_dist_changes':[p for p in changes if p.startswith('frontend/dist/')],'observed_skill_memory_baseline_file_body_drift':body_changes,'observed_same_body_mtime_drift':metadata_changes,'task_issued_skill_memory_body_writes':0,'runtime_metadata_limit':'Baseline body file set observed; usage/curator and independently added files are not an attribution or zero-global-change claim.'}
assert row['branch']==b['branch'] and row['head']==b['head'] and row['index_sha256']==b['index_sha256']
assert not missing and not row['out_of_scope'] and not nonfront_delta and not history_delta and not final_mismatch and not row['tracked_dist_changes'],row
out=E/('PRESERVATION_'+(sys.argv[1] if len(sys.argv)>1 else 'FINAL')+'.json');assert not out.exists();out.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(row,ensure_ascii=False,indent=2))
