from pathlib import Path
import sys, unittest, json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'executor'))
import bindings, execution, freshness
class Red(unittest.TestCase):
 def test_A_run_owned_checkouts(self):
  run=execution.D/'outputs/continuation-runs/red-fixture'
  m=bindings.build(run)
  self.assertTrue(all(Path(s['repository']).is_relative_to(run) for s in m['gates'].values()))
 def test_A_preserved_artifact_api(self):
  import artifacts
  self.assertTrue(callable(artifacts.seal))
 def test_B_compile_completeness_api(self):
  import compile_inventory
  self.assertTrue(callable(compile_inventory.validate))
 def test_C_acceptance_calls_closure(self):
  import inspect, parsers
  self.assertIn('vite_closure',inspect.getsource(parsers.parse))
if __name__=='__main__': unittest.main(verbosity=2)
