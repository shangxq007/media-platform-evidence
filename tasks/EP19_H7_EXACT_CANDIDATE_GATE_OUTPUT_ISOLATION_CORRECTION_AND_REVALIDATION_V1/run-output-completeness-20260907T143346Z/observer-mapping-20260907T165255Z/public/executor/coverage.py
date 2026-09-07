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
    controls=[p for p in O.iterdir() if p.is_file()] + [D/'CODEX_BRIEF.md']
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
    controls += [p for p in (D/'tools').rglob('*') if p.is_file()]
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
    if q.get('schema') not in ('ep19-owner-qualified-v1','ep19-output-corrections-v2') or not q.get('dependencies'):
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
    return [path,*map(Path,files)]

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
    if r.get('formal_wrapper_sha256')!=digest(H/'execution.py'):return False
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
