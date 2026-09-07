"""Synthetic qualification only; never candidate execution evidence."""
from pathlib import Path
import json,tempfile,unittest
import account
class AccountControls(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def check(self,rows,expected=('a','b'),skips=()):return account.reconcile(list(expected),rows,skips)
 def test_exact_multi_method(self):self.assertEqual(self.check([('a','PASS'),('b','PASS')])['result'],'PASS')
 def test_missing(self):self.assertEqual(self.check([('a','PASS')])['missing'],1)
 def test_unexpected(self):self.assertEqual(self.check([('a','PASS'),('b','PASS'),('c','PASS')])['unexpected'],1)
 def test_duplicate(self):self.assertEqual(self.check([('a','PASS'),('a','PASS'),('b','PASS')])['duplicate'],1)
 def test_failure(self):self.assertEqual(self.check([('a','FAIL'),('b','PASS')])['result'],'FAIL')
 def test_error(self):self.assertEqual(self.check([('a','ERROR'),('b','PASS')])['errored'],1)
 def test_unexpected_skip(self):self.assertEqual(self.check([('a','SKIPPED'),('b','PASS')])['result'],'FAIL')
 def test_expected_skip(self):self.assertEqual(self.check([('a','SKIPPED'),('b','PASS')],skips=['a'])['result'],'PASS')
 def test_expected_skip_not_observed(self):self.assertEqual(self.check([('a','PASS'),('b','PASS')],skips=['a'])['result'],'FAIL')
 def test_empty_expectation(self):
  with self.assertRaises(ValueError):self.check([],expected=[])
 def test_duplicate_expectation(self):
  with self.assertRaises(ValueError):self.check([],expected=['a','a'])
 def test_unknown_status(self):
  with self.assertRaises(ValueError):self.check([('a','not-a-status')])
 def test_delimiter_collision(self):
  a=account.fe_identity('f',['a > b'],'c',self.root);b=account.fe_identity('f',['a','b'],'c',self.root);self.assertNotEqual(a,b)
 def test_repeated_spaces(self):self.assertNotEqual(account.fe_identity('f',[],'a  b',self.root),account.fe_identity('f',[],'a b',self.root))
 def test_unicode_preserved(self):self.assertNotEqual(account.fe_identity('f',[],'é',self.root),account.fe_identity('f',[],'e\u0301',self.root))
 def test_empty_hierarchy_and_file(self):self.assertNotEqual(account.fe_identity('f',[],'a',self.root),account.fe_identity('g',[],'a',self.root))
 def test_explicit_root_relocation(self):self.assertEqual(account.fe_identity('/old/frontend/a',[' x '],'t','/old'),account.fe_identity('/new/frontend/a',[' x '],'t','/new'))
 def test_escape(self):
  with self.assertRaises(ValueError):account.fe_identity('../escape',[],'a',self.root)
 def xml(self,text):
  p=self.root/'module/build/test-results/test/TEST-X.xml';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);return account.xml_rows(self.root)
 def test_xml_multi_method(self):self.assertEqual(len(self.xml('<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="C" name="a"/><testcase classname="C" name="b"/></testsuite>')),2)
 def test_xml_empty(self):self.assertEqual(self.check(self.xml('<testsuite tests="0"/>'))['result'],'FAIL')
 def test_xml_malformed(self):
  with self.assertRaises(Exception):self.xml('<testsuite')
 def test_xml_counter_mismatch(self):
  with self.assertRaises(ValueError):self.xml('<testsuite tests="2"><testcase classname="C" name="a"/></testsuite>')
 def test_xml_status_counter_mismatch(self):
  with self.assertRaises(ValueError):self.xml('<testsuite tests="1" failures="0"><testcase classname="C" name="a"><failure/></testcase></testsuite>')
 def test_xml_ambiguous(self):
  with self.assertRaises(ValueError):self.xml('<testsuite tests="1"><testcase classname="C" name="a"><failure/><error/></testcase></testsuite>')
 def test_frontend_reporter_count_mismatch(self):
  p=self.root/'result.json';p.write_text(json.dumps({'success':True,'numRuntimeErrorTestSuites':0,'numTotalTests':1,'testResults':[]}))
  with self.assertRaises(ValueError):account.frontend_rows(p,self.root)
 def test_reporter_runtime_error_not_pass(self):
  p=self.root/'result.json';p.write_text(json.dumps({'success':False,'numRuntimeErrorTestSuites':1,'numTotalTests':1,'testResults':[{'name':str(self.root/'f'),'assertionResults':[{'ancestorTitles':[],'title':'t','status':'passed'}]}]}))
  with self.assertRaises(ValueError):account.frontend_rows(p,self.root)
 def test_frontend_exact_pass(self):
  p=self.root/'result.json';p.write_text(json.dumps({'success':True,'numRuntimeErrorTestSuites':0,'numTotalTests':1,'testResults':[{'name':str(self.root/'f'),'assertionResults':[{'ancestorTitles':['a > b','  中'],'title':'t','status':'passed'}]}]}))
  rows=account.frontend_rows(p,self.root);self.assertEqual(rows,[(account.fe_identity('f',['a > b','  中'],'t',self.root),'PASS')])
if __name__=='__main__':unittest.main(verbosity=2)
