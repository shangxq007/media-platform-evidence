"""Fresh fixture-only qualification for the external29 integration closure."""
from pathlib import Path
import argparse,hashlib,io,json,os,sys,time,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'executor'))
import durability,qualification_contract
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source_binding():
    return {str(p):digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'outputs' not in p.relative_to(ROOT).parts}
def exclusive(path,value,binary=False):
    raw=value if binary else (json.dumps(value,indent=2,sort_keys=True)+'\n').encode();durability.exclusive_bytes(path,raw,0o400)
class Result(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[];self.started={};self.outcomes={}
    def startTest(self,test):self.started[test.id()]=time.time_ns();super().startTest(test)
    def addSuccess(self,test):self.outcomes[test.id()]='PASS';super().addSuccess(test)
    def addFailure(self,test,err):self.outcomes[test.id()]='FAIL';super().addFailure(test,err)
    def addError(self,test,err):self.outcomes[test.id()]='ERROR';super().addError(test,err)
    def addSkip(self,test,reason):self.outcomes[test.id()]='SKIP';super().addSkip(test,reason)
    def stopTest(self,test):
        self.rows.append({'id':test.id(),'started_ns':self.started[test.id()],'finished_ns':time.time_ns(),'expected':'PASS','actual':self.outcomes.get(test.id(),'ERROR')});super().stopTest(test)
def identities(suite):
    result=[]
    for item in suite:
        if isinstance(item,unittest.TestSuite):result.extend(identities(item))
        else:result.append(item.id())
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture-root',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,mode=0o700);a.fixture_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.environ['EP19_QUALIFICATION_FIXTURE_ROOT']=str(a.fixture_root.absolute());os.environ['PYTHONDONTWRITEBYTECODE']='1'
    os.environ['EP19_TEST_TOOLING_ROOT']=str(ROOT.absolute())
    source_before=source_binding()
    sys.path.insert(0,str(Path(__file__).parent));suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
    expected=sorted(identities(suite))
    if len(expected)!=len(set(expected)) or not qualification_contract.REQUIRED_AFFECTED_CONTROLS<=set(expected):
        raise RuntimeError('EXPECTED_CONTROL_IDENTITY_SET_REJECT')
    stream=io.StringIO();started=time.time_ns();started_mono=time.monotonic_ns();result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite);finished_mono=time.monotonic_ns();finished=time.time_ns()
    log=stream.getvalue().encode();exclusive(a.output/'QUALIFICATION.native.log',log,True)
    source_after=source_binding();source_stable=source_before==source_after
    ids=[row['id'] for row in result.rows];accounting=qualification_contract.identity_accounting(expected,result.rows)
    result_doc={'schema':'ep19-external29-control-results-v2','result':'PASS' if result.wasSuccessful() and accounting['result']=='PASS' else 'FAIL',
        'tests':result.testsRun,'unique':len(set(ids)),'duplicates':len(ids)-len(set(ids)),'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'controls':result.rows,
        'expected_controls':expected,'mandatory_affected_controls':sorted(qualification_contract.REQUIRED_AFFECTED_CONTROLS),'identity_accounting':accounting,
        'fixture_only':True,'formal_attempt':False,'product_gate_execution':False,
        'raw_log':str((a.output/'QUALIFICATION.native.log').absolute()),
        'process_receipt':str((a.output/'PROCESS.json').absolute())}
    exclusive(a.output/'RESULT.json',result_doc)
    process={'schema':'ep19-external29-qualification-process-v2','argv':[sys.executable,'-B',str(Path(__file__).absolute()),'--output',str(a.output.absolute()),'--fixture-root',str(a.fixture_root.absolute())],
             'cwd':str(Path.cwd().absolute()),'pid':os.getpid(),
             'started_ns':started,'finished_ns':finished,'native_exit':0 if result.wasSuccessful() else 1,
             'started_monotonic_ns':started_mono,'finished_monotonic_ns':finished_mono,
             'duration_seconds':(finished_mono-started_mono)/1e9,
             'pid_namespace':os.readlink('/proc/self/ns/pid'),
             'native_status':'PASS' if result.wasSuccessful() else 'FAIL',
             'wrapper_exit':0 if source_stable else 1,
             'wrapper_status':'PASS' if source_stable else 'FAIL',
             'raw_log':str((a.output/'QUALIFICATION.native.log').absolute()),
             'log_sha256':digest(a.output/'QUALIFICATION.native.log'),'formal_attempt':False,'product_tests':False,'shared_preparation':False,'shared_baseline':False,'shared_probes':False}
    process.update(source_binding_before=source_before,source_binding_after=source_after,
                   source_binding_stable=source_stable,
                   result_receipt=str((a.output/'RESULT.json').absolute()),
                   result_sha256=digest(a.output/'RESULT.json'),
                   control_ids=expected,
                   control_statuses={row['id']:row['actual'] for row in result.rows})
    exclusive(a.output/'PROCESS.json',process)
    adapter=ROOT/'adapter71-qualification.reused.json';formal=ROOT/'candidate-qualification-v3.reused.json'
    dependencies={str(p.absolute()):digest(p) for p in (a.output/'QUALIFICATION.native.log',a.output/'PROCESS.json',a.output/'RESULT.json',adapter,formal)}
    qualification={'schema':'ep19-external29-integration-qualified-v2','result':result_doc['result'],'tests':result.testsRun,'fresh_tests':result.testsRun,'reused_tests':0,
        'unique':len(set(ids)),'duplicates':len(ids)-len(set(ids)),'failures':len(result.failures),'errors':len(result.errors),'source_binding':source_after,'dependencies':dependencies,
        'skipped':len(result.skipped),'expected_controls':expected,'mandatory_affected_controls':sorted(qualification_contract.REQUIRED_AFFECTED_CONTROLS),'identity_accounting':accounting,
        'raw_log':str((a.output/'QUALIFICATION.native.log').absolute()),'process_receipt':str((a.output/'PROCESS.json').absolute()),'result_receipt':str((a.output/'RESULT.json').absolute()),
        'fixture_root':str(a.fixture_root.absolute()),
        'adapter71_qualification':str(adapter.absolute()),'formal_qualification':str(formal.absolute()),
        'fresh_affected_closure':'V3 adapter plus actual driver lifecycle, continuous observer/native observer seam, failure ordering, exact29 dispatch/accounting and binding helpers',
        'reused_applicability':{'adapter71':'reference plus freshly rerun affected controls','formal158':'unchanged gate implementations selectively source-compared; not relabeled fresh','capsule13':'contained in formal qualification; not rerun'},
        'formal_attempt':False,'formal_baseline':False,'formal_preparation':False,'product_gate_execution':False,
        'source_binding_before_launch':source_before,'source_binding_after_execution':source_after,
        'source_binding_stable':source_stable,
        'accepted_observational_limit':'ledger overwrite-restore/truncate-regrow between covered captures remains undetectable'}
    exclusive(a.output/'QUALIFICATION.json',qualification);return process['native_exit'] if source_stable else 125
if __name__=='__main__':raise SystemExit(main())
