import pathlib,subprocess,json,hashlib,difflib,re,collections
out=pathlib.Path(__file__).parent; root=out.parent.parent; repo=pathlib.Path('/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git',*a],cwd=repo,text=True).strip()
def write(name,data): (out/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
before=json.loads((out/'before.json').read_text())
current={p:sha(repo/p) for p in git('ls-files','--cached','--others','--exclude-standard').splitlines() if (repo/p).is_file()}
changed=sorted(p for p,h in current.items() if before['files'].get(p)!=h)
expected=sorted(['frontend/src/product/publication/PublicationWorkspace.tsx','frontend/src/product/publication/PublicationWorkspace.test.tsx','frontend/src/product/publication/publication.css'])
assert changed==expected,changed
assert set(current)==set(before['files'])
prior_changed=[p for p,h in before['prior_evidence'].items() if not (root/p).is_file() or sha(root/p)!=h]
state={'head':git('rev-parse','HEAD'),'parent':git('rev-parse','HEAD^'),'branch':git('branch','--show-current'),'stash':git('stash','list'),'index_sha256':sha(pathlib.Path(git('rev-parse','--git-path','index')))}
assert all(state[k]==before[k] for k in state)
assert not prior_changed,prior_changed
write('preservation.json',{'state':state,'unchanged_source_files':len(current)-len(changed),'source_removed':[],'source_added':[],'changed_paths':changed,'prior_evidence_verified':len(before['prior_evidence']),'prior_evidence_changed':prior_changed,'status_after':git('status','--short'),'candidate_commit':None,'no_commit_authority':'Owner requires uncommitted source; parent will capture actual tree and run seven gates.'})
patch=''
for p in changed:
 patch+=''.join(difflib.unified_diff((out/'before'/p).read_text().splitlines(True),(repo/p).read_text().splitlines(True),fromfile='a/'+p,tofile='b/'+p))
(out/'CORRECTION_01.patch').write_text(patch)
write('SOURCE_MANIFEST.json',[{'path':p,'before_sha256':before['files'][p],'after_sha256':current[p],'scope':'frontend local CSS' if p.endswith('.css') else 'frontend local regression tests' if '.test.' in p else 'frontend local component i18n prop'} for p in changed])
# Native report arithmetic and identity accounting.
def tests(p):
 d=json.loads(p.read_text()); a=[(s['name'],t['fullName'],t['status']) for s in d['testResults'] for t in s['assertionResults']]; counts=collections.Counter(t[2] for t in a)
 assert len(a)==d['numTotalTests'];assert counts['passed']==d['numPassedTests'];assert counts['failed']==d['numFailedTests']
 return d,a,{'total':len(a),'passed':counts['passed'],'failed':counts['failed'],'pending':d['numPendingTests'],'errors':d.get('numRuntimeErrorTestSuites',0)}
base,old,_=tests(out.parent/'final-targeted/results.json'); green,new,counts=tests(out/'affected-green/results.json')
oldids={(p,t) for p,t,s in old};newids={(p,t) for p,t,s in new}; assert oldids<=newids;assert len(newids)==len(new)
write('test-identity.json',{'counts':counts,'baseline_retained':len(oldids),'added':sorted(newids-oldids),'removed':sorted(oldids-newids)})
def lint(p):
 data=json.loads(p.read_text());return sorted((d['filePath'],json.dumps(m,sort_keys=True)) for d in data for m in d['messages'])
a=lint(out.parent/'final-lint/results.json');b=lint(out/'lint/results.json');assert a==b
write('lint-identity.json',{'baseline':'writer/final-lint/results.json','current':'writer/correction-01/lint/results.json','message_identity_equal':True,'warnings':sum(json.loads(m)['severity']==1 for p,m in b),'errors':sum(json.loads(m)['severity']==2 for p,m in b),'added':[],'removed':[]})
styles={}
for name in ['red-contrast','affected-green']:
 log=(out/name/'output.log').read_text();styles[name]=[json.loads(line.split('resolved) ',1)[1]) for line in log.splitlines() if 'Publication computed style evidence (happy-dom; inherited colors resolved) ' in line]
write('computed-colors.json',{'environment':'happy-dom CSSOM with actual repository CSS and rendered Publication component; explicit ancestor resolution for inherit/transparent. Not native browser evidence or visual acceptance.','runs':styles})
controls=(out/'architecture-controls/output.log').read_text();tap={k:int(re.search(r'^# '+k+r' (\d+)$',controls,re.M)[1]) for k in ['tests','pass','fail','cancelled','skipped','todo']};assert tap['tests']==sum(tap[k] for k in ['pass','fail','cancelled','skipped','todo'])
write('architecture-controls-counts.json',{'source':'architecture-controls/output.log','format':'native TAP','counts':tap})
runs={p.parent.name:json.loads(p.read_text()) for p in out.glob('*/command.json')}
for name in ['affected-green','typecheck','lint','architecture','architecture-controls']:assert runs[name]['exit']==0
runs['red-contrast']['counts']=tests(out/'red-contrast/results.json')[2]
write('RUN_SUMMARY.json',runs)
result=subprocess.run(['git','diff','--check'],cwd=repo,capture_output=True,text=True);(out/'diff-check.log').write_text(result.stdout+result.stderr);assert result.returncode==0
write('diff-check.json',{'command':['git','diff','--check'],'cwd':str(repo),'exit':result.returncode})
print(json.dumps({'changed':changed,'counts':counts,'preserved_evidence':len(before['prior_evidence']),'lint_warnings':len(b),'controls':tap},indent=2))
