"""Parent-only bounded native frontend, Lean and Coq probes; never product gates."""
from pathlib import Path
import argparse,json,os,subprocess,sys,time,traceback,uuid
D=Path(__file__).resolve().parents[1];sys.path.insert(0,str(D/'executor'))
import coverage,execution,namespaces,observe,preservation
from parent_orchestration import copy_lean
h=coverage.digest;put=coverage.put

def main():
 p=argparse.ArgumentParser();p.add_argument('area',choices=['frontend','lean','formal']);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 root=a.output.absolute()
 if root.resolve()!=root or not root.is_relative_to(D/'qualification'):raise RuntimeError('PROBE_SCOPE')
 root.mkdir();run=root/'run';run.mkdir();lane='frontend' if a.area=='frontend' else 'backend';env=execution.environment(lane,run)
 receipts=[];wrapper=h(execution.H/'execution.py');owned=[];ids=[]
 result={'result':'FAIL','probe_program':str(Path(__file__).resolve()),'formal_wrapper_sha256':wrapper,'process_receipts':receipts,'container_ids':ids,'product_gate_execution':False,'independent_review':'REQUIRED/PENDING'}
 def call(name,cmd,frontend=False,timeout=120):
  argv=execution.frontend_sandbox(cmd,run,[run/'runtime/cache/frontend',run/'runtime/tmp/frontend'],run) if frontend else execution.formal_sandbox(cmd,repo or run,run,env)
  log=root/(name+'.log');start=time.time();rc=None;error=None
  with log.open('xb') as f:
   try:rc=subprocess.run(argv,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout).returncode
   except (OSError,subprocess.TimeoutExpired) as ex:error=str(ex)
  receipt=root/(name+'.json');put(receipt,{'argv':argv,'native_exit':rc,'error':error,'start':start,'end':time.time(),'raw_log':str(log),'log_sha256':h(log),'formal_wrapper_sha256':wrapper,'synthetic_only':True});receipts.append(str(receipt))
  if rc!=0:raise RuntimeError(name+': '+str(rc)+' '+str(error))
  return log.read_text()
 before=None;repo=None
 try:
  if a.area=='frontend':
   frozen=run/'frozen';frozen.write_text('fixed')
   code='''import errno,os,subprocess,sys
from pathlib import Path
f=Path(sys.argv[1]);p=Path(os.environ['XDG_RUNTIME_DIR']);assert p.stat().st_mode&0o777==0o700
(p/'marker').write_text('private')
try: f.write_text('forbidden');raise AssertionError('ESCAPED_WRITE')
except OSError as e: assert e.errno==errno.EROFS
subprocess.Popen([sys.executable,'-B','-c',"import time;from pathlib import Path;time.sleep(.3);Path("+repr(str(p/'late'))+").write_text('late')"],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print('READONLY_PRIVATE_PID_XDG_PASS')
'''
   call('frontend',[sys.executable,'-B','-c',code,str(frozen)],True);time.sleep(.5)
   assert frozen.read_text()=='fixed' and (Path(env['XDG_RUNTIME_DIR'])/'marker').read_text()=='private'
   assert not (Path(env['XDG_RUNTIME_DIR'])/'late').exists()
   result.update(readonly='PASS',private_pid='PASS',xdg_runtime='PASS',result='PASS')
  elif a.area=='lean':
   copy_lean(run);dest=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux'
   c=preservation.Collector(roots=[dest],expected_nonempty=[dest]).capture();put(root/'collector.json',c);assert c['result']=='COMPLETE'
   synth=Path(env['TMPDIR'])/'Runtime.lean';synth.write_text('theorem synthetic_runtime_identity (n : Nat) : n = n := by rfl\n')
   assert 'version 4.19.0' in call('lean-version',[str(dest/'bin/lean'),'--version'])
   call('lean-compile',[str(dest/'bin/lean'),'--root='+str(synth.parent),'-o',str(synth.with_suffix('.olean')),str(synth)])
   assert synth.with_suffix('.olean').stat().st_size>0
   call('host-tmp',[sys.executable,'-B','-c','from pathlib import Path;Path("/tmp/runtime-marker").write_text("owned")'])
   assert (Path(env['TMPDIR'])/'runtime-marker').read_text()=='owned'
   result.update(result='PASS',output_sha256=h(synth.with_suffix('.olean')),strict_collector='PASS',host_tmp_provenance='PASS',archive_reverified=False)
  else:
   inv=json.loads((execution.O/'inputs/PROOF_GATE_INVENTORY.json').read_text());env.update(inv['environment'])
   repo=run/'sources/backend';namespaces.clone(execution.O/'sources/backend',repo)
   paths=execution.exact(repo)+[p for p in (repo/'.git').rglob('*') if p.is_file()]
   before=observe.snapshot(paths);put(root/'source-before.json',before)
   result.update(coq_image=inv['environment']['COQ_IMAGE'],script_sha256=h(repo/'scripts/formal/validate-faof2.sh'))
   assert result['script_sha256']==inv['pins']['candidate/scripts/formal/validate-faof2.sh']
   image=call('image-inspect',['podman','image','inspect',result['coq_image'],'--format','{{.Id}}']).strip()
   assert image==inv['coq_image_id_raw'];result['observed_coq_image_id']=image
   info=json.loads(call('engine-info',['podman','info','--format','json']));assert info['host']['security']['selinuxEnabled'] is False
   result['selinux_enabled']=False
   def container(name,tail):
    label='ep19-qualification-'+uuid.uuid4().hex;cid=run/'runtime'/(name+'.cid');owned.append((label,cid))
    text=call(name,['podman','run','--pull=never','--network=none','--name',label,'--cidfile',str(cid),*tail])
    value=cid.read_text().strip();assert len(value)==64 and all(c in '0123456789abcdef' for c in value);ids.append(value)
    return text
   assert 'version 8.20.1' in container('coq-version',[image,'coqc','--version'])
   synth=run/'runtime/synthetic';synth.mkdir();(synth/'Runtime.v').write_text('Theorem synthetic_runtime_identity : forall n : nat, n = n.\nProof. intros n. reflexivity. Qed.\n')
   output=container('coq-compile',['-v',str(repo)+':/workspace:Z,ro','-v',str(synth)+':/synthetic:ro','-w','/workspace',image,'sh','-ec',
    'test ! -w /workspace/scripts/formal/validate-faof2.sh; sha256sum /workspace/scripts/formal/validate-faof2.sh /synthetic/Runtime.v; coqc -dump-glob /tmp/Runtime.glob -o /tmp/Runtime.vo /synthetic/Runtime.v; test -s /tmp/Runtime.vo; sha256sum /tmp/Runtime.glob /tmp/Runtime.vo; cat /proc/self/mountinfo'])
   assert result['script_sha256'] in output and h(synth/'Runtime.v') in output
   assert not (Path(env['TMPDIR'])/'Runtime.vo').exists()
   call('host-tmp',[sys.executable,'-B','-c','from pathlib import Path;Path("/tmp/host-marker").write_text("owned")'])
   assert (Path(env['TMPDIR'])/'host-marker').read_text()=='owned'
   result.update({k:'PASS' for k in ('namespace_tmp_probe','container_tool_visibility','namespace_bind_interpretation','output_path_provenance')})
   result.update(result='PASS',container_output_location='Container-private /tmp; hashes and mountinfo captured before explicit owned-container removal. Host bwrap /tmp independently probed.')
 except Exception as ex:result.update(result='FAIL',failure=str(ex),traceback=traceback.format_exc())
 finally:
  if a.area=='formal':
   try:
    for i,(label,cid) in enumerate(owned):
     # Only randomly named containers created by this invocation may be removed.
     if cid.exists():
      value=cid.read_text().strip();assert len(value)==64 and all(c in '0123456789abcdef' for c in value)
      if value not in ids:ids.append(value)
      call('cleanup-'+str(i),['podman','rm','--force',value])
     else:
      exists=call('missing-cid-inspect-'+str(i),['podman','ps','-a','--filter','name=^'+label+'$','--format','json'])
      assert json.loads(exists)==[], 'Uncaptured owned container; parent cleanup required: '+label
    if owned:
     remaining=json.loads(call('container-cleanup',['podman','ps','-a','--no-trunc','--format','json']))
     assert not any(x.get('Id',x.get('ID')) in ids for x in remaining)
     result.update(containers_remaining=[],container_cleanup='PASS')
    if before is not None:
     execution.exact(repo);after=observe.snapshot(list(before));put(root/'source-after.json',after);assert before==after
     result['unchanged_source']='PASS'
   except Exception as ex:result.update(result='FAIL',cleanup_or_source_failure=str(ex))
  put(root/'RESULT.json',result)
 print(json.dumps(result));return int(result['result']!='PASS')
if __name__=='__main__':raise SystemExit(main())
