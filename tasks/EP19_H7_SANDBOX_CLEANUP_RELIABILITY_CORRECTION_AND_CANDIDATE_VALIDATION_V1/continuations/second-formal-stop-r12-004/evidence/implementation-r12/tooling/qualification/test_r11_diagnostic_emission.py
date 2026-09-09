"""r11 actual-path controls for fallible gate diagnostic stderr emission."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = Path(os.environ.get("EP19_TEST_EXECUTOR_ROOT", ROOT / "executor"))
sys.path.insert(0, str(EXECUTOR))

import causal
import external29_driver
import executor_adapter


class NativeGateFailure(RuntimeError):
    pass


class DiagnosticStderrFailure(OSError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class FailingDiagnosticStream:
    def __init__(self, failure_point):
        self.failure_point = failure_point
        self.write_calls = 0
        self.flush_calls = 0
        self.error = None

    def write(self, value):
        self.write_calls += 1
        if self.failure_point == "write":
            self.error = DiagnosticStderrFailure(
                "r11 bounded diagnostic stderr write failure")
            raise self.error
        return len(value)

    def flush(self):
        self.flush_calls += 1
        if self.failure_point == "flush":
            self.error = DiagnosticStderrFailure(
                "r11 bounded diagnostic stderr flush failure")
            raise self.error


class R11ActualDiagnosticEmissionControls(unittest.TestCase):
    def setUp(self):
        fixture_root = Path(os.environ["EP19_QUALIFICATION_FIXTURE_ROOT"])
        self.temp = tempfile.TemporaryDirectory(dir=fixture_root)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def _formal_files(self):
        files = {}
        for name, value in (
            ("binding", {"fixture": True}),
            ("review", {"implementation_review": "PASS",
                        "independent_final_acceptance": "PENDING"}),
            ("applicability", {"fixture": True}),
            ("private-map", {"fixture": True}),
            ("private-inventory", {"fixture": True}),
        ):
            path = self.base / (name + ".json")
            dump(path, value)
            files[name] = path
        return files

    def _invoke_actual_formal(self, scenario, failure_point):
        files = self._formal_files()
        run = self.base / ("fixture-" + scenario)
        (run / "runtime").mkdir(parents=True)
        dump(run / "baseline.json", {"entries": {}})
        dump(run / "bindings.json", {
            "order": ["FIXTURE_GATE"],
            "gates": {"FIXTURE_GATE": {"dependencies": []}},
        })
        blocked_marker_parent = run / "blocked-marker-parent"
        blocked_marker_parent.write_text("not a directory\n")
        original_errors = []
        adapters = []
        native_process = {}
        stream = FailingDiagnosticStream(failure_point)

        class Runner:
            SHA = "fixture-candidate"
            TREE = "fixture-tree"
            runpath = staticmethod(lambda _run_id: run)
            put = staticmethod(external29_driver.durable)

            @staticmethod
            def run_gate(name, _matrix, _run, _scope, _sealed, _results):
                if scenario == "acquisition":
                    raise AssertionError("acquisition failure dispatched a native gate")
                child = subprocess.Popen(
                    [sys.executable, "-c", "raise SystemExit(73)"],
                    cwd=self.base, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    start_new_session=True)
                stdout, stderr = child.communicate(timeout=10)
                native_process.update(pid=child.pid, native_exit=child.returncode,
                                      stdout=stdout, stderr=stderr)
                error = NativeGateFailure("actual fixture native gate exited nonzero")
                original_errors.append(error)
                error.runner_gate_receipt = {
                    "gate": name, "result": "FAIL", "wrapper_exit": 1,
                    "native_exit": child.returncode, "child_pid": child.pid,
                    "error_type": type(error).__name__, "reason": str(error),
                    "failure_stage": "NATIVE_GATE",
                    "failure_dimensions": {
                        "native_invocation": True, "native_exit": child.returncode,
                        "native_command_exit_failure": True,
                        "product_assertion_failure": False,
                        "observer_preservation_failure": False,
                        "workload_timeout_or_cancellation": False,
                        "wrapper_or_environment_failure": True,
                        "evidence_persistence_failure": False,
                        "parser_helper_process_failure": False,
                        "cleanup_failure": False,
                    },
                    "causal_errors": external29_driver.causal_rows(
                        error, "NATIVE_GATE", "primary"),
                }
                raise error

        class Sequence:
            verify = staticmethod(lambda _run: True)

        class Observer:
            def bind_policy(self, _policy):
                return None

            def close(self):
                return None

        class FixtureAdapter(executor_adapter.RunAdapter):
            def __init__(self, *_args, **_kwargs):
                self.run = run
                self.state_path = run / "FORMAL_ATTEMPT.json"
                self.failure_path = blocked_marker_parent / "BOOKKEEPING_FAILURE.json"
                self.engine = None
                self.attempt_id = "fixture-attempt"
                self.failed = False
                self.failure_marker_errors = []
                adapters.append(self)

        config = {
            "run_id": "fixture-r11-diagnostic-" + scenario,
            "candidate": Runner.SHA, "tree": Runner.TREE,
            "owner_sha256": "0" * 64, "matrix_sha256": "1" * 64,
            "owner": str(files["binding"]), "dependency": str(files["binding"]),
        }
        for key in ("applicability", "private_map", "private_inventory"):
            source = files[key.replace("_", "-")]
            config[key] = str(source.absolute())
            config[key + "_sha256"] = digest(source)
        args = SimpleNamespace(
            binding=files["binding"], binding_sha256=digest(files["binding"]),
            run_id=config["run_id"], review=files["review"],
            applicability=files["applicability"], private_map=files["private-map"],
            private_inventory=files["private-inventory"])
        observe_module = __import__("observe")
        policy_module = __import__("policy_builder")
        capture_calls = []

        def strict_capture(_scope):
            capture_calls.append(len(capture_calls) + 1)
            if scenario == "acquisition" and len(capture_calls) == 2:
                try:
                    (self.base / "actual-missing-acquisition-source").read_bytes()
                except OSError as error:
                    original_errors.append(error)
                    raise
            return {"result": "COMPLETE", "entries": {}, "errors": []}

        patches = (
            patch.object(external29_driver, "verify_required_runtime_files", return_value=True),
            patch.object(external29_driver, "modules", return_value=(config, object(), Runner, Sequence)),
            patch.object(external29_driver, "consume_formal", return_value={"attempt_id": "fixture-attempt"}),
            patch.object(external29_driver, "observer_seed", return_value={}),
            patch.object(external29_driver, "strict_baseline", return_value=({}, {}, None)),
            patch.object(external29_driver, "engineering_preflight", return_value={}),
            patch.object(external29_driver, "strict_capture", side_effect=strict_capture),
            patch.object(external29_driver, "boundary", return_value={}),
            patch.object(observe_module, "BoundaryObserver", return_value=Observer()),
            patch.object(policy_module, "build", return_value={}),
            patch.object(policy_module, "write_private",
                         side_effect=lambda path, value: dump(path, value)),
            patch.object(executor_adapter, "RunAdapter", FixtureAdapter),
            patch.object(external29_driver.sys, "stderr", stream),
        )
        for item in patches:
            item.start()
        formal_return = None
        formal_error = None
        try:
            try:
                formal_return = external29_driver.formal(args)
            except BaseException as error:
                formal_error = error
        finally:
            for item in reversed(patches):
                item.stop()

        saved_path = run / "FORMAL_FAILURE.json"
        self.assertTrue(saved_path.is_file(), "available outer final sink was not used")
        saved_root = (Path(os.environ["EP19_QUALIFICATION_FIXTURE_ROOT"]) /
                      (scenario + "-diagnostic-failure"))
        saved_root.mkdir(mode=0o700)
        retained_path = saved_root / "FORMAL_FAILURE.json"
        retained_path.write_bytes(saved_path.read_bytes())
        saved = json.loads(retained_path.read_bytes())
        result = saved.get("results", {}).get("FIXTURE_GATE")
        dump(saved_root / "READBACK.json", {
            "schema": "ep19-r11-diagnostic-failure-readback-v1",
            "scenario": scenario, "failure_point": failure_point,
            "saved_receipt": str(retained_path.absolute()),
            "saved_receipt_sha256": digest(retained_path),
            "saved_receipt_bytes": retained_path.stat().st_size,
            "json_readback": True,
            "formal_return": formal_return,
            "formal_raised_type": None if formal_error is None else type(formal_error).__name__,
            "stderr_write_calls": stream.write_calls,
            "stderr_flush_calls": stream.flush_calls,
            "native_pid": native_process.get("pid"),
            "native_exit": native_process.get("native_exit"),
            "formal_attempt": False, "product_tests": False,
            "shared_preparation": False, "shared_probes": False,
            "shared_baseline": False, "candidate_formal_namespace_created": False,
        })

        self.assertTrue(original_errors, "actual primary failure was not acquired")
        self.assertTrue(adapters and adapters[0].failed)
        self.assertTrue(adapters[0].failure_marker_errors,
                        "actual marker persistence failure was not retained")
        self.assertIsNotNone(stream.error, "actual diagnostic stderr did not fail")
        self.assertIn("FIXTURE_GATE", saved.get("results", {}),
                      "gate result was not assigned before fallible diagnostic emission")
        self.assertIsNotNone(result)
        rows = saved["causal_errors"]
        result_rows = result.get("causal_errors", [])
        types = {row["error_type"] for row in rows}
        result_types = {row["error_type"] for row in result_rows}
        self.assertIn(type(original_errors[0]).__name__, types)
        self.assertIn("DiagnosticStderrFailure", types)
        self.assertTrue({row["error_type"] for row in adapters[0].failure_marker_errors}
                        <= types)
        self.assertIn(type(original_errors[0]).__name__, result_types)
        self.assertIn("DiagnosticStderrFailure", result_types)
        self.assertEqual(len({row["occurrence_id"] for row in rows}), len(rows))
        self.assertTrue(all(row.get("contexts") for row in rows), rows)
        self.assertEqual(result["result"], "FAIL")
        self.assertFalse(result["semantic_success_artifacts_allowed"])
        self.assertEqual(result["diagnostic_delivery"],
                         "BEST_EFFORT_STDERR_FAILED_RETAINED_IN_FINAL_SINK")
        self.assertFalse(result["diagnostic_stderr_delivered"])
        self.assertFalse(result["diagnostic_stderr_persistence_claim"])
        self.assertTrue(result["diagnostic_persistence_uncertain"])
        if scenario == "acquisition":
            self.assertEqual(native_process, {})
            self.assertFalse(result["failure_dimensions"]["native_invocation"])
        else:
            self.assertEqual(native_process["native_exit"], 73)
            self.assertEqual(result["native_exit"], 73)
            self.assertTrue(result["failure_dimensions"]["native_invocation"])

    def test_actual_acquisition_and_marker_then_stderr_write_failure_saved(self):
        self._invoke_actual_formal("acquisition", "write")

    def test_actual_native_gate_and_marker_then_stderr_flush_failure_saved(self):
        self._invoke_actual_formal("gate", "flush")


if __name__ == "__main__":
    unittest.main(verbosity=2)
