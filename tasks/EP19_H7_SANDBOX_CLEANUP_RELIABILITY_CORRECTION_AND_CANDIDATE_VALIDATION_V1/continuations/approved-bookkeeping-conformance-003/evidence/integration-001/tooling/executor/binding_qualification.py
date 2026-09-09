"""Bound evidence for the explicitly approved external binding delta only."""
from pathlib import Path
import ast, os
import binding_contract as bc

CHANGED = {
 'executor/execution.py','executor/namespaces.py','executor/bindings.py',
 'executor/parsers.py','executor/runner.py','executor/coverage.py',
 'executor/lean_preparation.py','qualification/build_qualification.py',
 'qualification/test_baseline_sequence.py','tools/hermes_execute_once.py','tools/revalidate_preparation.py',
}
ADDED = {'executor/identity_delta.py','tests/test_identity_delta.py','executor/binding_contract.py','executor/binding_qualification.py',
         'qualification/candidate_binding.py','qualification/qualify_synthetic.py',
         'tests/test_binding.py','tests/fixture_support.py','tests/verify_capsule.py'}

def source_files():
    paths=[]
    for folder in ('executor','qualification','tools','tests'):
        paths += [p for p in (bc.ROOT/folder).iterdir() if p.is_file() and (folder=='executor' or p.suffix=='.py')]
    paths += [bc.ROOT/'HISTORICAL_SOURCE_MANIFEST.json',bc.ROOT/'tests/CONTROL_IDENTITIES.json']
    return sorted(paths)

def source_scope():
    old=bc.read(bc.ROOT/'HISTORICAL_SOURCE_MANIFEST.json');rows=[]
    for p in source_files():
        name=str(p.relative_to(bc.ROOT));h=bc.digest(p)
        if name in old:
            prior=old[name];bc.require(bc.digest(prior['historical_path'])==prior['sha256'],'HISTORICAL_SOURCE_CHANGED '+name)
            changed=h!=prior['sha256']
            bc.require(not changed or name in CHANGED,'UNAPPROVED_CHANGED_COMPONENT '+name)
            rows.append({'current':str(p),'prior':prior['historical_path'],'sha256':h,
                         'prior_sha256':prior['sha256'],'mode':'fresh' if changed else 'reused'})
        else:
            bc.require(name in ADDED or name in ('HISTORICAL_SOURCE_MANIFEST.json','tests/CONTROL_IDENTITIES.json'),'UNAPPROVED_ADDED_COMPONENT '+name)
            rows.append({'current':str(p),'sha256':h,'mode':'fresh'})
    bc.require({str(p.relative_to(bc.ROOT)) for p in source_files()} >= set(old),'MISSING_HISTORICAL_COMPONENT')
    return rows

def check_files(files):
    bc.require(bool(files),'EMPTY_EVIDENCE_CLOSURE')
    for p,h in files.items():bc.require(bc.digest(bc.path(p))==h,'EVIDENCE_SEAL_MISMATCH '+p)

def fresh(path):
    """A label is insufficient: measured identities, sources, log and process agree."""
    path=bc.path(str(path));r=bc.read(path);files=r['sources'];check_files(files)
    bc.require(set(files)==set(map(str,source_files())),'FRESH_SOURCE_UNIVERSE')
    bc.require(r['binding_sha256']==os.environ.get('H7_BINDING_SHA256'),'FRESH_BINDING_STALE')
    bc.require(r['binding_config']==os.environ.get('H7_BINDING_CONFIG'),'FRESH_BINDING_PATH')
    config=bc.from_environment()
    import execution
    bc.require(execution.CONFIG==config,'RUNTIME_BINDING_CHANGED')
    bc.require(r['authority']==bc.authority(),'FRESH_AUTHORITY')
    result=bc.read(r['result_receipt']);process=bc.read(r['process_receipt'])
    for k in ('result_receipt','process_receipt','raw_log'):
        bc.require(bc.digest(r[k])==r['evidence'][r[k]],'FRESH_OUTPUT_SEAL '+k)
    wanted=bc.read(bc.ROOT/'tests/CONTROL_IDENTITIES.json')
    bc.require(result['identities']==wanted and result['executed_identities']==wanted,'FRESH_TEST_IDENTITIES')
    bc.require(result['result']=='PASS' and result['tests']==len(wanted)>0 and result['unique']==len(wanted)
               and result['duplicates']==0 and result['failures']==0 and result['errors']==0 and result['skipped']==0,'FRESH_RESULT_REJECT')
    bc.require(result['sources']==files and process['sources']==files,'FRESH_PROCESS_SOURCE_BINDING')
    bc.require(process['native_exit']==0 and process['raw_log']==r['raw_log'] and process['log_sha256']==bc.digest(r['raw_log'])
               and process['result_sha256']==bc.digest(r['result_receipt']),'FRESH_PROCESS_OR_LOG_REJECT')
    bc.require(process['argv']==[process['python'],'-B',str(bc.ROOT/'qualification/qualify_synthetic.py'),'_worker',process['run_root']], 'FRESH_PROGRAM_BINDING')
    bc.require(process['binding_sha256']==r['binding_sha256'] and result['binding_sha256']==r['binding_sha256'],'FRESH_CONFIG_BINDING')
    bc.require(0<process['started_ns']<=result['started_ns']<=result['finished_ns']<=process['finished_ns'],'FRESH_TIME_ORDER')
    bc.require(result['product_gate_execution'] is False and process['product_gate_execution'] is False,'SYNTHETIC_ONLY')
    bc.require(r['scope']==source_scope(),'FRESH_SCOPE_CHANGED')
    return r

def component(q,current,prior):
    files=q['dependencies'];current=str(current);prior=str(prior)
    if not files.get(current) or not files.get(prior):return False
    if files[current]==files[prior]:return True
    try:
        path=q['binding_extension'];bc.require(path in files,'MISSING_FRESH_QUALIFICATION')
        r=fresh(path)
        return any(row['current']==current and row.get('prior')==prior and row['mode']=='fresh'
                   and row['sha256']==files[current] and row['prior_sha256']==files[prior] for row in r['scope'])
    except (KeyError,ValueError,OSError,RuntimeError):return False

def function_text(path,name):
    text=Path(path).read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(text,node)

def extension(q):
    bc.require(q.get('schema')=='ep19-baseline-sequence-qualified-v1','NO_QUALIFICATION_SCHEMA_FALLBACK')
    path=q.get('binding_extension');bc.require(path and path in q['dependencies'],'MISSING_FRESH_QUALIFICATION')
    r=fresh(path)
    check_files(q['dependencies'])
    required={**r['sources'],**r['evidence'],str(path):bc.digest(path),**{str(p):bc.digest(p) for p in bc.closure()}}
    bc.require(all(q['dependencies'].get(p)==h for p,h in required.items()),'FRESH_CLOSURE_INCOMPLETE')
    for row in r['scope']:
        if 'prior' in row:bc.require(component(q,row['current'],row['prior']),'COMPONENT_NOT_QUALIFIED')
    # Native wrappers remain exactly the historical function text. No fresh Python
    # test is substituted for a native container/Gradle/Lean qualification.
    for name in ('formal_sandbox','frontend_sandbox'):
        bc.require(function_text(bc.ROOT/'executor/execution.py',name)==function_text(bc.HISTORICAL_D/'executor/execution.py',name),'NATIVE_WRAPPER_CHANGED')
    return r
