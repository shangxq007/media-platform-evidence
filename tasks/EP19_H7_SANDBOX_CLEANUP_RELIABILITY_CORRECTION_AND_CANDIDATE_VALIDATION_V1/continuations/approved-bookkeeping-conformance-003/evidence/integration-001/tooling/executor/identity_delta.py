"""Narrow, source-backed cleanup-test delta. Reads evidence; never runs producers."""
from pathlib import Path, PurePosixPath
import ast, csv, hashlib, io, json, re, xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from typing import Iterable
import binding_contract as bc
import account

SCHEMA = 'ep19-cleanup-identity-delta-v1'
MODULE = 'sandbox-isolation-module'
PACKAGE = 'com.example.platform.sandbox'
CLASSES = ('CleanupReliabilityTest', 'CleanupFailurePropagationTest')
TEST_PATHS = {f'{MODULE}/src/test/java/com/example/platform/sandbox/{c}.java': PACKAGE+'.'+c for c in CLASSES}
PRODUCT_PATHS = {f'{MODULE}/src/main/java/com/example/platform/sandbox/{c}.java' for c in
                 ('LocalBoundedProcessLauncher', 'BubblewrapSandboxProcessLauncher', 'ContainerSandboxProcessLauncher')}
TOOL = 'scripts/ci/change_impact_classifier.py'
# Reviewed immutable parent/candidate bytes (see CLASSIFIER_SOURCE_PROOF.json).
CLASSIFIER_SHA256 = 'd426f7748ef265fd9457ddd7f7cb3e0565d420ac9bb57bec7f8be3cf75cc106f'

def classified_impact(source, paths):
    """Evaluate only the pinned classifier's pure definitions, never its CLI/I/O."""
    bc.require(sha(source)==CLASSIFIER_SHA256, 'CHANGE_IMPACT_CLASSIFIER_SOURCE')
    parsed=ast.parse(source)
    pure_functions={'_under','_normalise_path','classify_path'}
    nodes=[node for node in parsed.body if isinstance(node,ast.Assign)
           or isinstance(node,ast.FunctionDef) and node.name in pure_functions
           or isinstance(node,ast.ClassDef) and node.name=='Classification']
    namespace={'__name__':__name__,'re':re,'PurePosixPath':PurePosixPath,
               'dataclass':dataclass,'Iterable':Iterable}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),TOOL+' [pure classification]','exec'),namespace)
    return namespace['Classification'].from_paths(paths,'git_diff').as_dict()

def check_impact(impact, prior, source, paths):
    expected=classified_impact(source,paths)
    bc.require(set(impact)==set(prior)==set(expected)
               and type(impact['schema_version']) is int
               and impact['schema_version']==prior['schema_version']==expected['schema_version']
               and impact['reason']==expected['reason'], 'CHANGE_IMPACT_POLICY_OR_SCHEMA')
    bc.require(impact['paths']==paths and type(impact['changed_path_count']) is int
               and impact['changed_path_count']==len(paths)
               and set(impact['path_categories'])==set(paths), 'CHANGE_IMPACT_DIFF')
    bc.require(impact['path_categories']==expected['path_categories']
               and impact['categories']==expected['categories'], 'CHANGE_IMPACT_CATEGORIES')
    policy=impact['policy']
    bc.require(isinstance(policy,dict) and set(policy)==set(prior['policy'])==set(expected['policy'])
               and all(type(value) is bool for value in policy.values())
               and policy==expected['policy'], 'CHANGE_IMPACT_POLICY_OR_SCHEMA')
    # Publishing is classifier metadata only, never an action authorization.
    # Every other historical requirement is still mandatory and unchanged.
    bc.require(all(policy[key] is value for key,value in prior['policy'].items()
                   if key!='runtime_image_publish'), 'CHANGE_IMPACT_REQUIRED_POLICY')

def encoded(value): return (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode()
def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def exact_keys(value, keys, reason): bc.require(isinstance(value,dict) and set(value)==set(keys.split()), reason)

def artifact(row):
    exact_keys(row, 'path sha256', 'ARTIFACT_SCHEMA')
    p=bc.path(row['path']);bc.require(bc.digest(p)==row['sha256'], 'DELTA_ARTIFACT_HASH '+str(p))
    return p

def tree_rows(raw):
    result={}
    for row in raw.split(b'\0'):
        if not row: continue
        meta,p=row.split(b'\t',1);mode,kind,oid=meta.decode().split();p=p.decode()
        bc.require(p not in result and kind in ('blob','commit'), 'TREE_ENTRY')
        result[p]=[mode,oid]
    return result

def changed(before, after):
    return {p: {'before':before.get(p), 'after':after.get(p)} for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)}

def methods(data, classname):
    # Deliberately supports only these ordinary, no-argument JUnit @Test sources.
    # Strip Java comments and literal bodies before recognizing declarations.
    text=re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', ' ', data.decode(), flags=re.S)
    bc.require(re.search(r'\bpackage\s+'+re.escape(PACKAGE)+r'\s*;',text) and
               re.search(r'\bclass\s+'+classname.split('.')[-1]+r'\b',text), 'TEST_SOURCE_CLASS')
    bc.require(not re.search(r'@(Disabled|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate|Nested|DisplayName)\b',text), 'UNSUPPORTED_TEST_SOURCE')
    names=re.findall(r'@Test\s+(?:(?:public|protected|final)\s+)*void\s+(\w+)\s*\(\s*\)\s*(?:throws\s+[\w.,\s]+)?\{',text)
    bc.require(names and len(names)==len(set(names))==len(re.findall(r'@Test\b',text)), 'TEST_SOURCE_METHODS')
    return sorted(name+'()' for name in names)

def native(row, c, argv, sources, outputs):
    p=artifact(row);r=bc.read(p)
    exact_keys(r, 'candidate tree immediate_parent canonical_comparison_base argv cwd native_exit wrapper_exit started_ns finished_ns pid raw_log sources outputs', 'NATIVE_SCHEMA')
    for k in ('candidate','tree','immediate_parent','canonical_comparison_base'):
        bc.require(r[k]==c[k], 'NATIVE_CANDIDATE '+k)
    bc.require(r['argv']==argv and r['cwd']==c['clone_source'], 'NATIVE_COMMAND')
    bc.require(type(r['native_exit']) is int and r['native_exit']==0 and type(r['wrapper_exit']) is int and r['wrapper_exit']==0, 'NATIVE_EXIT')
    bc.require(all(type(r[k]) is int for k in ('pid','started_ns','finished_ns')) and r['pid']>0 and 0<r['started_ns']<r['finished_ns'], 'NATIVE_PROCESS')
    bc.require(r['sources']==sources and r['outputs']==outputs, 'NATIVE_INPUT_OUTPUT_BINDING')
    return artifact(r['raw_log'])

def junit_argv():
    return ['./gradlew', ':'+MODULE+':test', *sum((['--tests', PACKAGE+'.'+c] for c in CLASSES), []),
            '--no-daemon','--rerun-tasks','--no-build-cache','--max-workers=8','--console=plain']

def impact_argv(candidate):
    return ['python3','-B',TOOL,'--base',bc.CANONICAL,'--head',candidate,'--json']

def validate(c, evidence, seal, git=None):
    p=bc.path(str(evidence));bc.require(bc.digest(p)==seal, 'DELTA_MANIFEST_SEAL');e=bc.read(p)
    exact_keys(e, 'schema candidate tree immediate_parent canonical_comparison_base clone_source trees parent_diff canonical_diff sources junit junit_receipt impact_receipt delta_identities delta_count', 'DELTA_SCHEMA')
    bc.require(e['schema']==SCHEMA, 'DELTA_SCHEMA')
    for k in ('candidate','tree','immediate_parent','canonical_comparison_base','clone_source'):
        bc.require(e[k]==c[k], 'DELTA_CANDIDATE '+k)
    bc.require(set(e['trees'])=={bc.PARENT,bc.CANONICAL,c['candidate']}, 'DELTA_TREE_UNIVERSE')
    for tree in e['trees'].values():
        bc.require(isinstance(tree,dict) and bool(tree),'DELTA_TREE')
        for name,row in tree.items():
            bc.require(not Path(name).is_absolute() and '..' not in Path(name).parts and isinstance(row,list) and len(row)==2
                       and row[0] in ('100644','100755','120000','160000') and re.fullmatch('[0-9a-f]{40}',row[1]), 'DELTA_TREE_ENTRY')
    old=e['trees'][bc.PARENT];new=e['trees'][c['candidate']]
    bc.require(old.get(TOOL)==new.get(TOOL) and TOOL in old, 'CHANGE_IMPACT_CLASSIFIER_CHANGED')
    delta=changed(old,new);canonical=changed(e['trees'][bc.CANONICAL],new)
    bc.require(e['parent_diff']==delta and e['canonical_diff']==canonical, 'DELTA_PATH_DIFF')
    bc.require(set(delta)==set(TEST_PATHS)|PRODUCT_PATHS, 'UNREVIEWED_CHANGED_PATHS')
    for name in TEST_PATHS:
        bc.require(name not in old and new[name][0]=='100644', 'TEST_NOT_NEW_REGULAR_SOURCE')
    for name in PRODUCT_PATHS:
        bc.require(name in old and old[name][0]==new[name][0]=='100644', 'PRODUCT_SOURCE_REMOVED_OR_MODE_CHANGED')
    if git is not None:
        bc.require(git(c['clone_source'],'rev-parse',c['candidate']+'^{tree}').decode().strip()==c['tree'], 'DELTA_GIT_TREE')
        bc.require(git(c['clone_source'],'rev-list','--parents','-n','1',c['candidate']).decode().split()==[c['candidate'],bc.PARENT], 'DELTA_GIT_PARENT')
        git(c['clone_source'],'merge-base','--is-ancestor',bc.CANONICAL,c['candidate'])
        for commit,rows in e['trees'].items():
            bc.require(tree_rows(git(c['clone_source'],'ls-tree','-rz',commit))==rows, 'DELTA_GIT_SOURCE')
    bc.require(set(e['sources'])==set(delta)|{TOOL}, 'DELTA_SOURCE_UNIVERSE')
    source_blobs={};wanted=[]
    for name,row in e['sources'].items():
        data=artifact(row).read_bytes();oid=blob(data)
        bc.require(new[name]==['100644',oid] or (name==TOOL and new[name]==['100755',oid]), 'DELTA_SOURCE_BLOB '+name)
        source_blobs[name]=oid
        if name in TEST_PATHS:
            wanted += [account.canonical([':'+MODULE+':test',TEST_PATHS[name],m]) for m in methods(data,TEST_PATHS[name])]
    bc.require(set(e['junit'])==set(TEST_PATHS.values()), 'JUNIT_CLASS_UNIVERSE')
    observed=[];outputs={}
    for classname,row in e['junit'].items():
        xml=artifact(row);bc.require(str(xml) not in outputs, 'DUPLICATE_XML');outputs[str(xml)]=row['sha256']
        suite=ET.parse(xml).getroot();cases=suite.findall('testcase')
        bc.require(suite.tag=='testsuite' and suite.get('name')==classname and int(suite.attrib['tests'])==len(cases), 'JUNIT_XML_COUNT_OR_CLASS')
        bc.require(all(int(suite.attrib[k])==0 for k in ('failures','errors','skipped')), 'JUNIT_XML_STATUS')
        for case in cases:
            bc.require(case.get('classname')==classname and not any(case.findall(k) for k in ('failure','error','skipped')), 'JUNIT_TEST_STATUS_OR_CLASS')
            observed.append(account.canonical([':'+MODULE+':test',classname,case.attrib['name']]))
    bc.require(Counter(observed)==Counter(wanted) and len(observed)==len(set(observed)), 'JUNIT_SOURCE_IDENTITY_SET')
    wanted=sorted(wanted)
    bc.require(e['delta_identities']==wanted and type(e['delta_count']) is int and e['delta_count']==len(wanted), 'MEASURED_DELTA_SET_OR_COUNT')
    native(e['junit_receipt'],c,junit_argv(),source_blobs,outputs)
    raw=native(e['impact_receipt'],c,impact_argv(c['candidate']),source_blobs,{})
    impact=bc.read(raw);prior=bc.read(bc.HISTORICAL_O/'inputs/CHANGE_IMPACT.json')
    paths=sorted(canonical)
    check_impact(impact,prior,artifact(e['sources'][TOOL]).read_bytes(),paths)
    return e, wanted, raw.read_bytes()

def closure(evidence):
    p=Path(evidence);e=bc.read(p);paths=[p]
    for row in [*e['sources'].values(),*e['junit'].values()]: paths.append(artifact(row))
    for key in ('junit_receipt','impact_receipt'):
        r=artifact(e[key]);paths += [r,artifact(bc.read(r)['raw_log'])]
    return paths

def inventories(c, evidence, seal, git=None):
    e,delta,impact=validate(c,evidence,seal,git)
    values={p.name:p.read_bytes().replace(bc.PARENT.encode(),c['candidate'].encode()).replace(bc.OLD_TREE.encode(),c['tree'].encode())
            for p in (bc.HISTORICAL_O/'inputs').iterdir() if p.is_file()}
    expected=json.loads(values['EXPECTED_IDENTITIES.json']);full=expected['FULL_BACKEND']
    old=full['identities'];skips=full['skips']
    bc.require(len(old)==len(set(old)) and len(skips)==len(set(skips)) and set(skips)<=set(old) and not set(old)&set(delta), 'BASE_IDENTITY_OR_DELTA_OVERLAP')
    # Cross-check both historical inventory encodings before appending anything.
    rows=list(csv.DictReader(io.StringIO(values['FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv'].decode()),delimiter='\t'))
    bc.require(Counter(account.canonical([r['TASK'],r['CLASSNAME'],r['TESTNAME']]) for r in rows)==Counter(old), 'HISTORICAL_TSV_SET')
    frozen=list(csv.DictReader(io.StringIO(values['FULL_TEST_EXPECTED_FROZEN.tsv'].decode()),delimiter='\t'))
    frozen_ids=[account.canonical([':'+r['module'].replace('/',':')+':test',r['test_class'],r['test_identity']]) for r in frozen]
    bc.require(Counter(frozen_ids)==Counter(old) and {i for i,r in zip(frozen_ids,frozen) if r['expected_status']=='SKIPPED'}==set(skips), 'HISTORICAL_FROZEN_SET_OR_SKIPS')
    full['identities']=old+delta;values['EXPECTED_IDENTITIES.json']=encoded(expected)
    for key in ('FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv','FULL_TEST_EXPECTED_FROZEN.tsv'):
        bc.require(values[key].endswith(b'\n'), 'TSV_TERMINATOR')
        for identity in delta:
            task,classname,name=json.loads(identity)
            row=[task,classname,name] if key.endswith('REPOSITORY_FORMAT.tsv') else [MODULE,classname,name,'PASSED','SOURCE_BACKED_CANDIDATE_JUNIT_DELTA']
            bc.require(all(not any(ch in v for ch in '\t\r\n') for v in row), 'TSV_IDENTITY_ENCODING')
            values[key]+=('\t'.join(row)+'\n').encode()
    identity=json.loads(values['CANDIDATE_IDENTITY.json'])
    identity['parent']=c['immediate_parent'];identity['paths']=sorted(e['canonical_diff'])
    values['CANDIDATE_IDENTITY.json']=encoded(identity)
    values['CHANGE_IMPACT.json']=impact
    fcv=json.loads(values['FCV_STAGE2_INVENTORY.json'])
    fcv['expected_identities']=len(full['identities']);fcv['expected_skips']=len(skips)
    fcv['derivation']='Historical accepted identity set and skips preserved; source-backed candidate JUnit delta bound by reviewed_delta in BINDING.json. No historical test result is a current PASS.'
    fcv['unchanged_source_proof']=sorted(e['canonical_diff'])
    for key in ('FULL_TEST_EXPECTED_FROZEN.tsv','FULL_TEST_EXPECTED_REPOSITORY_FORMAT.tsv'): fcv['pins'][key]=sha(values[key])
    values['FCV_STAGE2_INVENTORY.json']=encoded(fcv)
    ci=json.loads(values['CI_EXTRA_INVENTORY.json']);ci['pins']['CHANGE_IMPACT.json']=sha(impact);values['CI_EXTRA_INVENTORY.json']=encoded(ci)
    return values
