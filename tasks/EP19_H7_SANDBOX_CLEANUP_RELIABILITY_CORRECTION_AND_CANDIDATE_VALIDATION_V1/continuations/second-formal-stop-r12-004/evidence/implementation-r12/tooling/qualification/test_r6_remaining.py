"""Fixed source-bound controls for r5 AR008/AR010 residual paths."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import importlib.util, json, os, signal, subprocess, sys, tempfile, time, types, unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
TARGET = Path(os.environ.get("EP19_TEST_EXECUTOR_ROOT", HERE / "executor")).absolute()
TOOLING = Path(os.environ.get("EP19_TEST_TOOLING_ROOT", HERE)).absolute()
sys.path.insert(0, str(TARGET))
import capture, durability, external29_driver, native_observe, observe, preservation

def flattened(error):
    rows = []; pending = [error]
    while pending:
        item = pending.pop(0); rows.append(type(item).__name__ + ":" + str(item))
        pending.extend(getattr(item, "exceptions", ()))
    return rows

def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n")

class R6ExceptionCompositionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("EP19_QUALIFICATION_FIXTURE_ROOT"))
        self.addCleanup(self.temp.cleanup); self.base = Path(self.temp.name)

    def observer_policy(self):
        root = self.base / "skills"; package = root / "fixture"; package.mkdir(parents=True)
        (package / "SKILL.md").write_text("fixture\n")
        usage = root / ".usage.json"; usage.write_text("{}\n")
        lock = root / ".usage.json.lock"; lock.write_bytes(b"")
        ledger = root / ".curator_ledger.jsonl"; ledger.write_bytes(b"")
        return {"root": str(root), "paths": {"usage": str(usage), "lock": str(lock),
                "ledger": str(ledger)}, "eligible_map": {"fixture": {"package": str(package)}}}

    def test_boundary_observer_constructor_retains_primary_and_close_failure(self):
        policy = self.observer_policy(); real_close = observe.BoundaryObserver.close
        def close_then_fail(instance):
            real_close(instance); raise OSError("boundary observer close failed")
        with patch.object(observe.BoundaryObserver, "_add", side_effect=ValueError("boundary observer add failed")), \
             patch.object(observe.BoundaryObserver, "close", close_then_fail):
            with self.assertRaises(BaseException) as caught: observe.BoundaryObserver(policy)
        messages = " ".join(flattened(caught.exception))
        self.assertIn("boundary observer add failed", messages)
        self.assertIn("boundary observer close failed", messages)

    def test_parent_fd_attempts_every_ancestor_close_and_keeps_body_failure(self):
        leaf = self.base / "a" / "b" / "c.txt"; leaf.parent.mkdir(parents=True); leaf.write_text("x")
        opened = []; closed = []; real_open = preservation.os.open; real_close = preservation.os.close
        def recording_open(*args, **kwargs):
            fd = real_open(*args, **kwargs); opened.append(fd); return fd
        failed = [False]
        def one_close_failure(fd):
            closed.append(fd); real_close(fd)
            if not failed[0]: failed[0] = True; raise OSError("ancestor close failed")
        with patch.object(preservation.os, "open", side_effect=recording_open), \
             patch.object(preservation.os, "close", side_effect=one_close_failure):
            with self.assertRaises(BaseException) as caught:
                with preservation.parent_fd(leaf): raise ValueError("parent body failed")
        messages = " ".join(flattened(caught.exception))
        self.assertIn("parent body failed", messages); self.assertIn("ancestor close failed", messages)
        self.assertEqual(set(opened), set(closed))

    def test_durable_stream_attempts_flush_stream_fd_and_parent_cleanup_independently(self):
        target = self.base / "durable" / "evidence.log"; target.parent.mkdir(); calls = []
        real_fdopen = durability.os.fdopen; real_close = durability.os.close
        class Stream:
            def __init__(self, wrapped): self.wrapped = wrapped
            def flush(self): calls.append("flush"); raise OSError("flush failed")
            def close(self): calls.append("stream.close")
        def fdopen(fd, *args, **kwargs): return Stream(real_fdopen(fd, *args, **kwargs))
        failed = [False]
        def raw_close(fd):
            calls.append("fd.close"); real_close(fd)
            if not failed[0]: failed[0] = True; raise OSError("raw close failed")
        def parent_sync(path): calls.append("parent.fsync"); raise OSError("parent fsync failed")
        with patch.object(durability.os, "fdopen", side_effect=fdopen), \
             patch.object(durability.os, "close", side_effect=raw_close), \
             patch.object(durability, "fsync_directory", side_effect=parent_sync):
            with self.assertRaises(BaseException) as caught:
                with durability.exclusive_stream(target): raise ValueError("stream body failed")
        messages = " ".join(flattened(caught.exception))
        for expected in ("stream body failed", "flush failed", "raw close failed", "parent fsync failed"):
            self.assertIn(expected, messages)
        self.assertEqual(calls, ["flush", "stream.close", "fd.close", "parent.fsync"])

    def test_durable_stream_fdopen_failure_releases_owned_raw_fd_and_syncs_parent(self):
        target = self.base / "fdopen" / "evidence.log"; target.parent.mkdir(); calls = []
        real_close = durability.os.close
        def close(fd): calls.append("fd.close"); return real_close(fd)
        def parent_sync(path): calls.append("parent.fsync")
        with patch.object(durability.os, "fdopen", side_effect=OSError("fdopen failed")), \
             patch.object(durability.os, "close", side_effect=close), \
             patch.object(durability, "fsync_directory", side_effect=parent_sync):
            with self.assertRaises(BaseException) as caught:
                with durability.exclusive_stream(target): self.fail("fdopen failure yielded a stream")
        self.assertIn("fdopen failed", " ".join(flattened(caught.exception)))
        self.assertEqual(calls, ["fd.close", "parent.fsync"])

    def test_capture_file_body_and_fd_close_failure_are_both_reported(self):
        target = self.base / "capture.txt"; target.write_text("stable\n"); real_close = capture.os.close
        def close_then_fail(fd): real_close(fd); raise OSError("capture close failed")
        def hook(phase, _path, _attempt):
            if phase == "opened": raise capture.CaptureError("capture body failed")
        with patch.object(capture.os, "close", side_effect=close_then_fail):
            with self.assertRaises(BaseException) as caught:
                capture.capture_file(target, attempts=1, hook=hook)
        messages = " ".join(flattened(caught.exception))
        self.assertIn("capture body failed", messages); self.assertIn("capture close failed", messages)

    def load_vite(self):
        execution = types.ModuleType("execution"); execution.H = TARGET
        spec = importlib.util.spec_from_file_location("r6_vite_" + self.base.name, TARGET / "vite_closure.py")
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"execution": execution}): spec.loader.exec_module(module)
        return module

    def test_vite_helper_primary_and_real_stream_fsync_failure_both_survive(self):
        module = self.load_vite(); root = self.base / "built"; root.mkdir(); real_fsync = durability.os.fsync
        calls = [0]
        def first_fsync_fails(fd):
            calls[0] += 1
            if calls[0] == 1: raise OSError("controlled file fsync failed")
            return real_fsync(fd)
        with patch.object(module.subprocess, "run", return_value=types.SimpleNamespace(returncode=7)), \
             patch.object(durability.os, "fsync", side_effect=first_fsync_fails):
            with self.assertRaises(BaseException) as caught:
                module.validate(root, "/", self.base / "tools", self.base / "closure.json")
        rows = getattr(caught.exception, "causal_errors", [])
        reasons = " ".join(row.get("reason", "") for row in rows) + " " + " ".join(flattened(caught.exception))
        dimensions = getattr(caught.exception, "failure_dimensions", {})
        self.assertIn("exit=7", reasons); self.assertIn("controlled file fsync failed", reasons)
        self.assertTrue(dimensions.get("parser_helper_process_failure"), dimensions)
        self.assertTrue(dimensions.get("evidence_persistence_failure"), dimensions)

    def test_exception_after_exited_parent_terminates_actual_owned_descendant(self):
        protected = self.base / "protected"; protected.write_text("stable\n")
        pid_file = self.base / "descendant.pid"; log = self.base / "native.log"
        script = ("import pathlib,subprocess,sys,time\n"
                  "p=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(60)'],start_new_session=True)\n"
                  "pathlib.Path(sys.argv[1]).write_text(str(p.pid))\n"
                  "time.sleep(.15)\n")
        real_drain = native_observe.Watch.drain; count = [0]
        def fail_after_parent_exit(watch, *args, **kwargs):
            count[0] += 1
            if count[0] == 2:
                deadline = time.monotonic() + 3
                while not pid_file.exists() and time.monotonic() < deadline: time.sleep(.01)
                time.sleep(.3)
                raise RuntimeError("observer exception after parent exit")
            return real_drain(watch, *args, **kwargs)
        descendant = None
        try:
            with patch.object(native_observe.Watch, "drain", fail_after_parent_exit):
                with self.assertRaises(BaseException) as caught:
                    native_observe.run([sys.executable, "-B", "-c", script, str(pid_file)], self.base, log,
                        protected=[protected], repositories=[], metadata_roots=[], allowed=[self.base],
                        enumeration_roots=[], pruned_roots=[], expected_missing=[], frozen_roots=[], timeout=3)
            descendant = int(pid_file.read_text()); receipt = getattr(caught.exception, "native_observe_receipt", {})
            self.assertIn("observer exception after parent exit", " ".join(flattened(caught.exception)))
            self.assertIn(descendant, receipt.get("owned_processes_terminated", []), receipt)
            self.assertEqual(receipt.get("owned_processes_remaining"), [], receipt)
            self.assertEqual(receipt.get("owned_descendant_cleanup", {}).get("result"), "QUIESCENT", receipt)
            with self.assertRaises(ProcessLookupError): os.kill(descendant, 0)
        finally:
            if descendant is None and pid_file.exists(): descendant = int(pid_file.read_text())
            if descendant is not None:
                try: os.kill(descendant, signal.SIGKILL)
                except ProcessLookupError: pass
                try: os.waitpid(descendant, 0)
                except ChildProcessError: pass

    def test_owned_descendant_unknown_permission_and_timeout_are_distinct(self):
        class Scope:
            known = {991001: "one"}
            def pending(self): return [991001]
            @staticmethod
            def birth(_pid): return "one"
        with patch.object(native_observe.os, "kill", side_effect=PermissionError("denied")):
            receipt = native_observe.cleanup_owned_descendants(Scope(), timeout_seconds=.02)
        kinds = {row["kind"] for row in receipt["errors"]}
        self.assertIn("OWNED_DESCENDANT_SIGNAL_PERMISSION", kinds)
        self.assertIn("OWNED_DESCENDANT_CLEANUP_TIMEOUT", kinds)
        self.assertEqual(receipt["result"], "NOT_QUIESCENT")

    def test_attached_receipt_plus_marker_failure_reaches_final_gate_result(self):
        run = self.base / "graph"; run.mkdir(); dump(run / "bindings.json", {"order": ["FIXTURE"]})
        attached = {"gate": "FIXTURE", "result": "FAIL", "reason": "original parser failure",
                    "failure_stage": "RECEIPT_PERSISTENCE", "native_exit": 0, "child_pid": 101,
                    "causal_errors": [{"role": "primary", "stage": "PARSER_CALLBACK",
                    "error_type": "RuntimeError", "reason": "original parser failure"},
                    {"role": "secondary", "stage": "RECEIPT_PERSISTENCE",
                    "error_type": "OSError", "reason": "final receipt write failed"}],
                    "failure_dimensions": {"native_invocation": True, "native_exit": 0,
                    "product_assertion_failure": True, "evidence_persistence_failure": True}}
        error = OSError("final receipt write failed"); error.runner_gate_receipt = attached
        class Runner:
            SHA = "s"; TREE = "t"
            @staticmethod
            def run_gate(*_args): raise error
        class Adapter:
            failed = False
            def _latch_exception(self, _phase, exc):
                self.failed = True
                exc.failure_marker_errors = [{"role": "failure-marker-persistence",
                    "stage": "FAILURE_MARKER_PERSISTENCE", "error_type": "OSError",
                    "reason": "failure marker write failed"}]
        with patch.object(external29_driver, "latching_strict_check", return_value={}), \
             patch.object(external29_driver, "boundary", return_value={}):
            results, stopped = external29_driver.execute_actual_graph(run, {}, {}, {}, Adapter(),
                                                                       object(), Runner, object(), None)
        result = results["FIXTURE"]; self.assertTrue(stopped)
        joined = " ".join(row["reason"] for row in result.get("causal_errors", []) +
                          result.get("secondary_failures", []))
        self.assertIn("original parser failure", joined); self.assertIn("final receipt write failed", joined)
        self.assertIn("failure marker write failed", joined)
        self.assertTrue(result.get("diagnostic_persistence_uncertain"), result)

if __name__ == "__main__": unittest.main(verbosity=2)
