"""Build the exact immutable candidate/runtime binding used by external29."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess

CANDIDATE='a29864343ed4f630b052c20d86c23b240f13cfd0'
TREE='fd37409d0274662abbe86f69e3d963c05b379696'
PARENT='689ab9456461a8d19a72d059f5157092efc43aff'
BASE='86d6aef94fd5e58da552e97c11473cff6eca734e'
PATCH='bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690'
OWNER='4f431b08fda1066719b63d9753f5db202f5c1191371c33d9d99fed66dd5b01ff'
MATRIX='57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e'

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
    if q.get('schema')!='ep19-external29-integration-qualified-v1' or q.get('result')!='PASS':raise RuntimeError('INTEGRATION_QUALIFICATION_NOT_PASS')
    if adapter.get('schema')!='ep19-approved-bookkeeping-qualification-v3' or adapter.get('fresh_tests')!=71 or adapter.get('result')!='PASS':raise RuntimeError('ADAPTER71_NOT_APPLICABLE')
    if dep.get('result')!='PASS' or dep.get('ledger_role')!='OBSERVATION_INTEGRITY_ONLY' or dep.get('unbound_dynamic_readers'):raise RuntimeError('DEPENDENCY_BINDING_REJECT')
    source=sources(tooling)
    if q.get('source_binding')!=source:raise RuntimeError('QUALIFICATION_SOURCE_BINDING_STALE')
    inventories={p.name:digest(p) for p in sorted((control/'inputs').iterdir()) if p.is_file()}
    if not re.fullmatch(r'candidate-formal-002-[a-z0-9][a-z0-9_-]{1,48}',a.run_id):raise RuntimeError('NEW_002_NAMESPACE_REQUIRED')
    return {'schema':'ep19-external29-runtime-binding-v1','root':str(tooling),'clone_source':str(checkout),
            'candidate':CANDIDATE,'tree':TREE,'immediate_parent':PARENT,'canonical_comparison_base':BASE,
            'product_patch_sha256':PATCH,'control_root':str(control),'matrix_sha256':MATRIX,'inventories':inventories,
            'run_id':a.run_id,'owner':str(a.owner.resolve()),'owner_sha256':digest(a.owner),
            'dependency':str(a.dependency.resolve()),'dependency_sha256':digest(a.dependency),
            'qualification':str(a.qualification.resolve()),'qualification_sha256':digest(a.qualification),
            'adapter_qualification':str(a.adapter_qualification.resolve()),'adapter_qualification_sha256':digest(a.adapter_qualification),
            'reviewed_delta':{'path':str(a.reviewed_delta.resolve()),'sha256':digest(a.reviewed_delta)},'source_binding':source}
def write(path,value):
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try:os.write(fd,raw);os.fsync(fd)
    finally:os.close(fd)
def main():
    p=argparse.ArgumentParser();
    for name in ('checkout','owner','dependency','qualification','adapter-qualification','matrix','tooling-root','reviewed-delta','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--run-id',required=True);a=p.parse_args();write(a.output,build(a));print(digest(a.output))
if __name__=='__main__':main()
