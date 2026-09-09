from pathlib import Path
import json,hashlib,socket,datetime,ast
R=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text()) if p.exists() else []
def save(n,d):(R/n).write_text(json.dumps(d,indent=2,ensure_ascii=False))
def manifest(root):return [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink() and 'node_modules' not in p.parts and 'profile' not in p.parts]
initial=load(R/'INPUT_BINDING.json');preserved=[]
for group in ['source','ordinary','old_browser']:
 for x in initial[group]:assert sha(Path(x['path']))==x['sha256'],x['path']
 preserved.append({'group':group,'files':len(initial[group]),'unchanged':True})
rows={};network={};shots=[];commands=[];pids=[];assertions=[];scenarios=[]
for rd in sorted(R.glob('matrix-*')):
 ss=load(rd/'SCENARIO_RESULTS.json');aa=load(rd/'NATIVE_CHECKS.json');nn=load(rd/'BROWSER_HTTP_REQUESTS.json');ii=load(rd/'ALL_INTERCEPTED_ATTEMPTS.json');rr=[]
 for name in ['fixture','ordinary']:
  rr += [dict(json.loads(l),receiver=name) for l in (rd/(name+'-http.jsonl')).read_text().splitlines()]
 (rd/'ACTUAL_RECEIVER_REQUESTS.json').write_text(json.dumps(rr,indent=2))
 rows[rd.name]={'scenarios':len(ss),'pass':sum(s['status']=='PASS' for s in ss),'fail':sum(s['status']=='FAIL' for s in ss),'assertions':len(aa),'assertions_pass':sum(a['passed'] for a in aa),'assertions_fail':sum(not a['passed'] for a in aa)}
 network[rd.name]={'browser_events':len(nn),'interceptions':len(ii),'receiver_requests':len(rr),'browser_mutations':sum(x['method'] not in ['GET','HEAD'] for x in nn),'intercept_mutations':sum(x['method'] not in ['GET','HEAD'] for x in ii),'receiver_mutations':sum(x['method'] not in ['GET','HEAD'] for x in rr),'intercept_blocked':sum(not x['allowed_to_local_receiver'] for x in ii),'receiver_forwarded':sum(x['forwarded'] for x in rr)}
 for x in load(rd/'SERVED_MANIFEST.json'):
  root=R/'build' if x['build']=='fixture' else R.parent/'validation-02/build'
  assert sha(root/x['path'])==x['disk_sha256']==x['served_sha256']
 for c in load(rd/'COMMANDS.json'):commands.append(dict(c,run=rd.name));pids.append({'pid':c['pid'],'present':Path('/proc/'+str(c['pid'])).exists()})
 for p in rd.glob('*.png'):shots.append({'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'run':rd.name,'final_green':rd.name in ['matrix-02','matrix-03']})
 if rd.name in ['matrix-02','matrix-03']:
  assert len(ss)==18 and all(s['status']=='PASS' for s in ss) and all(a['passed'] for a in aa)
  assertions.extend(dict(a,run=rd.name) for a in aa);scenarios.extend(dict(s,run=rd.name) for s in ss)
 assert load(rd/'TEARDOWN.json')['children_exited'] and not load(rd/'TEARDOWN.json')['remaining_ports']
ports=[]
for port in [4200,4201,9279]:
 with socket.socket() as s:ports.append({'port':port,'connect_ex':s.connect_ex(('127.0.0.1',port))})
assert not any(p['present'] for p in pids) and all(p['connect_ex']!=0 for p in ports)
# Mechanically preserve all prior distinct assertions, not duplicate network accounting.
prior=[]
for run in ['matrix-05','supplemental-01','restricted-02','overflow-01']:prior+=load(R.parent/'browser-v10'/run/'NATIVE_CHECKS.json')
old={x['name']:x['expression'] for x in prior};new={x['name']:x['expression'] for x in assertions}
assert all(k in new and new[k]==v for k,v in old.items())
save('ASSERTION_PRESERVATION.json',{'prior_distinct':len(old),'all_names_and_expressions_retained':True})
colors=load(R/'matrix-03/NATIVE_CONTRAST.json')
counts={'per_run':rows,'green_runs':['matrix-02','matrix-03'],'green_scenario_executions':len(scenarios),'distinct_scenario_ids':len({s['id'] for s in scenarios}),'distinct_user_journeys':len({s['id'] for s in scenarios if s['id']!='V10-10'}),'cross_cutting_audit_ids':['V10-10'],'green_assertion_executions':len(assertions),'distinct_assertions':len(new),'assertion_repetitions':len(assertions)-len(new),'all_screenshots':len(shots),'green_screenshots':sum(s['final_green'] for s in shots),'contrast_min_by_theme':{t:min(c['contrast'] for e in colors if e['theme']==t for c in e['colors']) for t in ['dark','light']}}
assert sha(R/'runner/combined.py')==load(R/'FIRST_MATRIX_VERIFIED.json')['runner_sha256']
for p in list((R/'fixture').glob('*.ts*'))+[R/'build.mjs',R/'runner/run.py',R/'runner/control.py']:assert 'validation-01' not in p.read_text() and 'ea4798924207d4004c92910815a42753e4ab9724' not in p.read_text()
save('COUNTS.json',counts);save('FINAL_ASSERTIONS.json',assertions);save('FINAL_SCENARIO_RESULTS.json',scenarios);save('NETWORK_TOTALS.json',network);save('SCREENSHOTS.json',shots);save('NATIVE_COMMANDS_INDEX.json',commands);save('FINAL_TEARDOWN.json',{'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pids':pids,'ports':ports});save('FINAL_HASH_BINDING.json',{'tree':initial['tree'],'preserved':preserved,'fixture':manifest(R/'fixture'),'runner':manifest(R/'runner'),'build':manifest(R/'build'),'build_configuration':[{'path':str(R/n),'sha256':sha(R/n)} for n in ['build.mjs','build_run.py','BUILD_FINAL03_COMMAND.json','build.log']],'dependency_symlink':str((R/'fixture/node_modules').resolve()),'served_all_runs_match':True,'first_matrix_runner_binding_verified':True})
print(json.dumps(counts,indent=2));print(json.dumps(network,indent=2));print('BINDING_ASSERTIONS_PRESERVATION_TEARDOWN_VERIFIED')
