"""Read-only loader validation for the frozen r12 candidate-formal-002 binding."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(root,*args):
    return subprocess.check_output(['git','--no-optional-locks','-C',str(root),*args],
        env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_NO_REPLACE_OBJECTS':'1'},text=True).strip()
def main():
    p=argparse.ArgumentParser();p.add_argument('--binding',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();binding=a.binding.absolute()
    value=json.loads(binding.read_text());root=Path(value['root']);checkout=Path(value['clone_source'])
    sys.path[:0]=[str(root/'executor'),str(root/'qualification')]
    os.environ['H7_BINDING_CONFIG']=str(binding);os.environ['H7_BINDING_SHA256']=sha(binding)
    started_wall=time.time_ns();started_mono=time.monotonic_ns();result='FAIL';detail={}
    try:
        import binding_contract;loaded=binding_contract.from_environment()
        import coverage,dependency_contract,external29_driver
        closure=coverage.qualification_inputs(Path(loaded['qualification']))
        dependency=json.loads(Path(loaded['dependency']).read_text())
        dependency_contract.validate(dependency,matrix_path=root/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json')
        external29_driver.verify_required_runtime_files(root)
        __import__('execution').verify_object_source()
        if loaded['run_id']!='candidate-formal-002':raise RuntimeError('RUN_ID_NOT_EXACT')
        head=git(checkout,'rev-parse','HEAD');tree=git(checkout,'rev-parse','HEAD^{tree}')
        parent=git(checkout,'rev-list','--parents','-n','1','HEAD').split()
        patch=subprocess.check_output(['git','--no-optional-locks','-C',str(checkout),'diff','--binary',
            loaded['immediate_parent'],loaded['candidate']],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
        if head!=loaded['candidate'] or tree!=loaded['tree'] or parent!=[loaded['candidate'],loaded['immediate_parent']]:
            raise RuntimeError('FROZEN_CANDIDATE_IDENTITY_REJECT')
        if hashlib.sha256(patch).hexdigest()!=loaded['product_patch_sha256']:
            raise RuntimeError('FROZEN_CANDIDATE_PATCH_REJECT')
        if git(checkout,'status','--porcelain','--untracked-files=no'):
            raise RuntimeError('FROZEN_CANDIDATE_TRACKED_STATUS_REJECT')
        result='PASS';detail={'run_id':loaded['run_id'],'source_count':len(loaded['source_binding']),
            'qualification_closure_count':len(closure),'dependency_sha256':loaded['dependency_sha256'],
            'qualification_sha256':loaded['qualification_sha256'],'candidate':head,'tree':tree,
            'product_identity_delta':loaded['product_identity_delta'],
            'external_implementation_delta':loaded['external_implementation_delta'],
            'product_identity_consumer_validation':'PASS',
            'product_patch_sha256':hashlib.sha256(patch).hexdigest(),'tracked_status_clean':True}
    except BaseException as error:detail={'error_type':type(error).__name__,'reason':str(error)}
    finished_mono=time.monotonic_ns();finished_wall=time.time_ns()
    doc={'schema':'ep19-r12-runtime-loader-validation-v1','result':result,'binding':str(binding),
        'binding_sha256':sha(binding),'detail':detail,'started_wall_ns':started_wall,
        'finished_wall_ns':finished_wall,'started_monotonic_ns':started_mono,
        'finished_monotonic_ns':finished_mono,'duration_seconds':(finished_mono-started_mono)/1e9,
        'formal_attempt':False,'formal_namespace_created':False,'product_tests':False,
        'shared_preparation':False,'shared_probes':False,'formal_baseline':False,
        'pid':os.getpid(),'pid_namespace':os.readlink('/proc/self/ns/pid')}
    import durability
    durability.exclusive_bytes(a.output,(json.dumps(doc,indent=2,sort_keys=True)+'\n').encode(),0o400)
    print(json.dumps(doc,sort_keys=True));return 0 if result=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
