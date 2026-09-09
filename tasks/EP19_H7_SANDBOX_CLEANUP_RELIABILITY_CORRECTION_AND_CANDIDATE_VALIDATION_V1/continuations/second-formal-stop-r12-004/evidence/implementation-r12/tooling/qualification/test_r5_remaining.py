"""Source-bound controls for the residual r5 failure-transition findings."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parents[1]
TARGET = Path(os.environ.get("EP19_TEST_EXECUTOR_ROOT", HERE / "executor")).absolute()
TOOLING = Path(os.environ.get("EP19_TEST_TOOLING_ROOT", HERE)).absolute()
sys.path.insert(0, str(TARGET))

import external29_driver
import native_observe


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def flattened(error):
    rows = []
    pending = [error]
    while pending:
        item = pending.pop(0)
        rows.append(type(item).__name__ + ":" + str(item))
        pending.extend(getattr(item, "exceptions", ()))
    return rows


class R5FailureTransitionControls(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT")
        self.temp = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def actual_runner(self):
        execution = types.ModuleType("execution")
        execution.CONTROL = TOOLING / "candidate-inputs-v3"
        execution.PARENT = "p"
        execution.D = TOOLING
        execution.O = TOOLING
        execution.H = TARGET
        execution.BASE = "b"
        execution.SHA = "s"
        execution.TREE = "t"
        execution.CONFIG = {"owner": str(self.base / "owner")}
        execution.CLONE_SOURCE = self.base
        execution.HISTORICAL_D = TOOLING
        execution.verify_object_source = lambda *a, **k: True
        execution.exact = lambda *a, **k: True
        execution.git = lambda *a, **k: b""
        execution.environment = lambda *a, **k: {}
        execution.frontend_sandbox = lambda argv, *a, **k: argv
        execution.formal_sandbox = lambda argv, *a, **k: argv
        coverage = types.ModuleType("coverage")
        coverage.digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        coverage.put = lambda path, value: dump(path, value)
        coverage.seal = lambda paths: {str(Path(p)): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                                       for p in paths}
        coverage.check_seal = lambda *_a, **_k: True
        coverage.watch_args = lambda *_a, **_k: {}
        name = "r5_fixture_runner_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "runner.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution, "coverage": coverage}):
            spec.loader.exec_module(module)
        return module

    def invoke_formal_cleanup_failure(self, *, observer_failure=False):
        run = self.base / "formal-run"
        run.mkdir()
        files = {}
        for name in ("binding", "review", "applicability", "private-map", "private-inventory"):
            path = self.base / (name + ".json")
            dump(path, {"name": name})
            files[name] = path
        dump(files["review"], {"implementation_review": "PASS",
                               "independent_final_acceptance": "PENDING"})
        digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        config = {"run_id": "candidate-formal-002",
                  "applicability": str(files["applicability"]),
                  "applicability_sha256": digest(files["applicability"]),
                  "private_map": str(files["private-map"]),
                  "private_map_sha256": digest(files["private-map"]),
                  "private_inventory": str(files["private-inventory"]),
                  "private_inventory_sha256": digest(files["private-inventory"]),
                  "owner": str(files["review"]), "dependency": str(files["binding"]),
                  "qualification": str(files["binding"]),
                  "adapter_qualification": str(files["binding"]),
                  "candidate": "s", "tree": "t", "owner_sha256": "o",
                  "matrix_sha256": "m"}

        class Runner:
            SHA = "s"
            TREE = "t"

            @staticmethod
            def runpath(_name): return run

            @staticmethod
            def put(path, value): dump(path, value)

        class Sequence:
            verify = staticmethod(lambda *_a, **_k: True)

        class Adapter:
            failed = False
            failure_path = run / "BOOKKEEPING_FAILURE.json"

            def __init__(self, *_a, **_k): pass

            def fail(self, *_a, **_k): self.failed = True

        class Observer:
            closed = False

            def __init__(self, *_a, **_k): pass

            def bind_policy(self, *_a): pass

            def close(self):
                self.closed = True
                if observer_failure: raise OSError("second cleanup failed")

        observer = Observer()

        class Continuous:
            closed = False

            def close(self):
                self.closed = True
                raise OSError("first cleanup failed")

        continuous = Continuous()
        observe_module = __import__("observe")
        policy_module = __import__("policy_builder")
        adapter_module = __import__("executor_adapter")
        args = SimpleNamespace(binding=files["binding"], binding_sha256=digest(files["binding"]),
                               run_id="candidate-formal-002", review=files["review"],
                               applicability=files["applicability"], private_map=files["private-map"],
                               private_inventory=files["private-inventory"])
        patches = (
            patch.object(external29_driver, "verify_required_runtime_files", return_value=True),
            patch.object(external29_driver, "modules", return_value=(config, object(), Runner, Sequence)),
            patch.object(external29_driver, "consume_formal", return_value={"attempt_id": "a"}),
            patch.object(external29_driver, "observer_seed", return_value={}),
            patch.object(external29_driver, "strict_baseline", return_value=({}, {}, continuous)),
            patch.object(external29_driver, "engineering_preflight",
                         side_effect=ValueError("original formal failure")),
            patch.object(observe_module, "BoundaryObserver", return_value=observer),
            patch.object(policy_module, "build", return_value={}),
            patch.object(policy_module, "write_private", side_effect=lambda path, value: dump(path, value)),
            patch.object(adapter_module, "RunAdapter", Adapter),
        )
        for item in patches: item.start()
        try:
            try:
                external29_driver.formal(args)
            except BaseException as error:
                return error, observer, continuous
            self.fail("cleanup failure was normalized into success")
        finally:
            for item in reversed(patches): item.stop()

    def test_formal_cleanup_attempts_observer_after_continuous_close_failure(self):
        error, observer, continuous = self.invoke_formal_cleanup_failure()
        self.assertTrue(continuous.closed)
        self.assertTrue(observer.closed, flattened(error))

    def test_formal_cleanup_retains_original_and_cleanup_causes(self):
        error, observer, _continuous = self.invoke_formal_cleanup_failure(observer_failure=True)
        messages = flattened(error)
        self.assertTrue(observer.closed)
        self.assertTrue(any("original formal failure" in row for row in messages), messages)
        self.assertTrue(any("first cleanup failed" in row for row in messages), messages)
        self.assertTrue(any("second cleanup failed" in row for row in messages), messages)

    def test_watch_constructor_cleanup_failure_preserves_original_cause(self):
        protected = self.base / "constructor-protected"
        protected.write_text("stable\n")
        real_close = native_observe.os.close

        def close_then_fail(fd):
            real_close(fd)
            raise OSError("constructor fd cleanup failed")

        with patch.object(native_observe.Watch, "add", side_effect=ValueError("constructor watch add failed")), \
             patch.object(native_observe.os, "close", side_effect=close_then_fail):
            with self.assertRaises(BaseExceptionGroup) as caught:
                native_observe.Watch(
                    protected=[protected], repositories=[], metadata_roots=[], allowed=[self.base],
                    enumeration_roots=[], pruned_roots=[], expected_missing=[], frozen_roots=[])
        messages = flattened(caught.exception)
        self.assertTrue(any("constructor watch add failed" in row for row in messages), messages)
        self.assertTrue(any("constructor fd cleanup failed" in row for row in messages), messages)

    def test_native_observer_exception_retains_executed_child_and_compound_causes(self):
        protected = self.base / "protected"
        protected.write_text("stable\n")
        log = self.base / "native.log"
        real_stream = __import__("durability").exclusive_stream
        real_close = native_observe.Watch.close

        @contextmanager
        def fail_after_stream(*args, **kwargs):
            with real_stream(*args, **kwargs) as stream:
                yield stream
            raise OSError("native log fsync failure")

        def close_then_fail(watch):
            real_close(watch)
            raise OSError("native watcher cleanup failure")

        with patch("durability.exclusive_stream", fail_after_stream), \
             patch.object(native_observe.Watch, "close", close_then_fail):
            with self.assertRaises(BaseException) as caught:
                native_observe.run(
                    [sys.executable, "-B", "-c", "pass"], self.base, log,
                    protected=[protected], repositories=[], metadata_roots=[], allowed=[self.base],
                    enumeration_roots=[], pruned_roots=[], expected_missing=[], frozen_roots=[], timeout=2)
        receipt = getattr(caught.exception, "native_observe_receipt", None)
        self.assertIsInstance(receipt, dict, flattened(caught.exception))
        self.assertTrue(receipt["failure_dimensions"]["native_invocation"])
        self.assertEqual(receipt["native_exit"], 0)
        self.assertTrue(receipt["failure_dimensions"]["evidence_persistence_failure"])
        self.assertTrue(receipt["failure_dimensions"]["cleanup_failure"])
        causes = " ".join(row["reason"] for row in receipt["causal_errors"])
        self.assertIn("native log fsync failure", causes)
        self.assertIn("native watcher cleanup failure", causes)

    def run_gate_parser_error(self, error):
        runner = self.actual_runner()
        run = self.base / ("parser-run-" + str(len(list(self.base.iterdir()))))
        repo = self.base / ("repo-" + str(len(list(self.base.iterdir()))))
        repo.mkdir();(run / "runtime/gates").mkdir(parents=True)
        command = [sys.executable, "-B", "-c", "pass"]
        matrix = {"gates": {"FIXTURE": {"repository": str(repo), "dependencies": [],
                  "command": command, "authoritative_command": command, "cwd": str(repo),
                  "timeout_seconds": 2, "output_bindings": {"required_files": []}}}}
        observed = {"result": "PASS_BOUNDED_OBSERVATION", "native_exit": 0, "wrapper_exit": 0,
                    "child_pid": 123, "failure_dimensions": {"native_invocation": True,
                    "native_exit": 0, "native_command_exit_failure": False,
                    "product_assertion_failure": False, "observer_preservation_failure": False,
                    "workload_timeout_or_cancellation": False, "wrapper_or_environment_failure": False,
                    "evidence_persistence_failure": False, "cleanup_failure": False}}
        with patch.object(runner, "check_execution_seal", return_value=True), \
             patch.object(runner, "repos", return_value=[]), \
             patch.object(runner, "compare_baseline", return_value={}), \
             patch.object(runner.artifacts, "producer_inputs", return_value={}), \
             patch.object(runner.freshness, "preserve_cleanup", return_value=[]), \
             patch.object(runner.freshness, "dependency_inputs", return_value={}), \
             patch.object(runner, "packaging_receipts", return_value=[]), \
             patch.object(runner.observe, "run", return_value=observed), \
             patch.object(runner.parsers, "parse", side_effect=error):
            return runner.run_gate("FIXTURE", matrix, run, {"allowed": []}, {}, {})

    def test_runner_parser_evidence_exception_is_not_product_failure(self):
        result = self.run_gate_parser_error(OSError("parser evidence fsync failure"))
        self.assertTrue(result["failure_dimensions"]["evidence_persistence_failure"])
        self.assertFalse(result["failure_dimensions"]["product_assertion_failure"])

    def test_runner_product_assertion_remains_separate(self):
        result = self.run_gate_parser_error(RuntimeError("actual assertion mismatch"))
        self.assertTrue(result["failure_dimensions"]["product_assertion_failure"])
        self.assertFalse(result["failure_dimensions"]["evidence_persistence_failure"])

    def test_vite_helper_nonzero_is_process_not_product_failure(self):
        execution = types.ModuleType("execution")
        execution.H = TARGET
        name = "r5_fixture_vite_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "vite_closure.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        root = self.base / "built";root.mkdir()
        with self.assertRaises(Exception) as caught:
            module.validate(root, "/", self.base / "missing-parser-tools", self.base / "closure.json")
        dimensions = getattr(caught.exception, "failure_dimensions", {})
        self.assertTrue(dimensions.get("parser_helper_process_failure"), flattened(caught.exception))
        self.assertFalse(dimensions.get("product_assertion_failure", False))

    def load_vite_helper(self):
        execution = types.ModuleType("execution")
        execution.H = TARGET
        name = "r5_fixture_vite_boundary_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "vite_closure.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        return module

    def test_vite_log_fsync_failure_is_evidence_not_product(self):
        module = self.load_vite_helper()

        @contextmanager
        def fail_log(*_args, **_kwargs):
            raise OSError("vite log fsync failure")
            yield

        root = self.base / "vite-built";root.mkdir()
        with patch("durability.exclusive_stream", fail_log):
            with self.assertRaises(Exception) as caught:
                module.validate(root, "/", self.base / "parser-tools", self.base / "vite-output.json")
        dimensions = getattr(caught.exception, "failure_dimensions", {})
        self.assertTrue(dimensions.get("evidence_persistence_failure"), flattened(caught.exception))
        self.assertFalse(dimensions.get("product_assertion_failure", False))

    def test_vite_launch_failure_is_environment_not_product(self):
        module = self.load_vite_helper()
        root = self.base / "vite-launch-built";root.mkdir()
        with patch.object(module.subprocess, "run", side_effect=FileNotFoundError("node missing")):
            with self.assertRaises(Exception) as caught:
                module.validate(root, "/", self.base / "parser-tools", self.base / "vite-launch.json")
        dimensions = getattr(caught.exception, "failure_dimensions", {})
        self.assertTrue(dimensions.get("wrapper_or_environment_failure"), flattened(caught.exception))
        self.assertFalse(dimensions.get("product_assertion_failure", False))

    def test_driver_marker_failure_preserves_gate_primary_and_secondary(self):
        run = self.base / "graph";run.mkdir()
        dump(run / "bindings.json", {"order": ["FIXTURE"], "gates": {"FIXTURE": {}}})

        class Runner:
            SHA = "s";TREE = "t"

            @staticmethod
            def run_gate(*_args):
                return {"gate": "FIXTURE", "result": "FAIL", "reason": "original gate rejection",
                        "native_exit": 7, "child_pid": 321, "failure_dimensions": {
                        "native_invocation": True, "native_exit": 7,
                        "native_command_exit_failure": True, "product_assertion_failure": False,
                        "observer_preservation_failure": False,
                        "workload_timeout_or_cancellation": False,
                        "wrapper_or_environment_failure": False,
                        "evidence_persistence_failure": False, "cleanup_failure": False}}

        class Adapter:
            failed = False

            def fail(self, *_args):
                self.failed = True
                raise OSError("failure marker persistence failed")

        adapter = Adapter()
        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", return_value={}):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, {}, adapter, object(), Runner, object(), None)
        result = results["FIXTURE"]
        self.assertTrue(stopped)
        self.assertEqual(result["reason"], "original gate rejection")
        self.assertEqual(result["native_exit"], 7)
        self.assertTrue(result["failure_dimensions"]["evidence_persistence_failure"])
        self.assertIn("failure marker persistence failed",
                      " ".join(row["reason"] for row in result["secondary_failures"]))

    def test_final_receipt_failure_reaches_driver_with_prior_native_and_parser_facts(self):
        runner = self.actual_runner()
        run = self.base / "receipt-graph";run.mkdir()
        repo = self.base / "receipt-repo";repo.mkdir()
        dump(run / "bindings.json", {"order": ["FIXTURE"], "gates": {"FIXTURE": {}}})
        command = [sys.executable, "-B", "-c", "pass"]
        matrix = {"gates": {"FIXTURE": {"repository": str(repo), "dependencies": [],
                  "command": command, "authoritative_command": command, "cwd": str(repo),
                  "timeout_seconds": 2, "output_bindings": {"required_files": []}}}}
        observed = {"result": "PASS_BOUNDED_OBSERVATION", "native_exit": 0, "wrapper_exit": 0,
                    "child_pid": 789, "failure_dimensions": {"native_invocation": True,
                    "native_exit": 0, "native_command_exit_failure": False,
                    "product_assertion_failure": False, "observer_preservation_failure": False,
                    "workload_timeout_or_cancellation": False, "wrapper_or_environment_failure": False,
                    "evidence_persistence_failure": False, "cleanup_failure": False}}
        ordinary_put = runner.put

        def fail_receipt(path, value):
            if Path(path).name == "receipt.json": raise OSError("final receipt fsync failure")
            return ordinary_put(path, value)

        class RunnerProxy:
            SHA = "s";TREE = "t"

            @staticmethod
            def run_gate(*_args): return runner.run_gate("FIXTURE", matrix, run, {"allowed": []}, {}, {})

        class Adapter:
            failed = False

            def _latch_exception(self, *_args): self.failed = True

        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", return_value={}), \
             patch.object(runner, "check_execution_seal", return_value=True), \
             patch.object(runner, "repos", return_value=[]), \
             patch.object(runner, "compare_baseline", return_value={}), \
             patch.object(runner.artifacts, "producer_inputs", return_value={}), \
             patch.object(runner.freshness, "preserve_cleanup", return_value=[]), \
             patch.object(runner.freshness, "dependency_inputs", return_value={}), \
             patch.object(runner, "packaging_receipts", return_value=[]), \
             patch.object(runner.observe, "run", return_value=observed), \
             patch.object(runner.parsers, "parse", side_effect=RuntimeError("parser assertion failed")), \
             patch.object(runner, "put", side_effect=fail_receipt):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, {}, Adapter(), object(), RunnerProxy, object(), None)
        result = results["FIXTURE"]
        self.assertTrue(stopped)
        self.assertEqual(result["native_exit"], 0)
        self.assertTrue(result["failure_dimensions"]["product_assertion_failure"])
        self.assertTrue(result["failure_dimensions"]["evidence_persistence_failure"])
        self.assertIn("parser assertion failed", result["reason"])
        self.assertIn("final receipt fsync failure", result["receipt_persistence_error"])

    def postseal_failure(self, *, supplement_failure=False):
        runner = self.actual_runner()
        run = self.base / ("postseal-run-" + str(len(list(self.base.iterdir()))))
        repo = self.base / ("postseal-repo-" + str(len(list(self.base.iterdir()))))
        repo.mkdir();(run / "runtime/gates").mkdir(parents=True)
        output = run / "runtime/outputs/result.bin"
        command = [sys.executable, "-B", "-c", "pass"]
        matrix = {"gates": {"FIXTURE": {"repository": str(repo), "dependencies": [],
                  "command": command, "authoritative_command": command, "cwd": str(repo),
                  "timeout_seconds": 2, "output_bindings": {"required_files": [str(output)]}}}}
        observed = {"result": "PASS_BOUNDED_OBSERVATION", "native_exit": 0, "wrapper_exit": 0,
                    "child_pid": 456, "failure_dimensions": {"native_invocation": True,
                    "native_exit": 0, "native_command_exit_failure": False,
                    "product_assertion_failure": False, "observer_preservation_failure": False,
                    "workload_timeout_or_cancellation": False, "wrapper_or_environment_failure": False,
                    "evidence_persistence_failure": False, "cleanup_failure": False}}

        def execute(*_args, **_kwargs):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"accepted output")
            return observed

        ordinary_digest = runner.coverage.digest

        def fail_postseal(path):
            path = Path(path)
            if "sealed" in path.parts and path.name.isdigit():
                raise OSError("controlled postseal validation failure")
            return ordinary_digest(path)

        real_exclusive_directory = runner.durability.exclusive_directory

        def maybe_fail_supplement(path, *args, **kwargs):
            if Path(path).name == "failure-supplement":
                raise OSError("controlled supplement persistence failure")
            return real_exclusive_directory(path, *args, **kwargs)

        with patch.object(runner, "check_execution_seal", return_value=True), \
             patch.object(runner, "repos", return_value=[]), \
             patch.object(runner, "compare_baseline", return_value={}), \
             patch.object(runner.artifacts, "producer_inputs", return_value={}), \
             patch.object(runner.freshness, "preserve_cleanup", return_value=[]), \
             patch.object(runner.freshness, "dependency_inputs", return_value={}), \
             patch.object(runner, "packaging_receipts", return_value=[]), \
             patch.object(runner.observe, "run", side_effect=execute), \
             patch.object(runner.parsers, "parse", return_value={"result": "PASS"}), \
             patch.object(runner.coverage, "digest", side_effect=fail_postseal), \
             patch.object(runner.durability, "exclusive_directory",
                          side_effect=maybe_fail_supplement if supplement_failure else real_exclusive_directory):
            result = runner.run_gate("FIXTURE", matrix, run, {"allowed": []}, {}, {})
        return runner, run, result

    def test_postseal_failure_uses_bound_immutable_supplement(self):
        runner, run, result = self.postseal_failure()
        gate = run / "runtime/gates/FIXTURE"
        self.assertEqual(result["result"], "FAIL")
        self.assertIn("controlled postseal validation failure", result["reason"])
        self.assertTrue(result["failure_evidence_sealed"])
        self.assertEqual(result["failure_evidence_kind"], "IMMUTABLE_FAILURE_SUPPLEMENT")
        self.assertTrue(runner.artifacts.verify(result["artifacts"], gate, run.name, "FIXTURE"))
        self.assertTrue(runner.artifacts.verify_failure_supplement(
            result["failure_supplement"], gate, run.name, "FIXTURE", result["artifacts"]))

    def test_supplement_persistence_failure_stays_secondary_and_never_success(self):
        _runner, _run, result = self.postseal_failure(supplement_failure=True)
        self.assertEqual(result["result"], "FAIL")
        self.assertIn("controlled postseal validation failure", result["reason"])
        self.assertFalse(result["failure_evidence_sealed"])
        self.assertIn("controlled supplement persistence failure", result["failure_supplement_error"])
        self.assertTrue(result["failure_dimensions"]["evidence_persistence_failure"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
