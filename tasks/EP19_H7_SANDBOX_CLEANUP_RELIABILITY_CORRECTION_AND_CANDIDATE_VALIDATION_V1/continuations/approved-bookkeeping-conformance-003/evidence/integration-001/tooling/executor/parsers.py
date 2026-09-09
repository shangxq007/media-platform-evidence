"""Output acceptance tied to the current producer; no historical PASS reuse."""
from pathlib import Path
import csv, json, os, re
import account, packaging
from execution import CONTROL, PARENT, D,O,H,SHA,TREE,git
from coverage import digest
from bindings import XML,NATIVE

def marker(text,pattern):
    if not re.search(pattern,text,re.M):raise RuntimeError('MISSING_NATIVE_ASSERTION '+pattern)

def parse(name,run,gate,repo):
    text=(gate/'native.log').read_text();o=run/'runtime/outputs';e=json.loads((CONTROL/'inputs/EXPECTED_IDENTITIES.json').read_text());result={'result':'PASS','parser_gate':name}
    if name in XML:
        want=e[name];result=account.reconcile(want['identities'],account.xml_rows(gate/'xml'),want['skips'])
        if name=='FULL_BACKEND':
            rows=list(csv.DictReader((o/'backend/FULL_EXECUTION_MANIFEST.tsv').open(),delimiter='\t'))
            if len(rows)!=1 or rows[0]['COMMIT']!=SHA or rows[0]['PROFILE']!='V2_CANDIDATE_FCV' or rows[0]['RESULTS_ROOT']!=str(repo):raise RuntimeError('FULL_MANIFEST_BINDING')
            total=len(want['identities']);skipped=len(want['skips'])
            marker(text,rf'^PASS FULL_DETERMINISTIC_BACKEND_SUITE total={total} passed={total-skipped} skipped={skipped}$')
    elif name=='CHANGE_IMPACT':
        if json.loads(text)!=json.loads((CONTROL/'inputs/CHANGE_IMPACT.json').read_text()):raise RuntimeError('CHANGE_IMPACT_MISMATCH')
    elif name=='H7_FOCUSED':result=account.reconcile(e[name]['identities'],account.unittest_rows(gate/'native.log'))
    elif name=='H7_MUTATIONS':
        result=account.reconcile(e[name]['identities'],re.findall(r'^MUTATION (\S+)=(PASS|FAIL)\b',text,re.M));marker(text,r'^MUTATION_MATRIX_FAILURES=0$')
    elif name=='H7_ENTRY':
        r=json.loads((o/'backend/H7_PRODUCTION_INPUT_RECEIPT.json').read_text())
        if r.get('schema')!='h7-git-tree-input-v1' or r.get('tree')!=TREE or r.get('repository')!=str(repo):raise RuntimeError('H7_RECEIPT_BINDING')
        validate_h7_receipt(r,repo)
        marker(text,r'^H7_ARCHITECTURE_GUARD=PASS$')
    elif name=='FRONTEND_COLLECTION':
        rows=[(account.canonical(json.loads(x)),'PASS') for x in (o/'frontend-evidence/COLLECTED.jsonl').read_text().splitlines()]
        result=account.reconcile(e['FRONTEND_TEST']['identities'],rows)
    elif name=='FRONTEND_TEST':result=account.reconcile(e[name]['identities'],account.frontend_rows(o/'frontend-evidence/FRONTEND_TEST_RESULTS.json',repo),e[name]['skips'])
    elif name=='FRONTEND_IDENTITIES':
        rows=json.loads(text);old=json.loads((CONTROL/'inputs/FRONTEND_IDENTITIES.native.log').read_text())
        oldroot=str(O.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/candidate')
        def normalize(rows,root):
            return sorted((str(Path(r['file']).relative_to(root)),r['name']) for r in rows)
        if normalize(rows,repo)!=normalize(old,oldroot):raise RuntimeError('FRONTEND_LIST_IDENTITY_MISMATCH')
    elif name=='FRONTEND_BUILD':
        resolution=json.loads((gate/'resolution.json').read_text())
        if resolution['outDir']!=str(o/'frontend') or resolution['emptyOutDir'] is not True:raise RuntimeError('VITE_OUTPUT_BOUNDARY')
        import vite_closure
        result['closure']=vite_closure.validate(o/'frontend',resolution['base'],D/'tools',gate/'vite-closure.json')
        result['external_output_consumed_by_bootJar']=False;marker(text,r'built in')
    elif name=='APPLICATION_CLASSPATH':
        cp=(o/'backend/classpath.txt').read_text().strip();paths=[Path(p) for p in cp.split(os.pathsep)]
        if not cp or any(not p.is_absolute() or not p.exists() or p.resolve()!=p or not (p.is_relative_to(repo) or p.is_relative_to(run/'runtime/cache/backend')) for p in paths):raise RuntimeError('CLASSPATH_INPUT_MISSING_OR_ESCAPE')
        result['classpath']=list(map(str,paths))
    elif name=='APPLICATION_PROBE':
        for s in ['IMPLEMENTATION_PUBLIC=false','IMPLEMENTATION_EXPOSED_COUNT=0','QUERY_EXPOSED_COUNT=1','APPLICATION_MODULES_CENSUS=PASS']:marker(text,'^'+s+'$')
    elif name=='SHADOW':
        if len(re.findall(r'^PASS: .* rejects missing authority and does not recreate ',text,re.M))!=3:raise RuntimeError('SHADOW_EXPECTED_CONTROL_COUNT')
        marker(text,r'^OK: PFIRR1-B1 jOOQ authority verification is fail-closed and non-mutating$')
    elif name=='CLASSIFIER_TEST':marker(text,r'^CHANGE_IMPACT_CLASSIFIER_RED_MATRIX=PASS cases=\d+ workflow_mutations=\d+ governance_mutations=\d+ classifier_mutations=\d+')
    elif name=='ARCHITECTURE':marker(text,r'All architecture drift checks passed')
    elif name.startswith('GITOPS_'):marker(text,r'^  FAIL: +0$');marker(text,r'All critical checks passed')
    elif name=='FORMAL':marker(text,r'^FAOF2_FORMAL_VALIDATION=PASS lean=4.19.0 coq=8.20.1$')
    elif name in ('GRADLE_PREFLIGHT','COMPILE','FOUNDATION','BOOTJAR'):
        marker(text,r'^BUILD SUCCESSFUL in ')
        if name=='FOUNDATION':
            for s in ['MISSING_GENERATOR_JAR_NEGATIVE_CONTROL=PASS','NO_OP_GENERATOR_NEGATIVE_CONTROL=PASS','OK PFIRR1-B2:']:marker(text,re.escape(s))
    elif name in NATIVE:result['basis']='Exact sealed command native success; producer defines exit-code contract; raw log digest retained'
    else:raise RuntimeError('UNBOUND_PARSER '+name)
    if result['result']!='PASS':raise RuntimeError('IDENTITY_ACCOUNTING_REJECT '+json.dumps(result))
    return result


def validate_h7_receipt(receipt,repo):
    # Exact membership predicate recovered from candidate h7_input_boundary.py:54-57.
    expected={}
    for raw in git(repo,'ls-tree','-rz',TREE).split(b'\0'):
        if not raw:continue
        meta,name=raw.split(b'\t',1);name=os.fsdecode(name);mode,kind,blob=meta.decode().split()
        if name=='settings.gradle.kts' or (name.endswith('.java') and '/src/main/java/' in '/'+name and '/build/' not in '/'+name and '/generated/' not in '/'+name):expected[name]=blob
    rows=receipt.get('inputs',[])
    if not expected or len(rows)!=len(expected) or {r['path'] for r in rows}!=set(expected):raise RuntimeError('H7_RECEIPT_INCOMPLETE_MEMBERSHIP')
    for row in rows:
        if row['git_blob']!=expected[row['path']] or row['sha256']!=digest(repo/row['path']):raise RuntimeError('H7_RECEIPT_CONTENT_BINDING')
    selected=receipt.get('selected_paths',[])
    if not selected or len(selected)!=len(set(selected)) or not set(selected)<=set(expected) or set(receipt.get('selected_text_sha256',{}))!=set(selected):raise RuntimeError('H7_RECEIPT_INCOMPLETE_SELECTION')
