from pathlib import Path
import importlib.util,json,unittest
D=Path(__file__).resolve().parents[1]
class IsolationTests(unittest.TestCase):
 def test_frontend_command_overrides_destructive_output(self):
  p=D/'owned/isolation.py'
  if p.exists():
   s=importlib.util.spec_from_file_location('isolation',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);cmd=m.frontend_command(D/'outputs/frontend')
  else:cmd=json.loads((D/'inputs/CI_EXTRA_INVENTORY.json').read_text())['commands']['FRONTEND_BUILD']
  self.assertIn('--outDir',cmd,'Legacy npm build leaves tracked static output/cleanup authority active')
  self.assertEqual(cmd[cmd.index('--outDir')+1],str(D/'outputs/frontend'))
 def test_protected_output_rejected(self):
  import isolation
  with self.assertRaises(RuntimeError):isolation.frontend_command(D/'sources/backend')
 def test_tracked_mutation_rejected(self):
  import tempfile,subprocess,sys
  with tempfile.TemporaryDirectory(dir=D/'fixtures') as name:
   root=Path(name); (root/'.git/objects/pack').mkdir(parents=True); f=root/'tracked.txt';f.write_text('frozen')
   module=D/'owned/observe.py'
   if module.exists():
    s=importlib.util.spec_from_file_location('observe',module);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    result=m.run([sys.executable,'-B','-c','from pathlib import Path;Path('+repr(str(f))+').write_text("drift")'],root,root/'log.txt',protected=[f],repositories=[],metadata_roots=[],allowed=[])
   else:
    old=D.parent/'EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/owned/pack_monitor.py'
    s=importlib.util.spec_from_file_location('old_monitor',old);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    result=m.run(root/'.git/objects/pack',[sys.executable,'-B','-c','from pathlib import Path;Path('+repr(str(f))+').write_text("drift")'],root,root/'log.txt')
   self.assertNotEqual(result['result'],'PASS_BOUNDED_OBSERVATION','Pack-only coverage misses protected source mutation')
if __name__=='__main__':unittest.main(verbosity=2)
