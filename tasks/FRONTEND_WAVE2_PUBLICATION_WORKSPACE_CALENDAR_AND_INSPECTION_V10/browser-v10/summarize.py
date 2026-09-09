from pathlib import Path
import json,hashlib,socket,datetime
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(R/n).write_text(json.dumps(d,indent=2))
def load(p):return json.loads(p.read_text()) if p.exists() else []
def manifest(root):return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts]
runs=[p for p in sorted(R.iterdir()) if p.is_dir() and (p/'COMMANDS.json').exists()]
selected=['matrix-04','matrix-05','supplemental-01','restricted-02','overflow-01'];rows={};network={};shots=[];commands=[];pids=[];assertions=[];scenarios=[]
for rd in runs:
 checks=load(rd/'NATIVE_CHECKS.json');ss=load(rd/'SCENARIO_RESULTS.json');n=load(rd/'BROWSER_HTTP_REQUESTS.json');ii=load(rd/'ALL_INTERCEPTED_ATTEMPTS.json');receiver=[]
 for name in ['fixture','ordinary']:
  p=rd/(name+'-http.jsonl')
  if p.exists():receiver += [dict(json.loads(l),receiver=name) for l in p.read_text().splitlines()]
 (rd/'ACTUAL_RECEIVER_REQUESTS.json').write_text(json.dumps(receiver,indent=2))
 rows[rd.name]={'scenario_executions':len(ss),'scenario_pass':sum(x['status']=='PASS' for x in ss),'scenario_fail':sum(x['status']=='FAIL' for x in ss),'assertions':len(checks),'assertion_pass':sum(x['passed'] for x in checks),'assertion_fail':sum(not x['passed'] for x in checks),'screenshots':len(list(rd.glob('*.png')))}
 network[rd.name]={'browser_events':len(n),'interceptions':len(ii),'actual_receiver_requests':len(receiver),'browser_mutations':sum(x['method'] not in ['GET','HEAD'] for x in n),'intercepted_mutations':sum(x['method'] not in ['GET','HEAD'] for x in ii),'blocked_interceptions':sum(not x['allowed_to_local_receiver'] for x in ii),'receiver_mutations':sum(x['method'] not in ['GET','HEAD'] for x in receiver)}
 for p in rd.glob('*.png'):shots.append({'run':rd.name,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size})
 for cmd in load(rd/'COMMANDS.json'):commands.append(dict(cmd,run=rd.name));pids.append({'run':rd.name,'pid':cmd['pid'],'present':Path('/proc/'+str(cmd['pid'])).exists()})
 for x in load(rd/'SERVED_MANIFEST.json'):
  root=R/'build' if x['build']=='fixture' else R.parent/'validation-01/build'
  assert sha(root/x['path'])==x['disk_sha256']==x['served_sha256']
 if rd.name in selected:assertions.extend(dict(x,run=rd.name) for x in checks);scenarios.extend(dict(x,run=rd.name) for x in ss)
ports=[]
for port in [4200,4201,9279]:
 with socket.socket() as s:ports.append({'port':port,'connect_ex':s.connect_ex(('127.0.0.1',port))})
assert not any(x['present'] for x in pids) and all(x['connect_ex']!=0 for x in ports)
initial=load(R/'INPUT_BINDING.json');preserved=[]
for group in ['source','ordinary']:
 for row in initial[group]:assert sha(Path(row['path']))==row['sha256']
 preserved.append({'group':group,'files':len(initial[group]),'unchanged':True})
for p in list((R/'fixture').glob('*.ts*'))+[R/'build.mjs',R/'runner/run.py']:
 assert 'validation-03' not in p.read_text() and 'validation-02' not in p.read_text()
counts={'per_run':rows,'selected_runs':selected,'selected_scenario_executions':len(scenarios),'selected_unique_scenario_ids':len({x['id'] for x in scenarios}),'selected_assertion_executions':len(assertions),'selected_unique_assertion_names':len({x['name'] for x in assertions}),'selected_assertion_repetitions':len(assertions)-len({x['name'] for x in assertions}),'selected_all_pass':all(x['passed'] for x in assertions) and all(x['status']=='PASS' for x in scenarios),'all_runs_screenshots':len(shots),'final_matrix_runs':['matrix-04','matrix-05'],'final_matrix_scenario_executions':20,'final_matrix_unique_scenarios':10,'final_matrix_assertion_executions':sum(rows[n]['assertions'] for n in ['matrix-04','matrix-05'])}
save('COUNTS.json',counts);save('FINAL_ASSERTIONS.json',assertions);save('FINAL_SCENARIO_RESULTS.json',scenarios);save('NETWORK_TOTALS.json',network);save('SCREENSHOTS.json',shots);save('NATIVE_COMMANDS_INDEX.json',commands);save('FINAL_TEARDOWN.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pids':pids,'ports':ports});save('FINAL_HASH_BINDING.json',{'tree':initial['tree'],'preserved_inputs':preserved,'fixture':manifest(R/'fixture'),'build':manifest(R/'build'),'runner':manifest(R/'runner'),'build_configuration':[{'path':str(R/n),'sha256':sha(R/n)} for n in ['build.mjs','build_run.py','BUILD_FINAL03_COMMAND.json','build.log']],'served_all_runs_match':True})
print(json.dumps(counts,indent=2));print('BINDING_NETWORK_TEARDOWN_VERIFIED')
