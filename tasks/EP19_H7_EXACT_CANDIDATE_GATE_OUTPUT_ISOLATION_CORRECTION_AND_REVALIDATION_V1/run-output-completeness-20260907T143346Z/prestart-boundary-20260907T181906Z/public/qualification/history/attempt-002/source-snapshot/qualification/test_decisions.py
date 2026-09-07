"""Disposable retained controls. No product commands or formal prepare/launch.

run_all is real. Owner authorization, expensive technical preflight and gates
are explicit fixture adapters; filesystem comparisons and seal checks are real.
"""
from pathlib import Path
from contextlib import ExitStack
import copy
import errno
import hashlib
import json
import os
import shutil
import sys
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'executor'))
import artifacts
import coverage
import decision_evidence as de
import execution
import observe
import preservation
import runner

OUT = Path(os.environ['EP19_DIAGNOSTIC_TEST_OUTPUT'])


def put(path, value):
    coverage.put(path, value)


class DecisionControls(unittest.TestCase):
    def setUp(self):
        self.root = OUT/'fixtures'/(self._testMethodName+'-'+uuid.uuid4().hex)
        self.run = self.root/'outputs/continuation-runs/fixture'
        (self.run/'runtime/gates').mkdir(parents=True)
        (self.run/'runtime/producer-events').mkdir()
        self.target = self.root/'protected.txt'
        self.target.write_text('FIXTURE instruction body, never exported in decision evidence')
        self.baseline = observe.snapshot([self.target])
        put(self.run/'baseline.json', {'result':'COMPLETE', 'entries':self.baseline})
        self.scope = {'protected':[str(self.target)], 'allowed':[str(self.run/'runtime')],
                      'sealed_inputs':[], 'frozen_roots':[], 'enumeration_roots':[],
                      'repositories':[], 'metadata_roots':[], 'cross_lane':[],
                      'shared_git':None, 'pruned_roots':[], 'expected_missing':[],
                      'shadow_root':str(self.root/'shadow'), 'shadow_declared':['control']}
        put(self.run/'scope.json', self.scope)
        self.init = self.run/'runtime/cache/backend/gradle/init.d'
        self.init.mkdir(parents=True)
        shutil.copyfile(runner.H/'packaging.init.gradle', self.init/'ep19-packaging.gradle')
        self.sources = coverage.local_imports()[0]
        self.sealed = coverage.seal([*self.sources, self.init/'ep19-packaging.gradle'])
        self.ids = {'candidate':runner.SHA, 'tree':runner.TREE, 'base':runner.BASE, 'run_id':self.run.name}
        self.seal = {**self.ids, 'files':self.sealed}
        put(self.run/'seal.json', self.seal)
        self.ready = {**self.ids, 'result':'ENGINEERING_READY', 'engineering_blockers':[]}
        put(self.run/'preflight.json', self.ready)
        self.review = self.root/'review.json'
        self.decision = {**self.ids, **runner.REVIEW_STATES, 'independent_review':'PENDING',
                         'engineering_execution_authorization':'OWNER_AUTHORIZED',
                         'owner_decision_sha256':runner.OWNER_SHA256,
                         'seal_sha256':coverage.digest(self.run/'seal.json'),
                         'preflight_sha256':coverage.digest(self.run/'preflight.json')}
        put(self.review, self.decision)
        self.matrix = {'order':['FIXTURE'], 'gates':{'FIXTURE':{
            'repository':str(self.root), 'dependencies':[],
            'command':['PRODUCT_COMMAND_MUST_NEVER_EXECUTE']}}}
        put(self.run/'bindings.json', self.matrix)
        self.addCleanup(lambda: put(self.root/'fixture-control.json', {
            'test':self.id(), 'fixture_only':True, 'retained':True,
            'product_gate_execution':False}))

    def receipts(self):
        return [(p, json.loads(p.read_text())) for p in sorted((self.run/'runtime/decision-evidence').glob('*.json'))]

    def compare(self, **kwargs):
        return runner.compare_baseline(self.run, {}, phase='PRESTART', **kwargs)

    def adapters(self, preflight=None, gate=None):
        stack = ExitStack()
        stack.enter_context(patch.object(runner, 'owner_authorization'))
        stack.enter_context(patch.object(execution, 'D', self.root))
        stack.enter_context(patch.object(runner, 'preflight', side_effect=preflight or
                                        (lambda *a, **kw:dict(self.ready))))
        stack.enter_context(patch.object(runner, 'run_gate', side_effect=gate or self.fixture_gate))
        return stack

    def fixture_gate(self, name, matrix, run, scope, sealed, results):
        # An inert fixture receipt exercises real graph/final dependency validation.
        gate = run/'runtime/gates'/name
        gate.mkdir()
        data = gate/'fixture-only.txt'
        data.write_text('Synthetic gate adapter: no command was launched')
        row = {**self.ids, 'gate':name, 'native_exit':0, 'wrapper_exit':0}
        return artifacts.finalize(row, gate, [data])

    def reject_launch(self, reason, **kwargs):
        with self.adapters(**kwargs), self.assertRaisesRegex(RuntimeError, reason):
            runner.run_all(self.run, self.review)
        self.assertFalse((self.run/'runtime/START.json').exists())
        self.assertEqual(list((self.run/'runtime/gates').iterdir()), [])

    def test_real_run_all_positive_prestart_and_final(self):
        with self.adapters():
            self.assertEqual(runner.run_all(self.run, self.review), 0)
        rows = [r for _, r in self.receipts()]
        self.assertEqual([r['phase'] for r in rows], ['PRESTART', 'FINAL_ACCEPTANCE'])
        self.assertEqual([r['START']['status'] for r in rows], ['ABSENT_AT_CAPTURE', 'FILE_PRESENT_AT_CAPTURE'])
        self.assertTrue(all(r['decision'] == 'PASS' for r in rows))
        self.assertTrue(all(r['gate_process_status'] == 'NOT_ESTABLISHED' for r in rows))
        self.assertEqual(json.loads((self.run/'runtime/RESULTS.json').read_text())['result'], 'PASS')

    def test_real_run_all_protected_drift_before_start(self):
        self.target.write_text('changed')
        self.reject_launch('FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP')
        row = self.receipts()[0][1]
        self.assertEqual(row['reason'], 'FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP')
        self.assertEqual(row['START']['status'], 'ABSENT_AT_CAPTURE')
        self.assertEqual(row['phase'], 'PRESTART')
        self.assertIn('sha256', [f['field'] for f in row['differences'][0]['fields']])

    def test_actual_gate_boundary_rejects_before_command(self):
        self.target.write_text('changed')
        with patch.object(runner, 'repos', return_value=[]), patch.object(observe, 'run') as child:
            row = runner.run_gate('FIXTURE', self.matrix, self.run, self.scope, self.sealed, {})
        child.assert_not_called()
        self.assertEqual(row['reason'], 'FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP')
        receipt = self.receipts()[0][1]
        self.assertEqual((receipt['phase'], receipt['gate']), ('GATE_BOUNDARY', 'FIXTURE'))
        self.assertEqual(receipt['call_boundary'], 'GATE_COMMAND_NOT_YET_INVOKED_BY_THIS_CALL')

    def test_actual_preflight_phase_and_rejection(self):
        self.target.write_text('changed')
        # Unprepared technical fixture intentionally blocks other preflight areas.
        with patch.object(runner, 'owner_authorization'), patch.object(runner, 'repos', return_value=[]), \
                patch.object(runner.bindings, 'build', return_value=self.matrix):
            result = runner.preflight(self.run, write=False)
        put(self.root/'actual-preflight-result.json', result)
        self.assertIn('FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP', result['engineering_blockers'])
        self.assertEqual(self.receipts()[0][1]['phase'], 'PREFLIGHT')

    def test_launch_preflight_callsite_labels_and_blocks(self):
        original = runner.preflight
        def technical(*args, **kwargs):
            self.assertEqual(kwargs['decision_phase'], 'LAUNCH_PREFLIGHT')
            with patch.object(runner, 'repos', return_value=[]), \
                    patch.object(runner.bindings, 'build', return_value=self.matrix):
                return original(*args, **kwargs)
        self.reject_launch('CURRENT_TECHNICAL_PREFLIGHT_REJECT', preflight=technical)
        self.assertEqual(self.receipts()[0][1]['phase'], 'LAUNCH_PREFLIGHT')

    def test_final_callsite_drift_rejects_and_keeps_prestart(self):
        def gate(*args):
            result = self.fixture_gate(*args)
            self.target.write_text('fixture changed after prestart')
            return result
        with self.adapters(gate=gate):
            self.assertEqual(runner.run_all(self.run, self.review), 1)
        rows = [r for _, r in self.receipts()]
        self.assertEqual([r['decision'] for r in rows], ['PASS', 'REJECT'])
        self.assertEqual(rows[-1]['phase'], 'FINAL_ACCEPTANCE')
        self.assertEqual(json.loads((self.run/'runtime/STOP.json').read_text())['phase'], 'FINAL_ACCEPTANCE')

    def test_one_capture_binds_passing_decision_not_later_values(self):
        raw = (self.run/'baseline.json').read_bytes()
        native = preservation.Collector.capture
        count = []
        def capture(collector):
            result = native(collector)
            if str(self.target) in result['entries']:
                count.append(1)
                self.target.write_text('later value')
                (self.run/'baseline.json').write_text('{"entries":{}}')
            return result
        with patch.object(preservation.Collector, 'capture', capture):
            saved = self.compare()
        row = json.loads(saved.read_text())
        self.assertEqual(count, [1])
        self.assertEqual(row['current'], self.baseline)
        self.assertEqual(row['baseline_entries'], self.baseline)
        self.assertEqual(row['baseline_identity']['raw_sha256'], de.digest(raw))
        self.assertEqual(row['decision'], 'PASS')
        self.assertNotIn('FIXTURE instruction body', saved.read_text())

    def test_rejection_binds_capture_not_later_restoration(self):
        self.target.write_text('bad at decision')
        native = preservation.Collector.capture
        seen = {}
        def capture(collector):
            result = native(collector)
            if str(self.target) in result['entries']:
                seen.update(copy.deepcopy(result['entries']))
                self.target.write_text('restored later')
            return result
        with patch.object(preservation.Collector, 'capture', capture), \
                self.assertRaisesRegex(RuntimeError, 'FROZEN_BASELINE_DRIFT'):
            self.compare()
        self.assertEqual(self.receipts()[0][1]['current'], seen)

    def test_later_decision_cannot_overwrite_prior_receipt(self):
        first = self.compare(); raw = first.read_bytes()
        self.target.write_text('later mutation')
        with self.assertRaises(RuntimeError):
            self.compare()
        self.assertEqual(first.read_bytes(), raw)
        self.assertEqual(len(self.receipts()), 2)
        self.assertEqual(first.stat().st_mode & 0o777, 0o400)
        with self.assertRaises(PermissionError):
            first.open('wb')

    def test_incomplete_capture_preserves_partial_rows_and_errors(self):
        missing = self.root/'later-missing'
        missing.write_text('once present')
        before = observe.snapshot([self.target, missing])
        (self.run/'baseline.json').write_text(json.dumps({'entries':before}))
        missing.unlink()
        with self.assertRaisesRegex(RuntimeError, 'INCOMPLETE_CAPTURE'):
            self.compare()
        row = self.receipts()[0][1]
        self.assertIn(str(self.target), row['current'])
        self.assertEqual(row['capture_errors'][0]['errno'], errno.ENOENT)
        self.assertIn('missing', next(r for r in row['differences'] if r['path'] == str(missing))['categories'])

    def test_capture_exception_retains_accumulated_rows(self):
        native = preservation.Collector.capture
        def capture(collector):
            result = native(collector)
            if str(self.target) in result['entries']:
                raise OSError(errno.EIO, 'INJECTED_CAPTURE_EXCEPTION_AFTER_PARTIAL_ROWS')
            return result
        with patch.object(preservation.Collector, 'capture', capture), \
                self.assertRaisesRegex(RuntimeError, 'INCOMPLETE_CAPTURE'):
            self.compare()
        row = self.receipts()[0][1]
        self.assertEqual(row['current'], self.baseline)
        self.assertEqual(row['capture_errors'][0]['errno'], errno.EIO)
        self.assertEqual(row['decision'], 'REJECT')

    def test_native_unreadable_capture_rejects_before_start(self):
        self.target.chmod(0)
        try:
            self.reject_launch('INCOMPLETE_CAPTURE')
        finally:
            self.target.chmod(0o600)
        row = self.receipts()[0][1]
        self.assertEqual(row['capture_errors'][0]['errno'], errno.EACCES)
        self.assertIn('unreadable', row['differences'][0]['categories'])

    def test_native_file_mutation_during_capture_unstable_rejects(self):
        original = de.Collector
        def collector(*args, **kwargs):
            def hook(phase, path):
                if phase == 'after_read' and path == self.target:
                    self.target.write_text('native mutation at injected scheduling hook')
            return original(*args, hook=hook, **kwargs)
        with patch.object(de, 'Collector', collector), self.assertRaisesRegex(RuntimeError, 'INCOMPLETE_CAPTURE'):
            self.compare()
        row = self.receipts()[0][1]
        self.assertIn('unstable', row['differences'][0]['categories'])

    def test_injected_incomplete_even_equal_entries_rejects(self):
        native = preservation.Collector.capture
        def capture(collector):
            result = native(collector)
            if str(self.target) in result['entries']:
                result['result'] = 'INCOMPLETE'
            return result
        with patch.object(preservation.Collector, 'capture', capture):
            self.reject_launch('INCOMPLETE_CAPTURE')
        self.assertEqual(self.receipts()[0][1]['current'], self.baseline)

    def test_native_evidence_permission_failure_rejects_launch(self):
        out = self.run/'runtime/decision-evidence'
        out.mkdir(mode=0o500)
        try:
            self.reject_launch('DECISION_EVIDENCE_WRITE_FAILED.*Permission denied')
        finally:
            out.chmod(0o700)
        self.assertEqual(self.receipts(), [])

    def test_injected_partial_write_failure_retained(self):
        native = de.os.write
        calls = []
        def write(fd, data):
            if not calls:
                calls.append(1)
                return native(fd, data[:64])
            raise OSError(errno.ENOSPC, 'INJECTED_ENOSPC_NOT_NATIVE_DISK_EXHAUSTION')
        with patch.object(de.os, 'write', write):
            self.reject_launch('DECISION_EVIDENCE_WRITE_FAILED.*INJECTED_ENOSPC')
        files = list((self.run/'runtime/decision-evidence').glob('*.json'))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].stat().st_size, 64)
        self.assertEqual(files[0].stat().st_mode & 0o777, 0o400)

    def test_injected_fsync_failure_rejects_despite_complete_file(self):
        with patch.object(de.os, 'fsync', side_effect=OSError(errno.EIO, 'INJECTED_FSYNC_FAILURE')):
            self.reject_launch('DECISION_EVIDENCE_WRITE_FAILED.*INJECTED_FSYNC_FAILURE')
        row = self.receipts()[0][1]
        self.assertEqual(row['decision'], 'PASS')
        self.assertIn('does not prove write/fsync completion', row['decision_scope'])

    def test_unreadable_baseline_retains_error_when_scope_allows_evidence(self):
        path = self.run/'baseline.json'
        path.chmod(0)
        try:
            with self.assertRaises(PermissionError):
                self.compare()
        finally:
            path.chmod(0o600)
        row = self.receipts()[0][1]
        self.assertEqual(row['decision'], 'REJECT')
        self.assertEqual(row['baseline_identity']['status'], 'NOT_ESTABLISHED')
        self.assertEqual(row['evidence_errors'][0]['errno'], errno.EACCES)

    def test_malformed_baseline_retains_raw_identity_and_error(self):
        path = self.run/'baseline.json'
        path.write_text('{malformed fixture baseline')
        with self.assertRaises(json.JSONDecodeError):
            self.compare()
        row = self.receipts()[0][1]
        self.assertEqual(row['baseline_identity']['raw_sha256'], coverage.digest(path))
        self.assertEqual(row['decision'], 'REJECT')

    def test_effective_scope_cannot_remove_stored_overlap(self):
        stored = copy.deepcopy(self.scope)
        stored['enumeration_roots'] = [str(self.run/'runtime')]
        (self.run/'scope.json').write_text(json.dumps(stored))
        with self.assertRaisesRegex(RuntimeError, 'DECISION_EVIDENCE_SCOPE_OVERLAP'):
            self.compare(scope=self.scope)
        self.assertFalse((self.run/'runtime/decision-evidence').exists())

    def test_protected_permission_change_remains_mismatch(self):
        self.target.chmod(0o600)
        self.reject_launch('FROZEN_BASELINE_DRIFT')
        fields = self.receipts()[0][1]['differences'][0]['fields']
        self.assertIn('metadata.st_mode', [f['field'] for f in fields])

    def test_expected_missing_reappearance_is_not_accepted(self):
        path = self.root/'expected-missing'
        (self.run/'baseline.json').write_text(json.dumps({'entries':observe.snapshot([path], [path])}))
        path.write_text('unexpected addition')
        with self.assertRaisesRegex(RuntimeError, 'INCOMPLETE_CAPTURE'):
            self.compare()
        row = self.receipts()[0][1]
        self.assertIn('EXPECTED_ABSENCE_CHANGED', str(row['capture_errors']))
        self.assertIn('added', row['differences'][0]['categories'])

    def test_directory_metadata_fields_remain_compared(self):
        directory = self.root/'directory'
        directory.mkdir()
        before = observe.snapshot([directory])
        (self.run/'baseline.json').write_text(json.dumps({'entries':before}))
        (directory/'new-entry').write_text('new')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN_BASELINE_DRIFT'):
            self.compare()
        self.assertTrue(self.receipts()[0][1]['differences'][0]['fields'])

    def test_observer_directory_entry_rejects_even_metadata_restored_in_fixture(self):
        directory = self.root/'observed-repository'
        directory.mkdir()
        before = observe.snapshot([directory])
        watch = observe.Watch([directory], [directory], [], [])
        try:
            (directory/'unknown').write_text('new entry')
            old = before[str(directory)]['metadata']
            native_metadata = preservation.metadata
            def fixture_restored(st):
                result = native_metadata(st)
                return dict(old) if result['st_ino'] == old['st_ino'] else result
            # Explicit fault model: all directory endpoint metadata reads restored.
            with patch.object(preservation, 'metadata', fixture_restored):
                self.assertEqual(observe.snapshot([directory]), before)
            watch.drain()
            self.assertTrue(watch.rejected())
            put(self.root/'observer-events.json', {'events':watch.events, 'errors':watch.errors,
                'fixture_metadata_restoration':'mocked all directory metadata fields; actual native create event'})
        finally:
            watch.close()

    def test_observer_instruction_and_unknown_path_violations(self):
        instructions = self.root/'instructions'
        repo = self.root/'repository'
        instructions.mkdir(); repo.mkdir()
        body = instructions/'SKILL.md'; body.write_text('fixture instruction')
        watch = observe.Watch([body], [repo], [], [], enumeration_roots=[instructions])
        try:
            body.write_text('changed body'); (repo/'unknown').write_text('unknown')
            watch.drain()
            categories = {e['category'] for e in watch.events}
            self.assertTrue(watch.rejected())
            self.assertIn('REJECT_INSTRUCTION_EVENT', categories)
            self.assertIn('REJECT_UNDECLARED_REPOSITORY_WRITE', categories)
            put(self.root/'observer-events.json', {'events':watch.events, 'errors':watch.errors})
        finally:
            watch.close()

    def test_usage_runtime_protected_member_is_not_excluded(self):
        usage = self.run/'runtime/usage.json'
        usage.write_text('usage old')
        (self.run/'baseline.json').write_text(json.dumps({'entries':observe.snapshot([usage])}))
        usage.write_text('usage new')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN_BASELINE_DRIFT'):
            self.compare()
        self.assertIn(str(usage), self.receipts()[0][1]['before'])

    def test_scope_overlap_rejected_without_writing_evidence(self):
        for kind in ('protected', 'sealed_inputs', 'frozen_roots', 'enumeration_roots'):
            for path in (self.run/'runtime', self.run/'runtime/decision-evidence/reserved'):
                with self.subTest(kind=kind, path=path):
                    scope = copy.deepcopy(self.scope)
                    scope[kind] = [str(path)]
                    with self.assertRaisesRegex(RuntimeError, 'DECISION_EVIDENCE_SCOPE_OVERLAP'):
                        self.compare(scope=scope)
        self.assertFalse((self.run/'runtime/decision-evidence').exists())

    def test_baseline_parent_directory_overlap_rejected(self):
        (self.run/'baseline.json').write_text(json.dumps({'entries':observe.snapshot([self.run/'runtime'])}))
        with self.assertRaisesRegex(RuntimeError, 'DECISION_EVIDENCE_SCOPE_OVERLAP'):
            self.compare()
        self.assertFalse((self.run/'runtime/decision-evidence').exists())

    def test_output_symlink_rejects_without_following(self):
        outside = self.root/'outside'; outside.mkdir()
        (self.run/'runtime/decision-evidence').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'DECISION_EVIDENCE_WRITE_FAILED'):
            self.compare()
        self.assertEqual(list(outside.iterdir()), [])

    def test_output_symlink_ancestor_rejects(self):
        outside = self.root/'moved-runtime'
        (self.run/'runtime').rename(outside)
        (self.run/'runtime').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'DECISION_EVIDENCE_WRITE_FAILED'):
            self.compare()
        self.assertFalse((outside/'decision-evidence').exists())

    def test_successful_shadow_exception_and_exact_check_preserved(self):
        root = Path(self.scope['shadow_root'])
        (root/'.git').mkdir(parents=True)
        paths = [root/'control', root/'.git/index']
        for path in paths: path.write_text('original fixture')
        (self.run/'baseline.json').write_text(json.dumps({'entries':observe.snapshot([self.target, *paths])}))
        for path in paths: path.write_text('changed fixture metadata/content, exact mocked separately')
        with patch.object(runner, 'exact') as exact:
            runner.compare_baseline(self.run, {'SHADOW':{'result':'PASS'}}, phase='FINAL_ACCEPTANCE')
        exact.assert_called_once_with(root)
        self.assertEqual(set(self.receipts()[0][1]['shadow_omitted']), set(map(str, paths)))
        with patch.object(runner, 'exact', side_effect=RuntimeError('TRACKED_INPUT_MISMATCH')), \
                self.assertRaisesRegex(RuntimeError, 'TRACKED_INPUT_MISMATCH'):
            runner.compare_baseline(self.run, {'SHADOW':{'result':'PASS'}}, phase='FINAL_ACCEPTANCE')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN_BASELINE_DRIFT'):
            runner.compare_baseline(self.run, {'SHADOW':{'result':'FAIL'}}, phase='GATE_BOUNDARY')

    def test_old_launch_seal_missing_new_helper_rejects(self):
        self.seal['files'].pop(str(ROOT/'executor/decision_evidence.py'))
        (self.run/'seal.json').write_text(json.dumps(self.seal))
        self.reject_launch('EXECUTOR_SOURCE_BINDING_MISSING')

    def test_changed_launch_source_rejects_using_disposable_copy(self):
        copied = self.root/'executor-copy'
        shutil.copytree(ROOT/'executor', copied)
        self.seal['files'] = coverage.seal([*copied.iterdir(), self.init/'ep19-packaging.gradle'])
        (self.run/'seal.json').write_text(json.dumps(self.seal))
        with (copied/'runner.py').open('a') as file: file.write('\n# fixture stale source\n')
        with patch.object(coverage, 'H', copied), patch.object(runner, 'H', copied):
            self.reject_launch('FROZEN_INPUT_CHANGED')

    def test_mismatched_candidate_launch_identity_rejects(self):
        self.decision['candidate'] = '0'*40
        (self.review).write_text(json.dumps(self.decision))
        self.reject_launch('LAUNCH_CANDIDATE_IDENTITY_MISMATCH')

    def test_stale_qualification_helper_universe_rejects(self):
        q = self.root/'qualification.json'
        helpers = coverage.seal(self.sources)
        helpers.pop(str(ROOT/'executor/decision_evidence.py'))
        put(q, {'schema':'ep19-output-corrections-v2', 'helpers':helpers, 'dependencies':helpers})
        with self.assertRaisesRegex(RuntimeError, 'QUALIFICATION_HELPER_UNIVERSE_CHANGED'):
            coverage.qualification_inputs(q)

    def test_changed_qualification_program_identity_rejects(self):
        program = self.root/'qualification-program.py'
        program.write_text('# original fixture qualification')
        helpers = coverage.seal(self.sources)
        files = {**helpers, **coverage.seal([program])}
        q = self.root/'qualification.json'
        put(q, {'schema':'ep19-output-corrections-v2', 'helpers':helpers, 'dependencies':files})
        program.write_text('# changed qualification after sealing')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN_INPUT_CHANGED'):
            coverage.qualification_inputs(q)

    def test_unchanged_original_helpers_and_no_removed_sources(self):
        original = ROOT/'preimages/executor'
        for path in original.iterdir():
            if path.name != 'runner.py':
                self.assertEqual(path.read_bytes(), (ROOT/'executor'/path.name).read_bytes(), path.name)
        self.assertEqual({p.name for p in (ROOT/'executor').iterdir()} - {p.name for p in original.iterdir()},
                         {'decision_evidence.py'})


if __name__ == '__main__':
    class Result(unittest.TextTestResult):
        def startTest(self, test):
            super().startTest(test)
            self.active_id = test.id()
        def addSuccess(self, test):
            super().addSuccess(test); outcomes.append({'test':test.id(), 'result':'PASS'})
        def addFailure(self, test, err):
            super().addFailure(test, err); outcomes.append({'test':test.id(), 'result':'FAIL'})
        def addError(self, test, err):
            super().addError(test, err); outcomes.append({'test':test.id(), 'result':'ERROR'})
    outcomes = []
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DecisionControls)
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
    put(OUT/'test-results.json', {'result':'PASS' if result.wasSuccessful() else 'FAIL',
        'tests':result.testsRun, 'failures':len(result.failures), 'errors':len(result.errors),
        'skipped':len(result.skipped), 'controls':outcomes, 'product_gate_execution':False,
        'scope':'Disposable synthetic runner adapters and native filesystem controls only'})
    raise SystemExit(0 if result.wasSuccessful() else 1)
