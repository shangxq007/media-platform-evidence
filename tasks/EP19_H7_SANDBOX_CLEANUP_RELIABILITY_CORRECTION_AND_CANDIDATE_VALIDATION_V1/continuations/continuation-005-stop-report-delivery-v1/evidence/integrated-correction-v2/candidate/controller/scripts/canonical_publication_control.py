#!/usr/bin/env python3
"""Fail-closed canonical publication authorization control plane.

This module never invokes Git and never writes repository source code.  It
maintains queue/slot control state and emits exact authorization/readback
receipts for a separately authorized publication controller.
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import datetime as dt
import fcntl
import fnmatch
import glob
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any, Iterable, Iterator, Mapping, Sequence


PROTOCOL_VERSION = "CANONICAL_PUBLICATION_CONTROL_V1"
SLOT_RESOURCE = "MEDIA_PLATFORM_CANONICAL_PUBLICATION_SLOT"
SKILL_DIR = Path(__file__).resolve().parents[1]
REFERENCE_DIR = SKILL_DIR / "references"


class ControlError(RuntimeError):
    """A fail-closed control-plane rejection."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def normalized_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: os.PathLike[str] | str) -> str:
    return sha256_bytes(Path(path).read_bytes())


def load_json(path: os.PathLike[str] | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_bytes(path: os.PathLike[str] | str, data: bytes) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write_json(path: os.PathLike[str] | str, value: Any) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))


def immutable_write_json(path: os.PathLike[str] | str, value: Any) -> None:
    target = Path(path)
    payload = canonical_json_bytes(value)
    if target.exists():
        if target.read_bytes() != payload:
            raise ControlError(f"immutable receipt already exists with different bytes: {target}")
        return
    atomic_write_bytes(target, payload)


def stable_state_readback(path: os.PathLike[str] | str) -> dict[str, Any]:
    target = Path(path)
    authority_names = {"queue.json", "transition-ledger.json", "slot.json"}
    transaction = StateTransaction(target.parent) if target.name in authority_names else None
    if transaction is not None:
        with transaction.mutex():
            queue, ledger, slot = transaction._read_locked()
            first = target.read_bytes()
            second = target.read_bytes()
            authority_sha256 = {
                "queue.json": sha256_bytes(canonical_json_bytes(queue)),
                "transition-ledger.json": sha256_bytes(canonical_json_bytes(ledger)),
                "slot.json": sha256_bytes(canonical_json_bytes(slot)),
            }
            sequence = queue["STATE_TRANSACTION_SEQUENCE"]
    else:
        first = target.read_bytes()
        second = target.read_bytes()
        authority_sha256 = None
        sequence = None
    if first != second:
        raise ControlError("stable-state readback bytes differ")
    result = {
        "PATH": str(target),
        "BYTE_IDENTICAL_READS": True,
        "SHA256_FIRST": sha256_bytes(first),
        "SHA256_SECOND": sha256_bytes(second),
        "STABLE_STATE_READBACK": "PASS",
        "TIMESTAMP": utc_now(),
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
    }
    if authority_sha256 is not None:
        result.update({"AUTHORITY_SHA256": authority_sha256,
                       "STATE_TRANSACTION_SEQUENCE": sequence,
                       "SAME_LOCKED_SNAPSHOT": True})
    return result


STATE_TRANSACTION_VERSION = "CANONICAL_PUBLICATION_STATE_TRANSACTION_V1"
STATE_LOCK_NAME = ".canonical-publication-state.lock"
STATE_JOURNAL_NAME = ".canonical-publication-state-transaction.json"
HEX40 = frozenset("0123456789abcdef")
HEX64 = frozenset("0123456789abcdef")


def _is_lower_hex(value: Any, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and set(value) <= HEX64


def verified_json_reference(reference: Mapping[str, Any], name: str) -> tuple[dict[str, Any], str]:
    """Read evidence bytes, verify the caller digest, then parse one JSON object."""
    if not isinstance(reference, Mapping):
        raise ControlError(f"{name} reference must be an object")
    path_value = reference.get("PATH")
    expected = reference.get("SHA256")
    if not isinstance(path_value, str) or not path_value or not _is_lower_hex(expected, 64):
        raise ControlError(f"{name} path/digest reference is invalid")
    path = Path(path_value)
    if not path.is_file():
        raise ControlError(f"{name} path is not a regular file")
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != expected:
        raise ControlError(f"{name} byte digest mismatch")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlError(f"{name} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ControlError(f"{name} JSON must be an object")
    return value, actual


def verified_file_reference(reference: Mapping[str, Any], name: str) -> tuple[bytes, str]:
    if not isinstance(reference, Mapping):
        raise ControlError(f"{name} reference must be an object")
    path_value, expected = reference.get("PATH"), reference.get("SHA256")
    if not isinstance(path_value, str) or not path_value or not _is_lower_hex(expected, 64):
        raise ControlError(f"{name} path/digest reference is invalid")
    path = Path(path_value)
    if not path.is_file():
        raise ControlError(f"{name} path is not a regular file")
    payload = path.read_bytes(); actual = sha256_bytes(payload)
    if actual != expected:
        raise ControlError(f"{name} byte digest mismatch")
    return payload, actual


def verify_native_provenance(value: Mapping[str, Any], name: str, *, candidate: str, tree: str,
                             attempt_id: str, source_sha256: str, actor: str | None = None) -> str:
    receipt, receipt_sha = verified_json_reference(value.get("producer_receipt", {}), f"{name} producer receipt")
    expected = {"schema": "ep19-native-producer-receipt-v1", "result": "PASS", "native_exit_code": 0,
        "candidate": candidate, "tree": tree, "attempt_id": attempt_id,
        "source_sha256": source_sha256, "subject": name}
    _require_exact(receipt, expected, f"{name} producer receipt")
    if actor is not None and receipt.get("actor") != actor:
        raise ControlError(f"{name} producer actor mismatch")
    if (not isinstance(receipt.get("actor"), str) or not receipt["actor"]
            or not isinstance(receipt.get("started_ns"), int) or isinstance(receipt.get("started_ns"), bool)
            or not isinstance(receipt.get("finished_ns"), int) or receipt["finished_ns"] < receipt["started_ns"]):
        raise ControlError(f"{name} native producer timing/actor is invalid")
    verified_file_reference(receipt.get("stdout", {}), f"{name} native stdout")
    verified_file_reference(receipt.get("stderr", {}), f"{name} native stderr")
    return receipt_sha


def _require_exact(value: Mapping[str, Any], expected: Mapping[str, Any], name: str) -> None:
    for field, required in expected.items():
        if value.get(field) != required:
            raise ControlError(f"{name}.{field} does not match the required value")


class InjectedFault(RuntimeError):
    """Synthetic-only interruption used by source-bound qualification."""


class StateTransaction:
    """One journaled transaction domain for queue, ledger, and slot.

    The publication-slot flock remains the outer lock whenever a slot operation
    also changes authority state. All original readers take this inner lock and
    reject a present journal, so no partial multi-file state is consumable.
    """

    def __init__(self, state_root: os.PathLike[str] | str):
        self.root = Path(state_root)
        self.queue_path = self.root / "queue.json"
        self.ledger_path = self.root / "transition-ledger.json"
        self.slot_path = self.root / "slot.json"
        self.lock_path = self.root / STATE_LOCK_NAME
        self.journal_path = self.root / STATE_JOURNAL_NAME

    @contextlib.contextmanager
    def mutex(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _validate_values(queue: Any, ledger: Any, slot: Any) -> None:
        if not all(isinstance(value, dict) for value in (queue, ledger, slot)):
            raise ControlError("all three authority objects must be present")
        if queue.get("SCHEMA_VERSION") not in {None, "CANONICAL_PUBLICATION_QUEUE_V1"}:
            raise ControlError("queue schema version mismatch")
        if ledger.get("SCHEMA_VERSION") != "CONTROL_PLANE_TRANSITION_LEDGER_V1":
            raise ControlError("transition ledger schema version mismatch")
        if slot.get("PROTOCOL_VERSION") != PROTOCOL_VERSION or slot.get("RESOURCE_NAME") != SLOT_RESOURCE:
            raise ControlError("slot authority schema/version mismatch")
        if not isinstance(queue.get("ENTRIES"), list) or not isinstance(ledger.get("EVENTS"), list):
            raise ControlError("queue entries and ledger events must be arrays")
        sequence = queue.get("STATE_TRANSACTION_SEQUENCE", 0)
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
            raise ControlError("queue transaction sequence is invalid")
        if ledger.get("STATE_TRANSACTION_SEQUENCE", 0) != sequence or slot.get("STATE_TRANSACTION_SEQUENCE", 0) != sequence:
            raise ControlError("authority transaction sequence mismatch")
        transaction_ids = [
            event.get("TRANSACTION_ID") for event in ledger["EVENTS"]
            if event.get("STATE_TRANSACTION_VERSION") == STATE_TRANSACTION_VERSION
        ]
        if None in transaction_ids or len(transaction_ids) != len(set(transaction_ids)):
            raise ControlError("state transaction ledger identities are invalid")

    def _read_locked(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        if self.journal_path.exists():
            raise ControlError("interrupted/uncertain state transaction exists; explicit recovery is required")
        queue = load_json(self.queue_path)
        ledger = load_json(self.ledger_path)
        if not self.slot_path.is_file():
            raise ControlError("slot authority is absent")
        slot = load_json(self.slot_path)
        self._validate_values(queue, ledger, slot)
        return queue, ledger, slot

    def read(self) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        with self.mutex():
            return self._read_locked()

    @staticmethod
    def _payload_digest(operation: str, key: str, actor: str, timestamp: str, body: Mapping[str, Any]) -> str:
        return sha256_bytes(normalized_json_bytes({
            "OPERATION": operation, "IDEMPOTENCY_KEY": key, "ACTOR": actor,
            "TIMESTAMP": timestamp, "BODY": body,
        }))

    def commit(
        self,
        *,
        operation: str,
        idempotency_key: str,
        actor: str,
        timestamp: str,
        body: Mapping[str, Any],
        mutate: Any,
        expected_queue_sha256: str | None = None,
        expected_ledger_sha256: str | None = None,
        fault: str | None = None,
        already_locked: bool = False,
    ) -> dict[str, Any]:
        if not all(isinstance(value, str) and value for value in (operation, idempotency_key, actor, timestamp)):
            raise ControlError("transaction operation/key/actor/timestamp must be non-empty")
        payload_digest = self._payload_digest(operation, idempotency_key, actor, timestamp, body)
        transaction_id = sha256_bytes(normalized_json_bytes({"VERSION": STATE_TRANSACTION_VERSION, "PAYLOAD": payload_digest}))

        def perform() -> dict[str, Any]:
            queue, ledger, slot = self._read_locked()
            matching = [event for event in ledger["EVENTS"] if event.get("IDEMPOTENCY_KEY") == idempotency_key and event.get("STATE_TRANSACTION_VERSION") == STATE_TRANSACTION_VERSION]
            if len(matching) > 1:
                raise ControlError("duplicate idempotency key in state ledger")
            if matching:
                if matching[0].get("PAYLOAD_SHA256") != payload_digest:
                    raise ControlError("idempotency key already exists with a different payload")
                return {"STATUS": "IDEMPOTENT_REPLAY", "TRANSACTION_ID": matching[0]["TRANSACTION_ID"], "PAYLOAD_SHA256": payload_digest}
            before_queue = file_digest(self.queue_path)
            before_ledger = file_digest(self.ledger_path)
            if expected_queue_sha256 is not None and before_queue != expected_queue_sha256:
                raise ControlError("queue expected-before identity mismatch")
            if expected_ledger_sha256 is not None and before_ledger != expected_ledger_sha256:
                raise ControlError("ledger expected-before identity mismatch")
            after_queue, after_ledger, after_slot = copy.deepcopy(queue), copy.deepcopy(ledger), copy.deepcopy(slot)
            mutate(after_queue, after_ledger, after_slot, transaction_id, payload_digest)
            sequence = int(queue.get("STATE_TRANSACTION_SEQUENCE", 0)) + 1
            after_queue["STATE_TRANSACTION_SEQUENCE"] = sequence
            after_ledger["STATE_TRANSACTION_SEQUENCE"] = sequence
            if after_slot is not None:
                after_slot["STATE_TRANSACTION_SEQUENCE"] = sequence
            event = {
                "EVENT_TYPE": operation, "TRANSACTION_ID": transaction_id,
                "IDEMPOTENCY_KEY": idempotency_key, "PAYLOAD_SHA256": payload_digest,
                "ACTOR": actor, "TIMESTAMP": timestamp,
                "STATE_TRANSACTION_VERSION": STATE_TRANSACTION_VERSION,
            }
            after_ledger["EVENTS"].append(event)
            after_values = {"queue.json": after_queue, "transition-ledger.json": after_ledger}
            if after_slot is not None:
                after_values["slot.json"] = after_slot
            journal = {
                "STATE_TRANSACTION_VERSION": STATE_TRANSACTION_VERSION,
                "AUTHORITY": False,
                "TRANSACTION_ID": transaction_id,
                "BEFORE_SHA256": {"queue.json": before_queue, "transition-ledger.json": before_ledger, **({"slot.json": file_digest(self.slot_path)} if slot is not None else {})},
                "AFTER": after_values,
                "AFTER_SHA256": {name: sha256_bytes(canonical_json_bytes(value)) for name, value in after_values.items()},
            }
            atomic_write_json(self.journal_path, journal)
            for index, name in enumerate(("queue.json", "transition-ledger.json", "slot.json")):
                if name not in after_values:
                    continue
                atomic_write_json(self.root / name, after_values[name])
                if fault == f"AFTER_WRITE_{index + 1}":
                    raise InjectedFault(f"synthetic interruption after {name}")
            for name, expected in journal["AFTER_SHA256"].items():
                if file_digest(self.root / name) != expected:
                    raise ControlError(f"post-write authority verification failed: {name}")
            self._clear_journal()
            return {"STATUS": "COMMITTED", "TRANSACTION_ID": transaction_id, "PAYLOAD_SHA256": payload_digest}

        if already_locked:
            return perform()
        with self.mutex():
            return perform()

    def _clear_journal(self) -> None:
        self.journal_path.unlink()
        directory_fd = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

    def recover(self) -> dict[str, Any]:
        with self.mutex():
            if not self.journal_path.exists():
                raise ControlError("no interrupted state transaction to recover")
            journal = load_json(self.journal_path)
            required_keys = {"STATE_TRANSACTION_VERSION", "AUTHORITY", "TRANSACTION_ID", "BEFORE_SHA256", "AFTER", "AFTER_SHA256"}
            authority_names = {"queue.json", "transition-ledger.json", "slot.json"}
            if (set(journal) != required_keys or journal.get("STATE_TRANSACTION_VERSION") != STATE_TRANSACTION_VERSION
                    or journal.get("AUTHORITY") is not False or not _is_lower_hex(journal.get("TRANSACTION_ID"), 64)
                    or set(journal.get("BEFORE_SHA256", {})) != authority_names
                    or set(journal.get("AFTER", {})) != authority_names
                    or set(journal.get("AFTER_SHA256", {})) != authority_names):
                raise ControlError("unknown state transaction recovery journal")
            for name, value in journal.get("AFTER", {}).items():
                expected_after = journal["AFTER_SHA256"].get(name)
                if sha256_bytes(canonical_json_bytes(value)) != expected_after:
                    raise ControlError(f"recovery payload digest mismatch: {name}")
                current = file_digest(self.root / name) if (self.root / name).exists() else None
                if current not in {journal["BEFORE_SHA256"].get(name), expected_after}:
                    raise ControlError(f"authority changed outside interrupted transaction: {name}")
            for name, value in journal["AFTER"].items():
                if not (self.root / name).exists() or file_digest(self.root / name) != journal["AFTER_SHA256"][name]:
                    atomic_write_json(self.root / name, value)
            queue = load_json(self.queue_path); ledger = load_json(self.ledger_path); slot = load_json(self.slot_path)
            self._validate_values(queue, ledger, slot)
            matching = [event for event in ledger["EVENTS"] if event.get("TRANSACTION_ID") == journal["TRANSACTION_ID"]]
            if len(matching) != 1:
                raise ControlError("recovered transaction is not represented exactly once in ledger")
            self._clear_journal()
            return {"STATUS": "RECOVERED_COMMITTED", "TRANSACTION_ID": journal["TRANSACTION_ID"]}


class DeltaClassifier:
    def __init__(self, definition_path: os.PathLike[str] | str | None = None):
        self.definition_path = Path(definition_path or REFERENCE_DIR / "delta-classifier-v1.json")
        self.definition = load_json(self.definition_path)
        self.categories = tuple(self.definition["categories"])
        if len(self.categories) != 12 or len(set(self.categories)) != 12 or self.categories[-1] != "UNKNOWN":
            raise ControlError("delta classifier must contain the exact 12 unique categories")
        rule_categories = [rule["category"] for rule in self.definition["rules"]]
        if set(rule_categories) != set(self.categories) - {"UNKNOWN"}:
            raise ControlError("classifier rules do not cover every non-UNKNOWN category exactly")

    @staticmethod
    def _valid_path(path: str) -> bool:
        if not path or "\x00" in path or "\\" in path:
            return False
        pure = PurePosixPath(path)
        return not pure.is_absolute() and ".." not in pure.parts and path not in {".", "./"}

    @staticmethod
    def _matches(path: str, pattern: str) -> bool:
        return fnmatch.fnmatchcase(path, pattern) or PurePosixPath(path).match(pattern)

    def classify_path(self, path: str) -> list[str]:
        if not self._valid_path(path):
            return ["UNKNOWN"]
        matches = {
            rule["category"]
            for rule in self.definition["rules"]
            if any(self._matches(path, pattern) for pattern in rule["globs"])
        }
        if not matches:
            return ["UNKNOWN"]
        return [category for category in self.categories if category in matches]

    def classify_paths(self, paths: Iterable[str]) -> dict[str, list[str]]:
        values = list(paths)
        if not values:
            return {"": ["UNKNOWN"]}
        return {path: self.classify_path(path) for path in values}


class GateImpactMatrix:
    ALLOWED = {
        "REUSE_ALLOWED_IF_INPUT_UNCHANGED",
        "RERUN_REQUIRED",
        "NOT_APPLICABLE",
        "UNKNOWN_RERUN_REQUIRED",
    }

    def __init__(self, matrix_path: os.PathLike[str] | str | None = None):
        self.matrix_path = Path(matrix_path or REFERENCE_DIR / "gate-impact-matrix-v1.json")
        self.data = load_json(self.matrix_path)

    def validate(self) -> dict[str, Any]:
        categories = self.data["categories"]
        gates = self.data["gates"]
        matrix = self.data["matrix"]
        errors: list[str] = []
        if len(categories) != 12 or len(set(categories)) != 12:
            errors.append("category set is not exactly 12 unique values")
        if len(gates) != 17 or len(set(gates)) != 17:
            errors.append("gate set is not exactly 17 unique values")
        if set(matrix) != set(categories):
            errors.append("matrix categories have missing or extra rows")
        for category in categories:
            row = matrix.get(category, {})
            if set(row) != set(gates):
                errors.append(f"{category} has missing or extra gate cells")
            invalid = set(row.values()) - self.ALLOWED
            if invalid:
                errors.append(f"{category} has invalid values: {sorted(invalid)}")
            for gate in gates[:3]:
                if row.get(gate) != "RERUN_REQUIRED":
                    errors.append(f"{category}/{gate} must be RERUN_REQUIRED")
        unknown = matrix.get("UNKNOWN", {})
        for gate in gates[3:]:
            if unknown.get(gate) != "UNKNOWN_RERUN_REQUIRED":
                errors.append(f"UNKNOWN/{gate} must fail closed to rerun")
        if errors:
            raise ControlError("; ".join(errors))
        return {
            "GATE_IMPACT_MATRIX_COMPLETE": "YES",
            "CATEGORY_COUNT": len(categories),
            "GATE_COUNT": len(gates),
            "CELL_COUNT": sum(len(matrix[category]) for category in categories),
        }

    def impact(self, category: str, gate: str) -> str:
        self.validate()
        try:
            return self.data["matrix"][category][gate]
        except KeyError as exc:
            raise ControlError(f"unknown category or gate: {category}/{gate}") from exc


FINGERPRINT_GROUPS = (
    "included_paths",
    "included_globs",
    "relevant_build_config_files",
    "tests",
    "schemas_resources",
)


def _sorted_definition(definition: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(definition)
    for group in FINGERPRINT_GROUPS:
        normalized[group] = sorted(
            (dict(item) for item in definition.get(group, [])),
            key=lambda item: normalized_json_bytes(item),
        )
    return normalized


def compute_gate_fingerprint(
    gate_name: str,
    root: os.PathLike[str] | str,
    definitions_path: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    data = load_json(definitions_path or REFERENCE_DIR / "fingerprint-definitions-v1.json")
    definitions = data["definitions"]
    if set(definitions) != {
        "H7_POSTGRESQL_CONCURRENCY", "BACKEND_FULL_SERIAL", "H2_H1_BOUNDARY",
        "FORMAL_VERIFICATION", "FRONTEND_CI",
    }:
        raise ControlError("fingerprint pilot definitions are not the exact five gates")
    if gate_name not in definitions:
        raise ControlError(f"gate has no pilot fingerprint definition: {gate_name}")
    definition = _sorted_definition(definitions[gate_name])
    base = Path(root).resolve()
    selected: dict[str, str] = {}
    for group in FINGERPRINT_GROUPS:
        for item in definition[group]:
            key = "path" if "path" in item else "glob"
            expression = item[key]
            optional = item.get("optional", False)
            if key == "path":
                candidates = [base / expression] if (base / expression).is_file() else []
            else:
                candidates = [Path(value) for value in glob.glob(str(base / expression), recursive=True)]
                candidates = [candidate for candidate in candidates if candidate.is_file()]
            if not candidates and not optional:
                raise ControlError(f"missing required fingerprint input: {group}:{expression}")
            for candidate in candidates:
                resolved = candidate.resolve()
                try:
                    relative = resolved.relative_to(base).as_posix()
                except ValueError as exc:
                    raise ControlError("fingerprint input escapes root") from exc
                selected[relative] = file_digest(resolved)
    manifest = {
        "framework_version": data["version"],
        "gate_identifier": definition["gate_identifier"],
        "gate_version": definition["gate_version"],
        "definition": definition,
        "files": [{"path": path, "sha256": selected[path]} for path in sorted(selected)],
    }
    return {
        "GATE_NAME": gate_name,
        "ALGORITHM": "SHA-256",
        "INPUT_COUNT": len(selected),
        "NORMALIZED_MANIFEST": manifest,
        "INPUT_FINGERPRINT": sha256_bytes(normalized_json_bytes(manifest)),
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
    }


def validate_evidence(evidence: Mapping[str, Any]) -> None:
    required = {"EVIDENCE_CLASS", "GATE_NAME", "SUBJECT_SHA", "SUBJECT_TREE", "RESULT", "TIMESTAMP", "PROTOCOL_VERSION"}
    missing = required - set(evidence)
    if missing:
        raise ControlError(f"unclassified/incomplete evidence; missing {sorted(missing)}")
    if evidence["EVIDENCE_CLASS"] not in {"CANDIDATE_EVIDENCE", "INTEGRATION_EVIDENCE"}:
        raise ControlError("evidence must be classified as CANDIDATE_EVIDENCE or INTEGRATION_EVIDENCE")


def evidence_reuse_receipt(
    evidence: Mapping[str, Any],
    *,
    current_candidate_sha: str,
    current_candidate_tree: str,
    old_fingerprint: str | None = None,
    new_fingerprint: str | None = None,
    delta_classes: Sequence[str] = (),
    stale_merge: bool = False,
    explicit_input_closure_proof: bool = False,
    matrix: GateImpactMatrix | None = None,
) -> dict[str, Any]:
    validate_evidence(evidence)
    gate = str(evidence["GATE_NAME"])
    allowed = False
    level = "NONE"
    reason: str
    if evidence["EVIDENCE_CLASS"] == "CANDIDATE_EVIDENCE":
        allowed = evidence["SUBJECT_SHA"] == current_candidate_sha and evidence["SUBJECT_TREE"] == current_candidate_tree
        level = "FULL" if allowed else "NONE"
        reason = "unchanged candidate SHA/tree" if allowed else "candidate SHA/tree changed"
    elif stale_merge:
        reason = "stale merge object is never reusable or publishable"
    elif gate in load_json(REFERENCE_DIR / "protocol-v1.json")["always_fresh_integration_gates"]:
        reason = "always-fresh integration gate cannot reuse prior evidence"
    elif old_fingerprint and new_fingerprint and old_fingerprint == new_fingerprint:
        allowed = True
        level = "FULL"
        reason = "trustworthy deterministic input fingerprints are equal"
    elif explicit_input_closure_proof and delta_classes and "UNKNOWN" not in delta_classes and matrix is not None:
        impacts = [matrix.impact(category, gate) for category in delta_classes]
        allowed = all(value in {"REUSE_ALLOWED_IF_INPUT_UNCHANGED", "NOT_APPLICABLE"} for value in impacts)
        level = "PARTIAL" if allowed else "NONE"
        reason = "explicit conservative matrix/input-closure proof" if allowed else "matrix requires rerun"
    else:
        reason = "no trustworthy equal fingerprint or conservative input-closure proof"
    return {
        "GATE_NAME": gate,
        "PREVIOUS_EVIDENCE_SOURCE": evidence.get("EVIDENCE_SOURCE", "INLINE"),
        "PREVIOUS_INTEGRATION_OR_CANDIDATE_SHA": evidence["SUBJECT_SHA"],
        "OLD_INPUT_FINGERPRINT_IF_AVAILABLE": old_fingerprint,
        "NEW_INPUT_FINGERPRINT_IF_AVAILABLE": new_fingerprint,
        "DELTA_CLASSES": list(delta_classes),
        "REUSE_REASON": reason,
        "REUSE_DECISION": "ALLOWED" if allowed else "DENIED",
        "REUSE_LEVEL": level,
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
    }


class QueueControl:
    REQUIRED_FIELDS = {
        "QUEUE_ENTRY_ID", "LANE_ID", "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA", "CANDIDATE_TREE",
        "CURRENT_STATE", "DEPENDENCIES", "READY_TIMESTAMP", "PUBLICATION_PRIORITY", "SLOT_HOLDER",
        "CANONICAL_PARENT_1", "INTEGRATION_SHA", "INTEGRATION_TREE", "INDEPENDENT_REVIEW_STATUS",
        "PUBLICATION_STATUS", "FAILURE_REASON",
    }

    def __init__(self, queue_path: os.PathLike[str] | str, protocol_path: os.PathLike[str] | str | None = None):
        self.queue_path = Path(queue_path)
        self.state_root = self.queue_path.parent
        self.transaction = StateTransaction(self.state_root)
        protocol = load_json(protocol_path or REFERENCE_DIR / "protocol-v1.json")
        self.states = tuple(protocol["states"])
        self.transitions = protocol["transitions"]

    def load(self) -> dict[str, Any]:
        data, _, _ = self.transaction.read()
        entries = data.get("ENTRIES", [])
        ids: set[str] = set()
        for entry in entries:
            missing = self.REQUIRED_FIELDS - set(entry)
            if missing:
                raise ControlError(f"queue entry missing fields: {sorted(missing)}")
            if entry["CURRENT_STATE"] not in self.states:
                raise ControlError(f"queue entry has illegal state: {entry['CURRENT_STATE']}")
            if entry["QUEUE_ENTRY_ID"] in ids:
                raise ControlError("duplicate queue entry ID")
            ids.add(entry["QUEUE_ENTRY_ID"])
        return data

    def get(self, entry_id: str) -> dict[str, Any]:
        for entry in self.load()["ENTRIES"]:
            if entry["QUEUE_ENTRY_ID"] == entry_id:
                return entry
        raise ControlError(f"unknown queue entry: {entry_id}")

    @staticmethod
    def dependencies_resolved(entry: Mapping[str, Any]) -> bool:
        return all(dep.get("STATUS") == "RESOLVED" for dep in entry["DEPENDENCIES"])

    def transition(
        self,
        entry_id: str,
        new_state: str,
        *,
        actor: str,
        candidate_sha: str | None = None,
        candidate_tree: str | None = None,
    ) -> dict[str, Any]:
        timestamp = utc_now()
        body = {"QUEUE_ENTRY_ID": entry_id, "TO": new_state, "CANDIDATE_SHA": candidate_sha, "CANDIDATE_TREE": candidate_tree}
        changed: dict[str, Any] = {}

        def mutate(data: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = next((item for item in data["ENTRIES"] if item["QUEUE_ENTRY_ID"] == entry_id), None)
            if entry is None:
                raise ControlError(f"unknown queue entry: {entry_id}")
            old_state = entry["CURRENT_STATE"]
            policy = load_json(REFERENCE_DIR / "protocol-v1.json").get("ep19_successor", {})
            if entry_id == policy.get("successor_id") and new_state in {
                "SLOT_ACQUIRED", "INTEGRATING", "VALIDATING_INTEGRATION", "FROZEN_FOR_REVIEW",
                "INDEPENDENT_REVIEW", "APPROVED_FOR_PUBLICATION", "PUBLISHING", "CANONICAL",
            }:
                raise ControlError("EP19 controlled transition requires its dedicated original consumer")
            proposed_sha = candidate_sha or entry["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"]
            proposed_tree = candidate_tree or entry["CANDIDATE_TREE"]
            if old_state != "ENGINEERING" and (proposed_sha != entry["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"] or proposed_tree != entry["CANDIDATE_TREE"]):
                raise ControlError("candidate SHA/tree mutation after prevalidation is denied")
            if new_state not in self.transitions.get(old_state, []):
                raise ControlError(f"illegal queue transition: {old_state} -> {new_state}")
            if new_state in {"QUEUED", "SLOT_ACQUIRED"} and not self.dependencies_resolved(entry):
                raise ControlError("unresolved dependencies prohibit queueing or slot acquisition")
            entry["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"] = proposed_sha
            entry["CANDIDATE_TREE"] = proposed_tree
            entry["CURRENT_STATE"] = new_state
            entry["LAST_TRANSITION"] = {"FROM": old_state, "TO": new_state, "ACTOR": actor, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
            changed.update(copy.deepcopy(entry))

        self.transaction.commit(
            operation="QUEUE_TRANSITION", idempotency_key=f"queue-{os.urandom(16).hex()}", actor=actor,
            timestamp=timestamp, body=body, mutate=mutate,
        )
        return changed

    def record_independent_review(
        self, entry_id: str, *, evidence: Mapping[str, Any], actor: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        review, review_sha = verified_json_reference(evidence, "independent publication review")
        _require_exact(review, {"schema": "canonical-publication-independent-review-v1", "decision": "APPROVED", "reviewer_role": "INDEPENDENT_PUBLICATION_REVIEWER"}, "independent publication review")
        if review.get("reviewer_actor") != actor:
            raise ControlError("independent publication reviewer actor mismatch")
        changed: dict[str, Any] = {}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == entry_id), None)
            if entry is None or entry.get("CURRENT_STATE") != "INDEPENDENT_REVIEW":
                raise ControlError("independent approval requires INDEPENDENT_REVIEW state")
            _require_exact(review, {
                "candidate": entry["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"], "tree": entry["CANDIDATE_TREE"],
                "integration_sha": entry["INTEGRATION_SHA"], "integration_tree": entry["INTEGRATION_TREE"],
            }, "independent publication review")
            entry["INDEPENDENT_REVIEW_STATUS"] = "APPROVED"
            entry["CURRENT_STATE"] = "APPROVED_FOR_PUBLICATION"
            entry["INDEPENDENT_REVIEW_EVIDENCE"] = {**dict(evidence), "VERIFIED_SHA256": review_sha}
            entry["LAST_TRANSITION"] = {"FROM": "INDEPENDENT_REVIEW", "TO": "APPROVED_FOR_PUBLICATION", "ACTOR": actor, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
            changed.update(copy.deepcopy(entry))
        self.transaction.commit(operation="INDEPENDENT_PUBLICATION_REVIEW_APPROVED", idempotency_key=f"independent-review-{review_sha}", actor=actor, timestamp=timestamp, body={"QUEUE_ENTRY_ID": entry_id, "EVIDENCE_SHA256": review_sha}, mutate=mutate, expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)
        return changed


class SlotControl:
    def __init__(self, state_root: os.PathLike[str] | str):
        self.state_root = Path(state_root)
        self.slot_path = self.state_root / "slot.json"
        self.lock_path = self.state_root / ".canonical-publication-slot.lock"
        self.transaction = StateTransaction(self.state_root)

    @contextlib.contextmanager
    def _mutex(self) -> Iterator[None]:
        self.state_root.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def load(self) -> dict[str, Any]:
        _, _, slot = self.transaction.read()
        if slot is None:
            raise ControlError("slot authority is absent")
        return slot

    def acquire(self, owner: str, entry: Mapping[str, Any], fresh_canonical_main: str) -> dict[str, Any]:
        queue_entry_id = entry.get("QUEUE_ENTRY_ID")
        candidate_sha = entry.get("EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA")
        candidate_tree = entry.get("CANDIDATE_TREE")
        if not owner or not queue_entry_id or not candidate_sha or not candidate_tree or not fresh_canonical_main:
            raise ControlError("slot acquisition fields must be non-empty")
        if entry.get("CURRENT_STATE") != "QUEUED":
            raise ControlError("slot acquisition requires a QUEUED entry")
        if not QueueControl.dependencies_resolved(entry):
            raise ControlError("unresolved dependencies prohibit slot acquisition")
        timestamp = utc_now()
        changed: dict[str, Any] = {}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], state: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            if state is None:
                raise ControlError("slot authority is absent")
            authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == queue_entry_id), None)
            if authoritative is None or authoritative.get("CURRENT_STATE") != "QUEUED":
                raise ControlError("slot acquisition requires the authoritative QUEUED entry")
            if authoritative.get("EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA") != candidate_sha or authoritative.get("CANDIDATE_TREE") != candidate_tree:
                raise ControlError("caller entry differs from authoritative queue identity")
            if not QueueControl.dependencies_resolved(authoritative):
                raise ControlError("unresolved dependencies prohibit slot acquisition")
            if state["STATUS"] != "AVAILABLE" or state.get("HOLDER") is not None:
                raise ControlError("publication slot already has a holder")
            state.update({
                "STATUS": "HELD", "HOLDER": owner, "QUEUE_ENTRY_ID": queue_entry_id,
                "CANDIDATE_SHA": candidate_sha, "CANDIDATE_TREE": candidate_tree,
                "FRESH_CANONICAL_MAIN": fresh_canonical_main, "ACQUIRED_AT": timestamp,
                "FROZEN_INTEGRATION_SHA": None, "FROZEN_INTEGRATION_TREE": None,
                "FROZEN_PARENT_1": None, "FROZEN_PARENT_2": None, "FROZEN_AT": None,
                "RELEASED_AT": None, "RELEASE_REASON": None,
            })
            authoritative["CURRENT_STATE"] = "SLOT_ACQUIRED"
            authoritative["SLOT_HOLDER"] = owner
            authoritative["CANONICAL_PARENT_1"] = fresh_canonical_main
            authoritative["LAST_TRANSITION"] = {"FROM": "QUEUED", "TO": "SLOT_ACQUIRED", "ACTOR": owner, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
            changed.update(copy.deepcopy(state))
        with self._mutex():
            self.transaction.commit(operation="ACQUIRE_PUBLICATION_SLOT", idempotency_key=f"slot-acquire-{os.urandom(16).hex()}", actor=owner, timestamp=timestamp, body={"QUEUE_ENTRY_ID": queue_entry_id, "FRESH_MAIN": fresh_canonical_main}, mutate=mutate)
        return changed

    def require_holder(self, owner: str, queue_entry_id: str | None = None) -> dict[str, Any]:
        state = self.load()
        if state["STATUS"] != "HELD" or state.get("HOLDER") != owner:
            raise ControlError("operation denied: actor is not publication slot holder")
        if queue_entry_id is not None and state.get("QUEUE_ENTRY_ID") != queue_entry_id:
            raise ControlError("operation denied: slot is bound to another queue entry")
        return state

    def assert_retained_for_review(self, owner: str, queue_entry_id: str, queue_state: str) -> None:
        if queue_state in {"FROZEN_FOR_REVIEW", "INDEPENDENT_REVIEW", "APPROVED_FOR_PUBLICATION", "PUBLISHING"}:
            self.require_holder(owner, queue_entry_id)

    def freeze_integration(
        self,
        *,
        owner: str,
        entry: Mapping[str, Any],
        integration_sha: str,
        integration_tree: str,
        parent_1: str,
        parent_2: str,
        always_fresh_gate_results: Mapping[str, str],
    ) -> dict[str, Any]:
        if entry.get("CURRENT_STATE") != "VALIDATING_INTEGRATION":
            raise ControlError("integration freeze requires VALIDATING_INTEGRATION state")
        if not integration_sha or not integration_tree:
            raise ControlError("integration SHA/tree must be explicit")
        all_fresh_gates = set(load_json(REFERENCE_DIR / "protocol-v1.json")["always_fresh_integration_gates"])
        # Remote readbacks occur only after local freeze and review-ref publication.
        # Requiring them here creates an impossible/false pre-review dependency.
        required_gates = all_fresh_gates - {"REMOTE_CANDIDATE_READBACK", "POST_PUBLICATION_MAIN_READBACK"}
        provided_gates = set(always_fresh_gate_results)
        if not required_gates.issubset(provided_gates) or not provided_gates.issubset(all_fresh_gates):
            raise ControlError("pre-freeze always-fresh gate result set is incomplete or has extras")
        failed = sorted(gate for gate, result in always_fresh_gate_results.items() if result != "PASS")
        if failed:
            raise ControlError(f"always-fresh integration gates did not pass: {failed}")
        timestamp = utc_now()
        changed: dict[str, Any] = {}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], state: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            if state is None or state.get("STATUS") != "HELD" or state.get("HOLDER") != owner or state.get("QUEUE_ENTRY_ID") != entry.get("QUEUE_ENTRY_ID"):
                raise ControlError("operation denied: actor is not publication slot holder")
            authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == entry.get("QUEUE_ENTRY_ID")), None)
            if authoritative is None or authoritative.get("CURRENT_STATE") != "VALIDATING_INTEGRATION":
                raise ControlError("integration freeze requires authoritative VALIDATING_INTEGRATION state")
            if parent_1 != state["FRESH_CANONICAL_MAIN"]:
                raise ControlError("Parent 1 does not equal slot-acquisition fresh main")
            if parent_2 != state["CANDIDATE_SHA"]:
                raise ControlError("Parent 2 does not equal slot-bound exact candidate")
            state.update({
                "FROZEN_INTEGRATION_SHA": integration_sha,
                "FROZEN_INTEGRATION_TREE": integration_tree,
                "FROZEN_PARENT_1": parent_1,
                "FROZEN_PARENT_2": parent_2,
                "FROZEN_AT": timestamp,
            })
            authoritative["CURRENT_STATE"] = "FROZEN_FOR_REVIEW"
            authoritative["INTEGRATION_SHA"] = integration_sha
            authoritative["INTEGRATION_TREE"] = integration_tree
            authoritative["CANONICAL_PARENT_1"] = parent_1
            authoritative["LAST_TRANSITION"] = {"FROM": "VALIDATING_INTEGRATION", "TO": "FROZEN_FOR_REVIEW", "ACTOR": owner, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
            changed.update(copy.deepcopy(state))
        with self._mutex():
            self.transaction.commit(operation="FREEZE_INTEGRATION", idempotency_key=f"freeze-{os.urandom(16).hex()}", actor=owner, timestamp=timestamp, body={"QUEUE_ENTRY_ID": entry.get("QUEUE_ENTRY_ID"), "INTEGRATION_SHA": integration_sha, "INTEGRATION_TREE": integration_tree, "PARENT_1": parent_1, "PARENT_2": parent_2}, mutate=mutate)
        return changed

    def release(self, owner: str, *, outcome: str, queue_state: str) -> dict[str, Any]:
        if outcome not in {"PUBLICATION_SUCCESS", "EXPLICIT_FAIL_CLOSED_RELEASE"}:
            raise ControlError("slot release requires publication success or explicit fail-closed release")
        timestamp = utc_now()
        changed: dict[str, Any] = {}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], state: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            if state is None or state.get("STATUS") != "HELD" or state.get("HOLDER") != owner:
                raise ControlError("operation denied: actor is not publication slot holder")
            previous = {"HOLDER": state["HOLDER"], "QUEUE_ENTRY_ID": state["QUEUE_ENTRY_ID"]}
            state.update({
                "STATUS": "AVAILABLE", "HOLDER": None, "QUEUE_ENTRY_ID": None,
                "CANDIDATE_SHA": None, "CANDIDATE_TREE": None,
                "FROZEN_INTEGRATION_SHA": None, "FROZEN_INTEGRATION_TREE": None,
                "FROZEN_PARENT_1": None, "FROZEN_PARENT_2": None, "FROZEN_AT": None,
                "FRESH_CANONICAL_MAIN": None, "RELEASED_AT": timestamp, "RELEASE_REASON": outcome,
                "PREVIOUS_HOLDER": previous["HOLDER"], "PREVIOUS_QUEUE_ENTRY_ID": previous["QUEUE_ENTRY_ID"],
            })
            changed.update(copy.deepcopy(state))
        with self._mutex():
            self.transaction.commit(operation="RELEASE_PUBLICATION_SLOT", idempotency_key=f"slot-release-{os.urandom(16).hex()}", actor=owner, timestamp=timestamp, body={"OUTCOME": outcome, "QUEUE_STATE": queue_state}, mutate=mutate)
        return changed

    def authorize_publication(
        self,
        *,
        owner: str,
        entry: Mapping[str, Any],
        current_observed_main: str,
        exact_parent_1: str,
        exact_parent_2: str,
        force_push: bool = False,
        history_rewrite: bool = False,
        receipt_path: os.PathLike[str] | str | None = None,
    ) -> dict[str, Any]:
        if force_push:
            raise ControlError("force push is forbidden")
        if history_rewrite:
            raise ControlError("history rewrite is forbidden")
        with self._mutex():
            with self.transaction.mutex():
                queue, _, slot = self.transaction._read_locked()
                if slot is None or slot.get("STATUS") != "HELD" or slot.get("HOLDER") != owner or slot.get("QUEUE_ENTRY_ID") != entry.get("QUEUE_ENTRY_ID"):
                    raise ControlError("operation denied: actor is not publication slot holder")
                authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == entry.get("QUEUE_ENTRY_ID")), None)
                if authoritative is None or authoritative["CURRENT_STATE"] != "APPROVED_FOR_PUBLICATION":
                    raise ControlError("entry is not approved for publication")
                if authoritative.get("INDEPENDENT_REVIEW_STATUS") != "APPROVED":
                    raise ControlError("independent review has not approved the frozen integration")
                required_values = [authoritative["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"], authoritative["CANDIDATE_TREE"], authoritative["CANONICAL_PARENT_1"], authoritative["INTEGRATION_SHA"], authoritative["INTEGRATION_TREE"]]
                if not all(required_values):
                    raise ControlError("publication identity is incomplete")
                if authoritative["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"] != slot.get("CANDIDATE_SHA") or authoritative["CANDIDATE_TREE"] != slot.get("CANDIDATE_TREE"):
                    raise ControlError("candidate SHA/tree differs from slot-acquisition identity")
                if authoritative["INTEGRATION_SHA"] != slot.get("FROZEN_INTEGRATION_SHA") or authoritative["INTEGRATION_TREE"] != slot.get("FROZEN_INTEGRATION_TREE"):
                    raise ControlError("integration SHA/tree differs from frozen slot identity")
                if current_observed_main != slot["FRESH_CANONICAL_MAIN"] or exact_parent_1 != slot["FRESH_CANONICAL_MAIN"]:
                    raise ControlError("Parent 1/current main differs from slot-acquisition fresh main")
                if authoritative["CANONICAL_PARENT_1"] != exact_parent_1:
                    raise ControlError("entry canonical Parent 1 differs from exact Parent 1")
                if exact_parent_2 != authoritative["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"]:
                    raise ControlError("Parent 2 differs from exact accepted lane candidate")
                if exact_parent_1 != slot.get("FROZEN_PARENT_1") or exact_parent_2 != slot.get("FROZEN_PARENT_2"):
                    raise ControlError("ordered parents differ from the frozen integration")
                receipt = {
                    "OWNER": owner, "QUEUE_ENTRY_ID": authoritative["QUEUE_ENTRY_ID"],
                    "CANDIDATE_SHA": authoritative["EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA"], "CANDIDATE_TREE": authoritative["CANDIDATE_TREE"],
                    "FRESH_CANONICAL_PARENT_1": slot["FRESH_CANONICAL_MAIN"], "INTEGRATION_SHA": authoritative["INTEGRATION_SHA"],
                    "INTEGRATION_TREE": authoritative["INTEGRATION_TREE"], "EXACT_PARENT_1": exact_parent_1,
                    "EXACT_PARENT_2": exact_parent_2, "CURRENT_OBSERVED_MAIN": current_observed_main,
                    "TIMESTAMP": utc_now(), "PROTOCOL_VERSION": PROTOCOL_VERSION,
                    "AUTHORIZATION": "EXACT_NORMAL_PUBLICATION_ONLY", "FORCE_PUSH": False,
                    "HISTORY_REWRITE": False, "GIT_PUBLICATION_PERFORMED": False,
                }
                if receipt_path is not None:
                    immutable_write_json(receipt_path, receipt)
                return receipt

    def authorize_ep19_direct_ff(
        self,
        *,
        owner: str,
        entry: Mapping[str, Any],
        ancestry_evidence: Mapping[str, Any],
        race_evidence: Mapping[str, Any],
        remote_evidence: Mapping[str, Any],
        idempotency_key: str,
        timestamp: str,
        expected_queue_sha256: str,
        expected_ledger_sha256: str,
        receipt_path: os.PathLike[str] | str | None = None,
    ) -> dict[str, Any]:
        """Authorize only the Owner-bound a298 direct fast-forward exception."""
        policy = load_json(REFERENCE_DIR / "protocol-v1.json")["ep19_successor"]
        if (entry.get("QUEUE_ENTRY_ID") != policy["successor_id"]
                or entry.get("EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA") != policy["candidate"]
                or entry.get("CANDIDATE_TREE") != policy["tree"]):
            raise ControlError("direct-FF caller entry differs from the exact authorized target")
        ancestry, ancestry_sha = verified_json_reference(ancestry_evidence, "fresh-main ancestry evidence")
        race, race_sha = verified_json_reference(race_evidence, "final main race evidence")
        remote, remote_sha = verified_json_reference(remote_evidence, "remote candidate evidence")
        _require_exact(ancestry, {
            "schema": "ep19-fresh-main-ancestry-v1", "result": "PASS", "native_exit_code": 0,
            "candidate": policy["candidate"], "candidate_tree": policy["tree"], "is_ancestor": True, "actor": owner,
        }, "fresh-main ancestry evidence")
        fresh_main = ancestry.get("fresh_main")
        if not _is_lower_hex(fresh_main, 40):
            raise ControlError("fresh-main ancestry evidence has invalid fresh_main")
        _require_exact(race, {
            "schema": "ep19-final-main-race-check-v1", "result": "PASS", "native_exit_code": 0,
            "observed_main": fresh_main, "no_race": True, "actor": owner,
        }, "final main race evidence")
        _require_exact(remote, {
            "schema": "ep19-remote-candidate-readback-v1", "result": "PASS", "native_exit_code": 0,
            "candidate": policy["candidate"], "candidate_tree": policy["tree"], "actor": owner,
        }, "remote candidate evidence")
        evidence_source = ancestry.get("executor_sha256")
        if not _is_lower_hex(evidence_source, 64) or race.get("executor_sha256") != evidence_source or remote.get("executor_sha256") != evidence_source:
            raise ControlError("direct-FF native evidence producer identity is missing or mixed")
        for value, name in ((ancestry, "fresh-main ancestry"), (race, "final main race"),
                            (remote, "remote candidate readback")):
            verify_native_provenance(value, name, candidate=policy["candidate"], tree=policy["tree"],
                attempt_id=policy["publication_attempt_id"], source_sha256=evidence_source, actor=owner)
        receipt = {
            "OWNER": owner, "QUEUE_ENTRY_ID": policy["successor_id"],
            "CANDIDATE_SHA": policy["candidate"], "CANDIDATE_TREE": policy["tree"],
            "FRESH_CANONICAL_MAIN": fresh_main, "CURRENT_OBSERVED_MAIN": race["observed_main"],
            "ANCESTRY_EVIDENCE_SHA256": ancestry_sha, "RACE_EVIDENCE_SHA256": race_sha,
            "REMOTE_CANDIDATE_EVIDENCE_SHA256": remote_sha, "TIMESTAMP": timestamp,
            "PROTOCOL_VERSION": PROTOCOL_VERSION,
            "AUTHORIZATION": policy["direct_ff_authorization"],
            "FORCE_PUSH": False, "HISTORY_REWRITE": False, "GIT_PUBLICATION_PERFORMED": False,
        }
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            if slot is None or slot.get("STATUS") != "HELD" or slot.get("HOLDER") != owner or slot.get("QUEUE_ENTRY_ID") != policy["successor_id"]:
                raise ControlError("direct-FF denied: actor is not the exact publication slot holder")
            authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == policy["successor_id"]), None)
            if authoritative is None or authoritative.get("CURRENT_STATE") != "APPROVED_FOR_PUBLICATION":
                raise ControlError("direct-FF requires the authoritative APPROVED_FOR_PUBLICATION successor")
            if authoritative.get("INDEPENDENT_REVIEW_STATUS") != "APPROVED":
                raise ControlError("direct-FF independent engineering acceptance is absent")
            if authoritative.get("EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA") != policy["candidate"] or authoritative.get("CANDIDATE_TREE") != policy["tree"]:
                raise ControlError("direct-FF exception is not bound to exact a298 identity")
            if authoritative.get("IMPLEMENTATION_SHA256") != evidence_source:
                raise ControlError("direct-FF evidence was not produced by the admitted executor source")
            if slot.get("CANDIDATE_SHA") != policy["candidate"] or slot.get("CANDIDATE_TREE") != policy["tree"]:
                raise ControlError("direct-FF slot identity differs from exact a298 identity")
            if slot.get("FRESH_CANONICAL_MAIN") != fresh_main:
                raise ControlError("fresh ancestry/race evidence differs from slot-acquisition main")
            authoritative["CURRENT_STATE"] = "PUBLISHING"
            authoritative["PUBLICATION_STATUS"] = "AUTHORIZED_DIRECT_FAST_FORWARD"
            authoritative["PUBLICATION_AUTHORIZATION"] = copy.deepcopy(receipt)
            authoritative["LAST_TRANSITION"] = {"FROM": "APPROVED_FOR_PUBLICATION", "TO": "PUBLISHING", "ACTOR": owner, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
        with self._mutex():
            result = self.transaction.commit(
                operation="AUTHORIZE_EP19_DIRECT_FF", idempotency_key=idempotency_key, actor=owner,
                timestamp=timestamp, body=receipt, mutate=mutate,
                expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256,
            )
        if receipt_path is not None:
            immutable_write_json(receipt_path, receipt)
        return {**result, "RECEIPT": receipt}

    def prepare_ep19_direct_ff(
        self, *, owner: str, entry: Mapping[str, Any], idempotency_key: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        """Apply the exact exception ordering after engineering acceptance and slot acquisition."""
        policy = load_json(REFERENCE_DIR / "protocol-v1.json")["ep19_successor"]
        if (entry.get("QUEUE_ENTRY_ID") != policy["successor_id"]
                or entry.get("EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA") != policy["candidate"]
                or entry.get("CANDIDATE_TREE") != policy["tree"]):
            raise ControlError("direct-FF preparation caller entry differs from exact a298 target")
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any], transaction_id: str, payload_digest: str) -> None:
            authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == policy["successor_id"]), None)
            if (authoritative is None or authoritative.get("CURRENT_STATE") != "SLOT_ACQUIRED"
                    or authoritative.get("INDEPENDENT_REVIEW_STATUS") != "APPROVED"
                    or not QueueControl.dependencies_resolved(authoritative)):
                raise ControlError("direct-FF preparation requires accepted engineering evidence and SLOT_ACQUIRED")
            if (slot.get("STATUS") != "HELD" or slot.get("HOLDER") != owner
                    or slot.get("QUEUE_ENTRY_ID") != policy["successor_id"]
                    or slot.get("CANDIDATE_SHA") != policy["candidate"]
                    or slot.get("CANDIDATE_TREE") != policy["tree"]):
                raise ControlError("direct-FF preparation requires the exact held original slot")
            authoritative["CURRENT_STATE"] = "APPROVED_FOR_PUBLICATION"
            authoritative["DIRECT_FF_ORDERING"] = "ENGINEERING_ACCEPTED_THEN_SLOT_THEN_FRESH_EVIDENCE"
            authoritative["LAST_TRANSITION"] = {"FROM": "SLOT_ACQUIRED", "TO": "APPROVED_FOR_PUBLICATION",
                "ACTOR": owner, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
        with self._mutex():
            return self.transaction.commit(operation="PREPARE_EP19_DIRECT_FF", idempotency_key=idempotency_key,
                actor=owner, timestamp=timestamp, body={"QUEUE_ENTRY_ID": policy["successor_id"],
                "CANDIDATE": policy["candidate"]}, mutate=mutate,
                expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)

    def record_ep19_publication_result(
        self,
        *,
        owner: str,
        canonical_readback_evidence: Mapping[str, Any],
        idempotency_key: str,
        timestamp: str,
        expected_queue_sha256: str,
        expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        policy = load_json(REFERENCE_DIR / "protocol-v1.json")["ep19_successor"]
        readback, readback_sha = verified_json_reference(canonical_readback_evidence, "canonical readback evidence")
        _require_exact(readback, {
            "schema": "ep19-canonical-main-readback-v1", "result": "PASS", "native_exit_code": 0,
            "candidate": policy["candidate"], "candidate_tree": policy["tree"], "actor": owner,
        }, "canonical readback evidence")
        evidence_source = readback.get("executor_sha256")
        if not _is_lower_hex(evidence_source, 64):
            raise ControlError("canonical readback executor source identity is absent")
        verify_native_provenance(readback, "canonical main readback", candidate=policy["candidate"],
            tree=policy["tree"], attempt_id=policy["publication_attempt_id"],
            source_sha256=evidence_source, actor=owner)
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            if slot is None or slot.get("STATUS") != "HELD" or slot.get("HOLDER") != owner or slot.get("QUEUE_ENTRY_ID") != policy["successor_id"]:
                raise ControlError("publication result denied: actor is not slot holder")
            authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == policy["successor_id"]), None)
            if authoritative is None or authoritative.get("CURRENT_STATE") != "PUBLISHING" or authoritative.get("PUBLICATION_STATUS") != "AUTHORIZED_DIRECT_FAST_FORWARD":
                raise ControlError("publication result requires the authorized direct-FF PUBLISHING state")
            if authoritative.get("IMPLEMENTATION_SHA256") != evidence_source:
                raise ControlError("canonical readback was not produced by the admitted executor source")
            authoritative["CURRENT_STATE"] = "CANONICAL"
            authoritative["PUBLICATION_STATUS"] = "PUBLISHED"
            authoritative["CANONICAL_READBACK_EVIDENCE"] = {**dict(canonical_readback_evidence), "VERIFIED_SHA256": readback_sha}
            authoritative["LAST_TRANSITION"] = {"FROM": "PUBLISHING", "TO": "CANONICAL", "ACTOR": owner, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
        with self._mutex():
            return self.transaction.commit(
                operation="RECORD_EP19_PUBLICATION_RESULT", idempotency_key=idempotency_key, actor=owner,
                timestamp=timestamp, body={"READBACK_SHA256": readback_sha, "CANDIDATE": policy["candidate"]}, mutate=mutate,
                expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256,
            )

    def identity_readback(
        self,
        *,
        owner: str,
        entry: Mapping[str, Any],
        gate_name: str,
        observed_sha: str,
        receipt_path: os.PathLike[str] | str | None = None,
    ) -> dict[str, Any]:
        if gate_name not in {"REMOTE_CANDIDATE_READBACK", "POST_PUBLICATION_MAIN_READBACK"}:
            raise ControlError("unsupported identity readback gate")
        with self._mutex():
            with self.transaction.mutex():
                queue, _, slot = self.transaction._read_locked()
                authoritative = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == entry.get("QUEUE_ENTRY_ID")), None)
                if (authoritative is None or slot.get("STATUS") != "HELD" or slot.get("HOLDER") != owner
                        or slot.get("QUEUE_ENTRY_ID") != entry.get("QUEUE_ENTRY_ID")):
                    raise ControlError("identity readback lost its slot/entry authorization")
                expected = slot.get("FROZEN_INTEGRATION_SHA")
                if not expected or observed_sha != expected:
                    raise ControlError(f"{gate_name} observed identity differs from expected identity")
                receipt = {
            "RECEIPT_TYPE": "REMOTE_IDENTITY_READBACK_V1",
            "GATE_NAME": gate_name,
            "OWNER": owner,
            "QUEUE_ENTRY_ID": entry["QUEUE_ENTRY_ID"],
            "CANDIDATE_SHA": slot["CANDIDATE_SHA"],
            "CANDIDATE_TREE": slot["CANDIDATE_TREE"],
            "FRESH_CANONICAL_PARENT_1": slot["FRESH_CANONICAL_MAIN"],
            "INTEGRATION_SHA": slot.get("FROZEN_INTEGRATION_SHA"),
            "INTEGRATION_TREE": slot.get("FROZEN_INTEGRATION_TREE"),
            "EXPECTED_SHA": expected,
            "OBSERVED_SHA": observed_sha,
            "RESULT": "PASS",
            "TIMESTAMP": utc_now(),
            "PROTOCOL_VERSION": PROTOCOL_VERSION,
            "GIT_OPERATION_PERFORMED": False,
                }
        if receipt_path is not None:
            immutable_write_json(receipt_path, receipt)
        return receipt


class EP19AcceptanceControl:
    """EP19 acceptance consumer integrated into the original authority domain."""

    def __init__(self, state_root: os.PathLike[str] | str):
        self.root = Path(state_root)
        self.transaction = StateTransaction(self.root)
        self.policy = load_json(REFERENCE_DIR / "protocol-v1.json")["ep19_successor"]

    def _successor(self, queue: Mapping[str, Any]) -> dict[str, Any]:
        entry = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == self.policy["successor_id"]), None)
        if entry is None:
            raise ControlError("EP19 successor is absent")
        return entry

    def inspect(self) -> dict[str, Any]:
        with self.transaction.mutex():
            queue, ledger, slot = self.transaction._read_locked()
            entry = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == self.policy["successor_id"]), None)
            transaction_id = entry.get("LAST_TRANSITION", {}).get("TRANSACTION_ID") if entry else None
            return {
                "schema": "ep19-original-controller-admission-readback-v1",
                "result": "PASS" if entry is not None else "NOT_READY",
                "candidate": self.policy["candidate"], "tree": self.policy["tree"],
                "successor_id": self.policy["successor_id"], "controller_sha256": file_digest(__file__),
                "same_locked_snapshot": True,
                "queue_sha256": sha256_bytes(canonical_json_bytes(queue)),
                "ledger_sha256": sha256_bytes(canonical_json_bytes(ledger)),
                "slot_sha256": sha256_bytes(canonical_json_bytes(slot)),
                "transaction_id": transaction_id,
                "COMMITTED": entry is not None,
                "QUEUE_ENTRY_ID": self.policy["successor_id"],
                "CURRENT_STATE": entry.get("CURRENT_STATE") if entry else None,
                "QUEUE_SHA256": sha256_bytes(canonical_json_bytes(queue)),
                "LEDGER_SHA256": sha256_bytes(canonical_json_bytes(ledger)),
                "SLOT_SHA256": sha256_bytes(canonical_json_bytes(slot)),
                "SAME_LOCKED_SNAPSHOT": True,
                "STATE_TRANSACTION_SEQUENCE": queue.get("STATE_TRANSACTION_SEQUENCE", 0),
            }

    def _verify_identity(self, reference: Mapping[str, Any], name: str, schema: str) -> tuple[dict[str, Any], str]:
        value, digest = verified_json_reference(reference, name)
        _require_exact(value, {"schema": schema, "candidate": self.policy["candidate"]}, name)
        if "tree" in value and value["tree"] != self.policy["tree"]:
            raise ControlError(f"{name}.tree differs from exact candidate tree")
        return value, digest

    def _verify_admission(self, evidence: Mapping[str, Any]) -> tuple[dict[str, Any], str, dict[str, str]]:
        value, digest = verified_json_reference(evidence, "EP19 admission evidence")
        _require_exact(value, {
            "schema": "ep19-original-control-plane-admission-evidence-v1", "result": "PASS", "fixture_only": False,
            "successor_id": self.policy["successor_id"], "predecessor_id": self.policy["predecessor_id"],
            "authorization_id": self.policy["authorization_id"], "candidate": self.policy["candidate"],
            "tree": self.policy["tree"], "product_patch_sha256": self.policy["product_patch_sha256"],
            "historical_formal_consumed": self.policy["historical_formal_consumed"],
            "new_formal_total": self.policy["new_formal_total"], "new_formal_used": 0,
            "global_next_ordinal": self.policy["global_next_ordinal"], "successor_registered": False,
            "ledger_route_ready": True, "publication_route_ready": True, "dependencies_ready": True,
            "live_state_mutated_by_writer": False,
        }, "EP19 admission evidence")
        identities: dict[str, str] = {}
        for field, schema in (
            ("EXECUTOR_IDENTITY", "ep19-executor-identity-v1"),
            ("CONFIG_IDENTITY", "ep19-executor-config-v1"),
            ("POLICY_IDENTITY", "ep19-gate-policy-v1"),
        ):
            identity_value, _ = self._verify_identity(value.get(field, {}), field, schema)
            _, source_sha = verified_file_reference(identity_value.get("SOURCE", {}), f"{field} accepted source")
            verify_native_provenance(identity_value, field, candidate=self.policy["candidate"], tree=self.policy["tree"],
                attempt_id="PRECONSUMPTION_ADMISSION", source_sha256=source_sha)
            identities[field] = source_sha
        controller_sha = file_digest(__file__)
        if value.get("canonical_controller_sha256") != controller_sha:
            raise ControlError("admission does not bind the executing canonical controller bytes")
        if value.get("implementation_sha256") != identities["EXECUTOR_IDENTITY"]:
            raise ControlError("admission implementation_sha256 differs from verified executor source bytes")
        return value, digest, identities

    def register_successor(
        self, *, evidence: Mapping[str, Any], idempotency_key: str, actor: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str, fault: str | None = None,
    ) -> dict[str, Any]:
        admission, admission_sha, identities = self._verify_admission(evidence)
        body = {"ADMISSION_SHA256": admission_sha, "SUCCESSOR": self.policy["successor_id"], "CANDIDATE": self.policy["candidate"]}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            predecessor = next((item for item in queue["ENTRIES"] if item.get("QUEUE_ENTRY_ID") == self.policy["predecessor_id"]), None)
            if predecessor is None:
                raise ControlError("authorized EP19 predecessor is absent")
            _require_exact(predecessor, {
                "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "86d6aef94fd5e58da552e97c11473cff6eca734e",
                "CANDIDATE_TREE": "dba5e1e457af28cfca865e44f48eedabcc28aebb",
                "CURRENT_STATE": "RELEASED_FAILED",
                "PUBLICATION_STATUS": "PUBLISHED_POST_PUBLICATION_SANITY_BLOCKED",
            }, "EP19 predecessor")
            if any(item.get("QUEUE_ENTRY_ID") == self.policy["successor_id"] for item in queue["ENTRIES"]):
                raise ControlError("EP19 successor already exists under a different operation")
            entry = {
                "QUEUE_ENTRY_ID": self.policy["successor_id"], "LANE_ID": "ep19-entitlement-query-authority",
                "SUCCESSOR_OF_QUEUE_ENTRY_ID": self.policy["predecessor_id"], "AUTHORIZATION_ID": self.policy["authorization_id"],
                "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": self.policy["candidate"], "CANDIDATE_TREE": self.policy["tree"],
                "IMMEDIATE_PARENT_SHA": self.policy["immediate_parent"], "PATCH_SHA256": self.policy["product_patch_sha256"],
                "CURRENT_STATE": "PREVALIDATING", "DEPENDENCIES": [
                    {"NAME": "EXACT_29_GATE_FORMAL_ACCEPTANCE", "STATUS": "UNRESOLVED"},
                    {"NAME": "INDEPENDENT_ENGINEERING_ACCEPTANCE", "STATUS": "UNRESOLVED"},
                ],
                "READY_TIMESTAMP": None, "PUBLICATION_PRIORITY": 1, "SLOT_HOLDER": None,
                "CANONICAL_PARENT_1": None, "INTEGRATION_SHA": None, "INTEGRATION_TREE": None,
                "INDEPENDENT_REVIEW_STATUS": "NOT_STARTED", "PUBLICATION_STATUS": "NOT_AUTHORIZED", "FAILURE_REASON": None,
                "DIRECT_FAST_FORWARD_EXCEPTION": self.policy["direct_ff_authorization"],
                "FORMAL": {"HISTORICAL_CONSUMED": "2/2", "NEW_TOTAL": 1, "NEW_USED": 0, "GLOBAL_NEXT_ORDINAL": 3, "AUTO_RETRY": False, "USAGE_KNOWN": True},
                "EXECUTOR_IDENTITY": copy.deepcopy(admission["EXECUTOR_IDENTITY"]),
                "CONFIG_IDENTITY": copy.deepcopy(admission["CONFIG_IDENTITY"]),
                "POLICY_IDENTITY": copy.deepcopy(admission["POLICY_IDENTITY"]),
                "IMPLEMENTATION_SHA256": identities["EXECUTOR_IDENTITY"],
                "CANONICAL_CONTROLLER_SHA256": file_digest(__file__),
                "ADMISSION_EVIDENCE": {**dict(evidence), "VERIFIED_SHA256": admission_sha},
                "LAST_TRANSITION": {"FROM": "ABSENT_WITH_PREDECESSOR_RELEASED_FAILED", "TO": "PREVALIDATING", "ACTOR": actor, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id},
            }
            queue["ENTRIES"].append(entry)
        return self.transaction.commit(
            operation="REGISTER_EP19_SUCCESSOR", idempotency_key=idempotency_key, actor=actor,
            timestamp=timestamp, body=body, mutate=mutate, expected_queue_sha256=expected_queue_sha256,
            expected_ledger_sha256=expected_ledger_sha256, fault=fault,
        )

    def record_formal_start(
        self, *, admission_receipt: Mapping[str, Any], idempotency_key: str, actor: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        admission, admission_sha = verified_json_reference(admission_receipt, "coherence preconsumption admission")
        _require_exact(admission, {"schema": "ep19-preconsumption-admission-v1", "result": "PASS",
            "formal_attempt": False, "formal_budget_consumed": False,
            "candidate": self.policy["candidate"], "tree": self.policy["tree"],
            "new_allowance_total": 1, "new_allowance_used": 0, "global_ordinal": 3},
            "coherence preconsumption admission")
        body = {"FORMAL_ATTEMPT_ID": self.policy["formal_attempt_id"], "GLOBAL_ORDINAL": 3,
                "ADMISSION_RECEIPT_SHA256": admission_sha}
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = self._successor(queue)
            formal = entry["FORMAL"]
            if entry["CURRENT_STATE"] != "PREVALIDATING" or formal.get("USAGE_KNOWN") is not True or formal.get("NEW_USED") != 0 or formal.get("NEW_TOTAL") != 1:
                raise ControlError("formal start budget/state precondition failed")
            formal["NEW_USED"] = 1
            entry["FORMAL_STATUS"] = "RUNNING"
            entry["FORMAL_ATTEMPT_ID"] = self.policy["formal_attempt_id"]
            entry["FORMAL_ACTOR"] = actor
            entry["FORMAL_STARTED_AT"] = timestamp
        result = self.transaction.commit(operation="EP19_FORMAL_ATTEMPT_STARTED", idempotency_key=idempotency_key, actor=actor, timestamp=timestamp, body=body, mutate=mutate, expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)
        successor = self._successor(self.transaction.read()[0])
        return {**result, "RECEIPT": {
            "schema": "ep19-original-control-plane-formal-consume-evidence-v1", "result": "PASS",
            "fixture_only": False, "successor_id": self.policy["successor_id"],
            "authorization_id": self.policy["authorization_id"], "candidate": self.policy["candidate"],
            "formal_attempt_id": self.policy["formal_attempt_id"], "historical_formal_consumed": "2/2",
            "new_used_before": 0, "new_used_after": 1, "global_ordinal": 3, "auto_retry": False,
            "idempotency_key": idempotency_key, "transaction_id": result["TRANSACTION_ID"],
            "implementation_sha256": successor["IMPLEMENTATION_SHA256"],
            "admission_control_evidence_sha256": admission["control_plane_evidence_sha256"],
            "admission_receipt_sha256": admission_sha, "performed_by_parent": True}}

    def _verify_gate_bundle(self, reference: Mapping[str, Any], actor: str) -> tuple[dict[str, Any], str]:
        bundle, bundle_sha = verified_json_reference(reference, "formal result evidence")
        _require_exact(bundle, {
            "schema": "ep19-original-control-plane-formal-result-v1", "result": "PASS", "native_result": "PASS",
            "native_exit_code": 0, "candidate": self.policy["candidate"], "tree": self.policy["tree"],
            "formal_attempt_id": self.policy["formal_attempt_id"],
        }, "formal result evidence")
        gates = bundle.get("gate_results")
        required = self.policy["formal_gate_order"]
        executor_sha = bundle.get("executor_sha256")
        if not _is_lower_hex(executor_sha, 64):
            raise ControlError("formal result executor identity is absent or invalid")
        if not isinstance(gates, dict) or set(gates) != set(required) or bundle.get("gate_order") != required:
            raise ControlError("formal result does not contain the exact ordered 29 gates")
        for gate in required:
            value, _ = verified_json_reference(gates[gate], f"formal gate {gate}")
            _require_exact(value, {
                "schema": "ep19-native-gate-result-v1", "gate": gate, "candidate": self.policy["candidate"],
                "tree": self.policy["tree"], "native_result": "PASS", "native_exit_code": 0, "acceptance": "ACCEPTED",
                "executor_sha256": executor_sha,
            }, f"formal gate {gate}")
            if not isinstance(value.get("executor_actor"), str) or not value["executor_actor"]:
                raise ControlError(f"formal gate {gate} executor actor is absent")
            verify_native_provenance(value, f"formal gate {gate}", candidate=self.policy["candidate"],
                tree=self.policy["tree"], attempt_id=self.policy["formal_attempt_id"],
                source_sha256=executor_sha, actor=actor)
        seal, _ = verified_json_reference(bundle.get("protection_final_seal", {}), "protection final seal")
        _require_exact(seal, {"schema": "ep19-protection-final-seal-v1", "result": "PASS", "candidate": self.policy["candidate"], "tree": self.policy["tree"], "executor_sha256": executor_sha, "formal_attempt_id": self.policy["formal_attempt_id"]}, "protection final seal")
        verify_native_provenance(seal, "protection final seal", candidate=self.policy["candidate"],
            tree=self.policy["tree"], attempt_id=self.policy["formal_attempt_id"], source_sha256=executor_sha, actor=actor)
        return bundle, bundle_sha

    def record_formal_result(
        self, *, evidence: Mapping[str, Any], idempotency_key: str, actor: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        raw, raw_sha = verified_json_reference(evidence, "formal result evidence")
        passed = raw.get("result") == "PASS"
        if passed:
            bundle, bundle_sha = self._verify_gate_bundle(evidence, actor)
        else:
            bundle, bundle_sha = raw, raw_sha
            if raw.get("result") not in {"FAILED", "ERROR", "INTERRUPTED", "NOT_RUN"}:
                raise ControlError("formal result has unknown non-pass status")
            _require_exact(raw, {
                "schema": "ep19-original-control-plane-formal-result-v1", "native_result": raw["result"],
                "acceptance": "REJECTED", "candidate": self.policy["candidate"], "tree": self.policy["tree"],
                "formal_attempt_id": self.policy["formal_attempt_id"],
            }, "formal result evidence")
            if not isinstance(raw.get("native_exit_code"), int) or isinstance(raw.get("native_exit_code"), bool):
                raise ControlError("formal failure native exit code is absent")
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = self._successor(queue)
            if entry.get("CURRENT_STATE") != "PREVALIDATING" or entry.get("FORMAL_STATUS") != "RUNNING" or entry["FORMAL"].get("NEW_USED") != 1:
                raise ControlError("formal result state/consumption precondition failed")
            if bundle.get("executor_sha256") != entry["IMPLEMENTATION_SHA256"]:
                raise ControlError("formal result executor identity differs from admitted executor")
            entry["FORMAL_STATUS"] = bundle["result"]
            entry["CURRENT_STATE"] = "READY_FOR_CANONICAL_QUEUE" if passed else "RELEASED_FAILED"
            entry["FORMAL_RESULT_EVIDENCE"] = {**dict(evidence), "VERIFIED_SHA256": bundle_sha}
            if passed:
                entry["DEPENDENCIES"][0]["STATUS"] = "RESOLVED"
            else:
                entry["FAILURE_REASON"] = f"FORMAL_{bundle['result']}"
            destination = "READY_FOR_CANONICAL_QUEUE" if passed else "RELEASED_FAILED"
            entry["LAST_TRANSITION"] = {"FROM": "PREVALIDATING", "TO": destination, "ACTOR": actor, "TIMESTAMP": timestamp, "TRANSACTION_ID": transaction_id}
        operation = "EP19_FORMAL_RESULT_PASS" if passed else "EP19_FORMAL_RESULT_FAILURE"
        return self.transaction.commit(operation=operation, idempotency_key=idempotency_key, actor=actor, timestamp=timestamp, body={"EVIDENCE_SHA256": bundle_sha, "RESULT": bundle["result"]}, mutate=mutate, expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)

    def record_engineering_acceptance(
        self, *, evidence: Mapping[str, Any], idempotency_key: str, actor: str, timestamp: str,
        expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        review, review_sha = verified_json_reference(evidence, "independent engineering acceptance")
        _require_exact(review, {
            "schema": "ep19-independent-engineering-acceptance-v1", "decision": "ACCEPTED",
            "candidate": self.policy["candidate"], "tree": self.policy["tree"], "reviewer_role": "INDEPENDENT_ENGINEERING_REVIEWER",
        }, "independent engineering acceptance")
        verify_native_provenance(review, "independent engineering acceptance", candidate=self.policy["candidate"],
            tree=self.policy["tree"], attempt_id=self.policy["formal_attempt_id"],
            source_sha256=review.get("implementation_sha256"), actor=actor)
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = self._successor(queue)
            if entry.get("CURRENT_STATE") != "READY_FOR_CANONICAL_QUEUE" or entry.get("FORMAL_STATUS") != "PASS":
                raise ControlError("engineering acceptance requires passed formal result")
            if review.get("implementation_sha256") != entry["IMPLEMENTATION_SHA256"]:
                raise ControlError("engineering review did not review the admitted executor identity")
            if review.get("reviewed_controller_sha256") != entry["CANONICAL_CONTROLLER_SHA256"]:
                raise ControlError("engineering review did not review the executing canonical controller")
            if review.get("reviewed_formal_evidence_sha256") != entry.get("FORMAL_RESULT_EVIDENCE", {}).get("VERIFIED_SHA256"):
                raise ControlError("engineering review did not bind the accepted formal evidence bytes")
            reviewer = review.get("reviewer_actor")
            if not isinstance(reviewer, str) or not reviewer or reviewer != actor or reviewer == entry.get("FORMAL_ACTOR"):
                raise ControlError("engineering reviewer identity is absent or not independent")
            entry["INDEPENDENT_REVIEW_STATUS"] = "APPROVED"
            entry["INDEPENDENT_ENGINEERING_ACTOR"] = reviewer
            entry["INDEPENDENT_ENGINEERING_EVIDENCE"] = {**dict(evidence), "VERIFIED_SHA256": review_sha}
            entry["DEPENDENCIES"][1]["STATUS"] = "RESOLVED"
        return self.transaction.commit(operation="EP19_ENGINEERING_ACCEPTED", idempotency_key=idempotency_key, actor=actor, timestamp=timestamp, body={"EVIDENCE_SHA256": review_sha}, mutate=mutate, expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)

    def close_successor(
        self, *, sanity_evidence: Mapping[str, Any], closure_review_evidence: Mapping[str, Any],
        idempotency_key: str, actor: str, timestamp: str, expected_queue_sha256: str, expected_ledger_sha256: str,
    ) -> dict[str, Any]:
        sanity, sanity_sha = verified_json_reference(sanity_evidence, "post-publication sanity evidence")
        _require_exact(sanity, {"schema": "ep19-post-publication-sanity-v1", "result": "PASS", "candidate": self.policy["candidate"], "tree": self.policy["tree"]}, "post-publication sanity evidence")
        results = sanity.get("gate_results")
        if not isinstance(results, dict) or set(results) != set(self.policy["post_publication_sanity_gates"]) or sanity.get("gate_order") != self.policy["post_publication_sanity_gates"]:
            raise ControlError("post-publication sanity evidence has missing/extra/reordered gates")
        for gate, reference in results.items():
            value, _ = verified_json_reference(reference, f"post-publication sanity gate {gate}")
            _require_exact(value, {
                "schema": "ep19-post-publication-sanity-gate-v1", "gate": gate,
                "candidate": self.policy["candidate"], "tree": self.policy["tree"],
                "native_result": "PASS", "native_exit_code": 0, "acceptance": "ACCEPTED",
            }, f"post-publication sanity gate {gate}")
            source_sha = value.get("executor_sha256")
            if not _is_lower_hex(source_sha, 64) or source_sha != sanity.get("implementation_sha256"):
                raise ControlError(f"post-publication sanity gate {gate} executor identity mismatch")
            verify_native_provenance(value, f"post-publication sanity gate {gate}",
                candidate=self.policy["candidate"], tree=self.policy["tree"],
                attempt_id=self.policy["publication_attempt_id"], source_sha256=source_sha)
        review, review_sha = verified_json_reference(closure_review_evidence, "independent closure review")
        _require_exact(review, {"schema": "ep19-independent-closure-review-v1", "decision": "ACCEPTED", "candidate": self.policy["candidate"], "tree": self.policy["tree"], "reviewer_role": "INDEPENDENT_CLOSURE_REVIEWER"}, "independent closure review")
        verify_native_provenance(review, "independent closure review", candidate=self.policy["candidate"],
            tree=self.policy["tree"], attempt_id=self.policy["publication_attempt_id"],
            source_sha256=review.get("implementation_sha256"), actor=actor)
        def mutate(queue: dict[str, Any], ledger: dict[str, Any], slot: dict[str, Any] | None, transaction_id: str, payload_digest: str) -> None:
            entry = self._successor(queue)
            if entry.get("CURRENT_STATE") != "CANONICAL" or entry.get("PUBLICATION_STATUS") != "PUBLISHED":
                raise ControlError("closure requires canonical publication readback")
            if sanity.get("implementation_sha256") != entry.get("IMPLEMENTATION_SHA256"):
                raise ControlError("sanity evidence executor identity differs from admitted executor")
            if review.get("implementation_sha256") != entry.get("IMPLEMENTATION_SHA256") or review.get("reviewed_controller_sha256") != entry.get("CANONICAL_CONTROLLER_SHA256") or review.get("reviewed_sanity_sha256") != sanity_sha:
                raise ControlError("closure review did not bind exact implementation/sanity evidence")
            canonical_sha = entry.get("CANONICAL_READBACK_EVIDENCE", {}).get("VERIFIED_SHA256")
            if review.get("reviewed_canonical_readback_sha256") != canonical_sha:
                raise ControlError("closure review did not bind canonical readback evidence")
            reviewer = review.get("reviewer_actor")
            if not isinstance(reviewer, str) or reviewer != actor or reviewer in {entry.get("FORMAL_ACTOR"), entry.get("INDEPENDENT_ENGINEERING_ACTOR")}:
                raise ControlError("closure reviewer identity is absent or not independent")
            entry["EP19_CLOSED"] = "CLOSED_ACCEPTED_SUCCESSOR"
            entry["ACCEPTANCE_DECISION"] = "ACCEPTED"
            entry["POST_PUBLICATION_SANITY_EVIDENCE"] = {**dict(sanity_evidence), "VERIFIED_SHA256": sanity_sha}
            entry["INDEPENDENT_CLOSURE_EVIDENCE"] = {**dict(closure_review_evidence), "VERIFIED_SHA256": review_sha}
        return self.transaction.commit(operation="CLOSE_EP19_SUCCESSOR", idempotency_key=idempotency_key, actor=actor, timestamp=timestamp, body={"SANITY_SHA256": sanity_sha, "CLOSURE_REVIEW_SHA256": review_sha}, mutate=mutate, expected_queue_sha256=expected_queue_sha256, expected_ledger_sha256=expected_ledger_sha256)


class LockOrderGuard:
    """Models lock order without touching the real worktree registry."""

    def __init__(self) -> None:
        self.publication_slot = False
        self.worktree_registry = False

    def acquire_publication_slot(self) -> None:
        if self.worktree_registry:
            raise ControlError("inverse lock order denied")
        self.publication_slot = True

    def acquire_worktree_registry_for_bounded_mutation(self) -> None:
        if not self.publication_slot:
            raise ControlError("worktree registry cannot precede publication slot")
        if self.worktree_registry:
            raise ControlError("worktree registry lease already held")
        self.worktree_registry = True

    def release_worktree_registry(self) -> None:
        if not self.worktree_registry:
            raise ControlError("worktree registry lease is not held")
        self.worktree_registry = False

    def enter_review(self) -> None:
        if not self.publication_slot or self.worktree_registry:
            raise ControlError("review requires retained publication slot and released registry")

    def release_publication_slot(self) -> None:
        if self.worktree_registry:
            raise ControlError("release worktree registry before publication slot")
        self.publication_slot = False


def initial_queue(inventory: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1",
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "CUTOVER_MODE": "FORWARD_CUTOVER_NO_GLOBAL_RESTART",
        "PRIORITY_POLICY": [
            {"PUBLICATION_PRIORITY": 1, "POLICY_LABEL": "H7"},
            {"PUBLICATION_PRIORITY": 2, "POLICY_LABEL": "STORAGE_MIGRATION_WHEN_READY"},
            {"PUBLICATION_PRIORITY": 3, "POLICY_LABEL": "H6_CORRECTED"},
            {"PUBLICATION_PRIORITY": 4, "POLICY_LABEL": "STUDIO_S0"},
            {"PUBLICATION_PRIORITY": 5, "POLICY_LABEL": "H9_CORRECTED_OR_UPSTREAM"},
        ],
        "ENTRIES": [{
            "QUEUE_ENTRY_ID": "H7-TIMELINE-OPERATION-FIRST-REAL-MEDIA-CUT-V1",
            "LANE_ID": "timeline-operation-first-real-media-cut",
            "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "f5af2537cb95d5693be460f4d17064f0fa4a6e43",
            "CANDIDATE_TREE": "e0cbac55fa888229fefc362cf2aa37e66d04d675",
            "CURRENT_STATE": "PREVALIDATING",
            "DEPENDENCIES": [{"NAME": "FORMAL_ENVIRONMENT_PREFLIGHT_SELECTED_PROOF_PASS", "STATUS": "UNRESOLVED"}],
            "READY_TIMESTAMP": None,
            "PUBLICATION_PRIORITY": 1,
            "SLOT_HOLDER": None,
            "CANONICAL_PARENT_1": None,
            "INTEGRATION_SHA": None,
            "INTEGRATION_TREE": None,
            "INDEPENDENT_REVIEW_STATUS": "NOT_STARTED",
            "PUBLICATION_STATUS": "NOT_AUTHORIZED",
            "FAILURE_REASON": None,
            "INVENTORY_CAPTURED_AT": inventory["captured_at"],
        }],
    }


def initialize_state(state_root: os.PathLike[str] | str, inventory_path: os.PathLike[str] | str) -> dict[str, Any]:
    root = Path(state_root)
    receipts = root / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    inventory = load_json(inventory_path)
    if inventory.get("in_flight_task_count") != 21 or len(inventory.get("lanes", [])) != 21:
        raise ControlError("inventory must contain exactly 21 in-flight tasks")
    if inventory.get("unknown_phase_count") != 0:
        raise ControlError("inventory UNKNOWN phase count must be zero")
    calculated: dict[str, int] = {}
    for lane in inventory["lanes"]:
        calculated[lane["transition"]] = calculated.get(lane["transition"], 0) + 1
    if calculated != inventory.get("transition_counts"):
        raise ControlError("inventory transition counts do not match lane records")
    queue = initial_queue(inventory)
    slot = {
        "RESOURCE_NAME": SLOT_RESOURCE, "PROTOCOL_VERSION": PROTOCOL_VERSION,
        "MAX_HOLDERS": 1, "STATUS": "AVAILABLE", "HOLDER": None, "QUEUE_ENTRY_ID": None,
        "FRESH_CANONICAL_MAIN": None, "ACQUIRED_AT": None, "RELEASED_AT": None, "RELEASE_REASON": None,
        "CANDIDATE_SHA": None, "CANDIDATE_TREE": None,
        "FROZEN_INTEGRATION_SHA": None, "FROZEN_INTEGRATION_TREE": None,
        "FROZEN_PARENT_1": None, "FROZEN_PARENT_2": None, "FROZEN_AT": None,
    }
    ledger = {
        "SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1",
        "CUTOVER_TIMESTAMP": utc_now(),
        "EVENTS": [
            {
                "LANE_ID": lane["task_lane_id"], "FROM_PHASE": lane["current_phase"],
                "TRANSITION": lane["transition"], "ACTIVE_TASK_RESTARTED": False,
                "CANDIDATE_REBUILT": False, "SOURCE_INVENTORY_SHA256": file_digest(inventory_path),
            }
            for lane in inventory["lanes"]
        ],
        "TRANSITION_COUNTS": inventory["transition_counts"],
        "ACTIVE_TASK_RESTART_COUNT": 0,
        "ACTIVE_CANDIDATE_REBUILD_COUNT": 0,
    }
    queue["STATE_TRANSACTION_SEQUENCE"] = 1
    ledger["STATE_TRANSACTION_SEQUENCE"] = 1
    slot["STATE_TRANSACTION_SEQUENCE"] = 1
    transaction = StateTransaction(root)
    with transaction.mutex():
        if transaction.journal_path.exists() or any(path.exists() for path in (transaction.queue_path, transaction.ledger_path, transaction.slot_path)):
            raise ControlError("state initialization refuses existing authority or recovery journal")
        after = {"queue.json": queue, "transition-ledger.json": ledger, "slot.json": slot}
        journal = {
            "STATE_TRANSACTION_VERSION": STATE_TRANSACTION_VERSION, "AUTHORITY": False,
            "TRANSACTION_ID": sha256_bytes(normalized_json_bytes({"OPERATION": "INITIALIZE_STATE", "INVENTORY": file_digest(inventory_path)})),
            "BEFORE_SHA256": {name: None for name in after}, "AFTER": after,
            "AFTER_SHA256": {name: sha256_bytes(canonical_json_bytes(value)) for name, value in after.items()},
        }
        atomic_write_json(transaction.journal_path, journal)
        for name, value in after.items():
            atomic_write_json(root / name, value)
        transaction._clear_journal()
    receipt = {
        "RECEIPT_TYPE": "IN_FLIGHT_INVENTORY_FORWARD_CUTOVER_RECEIPT",
        "INVENTORY_PATH": str(Path(inventory_path).resolve()),
        "INVENTORY_SHA256": file_digest(inventory_path),
        "IN_FLIGHT_TASK_COUNT": 21,
        "UNKNOWN_PHASE_COUNT": 0,
        "TRANSITION_COUNTS": inventory["transition_counts"],
        "ACTIVE_TASK_RESTART_COUNT": 0,
        "ACTIVE_CANDIDATE_REBUILD_COUNT": 0,
        "ENGINEERING_CONCURRENCY_PRESERVED": "YES",
        "TIMESTAMP": utc_now(),
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
    }
    immutable_write_json(receipts / "inventory-forward-cutover-receipt.json", receipt)
    QueueControl(root / "queue.json").load()
    return {"queue": queue, "slot": slot, "ledger": ledger, "inventory_receipt": receipt}


def _expect_rejection(name: str, operation: Any) -> dict[str, Any]:
    try:
        operation()
    except ControlError as exc:
        return {"CONTROL": name, "EXPECTED": "REJECT", "OBSERVED": "REJECT", "RESULT": "PASS", "REASON": str(exc)}
    return {"CONTROL": name, "EXPECTED": "REJECT", "OBSERVED": "ALLOW", "RESULT": "FAIL", "REASON": "operation unexpectedly allowed"}


def run_red_controls() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="canonical-publication-red-") as temporary:
        root = Path(temporary)
        atomic_write_json(root / "queue.json", {"SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1", "PROTOCOL_VERSION": PROTOCOL_VERSION, "ENTRIES": [{
            "QUEUE_ENTRY_ID": "entry-a", "LANE_ID": "lane-a", "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "candidate-a",
            "CANDIDATE_TREE": "tree-a", "CURRENT_STATE": "QUEUED", "DEPENDENCIES": [], "READY_TIMESTAMP": None,
            "PUBLICATION_PRIORITY": 1, "SLOT_HOLDER": None, "CANONICAL_PARENT_1": None, "INTEGRATION_SHA": None,
            "INTEGRATION_TREE": None, "INDEPENDENT_REVIEW_STATUS": "NOT_STARTED", "PUBLICATION_STATUS": "NOT_AUTHORIZED", "FAILURE_REASON": None,
        }]})
        atomic_write_json(root / "transition-ledger.json", {"SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1", "EVENTS": []})
        atomic_write_json(root / "slot.json", {
            "RESOURCE_NAME": SLOT_RESOURCE, "PROTOCOL_VERSION": PROTOCOL_VERSION, "MAX_HOLDERS": 1,
            "STATUS": "AVAILABLE", "HOLDER": None, "QUEUE_ENTRY_ID": None, "FRESH_CANONICAL_MAIN": None,
            "CANDIDATE_SHA": None, "CANDIDATE_TREE": None,
            "FROZEN_INTEGRATION_SHA": None, "FROZEN_INTEGRATION_TREE": None,
            "FROZEN_PARENT_1": None, "FROZEN_PARENT_2": None, "FROZEN_AT": None,
            "ACQUIRED_AT": None, "RELEASED_AT": None, "RELEASE_REASON": None,
        })
        slot = SlotControl(root)
        entry = {
            "QUEUE_ENTRY_ID": "entry-a", "CURRENT_STATE": "APPROVED_FOR_PUBLICATION",
            "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "candidate-a", "CANDIDATE_TREE": "tree-a",
            "CANONICAL_PARENT_1": "main-a", "INTEGRATION_SHA": "integration-a", "INTEGRATION_TREE": "itree-a",
            "INDEPENDENT_REVIEW_STATUS": "APPROVED",
        }
        acquirable = dict(entry)
        acquirable.update({"CURRENT_STATE": "QUEUED", "DEPENDENCIES": []})
        slot.acquire("owner-a", acquirable, "main-a")
        red_queue = QueueControl(root / "queue.json")
        red_queue.transition("entry-a", "INTEGRATING", actor="owner-a")
        red_queue.transition("entry-a", "VALIDATING_INTEGRATION", actor="owner-a")
        validating = dict(entry)
        validating["CURRENT_STATE"] = "VALIDATING_INTEGRATION"
        gates = {gate: "PASS" for gate in load_json(REFERENCE_DIR / "protocol-v1.json")["always_fresh_integration_gates"]}
        slot.freeze_integration(owner="owner-a", entry=validating, integration_sha="integration-a", integration_tree="itree-a", parent_1="main-a", parent_2="candidate-a", always_fresh_gate_results=gates)
        second = dict(acquirable)
        second["QUEUE_ENTRY_ID"] = "entry-b"
        rows.append(_expect_rejection("two simultaneous publication slot holders", lambda: slot.acquire("owner-b", second, "main-a")))
        atomic_write_json(root / "empty-slot.json", {"STATUS": "AVAILABLE", "HOLDER": None})
        empty = SlotControl(root / "unused")
        empty.state_root.mkdir()
        atomic_write_json(empty.state_root / "queue.json", {"SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1", "PROTOCOL_VERSION": PROTOCOL_VERSION, "ENTRIES": []})
        atomic_write_json(empty.state_root / "transition-ledger.json", {"SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1", "EVENTS": []})
        atomic_write_json(empty.slot_path, {"STATUS": "AVAILABLE", "HOLDER": None})
        rows.append(_expect_rejection("publication without slot", lambda: empty.authorize_publication(owner="owner-a", entry=entry, current_observed_main="main-a", exact_parent_1="main-a", exact_parent_2="candidate-a")))
        rows.append(_expect_rejection("release by non-owner", lambda: slot.release("owner-b", outcome="EXPLICIT_FAIL_CLOSED_RELEASE", queue_state="INTEGRATING")))
        rows.append(_expect_rejection("main update by non-slot-holder", lambda: slot.authorize_publication(owner="owner-b", entry=entry, current_observed_main="main-a", exact_parent_1="main-a", exact_parent_2="candidate-a")))

        queue_data = {"ENTRIES": [{
            "QUEUE_ENTRY_ID": "q", "LANE_ID": "lane", "EXACT_IMPLEMENTATION_OR_DR_CANDIDATE_SHA": "c",
            "CANDIDATE_TREE": "t", "CURRENT_STATE": "READY_FOR_CANONICAL_QUEUE",
            "DEPENDENCIES": [{"NAME": "proof", "STATUS": "UNRESOLVED"}], "READY_TIMESTAMP": None,
            "PUBLICATION_PRIORITY": 1, "SLOT_HOLDER": None, "CANONICAL_PARENT_1": None,
            "INTEGRATION_SHA": None, "INTEGRATION_TREE": None, "INDEPENDENT_REVIEW_STATUS": "NOT_STARTED",
            "PUBLICATION_STATUS": "NOT_AUTHORIZED", "FAILURE_REASON": None,
        }]}
        queue_root = root / "queue-control"
        queue_root.mkdir()
        queue_data.update({"SCHEMA_VERSION": "CANONICAL_PUBLICATION_QUEUE_V1", "PROTOCOL_VERSION": PROTOCOL_VERSION})
        atomic_write_json(queue_root / "queue.json", queue_data)
        atomic_write_json(queue_root / "transition-ledger.json", {"SCHEMA_VERSION": "CONTROL_PLANE_TRANSITION_LEDGER_V1", "EVENTS": []})
        atomic_write_json(queue_root / "slot.json", {"STATUS": "AVAILABLE", "HOLDER": None})
        queue = QueueControl(queue_root / "queue.json")
        rows.append(_expect_rejection("queue skip with unresolved dependency", lambda: queue.transition("q", "QUEUED", actor="red")))

        integration_evidence = {
            "EVIDENCE_CLASS": "INTEGRATION_EVIDENCE", "GATE_NAME": "BACKEND_CI", "SUBJECT_SHA": "old-merge",
            "SUBJECT_TREE": "old-tree", "RESULT": "PASS", "TIMESTAMP": utc_now(), "PROTOCOL_VERSION": PROTOCOL_VERSION,
        }
        stale = evidence_reuse_receipt(integration_evidence, current_candidate_sha="c", current_candidate_tree="t", stale_merge=True)
        rows.append({"CONTROL": "reuse of stale merge object", "EXPECTED": "REJECT", "OBSERVED": "REJECT" if stale["REUSE_DECISION"] == "DENIED" else "ALLOW", "RESULT": "PASS" if stale["REUSE_DECISION"] == "DENIED" else "FAIL", "REASON": stale["REUSE_REASON"]})
        unjustified = evidence_reuse_receipt(integration_evidence, current_candidate_sha="c", current_candidate_tree="t")
        rows.append({"CONTROL": "reuse of integration evidence without justification", "EXPECTED": "REJECT", "OBSERVED": "REJECT" if unjustified["REUSE_DECISION"] == "DENIED" else "ALLOW", "RESULT": "PASS" if unjustified["REUSE_DECISION"] == "DENIED" else "FAIL", "REASON": unjustified["REUSE_REASON"]})
        unknown_safe = all(GateImpactMatrix().impact("UNKNOWN", gate) == "UNKNOWN_RERUN_REQUIRED" for gate in GateImpactMatrix().data["gates"][3:])
        rows.append({"CONTROL": "UNKNOWN delta treated as harmless", "EXPECTED": "REJECT", "OBSERVED": "REJECT" if unknown_safe else "ALLOW", "RESULT": "PASS" if unknown_safe else "FAIL", "REASON": "UNKNOWN requires every potentially applicable gate rerun"})
        rows.append(_expect_rejection("frozen integration loses slot during independent review", lambda: slot.release("owner-a", outcome="ROUTINE_RELEASE", queue_state="INDEPENDENT_REVIEW")))
        queue_data["ENTRIES"][0]["CURRENT_STATE"] = "PREVALIDATING"
        atomic_write_json(queue_root / "queue.json", queue_data)
        rows.append(_expect_rejection("candidate SHA changes after prevalidation", lambda: queue.transition("q", "READY_FOR_CANONICAL_QUEUE", actor="red", candidate_sha="changed")))
        rows.append(_expect_rejection("Parent 1 not equal to slot-acquisition fresh main", lambda: slot.authorize_publication(owner="owner-a", entry=entry, current_observed_main="main-b", exact_parent_1="main-b", exact_parent_2="candidate-a")))
        rows.append(_expect_rejection("Parent 2 not equal to accepted exact candidate", lambda: slot.authorize_publication(owner="owner-a", entry=entry, current_observed_main="main-a", exact_parent_1="main-a", exact_parent_2="candidate-b")))
        rows.append(_expect_rejection("force push attempt", lambda: slot.authorize_publication(owner="owner-a", entry=entry, current_observed_main="main-a", exact_parent_1="main-a", exact_parent_2="candidate-a", force_push=True)))
        rows.append(_expect_rejection("history rewrite attempt", lambda: slot.authorize_publication(owner="owner-a", entry=entry, current_observed_main="main-a", exact_parent_1="main-a", exact_parent_2="candidate-a", history_rewrite=True)))
    passed = len(rows) == 14 and all(row["RESULT"] == "PASS" for row in rows)
    return {
        "RECEIPT_TYPE": "PUBLICATION_CONTROL_RED_MATRIX_V1",
        "RED_CONTROL_COUNT": len(rows),
        "PUBLICATION_CONTROL_RED_MATRIX": "PASS" if passed else "FAIL",
        "ROWS": rows,
        "TIMESTAMP": utc_now(),
        "PROTOCOL_VERSION": PROTOCOL_VERSION,
    }


def validate_reference_files() -> dict[str, Any]:
    classifier = DeltaClassifier()
    matrix = GateImpactMatrix().validate()
    fingerprint_data = load_json(REFERENCE_DIR / "fingerprint-definitions-v1.json")
    protocol = load_json(REFERENCE_DIR / "protocol-v1.json")
    if len(protocol["states"]) != 14 or len(set(protocol["states"])) != 14:
        raise ControlError("protocol state set must contain exactly 14 unique states")
    if fingerprint_data.get("fingerprinted_gate_count") != 5 or len(fingerprint_data["definitions"]) != 5:
        raise ControlError("fingerprint framework must contain exactly five pilot gates")
    return {
        "DELTA_CLASSIFIER_CATEGORY_COUNT": len(classifier.categories),
        **matrix,
        "FINGERPRINTED_GATE_COUNT": 5,
        "PROTOCOL_STATE_COUNT": len(protocol["states"]),
    }


def _command_init(arguments: argparse.Namespace) -> dict[str, Any]:
    return initialize_state(arguments.state_root, arguments.inventory)


def _command_classify(arguments: argparse.Namespace) -> dict[str, Any]:
    return DeltaClassifier().classify_paths(arguments.paths)


def _command_red(arguments: argparse.Namespace) -> dict[str, Any]:
    receipt = run_red_controls()
    if arguments.output:
        atomic_write_json(arguments.output, receipt)
    if receipt["PUBLICATION_CONTROL_RED_MATRIX"] != "PASS":
        raise ControlError("red matrix failed")
    return receipt


def _command_validate(arguments: argparse.Namespace) -> dict[str, Any]:
    result = validate_reference_files()
    if arguments.queue:
        queue = QueueControl(arguments.queue).load()
        result["QUEUE_ENTRY_COUNT"] = len(queue["ENTRIES"])
    return result


def _command_transition(arguments: argparse.Namespace) -> dict[str, Any]:
    return QueueControl(arguments.queue).transition(
        arguments.entry, arguments.to_state, actor=arguments.actor,
        candidate_sha=arguments.candidate_sha, candidate_tree=arguments.candidate_tree,
    )


def _command_acquire_slot(arguments: argparse.Namespace) -> dict[str, Any]:
    queue_control = QueueControl(arguments.queue)
    entry = queue_control.get(arguments.entry)
    slot = SlotControl(arguments.state_root)
    return slot.acquire(arguments.owner, entry, arguments.fresh_main)


def _command_release_slot(arguments: argparse.Namespace) -> dict[str, Any]:
    return SlotControl(arguments.state_root).release(
        arguments.owner, outcome=arguments.outcome, queue_state=arguments.queue_state,
    )


def _command_freeze(arguments: argparse.Namespace) -> dict[str, Any]:
    queue_control = QueueControl(arguments.queue)
    entry = queue_control.get(arguments.entry)
    return SlotControl(arguments.state_root).freeze_integration(
        owner=arguments.owner, entry=entry, integration_sha=arguments.integration_sha,
        integration_tree=arguments.integration_tree, parent_1=arguments.parent_1,
        parent_2=arguments.parent_2, always_fresh_gate_results=load_json(arguments.gate_results),
    )


def _command_authorize(arguments: argparse.Namespace) -> dict[str, Any]:
    entry = QueueControl(arguments.queue).get(arguments.entry)
    return SlotControl(arguments.state_root).authorize_publication(
        owner=arguments.owner, entry=entry, current_observed_main=arguments.observed_main,
        exact_parent_1=arguments.parent_1, exact_parent_2=arguments.parent_2,
        force_push=arguments.force_push, history_rewrite=arguments.history_rewrite,
        receipt_path=arguments.output,
    )


def _command_identity_readback(arguments: argparse.Namespace) -> dict[str, Any]:
    entry = QueueControl(arguments.queue).get(arguments.entry)
    return SlotControl(arguments.state_root).identity_readback(
        owner=arguments.owner, entry=entry, gate_name=arguments.gate,
        observed_sha=arguments.observed_sha, receipt_path=arguments.output,
    )


def _command_independent_review(arguments: argparse.Namespace) -> dict[str, Any]:
    return QueueControl(arguments.queue).record_independent_review(
        arguments.entry, evidence={"PATH": arguments.evidence_path, "SHA256": arguments.evidence_sha256},
        actor=arguments.actor, timestamp=arguments.timestamp,
        expected_queue_sha256=arguments.expected_queue_sha256, expected_ledger_sha256=arguments.expected_ledger_sha256,
    )


def _command_fingerprint(arguments: argparse.Namespace) -> dict[str, Any]:
    receipt = compute_gate_fingerprint(arguments.gate, arguments.root)
    if arguments.output:
        immutable_write_json(arguments.output, receipt)
    return receipt


def _command_stable_readback(arguments: argparse.Namespace) -> dict[str, Any]:
    receipt = stable_state_readback(arguments.path)
    if arguments.output:
        immutable_write_json(arguments.output, receipt)
    return receipt


def _evidence_argument(arguments: argparse.Namespace, prefix: str = "evidence") -> dict[str, str]:
    return {"PATH": getattr(arguments, f"{prefix}_path"), "SHA256": getattr(arguments, f"{prefix}_sha256")}


def _ep19_common(arguments: argparse.Namespace) -> dict[str, Any]:
    return {
        "idempotency_key": arguments.idempotency_key, "actor": arguments.actor,
        "timestamp": arguments.timestamp, "expected_queue_sha256": arguments.expected_queue_sha256,
        "expected_ledger_sha256": arguments.expected_ledger_sha256,
    }


def _command_recover_state(arguments: argparse.Namespace) -> dict[str, Any]:
    return StateTransaction(arguments.state_root).recover()


def _command_inspect_ep19(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).inspect()


def _command_register_ep19(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).register_successor(evidence=_evidence_argument(arguments), **_ep19_common(arguments))


def _command_ep19_formal_start(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).record_formal_start(
        admission_receipt=_evidence_argument(arguments), **_ep19_common(arguments))


def _command_ep19_formal_result(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).record_formal_result(evidence=_evidence_argument(arguments), **_ep19_common(arguments))


def _command_ep19_engineering(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).record_engineering_acceptance(evidence=_evidence_argument(arguments), **_ep19_common(arguments))


def _command_ep19_prepare_direct_ff(arguments: argparse.Namespace) -> dict[str, Any]:
    entry = QueueControl(arguments.queue).get(arguments.entry)
    return SlotControl(arguments.state_root).prepare_ep19_direct_ff(
        owner=arguments.actor, entry=entry, **{key: value for key, value in _ep19_common(arguments).items() if key != "actor"})


def _command_ep19_direct_ff(arguments: argparse.Namespace) -> dict[str, Any]:
    entry = QueueControl(arguments.queue).get(arguments.entry)
    return SlotControl(arguments.state_root).authorize_ep19_direct_ff(
        owner=arguments.actor, entry=entry,
        ancestry_evidence=_evidence_argument(arguments, "ancestry"),
        race_evidence=_evidence_argument(arguments, "race"),
        remote_evidence=_evidence_argument(arguments, "remote"),
        receipt_path=arguments.output, **{key: value for key, value in _ep19_common(arguments).items() if key != "actor"},
    )


def _command_ep19_publication_result(arguments: argparse.Namespace) -> dict[str, Any]:
    return SlotControl(arguments.state_root).record_ep19_publication_result(
        owner=arguments.actor, canonical_readback_evidence=_evidence_argument(arguments),
        **{key: value for key, value in _ep19_common(arguments).items() if key != "actor"},
    )


def _command_close_ep19(arguments: argparse.Namespace) -> dict[str, Any]:
    return EP19AcceptanceControl(arguments.state_root).close_successor(
        sanity_evidence=_evidence_argument(arguments, "sanity"),
        closure_review_evidence=_evidence_argument(arguments, "closure_review"), **_ep19_common(arguments),
    )


def _add_ep19_transaction_arguments(parser: argparse.ArgumentParser, *, evidence: bool = False) -> None:
    parser.add_argument("--state-root", required=True)
    if evidence:
        parser.add_argument("--evidence-path", required=True)
        parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--expected-queue-sha256", required=True)
    parser.add_argument("--expected-ledger-sha256", required=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init-state", help="initialize forward-cutover state from inventory")
    init.add_argument("--state-root", required=True)
    init.add_argument("--inventory", required=True)
    init.set_defaults(handler=_command_init)
    classify = subparsers.add_parser("classify", help="classify changed paths conservatively")
    classify.add_argument("paths", nargs="*")
    classify.set_defaults(handler=_command_classify)
    red = subparsers.add_parser("red-controls", help="run all 14 fail-closed negative controls")
    red.add_argument("--output")
    red.set_defaults(handler=_command_red)
    validate = subparsers.add_parser("validate", help="validate protocol references and optional queue")
    validate.add_argument("--queue")
    validate.set_defaults(handler=_command_validate)
    transition = subparsers.add_parser("transition", help="apply one strict queue transition")
    transition.add_argument("--queue", required=True)
    transition.add_argument("--entry", required=True)
    transition.add_argument("--to-state", required=True)
    transition.add_argument("--actor", required=True)
    transition.add_argument("--candidate-sha")
    transition.add_argument("--candidate-tree")
    transition.set_defaults(handler=_command_transition)
    acquire = subparsers.add_parser("acquire-slot", help="bind the sole slot to a resolved QUEUED entry")
    acquire.add_argument("--state-root", required=True)
    acquire.add_argument("--queue", required=True)
    acquire.add_argument("--entry", required=True)
    acquire.add_argument("--owner", required=True)
    acquire.add_argument("--fresh-main", required=True)
    acquire.set_defaults(handler=_command_acquire_slot)
    release = subparsers.add_parser("release-slot", help="release by holder for an allowed terminal outcome")
    release.add_argument("--state-root", required=True)
    release.add_argument("--owner", required=True)
    release.add_argument("--outcome", choices=["PUBLICATION_SUCCESS", "EXPLICIT_FAIL_CLOSED_RELEASE"], required=True)
    release.add_argument("--queue-state", required=True)
    release.set_defaults(handler=_command_release_slot)
    freeze = subparsers.add_parser("freeze-integration", help="bind an exact validated integration to the held slot")
    freeze.add_argument("--state-root", required=True)
    freeze.add_argument("--queue", required=True)
    freeze.add_argument("--entry", required=True)
    freeze.add_argument("--owner", required=True)
    freeze.add_argument("--integration-sha", required=True)
    freeze.add_argument("--integration-tree", required=True)
    freeze.add_argument("--parent-1", required=True)
    freeze.add_argument("--parent-2", required=True)
    freeze.add_argument("--gate-results", required=True, help="JSON object containing the exact always-fresh gate set")
    freeze.set_defaults(handler=_command_freeze)
    authorize = subparsers.add_parser("authorize-publication", help="emit exact normal-publication authorization only")
    authorize.add_argument("--state-root", required=True)
    authorize.add_argument("--queue", required=True)
    authorize.add_argument("--entry", required=True)
    authorize.add_argument("--owner", required=True)
    authorize.add_argument("--observed-main", required=True)
    authorize.add_argument("--parent-1", required=True)
    authorize.add_argument("--parent-2", required=True)
    authorize.add_argument("--output", required=True)
    authorize.add_argument("--force-push", action="store_true")
    authorize.add_argument("--history-rewrite", action="store_true")
    authorize.set_defaults(handler=_command_authorize)
    identity = subparsers.add_parser("identity-readback", help="emit a fail-closed remote identity readback receipt")
    identity.add_argument("--state-root", required=True)
    identity.add_argument("--queue", required=True)
    identity.add_argument("--entry", required=True)
    identity.add_argument("--owner", required=True)
    identity.add_argument("--gate", choices=["REMOTE_CANDIDATE_READBACK", "POST_PUBLICATION_MAIN_READBACK"], required=True)
    identity.add_argument("--observed-sha", required=True)
    identity.add_argument("--output", required=True)
    identity.set_defaults(handler=_command_identity_readback)
    independent = subparsers.add_parser("record-independent-review", help="verify machine review bytes and approve the frozen normal publication")
    independent.add_argument("--queue", required=True)
    independent.add_argument("--entry", required=True)
    independent.add_argument("--evidence-path", required=True)
    independent.add_argument("--evidence-sha256", required=True)
    independent.add_argument("--actor", required=True)
    independent.add_argument("--timestamp", required=True)
    independent.add_argument("--expected-queue-sha256", required=True)
    independent.add_argument("--expected-ledger-sha256", required=True)
    independent.set_defaults(handler=_command_independent_review)
    fingerprint = subparsers.add_parser("fingerprint", help="compute one deterministic pilot gate fingerprint")
    fingerprint.add_argument("--gate", required=True)
    fingerprint.add_argument("--root", required=True)
    fingerprint.add_argument("--output")
    fingerprint.set_defaults(handler=_command_fingerprint)
    readback = subparsers.add_parser("stable-readback", help="perform two byte-identical state reads")
    readback.add_argument("path")
    readback.add_argument("--output")
    readback.set_defaults(handler=_command_stable_readback)
    recover = subparsers.add_parser("recover-state", help="recover one interrupted original state transaction")
    recover.add_argument("--state-root", required=True)
    recover.set_defaults(handler=_command_recover_state)
    inspect_ep19 = subparsers.add_parser("inspect-ep19-successor", help="inspect the integrated EP19 successor in original authority state")
    inspect_ep19.add_argument("--state-root", required=True)
    inspect_ep19.set_defaults(handler=_command_inspect_ep19)
    register_ep19 = subparsers.add_parser("register-ep19-successor", help="register exact EP19 successor from verified admission bytes")
    _add_ep19_transaction_arguments(register_ep19, evidence=True)
    register_ep19.set_defaults(handler=_command_register_ep19)
    formal_start = subparsers.add_parser("record-ep19-formal-start", help="consume the sole new EP19 formal allowance exactly once")
    _add_ep19_transaction_arguments(formal_start, evidence=True)
    formal_start.set_defaults(handler=_command_ep19_formal_start)
    formal_result = subparsers.add_parser("record-ep19-formal-result", help="verify and record exact 29-gate native result bytes")
    _add_ep19_transaction_arguments(formal_result, evidence=True)
    formal_result.set_defaults(handler=_command_ep19_formal_result)
    engineering = subparsers.add_parser("record-ep19-engineering-acceptance", help="verify independent engineering machine decision bytes")
    _add_ep19_transaction_arguments(engineering, evidence=True)
    engineering.set_defaults(handler=_command_ep19_engineering)
    prepare_direct_ff = subparsers.add_parser("prepare-ep19-direct-ff", help="apply the exact accepted-engineering then slot exception ordering")
    _add_ep19_transaction_arguments(prepare_direct_ff)
    prepare_direct_ff.add_argument("--queue", required=True)
    prepare_direct_ff.add_argument("--entry", required=True)
    prepare_direct_ff.set_defaults(handler=_command_ep19_prepare_direct_ff)
    direct_ff = subparsers.add_parser("authorize-ep19-direct-ff", help="authorize only the exact a298 direct-FF exception")
    _add_ep19_transaction_arguments(direct_ff)
    direct_ff.add_argument("--queue", required=True)
    direct_ff.add_argument("--entry", required=True)
    for prefix in ("ancestry", "race", "remote"):
        direct_ff.add_argument(f"--{prefix}-path", required=True)
        direct_ff.add_argument(f"--{prefix}-sha256", required=True)
    direct_ff.add_argument("--output", required=True)
    direct_ff.set_defaults(handler=_command_ep19_direct_ff)
    publication_result = subparsers.add_parser("record-ep19-publication-result", help="verify canonical readback bytes and record CANONICAL")
    _add_ep19_transaction_arguments(publication_result, evidence=True)
    publication_result.set_defaults(handler=_command_ep19_publication_result)
    close_ep19 = subparsers.add_parser("close-ep19-successor", help="verify sanity and independent closure bytes")
    _add_ep19_transaction_arguments(close_ep19)
    for prefix in ("sanity", "closure-review"):
        close_ep19.add_argument(f"--{prefix}-path", required=True)
        close_ep19.add_argument(f"--{prefix}-sha256", required=True)
    close_ep19.set_defaults(handler=_command_close_ep19)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        result = arguments.handler(arguments)
    except (ControlError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"STATUS": "REJECTED", "ERROR": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
