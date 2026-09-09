"""Actual one-process external29 driver for the bounded new opportunity.

Preparation is deliberately separate.  ``formal`` is the only command that can
create a formal marker, policy, baseline, preflight, or dispatch a gate.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time, traceback, uuid
import durability
import causal

ROOT=Path(__file__).resolve().parents[1]
EXECUTOR=ROOT/'executor'
QUALIFICATION=ROOT/'qualification'
sys.path[:0]=[str(EXECUTOR),str(QUALIFICATION)]
REQUIRED_RUNTIME_FILES=('runner.py','execution.py','native_observe.py','observe.py','boundary.py','causal.py',
                        'bookkeeping_v3.py','capture.py','executor_adapter.py','compile.init.gradle',
                        'packaging.init.gradle','vite_closure.mjs','vite_resolution.mjs','durability.py',
                        'dependency_contract.py','qualification_contract.py','freshness.py','parsers.py',
                        'vite_closure.py','parser_tools.py','artifacts.py','eligibility_coherence.py',
                        'eligibility_admission.py')

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
    config={**binding_contract.from_environment(),'binding_sha256':binding_sha256}
    import coverage, runner, sequence
    return config,coverage,runner,sequence

def durable(path,value,mode=0o400):
    path=Path(path)
    payload=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    durability.exclusive_bytes(path,payload,mode)

def consume_formal(run,binding,review,contract,control,control_consume,admission):
    forbidden=('FORMAL_ATTEMPT.json','BASELINE_ATTEMPT.json','LAUNCHER_ATTEMPT.json','baseline.json','seal.json','runtime/START.json')
    if any((run/name).exists() for name in forbidden): raise RuntimeError('FORMAL_NAMESPACE_ALREADY_CONSUMED')
    durability.fsync_directory_chain(run,ROOT)
    value={'schema':'ep19-external29-formal-attempt-v2','attempt_id':uuid.uuid4().hex,
           'run_id':run.name,'state':'CONSUMED_BEFORE_POLICY_AND_BASELINE','formal_attempt':True,
           'global_attempt_ordinal':3,'historical_attempts_consumed':'2/2',
           'new_allowance_total':1,'new_allowance_used_before':0,'new_allowance_used_after':1,
           'retry_authorized':False,
           'consumed_ns':time.time_ns(),'binding':str(binding),'binding_sha256':digest(binding),
           'review':str(review),'review_sha256':digest(review),
           'eligibility_contract':str(contract),'eligibility_contract_sha256':digest(contract),
           'control_plane_evidence':str(control),'control_plane_evidence_sha256':digest(control),
           'control_plane_consume_evidence':str(control_consume),
           'control_plane_consume_evidence_sha256':digest(control_consume),
           'preconsumption_admission':str(admission),'preconsumption_admission_sha256':digest(admission)}
    durable(run/'FORMAL_ATTEMPT.json',value)
    return value

def observer_seed(config,applicability,*,root=None):
    import bookkeeping_v3 as bk
    from policy_builder import eligible_from_applicability
    packages=eligible_from_applicability(load(applicability))
    root=Path(root or bk.PRODUCTION_ROOT)
    return {'root':str(root),'paths':{'usage':str(root/bk.USAGE_NAME),
            'lock':str(root/bk.LOCK_NAME),'ledger':str(root/bk.LEDGER_NAME)},
            'eligible_map':{name:{'package':path} for name,path in packages.items()}}

def boundary(adapter,observer,phase,run,*,strict=True,coverage_errors=(),continuous=None,
             finalize_observation=False):
    """Acquire and adjudicate one real boundary; any acquisition fault latches adapter."""
    try:
        method=getattr(adapter,phase.lower())
        if finalize_observation:
            def final_event_source():
                observer.drain(.05)
                if continuous is not None:
                    continuous.drain();continuous.validate_directory_identities()
                    continuous.drain()
                observer.drain()
                ended_ns=time.monotonic_ns()
                if continuous is not None: continuous.stop_and_drain(ended_ns)
                observer.stop_and_drain(ended_ns)
                events=list(observer.events)
                errors=list(observer.errors)
                continuous_events=list(continuous.events) if continuous is not None else []
                continuous_errors=list(continuous.errors) if continuous is not None else []
                gaps=list(continuous.gaps) if continuous is not None else []
                errors.extend(continuous_errors)
                if continuous is not None and continuous.rejected():
                    errors.append('CONTINUOUS_PROTECTION_REJECT')
                if events or continuous_events:
                    errors.append('FINAL_POST_CAPTURE_EVENT_REQUIRES_REJECT')
                return {'events':events+continuous_events,'errors':sorted(set(errors)),
                        'continuous_events':continuous_events,'continuous_errors':continuous_errors,
                        'continuous_gaps':gaps,'coverage_complete':not errors and not gaps,
                        'observer_closed':True,'continuous_closed':continuous is None or continuous.closed,
                        'observation_ended_monotonic_ns':ended_ns,
                        'shutdown_started_monotonic_ns':ended_ns,
                        'claim':'Coverage ends immediately before controlled watch removal; every event queued before that endpoint is drained and adjudicated; no claim extends after it.'}
            result=method(events=[],coverage_errors=list(coverage_errors),coverage_complete=True,
                          strict_input_integrity=strict,evidence_dir=run/'runtime/bookkeeping-decisions',
                          final_event_source=final_event_source)
            observer.events=[];observer.errors=[]
            if continuous is not None:
                continuous.events=[];continuous.errors=[];continuous.gaps=[]
            return result
        events,errors=observer.boundary_events()
        if continuous is not None:
            continuous.drain();continuous.validate_directory_identities()
            events.extend(continuous.events)
            errors.extend(continuous.errors)
            if continuous.rejected(): errors.append('CONTINUOUS_PROTECTION_REJECT')
        result=method(events=events,coverage_errors=[*errors,*coverage_errors],
                      coverage_complete=not errors,strict_input_integrity=strict,
                      evidence_dir=run/'runtime/bookkeeping-decisions')
        if continuous is not None:
            continuous.events=[];continuous.errors=[];continuous.gaps=[]
        return result
    except Exception as exc:
        if not adapter.failed:
            adapter._latch_exception('ACQUISITION_OR_'+phase,exc)
        raise

def strict_capture(scope):
    import decision_evidence
    return decision_evidence.capture(set(scope['protected']),scope.get('expected_missing',[]))

def mutable_bookkeeping(path,policy):
    import bookkeeping_v3 as bk
    path=Path(path);root=Path(policy['root'])
    return str(path) in {policy['root'],*policy['paths'].values()} or (path.parent==root and bk.TEMP_RE.fullmatch(path.name))

def strict_check(run,scope,policy,phase,coverage,continuous=None):
    if continuous is not None:
        continuous.drain();continuous.validate_directory_identities()
    before=load(run/'baseline.json')['entries'];captured=strict_capture(scope)
    if continuous is not None:
        continuous.drain();continuous.validate_directory_identities()
    current=captured.get('entries',{});errors=captured.get('errors',[])
    keys=set(before)|set(current)
    changed=[path for path in sorted(keys) if before.get(path)!=current.get(path)]
    rejected=[path for path in changed if not mutable_bookkeeping(path,policy)]
    result={'schema':'ep19-external29-strict-boundary-v1','phase':phase,'capture_result':captured.get('result'),
            'capture_errors':errors,'changed_paths':changed,'rejected_paths':rejected,
            'OLD_STRICT_PRESERVATION_RESULT':'PASS' if not changed else 'OLD_STRICT_REJECT',
            'STRICT_INPUT_INTEGRITY':'PASS' if captured.get('result')=='COMPLETE' and not errors and not rejected else 'REJECT',
            'finished_ns':time.time_ns()}
    if continuous is not None:
        result['continuous_registered_watches']=len(continuous.watches)
        result['continuous_events']=list(continuous.events)
        result['continuous_errors']=list(continuous.errors)
        result['continuous_gaps']=list(continuous.gaps)
        if continuous.rejected(): result['STRICT_INPUT_INTEGRITY']='REJECT'
    target=run/'runtime/strict-decisions';durability.ensure_directory(target,0o700)
    durable(target/(str(time.time_ns())+'-'+phase.lower()+'.json'),result)
    if continuous is not None:
        continuous.events=[];continuous.errors=[];continuous.gaps=[]
    if result['STRICT_INPUT_INTEGRITY']!='PASS': raise RuntimeError('STRICT_INPUT_BOUNDARY_REJECT '+phase)
    return result


def latching_strict_check(adapter,run,scope,policy,phase,coverage,continuous=None):
    try:
        return strict_check(run,scope,policy,phase,coverage,continuous)
    except Exception as exc:
        if not adapter.failed:
            adapter._latch_exception('STRICT_ACQUISITION_OR_'+phase,exc)
        raise

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
        v3=boundary(adapter,observer,'BASELINE',run,strict=True,coverage_errors=watcher.errors,
                    continuous=watcher)
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
        boundary(adapter,observer,'SEAL',run,continuous=watcher)
        return scope,files,watcher
    except BaseException as original:
        try:
            watcher.close()
        except BaseException as cleanup:
            raise BaseExceptionGroup('STRICT_BASELINE_ACQUISITION_AND_CLEANUP_FAILURE',
                                     [original,cleanup]) from None
        raise


def classify_gate_failure(result):
    """Keep independent causal facts; a nonzero observed exit is never a product verdict."""
    observed=dict(result.get('failure_dimensions') or {})
    dimensions={
        'native_invocation':bool(result.get('child_pid') or observed.get('native_invocation')),
        'native_exit':result.get('native_exit'),
        'native_command_exit_failure':result.get('native_exit') not in (None,0),
        'product_assertion_failure':bool(observed.get('product_assertion_failure')),
        'observer_preservation_failure':bool(
            observed.get('observer_preservation_failure') or result.get('unapproved_changed') or
            result.get('observation_errors') or result.get('gaps')),
        'workload_timeout_or_cancellation':bool(
            observed.get('workload_timeout_or_cancellation') or result.get('timeout')),
        'wrapper_or_environment_failure':bool(observed.get('wrapper_or_environment_failure')),
        'evidence_persistence_failure':bool(observed.get('evidence_persistence_failure')),
        'parser_helper_process_failure':bool(observed.get('parser_helper_process_failure')),
        'cleanup_failure':bool(observed.get('cleanup_failure') or result.get('cleanup_errors')),
    }
    classes=[]
    for flag,label in (
            ('product_assertion_failure','PRODUCT_ASSERTION_FAILURE'),
            ('observer_preservation_failure','OBSERVER_PRESERVATION_FAILURE'),
            ('workload_timeout_or_cancellation','WORKLOAD_TIMEOUT_OR_CANCELLATION'),
            ('wrapper_or_environment_failure','WRAPPER_OR_ENVIRONMENT_FAILURE'),
            ('evidence_persistence_failure','EVIDENCE_PERSISTENCE_FAILURE'),
            ('parser_helper_process_failure','PARSER_HELPER_PROCESS_FAILURE'),
            ('cleanup_failure','CLEANUP_FAILURE'),
            ('native_command_exit_failure','NATIVE_COMMAND_EXIT_FAILURE')):
        if dimensions[flag]:classes.append(label)
    if not classes:classes=['UNCLASSIFIED_FAILURE']
    return {'failure_dimensions':dimensions,'failure_classes':classes,
            'failure_class':classes[0] if len(classes)==1 else 'MULTIPLE_CAUSAL_FAILURES'}


def causal_rows(error,stage,role='secondary'):
    return causal.receipt_rows(error,role,stage)


def attached_receipt(error):
    for attribute in causal.RECEIPT_ATTRIBUTES:
        receipt=getattr(error,attribute,None)
        if isinstance(receipt,dict):return receipt
    return None


def merge_graph_exception(result,error,name,stage):
    attached=attached_receipt(error)
    current=dict(attached if isinstance(attached,dict) else result or {})
    current.update(gate=name,result='FAIL',wrapper_exit=1)
    if 'reason' not in current:
        current.update(error_type=type(error).__name__,reason=str(error),traceback=traceback.format_exc(),
                       failure_stage=stage)
    else:
        current.setdefault('primary_failure',{'error_type':current.get('error_type'),
            'reason':current.get('reason'),'traceback':current.get('traceback'),
            'failure_stage':current.get('failure_stage'),
            'failure_dimensions':current.get('failure_dimensions')})
        current['secondary_failure_stage']=stage
    incoming=causal_rows(error,stage)
    existing=list(current.get('causal_errors') or [])
    current['causal_errors']=causal.unique(existing+incoming)
    marker_rows=list(getattr(error,'failure_marker_errors',[]) or [])
    secondary=list(current.get('secondary_failures') or [])
    persistence_rows=(marker_rows if marker_rows else
                      incoming if stage=='FAILURE_MARKER_PERSISTENCE' and isinstance(result,dict) else [])
    current['secondary_failures']=causal.unique(secondary+persistence_rows)
    if persistence_rows:
        current['diagnostic_persistence_uncertain']=True
        current['diagnostic_delivery']='SANITIZED_NATIVE_LOG_PLUS_IN_MEMORY_RESULT'
    dimensions=dict(current.get('failure_dimensions') or {})
    if stage in ('FAILURE_MARKER_PERSISTENCE','RECEIPT_PERSISTENCE'):
        dimensions['evidence_persistence_failure']=True
    current['failure_dimensions']=dimensions
    current.update(classify_gate_failure(current))
    return current


def emit_persistence_uncertainty(result):
    """Best-effort diagnostic only; the owning caller handles any write failure."""
    rows=list(result.get('causal_errors') or [])+list(result.get('secondary_failures') or [])
    payload={'schema':'ep19-sanitized-native-persistence-uncertainty-v1','result':'FAIL',
             'gate':result.get('gate'),'diagnostic_persistence_uncertain':True,
             'error_types':sorted({str(row.get('error_type','UNKNOWN'))[:80] for row in rows}),
             'stages':sorted({str(row.get('stage','UNKNOWN'))[:80] for row in rows}),
             'success_allowed':False}
    print(json.dumps(payload,sort_keys=True),file=sys.stderr,flush=True)
    return True


def raise_diagnostic_emission_failure(primary,diagnostic,result,results):
    """Keep the gate/acquisition failure primary and stderr failure secondary."""
    diagnostic_rows=causal.rows(
        diagnostic,'diagnostic-stderr-emission','DIAGNOSTIC_STDERR_EMISSION',
        'secondary-for-gate-or-acquisition-failure')
    result['secondary_failures']=causal.unique(
        list(result.get('secondary_failures') or [])+diagnostic_rows)
    result['causal_errors']=causal.unique(
        list(result.get('causal_errors') or [])+diagnostic_rows)
    result.update(
        diagnostic_delivery='BEST_EFFORT_STDERR_FAILED_RETAINED_IN_FINAL_SINK',
        diagnostic_stderr_delivered=False,
        diagnostic_stderr_persistence_claim=False,
        semantic_success_artifacts_allowed=False)
    dimensions=dict(result.get('failure_dimensions') or {})
    dimensions['diagnostic_emission_failure']=True
    result['failure_dimensions']=dimensions
    primary.runner_gate_receipt=result
    primary.graph_failure_results=results
    try:
        causal.raise_composed(
            'GATE_OR_ACQUISITION_FAILURE_AND_DIAGNOSTIC_STDERR_EMISSION_FAILURE',
            primary,
            [('diagnostic-stderr-emission','DIAGNOSTIC_STDERR_EMISSION',diagnostic)],
            dimensions={'diagnostic_emission_failure':True,
                        'semantic_success_artifacts_allowed':False},
            primary_stage=result.get('failure_stage') or 'GATE_OR_ACQUISITION')
    except BaseException as combined:
        combined.runner_gate_receipt=result
        combined.graph_failure_results=results
        combined.diagnostic_stderr_delivered=False
        combined.diagnostic_stderr_persistence_claim=False
        raise combined from None


def close_owned_resources(continuous,observer):
    errors=[]
    for role,resource in (('continuous',continuous),('observer',observer)):
        if resource is None:continue
        try:resource.close()
        except BaseException as error:
            setattr(error,'cleanup_role',role);errors.append(error)
    return errors

class EngineeringPreflightBlocked(RuntimeError):
    pass


def preflight_blocked_failure(result, original):
    """Construct the original structured rejection before its receipt can fail."""
    failure=EngineeringPreflightBlocked(
        'ENGINEERING_PREFLIGHT_BLOCKED '+repr(result['engineering_blockers']))
    failure.preflight_receipt=result
    failure.preflight_receipt_persisted=False
    failure.causal_errors=list(result['causal_errors'])
    return failure


def raise_preflight_receipt_persistence_failure(failure,result,persistence):
    """Keep the rejection primary and the actual receipt write failure secondary."""
    try:
        causal.raise_composed(
            'ENGINEERING_PREFLIGHT_REJECTION_AND_RECEIPT_PERSISTENCE_FAILURE',
            failure,
            [('preflight-receipt-persistence','PREFLIGHT_RECEIPT_PERSISTENCE',
              persistence)],
            dimensions={'evidence_persistence_failure':True},
            primary_stage='ENGINEERING_PREFLIGHT')
    except BaseException as combined:
        combined.preflight_receipt=result
        combined.preflight_receipt_persisted=False
        raise combined from None


def engineering_preflight(run,scope,policy,adapter,observer,config,coverage,runner,sequence,continuous):
    sequence.verify(run);problems=[];original=None
    try:
        coverage.qualification_inputs(Path(config['qualification']))
        coverage.check_seal(load(run/'seal.json')['files'])
        for root in runner.repos(run): runner.exact(root)
        if load(run/'bindings.json')!=runner.bindings.build(run): raise RuntimeError('EXECUTION_BINDINGS_CHANGED')
        lean=run/'runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean'
        if not lean.is_file() or lean.is_symlink(): raise RuntimeError('LEAN_4_19_0_NOT_PREPARED')
        latching_strict_check(adapter,run,scope,policy,'PREFLIGHT',coverage,continuous)
        v3=boundary(adapter,observer,'PREFLIGHT',run,continuous=continuous)
    except Exception as exc:
        original=exc;problems.append(str(exc));v3=None
    result={'schema':'ep19-external29-preflight-v1','result':'ENGINEERING_READY' if not problems else 'ENGINEERING_PREFLIGHT_BLOCKED',
            'engineering_blockers':problems,'run_id':run.name,'candidate':runner.SHA,'tree':runner.TREE,
            'matrix_keys':load(run/'bindings.json')['order'],'required_gates':29,'v3':v3,'product_gates':'NOT_RUN',
            'preflight_disposition':'IRREVERSIBLY_LATCHED_REJECT' if problems else 'READY',
            'causal_errors':([] if original is None else
                             causal.receipt_rows(original,'primary','ENGINEERING_PREFLIGHT'))}
    failure=preflight_blocked_failure(result,original) if problems else None
    try:
        runner.put(run/'preflight.json',result)
    except BaseException as persistence:
        if failure is not None:
            raise_preflight_receipt_persistence_failure(failure,result,persistence)
        persistence.preflight_receipt=result
        persistence.preflight_receipt_persisted=False
        if not adapter.failed:
            adapter._latch_exception('PREFLIGHT_RECEIPT_PERSISTENCE',persistence)
        raise
    if failure is not None:
        failure.preflight_receipt_persisted=True
        raise failure from original
    return result

def failure_results(order,runner,reason,existing=None):
    results=dict(existing or {})
    for name in order:
        results.setdefault(name,{'gate':name,'result':'NOT_RUN','reason':reason,'candidate':runner.SHA,'tree':runner.TREE})
    return results


def formal_failure_document(error,attempt_id,order,runner,existing=None):
    """Build the exact formal catch-path receipt without consuming a namespace."""
    results=failure_results(order,runner,'FORMAL_SETUP_OR_BOUNDARY_FAILURE',existing)
    failure={'schema':'ep19-external29-formal-failure-v1','reason':str(error),
             'error_type':type(error).__name__,'traceback':traceback.format_exc(),
             'attempt_id':attempt_id,'downstream_dispatch':False,'results':results,
             'required_gates':29,'passed_gates':0,'failed_gates':0,'not_run_gates':29,
             'baseline_rebuild_authorized':False,
             'causal_errors':causal_rows(error,'FORMAL_BODY','primary')}
    preflight=getattr(error,'preflight_receipt',None)
    if isinstance(preflight,dict):
        failure['preflight_disposition']=preflight
        failure['preflight_receipt_persisted']=bool(
            getattr(error,'preflight_receipt_persisted',False))
    final_boundary=getattr(error,'final_failure_receipt',None)
    if isinstance(final_boundary,dict):
        failure['final_boundary_disposition']=final_boundary
        failure['final_failure_receipt_persisted']=bool(
            getattr(error,'final_failure_receipt_persisted',False))
    return failure


def final_boundary_failure_document(error):
    """Freeze the original FINAL/COVERAGE/SEAL rejection before its sink runs."""
    return {
        'schema':'ep19-external29-final-boundary-failure-v1',
        'result':'FINAL_ACCEPTANCE_REJECTED',
        'disposition':'IRREVERSIBLY_LATCHED_REJECT',
        'reason':str(error),'error_type':type(error).__name__,
        'traceback':traceback.format_exc(),
        'causal_errors':causal_rows(error,'FINAL_ACCEPTANCE','primary'),
        'semantic_success_artifacts_allowed':False,
    }


def persist_final_boundary_failure(run,runner,error):
    """Persist the actual runtime receipt without allowing its fault to replace error."""
    receipt=final_boundary_failure_document(error)
    error.final_failure_receipt=receipt
    error.final_failure_receipt_persisted=False
    try:
        runner.put(Path(run)/'runtime/FINAL_FAILURE.json',receipt)
    except BaseException as persistence:
        try:
            causal.raise_composed(
                'FINAL_ACCEPTANCE_REJECTION_AND_RECEIPT_PERSISTENCE_FAILURE',
                error,
                [('final-failure-receipt-persistence',
                  'FINAL_FAILURE_RECEIPT_PERSISTENCE',persistence)],
                dimensions={'evidence_persistence_failure':True,
                            'semantic_success_artifacts_allowed':False},
                primary_stage='FINAL_ACCEPTANCE')
        except BaseException as combined:
            combined.final_failure_receipt=receipt
            combined.final_failure_receipt_persisted=False
            raise combined from None
    error.final_failure_receipt_persisted=True
    return receipt


def formal_persistence_failure(primary_error,secondary_errors,cleanup_errors):
    """Build the actual native fallback when a final failure sink cannot persist."""
    secondary_errors=list(secondary_errors);cleanup_errors=list(cleanup_errors)
    errors=([primary_error] if primary_error is not None else [])+secondary_errors+cleanup_errors
    label=('FORMAL_PRIMARY_PERSISTENCE_AND_CLEANUP_FAILURE' if primary_error is not None
           else 'FORMAL_PERSISTENCE_OR_CLEANUP_FAILURE')
    failure=BaseExceptionGroup(label,errors)
    rows=[]
    if primary_error is not None:
        rows.extend(causal_rows(primary_error,'FORMAL_BODY','primary'))
    rows.extend(row for error in secondary_errors
                for row in causal_rows(error,'FORMAL_FAILURE_PERSISTENCE'))
    rows.extend(row for error in cleanup_errors
                for row in causal_rows(error,'FORMAL_RESOURCE_CLEANUP'))
    failure.formal_failure_causes=causal.unique(rows)
    failure.causal_errors=list(failure.formal_failure_causes)
    preflight=getattr(primary_error,'preflight_receipt',None)
    if isinstance(preflight,dict):
        failure.preflight_receipt=preflight
        failure.preflight_receipt_persisted=bool(
            getattr(primary_error,'preflight_receipt_persisted',False))
    final_boundary=getattr(primary_error,'final_failure_receipt',None)
    if isinstance(final_boundary,dict):
        failure.final_failure_receipt=final_boundary
        failure.final_failure_receipt_persisted=bool(
            getattr(primary_error,'final_failure_receipt_persisted',False))
    return failure


MAX_NATIVE_DIAGNOSTIC_OCCURRENCES=64
MAX_NATIVE_DIAGNOSTIC_BYTES=65536


def _bounded_public_text(value,limit=256):
    value=str(value)
    return value if len(value)<=limit else value[:limit]+'...'


def _public_context(value):
    keys=('context_id','parent_context_id','role','stage','association','context_kind')
    return {key:(None if value.get(key) is None else _bounded_public_text(value.get(key)))
            for key in keys if key in value}


def _public_causal_rows(error):
    rows=causal.public_rows(causal_rows(error,'NATIVE_MAIN','primary'))
    result=[]
    for row in rows[:MAX_NATIVE_DIAGNOSTIC_OCCURRENCES]:
        result.append({
            'schema':row.get('schema'),'occurrence_id':_bounded_public_text(
                row.get('occurrence_id','UNKNOWN')),
            'error_type':_bounded_public_text(row.get('error_type','UNKNOWN'),80),
            'role':_bounded_public_text(row.get('role','UNKNOWN'),80),
            'stage':_bounded_public_text(row.get('stage','UNKNOWN'),120),
            'association':_bounded_public_text(row.get('association','UNKNOWN'),160),
            'contexts':[_public_context(item) for item in row.get('contexts',())[:32]],
            'reason_sha256':row['reason_sha256'],'reason_exposed':False,
        })
    return result


def _public_disposition(error,attribute):
    receipt=getattr(error,attribute,None)
    if not isinstance(receipt,dict):return None
    allowed=('schema','result','disposition','preflight_disposition',
             'semantic_success_artifacts_allowed','downstream_dispatch')
    return {key:receipt[key] for key in allowed if key in receipt and
            isinstance(receipt[key],(str,bool,int,float,type(None)))}


def native_failure_document(error):
    """Bounded public diagnostic: topology and types, never private reason bodies."""
    document={
        'schema':'ep19-external29-native-failure-v1','result':'FAIL',
        'success_allowed':False,'native_exit':'NONZERO',
        'stderr_transport':'BEST_EFFORT_NOT_DURABLE',
        'stderr_persistence_claim':False,
        'error_type':_bounded_public_text(type(error).__name__,80),
        'causal_errors':_public_causal_rows(error),
        'causal_occurrences_truncated':len(causal_rows(
            error,'NATIVE_MAIN','primary'))>MAX_NATIVE_DIAGNOSTIC_OCCURRENCES,
    }
    preflight=_public_disposition(error,'preflight_receipt')
    if preflight is not None:
        document['preflight_disposition']=preflight
        document['preflight_receipt_persisted']=bool(
            getattr(error,'preflight_receipt_persisted',False))
    final_boundary=_public_disposition(error,'final_failure_receipt')
    if final_boundary is not None:
        document['final_boundary_disposition']=final_boundary
        document['final_failure_receipt_persisted']=bool(
            getattr(error,'final_failure_receipt_persisted',False))
    diagnostic_errors=getattr(error,'diagnostic_errors',None)
    if isinstance(diagnostic_errors,list):
        document['coherence_primary_reject']=_bounded_public_text(
            getattr(error,'primary_reason','COHERENCE_REJECT'),120)
        document['coherence_diagnostic_persistence_errors']=[{
            'sink':_bounded_public_text(row.get('sink','UNKNOWN'),32),
            'error_type':_bounded_public_text(row.get('error_type','UNKNOWN'),80),
            'reason_sha256':hashlib.sha256(str(row.get('reason','')).encode()).hexdigest(),
            'reason_exposed':False} for row in diagnostic_errors[:8] if isinstance(row,dict)]
        document['coherence_diagnostic_persistence_errors_truncated']=len(diagnostic_errors)>8
    return document


def emit_native_failure(error,fd=2):
    """Best-effort stderr transport; False explicitly means no delivery claim."""
    document=native_failure_document(error)
    payload=(json.dumps(document,sort_keys=True,separators=(',',':'))+'\n').encode()
    if len(payload)>MAX_NATIVE_DIAGNOSTIC_BYTES:
        document['causal_errors']=document['causal_errors'][:8]
        document['causal_occurrences_truncated']=True
        payload=(json.dumps(document,sort_keys=True,separators=(',',':'))+'\n').encode()
    if len(payload)>MAX_NATIVE_DIAGNOSTIC_BYTES:
        return False
    try:
        view=memoryview(payload)
        while view:
            count=os.write(fd,view)
            if count<=0:return False
            view=view[count:]
        return True
    except BaseException:
        return False

def execute_actual_graph(run,scope,sealed,policy,adapter,observer,runner,coverage,continuous):
    matrix=load(run/'bindings.json');results={};stopped=False
    runner.compare_baseline=lambda _run,_results,**kwargs: latching_strict_check(adapter,run,scope,policy,kwargs.get('phase','GATE_BOUNDARY'),coverage,continuous)
    for name in matrix['order']:
        if stopped:
            results[name]={'gate':name,'result':'NOT_RUN','reason':'PRIOR_REQUIRED_FAILURE','candidate':runner.SHA,'tree':runner.TREE}
            continue
        result=None;transition='GATE_OR_POST_COMMAND'
        try:
            latching_strict_check(adapter,run,scope,policy,'COMMAND_BEFORE_'+name,coverage,continuous)
            boundary(adapter,observer,'COMMAND',run,continuous=continuous)
            result=runner.run_gate(name,matrix,run,scope,sealed,results)
            if result.get('result')!='PASS':
                result.update(classify_gate_failure(result))
                transition='FAILURE_MARKER_PERSISTENCE'
                adapter.fail('GATE_EXECUTION_'+name,{'decision':'REJECT','failure_class':result['failure_class'],
                                                    'gate':name,'gate_receipt':result,
                                                    'semantic_success_artifacts_allowed':False})
                stopped=True
            else:
                latching_strict_check(adapter,run,scope,policy,'COMMAND_AFTER_'+name,coverage,continuous)
                boundary(adapter,observer,'COMMAND',run,continuous=continuous)
                boundary(adapter,observer,'GATE',run,continuous=continuous)
        except Exception as exc:
            if not adapter.failed:adapter._latch_exception('GATE_OR_POST_COMMAND_'+name,exc)
            result=merge_graph_exception(result,exc,name,transition)
            result.setdefault('candidate',runner.SHA);result.setdefault('tree',runner.TREE)
            result.setdefault('semantic_success_artifacts_allowed',False)
            results[name]=result
            stopped=True
            exc.runner_gate_receipt=result
            exc.graph_failure_results=results
            if result.get('diagnostic_persistence_uncertain'):
                result.update(diagnostic_delivery='BEST_EFFORT_STDERR_PENDING',
                              diagnostic_stderr_delivered=False,
                              diagnostic_stderr_persistence_claim=False)
                try:
                    emit_persistence_uncertainty(result)
                except BaseException as diagnostic:
                    raise_diagnostic_emission_failure(exc,diagnostic,result,results)
                result.update(diagnostic_delivery='BEST_EFFORT_STDERR_EMITTED_NOT_DURABLE',
                              diagnostic_stderr_delivered=True,
                              diagnostic_stderr_persistence_claim=False)
        results[name]=result
        if result.get('result')!='PASS': stopped=True
    return results,stopped

def validate_formal_admission(args,config,review):
    import eligibility_coherence as coherence
    import eligibility_admission
    contract_path=Path(args.eligibility_contract).absolute();control=Path(args.control_plane_evidence).absolute()
    admission=Path(args.admission).absolute()
    if str(contract_path)!=config['eligibility_contract'] or digest(contract_path)!=config['eligibility_contract_file_sha256']:
        raise RuntimeError('FORMAL_ELIGIBILITY_CONTRACT_BINDING_MISMATCH')
    contract=coherence.validate_contract(coherence.load(contract_path))
    coherence.validate_review(review)
    coherence.validate_control_plane(contract,control)
    coherence.validate_version_chain(contract,config,review)
    admitted=eligibility_admission.validate_admission_receipt(
        admission,config=config,contract=contract,review=review,control=control)
    control_consume=Path(args.control_plane_consume_evidence).absolute()
    coherence.validate_control_consumption(
        contract,control_consume,admission_control_sha256=digest(control))
    return contract_path,control,control_consume,admission,contract,admitted

def formal(args):
    verify_required_runtime_files()
    config,coverage,runner,sequence=modules(args.binding,args.binding_sha256);run=runner.runpath(args.run_id)
    review=Path(args.review).absolute();binding=Path(args.binding).absolute()
    if args.run_id!=config['run_id']: raise RuntimeError('RUN_ID_BINDING_MISMATCH')
    decision=load(review)
    if decision.get('implementation_review')!='PASS' or decision.get('independent_final_acceptance') not in ('PENDING','REQUIRED'):
        raise RuntimeError('PARENT_IMPLEMENTATION_REVIEW_REQUIRED_FINAL_ACCEPTANCE_STAYS_SEPARATE')
    contract_path,control,control_consume,admission,contract,admitted=validate_formal_admission(args,config,review)
    attempt=consume_formal(run,binding,review,contract_path,control,control_consume,admission)
    applicability=Path(args.applicability).absolute();private_map=Path(args.private_map).absolute()
    observer=None;continuous=None;adapter=None;results={};order=load(ROOT/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json')['order']
    primary_error=None;secondary_errors=[];return_code=1;summary=None
    try:
        from observe import BoundaryObserver
        observer=BoundaryObserver(observer_seed(config,applicability))
        from policy_builder import build,write_private
        private_inventory=Path(args.private_inventory).absolute()
        for supplied,key in ((applicability,'applicability'),(private_map,'private_map'),(private_inventory,'private_inventory')):
            if str(supplied)!=config[key] or digest(supplied)!=config[key+'_sha256']:
                raise RuntimeError('FORMAL_PRIVATE_INPUT_BINDING_MISMATCH '+key)
        coherence_private=run/'runtime/eligibility/FORMAL_POST_CONSUME.private.json'
        coherence_public=run/'runtime/eligibility/FORMAL_POST_CONSUME.json'
        policy=build(applicability,private_map,private_inventory,config['owner'],config['dependency'],
                     coherence_contract=contract_path,coherence_private=coherence_private,
                     coherence_public=coherence_public,capture_phase='FORMAL_POST_CONSUME')
        if policy['eligibility_coherence']['capture_id']==admitted['comparison']['capture_id']:
            raise RuntimeError('FORMAL_MUST_RECAPTURE_AFTER_CONSUME')
        observer.bind_policy(policy)
        policy_path=run/'bookkeeping-policy-v3.private.json';write_private(policy_path,policy)
        from executor_adapter import RunAdapter
        expected={'candidate':config['candidate'],'tree':config['tree'],
                  'owner_sha256':config['owner_sha256'],'matrix_sha256':config['matrix_sha256']}
        adapter=RunAdapter(run,policy,consumed_attempt=attempt,binding=load(binding),expected_binding=expected)
        sequence.verify(run)
        scope,sealed,continuous=strict_baseline(run,policy,adapter,observer,config,coverage,runner,sequence,review,binding)
        engineering_preflight(run,scope,policy,adapter,observer,config,coverage,runner,sequence,continuous)
        latching_strict_check(adapter,run,scope,policy,'PRESTART',coverage,continuous);boundary(adapter,observer,'PRESTART',run,continuous=continuous)
        runner.put(run/'runtime/START.json',{'time':time.time(),'run_id':run.name,'attempt_id':attempt['attempt_id'],
                                             'review':str(review),'review_sha256':digest(review),'sealed_inputs':sealed})
        results,stopped=execute_actual_graph(run,scope,{**sealed,str(review):digest(review)},policy,adapter,observer,runner,coverage,continuous)
        try:
            if stopped:
                raise RuntimeError('FAILURE_LATCH_BLOCKS_SUCCESS_FINAL')
            latching_strict_check(adapter,run,scope,policy,'FINAL',coverage,continuous);boundary(adapter,observer,'FINAL',run,continuous=continuous)
            boundary(adapter,observer,'COVERAGE',run,continuous=continuous)
            boundary(adapter,observer,'SEAL',run,continuous=continuous,finalize_observation=True)
        except Exception as exc:
            stopped=True
            persist_final_boundary_failure(run,runner,exc)
        summary={'schema':'ep19-external29-results-v1','result':'FAIL' if stopped else 'PASS','results':results,
                 'required_gates':29,'passed_gates':sum(r.get('result')=='PASS' for r in results.values()),
                 'failed_gates':sum(r.get('result')=='FAIL' for r in results.values()),
                 'not_run_gates':sum(r.get('result')=='NOT_RUN' for r in results.values()),
                 'expected_full_backend_identities':8000,'expected_skips':29,'candidate_acceptance':'PENDING_INDEPENDENT_REVIEW',
                 'publication':'NOT_PERFORMED'}
        return_code=int(stopped)
    except BaseException as exc:
        primary_error=exc
        try:
            graph_results=getattr(exc,'graph_failure_results',None)
            if isinstance(graph_results,dict):results=dict(graph_results)
            failure=formal_failure_document(
                exc,attempt['attempt_id'],order,runner,results)
            results=failure['results']
            if adapter is not None and not adapter.failure_path.exists():
                try:adapter.fail('FORMAL_SETUP',failure)
                except BaseException as marker_error:secondary_errors.append(marker_error)
            try:durable(run/'FORMAL_FAILURE.json',failure)
            except BaseException as failure_error:secondary_errors.append(failure_error)
        except BaseException as persistence_error:
            secondary_errors.append(persistence_error)
        return_code=1
    cleanup_errors=close_owned_resources(continuous,observer)
    if cleanup_errors:
        cleanup_doc={'schema':'ep19-external29-formal-cleanup-failure-v1','result':'FAIL',
                     'run_id':run.name,'attempt_id':attempt['attempt_id'],'success_allowed':False,
                     'primary_error':None if primary_error is None else causal.record(
                         primary_error,'primary','FORMAL_BODY','formal-primary'),
                     'cleanup_errors':[causal.record(error,getattr(error,'cleanup_role','unknown'),
                         'FORMAL_RESOURCE_CLEANUP','secondary-for-formal-primary') for error in cleanup_errors]}
        try:durable(run/'FORMAL_CLEANUP_FAILURE.json',cleanup_doc)
        except BaseException as cleanup_persistence_error:secondary_errors.append(cleanup_persistence_error)
    if primary_error is not None and (secondary_errors or cleanup_errors):
        raise formal_persistence_failure(
            primary_error,secondary_errors,cleanup_errors) from None
    if secondary_errors or cleanup_errors:
        raise formal_persistence_failure(
            None,secondary_errors,cleanup_errors) from None
    if primary_error is not None and not isinstance(primary_error,Exception):raise primary_error
    if summary is not None:
        try:runner.put(run/'runtime/RESULTS.json',summary)
        except BaseException as error:
            failure=BaseExceptionGroup('FORMAL_RESULT_RECEIPT_PERSISTENCE_FAILURE',[error])
            setattr(failure,'formal_failure_causes',causal_rows(error,'FORMAL_RESULT_RECEIPT_PERSISTENCE'))
            raise failure from None
    return return_code

def admission(args):
    """Standalone real admission. It cannot create any formal/baseline/START marker."""
    verify_required_runtime_files()
    config,coverage,runner,sequence=modules(args.binding,args.binding_sha256)
    run=runner.runpath(args.run_id)
    import eligibility_admission
    eligibility_admission.admit(
        config=config,binding=Path(args.binding),contract_path=Path(args.eligibility_contract),
        review=Path(args.review),control=Path(args.control_plane_evidence),run=run,
        output=Path(args.output),verify_preparation=lambda contract,current: sequence.verify(current)[0] and
        __import__('eligibility_coherence').validate_preparation(contract,current))
    return 0

def coherence_fixture(args):
    """Private qualification route through the real admission consumer, never formal."""
    config=load(args.config);config['binding_sha256']=digest(args.binding)
    import eligibility_admission
    eligibility_admission.admit(
        config=config,binding=args.binding,contract_path=args.eligibility_contract,
        review=args.review,control=args.control_plane_evidence,run=args.run,
        output=args.output,allow_fixture=True)
    return 0

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
    continuous=None;success_final_emitted=False
    try:
        with BoundaryObserver(policy) as observer:
            if args.scenario=='ancestor-change':
                import native_observe
                continuous=native_observe.Watch(protected=[package/'SKILL.md'],repositories=[],metadata_roots=[],allowed=[out],
                    enumeration_roots=[skills],pruned_roots=[],expected_missing=[],cross_lane=[],shared_git=None,
                    frozen_roots=[],bookkeeping_policy=policy)
            boundary(adapter,observer,'BASELINE',run)
            if args.scenario=='evidence-failure':
                blocked=root/'not-a-directory';blocked.write_text('x')
                events,errors=observer.boundary_events()
                adapter.preflight(events=events,coverage_errors=errors,coverage_complete=not errors,
                                  strict_input_integrity=True,evidence_dir=blocked)
            if args.scenario=='bad-coverage':
                events,errors=observer.boundary_events();adapter.preflight(events=events,coverage_errors=['WATCH_LOSS'],coverage_complete=False,evidence_dir=run/'evidence')
            if args.scenario=='capture-failure':
                (skills/'.usage.json').unlink();boundary(adapter,observer,'PREFLIGHT',run)
            boundary(adapter,observer,'PREFLIGHT',run)
            if args.scenario=='ancestor-change':
                old_mode=(root.stat().st_mode & 0o777);os.chmod(root,old_mode ^ 0o010)
                continuous.drain()
                os.chmod(root,old_mode)
                if continuous.rejected():raise RuntimeError('CONTINUOUS_ANCESTOR_PROTECTION_REJECT')
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
                fd=os.open(skills/'.usage.json.lock',os.O_WRONLY);os.close(fd);boundary(adapter,observer,'FINAL',run);boundary(adapter,observer,'COVERAGE',run);boundary(adapter,observer,'SEAL',run);success_final_emitted=True
    except Exception as exc: reason=str(exc)
    finally:
        if continuous is not None:continuous.close()
    for index in range(29):results.setdefault(str(index),{'result':'NOT_RUN'})
    receipt={'schema':'ep19-external29-fixture-result-v1','scenario':args.scenario,'fixture_only':True,'formal_attempt':False,
             'product_gate_execution':False,'result':'PASS' if args.scenario=='allowed' and not reason else 'EXPECTED_REJECT',
             'reason':reason,'dispatched':dispatched,'success_final_emitted':success_final_emitted,'passed':sum(r['result']=='PASS' for r in results.values()),
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
    value=argparse.ArgumentParser(description='EP19 external29 coherence driver; admission is non-consuming and formal consumes the unique new opportunity before policy/baseline.')
    sub=value.add_subparsers(dest='command',required=True)
    for name in ('prepare','identity','endpoints','revalidate','disposition'):
        item=sub.add_parser(name);item.add_argument('--run-id',required=True);item.add_argument('--binding',type=Path,required=True);item.add_argument('--binding-sha256',required=True)
        if name=='disposition': item.add_argument('--input',type=Path,required=True)
    for name in ('admission','formal'):
        item=sub.add_parser(name);item.add_argument('--run-id',required=True);item.add_argument('--binding',type=Path,required=True);item.add_argument('--binding-sha256',required=True);item.add_argument('--review',type=Path,required=True);item.add_argument('--eligibility-contract',type=Path,required=True);item.add_argument('--control-plane-evidence',type=Path,required=True)
        if name=='admission':item.add_argument('--output',type=Path,required=True)
        else:
            item.add_argument('--control-plane-consume-evidence',type=Path,required=True);item.add_argument('--admission',type=Path,required=True);item.add_argument('--applicability',type=Path,required=True);item.add_argument('--private-map',type=Path,required=True);item.add_argument('--private-inventory',type=Path,required=True)
    item=sub.add_parser('fixture');item.add_argument('--fixture-root',type=Path,required=True);item.add_argument('--output',type=Path,required=True);item.add_argument('--scenario',choices=['allowed','disallowed','bad-coverage','capture-failure','ancestor-change','evidence-failure'],required=True)
    item=sub.add_parser('coherence-fixture')
    for name in ('config','binding','eligibility-contract','review','control-plane-evidence','run','output'):
        item.add_argument('--'+name,type=Path,required=True)
    return value

def _dispatch_main():
    args=parser().parse_args()
    if args.command=='formal':return formal(args)
    if args.command=='admission':return admission(args)
    if args.command=='fixture':return fixture(args)
    if args.command=='coherence-fixture':return coherence_fixture(args)
    return preparation(args)

def main():
    try:return _dispatch_main()
    except SystemExit:raise
    except BaseException as error:
        emit_native_failure(error)
        return 1
if __name__=='__main__': raise SystemExit(main())
