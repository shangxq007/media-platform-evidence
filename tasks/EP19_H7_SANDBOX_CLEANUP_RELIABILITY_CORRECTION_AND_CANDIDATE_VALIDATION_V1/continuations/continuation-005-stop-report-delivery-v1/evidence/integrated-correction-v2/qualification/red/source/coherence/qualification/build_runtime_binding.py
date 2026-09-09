"""Build the exact immutable candidate/runtime binding used by external29."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess
import sys

CANDIDATE='a29864343ed4f630b052c20d86c23b240f13cfd0'
TREE='fd37409d0274662abbe86f69e3d963c05b379696'
PARENT='689ab9456461a8d19a72d059f5157092efc43aff'
BASE='86d6aef94fd5e58da552e97c11473cff6eca734e'
PATCH='bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690'
OWNER='b4e996d02931d722c959e9a4bbb1d0023ec0cd5e810b5b1a061299452816fd76'
MATRIX='57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e'
PRODUCT_DELTA='4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sources(root):
    root=Path(root)
    return {str(p):digest(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'outputs' not in p.relative_to(root).parts}
def git(root,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'}).decode().strip()
def build(a):
    checkout=a.checkout.resolve();tooling=a.tooling_root.resolve();control=tooling/'candidate-inputs-v3'
    if git(checkout,'rev-parse','HEAD')!=CANDIDATE or git(checkout,'rev-parse','HEAD^{tree}')!=TREE:raise RuntimeError('CANDIDATE_SHA_TREE_MISMATCH')
    if git(checkout,'rev-list','--parents','-n','1','HEAD').split()!=[CANDIDATE,PARENT]:raise RuntimeError('CANDIDATE_PARENT_MISMATCH')
    raw=subprocess.check_output(['git','--no-optional-locks','-C',str(checkout),'diff','--binary',PARENT,CANDIDATE],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
    if hashlib.sha256(raw).hexdigest()!=PATCH:raise RuntimeError('PRODUCT_PATCH_MISMATCH')
    if git(checkout,'status','--porcelain','--untracked-files=no'):raise RuntimeError('PRODUCT_TRACKED_STATUS_NOT_CLEAN')
    if digest(a.owner)!=OWNER or digest(a.matrix)!=MATRIX or a.matrix.absolute()!=control/'GATE_EXECUTION_MATRIX.json':raise RuntimeError('OWNER_OR_MATRIX_MISMATCH')
    q=json.loads(a.qualification.read_text());adapter=json.loads(a.adapter_qualification.read_text());dep=json.loads(a.dependency.read_text())
    if q.get('schema')!='ep19-external29-integration-qualified-v2' or q.get('result')!='PASS':raise RuntimeError('INTEGRATION_QUALIFICATION_NOT_PASS')
    if adapter.get('schema')!='ep19-approved-bookkeeping-qualification-v3' or adapter.get('fresh_tests')!=71 or adapter.get('result')!='PASS':raise RuntimeError('ADAPTER71_NOT_APPLICABLE')
    if dep.get('schema')!='ep19-writer-ledger-dependency-binding-v8' or dep.get('result')!='PASS' or dep.get('ledger_role')!='OBSERVATION_INTEGRITY_ONLY' or dep.get('unbound_dynamic_readers'):raise RuntimeError('DEPENDENCY_BINDING_REJECT')
    import sys
    if str(tooling/'executor') not in sys.path:sys.path.insert(0,str(tooling/'executor'))
    import dependency_contract
    dependency_contract.validate(dep,matrix_path=a.matrix)
    import identity_delta
    identity={"candidate":CANDIDATE,"tree":TREE,"immediate_parent":PARENT,
              "canonical_comparison_base":BASE,"clone_source":str(checkout)}
    def git_bytes(root,*args):
        return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],
            env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1',
                 'GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0'})
    product_identity_delta=a.product_identity_delta.resolve()
    if digest(product_identity_delta)!=PRODUCT_DELTA:
        raise RuntimeError('PRODUCT_IDENTITY_DELTA_NOT_GENUINE_FIXED_EVIDENCE')
    identity_delta.validate(identity,product_identity_delta,PRODUCT_DELTA,git=git_bytes)
    app=json.loads(a.applicability.read_text())
    if app.get('private_manifest_sha256')!=digest(a.private_map) or app.get('private_strict_inventory_sha256')!=digest(a.private_inventory):
        raise RuntimeError('ELIGIBILITY_PRIVATE_PROVENANCE_REJECT')
    source=sources(tooling)
    if q.get('source_binding')!=source:raise RuntimeError('QUALIFICATION_SOURCE_BINDING_STALE')
    inventories={p.name:digest(p) for p in sorted((control/'inputs').iterdir()) if p.is_file()}
    if a.run_id!='candidate-formal-003':raise RuntimeError('EXACT_CANDIDATE_FORMAL_003_REQUIRED')
    import eligibility_coherence as coherence
    contract_path=a.eligibility_contract.resolve()
    contract=coherence.validate_contract(coherence.load(contract_path))
    if contract['attempt_authority']['run_id']!=a.run_id or contract['candidate_identity']!={
            'candidate':CANDIDATE,'tree':TREE,'immediate_parent':PARENT,'product_patch_sha256':PATCH}:
        raise RuntimeError('ELIGIBILITY_CONTRACT_CANDIDATE_OR_ATTEMPT_REJECT')
    result={'schema':'ep19-external29-runtime-binding-v3','root':str(tooling),'clone_source':str(checkout),
            'candidate':CANDIDATE,'tree':TREE,'immediate_parent':PARENT,'canonical_comparison_base':BASE,
            'product_patch_sha256':PATCH,'control_root':str(control),'matrix_sha256':MATRIX,'inventories':inventories,
            'run_id':a.run_id,'owner':str(a.owner.resolve()),'owner_sha256':digest(a.owner),
            'dependency':str(a.dependency.resolve()),'dependency_sha256':digest(a.dependency),
            'qualification':str(a.qualification.resolve()),'qualification_sha256':digest(a.qualification),
            'adapter_qualification':str(a.adapter_qualification.resolve()),'adapter_qualification_sha256':digest(a.adapter_qualification),
            'applicability':str(a.applicability.resolve()),'applicability_sha256':digest(a.applicability),
            'private_map':str(a.private_map.resolve()),'private_map_sha256':digest(a.private_map),
            'private_inventory':str(a.private_inventory.resolve()),'private_inventory_sha256':digest(a.private_inventory),
            'eligibility_contract':str(contract_path),'eligibility_contract_file_sha256':digest(contract_path),
            'eligibility_contract_sha256':coherence.identity(contract),
            'control_plane_implementation':str(a.control_plane_implementation.resolve()),
            'control_plane_implementation_sha256':digest(a.control_plane_implementation),
            'product_identity_delta':{'path':str(a.product_identity_delta.resolve()),'sha256':digest(a.product_identity_delta)},
            'external_implementation_delta':{'path':str(a.external_implementation_delta.resolve()),
                                             'sha256':digest(a.external_implementation_delta)},
            'source_binding':source}
    coherence.validate_review(a.implementation_review)
    coherence.validate_version_chain(contract,result,a.implementation_review)
    return result
def write(path,value):
    executor=Path(__file__).resolve().parents[1]/'executor'
    if str(executor) not in sys.path:sys.path.insert(0,str(executor))
    import durability
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();durability.exclusive_bytes(path,raw,0o400)
def main():
    p=argparse.ArgumentParser();
    for name in ('checkout','owner','dependency','qualification','adapter-qualification','matrix','tooling-root',
                 'product-identity-delta','external-implementation-delta','applicability','private-map',
                 'private-inventory','eligibility-contract','implementation-review',
                 'control-plane-implementation','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--run-id',required=True);a=p.parse_args();write(a.output,build(a));print(digest(a.output))
if __name__=='__main__':main()
