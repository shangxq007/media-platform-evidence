"""Local offline checks of orchestration rejection and independent cache preparation."""
from pathlib import Path
import json,os,sys,unittest,uuid
from unittest.mock import patch
import parent_orchestration as parent
class Controls(unittest.TestCase):
 def setUp(self):
  self.root=Path(os.environ['EP19_QUALIFICATION_ROOT'])/(self._testMethodName+'-'+uuid.uuid4().hex[:8]);self.root.mkdir()
 def stage(self,**changes):
  log=self.root/'native.log';log.write_text('native fixture\n')
  r={'evidence':{str(log):parent.h(log)},'native_exit':0,'source_drift':False,'helpers':parent.helpers(),'programs':parent.programs(),'raw_log':str(log),'log_sha256':parent.h(log)};r.update(changes)
  parent.put(self.root/'controls-process.json',r)
 def test_current_source_stage_binding(self):
  self.stage();parent.validate_stage(self.root,'controls')
 def test_stage_evidence_change_reject(self):
  self.stage();(self.root/'native.log').write_text('altered')
  with self.assertRaisesRegex(RuntimeError,'STAGE_LOG_CHANGED'):parent.validate_stage(self.root,'controls')
 def test_changed_helper_evidence_reject(self):
  self.stage(helpers={})
  with self.assertRaisesRegex(RuntimeError,'CHANGED_HELPER'):parent.validate_stage(self.root,'controls')
 def test_changed_program_evidence_reject(self):
  self.stage(programs={})
  with self.assertRaisesRegex(RuntimeError,'CHANGED_HELPER_OR_PROGRAM'):parent.validate_stage(self.root,'controls')
 def test_absent_areas_cannot_assemble(self):
  with self.assertRaises(FileNotFoundError):parent.assemble(self.root)
  self.assertFalse((self.root/'QUALIFICATION.json').exists())
 def test_native_failure_cannot_be_stamped(self):
  self.stage(native_exit=7)
  with self.assertRaisesRegex(RuntimeError,'STAGE_NOT_PASS'):parent.validate_stage(self.root,'controls')
 def test_cache_copy_and_no_baseline_overwrite(self):
  source=self.root/'source';source.mkdir();rows=[]
  for i in range(4617):
   p=source/str(i);p.write_text(str(i));rows.append({'path':p.name,'source_sha256':parent.h(p),'destination_sha256':parent.h(p)})
  mat=self.root/'mapping.json';parent.put(mat,{'destination':str(source),'mapping':rows});run=self.root/'run'
  with patch.object(parent,'MATERIALIZATION',mat):
   dest=parent.copy_lean(run);self.assertNotEqual((source/'0').stat().st_ino,(dest/'0').stat().st_ino)
   (source/'0').write_text('changed');self.assertEqual((dest/'0').read_text(),'0')
   with self.assertRaisesRegex(RuntimeError,'LEAN_SOURCE_CHANGED'):parent.copy_lean(self.root/'other')
   parent.put(run/'baseline.json',{'synthetic_only':True})
   with self.assertRaisesRegex(RuntimeError,'CACHE_MUST_PRECEDE_BASELINE'):parent.copy_lean(run)
 def test_historical_parent_focused_receipt_rejected_after_helper_change(self):
  readback=parent.load(parent.D/'parent-verification-001/PARENT_READBACK.json')
  with self.assertRaisesRegex(RuntimeError,'FROZEN_INPUT_CHANGED'):
   parent.coverage.qualification_inputs(Path(readback['qualification_path'])/'QUALIFICATION.json')
 def test_cache_links_reject(self):
  p=self.root/'source';p.mkdir();(p/'file').write_text('x');(p/'link').symlink_to(p/'file')
  with self.assertRaisesRegex(RuntimeError,'CACHE_LINK'):parent.regular_inventory(p)
if __name__=='__main__':unittest.main(verbosity=2)
