from pathlib import Path
import json,csv,hashlib,subprocess,os,collections,shutil,zipfile
R=Path(__file__).resolve().parents[1];B=R.parent;P=B/'FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1';L=B/'FRONTEND_WAVE2_SLICE_1C_FOUNDATIONPAGES_LINT_CORRECTION_AND_VALIDATION_CONTINUATION_V1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):(R/p).write_text(json.dumps(x,indent=2))
def copy(q,to):to.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(q,to);assert sha(q)==sha(to)
hist=[json.loads(x) for x in (P/'BROWSER_NATIVE_EVENT_TIMELINE.jsonl').read_text().splitlines()];historical_input=[x['params'] for x in hist if x['method']=='Input.dispatchMouseEvent'];summaries=[]
for name in ['R1','R2']:
 root=R/'runs'/name;trace=json.loads((root/'trace.json').read_text());rows=trace['rows'];cmds=json.loads((root/'native-commands.json').read_text());events=[x for x in rows if x.get('kind')=='event' and x['listenerCapture']];notifications=[x for x in rows if x['kind']=='store-notification'];points=[x for x in rows if 'name' in x];down=next(x for x in events if x['type']=='pointerdown');up=next(x for x in events if x['type']=='pointerup');click=next(x for x in events if x['type']=='click');inputs=[x['params'] for x in cmds if x['method']=='Input.dispatchMouseEvent'];assert inputs==historical_input
 assert [x['state']['revision'] for x in notifications]==[2,3]
 assert notifications[0]['state']['selectedRefs'][0]['localId']=='project-node' and notifications[1]['state']['selectedRefs']==[]
 assert len({(x['state']['store'],x['state']['lifetime']) for x in notifications})==1
 assert all(x['activeCommittedStores']==[x['state']['store']] for x in notifications)
 assert 'at U ' in notifications[1]['stack'] and 'at onClick ' in notifications[1]['stack']
 assert 'at P ' not in notifications[1]['stack']
 for phase in [down,up,click]:
  node=next(n for n in phase['geometry']['nodes'] if n['id']=='project-node')['rect'];assert node['left']<=phase['clientX']<=node['right'] and node['top']<=phase['clientY']<=node['bottom']
 summary={'run':name,'input_equal_historical':True,'input':inputs,'event_type_sequence':[x['type'] for x in events],'notifications':notifications,'pointerdown':down,'pointerup':up,'click':click,'duration_pointerdown_to_click_ms':click['at']-down['at'],'duration_selected_to_cleared_ms':notifications[1]['at']-notifications[0]['at'],'native_command_count':len(cmds),'cdp_error_count':sum('error' in x['result'] for x in cmds),'logpoint_hit_counts':dict(collections.Counter(x['name'] for x in points)),'check_count':json.loads((root/'bounded-result.json').read_text())['checks_completed'],'process_receipts':json.loads((root/'process-receipts.json').read_text()),'ports':json.loads((root/'port-cleanup.json').read_text())}
 if name=='R2':
  inventories=[x for x in points if x['name']=='reconcile-inventory'];assert all(x['projectNodeMatches']==1 for x in inventories);assert len({x['adapter'] for x in inventories})==1
  action=next(x for x in points if x['name']=='dispatch-action');request=next(x for x in points if x['name']=='select-request' and not x['request']['refs']);nodrag=next(x for x in points if x['name']=='no-drag-return');background=next(x for x in points if x['name']=='background-click');assert action['action']=={'category':'LOCAL_EPHEMERAL','type':'select','ids':[]};assert request['request']['mode']=='replace' and request['request']['revision']==2 and request['requestLifetime']==request['lifetime'];assert nodrag['moved'] is False and nodrag['suppression'] is False and nodrag['delta']=={'x':0,'y':0};assert background['isStage'] is True
  summary['causal_boundary']={'action':action,'request':request,'nodrag':nodrag,'background':background,'inventory_calls':len(inventories),'adapter_ids':list({x['adapter'] for x in inventories}),'all_inventory_project_node_matches':1,'retire_hits':sum(x['name']=='retirement' for x in points),'register_hits':sum(x['name']=='register' for x in points),'reveal_hits':sum(x['name']=='reveal' for x in points)}
 summaries.append(summary)
 (root/'event-store-timeline.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
save('static/MEASURED_CAUSAL_SUMMARY.json',summaries)
# Source correspondence incl. original relevant context files not selected by first path filter.
manifest=list(csv.DictReader((L/'SOURCE_TREE_MANIFEST.tsv').open(),delimiter='\t'));by_path={x['path']:x for x in manifest}
for f in ['frontend/src/components/app-shell/AppShell.tsx','frontend/src/styles/foundation.css','frontend/src/foundation/projectContext.tsx','frontend/src/app/routeTree.tsx']:
 q=L/'snapshot'/f;assert sha(q)==by_path[f]['sha256'];copy(q,R/'static/source'/f)
for f,h in {'frontend/src/surfaces/FoundationPages.tsx':'f7b790ddcd3d5a529cbc43c744381f2bbf6578d5','frontend/src/interaction/InteractionShell.test.tsx':'bbfc026f2a7c972a880dfd838bf8c56d7086c474','frontend/src/product/canvas/WorkspaceCanvas.test.tsx':'6359cfc638c1948b8d6758cff05e8437842e1509'}.items():assert by_path[f]['blob']==h
contracts=[]
for directory,files in [('FRONTEND_WAVE2_SLICE_1C_ROUTE_SELECTION_LIFETIME_DECISION_RECOVERY_V1',['ROUTE_SELECTION_UX_CONTRACT.md','ROUTE_SELECTION_LIFETIME_DECISIONS.tsv','ROUTE_SELECTION_LIFETIME_TEST_PLAN.tsv','ROUTE_TRANSITION_MATRIX.tsv']),('FRONTEND_WAVE2_SLICE_1C_ROUTE_SELECTION_LIFETIME_BOUNDED_IMPLEMENTATION_V1',['WRITER_TASK.txt']),('FRONTEND_WAVE2_SELECTION_INVARIANTS_AND_CANVAS_MULTI_SELECTION_BOUNDED_IMPLEMENTATION_V1',['SCOPED_PRESENTATION_REF_MODEL.md'])]:
 for f in files:
  q=B/directory/f;to=R/'inputs/contracts'/directory/f;copy(q,to);contracts.append({'path':str(q),'sha256':sha(q),'authority':'Historical document; original proposal/draft labels preserved. Adoption recorded by Slice1C writer scope; current task source pins govern diagnosis.'})
save('inputs/contract-provenance.json',contracts)
# Preserve key predecessor records, exact manifests and original sealed reports/archives.
for f in ['FINAL_REPORT.txt','FRONTEND_WAVE2_SLICE_1C_BROWSER_ENVIRONMENT_CORRECTED_REVIEW_UPLOAD.txt','FRONTEND_WAVE2_SLICE_1C_BROWSER_ENVIRONMENT_CORRECTED_REVIEW_PACKAGE.zip','EVIDENCE_MANIFEST.sha256','BROWSER_NATIVE_EVENT_TIMELINE.jsonl','BROWSER_NATIVE_RAW.log','BROWSER_NATIVE_RESULTS.json','BROWSER_INPUT_SEAL.json','PYTHON_ENVIRONMENT_MANIFEST.json','HARNESS_SELFQUALIFICATION.json','VALIDATION_POLICY_CONTINUITY.json']:
 copy(P/f,R/'inputs/previous-environment'/f)
copy(L/'FRONTEND_WAVE2_SLICE_1C_FOUNDATIONPAGES_LINT_CORRECTED_REVIEW_PACKAGE.zip',R/'inputs/previous-lint/FRONTEND_WAVE2_SLICE_1C_FOUNDATIONPAGES_LINT_CORRECTED_REVIEW_PACKAGE.zip')
for q in (L/'build').rglob('*'):
 if q.is_file():copy(q,R/'inputs/build'/q.relative_to(L/'build'))
# Fresh measured end-preservation. Other lanes not continuously monitored.
preservation={}
for label,path in [('canonical',Path('[LOCAL_PRODUCT_REPOSITORY]')),('historical-worktree',Path('[LOCAL_FRONTEND_WORKTREE]'))]:
 prev=json.loads((R/'inputs'/f'{label}-tracked-before.json').read_text());changes=[]
 for f,old in prev['files'].items():
  q=path/f
  if q.is_symlink():new={'symlink':os.readlink(q)}
  elif q.is_file():new={'sha256':sha(q),'mode':q.stat().st_mode}
  else:new={'absent':True}
  if new!=old:changes.append({'path':f,'before':old,'after':new})
 index=Path(prev['index']);preservation[label]={'tracked_count':len(prev['files']),'changes':changes,'index_unchanged':sha(index)==prev['index_sha256']}
 for args,name in [(['status','--porcelain=v1','-uall'],'status'),(['rev-parse','HEAD'],'head'),(['symbolic-ref','-q','HEAD'],'branch'),(['stash','list'],'stash')]:
  p=subprocess.run(['git','--no-optional-locks','-C',str(path),*args],capture_output=True);data=p.stdout+p.stderr;(R/'static'/f'{label}-{name}-after.txt').write_bytes(data);preservation[label][name+'_unchanged']=data==(R/'inputs'/f'{label}-{name}.txt').read_bytes()
repo='[LOCAL_PRODUCT_REPOSITORY]'
for args,name in [(['show-ref'],'refs'),(['worktree','list','--porcelain'],'registry')]:
 data=subprocess.check_output(['git','--no-optional-locks','-C',repo,*args]);(R/'static'/f'git-{name}-after.txt').write_bytes(data);preservation[name+'_unchanged']=data==(R/'inputs'/f'git-{name}.txt').read_bytes()
obs=json.loads((R/'inputs/skill-memory-before.json').read_text());new={}
for root in [Path('[LOCAL_AGENT_HOME]/skills/software-development/systematic-debugging'),Path('[LOCAL_AGENT_HOME]/skills/software-development/frontend-contract-first-implementation'),Path('[LOCAL_AGENT_HOME]/memories')]:
 for q in root.rglob('*'):
  if q.is_file():new[str(q)]={'sha256':sha(q),'mtime_ns':q.stat().st_mtime_ns}
preservation['skill_memory']={'baseline_count':len(obs),'end_count':len(new),'differences':[{'path':f,'before':obs.get(f),'after':new.get(f)} for f in sorted(set(obs)|set(new)) if obs.get(f)!=new.get(f)],'task_issued_writes':0,'window':'after initial skill loading/preflight through analyze.py; two relevant skill directories and default memories only; not global all-skills monitoring'}
source_bad=[]
for x in manifest:
 q=L/'snapshot'/x['path'];mode='100755' if q.stat().st_mode&0o111 else '100644'
 if sha(q)!=x['sha256'] or mode!=x['mode']:source_bad.append(x['path'])
preservation['snapshot']={'entries':len(manifest),'mismatches':source_bad}
preservation['build']={'entries':8,'mismatches':[path for h,path in [line.split('  ',1) for line in (L/'BUILD_MANIFEST.sha256').read_text().splitlines()] if sha(L/'build'/path)!=h]}
pins=json.loads((P/'BROWSER_INPUT_SEAL.json').read_text())['harness'];preservation['harness']={label:[f for f,h in pins.items() if sha(root/f)!=h] for label,root in [('original',P/'harness'),('R1',R/'runs/R1'),('R2',R/'runs/R2')]}
policy=json.loads((P/'VALIDATION_POLICY_CONTINUITY.json').read_text())['pinned_files'];preservation['frozen_policy']={'entries':len(policy),'mismatches':[f for f,h in policy.items() if not (L/f).is_file() or sha(L/f)!=h]}
env=json.loads((P/'PYTHON_ENVIRONMENT_MANIFEST.json').read_text());preservation['venv']={'entries':len(env['installed_files']),'mismatches':[f for f,h in env['installed_files'].items() if sha(P/'venv'/f)!=h],'base_binary_unchanged':sha(Path('/usr/bin/python3.13'))==env['base_binary_sha256']};wheel=next((P/'wheels').glob('websockets-15.0.1*.whl'));preservation['wheel']={'sha256':sha(wheel),'expected':'f7a866fbc1e97b5c617ee4116daaa09b722101d4a3c170c787450ba409f9736f'}
prior_bad=[];prior_count=0
for line in (P/'EVIDENCE_MANIFEST.sha256').read_text().splitlines():
 h,f=line.split('  ',1);prior_count+=1
 if not (P/f).is_file() or sha(P/f)!=h:prior_bad.append(f)
preservation['previous_sealed_manifest']={'entries':prior_count,'mismatches':prior_bad}
preservation['required_originals']=[]
for item in json.loads((R/'inputs/required-input-verification.json').read_text()):
 actual=sha(Path(item['path']));preservation['required_originals'].append({'path':item['path'],'actual':actual,'match':actual==item['expected']})
save('static/PRESERVATION_READBACK.json',preservation)
print(json.dumps(preservation,indent=2))
print('timings',[(x['run'],x['duration_pointerdown_to_click_ms'],x['duration_selected_to_cleared_ms']) for x in summaries])
