"""Fresh controls for the three concrete r7 Part-B AR008 findings."""
from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = Path(os.environ.get("EP19_TEST_EXECUTOR_ROOT", ROOT / "executor"))
import sys
sys.path.insert(0, str(EXECUTOR))

import bookkeeping_v3 as bk
import causal
import durability
import executor_adapter
import external29_driver


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class R8ActualTransportControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(
            dir=os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT"))
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skills = self.base / "skills"
        self.skills.mkdir(mode=0o700)
        package = self.skills / "alpha"
        package.mkdir()
        (package / "SKILL.md").write_text("fixture\n")
        dump(self.skills / bk.USAGE_NAME, {"alpha": {"view_count": 1, "use_count": 1,
             "last_viewed_at": None, "last_used_at": None}})
        os.chmod(self.skills / bk.USAGE_NAME, 0o600)
        (self.skills / bk.LOCK_NAME).touch(mode=0o644)
        (self.skills / bk.LEDGER_NAME).write_bytes(b"")
        os.chmod(self.skills / bk.LEDGER_NAME, 0o600)
        self.policy = bk.create_policy(self.skills, owner_sha256="8" * 64,
                                       dependency_sha256="9" * 64,
                                       eligible_names=["alpha"], fixture=True)

    def adapter(self, name):
        run = self.base / name
        run.mkdir()
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        return run, adapter

    def test_actual_engine_reject_and_marker_fault_keep_decision_in_saved_driver_failure(self):
        run, adapter = self.adapter("reject-marker")
        dump(run / "bindings.json", {"order": ["FIXTURE"]})
        real_write = durability.os.write

        class Observer:
            calls = 0

            @classmethod
            def boundary_events(cls):
                cls.calls += 1
                return [], ["R8_FORCED_ACTUAL_BOUNDARY_REJECT"]

        class Runner:
            SHA = "fixture-candidate"
            TREE = "fixture-tree"

            @staticmethod
            def run_gate(*_args):
                raise AssertionError("gate must not run after the actual Engine rejects")

        def marker_write_fault(fd, value):
            target = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target == adapter.failure_path:
                raise OSError("r8 failure marker persistence fault")
            return real_write(fd, value)

        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(durability.os, "write", side_effect=marker_write_fault):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, self.policy, adapter, Observer(), Runner, object(), None)

        saved_path = run / "DRIVER_FINAL_FAILURE.fixture.json"
        external29_driver.durable(saved_path, results["FIXTURE"])
        saved = json.loads(saved_path.read_text())
        joined = " ".join(str(row.get("reason", "")) for row in
                          saved.get("causal_errors", []) + saved.get("secondary_failures", []))
        self.assertTrue(stopped)
        self.assertTrue(adapter.failed)
        self.assertEqual(Observer.calls, 1, "no later accepting boundary may run")
        self.assertEqual(saved["decision"], "REJECT")
        self.assertIn("R8_FORCED_ACTUAL_BOUNDARY_REJECT", " ".join(saved["reasons"]))
        self.assertIn("r8 failure marker persistence fault", joined)
        self.assertTrue(saved.get("diagnostic_persistence_uncertain"), saved)
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.final()

    def test_nested_actual_durability_failure_keeps_occurrences_and_context_topology(self):
        run, adapter = self.adapter("nested-causal")
        target = self.base / "durable-target" / "receipt.json"
        target.parent.mkdir()
        real_close = durability.os.close
        real_write = durability.os.write
        real_fsync = durability.os.fsync

        def write_primary(fd, value):
            target_path = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target_path == target:
                raise OSError("r8 outer write primary")
            return real_write(fd, value)

        def fsync_inner(fd):
            target_path = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target_path == target.parent:
                raise OSError("r8 inner directory fsync primary")
            return real_fsync(fd)

        def close_same_text(fd):
            target_path = Path(os.readlink(f"/proc/self/fd/{fd}"))
            real_close(fd)
            if target_path in (target, target.parent):
                raise OSError("r8 identical close failure")

        caught = None
        with patch.object(durability.os, "write", side_effect=write_primary), \
             patch.object(durability.os, "fsync", side_effect=fsync_inner), \
             patch.object(durability.os, "close", side_effect=close_same_text):
            try:
                durability.exclusive_bytes(target, b"fixture\n")
            except BaseException as error:
                caught = error
        self.assertIsNotNone(caught)
        adapter._latch_exception("R8_NESTED_DURABILITY", caught)
        saved = json.loads(adapter.failure_path.read_text())["decision"]
        rows = saved["causal_errors"]
        closes = [row for row in rows if row.get("reason") == "r8 identical close failure"]
        self.assertEqual(len(closes), 2, rows)
        self.assertEqual(len({row["occurrence_id"] for row in closes}), 2, closes)
        self.assertEqual({row["stage"] for row in closes},
                         {"FILE_FD_CLOSE", "DIRECTORY_FD_CLOSE"})
        inner = next(row for row in rows
                     if row.get("reason") == "r8 inner directory fsync primary")
        contexts = inner["contexts"]
        self.assertTrue(any(item["role"] == "primary" and
                            item["stage"] == "BODY_OR_NATIVE" for item in contexts), contexts)
        self.assertTrue(any(item["role"] == "publishing-parent-fsync" and
                            item["association"] == "secondary-for-primary"
                            for item in contexts), contexts)
        context_ids = {item["context_id"] for item in contexts}
        self.assertTrue(any(item.get("parent_context_id") in context_ids
                            for item in contexts if item.get("parent_context_id")), contexts)

    def test_actual_preflight_wiring_propagates_native_and_evidence_causes_to_formal_failure(self):
        run, adapter = self.adapter("preflight")
        dump(run / "bindings.json", {"order": ["FIXTURE"]})
        dump(run / "baseline.json", {"entries": {}})
        dump(run / "seal.json", {"files": {}})
        lean = run / "runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean"
        lean.parent.mkdir(parents=True)
        lean.write_text("fixture executable identity only\n")

        class Coverage:
            qualification_inputs = staticmethod(lambda _path: True)
            check_seal = staticmethod(lambda _files: True)

        class Bindings:
            @staticmethod
            def build(_run):
                return {"order": ["FIXTURE"]}

        class Runner:
            SHA = "fixture-candidate"
            TREE = "fixture-tree"
            bindings = Bindings()
            repos = staticmethod(lambda _run: [])
            exact = staticmethod(lambda _root: True)
            put = staticmethod(external29_driver.durable)

        class Sequence:
            verify = staticmethod(lambda _run: True)

        class Observer:
            boundary_events = staticmethod(lambda: ([], []))

        def bounded_fixture_producer(_scope):
            causal.raise_composed(
                "R8_PREFLIGHT_FIXTURE_COMPOSED_FAILURE",
                RuntimeError("r8 native preflight leaf"),
                [("evidence-write-secondary", "PREFLIGHT_EVIDENCE_WRITE",
                  OSError("r8 preflight evidence write secondary"))],
                primary_stage="PREFLIGHT_NATIVE_CAPTURE")

        caught = None
        with patch.object(external29_driver, "strict_capture",
                          side_effect=bounded_fixture_producer):
            try:
                external29_driver.engineering_preflight(
                    run, {"protected": []}, self.policy, adapter, Observer(),
                    {"qualification": str(self.base / "qualification.json")},
                    Coverage(), Runner(), Sequence(), None)
            except Exception as error:
                caught = error
        self.assertIsNotNone(caught)
        builder = getattr(external29_driver, "formal_failure_document", None)
        self.assertTrue(callable(builder), "formal must use the same source-tested failure builder")
        final = builder(caught, "fixture-attempt", ["FIXTURE"], Runner(), {})
        preflight = json.loads((run / "preflight.json").read_text())
        for receipt in (preflight, getattr(caught, "preflight_receipt", {}),
                        final.get("preflight_disposition", {})):
            self.assertEqual(receipt.get("result"), "ENGINEERING_PREFLIGHT_BLOCKED", receipt)
        joined = " ".join(row.get("reason", "") for row in final["causal_errors"])
        self.assertIn("r8 native preflight leaf", joined)
        self.assertIn("r8 preflight evidence write secondary", joined)
        self.assertTrue(adapter.failed)
        self.assertFalse((run / "runtime/START.json").exists())
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.final()


if __name__ == "__main__":
    unittest.main(verbosity=2)
