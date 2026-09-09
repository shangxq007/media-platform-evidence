"""Focused r3 predecessor controls for the six remaining production-path findings."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "executor"
sys.path.insert(0, str(EXECUTOR))

import bookkeeping_v3 as bk
import dependency_contract
import executor_adapter
import external29_driver
import native_observe
import observe


def dump(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class RemainingProductionPathControls(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT")
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.skills.mkdir(mode=0o700)
        self.package = self.skills / "alpha"
        self.package.mkdir()
        (self.package / "SKILL.md").write_text("fixture\n")
        dump(self.skills / bk.USAGE_NAME,
             {"alpha": {"view_count": 1, "use_count": 1,
                         "last_viewed_at": None, "last_used_at": None}})
        os.chmod(self.skills / bk.USAGE_NAME, 0o600)
        (self.skills / bk.LOCK_NAME).touch(mode=0o644)
        (self.skills / bk.LEDGER_NAME).write_bytes(b"")
        os.chmod(self.skills / bk.LEDGER_NAME, 0o600)
        self.policy = bk.create_policy(self.skills, owner_sha256="4" * 64,
                                       dependency_sha256="5" * 64,
                                       eligible_names=["alpha"], fixture=True)

    def _actual_runner(self):
        """Load the real runner.py bytes with only its environment constants isolated."""
        execution = types.ModuleType("execution")
        execution.CONTROL = ROOT / "candidate-inputs-v3"
        execution.PARENT = "p"
        execution.D = ROOT
        execution.O = ROOT
        execution.H = EXECUTOR
        execution.BASE = "b"
        execution.SHA = "s"
        execution.TREE = "t"
        execution.CONFIG = {"owner": str(self.base / "owner")}
        execution.CLONE_SOURCE = self.base
        execution.HISTORICAL_D = ROOT
        execution.verify_object_source = lambda *a, **k: True
        execution.exact = lambda *a, **k: True
        execution.git = lambda *a, **k: b""
        execution.environment = lambda *a, **k: {}
        execution.frontend_sandbox = lambda argv, *a, **k: argv
        execution.formal_sandbox = lambda argv, *a, **k: argv
        name = "r3_fixture_runner_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, EXECUTOR / "runner.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        return module

    def _actual_coverage(self):
        execution = types.ModuleType("execution")
        execution.CONTROL = ROOT / "candidate-inputs-v3"
        execution.PARENT = "p"
        execution.D = ROOT
        execution.O = ROOT
        execution.H = EXECUTOR
        execution.git = lambda *a, **k: b""
        name = "r3_fixture_coverage_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, EXECUTOR / "coverage.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        return module

    def test_ar001_event_queued_during_last_identity_check_is_rejected_before_endpoint(self):
        run = self.base / "run"
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
            original = continuous.validate_directory_identities

            def mutate_in_last_identity_loop():
                memory.write_text("mutated in final identity validation\n")
                return original()

            with patch.object(continuous, "validate_directory_identities",
                              side_effect=mutate_in_last_identity_loop):
                with self.assertRaises(Exception):
                    external29_driver.boundary(adapter, observer, "SEAL", run,
                                               continuous=continuous,
                                               finalize_observation=True)
        receipts = [json.loads(path.read_text()) for path in
                    (run / "runtime/bookkeeping-decisions").glob("*.json")]
        seal = next(row for row in receipts if row["phase"] == "SEAL")
        final = seal["final_observation_boundary"]
        self.assertEqual(seal["decision"], "REJECT", seal)
        self.assertTrue(final["continuous_events"], final)
        self.assertEqual(final["observation_ended_monotonic_ns"],
                         final["shutdown_started_monotonic_ns"])

    def test_ar002_actual_observer_seed_rebind_accepts_legal_temp_rename(self):
        applicability = self.base / "applicability.json"
        dump(applicability, {"eligible_packages": [{"skill": "alpha", "eligible": True,
                                                     "errors": [],
                                                     "package_root": str(self.package)}]})
        with patch.object(bk, "PRODUCTION_ROOT", self.skills):
            seed = external29_driver.observer_seed({}, applicability)
        with observe.BoundaryObserver(seed) as observer:
            observer.bind_policy(self.policy)
            temp = self.skills / ".usage_abc12_3z.tmp"
            temp.write_bytes((self.skills / bk.USAGE_NAME).read_bytes())
            os.chmod(temp, 0o600)
            observer.drain()
            os.replace(temp, self.skills / bk.USAGE_NAME)
            events, errors = observer.boundary_events()
        result = __import__("boundary").Engine(self.policy).check(
            "GATE", events=events, coverage_errors=errors)
        self.assertEqual(result["decision"], "PASS", result)

    def test_ar007_r2_declarative_graph_is_rejected_for_missing_actual_vite_edge(self):
        value = json.loads((ROOT.parents[1] / "writer-evidence-r2" /
                            "DEPENDENCY_BINDING.r2.candidate.json").read_text())
        with self.assertRaisesRegex(RuntimeError, "ACTUAL_HELPER_EDGE_CLOSURE"):
            dependency_contract.validate(
                value, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")

    def test_ar007_loader_rejects_extra_qualification_flag_with_other_bindings_valid(self):
        coverage = self._actual_coverage()
        source = ROOT.parents[1] / "writer-evidence-r2" / "qualification-003"
        out = self.base / "qualification"
        out.mkdir()
        log = out / "QUALIFICATION.native.log"
        result_path = out / "RESULT.json"
        process_path = out / "PROCESS.json"
        shutil.copyfile(source / "QUALIFICATION.native.log", log)
        shutil.copyfile(source / "RESULT.json", result_path)
        process = json.loads((source / "PROCESS.json").read_text())
        fixture_root = self.base / "fixture-root"
        fixture_root.mkdir()
        process["argv"] = [sys.executable, "-B", str((ROOT / "qualification" /
                              "build_integration_qualification.py").absolute()),
                           "--output", str(out.absolute()), "--fixture-root",
                           str(fixture_root.absolute()), "--extra"]
        process["raw_log"] = str(log.absolute())
        process["log_sha256"] = hashlib.sha256(log.read_bytes()).hexdigest()
        result_doc = json.loads(result_path.read_text())
        current_sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(ROOT.rglob("*")) if p.is_file() and
                           "__pycache__" not in p.parts and
                           "outputs" not in p.relative_to(ROOT).parts}
        process.update(wrapper_exit=0, pid=os.getpid(), cwd=str(ROOT.parents[1]),
                       source_binding_before=current_sources,
                       source_binding_after=current_sources,
                       source_binding_stable=True,
                       result_receipt=str(result_path.absolute()),
                       result_sha256=hashlib.sha256(result_path.read_bytes()).hexdigest(),
                       control_ids=result_doc["expected_controls"],
                       control_statuses={row["id"]: row["actual"]
                                         for row in result_doc["controls"]})
        dump(process_path, process)
        adapter = ROOT / "adapter71-qualification.reused.json"
        formal = ROOT / "candidate-qualification-v3.reused.json"
        q = json.loads((source / "QUALIFICATION.json").read_text())
        q.update(source_binding=current_sources,
                 source_binding_before_launch=current_sources,
                 source_binding_after_execution=current_sources,
                 source_binding_stable=True,
                 raw_log=str(log.absolute()), process_receipt=str(process_path.absolute()),
                 result_receipt=str(result_path.absolute()), fixture_root=str(fixture_root.absolute()),
                 adapter71_qualification=str(adapter.absolute()), formal_qualification=str(formal.absolute()))
        q["dependencies"] = {str(p.absolute()): hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (log, process_path, result_path, adapter, formal)}
        qpath = self.base / "qualification.json"
        dump(qpath, q)
        import qualification_contract
        with patch.object(qualification_contract, "REQUIRED_AFFECTED_CONTROLS",
                          frozenset(q["mandatory_affected_controls"])):
            with self.assertRaisesRegex(RuntimeError, "INTEGRATION_PROCESS_ARGV_BINDING_REJECT"):
                coverage.qualification_inputs(qpath)

    def test_ar008_actual_run_gate_caught_failure_latches_before_post_command_boundary(self):
        runner = self._actual_runner()
        run = self.base / "gate-run"
        (run / "runtime/gates").mkdir(parents=True)
        dump(run / "bindings.json", {"order": ["FIXTURE"], "gates": {
            "FIXTURE": {"repository": str(self.base), "dependencies": []}}})
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        calls = []

        def boundary_spy(*args, **kwargs):
            calls.append(args[2])
            if adapter.failed:
                raise executor_adapter.NamespaceConsumed("latched")

        with patch.object(runner, "check_execution_seal",
                          side_effect=OSError("fixture gate integrity acquisition")), \
             patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", side_effect=boundary_spy):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, self.policy, adapter, object(), runner, object(), None)
        self.assertTrue(stopped)
        self.assertTrue(adapter.failed)
        self.assertEqual(calls, ["COMMAND"])
        self.assertEqual(results["FIXTURE"]["failure_class"],
                         "WRAPPER_OR_ENVIRONMENT_FAILURE")
        self.assertTrue(results["FIXTURE"]["failure_dimensions"]
                        ["wrapper_or_environment_failure"])

    def test_ar009_actual_gate_and_sealed_copy_publish_parent_chain_durably(self):
        runner = self._actual_runner()
        run = self.base / "durable-run"
        gates = run / "runtime/gates"
        gates.mkdir(parents=True)
        matrix = {"gates": {"FIXTURE": {"repository": str(self.base),
                                          "dependencies": []}}}
        seen = []
        real_fsync_directory = __import__("durability").fsync_directory

        def recording(path):
            seen.append(str(Path(path)))
            return real_fsync_directory(path)

        with patch.object(runner, "check_execution_seal", side_effect=OSError("fixture")), \
             patch("durability.fsync_directory", side_effect=recording):
            result = runner.run_gate("FIXTURE", matrix, run, {}, {}, {})
        gate = gates / "FIXTURE"
        self.assertTrue(result["failure_evidence_sealed"])
        source = self.base / "artifact"
        source.write_bytes(b"immutable")
        extra_gate = gates / "EXTRA"
        extra_gate.mkdir()
        with patch("durability.fsync_directory", side_effect=recording):
            runner.artifacts.seal([source], extra_gate, run.name, "EXTRA")
        self.assertIn(str(gates), seen)
        self.assertIn(str(extra_gate / "sealed"), seen)
        self.assertIn(str(extra_gate), seen)

    def test_ar010_actual_native_final_stat_is_guarded_and_resources_close(self):
        protected = self.base / "protected"
        protected.write_text("stable\n")
        log = self.base / "native.log"
        real_stat = native_observe.os.stat

        def delayed_final(path, *args, **kwargs):
            if (Path(path) == self.base and any(
                    frame.filename.endswith("native_observe.py") and
                    frame.name == "validate_directory_identities"
                    for frame in traceback.extract_stack())):
                time.sleep(0.20)
            return real_stat(path, *args, **kwargs)

        old = bk.LIMITS["capture_total_seconds_per_boundary_max"]
        bk.LIMITS["capture_total_seconds_per_boundary_max"] = 0.03
        started = time.monotonic()
        try:
            with patch.object(native_observe.os, "stat", side_effect=delayed_final):
                result = native_observe.run(
                    [sys.executable, "-B", "-c", "pass"], self.base, log,
                    protected=[protected], repositories=[], metadata_roots=[], allowed=[self.base],
                    enumeration_roots=[], pruned_roots=[], expected_missing=[], frozen_roots=[])
        finally:
            bk.LIMITS["capture_total_seconds_per_boundary_max"] = old
        self.assertLess(time.monotonic() - started, 0.15)
        self.assertEqual(result["result"], "REJECT")
        self.assertIn("DIRECTORY_IDENTITY_ACQUISITION_TIME_LIMIT_EXCEEDED",
                      result["observation_errors"])

    def test_ar010_boundary_observer_inventory_failure_closes_constructor_fd(self):
        before = set(os.listdir("/proc/self/fd"))
        try:
            with patch("preservation.directory_inventory",
                       side_effect=OSError("fixture inventory failure")):
                with self.assertRaisesRegex(OSError, "fixture inventory failure"):
                    observe.BoundaryObserver(self.policy)
            after = set(os.listdir("/proc/self/fd"))
            self.assertEqual(after, before)
        finally:
            for fd in set(os.listdir("/proc/self/fd")) - before:
                try:
                    os.close(int(fd))
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
