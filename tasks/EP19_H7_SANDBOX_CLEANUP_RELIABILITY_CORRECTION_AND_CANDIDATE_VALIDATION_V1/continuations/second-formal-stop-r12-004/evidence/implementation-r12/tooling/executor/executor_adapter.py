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
import durability
import causal


class NamespaceConsumed(BoundaryReject):
    pass


def _durable_exclusive(path, value):
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    durability.exclusive_bytes(path, payload, 0o400)


class RunAdapter:
    def __init__(self, run, policy, *, consumed_attempt=None, **engine_args):
        self.run = Path(run)
        self.state_path = self.run / "BOOKKEEPING_ATTEMPT.json"
        self.failure_path = self.run / "BOOKKEEPING_FAILURE.json"
        self.engine = Engine(policy, **engine_args)
        self.attempt_id = None
        self.failed = False
        self.failure_marker_errors = []
        if consumed_attempt is not None:
            try:
                self.attach_consumed_attempt(consumed_attempt)
            except Exception as exc:
                self._latch_exception("ATTACH_CONSUMED_ATTEMPT", exc)
                raise

    def _latch_exception(self, phase, exc):
        primary_rows = causal.receipt_rows(exc, "primary", phase)
        diagnostic = {"decision": "REJECT",
                      "reasons": [f"{type(exc).__name__}:{exc}"],
                      "causal_errors": primary_rows,
                      "semantic_success_artifacts_allowed": False}
        try:
            self.fail(phase, diagnostic)
        except BaseException as marker_error:
            self._attach_marker_failure(phase, exc, marker_error, primary_rows)

    def _attach_marker_failure(self, phase, primary, marker_error, primary_rows=None):
        """Latch and associate marker failure without replacing the primary decision."""
        self.failed = True
        primary_rows = list(primary_rows or causal.receipt_rows(primary, "primary", phase))
        details = causal.rows(marker_error, "failure-marker-persistence",
                              "FAILURE_MARKER_PERSISTENCE",
                              "secondary-for-primary-exception")
        for detail in details:
            detail.update(phase=phase, primary_error_type=type(primary).__name__,
                          primary_reason=str(primary), primary_causal_errors=primary_rows)
        self.failure_marker_errors = causal.unique([*self.failure_marker_errors, *details])
        setattr(primary, "failure_marker_errors", list(self.failure_marker_errors))
        return details

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
        try:
            if self.attempt_id is not None:
                self._require_live()
                return
            if self.state_path.exists() or self.failure_path.exists():
                raise NamespaceConsumed("FAILED_OR_CONSUMED_NAMESPACE_CANNOT_RESURRECT")
            durability.ensure_directory(self.run, 0o700)
            attempt_id = uuid.uuid4().hex
            _durable_exclusive(self.state_path, {
                "schema": "ep19-approved-bookkeeping-attempt-v3",
                "attempt_id": attempt_id,
                "state": "CONSUMED_BEFORE_BASELINE",
                "consumed_ns": time.time_ns(),
                "formal_attempt": False,
            })
            self.attempt_id = attempt_id
        except Exception as exc:
            self._latch_exception("CONSUME_FOR_BASELINE", exc)
            raise

    def _require_live(self):
        if self.failed or not self.state_path.is_file() or self.failure_path.exists():
            raise NamespaceConsumed("FAILED_OR_UNCONSUMED_NAMESPACE_CANNOT_REACH_BOUNDARY")
        state = json.loads(self.state_path.read_text())
        if (state.get("attempt_id") != self.attempt_id or state.get("state") not in
                ("CONSUMED_BEFORE_BASELINE", "CONSUMED_BEFORE_POLICY_AND_BASELINE")):
            raise NamespaceConsumed("NAMESPACE_STATE_BINDING_MISMATCH")

    def boundary(self, phase, **kwargs):
        try:
            self._require_live()
            result = self.engine.check(phase, **kwargs)
        except Exception as exc:
            if not self.failed:
                self._latch_exception(phase, exc)
            raise
        if result["decision"] != "PASS":
            rejection = BoundaryReject("BOUNDARY_REJECT " + phase)
            rejection.boundary_decision_receipt = result
            rejection.causal_errors = list(result.get("causal_errors", []))
            try:
                self.fail(phase, result)
            except BaseException as marker_error:
                details = self._attach_marker_failure(
                    phase, rejection, marker_error,
                    causal.receipt_rows(rejection, "primary", phase))
                try:
                    causal.raise_composed(
                        "BOUNDARY_REJECT_AND_FAILURE_MARKER_PERSISTENCE_FAILURE",
                        rejection,
                        [("failure-marker-persistence", "FAILURE_MARKER_PERSISTENCE",
                          marker_error)],
                        dimensions={"evidence_persistence_failure": True},
                        primary_stage=phase)
                except BaseException as combined:
                    combined.boundary_decision_receipt = result
                    combined.failure_marker_errors = list(details)
                    raise combined from None
            raise rejection
        return result

    def fail(self, phase, result):
        self.failed = True
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
