from pathlib import Path
import json,hashlib,collections,socket,datetime
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
def manifest(root):return {'root':str(root),'files':[{'path':str(p.relative_to(root)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and 'node_modules' not in p.parts and not p.is_symlink()]}
before=read(R/'FINAL03_BEFORE_MANIFEST.json');preservation={}
for key in ['source','ordinary-build','prior-browser']:
 section=before[key];root=Path(section['root']);bad=[x['path'] for x in section['files'] if not (root/x['path']).is_file() or sha(root/x['path'])!=x['sha256']];assert not bad,(key,bad);preservation[key]={'verified_unchanged_files':len(section['files']),'mismatches':bad}
write('FINAL03_PRESERVATION.json',preservation)
results=[];checks=[];summaries=[];networks=[];commands=[];shots=[];served=[]
assigned=read(R/'SCENARIOS.json')['scenarios']
for name in ['final03-run-01','final03-run-02']:
 p=R/name;s=read(p/'SCENARIO_RESULTS.json');c=read(p/'NATIVE_CHECKS.json');assert len(s)==15 and set(x['id'] for x in s)==set(assigned);assert all(x['status']=='PASS' for x in s) and all(x['passed'] for x in c)
 assert all(x['IMPLEMENTATION_TREE']==before['tree'] for x in c)
 for row in s:assert all(x['passed'] for x in c[row['start_assertion']:row['end_assertion']])
 results.extend({'run':name,**x} for x in s);checks.extend({'run':name,**x} for x in c)
 summaries.append({'run':name,'scenarios':len(s),'pass_scenarios':sum(x['status']=='PASS' for x in s),'assertions':len(c),'pass_assertions':sum(x['passed'] for x in c),'screenshots':len(list(p.glob('*.png')))})
 net=read(p/'BROWSER_HTTP_REQUESTS.json');inter=read(p/'ALL_INTERCEPTED_ATTEMPTS.json');nav=read(p/'NAVIGATION_NETWORK_ASSERTION.json');rec=[]
 for receiver in ['fixture','ordinary']:rec.extend({'receiver':receiver,**json.loads(l)} for l in (p/(receiver+'-http.jsonl')).read_text().splitlines())
 write(name+'/ACTUAL_LOCAL_RECEIVER_REQUESTS.json',rec)
 networks.append({'run':name,'browser_network_count':len(net),'browser_methods':dict(collections.Counter(x['method'] for x in net)),'intercepted_count':len(inter),'interceptor_blocked':[x for x in inter if not x['allowed_to_local_receiver']],'intercepted_mutations':[x for x in inter if x['method'] not in ['GET','HEAD']],'browser_mutations':[x for x in net if x['method'] not in ['GET','HEAD']],'receiver_requests_including_health_and_manifests':len(rec),'receiver_mutation_attempts':[x for x in rec if x['method'] not in ['GET','HEAD']],'receiver_blocked_403':[x for x in rec if x['status']==403],'navigation_network_count':len(nav['navigation_network']),'navigation_interception_count':len(nav['navigation_interceptions']),'forbidden_navigation_network':nav['forbidden_navigation_network'],'forbidden_navigation_interceptions':nav['forbidden_navigation_interceptions']})
 cmds=read(p/'COMMANDS.json');assert next(x for x in cmds if x['name']=='tests')['exit']==0;commands.extend({'run':name,**x} for x in cmds)
 assert read(p/'TEARDOWN.json')=={'remaining_ports':[],'children_exited':True}
 for x in read(p/'SERVED_MANIFEST.json'):
  root=R/'build-final03' if x['build']=='fixture' else R.parent/'validation-03/build'
  assert sha(root/x['path'])==x['disk_sha256']==x['served_sha256']
 served.append({'run':name,'path':str(p/'SERVED_MANIFEST.json'),'sha256':sha(p/'SERVED_MANIFEST.json'),'all_disk_wire_hashes_equal':True})
 shots.extend({'run':name,'path':str(f),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(p.glob('*.png')))
names=collections.Counter(x['name'] for x in checks)
counts={'tree':before['tree'],'assigned_scenarios':len(assigned),'run_summaries':summaries,'final_runs':len(summaries),'scenario_executions':len(results),'distinct_scenarios':len({x['id'] for x in results}),'passed_scenario_executions':sum(x['status']=='PASS' for x in results),'failed_scenario_executions':sum(x['status']=='FAIL' for x in results),'assertion_executions':len(checks),'passed_assertions':sum(x['passed'] for x in checks),'failed_assertions':sum(not x['passed'] for x in checks),'distinct_assertion_names':len(names),'repeat_assertion_executions':len(checks)-len(names),'assertion_name_execution_counts':dict(names),'screenshots':len(shots)}
for n,d in [('COUNTS',counts),('SCENARIO_RESULTS',results),('ASSERTIONS',checks),('NETWORK_ACCOUNTING',networks),('NATIVE_COMMAND_EXITS',commands),('SCREENSHOTS',shots)]:write('FINAL03_'+n+'.json',d)
bindings={'tree':before['tree'],'source':before['source'],'ordinary-build':before['ordinary-build'],'fixture':manifest(R/'fixture-final03'),'fixture-build':manifest(R/'build-final03'),'runner':manifest(R/'runner-final03'),'build_config':{'path':str(R/'build-final03.mjs'),'sha256':sha(R/'build-final03.mjs')},'build_receipt':read(R/'BUILD_FINAL03_COMMAND.json'),'served':served,'react_dependency_target':str((R/'fixture-final03/node_modules').resolve()),'source_vite_config':{'path':str(R.parent/'validation-03/snapshot/frontend/vite.config.ts'),'sha256':sha(R.parent/'validation-03/snapshot/frontend/vite.config.ts')}}
assert bindings['build_receipt']['exit']==0
write('FINAL03_HASH_BINDING.json',bindings)
ports=[]
for port in [4200,4201,9279]:
 with socket.socket() as s:ports.append({'port':port,'connect_ex':s.connect_ex(('127.0.0.1',port))})
pids=[{'run':x['run'],'name':x['name'],'pid':x['pid'],'proc_exists':Path('/proc/'+str(x['pid'])).exists(),'exit':x['exit']} for x in commands]
assert all(x['connect_ex']!=0 for x in ports) and all(not x['proc_exists'] for x in pids)
write('FINAL03_TEARDOWN.json',{'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ports':ports,'processes':pids,'verified':True})
print(json.dumps({k:v for k,v in counts.items() if k!='assertion_name_execution_counts'},indent=2));print(json.dumps(networks,indent=2));print(json.dumps(preservation,indent=2));print('FINAL_BINDING_PRESERVATION_TEARDOWN_PASS')
