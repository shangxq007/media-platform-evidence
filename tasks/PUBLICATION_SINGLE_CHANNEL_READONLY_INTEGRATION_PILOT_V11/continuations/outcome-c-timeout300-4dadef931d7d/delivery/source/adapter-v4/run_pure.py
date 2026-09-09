"""Explicit pure-only runner. Never imports or collects transport tests."""
import sys
sys.dont_write_bytecode = True

def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system'):
        raise RuntimeError('PURE_RUNNER_FORBIDDEN_OPERATION')
sys.addaudithook(audit)
import builtins
original_import = builtins.__import__
def pure_import(name,*args,**kwargs):
    if name.split('.')[0] in {'socket','_socket','asyncio','transport','server','client','transport_tests','owner_runner','http','ssl','select','selectors','multiprocessing','concurrent'}:
        raise RuntimeError('PURE_RUNNER_FORBIDDEN_IMPORT')
    return original_import(name,*args,**kwargs)
builtins.__import__ = pure_import
import json
SELECTED_MODULES = ['test_correction_pure']
import unittest
from pathlib import Path

class Result(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.identities=[]
        self.failed_ids=set()
        self.error_ids=set()
        self.skipped_ids=set()
    def addFailure(self,test,err):
        self.failed_ids.add(test.id())
        super().addFailure(test,err)
    def addError(self,test,err):
        self.error_ids.add(test.id())
        super().addError(test,err)
    def addSkip(self,test,reason):
        self.skipped_ids.add(test.id())
        super().addSkip(test,reason)
    def addSubTest(self,test,subtest,err):
        if err is not None:
            (self.failed_ids if issubclass(err[0],test.failureException) else self.error_ids).add(test.id())
        super().addSubTest(test,subtest,err)
    def startTest(self,test):
        self.identities.append(test.id())
        super().startTest(test)

suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in ('test_correction_pure',))
result = unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
error_ids = result.error_ids
failed_ids = result.failed_ids-error_ids
skipped_ids = result.skipped_ids-error_ids-failed_ids
counts = {'total':result.testsRun,'passed':result.testsRun-len(failed_ids|error_ids|skipped_ids),'failures':len(failed_ids),'errors':len(error_ids),'skipped':len(skipped_ids)}
report = {'counts':counts,'identities':result.identities,'socket_audit_hook':True,'forbidden_imports':['socket','_socket','asyncio','transport','server','client','transport_tests','owner_runner','http','ssl','select','selectors','multiprocessing','concurrent'],'selected_modules':SELECTED_MODULES,'transport_collected':False,'forbidden_modules_loaded':sorted(set(sys.modules) & {'socket','_socket','asyncio','transport','server','client','transport_tests','owner_runner','http','ssl','select','selectors','multiprocessing','concurrent'}),'failed_identities':sorted(failed_ids),'error_identities':sorted(error_ids),'native_failure_entries':len(result.failures),'native_error_entries':len(result.errors)}
assert not report['forbidden_modules_loaded']
assert counts['total'] == sum(counts[k] for k in ('passed','failures','errors','skipped'))
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() else 1)
