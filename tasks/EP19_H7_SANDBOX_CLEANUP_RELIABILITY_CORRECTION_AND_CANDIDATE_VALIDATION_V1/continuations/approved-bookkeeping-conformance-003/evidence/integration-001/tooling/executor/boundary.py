"""One approved predicate used at baseline and every later execution boundary."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import time
import uuid

import bookkeeping_v3 as bk
import observe

PHASES = frozenset(("BASELINE", "PREFLIGHT", "PRESTART", "COMMAND", "GATE",
                    "FINAL", "COVERAGE", "SEAL"))


class BoundaryReject(RuntimeError):
    pass


def _reason(exc):
    return f"{type(exc).__name__}:{exc}"


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def _exclusive_write(path, payload, mode):
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("ZERO_EVIDENCE_WRITE")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def write_evidence(directory, result, bundle):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.is_symlink() or not directory.is_dir():
        raise BoundaryReject("EVIDENCE_DESTINATION_INVALID")
    leaf = f"{result['boundary_id']}.json"
    private = directory / "private"
    private.mkdir(mode=0o700, exist_ok=True)
    private_payload = {**result, "privacy": "PRIVATE_OWNER_ONLY_RAW_CAPTURE",
                       "capture_bundle": bk.private_bundle(bundle)}
    public_payload = {**result, "privacy": "SANITIZED_NO_RAW_BODIES",
                      "capture_bundle": bk.public_bundle(bundle)}
    _exclusive_write(private / leaf, _json_bytes(private_payload), 0o600)
    _exclusive_write(directory / leaf, _json_bytes(public_payload), 0o400)
    dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(dirfd)
    finally:
        os.close(dirfd)
    return {"public": str(directory / leaf), "private": str(private / leaf),
            "public_sha256": hashlib.sha256(_json_bytes(public_payload)).hexdigest(),
            "private_sha256": hashlib.sha256(_json_bytes(private_payload)).hexdigest()}


def validate_runtime_binding(binding, expected):
    if not isinstance(binding, dict) or binding.get("schema") not in (
            "ep19-approved-candidate-binding-v3", "ep19-external29-runtime-binding-v1"):
        raise BoundaryReject("BINDING_SCHEMA_STALE")
    for key, value in expected.items():
        if binding.get(key) != value:
            raise BoundaryReject("BINDING_MISMATCH " + key)
    dependency = binding
    if binding.get("schema") == "ep19-external29-runtime-binding-v1":
        dependency = json.loads(Path(binding["dependency"]).read_text())
    if dependency.get("ledger_use", dependency.get("ledger_role")) != "OBSERVATION_INTEGRITY_ONLY":
        raise BoundaryReject("LEDGER_DEPENDENCY_ROLE_INVALID")
    forbidden = set(dependency.get("ledger_consumers", [])) & {
        "authorization", "instruction_selection", "candidate_selection",
        "gate_policy", "rollback", "ledger_list",
    }
    if forbidden or dependency.get("unbound_dynamic_readers"):
        raise BoundaryReject("LEDGER_CONSUMER_DEPENDENCY_REJECT")
    return True


class Engine:
    """Stateful original+previous-prefix reducer shared by all named boundaries."""
    def __init__(self, policy, *, binding=None, expected_binding=None,
                 window_start=None, window_end=None):
        bk._validate_policy(policy)
        if binding is not None:
            validate_runtime_binding(binding, expected_binding or {})
        self.policy = policy
        self.session = bk.new_session(policy)
        self.binding = binding
        self.window_start = window_start or datetime.now(timezone.utc)
        self.window_end = window_end or datetime.max.replace(tzinfo=timezone.utc)
        self.boundary_count = 0
        self.previous_usage = {"sha256": policy["usage_baseline"]["sha256"],
                               "metadata": policy["usage_baseline"]["metadata"]}

    def check(self, phase, *, events=(), coverage_errors=(), coverage_complete=True,
              strict_input_integrity=True, evidence_dir=None, bundle=None):
        if phase not in PHASES:
            raise BoundaryReject("UNKNOWN_BOUNDARY_PHASE")
        started = time.time_ns()
        boundary_id = f"{self.boundary_count:04d}-{phase.lower()}-{uuid.uuid4().hex}"
        self.boundary_count += 1
        reasons = []
        usage = lock = ledger = strict = None
        try:
            bundle = bundle or bk.capture_bundle(self.policy["root"], self.policy["eligible_map"])
            if not bundle.get("coherent"):
                raise BoundaryReject("CAPTURE_BUNDLE_INCOHERENT")
            strict = bk.evaluate_root_and_manifests(self.policy, bundle)
            usage = bk.evaluate_usage(self.policy, bundle["usage"])
            lock = bk.evaluate_lock(self.policy, bundle["lock"])
            ledger = bk.evaluate_ledger(self.policy, self.session, bundle["ledger"],
                                        window_start=self.window_start,
                                        window_end=self.window_end)
        except Exception as exc:
            reasons.append(_reason(exc))
        ledger_growth = bool(ledger and ledger["appended_this_boundary"])
        usage_variation = bool(bundle and (bundle["usage"]["sha256"] != self.previous_usage["sha256"] or
                                           bundle["usage"]["metadata"] != self.previous_usage["metadata"]))
        semantic_event_reasons = []
        if any(event.get("path") == self.policy["paths"]["lock"] for event in events) and lock is None:
            semantic_event_reasons.append("LOCK_PENDING_ENDPOINT_UNDECIDABLE")
        if any(event.get("path") == self.policy["paths"]["ledger"] for event in events) and ledger is None:
            semantic_event_reasons.append("LEDGER_PENDING_ENDPOINT_UNDECIDABLE")
        if any(event.get("path") == self.policy["paths"]["usage"] for event in events) and usage is None:
            semantic_event_reasons.append("USAGE_PENDING_ENDPOINT_UNDECIDABLE")
        reduced = observe.reduce_events(self.policy, list(events), ledger_growth=ledger_growth,
                                        usage_variation=usage_variation,
                                        require_usage_event=phase != "BASELINE",
                                        coverage_errors=coverage_errors,
                                        semantic_reasons=semantic_event_reasons)
        reasons.extend(reduced["reasons"])
        capture_ids = bundle.get("capture_binding", {}) if bundle else {}
        coherent = bool(bundle and bundle.get("coherent") and
                        bundle.get("usage", {}).get("capture_id") == capture_ids.get("usage") and
                        bundle.get("lock", {}).get("capture_id") == capture_ids.get("lock") and
                        bundle.get("ledger", {}).get("capture_id") == capture_ids.get("ledger") and
                        bundle.get("root", {}).get("capture_id") == capture_ids.get("root"))
        if bundle and not coherent:
            reasons.append("CAPTURE_BINDING_MISMATCH")
        strict_pass = bool(strict and strict_input_integrity)
        semantics_pass = bool(usage and lock and ledger)
        rejected_events = sum(1 for event in reduced["events"]
                              if event["category"].startswith("REJECT"))
        unresolved = reduced["unresolved"]
        result = {
            "schema": "ep19-approved-boundary-decision-v3",
            "boundary_id": boundary_id,
            "phase": phase,
            "started_ns": started,
            "finished_ns": time.time_ns(),
            "STRICT_INPUT_INTEGRITY": "PASS" if strict_pass else "REJECT",
            "APPROVED_BOOKKEEPING_SEMANTICS": "PASS" if semantics_pass else "REJECT",
            "CAPTURE_BINDING_COHERENT": "YES" if coherent else "NO",
            "REJECTED_OR_UNRESOLVED_EVENTS": rejected_events + unresolved,
            "COVERAGE_COMPLETE": "YES" if coverage_complete and not coverage_errors else "NO",
            "OLD_STRICT_PRESERVATION_RESULT": (
                "PASS" if usage and ledger and usage["old_strict"] == ledger["old_strict"] == "PASS"
                else "OLD_STRICT_REJECT"),
            "usage": usage,
            "lock": lock,
            "ledger": ({key: value for key, value in ledger.items() if key != "next_session"}
                       if ledger else None),
            "strict": strict,
            "events": reduced["events"],
            "event_reasons": reduced["reasons"],
            "reasons": sorted(set(reasons)),
            "writer_attribution": "NOT_ESTABLISHED",
            "ledger_role": "OBSERVATION_INTEGRITY_ONLY",
            "accepted_observational_limit": (
                "Endpoint and original/previous-prefix checks cannot detect an overwrite-restore "
                "or truncate-regrow completed between covered captures."),
        }
        result["decision"] = "PASS" if bk.approved_baseline_acceptance(result) and not reasons else "REJECT"
        if result["decision"] == "PASS":
            self.session = ledger["next_session"]
            self.previous_usage = {"sha256": bundle["usage"]["sha256"],
                                   "metadata": bundle["usage"]["metadata"]}
        if evidence_dir is not None:
            try:
                result["evidence"] = write_evidence(evidence_dir, result, bundle)
            except Exception as exc:
                result["decision"] = "REJECT"
                result["reasons"].append("EVIDENCE_WRITE_FAILED:" + _reason(exc))
                raise BoundaryReject("EVIDENCE_WRITE_FAILED") from exc
        return result

    def require(self, phase, **kwargs):
        result = self.check(phase, **kwargs)
        if result["decision"] != "PASS":
            raise BoundaryReject("BOUNDARY_REJECT " + json.dumps(result["reasons"]))
        return result


def check_all_boundary_kinds(engine, source):
    """Adapter used by the formal executor: one predicate, no phase-specific bypass."""
    results = []
    for phase, kwargs in source:
        results.append(engine.require(phase, **kwargs))
    return results
