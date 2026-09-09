"""r10 controls for the actual FINAL receipt handler and production stderr boundary."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = Path(os.environ.get("EP19_TEST_EXECUTOR_ROOT", ROOT / "executor"))
sys.path.insert(0, str(EXECUTOR))

import durability
import external29_driver


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class R10ActualFinalBoundaryControls(unittest.TestCase):
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

    def _invoke_actual_formal_final_handler(self):
        """Reach the production formal() FINAL except without launching formal work."""
        files = self._formal_files()
        run = self.base / "fixture-final-handler"
        run.mkdir()
        order = external29_driver.load(
            ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")["order"]
        original = RuntimeError("r10 bounded private FINAL boundary rejection")

        class Runner:
            SHA = "fixture-candidate"
            TREE = "fixture-tree"
            runpath = staticmethod(lambda _run_id: run)
            put = staticmethod(external29_driver.durable)

        class Sequence:
            verify = staticmethod(lambda _run: True)

        class Observer:
            def bind_policy(self, _policy):
                return None

            def close(self):
                return None

        class Adapter:
            def __init__(self, *args, **kwargs):
                self.failure_path = run / "existing-failure-marker.json"
                self.failure_path.write_text("{}\n")

        config = {
            "run_id": "fixture-r10-final-handler",
            "candidate": Runner.SHA,
            "tree": Runner.TREE,
            "owner_sha256": "0" * 64,
            "matrix_sha256": "1" * 64,
            "owner": str(files["binding"]),
            "dependency": str(files["binding"]),
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
        adapter_module = __import__("executor_adapter")
        real_write = durability.os.write
        final_path = run / "runtime/FINAL_FAILURE.json"

        def final_receipt_write_fault(fd, value):
            target = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target == final_path:
                raise OSError("r10 actual FINAL_FAILURE.json write failure")
            return real_write(fd, value)

        def strict_check(*_args):
            phase = _args[4]
            if phase == "FINAL":
                raise original
            return {}

        results = {name: {"gate": name, "result": "PASS"} for name in order}
        patches = (
            patch.object(external29_driver, "verify_required_runtime_files", return_value=True),
            patch.object(external29_driver, "modules", return_value=(config, object(), Runner, Sequence)),
            patch.object(external29_driver, "consume_formal", return_value={"attempt_id": "fixture-attempt"}),
            patch.object(external29_driver, "observer_seed", return_value={}),
            patch.object(external29_driver, "strict_baseline", return_value=({}, {}, None)),
            patch.object(external29_driver, "engineering_preflight", return_value={}),
            patch.object(external29_driver, "latching_strict_check", side_effect=strict_check),
            patch.object(external29_driver, "boundary", return_value={}),
            patch.object(external29_driver, "execute_actual_graph", return_value=(results, False)),
            patch.object(observe_module, "BoundaryObserver", return_value=Observer()),
            patch.object(policy_module, "build", return_value={}),
            patch.object(policy_module, "write_private",
                         side_effect=lambda path, value: dump(path, value)),
            patch.object(adapter_module, "RunAdapter", Adapter),
            patch.object(durability.os, "write", side_effect=final_receipt_write_fault),
        )
        for item in patches:
            item.start()
        try:
            return_code = external29_driver.formal(args)
        finally:
            for item in reversed(patches):
                item.stop()
        self.assertEqual(return_code, 1)
        self.assertTrue(final_path.exists())
        self.assertEqual(final_path.read_bytes(), b"")
        return run, original

    def test_actual_final_failure_writer_fault_keeps_original_in_saved_formal_receipt(self):
        run, original = self._invoke_actual_formal_final_handler()
        saved_path = run / "FORMAL_FAILURE.json"
        self.assertTrue(saved_path.is_file())
        saved_root = (Path(os.environ["EP19_QUALIFICATION_FIXTURE_ROOT"]) /
                      "available-final-receipt")
        saved_root.mkdir(mode=0o700)
        retained_path = saved_root / "FORMAL_FAILURE.json"
        retained_path.write_bytes(saved_path.read_bytes())
        failed_runtime_path = saved_root / "FINAL_FAILURE.empty.bin"
        failed_runtime_path.write_bytes((run / "runtime/FINAL_FAILURE.json").read_bytes())
        dump(saved_root / "READBACK.json", {
            "schema": "ep19-r10-available-final-receipt-readback-v1",
            "saved_receipt": str(retained_path),
            "saved_receipt_sha256": digest(retained_path),
            "saved_receipt_bytes": retained_path.stat().st_size,
            "failed_runtime_receipt": str(failed_runtime_path),
            "failed_runtime_receipt_sha256": digest(failed_runtime_path),
            "failed_runtime_receipt_bytes": failed_runtime_path.stat().st_size,
            "json_readback": True, "formal_attempt": False,
            "product_tests": False, "candidate_formal_namespace_created": False,
        })
        saved = json.loads(retained_path.read_bytes())
        rows = saved["causal_errors"]
        by_type = {row["error_type"]: row for row in rows}
        self.assertIn("RuntimeError", by_type, rows)
        self.assertIn("OSError", by_type, rows)
        original_rows = external29_driver.causal_rows(
            original, "FINAL_ACCEPTANCE", "primary")
        self.assertIn(original_rows[0]["occurrence_id"],
                      {row["occurrence_id"] for row in rows})
        self.assertTrue(by_type["RuntimeError"]["contexts"])
        self.assertTrue(by_type["OSError"]["contexts"])
        disposition = saved["final_boundary_disposition"]
        self.assertEqual(disposition["result"], "FINAL_ACCEPTANCE_REJECTED")
        self.assertEqual(disposition["disposition"], "IRREVERSIBLY_LATCHED_REJECT")
        self.assertFalse(saved["final_failure_receipt_persisted"])
        self.assertFalse(disposition["semantic_success_artifacts_allowed"])

    def test_production_main_saved_stderr_has_structured_original_and_both_sink_failures(self):
        saved_root = Path(os.environ["EP19_QUALIFICATION_FIXTURE_ROOT"]) / "native-main-fallback"
        saved_root.mkdir(mode=0o700)
        child = self.base / "invoke_native_main.py"
        child.write_text(textwrap.dedent("""
            from pathlib import Path
            from unittest.mock import patch
            import json, os, sys

            executor = Path(os.environ["EP19_TEST_EXECUTOR_ROOT"])
            sys.path.insert(0, str(executor))
            import durability
            import external29_driver as driver

            run = Path(os.environ["EP19_R10_CHILD_RUN"])
            run.mkdir(mode=0o700)
            final_path = run / "runtime/FINAL_FAILURE.json"
            formal_path = run / "FORMAL_FAILURE.json"
            real_write = durability.os.write

            class Runner:
                SHA = "fixture-candidate"
                TREE = "fixture-tree"
                put = staticmethod(driver.durable)

            def write_fault(fd, value):
                target = Path(os.readlink(f"/proc/self/fd/{fd}"))
                if target == final_path:
                    raise OSError("r10 actual runtime final receipt sink failure")
                if target == formal_path:
                    raise OSError("r10 actual outer formal receipt sink failure")
                return real_write(fd, value)

            def producer(_args):
                original = RuntimeError("r10 bounded private final rejection body")
                with patch.object(durability.os, "write", side_effect=write_fault):
                    try:
                        try:
                            raise original
                        except Exception as caught:
                            handler = getattr(driver, "persist_final_boundary_failure", None)
                            if callable(handler):
                                handler(run, Runner, caught)
                            else:
                                Runner.put(final_path, {
                                    "reason": str(caught),
                                    "causal_errors": driver.causal_rows(
                                        caught, "FINAL_ACCEPTANCE", "primary"),
                                    "semantic_success_artifacts_allowed": False})
                    except BaseException as primary:
                        failure = driver.formal_failure_document(
                            primary, "fixture-attempt", ["FIXTURE"], Runner, {})
                        try:
                            driver.durable(formal_path, failure)
                        except BaseException as final_sink:
                            raise driver.formal_persistence_failure(
                                primary, [final_sink], []) from None
                raise AssertionError("fixture sink faults did not reject")

            driver.fixture = producer
            sys.argv = [str(executor / "external29_driver.py"), "fixture",
                        "--fixture-root", str(run / "unused-fixture"),
                        "--output", str(run / "unused-output"),
                        "--scenario", "allowed"]
            raise SystemExit(driver.main())
        """))
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "EP19_TEST_EXECUTOR_ROOT": str(EXECUTOR),
               "EP19_R10_CHILD_RUN": str(self.base / "native-main-run")}
        started_ns = __import__("time").time_ns()
        process = subprocess.run(
            [sys.executable, "-B", str(child)], cwd=self.base, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        finished_ns = __import__("time").time_ns()
        stdout_path = saved_root / "STDOUT.bin"
        stderr_path = saved_root / "STDERR.bin"
        stdout_path.write_bytes(process.stdout)
        stderr_path.write_bytes(process.stderr)
        process_doc = {
            "schema": "ep19-r10-native-main-parent-process-v1",
            "argv": [sys.executable, "-B", str(child)],
            "cwd": str(self.base), "native_exit": process.returncode,
            "started_wall_ns": started_ns, "finished_wall_ns": finished_ns,
            "stdout": str(stdout_path), "stdout_sha256": digest(stdout_path),
            "stderr": str(stderr_path), "stderr_sha256": digest(stderr_path),
            "formal_attempt": False, "product_tests": False,
            "shared_preparation": False, "shared_probes": False,
            "shared_baseline": False, "candidate_formal_namespace_created": False,
        }
        dump(saved_root / "PROCESS.json", process_doc)
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(process.stdout, b"")
        try:
            parsed = json.loads(process.stderr)
        except json.JSONDecodeError as error:
            self.fail("production stderr is not structured JSON: " + str(error))
        dump(saved_root / "PARSED.json", parsed)
        self.assertEqual(parsed["schema"], "ep19-external29-native-failure-v1")
        self.assertEqual(parsed["result"], "FAIL")
        self.assertFalse(parsed["success_allowed"])
        self.assertEqual(parsed["stderr_transport"], "BEST_EFFORT_NOT_DURABLE")
        rows = parsed["causal_errors"]
        self.assertEqual({row["error_type"] for row in rows},
                         {"RuntimeError", "OSError"})
        self.assertGreaterEqual(sum(row["error_type"] == "OSError" for row in rows), 2)
        self.assertEqual(len({row["occurrence_id"] for row in rows}), len(rows))
        self.assertTrue(all(row["contexts"] for row in rows))
        self.assertTrue(all(row["reason_exposed"] is False for row in rows))
        self.assertEqual(parsed["final_boundary_disposition"]["disposition"],
                         "IRREVERSIBLY_LATCHED_REJECT")
        self.assertFalse(parsed["final_failure_receipt_persisted"])

    def test_unavailable_stderr_returns_false_without_persistence_claim(self):
        original = RuntimeError("r10 private body must not be printed")
        failure = external29_driver.formal_persistence_failure(
            original, [OSError("r10 private sink detail")], [])
        emitter = getattr(external29_driver, "emit_native_failure", None)
        self.assertTrue(callable(emitter), "production native emitter is missing")
        with patch.object(external29_driver.os, "write",
                          side_effect=OSError("stderr unavailable")):
            self.assertFalse(emitter(failure))


if __name__ == "__main__":
    unittest.main(verbosity=2)
