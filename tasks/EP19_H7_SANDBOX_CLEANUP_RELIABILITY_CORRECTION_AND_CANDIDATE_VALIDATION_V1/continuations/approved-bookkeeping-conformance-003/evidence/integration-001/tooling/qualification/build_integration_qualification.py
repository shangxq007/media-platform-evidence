"""Fresh fixture-only qualification for the external29 integration closure."""
from pathlib import Path
import argparse,hashlib,io,json,os,sys,time,unittest

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source_binding():
    return {str(p):digest(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'outputs' not in p.relative_to(ROOT).parts}
def exclusive(path,value,binary=False):
    raw=value if binary else (json.dumps(value,indent=2,sort_keys=True)+'\n').encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400)
    try:
        view=memoryview(raw)
        while view:view=view[os.write(fd,view):]
        os.fsync(fd)
    finally:os.close(fd)
class Result(unittest.TextTestResult):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.rows=[];self.started={}
    def startTest(self,test):self.started[test.id()]=time.time_ns();super().startTest(test)
    def stopTest(self,test):
        failed=test in [x[0] for x in self.failures+self.errors]
        self.rows.append({'id':test.id(),'started_ns':self.started[test.id()],'finished_ns':time.time_ns(),'expected':'control assertion passes','actual':'FAIL' if failed else 'PASS'});super().stopTest(test)
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture-root',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,mode=0o700);a.fixture_root.mkdir(parents=True,exist_ok=True,mode=0o700)
    os.environ['EP19_QUALIFICATION_FIXTURE_ROOT']=str(a.fixture_root.absolute());os.environ['PYTHONDONTWRITEBYTECODE']='1'
    sys.path.insert(0,str(Path(__file__).parent));suite=unittest.defaultTestLoader.discover(str(Path(__file__).parent),pattern='test_*.py')
    stream=io.StringIO();started=time.time_ns();result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite);finished=time.time_ns()
    log=stream.getvalue().encode();exclusive(a.output/'QUALIFICATION.native.log',log,True)
    ids=[row['id'] for row in result.rows];result_doc={'schema':'ep19-external29-control-results-v1','result':'PASS' if result.wasSuccessful() else 'FAIL',
        'tests':result.testsRun,'unique':len(set(ids)),'duplicates':len(ids)-len(set(ids)),'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'controls':result.rows,
        'fixture_only':True,'formal_attempt':False,'product_gate_execution':False}
    exclusive(a.output/'RESULT.json',result_doc)
    process={'schema':'ep19-external29-qualification-process-v1','argv':[sys.executable,'-B',str(Path(__file__).absolute()),'--output',str(a.output.absolute()),'--fixture-root',str(a.fixture_root.absolute())],
             'started_ns':started,'finished_ns':finished,'native_exit':0 if result.wasSuccessful() else 1,'raw_log':str((a.output/'QUALIFICATION.native.log').absolute()),
             'log_sha256':digest(a.output/'QUALIFICATION.native.log'),'formal_attempt':False,'product_tests':False,'shared_preparation':False,'shared_baseline':False,'shared_probes':False}
    exclusive(a.output/'PROCESS.json',process)
    adapter=ROOT/'adapter71-qualification.reused.json';formal=ROOT/'candidate-qualification-v3.reused.json'
    dependencies={str(p.absolute()):digest(p) for p in (a.output/'QUALIFICATION.native.log',a.output/'PROCESS.json',a.output/'RESULT.json',adapter,formal)}
    qualification={'schema':'ep19-external29-integration-qualified-v1','result':result_doc['result'],'tests':result.testsRun,'fresh_tests':result.testsRun,'reused_tests':0,
        'unique':len(set(ids)),'duplicates':len(ids)-len(set(ids)),'failures':len(result.failures),'errors':len(result.errors),'source_binding':source_binding(),'dependencies':dependencies,
        'raw_log':str((a.output/'QUALIFICATION.native.log').absolute()),'process_receipt':str((a.output/'PROCESS.json').absolute()),'result_receipt':str((a.output/'RESULT.json').absolute()),
        'adapter71_qualification':str(adapter.absolute()),'formal_qualification':str(formal.absolute()),
        'fresh_affected_closure':'V3 adapter plus actual driver lifecycle, continuous observer/native observer seam, failure ordering, exact29 dispatch/accounting and binding helpers',
        'reused_applicability':{'adapter71':'reference plus freshly rerun affected controls','formal158':'unchanged gate implementations selectively source-compared; not relabeled fresh','capsule13':'contained in formal qualification; not rerun'},
        'formal_attempt':False,'formal_baseline':False,'formal_preparation':False,'product_gate_execution':False,
        'accepted_observational_limit':'ledger overwrite-restore/truncate-regrow between covered captures remains undetectable'}
    exclusive(a.output/'QUALIFICATION.json',qualification);return process['native_exit']
if __name__=='__main__':raise SystemExit(main())
