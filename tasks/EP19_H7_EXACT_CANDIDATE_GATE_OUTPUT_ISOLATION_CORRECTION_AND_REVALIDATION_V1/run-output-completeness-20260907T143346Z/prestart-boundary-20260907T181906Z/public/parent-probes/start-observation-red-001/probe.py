import sys,os,json,importlib.util
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch
src=Path(sys.argv[1]);out=Path(sys.argv[2]);os.environ['EP19_DIAGNOSTIC_TEST_OUTPUT']=str(out)
spec=importlib.util.spec_from_file_location('fixture_controls',src/'qualification/test_decisions.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=m.DecisionControls('test_real_run_all_positive_prestart_and_final');c.setUp();orig=m.de.parent_fd
@contextmanager
def fault(path):
 if Path(path).name=='START.json':raise PermissionError(13,'injected lifecycle observation unavailable')
 with orig(path) as fd:yield fd
rejected=False
try:
 with patch.object(m.de,'parent_fd',fault):c.compare()
except RuntimeError:rejected=True
print(json.dumps({'actual_rejected':rejected,'expected_rejected':True,'rows':[{'decision':r['decision'],'START':r['START']} for _,r in c.receipts()],'scope':'Disposable injection; no product gate'}))
assert rejected,'START_OBSERVATION_ERROR_ACCEPTED'
