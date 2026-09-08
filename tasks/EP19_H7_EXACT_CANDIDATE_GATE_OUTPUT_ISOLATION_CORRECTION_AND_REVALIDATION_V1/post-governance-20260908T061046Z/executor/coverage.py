"""Derive coverage from the recovered inventory; detached input seals avoid cycles."""
from pathlib import Path
import ast, hashlib, json, os
from execution import D,O,H, git
from preservation import INSTRUCTIONS, Collector

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')

def local_imports():
    files=set(p for p in H.iterdir() if p.is_file());edges=[]
    for p in list(files):
        if p.suffix!='.py':continue
        for n in ast.walk(ast.parse(p.read_text())):
            names=[n.module] if isinstance(n,ast.ImportFrom) else [x.name for x in n.names] if isinstance(n,ast.Import) else []
            for name in names:
                if not name:continue
                target=H/(name.split('.')[0]+'.py')
                if target.is_file():files.add(target);edges.append([str(p),str(target)])
    return sorted(files),edges

def derive(run, extra_inputs=()):
    old=json.loads((O/'PROTECTION_SCOPE.json').read_text());scope=json.loads(json.dumps(old))
    helpers,edges=local_imports()
    controls=[p for p in O.iterdir() if p.is_file()] + [D/'CODEX_BRIEF.md',D/'OWNER_AUTHORIZATION.txt',D/'BOUNDED_TASK.md']
    controls += [p for p in (D/'dependency').rglob('*') if p.is_file()] if (D/'dependency').is_dir() else []
    controls += [p for p in (D/'tools').rglob('*') if p.is_file()] if (D/'tools').is_dir() else []
    controls += [D/name for name in ('NEW_EXECUTOR_IDENTITY.json','QUALIFICATION_REUSE_LEDGER.json') if (D/name).is_file()]
    controls += [D/name for name in ('CHANGED_SOURCE_INVENTORY.json','IMPLEMENTATION_REPORT.zh-CN.md','PARENT_COMMANDS.md','FINAL_FIELDS.json') if (D/name).is_file()]
    controls += [D/'HERMES_REVIEW_NOTES.md'] if (D/'HERMES_REVIEW_NOTES.md').is_file() else []
    controls += [p for p in (D/'historical/parent-verification').rglob('*') if p.is_file()] if (D/'historical/parent-verification').is_dir() else []
    controls += [p for p in (D/'diffs').rglob('*') if p.is_file()] if (D/'diffs').is_dir() else []
    controls += [O/'qualification/CONTINUATION_PRESERVATION_CONTRACT.md',O/'observations/BEFORE.json']
    controls += list((O/'inputs').rglob('*'))
    controls += list((O/'owned').rglob('*'))
    controls = [p for p in controls if p.is_file()]
    config=json.loads((run/'prepare.json').read_text())
    controls += qualification_inputs(Path(config['qualification']))
    controls += [O/'owner-clarified-execution-20260907T1120Z'/n for n in
                 ('OWNER_DECISION.txt','OWNER_PROVENANCE.json','ENGINEERING_MAPPING.md')]
    frozen_roots=[run/'runtime/cache/backend/gradle/init.d',run/'runtime/cache/backend/formal-tools']
    runtime_inputs=[run/'runtime/cache/backend/gradle/init.d/ep19-packaging.gradle']
    runtime_inputs += [p for p in frozen_roots[1].rglob('*') if p.is_file()]
    controls += runtime_inputs
    controls += [p for p in (O/'tools').rglob('*') if p.is_file()]
    instructions=list(INSTRUCTIONS)
    # Every historical entry retained; no count is used as authority for membership.
    protected=set(old['protected'])|set(map(str,helpers+controls+list(map(Path,extra_inputs))))
    instruction=Collector(roots=instructions,expected_nonempty=instructions).capture()
    if instruction['result']=='COMPLETE':protected.update(instruction['entries'])
    runtime=[str(run/'runtime'),*old['allowed']]
    overlap=[p for p in protected if any(p==r or p.startswith(r+'/') for r in runtime)
             and not any(Path(p).is_relative_to(r) for r in frozen_roots)]
    if overlap:raise RuntimeError('FROZEN_RUNTIME_OVERLAP '+repr(overlap[:5]))
    scope.update(protected=sorted(protected),allowed=sorted(set(runtime)),enumeration_roots=instructions,
                 frozen_roots=list(map(str,frozen_roots)),
                 sealed_inputs=sorted(set(map(str,helpers+controls+list(map(Path,extra_inputs))))))
    policy=[Path(p) for p in extra_inputs if Path(p).name=='bookkeeping-policy-v2.private.json']
    if len(policy)!=1:raise RuntimeError('EXACT_V2_BOOKKEEPING_POLICY_REQUIRED')
    scope['bookkeeping_policy']=str(policy[0])
    scope['bookkeeping_target']='/home/user/.hermes/skills/.usage.json'
    scope['instruction_selection_binding']={
        'mechanism':'Fixed task-local 29-gate matrix and sealed instruction/input closure; no dynamic curator/UI selection during the validation window',
        'matrix':str(O/'GATE_EXECUTION_MATRIX.json'),'matrix_sha256':digest(O/'GATE_EXECUTION_MATRIX.json'),
        'gate_count':len(json.loads((O/'GATE_EXECUTION_MATRIX.json').read_text())['order']),
        'usage_file_retained_in_accounting':True}
    # Existing ignored generated trees were never enumerated by prepare_finalize.py's
    # --others --exclude-standard. Keep that scope, record exact prune derivation.
    pruned=[]
    for repo in old['repositories']:
        names=git(Path(repo),'ls-files','--others','--ignored','--exclude-standard','--directory','-z')
        for raw in names.split(b'\0'):
            if raw.endswith(b'/'):pruned.append(str(Path(repo)/os.fsdecode(raw).rstrip('/')))
    failed=O.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/candidate'
    historical=json.loads((O/'observations/BEFORE.json').read_text())
    scope['expected_missing']=sorted(str(failed/name) for name,row in historical['failed_scene'].items() if row.get('missing') is True)
    scope['protected']=sorted(set(scope['protected'])|{str(O/'observations/BEFORE.json')})
    scope['sealed_inputs']=sorted(set(scope['sealed_inputs'])|{str(O/'observations/BEFORE.json')})
    scope['pruned_roots']=sorted(set(pruned)-set(old['metadata_roots']))
    scope['instruction_capture']=instruction
    scope['coverage_derivation']={'original_inventory_sha256':digest(O/'PROTECTION_SCOPE.json'),
        'original_entries':len(old['protected']),'original_unique':len(set(old['protected'])),
        'retained_all_original_entries':set(old['protected'])<=protected,'protected_count':len(protected),
        'helper_import_edges':edges,'helper_files':list(map(str,helpers)),
        'ignored_prune_source':'git ls-files --others --ignored --exclude-standard --directory -z; existing generated ignored scope excluded by recovered --exclude-standard inventory',
        'classes':{'FROZEN_EXECUTION_INPUT':sorted(protected),'DECLARED_RUNTIME_OUTPUT':runtime,
                   'RUNTIME_EXCLUSIONS_FROZEN_SUBTREES':list(map(str,frozen_roots)),
                   'SEALED_DELIVERY':[]},'delivery':'No delivery artifact built; parent owns publication',
        'limits':'New/deleted nonignored repository subtrees reject. Existing ignored cache bodies are not censused. Ancestors watched without ancestor enumeration. Endpoints do not cover gaps between commands.'}
    import namespaces
    return namespaces.scope_roles(scope,run)

def watch_args(scope,shadow=False):
    names=['protected','repositories','metadata_roots','allowed','cross_lane','shared_git','enumeration_roots','pruned_roots','expected_missing']
    args={k:scope[k] for k in names}
    args['frozen_roots']=scope.get('frozen_roots',[])
    args['bookkeeping_policy']=scope.get('bookkeeping_policy')
    if shadow:args.update(shadow_root=scope['shadow_root'],shadow_declared=scope['shadow_declared'])
    return args

def seal(paths):return {str(p):digest(p) for p in sorted(set(map(Path,paths)))}
def check_seal(files):
    for p,h in files.items():
        if digest(p)!=h:raise RuntimeError('FROZEN_INPUT_CHANGED '+p)

def qualification_inputs(path):
    """Detached closure: source programs, reused preimages, raw inputs and receipts.

    The receipt itself is sealed by the run, never by its own dependency map.
    Successful synthetic preparation does not imply a qualified container runtime.
    """
    path=Path(path);q=json.loads(path.read_text())
    if q.get('schema') not in ('ep19-owner-qualified-v1','ep19-output-corrections-v2','ep19-bookkeeping-v2-qualified-v1','ep19-lean-materialization-qualified-v1') or not q.get('dependencies'):
        raise RuntimeError('QUALIFICATION_CLOSURE_MISSING')
    files=q['dependencies'];helpers=q.get('helpers',{})
    if set(helpers)!=set(map(str,local_imports()[0])):
        raise RuntimeError('QUALIFICATION_HELPER_UNIVERSE_CHANGED')
    if not set(helpers)<=set(files):raise RuntimeError('QUALIFICATION_HELPERS_NOT_IN_CLOSURE')
    if any(files[p]!=h for p,h in helpers.items()):raise RuntimeError('QUALIFICATION_HELPER_BINDING')
    check_seal(files)
    for name in ('qualification_program','raw_log','process_receipt','result_receipt') + (('reuse_ledger',) if q.get('schema')=='ep19-owner-qualified-v1' else ()):
        if q.get(name) not in files:raise RuntimeError('QUALIFICATION_REQUIRED_DEPENDENCY '+name)
    process=json.loads(Path(q['process_receipt']).read_text())
    result=json.loads(Path(q['result_receipt']).read_text())
    if process.get('native_exit')!=0 or process.get('log_sha256')!=files[q['raw_log']]:
        raise RuntimeError('QUALIFICATION_NATIVE_OR_LOG_REJECT')
    if result.get('result')!='PASS' or result.get('tests',0)<=0 or result.get('failures')!=0 or result.get('errors')!=0:
        raise RuntimeError('QUALIFICATION_RESULT_REJECT')
    if q.get('result')!='PASS' or q.get('product_gate_execution') is not False:
        raise RuntimeError('SYNTHETIC_QUALIFICATION_NOT_PASS')
    if q.get('schema')=='ep19-bookkeeping-v2-qualified-v1':
        required_areas=('bookkeeping_parser','bookkeeping_metadata','observer_reducer','decision_evidence',
                        'baseline_seal','preflight','prestart','command_boundary','final_acceptance',
                        'launch_reachability','strict_scope','evidence_write_failure','identity_binding')
        if any(q.get(area)!='PASS' for area in required_areas):
            raise RuntimeError('V2_QUALIFICATION_AREA_NOT_PASS')
        for name in ('red_log','green_log','qualification_matrix','reuse_ledger'):
            if q.get(name) not in files:raise RuntimeError('V2_QUALIFICATION_REQUIRED_DEPENDENCY '+name)
        if not full_capsule_reuse_qualified(q):raise RuntimeError('FULL_CAPSULE_REUSE_NOT_QUALIFIED')
    if q.get('schema')=='ep19-lean-materialization-qualified-v1':
        required_areas=('lean_materialization','link_chain_rejection','collector_compatibility',
                        'native_probe_binding','run_preparation_binding','identity_binding')
        if any(q.get(area)!='PASS' for area in required_areas):
            raise RuntimeError('LEAN_QUALIFICATION_AREA_NOT_PASS')
        for name in ('fresh_result','fresh_process','fresh_log','materialization_reuse_ledger',
                     'historical_v2_qualification'):
            if q.get(name) not in files:raise RuntimeError('LEAN_QUALIFICATION_REQUIRED_DEPENDENCY '+name)
        if q.get('tests')!=q.get('fresh_tests') or q.get('fresh_tests')<=0 or q.get('reused_tests')!=129:
            raise RuntimeError('LEAN_QUALIFICATION_ACCOUNTING')
        if not historical_v2_qualification_qualified(q):
            raise RuntimeError('HISTORICAL_V2_QUALIFICATION_REUSE_NOT_QUALIFIED')
        if not full_capsule_reuse_qualified(q):raise RuntimeError('FULL_CAPSULE_REUSE_NOT_QUALIFIED')
    return [path,*map(Path,files)]

def historical_v2_qualification_qualified(q):
    """Validate, but never relabel, the historical 129-control V2 capsule."""
    files=q.get('dependencies',{});path=q.get('historical_v2_qualification')
    if not path or path not in files:return False
    expected=D.parent/'bookkeeping-v2-20260908T004809Z/qualification/QUALIFICATION.json'
    if Path(path)!=expected:return False
    old=json.loads(Path(path).read_text())
    if old.get('schema')!='ep19-bookkeeping-v2-qualified-v1' or old.get('result')!='PASS' or old.get('tests')!=129:return False
    if old.get('product_gate_execution') is not False or not old.get('dependencies') or not old.get('helpers'):return False
    try:check_seal(old['dependencies'])
    except Exception:return False
    if not set(old['helpers'])<=set(old['dependencies']):return False
    result=json.loads(Path(old['result_receipt']).read_text())
    process=json.loads(Path(old['process_receipt']).read_text())
    if result.get('result')!='PASS' or result.get('tests')!=129 or result.get('failures')!=0 or result.get('errors')!=0:return False
    if process.get('native_exit')!=0 or process.get('log_sha256')!=old['dependencies'].get(old['raw_log']):return False
    return formal_boundary_qualified(old) and full_capsule_reuse_qualified(old)

def formal_boundary_qualified(q):
    """A PASS label cannot substitute for the actual bound container evidence."""
    files=q['dependencies'];path=q.get('formal_boundary_receipt')
    if not path or path not in files:return False
    r=json.loads(Path(path).read_text())
    required=('namespace_tmp_probe','container_tool_visibility','namespace_bind_interpretation',
              'output_path_provenance','container_cleanup','unchanged_source')
    if r.get('result')!='PASS' or any(r.get(k)!='PASS' for k in required):return False
    inv=json.loads((O/'inputs/PROOF_GATE_INVENTORY.json').read_text())
    if r.get('coq_image')!=inv['environment']['COQ_IMAGE'] or r.get('observed_coq_image_id')!=inv['coq_image_id_raw']:
        return False
    if r.get('script_sha256')!=inv['pins']['candidate/scripts/formal/validate-faof2.sh']:return False
    if r.get('formal_wrapper_sha256')!=digest(H/'execution.py'):
        reuse=q.get('formal_boundary_reuse')
        if not reuse or reuse not in files:return False
        ledger=json.loads(Path(reuse).read_text())
        if ledger.get('result')!='PASS' or ledger.get('reused_receipt')!=path or ledger.get('reused_receipt_sha256')!=files[path]:return False
        if ledger.get('old_wrapper_sha256')!=r.get('formal_wrapper_sha256') or ledger.get('current_wrapper_sha256')!=digest(H/'execution.py'):return False
        def component(source):
            tree=ast.parse(Path(source).read_text());node=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='formal_sandbox'),None)
            return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest() if node else None
        old=ledger.get('old_wrapper_source')
        if not old or old not in files or ledger.get('formal_sandbox_component_sha256')!=component(old) or component(H/'execution.py')!=component(old):return False
    program=r.get('probe_program')
    if not program or program not in files or not r.get('container_ids') or r.get('containers_remaining')!=[]:return False
    proofs=r.get('process_receipts',[])
    if not proofs:return False
    for p in proofs:
        if p not in files:return False
        process=json.loads(Path(p).read_text());log=process.get('raw_log')
        if process.get('native_exit')!=0 or log not in files or process.get('log_sha256')!=files[log]:return False
        if process.get('formal_wrapper_sha256')!=r['formal_wrapper_sha256']:return False
    return q.get('formal_boundary')=='PASS'

def full_capsule_reuse_qualified(q):
    """Verify filtered A/B/C/runtime reuse without accepting an old huge closure wholesale."""
    files=q.get('dependencies',{});path=q.get('full_capsule_reuse')
    if not path or path not in files:return False
    ledger=json.loads(Path(path).read_text())
    if ledger.get('result')!='PASS' or ledger.get('historical_45_diagnostics_reused') is not False:return False
    required={'run_isolation','artifact_copy','compile_completeness','vite_closure','packaging','frontend_boundary','formal_boundary','lean_runtime'}
    if set(ledger.get('areas',{}))!=required or any(v!='PASS' for v in ledger['areas'].values()):return False
    for row in ledger.get('exact_components',[]):
        current,prior=row.get('current'),row.get('prior')
        if not current or not prior or current not in files or prior not in files:return False
        if files[current]!=files[prior] or row.get('sha256')!=files[current]:return False
    for row in ledger.get('ast_components',[]):
        current,prior,name=row.get('current'),row.get('prior'),row.get('name')
        if not current or not prior or current not in files or prior not in files:return False
        def component(source):
            tree=ast.parse(Path(source).read_text());node=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name),None)
            return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest() if node else None
        if not row.get('sha256') or component(current)!=row['sha256'] or component(prior)!=row['sha256']:return False
    for row in ledger.get('native_receipts',[]):
        process,log=row.get('process'),row.get('log')
        if process not in files or log not in files:return False
        receipt=json.loads(Path(process).read_text())
        if receipt.get('native_exit')!=0 or receipt.get('log_sha256')!=files[log]:return False
        result=row.get('result')
        if result:
            if result not in files:return False
            measured=json.loads(Path(result).read_text())
            if measured.get('result')!='PASS' or measured.get('failures',0)!=0 or measured.get('errors',0)!=0:return False
    for source in ledger.get('programs_and_qualification_receipts',[]):
        if source not in files:return False
    return bool(ledger.get('exact_components') and ledger.get('native_receipts') and ledger.get('programs_and_qualification_receipts'))
