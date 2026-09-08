"""The existing 29 matrix keys are authoritative. No historical module is imported."""
from pathlib import Path
import json, re
from execution import D,O,H,SHA,TREE
from coverage import digest

XML={'AFFECTED_INTEGRATION','RUNTIME_PREFLIGHT','FULL_BACKEND'}
NATIVE={'ARCHITECTURE_SYNTAX','FRONTEND_LINT','FRONTEND_INSTALL','SEMGREP'}
PARSERS={
 'CHANGE_IMPACT':'exact_change_impact_json','H7_FOCUSED':'exact_unittest_identities',
 'H7_ENTRY':'h7_receipt_and_native_marker','H7_MUTATIONS':'exact_mutation_identities',
 'ARCHITECTURE_SYNTAX':'native_exit_contract','ARCHITECTURE':'architecture_summary',
 'GRADLE_PREFLIGHT':'gradle_success','COMPILE':'gradle_success',
 'AFFECTED_INTEGRATION':'exact_junit_identities','RUNTIME_PREFLIGHT':'exact_junit_identities',
 'SHADOW':'bound_shadow_semantics_final_content_and_three_controls',
 'CLASSIFIER_TEST':'classifier_assertion','GITOPS_STAGING':'gitops_summary',
 'GITOPS_STAGING_EGRESS':'gitops_summary','GITOPS_PRODUCTION':'gitops_summary',
 'GITOPS_PRODUCTION_EGRESS':'gitops_summary','FRONTEND_INSTALL':'native_exit_contract',
 'FRONTEND_LINT':'native_exit_contract','FRONTEND_IDENTITIES':'vitest_list_json',
 'FRONTEND_COLLECTION':'exact_structured_collection','FRONTEND_TEST':'exact_vitest_identities',
 'FRONTEND_BUILD':'external_vite_manifest','FORMAL':'formal_versions_and_summary',
 'SEMGREP':'native_exit_contract','FULL_BACKEND':'exact_junit_identities',
 'APPLICATION_CLASSPATH':'nonempty_bound_classpath','APPLICATION_PROBE':'compiled_application_modules_probe',
 'FOUNDATION':'foundation_native_assertions','BOOTJAR':'git_resource_zip_provenance'}
HISTORICAL_IDS={'COMPILE':['S10'],'ARCHITECTURE_SYNTAX':['S20'],'ARCHITECTURE':['S20'],
 'AFFECTED_INTEGRATION':['S30','S50'],'APPLICATION_CLASSPATH':['S40'],'APPLICATION_PROBE':['S41'],
 'FOUNDATION':['S60'],'BOOTJAR':['S70']}

def build(run):
    run=Path(run);m=json.loads((O/'GATE_EXECUTION_MATRIX.json').read_text())
    if len(m['order'])!=29 or len(set(m['order']))!=29 or set(m['order'])!=set(m['gates']) or set(PARSERS)!=set(m['gates']):raise RuntimeError('MATRIX_NOT_EXACT_29')
    if m['candidate']!=SHA or m['tree']!=TREE:raise RuntimeError('MATRIX_IDENTITY')
    for filename,h in m['inventories'].items():
        if digest(O/'inputs'/filename)!=h:raise RuntimeError('AUTHORITATIVE_INVENTORY_CHANGED')
    substitutions={str(O/'sources'):str(run/'sources'),str(O/'owned'):str(H),str(O/'outputs'):str(run/'runtime/outputs'),str(O/'cache'):str(run/'runtime/cache'),str(O/'tmp'):str(run/'runtime/tmp')}
    for name,s in m['gates'].items():
        s['authoritative_command']=s['command'][:];s['matrix_key']=name;s['historical_command_ids']=HISTORICAL_IDS.get(name,[])
        for field in ('command','outputs','cleanup'):
            s[field]=[rewrite(x,substitutions) for x in s[field]]
        for field in ('cache','tmp','cwd','repository'):s[field]=rewrite(s[field],substitutions)
        if name=='SHADOW':s['cache']=str(run/'runtime/cache/shadow');s['tmp']=str(run/'runtime/tmp/shadow')
        s['environment_namespaces']={'GRADLE_USER_HOME':str(Path(s['cache'])/'gradle'),'HOME':str(Path(s['cache'])/'home'),'TMPDIR':s['tmp'],'JAVA_TOOL_OPTIONS':'-Djava.io.tmpdir='+s['tmp'],'EP19_RUN_ROOT':str(run),'EP19_GATE_ID':name}
        roles=['gate']
        if name in ('CHANGE_IMPACT','GRADLE_PREFLIGHT','RUNTIME_PREFLIGHT','FRONTEND_INSTALL'):roles+=['prerequisite']
        if name in XML|{'H7_ENTRY','COMPILE','FRONTEND_COLLECTION','FRONTEND_TEST','FRONTEND_BUILD','APPLICATION_CLASSPATH','BOOTJAR'}:roles+=['producer']
        roles+=['verification'];s['roles']=roles;s['required']=True
        s['condition_source']={'inventory':s['original_inventory'],'policy':'inputs/CHANGE_IMPACT.json: policy full_ci/backend_ci/frontend_ci/architecture_drift/gitops_validation/formal_verification/semgrep_validation all true; original matrix serialized dependencies retained'}
        s['parser']=PARSERS[name];s['parser_source']='executor/parsers.py::parse; '+s['original_inventory']
        s['run_id']=run.name;s['timeout_seconds']=3600;s['freshness']='New exclusive gate log and receipt, output absence after preserved cleanup, actual producer success, digest-bound output and parser; no mtime-only acceptance'
        s['completeness']='Required output and all expected structured identities; missing/parser failure rejects';s['not_run']='Any prior required failure stops and records all remaining matrix keys NOT_RUN; no retry'
        if name=='FRONTEND_BUILD':s['command']+=['--manifest']
        if name=='COMPILE':s['command']+=['-I',str(H/'compile.init.gradle')]
        s['output_bindings']=output_bindings(name,run,s)
        if not name.startswith('FRONTEND_'):
            scope=json.loads((O/'PROTECTION_SCOPE.json').read_text())
            s['outputs']=sorted({rewrite(p,substitutions) for p in scope['allowed'] if Path(rewrite(p,substitutions)).is_relative_to(Path(s['repository']))}|{str(run/'runtime/outputs/backend')})
        s['source_binding']='Exact Git tracked bytes/modes/index/HEAD/tree in independent candidate clone, helpers and controls detached seal'
        s['process_outcomes']='native_exit and wrapper_exit independent; negative synthetic rejection is not product failure'
        s['packaging_schedule']='External Gradle init checks processResources/bootJar immediately after each actual producer; executor verifies receipts before acceptance'
        s['cleanup_binding']='Save exact existing generated output bytes and digest in gate cleanup-preimages before deletion; tracked/symlink/escape refuses'
        s['dependency_binding']='Prior receipt PASS with exact run/candidate/tree, all output digests checked before consumer'
    m.update(run_id=run.name,run_root=str(run),authoritative_matrix_sha256=digest(O/'GATE_EXECUTION_MATRIX.json'),status='ENGINEERING_BINDINGS_NOT_POLICY_ACCEPTANCE')
    return m

def rewrite(value,mapping):
    for before,after in mapping.items():value=value.replace(before,after)
    return value

def output_bindings(name,run,spec):
    o=run/'runtime/outputs';b=Path(spec['repository'])
    fixed={'H7_ENTRY':[o/'backend/H7_PRODUCTION_INPUT_RECEIPT.json'],
           'FULL_BACKEND':[o/'backend/FULL_EXECUTION_MANIFEST.tsv'],
           'FRONTEND_COLLECTION':[o/'frontend-evidence/COLLECTED.jsonl'],
           'FRONTEND_TEST':[o/'frontend-evidence/FRONTEND_TEST_RESULTS.json'],
           'FRONTEND_BUILD':[o/'frontend/index.html'],
           'APPLICATION_CLASSPATH':[o/'backend/classpath.txt'],
           'APPLICATION_PROBE':[o/'backend/probe.args',o/'backend/probe-classes/ExposureProbe.class']}
    return {'required_files':list(map(str,fixed.get(name,[]))),
            'junit_glob':'**/build/test-results/test/TEST-*.xml' if name in XML else None,
            'junit_capture_before_next_gate':name in XML,
            'native_log_required':True,'native_silent_output_allowed':name in NATIVE,
            'resource_checks':name in ('COMPILE','AFFECTED_INTEGRATION','FULL_BACKEND','BOOTJAR'),
            'jar_path':'Actual bootJar.archiveFile from bound Gradle producer rule' if name=='BOOTJAR' else None}
