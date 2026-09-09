"""Fresh source-bound controls for the concrete r6 reviewer findings only."""
from __future__ import annotations

from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "executor"
sys.path.insert(0, str(EXECUTOR))

import bookkeeping_v3 as bk
import boundary
import capture
import durability
import executor_adapter
import external29_driver
import native_observe
import preservation


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def rows(error):
    retained = getattr(error, "causal_errors", None)
    if isinstance(retained, list) and retained:
        return retained
    result = []
    pending = [error]
    while pending:
        item = pending.pop(0)
        children = list(getattr(item, "exceptions", ()))
        if children:
            pending.extend(children)
        else:
            result.append({"error_type": type(item).__name__, "reason": str(item)})
    return result


class R7ReviewerFindingControls(unittest.TestCase):
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
        self.policy = bk.create_policy(self.skills, owner_sha256="4" * 64,
                                       dependency_sha256="5" * 64,
                                       eligible_names=["alpha"], fixture=True)

    def _capture_cancellation(self, primary):
        target = self.base / (type(primary).__name__ + ".txt")
        target.write_text("owned descriptor\n")
        opened = []
        closed = []
        real_open = capture.os.open
        real_close = capture.os.close

        def recording_open(*args, **kwargs):
            fd = real_open(*args, **kwargs)
            opened.append(fd)
            return fd

        def close_then_fail(fd):
            closed.append(fd)
            real_close(fd)
            raise OSError("r7 capture close secondary")

        def fail_after_open(phase, _path, _attempt):
            if phase == "opened":
                raise primary

        caught = None
        try:
            with patch.object(capture.os, "open", side_effect=recording_open), \
                 patch.object(capture.os, "close", side_effect=close_then_fail):
                try:
                    capture.capture_file(target, attempts=1, hook=fail_after_open)
                except BaseException as error:
                    caught = error
            self.assertIsNotNone(caught)
            self.assertEqual(opened, closed)
            reasons = " ".join(str(row.get("reason", "")) for row in rows(caught))
            self.assertIn(str(primary), reasons)
            self.assertIn("r7 capture close secondary", reasons)
            with self.assertRaises(OSError):
                os.fstat(opened[0])
        finally:
            for fd in set(opened) - set(closed):
                try:
                    real_close(fd)
                except OSError:
                    pass

    def test_keyboard_interrupt_after_actual_fd_acquisition_releases_and_retains_both_causes(self):
        self._capture_cancellation(KeyboardInterrupt("r7 capture keyboard primary"))

    def test_memory_error_after_actual_fd_acquisition_releases_and_retains_both_causes(self):
        self._capture_cancellation(MemoryError("r7 capture memory primary"))

    def test_known_owned_descendants_are_isolated_when_one_identity_query_fails(self):
        unrelated = subprocess.Popen([sys.executable, "-B", "-c", "import time;time.sleep(60)"],
                                     start_new_session=True)
        scope = native_observe.ChildScope()
        children = [subprocess.Popen([sys.executable, "-B", "-c", "import time;time.sleep(60)"],
                                     start_new_session=True) for _ in range(2)]
        signaled = []
        real_birth = scope.birth
        real_kill = native_observe.os.kill
        try:
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if set(scope.pending()) == {child.pid for child in children}:
                    break
                time.sleep(.01)
            self.assertEqual(set(scope.known), {child.pid for child in children})
            uncertain_pid, controlled_pid = children[0].pid, children[1].pid

            def one_identity_failure(pid):
                if pid == uncertain_pid:
                    raise PermissionError("r7 controlled birth denial")
                return real_birth(pid)

            def record_kill(pid, sig):
                signaled.append(pid)
                return real_kill(pid, sig)

            with patch.object(scope, "birth", side_effect=one_identity_failure), \
                 patch.object(native_observe.os, "kill", side_effect=record_kill):
                receipt = native_observe.cleanup_owned_descendants(
                    scope, timeout_seconds=.08, poll_seconds=.005)
            self.assertIn(controlled_pid, receipt["terminated"], receipt)
            self.assertNotIn(unrelated.pid, signaled)
            self.assertNotIn(unrelated.pid, receipt["owned_identities"])
            self.assertEqual(receipt["result"], "NOT_QUIESCENT")
            self.assertTrue(any("IDENTITY" in row["kind"] for row in receipt["errors"]), receipt)
            self.assertIn(uncertain_pid, receipt["remaining"])
        finally:
            for process in [*children, unrelated]:
                try:
                    real_kill(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            scope.close()

    def test_capture_preservation_boundary_adapter_driver_saved_receipt_keeps_leaf_causes(self):
        run = self.base / "causal-run"
        run.mkdir()
        dump(run / "bindings.json", {"order": ["FIXTURE"]})
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        target = self.base / "protected.txt"
        target.write_text("stable\n")
        real_close = preservation.os.close

        def fault_bundle(*_args, **_kwargs):
            return preservation.capture_files([target])

        def close_then_fail(fd):
            real_close(fd)
            raise OSError("r7 preservation close leaf")

        class Observer:
            @staticmethod
            def boundary_events():
                return [], []

        class Runner:
            SHA = "s"
            TREE = "t"

            @staticmethod
            def run_gate(*_args):
                raise AssertionError("gate must not run after boundary capture failure")

        with patch.object(boundary.bk, "capture_bundle", side_effect=fault_bundle), \
             patch.object(preservation.os, "fstat", side_effect=MemoryError("r7 preservation primary leaf")), \
             patch.object(preservation.os, "close", side_effect=close_then_fail), \
             patch.object(external29_driver, "latching_strict_check", return_value={}):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, self.policy, adapter, Observer(), Runner, object(), None)
        self.assertTrue(stopped)
        self.assertTrue(adapter.failed)
        saved = json.loads(adapter.failure_path.read_text())
        saved_rows = saved["decision"].get("causal_errors", [])
        final_rows = results["FIXTURE"].get("causal_errors", [])
        for expected in ("r7 preservation primary leaf", "r7 preservation close leaf"):
            self.assertIn(expected, " ".join(row.get("reason", "") for row in saved_rows), saved)
            self.assertIn(expected, " ".join(row.get("reason", "") for row in final_rows), results)
        with self.assertRaises(executor_adapter.NamespaceConsumed):
            adapter.final()

    def test_actual_adapter_composed_marker_failure_reaches_driver_final_diagnostic(self):
        run = self.base / "marker-run"
        run.mkdir()
        dump(run / "bindings.json", {"order": ["FIXTURE"]})
        adapter = executor_adapter.RunAdapter(run, self.policy)
        adapter.consume_for_baseline()
        real_close = durability.os.close

        class Runner:
            SHA = "s"
            TREE = "t"

            @staticmethod
            def run_gate(*_args):
                raise RuntimeError("r7 original gate leaf")

        def close_then_fail(fd):
            real_close(fd)
            raise OSError("r7 marker close leaf")

        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", return_value={}), \
             patch.object(durability.os, "write", side_effect=OSError("r7 marker write leaf")), \
             patch.object(durability.os, "close", side_effect=close_then_fail), \
             patch.object(durability, "fsync_directory", side_effect=OSError("r7 marker parent fsync leaf")):
            results, stopped = external29_driver.execute_actual_graph(
                run, {}, {}, self.policy, adapter, object(), Runner, object(), None)
        self.assertTrue(stopped)
        self.assertTrue(adapter.failed)
        final = results["FIXTURE"]
        joined = " ".join(row.get("reason", "") for row in
                          final.get("causal_errors", []) + final.get("secondary_failures", []))
        for expected in ("r7 original gate leaf", "r7 marker write leaf",
                         "r7 marker close leaf", "r7 marker parent fsync leaf"):
            self.assertIn(expected, joined, final)
        self.assertTrue(final.get("diagnostic_persistence_uncertain"), final)


if __name__ == "__main__":
    unittest.main(verbosity=2)
