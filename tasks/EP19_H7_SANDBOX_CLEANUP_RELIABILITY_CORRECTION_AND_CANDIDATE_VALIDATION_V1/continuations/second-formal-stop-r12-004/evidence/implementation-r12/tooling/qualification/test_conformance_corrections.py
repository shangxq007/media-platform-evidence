"""Fresh counterexamples for AR001-004/007-010 and AR005/006 regressions.

All filesystem mutations are confined to EP19_QUALIFICATION_FIXTURE_ROOT.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import stat

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "executor"
sys.path.insert(0, str(EXECUTOR))

import bookkeeping_v3 as bk
import boundary
import capture
import executor_adapter
import external29_driver
import observe
import native_observe


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class Fixture(unittest.TestCase):
    def setUp(self):
        base = os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT")
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.skills.mkdir(mode=0o700)
        self.package = self.skills / "alpha"
        self.package.mkdir()
        (self.package / "SKILL.md").write_text("fixture\n")
        self.usage = self.skills / bk.USAGE_NAME
        dump(self.usage, {"alpha": {"view_count": 1, "use_count": 1,
                                    "last_viewed_at": None, "last_used_at": None}})
        os.chmod(self.usage, 0o600)
        self.lock = self.skills / bk.LOCK_NAME
        self.lock.touch(mode=0o644)
        self.ledger = self.skills / bk.LEDGER_NAME
        self.ledger.write_bytes(b"")
        os.chmod(self.ledger, 0o600)
        self.policy = bk.create_policy(self.skills, owner_sha256="4" * 64,
                                       dependency_sha256="5" * 64,
                                       eligible_names=["alpha"], fixture=True)

    def engine(self):
        return boundary.Engine(self.policy)

    def record(self, ident="111111111111", timestamp=None):
        manifest = deepcopy(self.policy["eligible_map"]["alpha"]["manifest"])
        return {"id": ident,
                "ts": timestamp or datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                "actor": "agent", "action": "edit", "skill": "alpha",
                "evidence": {}, "before": manifest, "after": deepcopy(manifest)}

    def append_raw(self, raw):
        with self.ledger.open("ab") as stream:
            stream.write(raw)

    def observed_decision(self, mutate, phase="GATE"):
        engine = self.engine()
        with observe.BoundaryObserver(self.policy) as watcher:
            mutate(watcher)
            events, errors = watcher.boundary_events()
        return engine.check(phase, events=events, coverage_errors=errors)


class Group1ContinuousAndTemp(Fixture):
    def test_external_file_moved_into_usage_is_rejected_by_real_observer(self):
        external = self.base / "external-usage"
        external.write_bytes(self.usage.read_bytes())
        os.chmod(external, 0o600)
        result = self.observed_decision(lambda watcher: os.replace(external, self.usage))
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("UNREGISTERED_SOURCE" in reason for reason in result["event_reasons"]), result)

    def test_bad_mode_short_lived_temp_is_rejected_by_real_observer(self):
        def mutate(watcher):
            temp = self.skills / ".usage_badmode1.tmp"
            temp.write_bytes(self.usage.read_bytes())
            os.chmod(temp, 0o644)
            watcher.drain()
            temp.unlink()
        result = self.observed_decision(mutate)
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("TEMP_OWNER_GROUP_MODE" in reason for reason in result["event_reasons"]), result)

    def test_temp_moved_outside_without_usage_target_is_rejected(self):
        def mutate(watcher):
            temp = self.skills / ".usage_moveout1.tmp"
            temp.write_bytes(self.usage.read_bytes())
            os.chmod(temp, 0o600)
            watcher.drain()
            os.replace(temp, self.base / "escaped")
        result = self.observed_decision(mutate)
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("RENAME_OUTSIDE_TARGET" in reason for reason in result["event_reasons"]), result)

    def test_outer_fixture_exercises_continuous_ancestor_rejection(self):
        out = self.base / "outer-out"
        fixture = self.base / "outer-fixture"
        process = subprocess.run(
            [sys.executable, "-B", str(EXECUTOR / "external29_driver.py"), "fixture",
             "--fixture-root", str(fixture), "--output", str(out),
             "--scenario", "ancestor-change"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads((out / "RESULT.json").read_text())
        self.assertEqual(result["result"], "EXPECTED_REJECT")
        self.assertIn("ANCESTOR", result["reason"])


class Group2TimeAndFraming(Fixture):
    def test_wall_clock_rollback_from_previous_accepted_boundary_rejects(self):
        engine = self.engine()
        engine.previous_boundary_wall_end_ns = time.time_ns() + 10_000_000_000
        engine.previous_boundary_monotonic_end_ns = time.monotonic_ns()
        result = engine.check("GATE")
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("WALL_CLOCK_ROLLBACK" in reason for reason in result["reasons"]), result)

    def test_future_ledger_timestamp_rejected_against_actual_capture_end(self):
        def mutate(watcher):
            raw = json.dumps(self.record(timestamp="2099-01-01T00:00:00.000000+00:00"),
                             sort_keys=True, separators=(",", ":")).encode() + b"\n"
            self.append_raw(raw)
        result = self.observed_decision(mutate)
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("OUTSIDE_BOUND_WINDOW" in reason for reason in result["reasons"]), result)

    def test_crlf_ledger_record_rejected_as_raw_framing(self):
        def mutate(watcher):
            raw = json.dumps(self.record(), sort_keys=True, separators=(",", ":")).encode() + b"\r\n"
            self.append_raw(raw)
        result = self.observed_decision(mutate)
        self.assertEqual(result["decision"], "REJECT", result)
        self.assertTrue(any("RAW_CR" in reason for reason in result["reasons"]), result)

    def test_escaped_cr_is_distinct_from_raw_cr(self):
        legacy = self.skills / "legacy"
        legacy.mkdir()
        (legacy / "SKILL.md").write_text("fixture\n")
        self.ledger.write_bytes(b'{"id":"000000000000","note":"escaped\\rvalue"}\n')
        policy = bk.create_policy(self.skills, owner_sha256="4" * 64,
                                  dependency_sha256="5" * 64,
                                  eligible_names=["alpha"], fixture=True)
        self.assertIn("000000000000", policy["ledger_original_ids"])

    def test_boundary_receipt_binds_actual_wall_and_monotonic_window(self):
        result = self.engine().check("BASELINE")
        window = result["capture_window"]
        self.assertLessEqual(window["wall_start_ns"], window["wall_end_ns"])
        self.assertLessEqual(window["monotonic_start_ns"], window["monotonic_end_ns"])
        self.assertNotIn("9999", window["wall_end_utc"])


class Group3IdentityAndProvenance(Fixture):
    def test_mandatory_affected_controls_are_fixed_independently(self):
        import qualification_contract
        required = qualification_contract.REQUIRED_AFFECTED_CONTROLS
        self.assertGreaterEqual(len(required), 12)
        self.assertIn(
            "test_conformance_corrections.Group1ContinuousAndTemp.test_external_file_moved_into_usage_is_rejected_by_real_observer",
            required)

    def test_missing_duplicate_unexpected_and_skip_are_all_rejected(self):
        import qualification_contract
        expected = ["a", "b"]
        rows = [{"id": "a", "actual": "PASS"}, {"id": "a", "actual": "PASS"},
                {"id": "c", "actual": "SKIP"}]
        result = qualification_contract.identity_accounting(expected, rows)
        self.assertEqual((result["missing"], result["unexpected"], result["duplicates"], result["skipped"]),
                         (["b"], ["c"], ["a"], ["c"]))
        self.assertEqual(result["result"], "REJECT")

    def test_dependency_source_closure_and_private_hashes_are_mandatory(self):
        import dependency_contract
        incomplete = {"schema": "ep19-writer-ledger-dependency-binding-v2",
                      "result": "PASS", "ledger_role": "OBSERVATION_INTEGRITY_ONLY",
                      "ledger_consumers": ["bookkeeping_v3.evaluate_ledger"],
                      "unbound_dynamic_readers": [], "authorization_source": False,
                      "instruction_or_skill_selection_source": False,
                      "candidate_selection_source": False,
                      "policy_or_gate_criteria_source": False, "rollback_source": False,
                      "sources": {}}
        with self.assertRaisesRegex(RuntimeError, "DEPENDENCY_SOURCE_CLOSURE"):
            dependency_contract.validate(incomplete, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")

    def test_private_eligibility_must_hash_bind_to_reviewed_applicability(self):
        import policy_builder as unused
        current = ROOT.parents[1]
        app = current / "writer-evidence-r2/INPUT_CURRENT_APPLICABILITY.json"
        private_map = current / "private-r6/ELIGIBLE_SKILLS_MAP.private.json"
        private_inventory = current / "private-r6/STRICT_PACKAGE_INVENTORY.private.json"
        dependency = Path(os.environ.get("EP19_TEST_DEPENDENCY_BINDING",
            current / "writer-evidence-r6/DEPENDENCY_BINDING.r6.candidate-003.json"))
        self.assertTrue(unused.validate_provenance(json.loads(app.read_text()), private_map,
                                                   private_inventory, json.loads(dependency.read_text())))

    def test_second_formal_run_id_is_exact_not_a_family(self):
        import binding_contract
        self.assertTrue(binding_contract.valid_run_id("candidate-formal-002"))
        self.assertFalse(binding_contract.valid_run_id("candidate-formal-002-extra"))


class Group4LatchDurabilityAndBounds(Fixture):
    def test_failure_marker_fsyncs_file_and_parent_directory(self):
        parent = self.base / "marker-parent"
        parent.mkdir()
        observed = []
        real_fsync = os.fsync
        def recording_fsync(fd):
            observed.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real_fsync(fd)
        with patch("durability.os.fsync", side_effect=recording_fsync):
            executor_adapter._durable_exclusive(parent / "marker.json", {"state": "failed"})
        self.assertIn("file", observed)
        self.assertIn("directory", observed)

    def test_evidence_failure_does_not_commit_engine_state(self):
        engine = self.engine()
        before_session = deepcopy(engine.session)
        before_usage = deepcopy(engine.previous_usage)
        not_directory = self.base / "not-a-directory"
        not_directory.write_text("x")
        with observe.BoundaryObserver(self.policy) as watcher:
            raw = json.dumps(self.record(), sort_keys=True, separators=(",", ":")).encode() + b"\n"
            self.append_raw(raw)
            events, errors = watcher.boundary_events()
        with self.assertRaises(boundary.BoundaryReject):
            engine.check("BASELINE", events=events, coverage_errors=errors, evidence_dir=not_directory)
        self.assertEqual(engine.session, before_session)
        self.assertEqual(engine.previous_usage, before_usage)

    def test_adapter_latches_after_actual_evidence_path_failure(self):
        run = self.base / "run"
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        not_directory = self.base / "not-a-directory"
        not_directory.write_text("x")
        with self.assertRaises(boundary.BoundaryReject):
            adapter.boundary("BASELINE", evidence_dir=not_directory)
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.preflight(evidence_dir=self.base / "recovered")

    def test_event_flood_is_bounded_during_real_drain(self):
        with observe.BoundaryObserver(self.policy) as watcher:
            for index in range(1200):
                temp = self.skills / f".usage_{index:08x}.tmp"
                temp.write_bytes(b"x")
                temp.unlink()
            events, errors = watcher.boundary_events()
        self.assertLessEqual(len(events), bk.LIMITS["pending_events_max"])
        self.assertIn("PENDING_EVENT_LIMIT_EXCEEDED_DURING_ACQUISITION", errors)

    def test_slow_regular_file_read_is_interrupted_inside_loop(self):
        target = self.base / "slow"
        target.write_bytes(b"x" * (capture.READ_CHUNK * 8))
        started = time.monotonic()
        def slow_hook(phase, path, attempt):
            if phase == "read":
                time.sleep(0.02)
        with self.assertRaisesRegex(capture.CaptureError, "TIME_LIMIT"):
            capture.capture_file(target, attempts=1, max_seconds=0.03, hook=slow_hook)
        self.assertLess(time.monotonic() - started, 0.12)

    def test_outer_fixture_failure_latch_blocks_success_final(self):
        out = self.base / "outer-out"
        fixture = self.base / "outer-fixture"
        process = subprocess.run(
            [sys.executable, "-B", str(EXECUTOR / "external29_driver.py"), "fixture",
             "--fixture-root", str(fixture), "--output", str(out),
             "--scenario", "evidence-failure"], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads((out / "RESULT.json").read_text())
        self.assertEqual(result["result"], "EXPECTED_REJECT")
        self.assertFalse(result["success_final_emitted"])


class PreformalActualRed(Fixture):
    """Behavioral predecessors for the six findings left open by preformal review."""

    def strict_scope(self, run):
        memory = self.base / "Memory.md"
        memory.write_text("sealed memory\n")
        scope = {"protected": [str(memory)], "expected_missing": []}
        baseline = {"entries": external29_driver.strict_capture(scope)["entries"]}
        dump(run / "baseline.json", baseline)
        return memory, scope

    def continuous(self, memory, run):
        return native_observe.Watch(
            protected=[memory], repositories=[], metadata_roots=[], allowed=[run],
            cross_lane=[], shared_git=None, enumeration_roots=[], pruned_roots=[],
            expected_missing=[], frozen_roots=[], bookkeeping_policy=self.policy)

    def test_ar001_final_receipt_contains_write_during_seal_capture(self):
        run = self.base / "final-run"
        run.mkdir()
        memory, scope = self.strict_scope(run)
        watcher = self.continuous(memory, run)
        real_capture = external29_driver.strict_capture

        def mutate_after_endpoint_capture(captured_scope):
            captured = real_capture(captured_scope)
            memory.write_text("changed during final seal capture\n")
            return captured

        try:
            with patch.object(external29_driver, "strict_capture",
                              side_effect=mutate_after_endpoint_capture):
                with self.assertRaisesRegex(RuntimeError, "STRICT_INPUT_BOUNDARY_REJECT"):
                    external29_driver.strict_check(
                        run, scope, self.policy, "SEAL", object(), watcher)
            receipt = json.loads(next((run / "runtime/strict-decisions").glob("*.json")).read_text())
            self.assertEqual(receipt["STRICT_INPUT_INTEGRITY"], "REJECT", receipt)
            self.assertTrue(receipt["continuous_events"], receipt)
        finally:
            watcher.close()

    def test_ar002_formal_seed_accepts_visible_legal_temp_without_keyerror(self):
        seed = {"root": str(self.skills), "paths": self.policy["paths"],
                "eligible_map": self.policy["eligible_map"]}
        with observe.BoundaryObserver(seed) as watcher:
            temp = self.skills / ".usage_abc12_3z.tmp"
            temp.write_bytes(self.usage.read_bytes())
            os.chmod(temp, 0o600)
            watcher.drain()
            self.assertTrue(any(row.get("temp_metadata_validated") for row in watcher.events),
                            watcher.events)

    def test_ar007_unknown_actual_status_cannot_pass_identity_accounting(self):
        import qualification_contract
        result = qualification_contract.identity_accounting(
            ["actual-control"], [{"id": "actual-control", "actual": "UNKNOWN"}])
        self.assertEqual(result["result"], "REJECT", result)

    def dependency_value_with(self, source_role, document):
        source = self.base / (source_role + ".json")
        dump(source, document)
        value = deepcopy(json.loads((ROOT.parents[1] / "writer-evidence/DEPENDENCY_BINDING.v2.json").read_text()))
        value["sources"][source_role] = {
            "path": str(source), "sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest()}
        return value

    def test_ar007_candidate_consumer_claim_is_checked_against_real_bytes(self):
        import dependency_contract
        fixed = deepcopy(json.loads((ROOT.parents[1] / "writer-evidence/INPUT_FIXED29_CONSUMER_BINDING.json").read_text()))
        fake = self.base / "claimed-candidate-source.py"
        fake.write_text("different bytes\n")
        fixed["candidate_sources"][0]["working_path"] = str(fake)
        value = self.dependency_value_with("fixed29_consumer_binding", fixed)
        with self.assertRaisesRegex(RuntimeError, "CANDIDATE_CONSUMER_SOURCE"):
            dependency_contract.validate(value, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")

    def test_ar007_instruction_selection_origin_hash_is_verified(self):
        import dependency_contract
        app = deepcopy(json.loads((ROOT.parents[1] / "writer-evidence/INPUT_CURRENT_APPLICABILITY.json").read_text()))
        app["instruction_source_bindings"][0]["sha256"] = "0" * 64
        value = self.dependency_value_with("current_applicability", app)
        with self.assertRaisesRegex(RuntimeError, "INSTRUCTION_SOURCE"):
            dependency_contract.validate(value, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")

    def test_ar008_transient_live_state_parse_failure_irreversibly_latches(self):
        run = self.base / "state-run"
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        real_read_text = Path.read_text
        failed_once = False

        def transient_read(path, *args, **kwargs):
            nonlocal failed_once
            if path == adapter.state_path and not failed_once:
                failed_once = True
                raise OSError("transient state read failure")
            return real_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", transient_read):
            with self.assertRaises(OSError):
                adapter.preflight()
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.preflight()

    def test_ar008_consume_write_failure_cannot_be_resurrected(self):
        run = self.base / "consume-run"
        adapter = executor_adapter.RunAdapter(run, self.policy)
        with patch.object(executor_adapter, "_durable_exclusive",
                          side_effect=OSError("transient consume failure")):
            with self.assertRaises(OSError):
                adapter.consume_for_baseline()
        executor_adapter._durable_exclusive(adapter.state_path, {
            "schema": "ep19-approved-bookkeeping-attempt-v3",
            "attempt_id": adapter.attempt_id,
            "state": "CONSUMED_BEFORE_BASELINE",
            "consumed_ns": time.time_ns(), "formal_attempt": False})
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.baseline()

    def test_ar008_outer_observer_failure_latches_same_adapter(self):
        run = self.base / "observer-run"
        run.mkdir()
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()

        class TransientObserver:
            def __init__(self): self.calls = 0
            def boundary_events(self):
                self.calls += 1
                if self.calls == 1: raise OSError("transient observer acquisition")
                return [], []

        observer = TransientObserver()
        with self.assertRaises(OSError):
            external29_driver.boundary(adapter, observer, "PREFLIGHT", run)
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            external29_driver.boundary(adapter, observer, "PREFLIGHT", run)

    def test_ar009_strict_decision_creation_fsyncs_publishing_runtime_directory(self):
        run = self.base / "durable-run"
        run.mkdir()
        unused_memory, scope = self.strict_scope(run)
        seen = []
        real_fsync = os.fsync

        def recording(fd):
            try: seen.append(os.readlink(f"/proc/self/fd/{fd}"))
            except OSError: seen.append("file")
            return real_fsync(fd)

        with patch("durability.os.fsync", side_effect=recording):
            external29_driver.strict_check(run, scope, self.policy, "PREFLIGHT", object())
        self.assertIn(str(run / "runtime"), seen, seen)

    def test_ar010_blocking_initial_fstat_is_interrupted_and_cleaned_up(self):
        target = self.base / "blocking-stat"
        target.write_bytes(b"ok")
        real_fstat = capture.os.fstat
        calls = 0

        def slow_first(fd):
            nonlocal calls
            calls += 1
            if calls == 1: time.sleep(0.2)
            return real_fstat(fd)

        started = time.monotonic()
        with patch.object(capture.os, "fstat", side_effect=slow_first):
            with self.assertRaisesRegex(capture.CaptureError, "TIME_LIMIT"):
                capture.capture_file(target, attempts=1, max_seconds=0.03)
        self.assertLess(time.monotonic() - started, 0.12)

    def test_ar010_temp_metadata_stat_is_bounded_inside_real_drain(self):
        real_lstat = os.lstat
        with observe.BoundaryObserver(self.policy) as watcher:
            temp = self.skills / ".usage_slow0001.tmp"
            temp.write_bytes(b"x")

            def slow_temp(path):
                if Path(path) == temp: time.sleep(5.2)
                return real_lstat(path)

            started = time.monotonic()
            with patch.object(observe.os, "lstat", slow_temp):
                watcher.drain()
            self.assertLess(time.monotonic() - started, 5.15)
            self.assertIn("EVENT_ACQUISITION_TIME_LIMIT_EXCEEDED", watcher.errors)


class PostfixIntegratedControls(Fixture):
    def test_final_combined_seal_rejects_memory_write_and_closes_observation(self):
        run = self.base / "combined-final-run"
        run.mkdir()
        memory = self.base / "Memory.md"
        memory.write_text("stable\n")
        adapter = executor_adapter.RunAdapter(run, self.policy)
        with observe.BoundaryObserver(self.policy) as observer:
            external29_driver.boundary(adapter, observer, "BASELINE", run)
            continuous = native_observe.Watch(
                protected=[memory], repositories=[], metadata_roots=[], allowed=[run],
                cross_lane=[], shared_git=None, enumeration_roots=[], pruned_roots=[],
                expected_missing=[], frozen_roots=[], bookkeeping_policy=self.policy)
            real_capture = bk.capture_bundle

            def mutate_during_seal(root, eligible_map):
                bundle = real_capture(root, eligible_map)
                memory.write_text("changed inside final seal acquisition\n")
                return bundle

            with patch.object(bk, "capture_bundle", side_effect=mutate_during_seal):
                with self.assertRaises(boundary.BoundaryReject):
                    external29_driver.boundary(
                        adapter, observer, "SEAL", run, continuous=continuous,
                        finalize_observation=True)
            self.assertTrue(observer.closed)
            self.assertTrue(continuous.closed)
        receipts = [json.loads(path.read_text()) for path in
                    (run / "runtime/bookkeeping-decisions").glob("*.json")]
        seal = next(row for row in receipts if row["phase"] == "SEAL")
        self.assertEqual(seal["decision"], "REJECT", seal)
        self.assertTrue(seal["final_observation_boundary"]["continuous_events"], seal)
        self.assertIn("no claim extends after it",
                      seal["final_observation_boundary"]["claim"])

    def test_seed_observer_rebind_accepts_legal_visible_temp_rename(self):
        seed = {"root": str(self.skills), "paths": self.policy["paths"],
                "eligible_map": self.policy["eligible_map"]}
        engine = self.engine()
        with observe.BoundaryObserver(seed) as watcher:
            watcher.bind_policy(self.policy)
            temp = self.skills / ".usage_abc12_3z.tmp"
            temp.write_bytes(self.usage.read_bytes())
            os.chmod(temp, 0o600)
            watcher.drain()
            os.replace(temp, self.usage)
            events, errors = watcher.boundary_events()
        result = engine.check("GATE", events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)

    def test_current_dependency_evidence_validates_real_r2_sources(self):
        import dependency_contract
        current = ROOT.parents[1]
        dependency = Path(os.environ.get("EP19_TEST_DEPENDENCY_BINDING",
            current / "writer-evidence-r6/DEPENDENCY_BINDING.r6.candidate-003.json"))
        value = json.loads(dependency.read_text())
        self.assertTrue(dependency_contract.validate(
            value, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json"))

    def test_duplicate_expected_identity_is_explicitly_rejected(self):
        import qualification_contract
        result = qualification_contract.identity_accounting(
            ["a", "a"], [{"id": "a", "actual": "PASS"},
                          {"id": "a", "actual": "PASS"}])
        self.assertEqual(result["expected_duplicates"], ["a"])
        self.assertEqual(result["result"], "REJECT")

    def test_postread_path_stat_is_deadline_guarded(self):
        target = self.base / "postread-stat"
        target.write_bytes(b"ok")
        real_lstat = capture.os.lstat
        calls = 0

        def slow_second(path):
            nonlocal calls
            calls += 1
            if calls == 2: time.sleep(0.2)
            return real_lstat(path)

        started = time.monotonic()
        with patch.object(capture.os, "lstat", side_effect=slow_second):
            with self.assertRaisesRegex(capture.CaptureError, "TIME_LIMIT"):
                capture.capture_file(target, attempts=1, max_seconds=0.03)
        self.assertLess(time.monotonic() - started, 0.12)

    def test_real_sustained_growth_is_bounded(self):
        target = self.base / "growing"
        target.write_bytes(b"x" * capture.READ_CHUNK)
        stop = threading.Event()

        def grow():
            with target.open("ab", buffering=0) as stream:
                while not stop.is_set():
                    stream.write(b"y" * 65536)
                    time.sleep(0.0005)

        worker = threading.Thread(target=grow)
        worker.start()
        started = time.monotonic()
        try:
            with self.assertRaises(capture.CaptureError):
                capture.capture_file(target, attempts=1, max_seconds=0.05,
                                     hook=lambda phase, path, attempt: time.sleep(0.002))
        finally:
            stop.set();worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertLess(time.monotonic() - started, 0.25)

    def test_directory_over_capacity_rejects(self):
        directory = self.base / "over-capacity"
        directory.mkdir()
        for index in range(32):
            (directory / f"entry-{index:02d}").write_text("x")
        with self.assertRaisesRegex(capture.CaptureError, "DIRECTORY_ENTRY_LIMIT_EXCEEDED"):
            capture.capture_directory(directory, max_entries=16,
                                      deadline=time.monotonic() + 1)

    def test_strict_acquisition_failure_latches_actual_adapter(self):
        run = self.base / "strict-latch-run"
        run.mkdir()
        memory = self.base / "strict-latch-memory"
        memory.write_text("stable\n")
        scope = {"protected": [str(memory)], "expected_missing": []}
        dump(run / "baseline.json", {"entries": external29_driver.strict_capture(scope)["entries"]})
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        memory.unlink()
        with self.assertRaisesRegex(RuntimeError, "STRICT_INPUT_BOUNDARY_REJECT"):
            external29_driver.latching_strict_check(
                adapter, run, scope, self.policy, "COMMAND_BEFORE_FIXTURE", object())
        memory.write_text("stable\n")
        with observe.BoundaryObserver(self.policy) as observer:
            with self.assertRaises(executor_adapter.NamespaceConsumed):
                external29_driver.boundary(adapter, observer, "PREFLIGHT", run)


if __name__ == "__main__":
    unittest.main(verbosity=2)
