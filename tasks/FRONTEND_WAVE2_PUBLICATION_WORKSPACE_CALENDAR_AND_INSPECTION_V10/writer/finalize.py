from pathlib import Path
import collections, datetime, difflib, hashlib, json, os, subprocess
r=Path.cwd(); e=Path(__file__).parent; rec=json.loads((e.parent/'RECOVERY.json').read_text()); before=json.loads((e/'before.json').read_text())
env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_ALTERNATE_OBJECT_DIRECTORIES':os.pathsep.join(rec['alternates'])}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[p for p,v in rec['files'].items() if (r/p).exists() and sha(r/p)!=v['sha256']]
deleted=[p for p in rec['files'] if not (r/p).exists()]
new=sorted(str(p.relative_to(r)) for p in (r/'frontend/src/product/publication').rglob('*') if p.is_file())
planned=json.loads((e/'proposed-paths.json').read_text())+['frontend/src/interaction/model.ts','frontend/src/product/publication/testing.ts']
patch=[]
for p in changed:
 old=(e/'baseline-changed'/p).read_bytes(); assert hashlib.sha256(old).hexdigest()==rec['files'][p]['sha256']
 patch.extend(difflib.unified_diff(old.decode().splitlines(True),(r/p).read_text().splitlines(True),fromfile='a/'+p,tofile='b/'+p))
for p in new: patch.extend(difflib.unified_diff([], (r/p).read_text().splitlines(True),fromfile='/dev/null',tofile='b/'+p))
(e/'V10-only.patch').write_text(''.join(patch))
index=Path(subprocess.check_output(['git','rev-parse','--git-path','index'],env=env,text=True).strip())
state={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'changed_from_recovery':changed,'new_paths':new,'deleted':deleted,'unexpected':[p for p in changed+new if p not in planned],'unchanged_recovery_files':len(rec['files'])-len(changed)-len(deleted),'head':subprocess.check_output(['git','rev-parse','HEAD','HEAD^'],env=env,text=True),'index_sha256':sha(index),'stash':subprocess.check_output(['git','stash','list'],env=env,text=True),'status':subprocess.check_output(['git','status','--porcelain=v1'],env=env,text=True)}
for label,key in [('head','head'),('index','index_sha256'),('stash','stash')]: state[label+'_preserved']=state[key]==before[key]
state['scope_ok']=not state['deleted'] and not state['unexpected']; assert state['scope_ok'] and all(state[k+'_preserved'] for k in ['head','index','stash'])
(e/'preservation.json').write_text(json.dumps(state,indent=2)); (e/'changed-paths.json').write_text(json.dumps(changed+new,indent=2))
manifest={p:{'sha256':sha(r/p),'bytes':(r/p).stat().st_size} for p in sorted(changed+new)}
(e/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n'); (e/'SOURCE_MANIFEST.sha256').write_text(sha(e/'SOURCE_MANIFEST.json')+'  SOURCE_MANIFEST.json\n')
prior=Path('/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/validation-03')
def warnings(rows):
 return collections.Counter(tuple([row['filePath'].split('/frontend/')[-1]]+[m.get(k) for k in ['ruleId','severity','line','column','endLine','endColumn','message']]) for row in rows for m in row['messages'])
a=warnings(json.loads((prior/'LINT.json').read_text())); b=warnings(json.loads((e/'final-lint/results.json').read_text()))
warningResult={'baseline':str(prior/'LINT.json'),'current':str(e/'final-lint/results.json'),'baseline_count':sum(a.values()),'current_count':sum(b.values()),'added':list((b-a).elements()),'removed':list((a-b).elements()),'equal':a==b}; assert a==b and sum(b.values())==46
(e/'lint-identity.json').write_text(json.dumps(warningResult,indent=2))
def identities(report):
 return [(row['name'].split('/frontend/')[-1],item['fullName']) for row in report['testResults'] for item in row['assertionResults']]
current=json.loads((e/'final-targeted/results.json').read_text()); previous=json.loads((prior/'FULL_UNIT.json').read_text())
old=identities(previous); now=identities(current); files={p for p,n in now}; relevant=[item for item in old if item[0] in files]
identityResult={'baseline_full_count':len(old),'current_targeted_count':len(now),'prior_identities_in_targeted_files':len(relevant),'retained':len(set(relevant)&set(now)),'added':sorted(set(now)-set(old)),'removed_in_targeted_files':sorted(set(relevant)-set(now)),'duplicates_current':len(now)-len(set(now)),'full_918_reverification':'PARENT_PENDING_NOT_WRITER_CLAIM'}
assert not identityResult['removed_in_targeted_files'] and identityResult['duplicates_current']==0
(e/'targeted-identity.json').write_text(json.dumps(identityResult,indent=2,ensure_ascii=False))
summary=[]
for d in sorted(p for p in e.iterdir() if p.is_dir() and (p/'command.json').exists()):
 command=json.loads((d/'command.json').read_text()); row={'run':d.name,**command}
 report=d/'results.json'
 if report.exists():
  result=json.loads(report.read_text())
  if isinstance(result,dict) and 'testResults' in result:
   statuses=collections.Counter(a['status'] for suite in result['testResults'] for a in suite['assertionResults'])
   row['test_counts']={'total':result['numTotalTests'],'passed':result['numPassedTests'],'failed':result['numFailedTests'],'pending':result.get('numPendingTests',0),'assertion_statuses':dict(statuses)}
   assert row['test_counts']['total']==row['test_counts']['passed']+row['test_counts']['failed']+row['test_counts']['pending']
 summary.append(row)
(e/'RUN_SUMMARY.json').write_text(json.dumps(summary,indent=2))
check=subprocess.run(['git','diff','--check'],env=env,capture_output=True,text=True); assert check.returncode==0
print(json.dumps({'changed_baseline':len(changed),'new':len(new),'unchanged':state['unchanged_recovery_files'],'scope_ok':state['scope_ok'],'head_index_stash_preserved':True,'targeted_passed':current['numPassedTests'],'retained_targeted':identityResult['retained'],'new_test_identities':len(identityResult['added']),'lint_warning_identities':sum(b.values()),'source_manifest_sha256':sha(e/'SOURCE_MANIFEST.json'),'diff_check_exit':check.returncode},indent=2))
