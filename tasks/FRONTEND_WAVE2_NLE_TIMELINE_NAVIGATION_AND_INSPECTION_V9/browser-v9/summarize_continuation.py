from pathlib import Path
import json,hashlib,socket,datetime,collections
R=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
def write(name,data):(R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assigned=read(R/'SCENARIOS.json')['scenarios']
all_results=[];all_checks=[];summaries=[];networks=[];commands=[]
for run in sorted(R.glob('continuation-run-*')):
 results=read(run/'SCENARIO_RESULTS.json');checks=read(run/'NATIVE_CHECKS.json');network=read(run/'BROWSER_HTTP_REQUESTS.json');intercept=read(run/'ALL_INTERCEPTED_ATTEMPTS.json')
 assert set(x['id'] for x in results)==set(assigned) and len(results)==len(assigned)
 for row in results:
  own=checks[row['start_assertion']:row['end_assertion']];assert row['status']!='PASS' or own and all(c['passed'] for c in own)
  all_results.append({'run':run.name,**row})
 for c in checks:all_checks.append({'run':run.name,**c})
 summaries.append({'run':run.name,'executed_unique_scenarios':len(set(x['id'] for x in results)),'passed':sum(x['status']=='PASS' for x in results),'failed':sum(x['status']=='FAIL' for x in results),'assertions':len(checks),'passed_assertions':sum(x['passed'] for x in checks),'failed_assertions':sum(not x['passed'] for x in checks),'distinct_assertion_names':len(set(x['name'] for x in checks))})
 receivers=[]
 for name in ['fixture','ordinary']:
  receivers.extend({'receiver':name,**json.loads(l)} for l in (run/(name+'-http.jsonl')).read_text().splitlines())
 networks.append({'run':run.name,'browser_network_count':len(network),'browser_methods':dict(collections.Counter(x['method'] for x in network)),'intercepted_count':len(intercept),'interceptor_blocked':[x for x in intercept if not x['allowed_to_local_receiver']],'browser_non_get_head':[x for x in network if x['method'] not in ['GET','HEAD']],'receiver_mutation_attempts':[x for x in receivers if x['method'] not in ['GET','HEAD']],'receiver_blocked_403':[x for x in receivers if x['status']==403],'receiver_requests_including_served_manifest':len(receivers)})
 cmds=read(run/'COMMANDS.json');commands.extend({'run':run.name,**x} for x in cmds)
 write(str(run.relative_to(R))+'/ACTUAL_LOCAL_RECEIVER_REQUESTS.json',receivers)
final_runs=['continuation-run-04','continuation-run-05'];final_results=[r for r in all_results if r['run'] in final_runs];final_checks=[r for r in all_checks if r['run'] in final_runs]
final_names=collections.Counter(x['name'] for x in final_checks)
counts={'tree':'a90af5baccf94a437b67e69fb1897328572a0209','assigned':len(assigned),'historical_COUNTS_unchanged':read(R/'COUNTS.json'),'run_summaries':summaries,'all_continuation_scenario_runs':len(all_results),'all_continuation_assertions':len(all_checks),'all_continuation_distinct_assertion_names':len(set(x['name'] for x in all_checks)),'final_harness_runs':final_runs,'final_executed_unique_scenarios':len(set(x['id'] for x in final_results)),'final_scenario_runs':len(final_results),'final_passed_scenario_runs':sum(x['status']=='PASS' for x in final_results),'final_failed_scenario_runs':sum(x['status']=='FAIL' for x in final_results),'final_passed_unique_scenarios':len({x['id'] for x in final_results if x['status']=='PASS'}),'final_failed_unique_scenarios':len({x['id'] for x in final_results if x['status']=='FAIL'}),'final_assertions':len(final_checks),'final_passed_assertions':sum(x['passed'] for x in final_checks),'final_failed_assertions':sum(not x['passed'] for x in final_checks),'final_distinct_assertion_names':len(final_names),'final_repeat_assertion_executions':len(final_checks)-len(final_names),'final_assertion_name_execution_counts':dict(final_names)}
write('CONTINUATION_COUNTS.json',counts);write('CONTINUATION_SCENARIO_RESULTS.json',all_results);write('CONTINUATION_ASSERTIONS.json',all_checks);write('CONTINUATION_NETWORK_ACCOUNTING.json',networks);write('CONTINUATION_NATIVE_COMMAND_EXITS.json',commands)
baseline=read(R/'ARTIFACT_MANIFEST.json');bindings={}
for kind in ['source','ordinary-build','fixture','fixture-build']:
 section=baseline[kind];root=Path(section['root']);rows=[]
 for row in section['files']:
  p=root/row['path'];h=sha(p);rows.append({'path':str(p),'baseline_sha256':row['sha256'],'current_sha256':h,'unchanged':h==row['sha256']})
 assert all(x['unchanged'] for x in rows)
 bindings[kind]=rows
bindings['previous_handoff']={'path':str(R/'BROWSER_FINAL_HANDOFF.md'),'sha256':sha(R/'BROWSER_FINAL_HANDOFF.md'),'note':'No continuation writes to this file; historical blocked report preserved.'}
for kind,root in [('fixture-continuation',R/'fixture-continuation-01'),('fixture-continuation-build',R/'build-continuation-01')]:
 bindings[kind]=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and 'node_modules' not in p.parts]
bindings['served_manifests']=[{'path':str(R/run/'SERVED_MANIFEST.json'),'sha256':sha(R/run/'SERVED_MANIFEST.json'),'all_hashes_match':all(x['disk_sha256']==x['served_sha256'] for x in read(R/run/'SERVED_MANIFEST.json'))} for run in final_runs]
bindings['harness']=[{'path':str(p),'sha256':sha(p)} for p in sorted(R.iterdir()) if p.is_file() and (p.suffix in ['.py','.mjs'] or p.name.startswith('BUILD_CONTINUATION'))]
write('CONTINUATION_HASH_BINDING.json',bindings)
shots=[{'run':run,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for run in final_runs for p in sorted((R/run).glob('*.png'))];write('CONTINUATION_SCREENSHOTS.json',shots)
ports=[]
for port in [4200,4201,9279]:
 with socket.socket() as s:ports.append({'port':port,'connect_ex':s.connect_ex(('127.0.0.1',port))})
pids=[{'run':row['run'],'name':row['name'],'pid':row['pid'],'proc_exists_now':Path('/proc/'+str(row['pid'])).exists(),'recorded_exit':row['exit']} for row in commands]
assert all(x['connect_ex']!=0 for x in ports)
assert all(not x['proc_exists_now'] for x in pids)
write('CONTINUATION_FINAL_TEARDOWN.json',{'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scoped_ports':ports,'scoped_spawned_processes':pids,'all_scoped_processes_absent':True,'all_scoped_ports_refuse':True})
print(json.dumps({k:v for k,v in counts.items() if k not in ['historical_COUNTS_unchanged','final_assertion_name_execution_counts']},indent=2));print('SCREENSHOTS',len(shots));print('HASH_BINDING_AND_TEARDOWN_PASS')
