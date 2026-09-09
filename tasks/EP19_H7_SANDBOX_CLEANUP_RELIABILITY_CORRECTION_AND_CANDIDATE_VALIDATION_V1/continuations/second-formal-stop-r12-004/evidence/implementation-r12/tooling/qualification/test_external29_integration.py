"""Fresh controls for the actual external29 driver seam (fixture-only)."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
EXECUTOR=ROOT/'executor';DRIVER=EXECUTOR/'external29_driver.py'
sys.path.insert(0,str(EXECUTOR))
import external29_driver as driver

class External29IntegrationControls(unittest.TestCase):
    def temp(self,name):
        parent=os.environ.get('EP19_QUALIFICATION_FIXTURE_ROOT')
        return Path(tempfile.mkdtemp(prefix=name+'-',dir=parent))
    def invoke(self,scenario):
        base=self.temp(scenario);out=base/'out'
        process=subprocess.run([sys.executable,'-B',str(DRIVER),'fixture','--fixture-root',str(base/'fixture'),
                                '--output',str(out),'--scenario',scenario],text=True,capture_output=True)
        self.assertEqual(process.returncode,0,process.stderr)
        return json.loads((out/'RESULT.json').read_text())
    def test_cli_help_is_real_and_lists_one_shot_formal(self):
        result=subprocess.run([sys.executable,'-B',str(DRIVER),'--help'],text=True,capture_output=True)
        self.assertEqual(result.returncode,0);self.assertIn('formal',result.stdout);self.assertIn('fixture',result.stdout)
    def test_no_standalone_baseline_or_preflight_subcommands(self):
        choices=driver.parser()._subparsers._group_actions[0].choices
        self.assertNotIn('baseline',choices);self.assertNotIn('preflight',choices)
    def test_allowed_real_observer_graph_dispatches_all_29(self):
        row=self.invoke('allowed');self.assertEqual((row['result'],row['passed'],row['failed'],row['not_run']),('PASS',29,0,0))
        self.assertEqual(row['dispatched'],list(range(29)))
    def test_disallowed_real_write_stops_and_accounts_remaining(self):
        row=self.invoke('disallowed');self.assertEqual((row['failed'],row['not_run'],row['dispatched']),(1,28,[0]))
    def test_bad_coverage_stops_before_dispatch(self):
        row=self.invoke('bad-coverage');self.assertEqual((row['dispatched'],row['not_run']),([],29));self.assertIn('BOUNDARY_REJECT',row['reason'])
    def test_capture_failure_stops_before_dispatch(self):
        row=self.invoke('capture-failure');self.assertEqual((row['dispatched'],row['not_run']),([],29))
    def test_fixture_never_marks_formal_or_product_execution(self):
        row=self.invoke('allowed');self.assertFalse(row['formal_attempt']);self.assertFalse(row['product_gate_execution']);self.assertTrue(row['fixture_only'])
    def test_actual_matrix_is_exact_29_unique_and_commands_nonempty(self):
        matrix=json.loads((ROOT/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json').read_text())
        self.assertEqual(len(matrix['order']),29);self.assertEqual(set(matrix['order']),set(matrix['gates']))
        self.assertEqual(len(set(matrix['order'])),29);self.assertTrue(all(matrix['gates'][k]['command'] for k in matrix['order']))
    def test_existing_matrix_timeout_values_are_not_rewritten(self):
        source=ROOT.parents[2]/'formal-tooling/candidate-inputs-v3/GATE_EXECUTION_MATRIX.json'
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),hashlib.sha256((ROOT/'candidate-inputs-v3/GATE_EXECUTION_MATRIX.json').read_bytes()).digest())
    def test_runtime_wrapper_and_gradle_init_closure_present(self):
        for name in ('runner.py','native_observe.py','observe.py','boundary.py','executor_adapter.py','compile.init.gradle','packaging.init.gradle','vite_closure.mjs'):
            self.assertTrue((EXECUTOR/name).is_file(),name)
        self.assertTrue(driver.verify_required_runtime_files())
    def test_missing_actual_wrapper_or_init_fails_closed(self):
        base=self.temp('missing-runtime');folder=base/'executor';folder.mkdir()
        for name in driver.REQUIRED_RUNTIME_FILES:
            if name!='packaging.init.gradle':(folder/name).write_text('fixture')
        with self.assertRaisesRegex(RuntimeError,'REQUIRED_RUNTIME_WRAPPER_OR_INIT_MISSING'):
            driver.verify_required_runtime_files(base)
    def test_formal_marker_precedes_observer_and_policy_in_source(self):
        text=DRIVER.read_text();body=text[text.index('def formal(args):'):text.index('def endpoint_checks():')]
        self.assertLess(body.index('consume_formal'),body.index('BoundaryObserver'));self.assertLess(body.index('consume_formal'),body.index('policy_builder'))
    def test_only_one_formal_marker_write_site(self):
        text=DRIVER.read_text();self.assertEqual(text.count("run/'FORMAL_ATTEMPT.json',value"),1)
    def test_failure_accounting_is_exact_29(self):
        class R:SHA='s';TREE='t'
        rows=driver.failure_results([str(x) for x in range(29)],R,'x')
        self.assertEqual(len(rows),29);self.assertTrue(all(v['result']=='NOT_RUN' for v in rows.values()))
    def test_native_observer_delegates_only_exact_v3_bookkeeping(self):
        text=(EXECUTOR/'native_observe.py').read_text();self.assertIn('DELEGATED_TO_CONTINUOUS_V3_OBSERVER',text)
        self.assertIn('path in self.bookkeeping_paths',text);self.assertIn('bookkeeping_v3.TEMP_RE.fullmatch',text)
    def test_full_backend_identity_expectation_remains_8000_29(self):
        text=DRIVER.read_text();self.assertIn("'expected_full_backend_identities':8000",text);self.assertIn("'expected_skips':29",text)

if __name__=='__main__':unittest.main(verbosity=2)
