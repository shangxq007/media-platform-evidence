from pathlib import Path
import collections,ctypes,errno,json,os,subprocess,sys,tempfile,time,unittest
import execution,isolation,observe
D=Path(__file__).resolve().parents[1]
class ContractControls(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=D/'fixtures');self.root=Path(self.temp.name);self.out=self.root/'outputs';self.out.mkdir()
 def tearDown(self):self.temp.cleanup()
 def rejected_output(self,p,**kwargs):
  with self.assertRaises(RuntimeError):isolation.validate_output(p,self.out,**kwargs)
 def test_escape(self):self.rejected_output(self.root/'escape')
 def test_shared_root(self):self.rejected_output(self.out)
 def test_symlink(self):
  (self.out/'link').symlink_to(self.root,target_is_directory=True);self.rejected_output(self.out/'link'/'out')
 def test_reserved_overlap(self):self.rejected_output(self.out/'backend',reserved=[self.out/'backend/sub'])
 def test_protected_overlap(self):self.rejected_output(self.out/'protected',protected=[self.out/'protected'])
 def test_candidate_identity(self):
  with self.assertRaisesRegex(RuntimeError,'IDENTITY_MISMATCH'):execution.exact(D/'sources/backend',sha='0'*40)
 def test_missing_evidence(self):
  with self.assertRaises(RuntimeError):execution.require_evidence({'candidate':execution.SHA,'tree':execution.TREE,'native_exit':0,'wrapper_exit':0,'result':'PASS'},[self.root/'missing'])
 def test_missing_gate(self):
  with self.assertRaises(RuntimeError):execution.required_complete(['required'],{})
 def test_failed_gate(self):
  p=self.root/'evidence';p.write_text('evidence')
  with self.assertRaises(RuntimeError):execution.require_evidence({'candidate':execution.SHA,'tree':execution.TREE,'native_exit':7,'wrapper_exit':1,'result':'FAIL'},[p])
 def test_native_failure(self):
  p=self.root/'tracked';p.write_text('fixed')
  r=observe.run([sys.executable,'-B','-c','raise SystemExit(7)'],self.root,self.root/'native.log',[p],[],[],[])
  self.assertEqual(r['native_exit'],7);self.assertEqual(r['wrapper_exit'],1)
 def test_transient_restore_at_exit(self):
  p=self.root/'tracked';p.write_text('fixed')
  code='from pathlib import Path; p=Path('+repr(str(p))+');p.write_text("changed");p.write_text("fixed")'
  r=observe.run([sys.executable,'-B','-c',code],self.root,self.root/'native.log',[p],[],[],[])
  self.assertEqual(r['wrapper_exit'],1);self.assertTrue(r['events']);self.assertTrue(r['final_queue_drained'])
 def test_permission_denied_syscall(self):
  p=self.root/'unreadable';p.mkdir();p.chmod(0)
  try:
   with self.assertRaises(OSError) as caught:observe.Watch([],[],[p],[])
   self.assertEqual(caught.exception.errno,errno.EACCES)
   (D/'outputs/PERMISSION_DENIED_CONTROL.json').write_text(json.dumps({'syscall':'inotify_add_watch','native_errno':caught.exception.errno,'expected_errno':errno.EACCES,'fixture_only':True,'protected_access_controls_changed':0})+'\n')
  finally:p.chmod(0o700)
 def test_actual_queue_overflow(self):
  p=self.root/'metadata';p.mkdir();w=observe.Watch([],[],[p],[])
  try:
   count=int(Path('/proc/sys/fs/inotify/max_queued_events').read_text())//3+100
   for i in range(count):(p/str(i)).write_bytes(b'x')
   w.drain();self.assertIn('QUEUE_OVERFLOW',w.errors);self.assertTrue(w.rejected())
  finally:w.close()
 def test_new_subtree_gap_rejected(self):
  p=self.root/'metadata';p.mkdir();w=observe.Watch([],[],[p],[])
  try:
   q=p/'new';q.mkdir();(q/'x').write_text('changed');w.drain();self.assertTrue(w.rejected());self.assertTrue(w.gaps)
  finally:w.close()
 def test_frontend_cannot_write_backend(self):
  backend=self.root/'synthetic-backend';backend.mkdir();p=backend/'isolation-negative-untracked'
  self.assertFalse(p.exists())
  code='from pathlib import Path;import errno;p=Path('+repr(str(p))+');\ntry:p.write_text("forbidden");raise SystemExit(9)\nexcept OSError as e:assert e.errno==errno.EROFS;print("READ_ONLY_BACKEND")'
  front=self.root/'synthetic-frontend';front.mkdir()
  command=execution.frontend_sandbox([sys.executable,'-B','-c',code],front,[front])
  r=subprocess.run(command,capture_output=True);self.assertEqual(r.returncode,0,r.stderr);self.assertIn(b'READ_ONLY_BACKEND',r.stdout);self.assertFalse(p.exists())
 def test_background_descendant_cannot_survive_frontend(self):
  p=self.root/'escaped';child='import time;from pathlib import Path;time.sleep(.3);Path('+repr(str(p))+').write_text("escaped")'
  code='import subprocess,sys;subprocess.Popen([sys.executable,"-B","-c",'+repr(child)+'])'
  r=subprocess.run(execution.frontend_sandbox([sys.executable,'-B','-c',code],self.root,[self.root]),capture_output=True)
  self.assertEqual(r.returncode,0,r.stderr);time.sleep(.6);self.assertFalse(p.exists())
 def test_cross_lane_frontend_metadata_not_frozen(self):
  p=self.root/'git';p.mkdir();ref=p/'frontend';ref.write_text('old');w=observe.Watch([],[],[p],[],cross_lane=[ref])
  try:ref.write_text('new');w.drain();self.assertFalse(w.rejected());self.assertTrue(w.events);self.assertEqual(w.events[0]['category'],'AUTHORIZED_CONCURRENT_FRONTEND_METADATA')
  finally:w.close()
 def test_primary_index_mutation_rejected(self):
  p=self.root/'git';p.mkdir();f=p/'index';f.write_text('before');w=observe.Watch([],[],[p],[])
  try:f.write_text('after');w.drain();self.assertTrue(w.rejected())
  finally:w.close()
 def test_late_host_descendant_write_is_observed(self):
  p=self.root/'tracked';p.write_text('fixed')
  child='import time;from pathlib import Path;time.sleep(.2);Path('+repr(str(p))+').write_text("late")'
  code='import subprocess,sys;subprocess.Popen([sys.executable,"-B","-c",'+repr(child)+'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)'
  r=observe.run([sys.executable,'-B','-c',code],self.root,self.root/'late.log',[p],[],[],[])
  self.assertEqual(r['native_exit'],0);self.assertEqual(r['wrapper_exit'],1);self.assertTrue(r['events'])
 def test_backend_cache_namespace_rejected(self):
  with self.assertRaises(RuntimeError):execution.frontend_sandbox(['true'],self.root,[D/'cache/backend'])
 def test_frontend_source_writable_mount_rejected(self):
  with self.assertRaises(RuntimeError):execution.frontend_sandbox(['true'],self.root,[D/'sources/frontend'])
 def test_ancestor_swap_and_restore_rejected(self):
  import shutil
  a=self.root/'ancestor';inside=a/'nested';inside.mkdir(parents=True);p=inside/'tracked';p.write_text('original');moved=self.root/'moved'
  script="from pathlib import Path;import os,shutil;a=Path(%r);m=Path(%r);os.rename(a,m);(a/'nested').mkdir(parents=True);(a/'nested/tracked').write_text('substitute');assert (a/'nested/tracked').read_text()=='substitute';shutil.rmtree(a);os.rename(m,a)"%(str(a),str(moved))
  r=observe.run([sys.executable,'-c',script],self.root,os.environ,protected=[p],repositories=[inside]);self.assertEqual(p.read_text(),'original');self.assertNotEqual(r['wrapper_exit'],0)
 def test_untagged_session_descendant_late_write_rejected(self):
  import time
  p=self.root/'tracked';p.write_text('original')
  late="import os,time;from pathlib import Path;os.environ.pop('EP19_GATE_SCOPE',None);os.setsid();os.chdir('/');time.sleep(2);Path(%r).write_text('late')"%str(p)
  parent="import subprocess,sys;subprocess.Popen([sys.executable,'-c',%r])"%late
  r=observe.run([sys.executable,'-c',parent],self.root,os.environ,protected=[p],repositories=[self.root],timeout=5)
  time.sleep(2.5)
  self.assertNotEqual(r['wrapper_exit'],0)
if __name__=='__main__':unittest.main(verbosity=2)
