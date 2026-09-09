"""Boundary adapter for the existing executor lifecycle.

It deliberately contains no gate launcher.  The parent integrates this adapter
after fresh preparation; the writer qualification exercises only disposable
files and cannot consume the remaining formal attempt.
"""
from __future__ import annotations

from pathlib import Path
import json
import os
import time
import uuid

from boundary import Engine, BoundaryReject


class NamespaceConsumed(BoundaryReject):
    pass


def _durable_exclusive(path, value):
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        view = memoryview(payload)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("ZERO_STATE_WRITE")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


class RunAdapter:
    def __init__(self, run, policy, *, consumed_attempt=None, **engine_args):
        self.run = Path(run)
        self.state_path = self.run / "BOOKKEEPING_ATTEMPT.json"
        self.failure_path = self.run / "BOOKKEEPING_FAILURE.json"
        self.engine = Engine(policy, **engine_args)
        self.attempt_id = None
        if consumed_attempt is not None:
            self.attach_consumed_attempt(consumed_attempt)

    def attach_consumed_attempt(self, attempt):
        """Attach the driver's one formal marker; never create a second marker."""
        if (not isinstance(attempt, dict) or
                attempt.get("state") != "CONSUMED_BEFORE_POLICY_AND_BASELINE" or
                attempt.get("formal_attempt") is not True or
                attempt.get("run_id") != self.run.name or
                not isinstance(attempt.get("attempt_id"), str)):
            raise NamespaceConsumed("FORMAL_ATTEMPT_MARKER_INVALID")
        marker = self.run / "FORMAL_ATTEMPT.json"
        if not marker.is_file() or json.loads(marker.read_text()) != attempt:
            raise NamespaceConsumed("FORMAL_ATTEMPT_MARKER_BINDING_MISMATCH")
        self.state_path = marker
        self.attempt_id = attempt["attempt_id"]

    def consume_for_baseline(self):
        if self.attempt_id is not None:
            self._require_live()
            return
        if self.state_path.exists() or self.failure_path.exists():
            raise NamespaceConsumed("FAILED_OR_CONSUMED_NAMESPACE_CANNOT_RESURRECT")
        self.run.mkdir(parents=True, exist_ok=True)
        self.attempt_id = uuid.uuid4().hex
        _durable_exclusive(self.state_path, {
            "schema": "ep19-approved-bookkeeping-attempt-v3",
            "attempt_id": self.attempt_id,
            "state": "CONSUMED_BEFORE_BASELINE",
            "consumed_ns": time.time_ns(),
            "formal_attempt": False,
        })

    def _require_live(self):
        if not self.state_path.is_file() or self.failure_path.exists():
            raise NamespaceConsumed("FAILED_OR_UNCONSUMED_NAMESPACE_CANNOT_REACH_BOUNDARY")
        state = json.loads(self.state_path.read_text())
        if (state.get("attempt_id") != self.attempt_id or state.get("state") not in
                ("CONSUMED_BEFORE_BASELINE", "CONSUMED_BEFORE_POLICY_AND_BASELINE")):
            raise NamespaceConsumed("NAMESPACE_STATE_BINDING_MISMATCH")

    def boundary(self, phase, **kwargs):
        self._require_live()
        result = self.engine.check(phase, **kwargs)
        if result["decision"] != "PASS":
            self.fail(phase, result)
            raise BoundaryReject("BOUNDARY_REJECT " + phase)
        return result

    def fail(self, phase, result):
        if not self.failure_path.exists():
            _durable_exclusive(self.failure_path, {
                "schema": "ep19-approved-bookkeeping-failure-v3",
                "attempt_id": self.attempt_id,
                "phase": phase,
                "failed_ns": time.time_ns(),
                "decision": result,
                "retry_authorized": False,
                "baseline_rebuild_authorized": False,
            })

    def baseline(self, **kwargs):
        self.consume_for_baseline()
        return self.boundary("BASELINE", **kwargs)

    def preflight(self, **kwargs): return self.boundary("PREFLIGHT", **kwargs)
    def prestart(self, **kwargs): return self.boundary("PRESTART", **kwargs)
    def command(self, **kwargs): return self.boundary("COMMAND", **kwargs)
    def gate(self, **kwargs): return self.boundary("GATE", **kwargs)
    def final(self, **kwargs): return self.boundary("FINAL", **kwargs)
    def coverage(self, **kwargs): return self.boundary("COVERAGE", **kwargs)
    def seal(self, **kwargs): return self.boundary("SEAL", **kwargs)
