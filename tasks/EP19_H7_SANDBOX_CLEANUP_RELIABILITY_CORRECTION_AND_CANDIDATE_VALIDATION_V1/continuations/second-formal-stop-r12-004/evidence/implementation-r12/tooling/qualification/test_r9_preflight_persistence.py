"""Exact r8->r9 controls for actual preflight/final failure persistence."""
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


class R9ActualPreflightPersistenceControls(unittest.TestCase):
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

    def _adapter(self, name):
        run = self.base / name
        run.mkdir()
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        dump(run / "bindings.json", {"order": ["FIXTURE"]})
        dump(run / "baseline.json", {"entries": {}})
        dump(run / "seal.json", {"files": {}})
        lean = run / "runtime/cache/backend/formal-tools/lean-4.19.0-linux/bin/lean"
        lean.parent.mkdir(parents=True)
        lean.write_text("fixture executable identity only\n")
        return run, adapter

    @staticmethod
    def _components():
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

        return Coverage(), Runner(), Sequence(), Observer()

    @staticmethod
    def _original_failure(_scope):
        causal.raise_composed(
            "R9_ORIGINAL_PREFLIGHT_CAPTURE_AND_CLEANUP_FAILURE",
            RuntimeError("r9 original preflight native leaf"),
            [("capture-cleanup", "PREFLIGHT_CAPTURE_CLEANUP",
              OSError("r9 original preflight cleanup leaf"))],
            primary_stage="PREFLIGHT_NATIVE_CAPTURE")

    def _invoke_preflight(self, name, *, fail_preflight_write):
        run, adapter = self._adapter(name)
        coverage, runner, sequence, observer = self._components()
        real_write = durability.os.write

        def actual_write_fault(fd, value):
            target = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target == run / "preflight.json":
                raise OSError("r9 actual preflight.json write failure")
            return real_write(fd, value)

        write = actual_write_fault if fail_preflight_write else real_write
        caught = None
        with patch.object(external29_driver, "strict_capture",
                          side_effect=self._original_failure), \
             patch.object(durability.os, "write", side_effect=write):
            try:
                external29_driver.engineering_preflight(
                    run, {"protected": []}, self.policy, adapter, observer,
                    {"qualification": str(self.base / "qualification.json")},
                    coverage, runner, sequence, None)
            except BaseException as error:
                caught = error
        self.assertIsNotNone(caught)
        self.assertTrue(adapter.failed)
        self.assertFalse((run / "runtime/START.json").exists())
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.final()
        return run, caught, runner

    def _assert_original_disposition(self, value):
        nested = value.get("preflight_disposition")
        disposition = nested if isinstance(nested, dict) else value
        self.assertEqual(disposition.get("result"), "ENGINEERING_PREFLIGHT_BLOCKED",
                         disposition)
        self.assertEqual(disposition.get("preflight_disposition"),
                         "IRREVERSIBLY_LATCHED_REJECT", disposition)
        rows = value.get("causal_errors", [])
        reasons = " ".join(str(row.get("reason", "")) for row in rows)
        self.assertIn("r9 original preflight native leaf", reasons)
        self.assertIn("r9 original preflight cleanup leaf", reasons)
        occurrences = [row.get("occurrence_id") for row in rows]
        self.assertEqual(len(occurrences), len(set(occurrences)), rows)

    def test_original_preflight_failure_alone_has_real_saved_final_readback(self):
        run, caught, runner = self._invoke_preflight(
            "original-only", fail_preflight_write=False)
        preflight = json.loads((run / "preflight.json").read_text())
        self._assert_original_disposition(preflight)
        final = external29_driver.formal_failure_document(
            caught, "fixture-attempt", ["FIXTURE"], runner, {})
        final_path = run / "FORMAL_FAILURE.fixture.json"
        external29_driver.durable(final_path, final)
        saved = json.loads(final_path.read_text())
        self._assert_original_disposition(saved)
        self.assertEqual(saved["results"]["FIXTURE"]["result"], "NOT_RUN")
        self.assertFalse(saved["downstream_dispatch"])

    def test_actual_preflight_write_failure_is_secondary_to_original_disposition(self):
        run, caught, runner = self._invoke_preflight(
            "preflight-write-fault", fail_preflight_write=True)
        receipt = getattr(caught, "preflight_receipt", {})
        self._assert_original_disposition(receipt)
        self.assertFalse(getattr(caught, "preflight_receipt_persisted", True))
        rows = external29_driver.causal_rows(
            caught, "FORMAL_BODY", "primary")
        reasons = " ".join(str(row.get("reason", "")) for row in rows)
        self.assertIn("r9 original preflight native leaf", reasons)
        self.assertIn("r9 original preflight cleanup leaf", reasons)
        self.assertIn("r9 actual preflight.json write failure", reasons)
        final = external29_driver.formal_failure_document(
            caught, "fixture-attempt", ["FIXTURE"], runner, {})
        final_path = run / "FORMAL_FAILURE.fixture.json"
        external29_driver.durable(final_path, final)
        saved = json.loads(final_path.read_text())
        self._assert_original_disposition(saved)
        saved_reasons = " ".join(row.get("reason", "")
                                 for row in saved["causal_errors"])
        self.assertIn("r9 actual preflight.json write failure", saved_reasons)
        self.assertFalse(saved["preflight_receipt_persisted"])

    def test_final_failure_sink_fault_retains_available_original_and_secondaries(self):
        run, caught, runner = self._invoke_preflight(
            "final-sink-fault", fail_preflight_write=True)
        final = external29_driver.formal_failure_document(
            caught, "fixture-attempt", ["FIXTURE"], runner, {})
        final_path = run / "FORMAL_FAILURE.fixture.json"
        real_write = durability.os.write

        def final_write_fault(fd, value):
            target = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if target == final_path:
                raise OSError("r9 actual final failure sink write failure")
            return real_write(fd, value)

        final_error = None
        with patch.object(durability.os, "write", side_effect=final_write_fault):
            try:
                external29_driver.durable(final_path, final)
            except BaseException as error:
                final_error = error
        self.assertIsNotNone(final_error)
        self.assertFalse(final_path.read_bytes(),
                         "a failed exclusive write is not a durable final receipt")
        builder = getattr(external29_driver, "formal_persistence_failure", None)
        if callable(builder):
            available = builder(caught, [final_error], [])
            rows = available.formal_failure_causes
            self._assert_original_disposition(
                {"preflight_disposition": available.preflight_receipt,
                 "causal_errors": rows})
        else:
            rows = (external29_driver.causal_rows(caught, "FORMAL_BODY", "primary") +
                    external29_driver.causal_rows(
                        final_error, "FORMAL_FAILURE_PERSISTENCE"))
        reasons = " ".join(str(row.get("reason", "")) for row in rows)
        self.assertIn("r9 original preflight native leaf", reasons)
        self.assertIn("r9 original preflight cleanup leaf", reasons)
        self.assertIn("r9 actual preflight.json write failure", reasons)
        self.assertIn("r9 actual final failure sink write failure", reasons)
        self.assertFalse((run / "runtime/START.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
