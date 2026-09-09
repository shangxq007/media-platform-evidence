"""Source-bound controls for the four r4 production-path findings."""
from __future__ import annotations

from pathlib import Path
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
DEPENDENCY = Path(os.environ.get(
    "EP19_TEST_DEPENDENCY_BINDING",
    HERE.parents[1] / "writer-evidence-r6/DEPENDENCY_BINDING.r6.candidate-003.json")).absolute()
sys.path.insert(0, str(TARGET))

import dependency_contract
import external29_driver
import native_observe


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


class R4ProductionPathControls(unittest.TestCase):
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
        name = "r4_fixture_runner_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "runner.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        return module

    def actual_freshness(self):
        coverage = types.ModuleType("coverage")
        coverage.digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        coverage.put = lambda path, value: dump(Path(path), value)
        execution = types.ModuleType("execution")
        execution.SHA = "s"
        execution.TREE = "t"
        execution.git = lambda *a, **k: b""
        name = "r4_fixture_freshness_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "freshness.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"coverage": coverage, "execution": execution}):
            spec.loader.exec_module(module)
        return module

    def test_ar010_strict_baseline_failed_handoff_closes_watch_and_preserves_cleanup_failure(self):
        protected = self.base / "protected"
        protected.write_text("stable\n")
        review = self.base / "review.json"
        binding = self.base / "binding.json"
        dump(review, {})
        dump(binding, {})
        run = self.base / "run"
        run.mkdir()

        class Coverage:
            @staticmethod
            def derive(_run, _extras):
                return {"protected": [str(protected)], "expected_missing": []}

            @staticmethod
            def watch_args(scope):
                return {"protected": scope["protected"], "repositories": [],
                        "metadata_roots": [], "allowed": [str(run)],
                        "cross_lane": [], "shared_git": None,
                        "enumeration_roots": [], "pruned_roots": [],
                        "expected_missing": [], "frozen_roots": []}

        class Runner:
            SHA = "s"
            TREE = "t"
            EXECUTOR_IDENTITY = binding

            @staticmethod
            def put(path, value):
                dump(Path(path), value)

            @staticmethod
            def identities(_run):
                return {"result": "PASS"}

        before = set(os.listdir("/proc/self/fd"))
        config = {"owner": str(review), "dependency": str(binding),
                  "qualification": str(binding),
                  "adapter_qualification": str(binding)}
        try:
            with patch.object(external29_driver, "boundary",
                              side_effect=OSError("injected boundary persistence failure")):
                with self.assertRaisesRegex(OSError, "injected boundary persistence failure"):
                    external29_driver.strict_baseline(
                        run, {}, object(), object(), config, Coverage, Runner, object(),
                        review, binding)
            self.assertEqual(set(os.listdir("/proc/self/fd")), before)
        finally:
            for fd in set(os.listdir("/proc/self/fd")) - before:
                try:
                    os.close(int(fd))
                except OSError:
                    pass

        real_close = native_observe.Watch.close

        def close_then_fail(watch):
            real_close(watch)
            raise OSError("injected watch cleanup failure")

        with patch.object(external29_driver, "boundary",
                          side_effect=ValueError("original acquisition failure")), \
             patch.object(native_observe.Watch, "close", close_then_fail):
            with self.assertRaises(BaseExceptionGroup) as caught:
                external29_driver.strict_baseline(
                    run, {}, object(), object(), config, Coverage, Runner, object(),
                    review, binding)
        messages = [str(item) for item in caught.exception.exceptions]
        self.assertTrue(any("original acquisition failure" in item for item in messages), messages)
        self.assertTrue(any("watch cleanup failure" in item for item in messages), messages)

    def test_ar007_current_finite_vite_parser_graph_is_complete_and_missing_edges_reject(self):
        value = json.loads(DEPENDENCY.read_text())
        matrix = TOOLING / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json"
        self.assertTrue(dependency_contract.validate(value, matrix_path=matrix))
        scope = value["actual_execution_scope"]
        required_nodes = {"parsers.py", "freshness.py", "vite_closure.py",
                          "vite_closure.mjs", "parser_tools.py"}
        self.assertTrue(required_nodes <= set(scope["source_nodes"]), scope["source_nodes"])
        edges = {(row["caller"], row["callee"], row["kind"]) for row in scope["edges"]}
        expected_edges = {
            ("runner.run_gate[FRONTEND_BUILD]", "freshness.require_fresh_outputs", "python-call"),
            ("freshness.require_fresh_outputs", "parsers.parse[FRONTEND_BUILD]", "parser-callback"),
            ("parsers.parse[FRONTEND_BUILD]", "vite_closure.validate", "python-call"),
            ("vite_closure.validate", "vite_closure.mjs", "mandatory-auxiliary-process"),
        }
        self.assertTrue(expected_edges <= edges, edges)
        graph = scope.get("parser_package_graph")
        self.assertIsInstance(graph, dict)
        self.assertEqual(set(graph["direct_packages"]),
                         {"acorn", "postcss", "postcss-value-parser", "parse5"})
        self.assertTrue(graph["nodes"])
        reachable = scope.get("reachable_local_graph")
        self.assertGreaterEqual(len(reachable["nodes"]), 30)
        self.assertIn("executor/external29_driver.py", reachable["nodes"])
        self.assertIn("executor/parsers.py", reachable["nodes"])
        malformed = json.loads(json.dumps(value))
        malformed["actual_execution_scope"]["source_nodes"].pop("vite_closure.py")
        with self.assertRaisesRegex(RuntimeError, "ACTUAL_EXECUTION_SOURCE_EDGE_CLOSURE"):
            dependency_contract.validate(malformed, matrix_path=matrix)
        malformed = json.loads(json.dumps(value))
        malformed["actual_execution_scope"]["edges"] = [
            row for row in malformed["actual_execution_scope"]["edges"]
            if row["callee"] != "vite_closure.mjs"]
        with self.assertRaisesRegex(RuntimeError, "ACTUAL_EXECUTION_SOURCE_EDGE_SEMANTICS"):
            dependency_contract.validate(malformed, matrix_path=matrix)

    def run_native_failure(self, *, protection=False, timeout=2):
        protected = self.base / ("protected-" + str(len(list(self.base.iterdir()))))
        protected.write_text("stable\n")
        log = self.base / (protected.name + ".log")
        if protection:
            script = ("import pathlib,time;time.sleep(.05);"
                      f"pathlib.Path({str(protected)!r}).write_text('changed\\n');time.sleep(10)")
        else:
            script = "import time;time.sleep(10)"
        return native_observe.run(
            [sys.executable, "-B", "-c", script], self.base, log,
            protected=[protected], repositories=[], metadata_roots=[], allowed=[self.base],
            enumeration_roots=[], pruned_roots=[], expected_missing=[], frozen_roots=[],
            timeout=timeout)

    def classify_through_actual_graph(self, receipt):
        run = self.base / ("graph-" + str(len(list(self.base.iterdir()))))
        run.mkdir()
        dump(run / "bindings.json", {"order": ["FIXTURE"], "gates": {"FIXTURE": {}}})

        class Runner:
            SHA = "s"
            TREE = "t"

            @staticmethod
            def run_gate(*_args):
                return {**receipt, "gate": "FIXTURE", "result": "FAIL",
                        "candidate": "s", "tree": "t"}

        class Adapter:
            failed = False

            def fail(self, _phase, result):
                self.failed = True
                self.result = result

        adapter = Adapter()
        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", return_value={}):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, {}, adapter, object(), Runner, object(), None)
        self.assertTrue(stopped)
        return results["FIXTURE"]

    def test_ar008_actual_outer_termination_retains_independent_protection_timeout_and_exit_causes(self):
        protection = self.classify_through_actual_graph(
            self.run_native_failure(protection=True, timeout=2))
        self.assertNotEqual(protection["native_exit"], 0)
        self.assertTrue(protection["failure_dimensions"]["observer_preservation_failure"])
        self.assertFalse(protection["failure_dimensions"]["product_assertion_failure"])
        self.assertIn("OBSERVER_PRESERVATION_FAILURE", protection["failure_classes"])
        self.assertNotIn("PRODUCT_ASSERTION_FAILURE", protection["failure_classes"])

        timeout = self.classify_through_actual_graph(
            self.run_native_failure(protection=False, timeout=.03))
        self.assertNotEqual(timeout["native_exit"], 0)
        self.assertTrue(timeout["failure_dimensions"]["workload_timeout_or_cancellation"])
        self.assertFalse(timeout["failure_dimensions"]["product_assertion_failure"])
        self.assertIn("WORKLOAD_TIMEOUT_OR_CANCELLATION", timeout["failure_classes"])

    def test_ar009_cleanup_preimage_is_durable_before_unlink_and_failed_gate_is_sealed(self):
        freshness = self.actual_freshness()
        source = self.base / "old-output"
        source.write_bytes(b"old output")
        destination = self.base / "gate" / "cleanup-preimages"
        durable_paths = []
        real_exclusive = __import__("durability").exclusive_bytes
        real_unlink = Path.unlink

        def record_exclusive(path, payload, *args, **kwargs):
            result = real_exclusive(path, payload, *args, **kwargs)
            durable_paths.append(Path(path))
            return result

        def guarded_unlink(path, *args, **kwargs):
            self.assertIn(destination / "0", durable_paths,
                          "source unlink preceded durable preimage publication")
            return real_unlink(path, *args, **kwargs)

        with patch("durability.exclusive_bytes", side_effect=record_exclusive), \
             patch.object(Path, "unlink", guarded_unlink):
            rows = freshness.preserve_cleanup(
                [source], destination, [self.base], self.base / "not-repository")
        self.assertEqual(rows[0]["sha256"], hashlib.sha256(b"old output").hexdigest())
        self.assertFalse(source.exists())

        runner = self.actual_runner()
        run = self.base / "failed-run"
        (run / "runtime/gates").mkdir(parents=True)
        matrix = {"gates": {"FIXTURE": {"repository": str(self.base),
                                          "dependencies": []}}}
        with patch.object(runner, "check_execution_seal",
                          side_effect=OSError("actual fixture acquisition failure")):
            result = runner.run_gate("FIXTURE", matrix, run, {}, {}, {})
        self.assertEqual(result["result"], "FAIL")
        self.assertTrue(result["failure_evidence_sealed"])
        self.assertTrue(result["artifacts"])
        self.assertTrue(runner.artifacts.verify(
            result["artifacts"], run / "runtime/gates/FIXTURE", run.name, "FIXTURE"))

    def test_ar009_actual_vite_failure_log_uses_durable_stream(self):
        execution = types.ModuleType("execution")
        execution.H = TARGET
        name = "r4_fixture_vite_" + self.base.name.replace("-", "_")
        spec = importlib.util.spec_from_file_location(name, TARGET / "vite_closure.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}):
            spec.loader.exec_module(module)
        output = self.base / "vite-result.json"
        root = self.base / "built"
        root.mkdir()
        seen = []
        real_sync = __import__("durability").fsync_directory

        def record(path):
            seen.append(Path(path))
            return real_sync(path)

        with patch("durability.fsync_directory", side_effect=record):
            with self.assertRaisesRegex(RuntimeError, "VITE_CLOSURE_REJECT"):
                module.validate(root, "/", self.base / "missing-parser-tools", output)
        log = Path(str(output) + ".native.log")
        self.assertTrue(log.is_file())
        self.assertIn(log.parent, seen)


if __name__ == "__main__":
    unittest.main(verbosity=2)
