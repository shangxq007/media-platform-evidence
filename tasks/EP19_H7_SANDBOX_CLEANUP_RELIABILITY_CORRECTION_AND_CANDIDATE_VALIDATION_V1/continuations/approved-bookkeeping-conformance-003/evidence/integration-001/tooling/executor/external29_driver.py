"""Actual one-process external29 driver for the authorized second attempt.

Preparation is deliberately separate.  ``formal`` is the only command that can
create a formal marker, policy, baseline, preflight, or dispatch a gate.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time, traceback, uuid

ROOT=Path(__file__).resolve().parents[1]
EXECUTOR=ROOT/'executor'
QUALIFICATION=ROOT/'qualification'
sys.path[:0]=[str(EXECUTOR),str(QUALIFICATION)]
REQUIRED_RUNTIME_FILES=('runner.py','execution.py','native_observe.py','observe.py','boundary.py',
                        'bookkeeping_v3.py','capture.py','executor_adapter.py','compile.init.gradle',
                        'packaging.init.gradle','vite_closure.mjs','vite_resolution.mjs')

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def verify_required_runtime_files(root=ROOT):
    missing=[name for name in REQUIRED_RUNTIME_FILES if not (Path(root)/'executor'/name).is_file()]
    if missing:raise RuntimeError('REQUIRED_RUNTIME_WRAPPER_OR_INIT_MISSING '+','.join(missing))
    return True

def configure(path, wanted):
    path=Path(path).absolute()
    actual=digest(path)
    if wanted!=actual: raise RuntimeError('BINDING_SHA256_MISMATCH')
    os.environ['H7_BINDING_CONFIG']=str(path)
    os.environ['H7_BINDING_SHA256']=actual
    return path

def modules(binding, binding_sha256):
    configure(binding,binding_sha256)
    import binding_contract
    config=binding_contract.from_environment()
    import coverage, runner, sequence
    return config,coverage,runner,sequence

def durable(path,value,mode=0o400):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    payload=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
    try:
        view=memoryview(payload)
        while view:
            count=os.write(fd,view)
            if count<=0: raise OSError('ZERO_DURABLE_WRITE')
            view=view[count:]
        os.fsync(fd)
    finally: os.close(fd)
    parent=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(parent)
    finally: os.close(parent)

def consume_formal(run,binding,review):
    forbidden=('FORMAL_ATTEMPT.json','BASELINE_ATTEMPT.json','LAUNCHER_ATTEMPT.json','baseline.json','seal.json','runtime/START.json')
    if any((run/name).exists() for name in forbidden): raise RuntimeError('FORMAL_NAMESPACE_ALREADY_CONSUMED')
    value={'schema':'ep19-external29-formal-attempt-v1','attempt_id':uuid.uuid4().hex,
           'run_id':run.name,'state':'CONSUMED_BEFORE_POLICY_AND_BASELINE','formal_attempt':True,
           'attempt_ordinal':2,'attempt_budget_total':2,'retry_authorized':False,
           'consumed_ns':time.time_ns(),'binding':str(binding),'binding_sha256':digest(binding),
           'review':str(review),'review_sha256':digest(review)}
    durable(run/'FORMAL_ATTEMPT.json',value)
    return value

def observer_seed(config,applicability):
    import bookkeeping_v3 as bk
    from policy_builder import eligible_from_applicability
    packages=eligible_from_applicability(load(applicability))
    return {'root':str(bk.PRODUCTION_ROOT),'paths':{'usage':str(bk.PRODUCTION_ROOT/bk.USAGE_NAME),
            'lock':str(bk.PRODUCTION_ROOT/bk.LOCK_NAME),'ledger':str(bk.PRODUCTION_ROOT/bk.LEDGER_NAME)},
            'eligible_map':{name:{'package':path} for name,path in packages.items()}}

def boundary(adapter,observer,phase,run,*,strict=True,coverage_errors=()):
    events,errors=observer.boundary_events()
    method=getattr(adapter,phase.lower())
    return method(events=events,coverage_errors=[*errors,*coverage_errors],
                  coverage_complete=not errors,strict_input_integrity=strict,
                  evidence_dir=run/'runtime/bookkeeping-decisions')

def strict_capture(scope):
    import decision_evidence
    return decision_evidence.capture(set(scope['protected']),scope.get('expected_missing',[]))

def mutable_bookkeeping(path,policy):
    import bookkeeping_v3 as bk
    path=Path(path);root=Path(policy['root'])
    return str(path) in {policy['root'],*policy['paths'].values()} or (path.parent==root and bk.TEMP_RE.fullmatch(path.name))

def strict_check(run,scope,policy,phase,coverage):
    before=load(run/'baseline.json')['entries'];captured=strict_capture(scope)
    current=captured.get('entries',{});errors=captured.get('errors',[])
    keys=set(before)|set(current)
    changed=[path for path in sorted(keys) if before.get(path)!=current.get(path)]
    rejected=[path for path in changed if not mutable_bookkeeping(path,policy)]
    result={'schema':'ep19-external29-strict-boundary-v1','phase':phase,'capture_result':captured.get('result'),
            'capture_errors':errors,'changed_paths':changed,'rejected_paths':rejected,
            'OLD_STRICT_PRESERVATION_RESULT':'PASS' if not changed else 'OLD_STRICT_REJECT',
            'STRICT_INPUT_INTEGRITY':'PASS' if captured.get('result')=='COMPLETE' and not errors and not rejected else 'REJECT',
            'finished_ns':time.time_ns()}
    target=run/'runtime/strict-decisions';target.mkdir(parents=True,exist_ok=True)
    durable(target/(str(time.time_ns())+'-'+phase.lower()+'.json'),result)
    if result['STRICT_INPUT_INTEGRITY']!='PASS': raise RuntimeError('STRICT_INPUT_BOUNDARY_REJECT '+phase)
    return result

def strict_baseline(run,policy,adapter,observer,config,coverage,runner,sequence,review,binding):
    runner.put(run/'identity.json',runner.identities(run))
    extras=[run/'FORMAL_ATTEMPT.json',run/'bookkeeping-policy-v3.private.json',Path(review),Path(binding),
            Path(config['owner']),Path(config['dependency']),Path(config['qualification']),Path(config['adapter_qualification']),runner.EXECUTOR_IDENTITY]
    scope=coverage.derive(run,extras);runner.put(run/'scope.json',scope)
    import native_observe, decision_evidence
    watcher=native_observe.Watch(**coverage.watch_args(scope))
    try:
        captured=decision_evidence.capture(watcher.capture_paths,watcher.expected_missing);watcher.drain()
        if captured['result']!='COMPLETE' or captured['errors'] or watcher.rejected():
            raise RuntimeError('STRICT_BASELINE_CAPTURE_OR_OBSERVATION_REJECT')
        v3=boundary(adapter,observer,'BASELINE',run,strict=True,coverage_errors=watcher.errors)
    finally: watcher.close()
    control={'result':'COMPLETE','schema':'ep19-external29-baseline-v1','entries':captured['entries'],
             'watches':len(watcher.watches),'time':time.time(),'privacy':'PRIVATE_NOT_FOR_PUBLIC_PACKAGE',
             'approved_v3_decision':v3,'OLD_STRICT_PRESERVATION_RESULT':v3['OLD_STRICT_PRESERVATION_RESULT']}
    initdir=run/'runtime/cache/backend/gradle/init.d'
    if {p.name for p in initdir.iterdir()}!={'ep19-packaging.gradle'}: raise RuntimeError('UNDECLARED_GRADLE_INIT_INPUT')
    tools={}
    for name in ('python3','git','java','javac','node','npm','npx','bash','bwrap','podman'):
        path=shutil.which(name);tools[name]={'path':path,'realpath':str(Path(path).resolve()) if path else None,
                                            'sha256':coverage.digest(Path(path).resolve()) if path else None}
    lean=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean'
    tools['lean-4.19.0']={'path':str(lean),'realpath':str(lean.resolve()),'sha256':coverage.digest(lean)}
    runner.put(run/'toolchain.json',tools)
    inputs=[*scope['sealed_inputs'],run/'scope.json',run/'bookkeeping-policy-v3.private.json',
            initdir/'ep19-packaging.gradle',run/'toolchain.json',*[Path(v['realpath']) for v in tools.values() if v['realpath']]]
    inputs += [p for p in (run/'runtime/cache/backend/formal-tools').rglob('*') if p.is_file()]
    files=coverage.seal(inputs)
    raw=(json.dumps(control,indent=2,ensure_ascii=True)+'\n').encode();files[str(run/'baseline.json')]=hashlib.sha256(raw).hexdigest()
    sequence.durable(run/'baseline.json',control)
    runner.put(run/'seal.json',{'files':files,'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,
                                'base':runner.BASE,'policy_acceptance':'V3_COMPUTED_FIVE_CONDITIONS'})
    boundary(adapter,observer,'SEAL',run)
    return scope,files

def engineering_preflight(run,scope,policy,adapter,observer,config,coverage,runner,sequence):
    sequence.verify(run);problems=[]
    try:
        coverage.qualification_inputs(Path(config['qualification']))
        coverage.check_seal(load(run/'seal.json')['files'])
        for root in runner.repos(run): runner.exact(root)
        if load(run/'bindings.json')!=runner.bindings.build(run): raise RuntimeError('EXECUTION_BINDINGS_CHANGED')
        lean=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean'
        if not lean.is_file() or lean.is_symlink(): raise RuntimeError('LEAN_4_19_0_NOT_PREPARED')
        strict_check(run,scope,policy,'PREFLIGHT',coverage)
        v3=boundary(adapter,observer,'PREFLIGHT',run)
    except Exception as exc: problems.append(str(exc));v3=None
    result={'schema':'ep19-external29-preflight-v1','result':'ENGINEERING_READY' if not problems else 'ENGINEERING_PREFLIGHT_BLOCKED',
            'engineering_blockers':problems,'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,
            'matrix_keys':load(run/'bindings.json')['order'],'required_gates':29,'v3':v3,'product_gates':'NOT_RUN'}
    runner.put(run/'preflight.json',result)
    if problems: raise RuntimeError('ENGINEERING_PREFLIGHT_BLOCKED '+repr(problems))
    return result

def failure_results(order,runner,reason,existing=None):
    results=dict(existing or {})
    for name in order:
        results.setdefault(name,{'gate':name,'result':'NOT_RUN','reason':reason,'candidate':runner.SHA,'tree':runner.TREE})
    return results

def execute_actual_graph(run,scope,sealed,policy,adapter,observer,runner,coverage):
    matrix=load(run/'bindings.json');results={};stopped=False
    runner.compare_baseline=lambda _run,_results,**kwargs: strict_check(run,scope,policy,kwargs.get('phase','GATE_BOUNDARY'),coverage)
    for name in matrix['order']:
        if stopped:
            results[name]={'gate':name,'result':'NOT_RUN','reason':'PRIOR_REQUIRED_FAILURE','candidate':runner.SHA,'tree':runner.TREE}
            continue
        try:
            strict_check(run,scope,policy,'COMMAND_BEFORE_'+name,coverage)
            boundary(adapter,observer,'COMMAND',run)
            result=runner.run_gate(name,matrix,run,scope,sealed,results)
            strict_check(run,scope,policy,'COMMAND_AFTER_'+name,coverage)
            boundary(adapter,observer,'COMMAND',run)
            boundary(adapter,observer,'GATE',run)
        except Exception as exc:
            result={'gate':name,'result':'FAIL','native_exit':None,'wrapper_exit':1,'reason':str(exc),'traceback':traceback.format_exc(),
                    'candidate':runner.SHA,'tree':runner.TREE}
        results[name]=result
        if result.get('result')!='PASS': stopped=True
    return results,stopped

def formal(args):
    verify_required_runtime_files()
    config,coverage,runner,sequence=modules(args.binding,args.binding_sha256);run=runner.runpath(args.run_id)
    review=Path(args.review).absolute();binding=Path(args.binding).absolute()
    if args.run_id!=config['run_id']: raise RuntimeError('RUN_ID_BINDING_MISMATCH')
    decision=load(review)
    if decision.get('implementation_review')!='PASS' or decision.get('independent_final_acceptance') not in ('PENDING','REQUIRED'):
        raise RuntimeError('PARENT_IMPLEMENTATION_REVIEW_REQUIRED_FINAL_ACCEPTANCE_STAYS_SEPARATE')
    attempt=consume_formal(run,binding,review)
    applicability=Path(args.applicability).absolute();private_map=Path(args.private_map).absolute()
    observer=None;adapter=None;results={};order=load(ROOT/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json')['order']
    try:
        from observe import BoundaryObserver
        observer=BoundaryObserver(observer_seed(config,applicability))
        from policy_builder import build,write_private
        policy=build(applicability,private_map,config['owner'],config['dependency'])
        policy_path=run/'bookkeeping-policy-v3.private.json';write_private(policy_path,policy)
        from executor_adapter import RunAdapter
        expected={'candidate':config['candidate'],'tree':config['tree'],
                  'owner_sha256':config['owner_sha256'],'matrix_sha256':config['matrix_sha256']}
        adapter=RunAdapter(run,policy,consumed_attempt=attempt,binding=load(binding),expected_binding=expected)
        sequence.verify(run)
        scope,sealed=strict_baseline(run,policy,adapter,observer,config,coverage,runner,sequence,review,binding)
        engineering_preflight(run,scope,policy,adapter,observer,config,coverage,runner,sequence)
        strict_check(run,scope,policy,'PRESTART',coverage);boundary(adapter,observer,'PRESTART',run)
        runner.put(run/'runtime/START.json',{'time':time.time(),'run_id':run.name,'attempt_id':attempt['attempt_id'],
                                             'review':str(review),'review_sha256':digest(review),'sealed_inputs':sealed})
        results,stopped=execute_actual_graph(run,scope,{**sealed,str(review):digest(review)},policy,adapter,observer,runner,coverage)
        try:
            strict_check(run,scope,policy,'FINAL',coverage);boundary(adapter,observer,'FINAL',run)
            boundary(adapter,observer,'COVERAGE',run);boundary(adapter,observer,'SEAL',run)
        except Exception as exc:
            stopped=True;runner.put(run/'runtime/FINAL_FAILURE.json',{'reason':str(exc),'traceback':traceback.format_exc()})
        summary={'schema':'ep19-external29-results-v1','result':'FAIL' if stopped else 'PASS','results':results,
                 'required_gates':29,'passed_gates':sum(r.get('result')=='PASS' for r in results.values()),
                 'failed_gates':sum(r.get('result')=='FAIL' for r in results.values()),
                 'not_run_gates':sum(r.get('result')=='NOT_RUN' for r in results.values()),
                 'expected_full_backend_identities':8000,'expected_skips':29,'candidate_acceptance':'PENDING_INDEPENDENT_REVIEW',
                 'publication':'NOT_PERFORMED'}
        runner.put(run/'runtime/RESULTS.json',summary)
        return int(stopped)
    except Exception as exc:
        results=failure_results(order,runner,'FORMAL_SETUP_OR_BOUNDARY_FAILURE',results)
        failure={'schema':'ep19-external29-formal-failure-v1','reason':str(exc),'traceback':traceback.format_exc(),
                 'attempt_id':attempt['attempt_id'],'downstream_dispatch':False,'results':results,
                 'required_gates':29,'passed_gates':0,'failed_gates':0,'not_run_gates':29,'baseline_rebuild_authorized':False}
        if adapter is not None and not adapter.failure_path.exists(): adapter.fail('FORMAL_SETUP',failure)
        durable(run/'FORMAL_FAILURE.json',failure)
        return 1
    finally:
        if observer is not None: observer.close()

def endpoint_checks():
    bwrap=Path('/usr/bin/bwrap');podman=Path('/usr/bin/podman');socket=Path('/run/user/1000/podman/podman.sock')
    if not bwrap.is_file() or not os.access(bwrap,os.X_OK): raise RuntimeError('BWRAP_ENDPOINT_UNAVAILABLE')
    if not podman.is_file() or not os.access(podman,os.X_OK): raise RuntimeError('PODMAN_ENDPOINT_UNAVAILABLE')
    if not socket.is_socket(): raise RuntimeError('PODMAN_SOCKET_UNAVAILABLE')
    image='docker.io/coqorg/coq@sha256:e50d77c4c5a9aa0d76ae1b343d79c5f922da3a75054b79c5dc635895438e4674'
    env={**os.environ,'XDG_RUNTIME_DIR':'/run/user/1000','CONTAINER_HOST':'unix:///run/user/1000/podman/podman.sock'}
    observed=subprocess.check_output([str(podman),'image','inspect',image,'--format','{{.Id}}'],env=env,text=True).strip()
    if observed!='b80d66c91b4da3a1b3c5d3e6672cf8f4ab72ed2f7a6a1f0cf7d3aef747cf6a4b': raise RuntimeError('COQ_IMAGE_IDENTITY_MISMATCH')
    return {'result':'PASS','bwrap':str(bwrap),'podman':str(podman),'socket':str(socket),'coq_image':image,'coq_image_id':observed}

def fixture(args):
    """Disposable real-FS/inotify graph; never imports the product runner."""
    root=Path(args.fixture_root).absolute();out=Path(args.output).absolute()
    if root.exists() or out.exists(): raise RuntimeError('FIXTURE_NAMESPACE_MUST_BE_EXCLUSIVE')
    skills=root/'skills';package=skills/'fixture-skill';package.mkdir(parents=True);out.mkdir(parents=True)
    (package/'SKILL.md').write_text('fixture\n');(skills/'.usage.json').write_text(json.dumps({'fixture-skill':{'view_count':1,'use_count':1,'last_viewed_at':None,'last_used_at':None}}))
    (skills/'.usage.json.lock').write_bytes(b'');(skills/'.curator_ledger.jsonl').write_bytes(b'')
    import bookkeeping_v3 as bk
    policy=bk.create_policy(skills,owner_sha256='0'*64,dependency_sha256='1'*64,eligible_names=['fixture-skill'],fixture=True)
    from observe import BoundaryObserver
    from executor_adapter import RunAdapter,BoundaryReject
    run=out/'run';run.mkdir();adapter=RunAdapter(run,policy)
    dispatched=[];results={};reason=None
    try:
        with BoundaryObserver(policy) as observer:
            boundary(adapter,observer,'BASELINE',run)
            if args.scenario=='bad-coverage':
                events,errors=observer.boundary_events();adapter.preflight(events=events,coverage_errors=['WATCH_LOSS'],coverage_complete=False,evidence_dir=run/'evidence')
            if args.scenario=='capture-failure':
                (skills/'.usage.json').unlink();boundary(adapter,observer,'PREFLIGHT',run)
            boundary(adapter,observer,'PREFLIGHT',run)
            if args.scenario=='allowed':
                usage=load(skills/'.usage.json');usage['fixture-skill']['view_count']=2
                (skills/'.usage.json').write_text(json.dumps(usage));fd=os.open(skills/'.usage.json.lock',os.O_WRONLY);os.close(fd)
                boundary(adapter,observer,'PRESTART',run)
                manifest=policy['eligible_map']['fixture-skill']['manifest']
                record={'id':'abcdef123456','ts':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(timespec='microseconds'),
                        'actor':'agent','action':'edit','skill':'fixture-skill','evidence':{},'before':manifest,'after':manifest}
                with (skills/'.curator_ledger.jsonl').open('ab') as stream:stream.write((json.dumps(record,separators=(',',':'))+'\n').encode())
            else: boundary(adapter,observer,'PRESTART',run)
            for index in range(29):
                if reason:
                    results[str(index)]={'result':'NOT_RUN'};continue
                dispatched.append(index)
                subprocess.check_call([sys.executable,'-c','pass'],cwd=root)
                if args.scenario=='disallowed' and index==0:(package/'SKILL.md').write_text('changed then restored is still observed\n')
                try:
                    boundary(adapter,observer,'COMMAND',run);boundary(adapter,observer,'GATE',run)
                    results[str(index)]={'result':'PASS'}
                except Exception as exc:
                    reason=str(exc);results[str(index)]={'result':'FAIL','reason':reason}
            if not reason:
                fd=os.open(skills/'.usage.json.lock',os.O_WRONLY);os.close(fd);boundary(adapter,observer,'FINAL',run);boundary(adapter,observer,'COVERAGE',run);boundary(adapter,observer,'SEAL',run)
    except Exception as exc: reason=str(exc)
    for index in range(29):results.setdefault(str(index),{'result':'NOT_RUN'})
    receipt={'schema':'ep19-external29-fixture-result-v1','scenario':args.scenario,'fixture_only':True,'formal_attempt':False,
             'product_gate_execution':False,'result':'PASS' if args.scenario=='allowed' and not reason else 'EXPECTED_REJECT',
             'reason':reason,'dispatched':dispatched,'passed':sum(r['result']=='PASS' for r in results.values()),
             'failed':sum(r['result']=='FAIL' for r in results.values()),'not_run':sum(r['result']=='NOT_RUN' for r in results.values()),'results':results}
    durable(out/'RESULT.json',receipt);print(json.dumps(receipt,sort_keys=True));return 0

def preparation(args):
    config,coverage,runner,sequence=modules(args.binding,args.binding_sha256);run=runner.runpath(args.run_id)
    os.environ['H7_RUN_ID']=args.run_id
    if args.command=='prepare': runner.prepare(run,Path(config['qualification']));return 0
    if args.command=='revalidate':
        sys.path.insert(0,str(ROOT/'tools'))
        import revalidate_preparation
        return revalidate_preparation.main()
    if args.command=='endpoints':
        started=time.time_ns();checks=endpoint_checks();sequence.durable(run/'PREPARED_ENDPOINTS.json',{'result':'PASS','run_id':run.name,'started_ns':started,'finished_ns':time.time_ns(),'checks':checks});return 0
    if args.command=='identity':
        basis=runner.executor_identity_basis(Path(config['qualification']));value={'identity_basis':basis,'identity':hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
        if runner.EXECUTOR_IDENTITY.exists():
            if load(runner.EXECUTOR_IDENTITY)!=value:raise RuntimeError('EXISTING_EXECUTOR_IDENTITY_STALE')
        else:durable(runner.EXECUTOR_IDENTITY,value)
        runner.verify_executor_identity();print(json.dumps({'result':'PASS','identity':value['identity']}));return 0
    if args.command=='disposition':
        supplied=load(args.input);required=['instructions_preloaded','no_governance_during_window','no_unrelated_activity_during_window']
        if any(supplied.get(key) is not True for key in required) or supplied.get('pending_required_instructions')!=[] or supplied.get('new_required_instruction_action')!='STOP': raise RuntimeError('DISPOSITION_REJECT')
        value={**supplied,'schema':sequence.SCHEMA,'run_id':run.name,'prepared_ns':time.time_ns(),'basis':sequence.basis(run),
               'instruction_inputs':coverage.seal(supplied['preloaded_instruction_paths']),'instruction_inventory':sequence.instruction_inventory()}
        sequence.durable(run/'PREPARATION_DISPOSITION.json',value);return 0
    raise RuntimeError('UNKNOWN_PREPARATION_COMMAND')

def parser():
    value=argparse.ArgumentParser(description='EP19 actual external29 V3 driver; formal is one-shot and consumes attempt 2 before policy capture.')
    sub=value.add_subparsers(dest='command',required=True)
    for name in ('prepare','identity','endpoints','revalidate','disposition'):
        item=sub.add_parser(name);item.add_argument('--run-id',required=True);item.add_argument('--binding',type=Path,required=True);item.add_argument('--binding-sha256',required=True)
        if name=='disposition': item.add_argument('--input',type=Path,required=True)
    item=sub.add_parser('formal');item.add_argument('--run-id',required=True);item.add_argument('--binding',type=Path,required=True);item.add_argument('--binding-sha256',required=True);item.add_argument('--review',type=Path,required=True);item.add_argument('--applicability',type=Path,required=True);item.add_argument('--private-map',type=Path,required=True)
    item=sub.add_parser('fixture');item.add_argument('--fixture-root',type=Path,required=True);item.add_argument('--output',type=Path,required=True);item.add_argument('--scenario',choices=['allowed','disallowed','bad-coverage','capture-failure'],required=True)
    return value

def main():
    args=parser().parse_args()
    if args.command=='formal':return formal(args)
    if args.command=='fixture':return fixture(args)
    return preparation(args)
if __name__=='__main__': raise SystemExit(main())
