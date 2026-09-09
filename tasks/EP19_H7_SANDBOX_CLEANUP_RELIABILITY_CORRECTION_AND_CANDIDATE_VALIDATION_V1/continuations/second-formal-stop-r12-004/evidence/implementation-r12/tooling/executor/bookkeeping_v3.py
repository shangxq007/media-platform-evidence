"""Approved A/B/C bookkeeping policy for EP19 external validation.

This module does not infer a writer and never uses ledger data for policy,
authorization, candidate selection, gate criteria, or rollback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import base64
import json
import math
import os
import re
import stat
import time

from capture import (FIELDS, CaptureError, canonical, capture_directory,
                     capture_file, capture_manifest, private_projection,
                     public_projection, sha256)

SCHEMA = "ep19-approved-bookkeeping-v3"
CONTRACT_VERSION = "OWNER_APPROVED_EP19_LOCK_USAGE_LEDGER_V3"
PRODUCTION_ROOT = Path("USER_HOME/.hermes/skills")
USAGE_NAME = ".usage.json"
LOCK_NAME = ".usage.json.lock"
LEDGER_NAME = ".curator_ledger.jsonl"
TEMP_RE = re.compile(r"^\.usage_[a-z0-9_]{8}\.tmp$")
MUTABLE_FIELDS = ("view_count", "use_count", "last_viewed_at", "last_used_at")
COUNT_FIELDS = frozenset(("view_count", "use_count"))
TIME_FIELDS = frozenset(("last_viewed_at", "last_used_at"))
ROOT_STRICT = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink")
USAGE_STRICT = ("st_dev", "st_mode", "st_uid", "st_gid", "st_nlink")
LEDGER_STRICT = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink")

LIMITS = {
    "original_prefix_bytes_max": 64 * 1024 * 1024,
    "appended_records_max": 128,
    "line_bytes_including_lf_max": 1024 * 1024,
    "append_total_bytes_max": 8 * 1024 * 1024,
    "manifest_items_max": 4096,
    "eligible_skills_max": 128,
    "stable_capture_attempts_per_boundary": 3,
    "capture_total_seconds_per_boundary_max": 5,
    "pending_events_max": 4096,
}
RECORD_KEYS = frozenset(("id", "ts", "actor", "action", "skill", "evidence", "before", "after"))
MANIFEST_KEYS = frozenset(("path", "sha256"))
ID_RE = re.compile(r"^[0-9a-f]{12}$")
SKILL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
TS_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{6})?\+00:00$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class PolicyError(RuntimeError):
    pass


def enforce_limit(name, value):
    """Shared inclusive resource-bound predicate used by qualification."""
    if name not in LIMITS or isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PolicyError("RESOURCE_LIMIT_ARGUMENT_INVALID")
    if value > LIMITS[name]:
        raise PolicyError(name.upper() + "_EXCEEDED")
    return True


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError("DUPLICATE_JSON_KEY " + str(key))
        result[key] = value
    return result


def _nonfinite(value):
    raise PolicyError("NONFINITE_JSON " + value)


def strict_json(raw):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyError("INVALID_UTF8") from exc
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    except PolicyError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PolicyError("MALFORMED_JSON") from exc

    def finite(node):
        if isinstance(node, float) and not math.isfinite(node):
            raise PolicyError("NONFINITE_JSON")
        if isinstance(node, dict):
            for child in node.values():
                finite(child)
        elif isinstance(node, list):
            for child in node:
                finite(child)
    finite(value)
    return value


def _jsonl_lines(raw, *, original=False):
    """Validate bytes as JSONL before JSON parsing; escaped ``\\r`` stays legal."""
    label = "ORIGINAL_LEDGER_" if original else "LEDGER_"
    if raw.startswith(b"\xef\xbb\xbf"):
        raise PolicyError(label + "BOM")
    if b"\r" in raw:
        raise PolicyError(label + "RAW_CR")
    if raw and not raw.endswith(b"\n"):
        raise PolicyError(label + "PARTIAL_LINE")
    if not raw:
        return []
    lines = raw.split(b"\n")
    if lines[-1] != b"":
        raise PolicyError(label + "PARTIAL_LINE")
    lines.pop()
    if any(line == b"" for line in lines):
        raise PolicyError(label + "EMPTY_LINE")
    return [line + b"\n" for line in lines]


def _deep_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_deep_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_deep_equal(a, b) for a, b in zip(left, right))
    return left == right


def _timestamp(value, *, null_allowed):
    if value is None and null_allowed:
        return None
    if not isinstance(value, str) or not value:
        raise PolicyError("TIMESTAMP_TYPE")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PolicyError("TIMESTAMP_FORMAT") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PolicyError("TIMESTAMP_NOT_UTC")
    return parsed


def _type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _validate_mutable(field, value):
    if field in COUNT_FIELDS:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PolicyError("COUNT_TYPE_OR_RANGE " + field)
    elif field in TIME_FIELDS:
        _timestamp(value, null_allowed=True)
    else:
        raise PolicyError("UNKNOWN_MUTABLE_FIELD")


def bind_eligible_packages(root, names):
    """Bind only a caller-supplied finite list; never discover/expand eligibility."""
    root = canonical(root)
    if isinstance(names, dict):
        supplied = dict(names)
    else:
        ordered = list(names)
        if len(ordered) != len(set(ordered)):
            raise PolicyError("DUPLICATE_ELIGIBLE_SKILL")
        supplied = {name: root / name for name in ordered}
    enforce_limit("eligible_skills_max", len(supplied))
    deadline = time.monotonic() + LIMITS["capture_total_seconds_per_boundary_max"]
    result = {}
    for name, raw_package in sorted(supplied.items()):
        if not isinstance(name, str) or not SKILL_RE.fullmatch(name):
            raise PolicyError("INVALID_ELIGIBLE_SKILL")
        package = canonical(raw_package)
        if package.resolve() != package or not package.is_relative_to(root) or package == root:
            raise PolicyError("ELIGIBLE_PACKAGE_NONCANONICAL_OR_SYMLINK")
        result[name] = {"package": str(package),
                        "manifest": capture_manifest(package, max_items=LIMITS["manifest_items_max"], deadline=deadline)}
    return result


def _historical_ids(raw):
    enforce_limit("original_prefix_bytes_max", len(raw))
    ids = set()
    for line in _jsonl_lines(raw, original=True):
        value = strict_json(line[:-1])
        if not isinstance(value, dict) or not isinstance(value.get("id"), str) or not value["id"]:
            raise PolicyError("ORIGINAL_LEDGER_ID_MISSING")
        if value["id"] in ids:
            raise PolicyError("ORIGINAL_LEDGER_DUPLICATE_ID")
        ids.add(value["id"])
    return ids


def _root_persistent_entries(row):
    return [name for name in row["entries"] if not TEMP_RE.fullmatch(name)]


def capture_bundle(root, eligible_map):
    """Capture all A/B/C decision inputs; each projection binds its own real bytes."""
    root = canonical(root)
    deadline = time.monotonic() + LIMITS["capture_total_seconds_per_boundary_max"]
    def remaining():
        value = deadline - time.monotonic()
        if value <= 0:
            raise PolicyError("BOUNDARY_CAPTURE_TIME_LIMIT_EXCEEDED")
        return value
    failures = []
    for bundle_attempt in range(1, LIMITS["stable_capture_attempts_per_boundary"] + 1):
        try:
            first_root = capture_directory(root, deadline=deadline)
            usage = capture_file(root / USAGE_NAME, attempts=1, max_seconds=remaining())
            lock = capture_file(root / LOCK_NAME, attempts=1, max_seconds=remaining())
            ledger = capture_file(root / LEDGER_NAME, attempts=1,
                                  max_bytes=LIMITS["original_prefix_bytes_max"] + LIMITS["append_total_bytes_max"],
                                  max_seconds=remaining())
            manifests = {}
            for name, binding in sorted(eligible_map.items()):
                manifests[name] = capture_manifest(binding["package"], max_items=LIMITS["manifest_items_max"],
                                                   deadline=deadline)
            final_root = capture_directory(root, deadline=deadline)
            remaining()
            if first_root["metadata"] != final_root["metadata"] or first_root["entries"] != final_root["entries"]:
                raise PolicyError("BUNDLE_ROOT_UNSTABLE")
            ids = {usage["capture_id"], lock["capture_id"], ledger["capture_id"]}
            if len(ids) != 3:
                raise PolicyError("CAPTURE_ID_COLLISION")
            return {"root": final_root, "usage": usage, "lock": lock, "ledger": ledger,
                    "manifests": manifests, "bundle_attempt": bundle_attempt,
                    "capture_binding": {"usage": usage["capture_id"], "lock": lock["capture_id"],
                                        "ledger": ledger["capture_id"], "root": final_root["capture_id"]},
                    "coherent": True}
        except (CaptureError, PolicyError) as exc:
            failures.append(f"{type(exc).__name__}:{exc}")
            remaining()
    raise PolicyError("BOUNDARY_SHARED_CAPTURE_RETRY_EXHAUSTED " + " | ".join(failures))


def create_policy(root=PRODUCTION_ROOT, *, owner_sha256, dependency_sha256,
                  eligible_names, fixture=False):
    root = canonical(root)
    if not fixture and root != PRODUCTION_ROOT:
        raise PolicyError("PRODUCTION_ROOT_BINDING_MISMATCH")
    eligible = bind_eligible_packages(root, eligible_names)
    bundle = capture_bundle(root, eligible)
    usage_data = strict_json(bundle["usage"]["raw"])
    if not isinstance(usage_data, dict) or any(not isinstance(key, str) for key in usage_data):
        raise PolicyError("USAGE_ROOT_SCHEMA")
    if not bundle["lock"]["raw"] == b"" or bundle["lock"]["metadata"]["st_size"] != 0:
        raise PolicyError("LOCK_BASELINE_NOT_EMPTY")
    if TEMP_RE.fullmatch(next((x for x in bundle["root"]["entries"] if TEMP_RE.fullmatch(x)), "")):
        raise PolicyError("PERSISTENT_TEMP_AT_BASELINE")
    records = {}
    for record_id, value in sorted(usage_data.items()):
        if not isinstance(value, dict):
            raise PolicyError("USAGE_RECORD_NOT_OBJECT")
        is_eligible = record_id in eligible
        mutable = {}
        for field in MUTABLE_FIELDS:
            if is_eligible and field in value:
                _validate_mutable(field, value[field])
                mutable[field] = value[field]
        records[record_id] = {
            "eligible": is_eligible,
            "membership": sorted(value),
            "types": {key: _type_name(item) for key, item in sorted(value.items())},
            "strict": {key: item for key, item in value.items()
                       if not (is_eligible and key in MUTABLE_FIELDS)},
            "mutable": mutable,
        }
    historical_ids = sorted(_historical_ids(bundle["ledger"]["raw"]))
    return {
        "schema": SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "privacy": "PRIVATE_OWNER_ONLY_RAW_CAPTURE",
        "root": str(root),
        "paths": {"usage": str(root / USAGE_NAME), "lock": str(root / LOCK_NAME),
                  "ledger": str(root / LEDGER_NAME)},
        "owner_decision_sha256": owner_sha256,
        "dependency_binding_sha256": dependency_sha256,
        "eligible_map": eligible,
        "limits": dict(LIMITS),
        "root_baseline": bundle["root"],
        "persistent_entries": _root_persistent_entries(bundle["root"]),
        "usage_baseline": private_projection(bundle["usage"]),
        "usage_records": records,
        "lock_baseline": private_projection(bundle["lock"]),
        "ledger_baseline": private_projection(bundle["ledger"]),
        "ledger_original_ids": historical_ids,
        "capture_protocol": "same-real-byte-stat-read-stat-v3",
        "claims_not_made": ["WRITER_IDENTITY", "COMPLETE_SYSCALL_HISTORY",
                            "LEDGER_OVERWRITE_RESTORE_DETECTABLE_BETWEEN_CAPTURES"],
    }


def new_session(policy):
    _validate_policy(policy)
    baseline = policy["ledger_baseline"]
    return {"previous_ledger_raw_base64": baseline["raw_base64"],
            "previous_ledger_metadata": baseline["metadata"],
            "previous_ledger_sha256": baseline["sha256"],
            "seen_ids": list(policy["ledger_original_ids"]),
            "appended_records": 0, "appended_bytes": 0, "last_timestamp": None,
            "bound_contract_version": CONTRACT_VERSION}


def _validate_policy(policy):
    if policy.get("schema") != SCHEMA or policy.get("contract_version") != CONTRACT_VERSION:
        raise PolicyError("STALE_OR_UNKNOWN_POLICY")
    if policy.get("limits") != LIMITS:
        raise PolicyError("RESOURCE_LIMIT_BINDING_MISMATCH")
    enforce_limit("eligible_skills_max", len(policy.get("eligible_map", {})))


def evaluate_usage(policy, capture):
    baseline = policy["usage_baseline"]
    current = strict_json(capture["raw"])
    if not isinstance(current, dict) or sorted(current) != sorted(policy["usage_records"]):
        raise PolicyError("USAGE_RECORD_MEMBERSHIP_CHANGED")
    for field in USAGE_STRICT:
        if capture["metadata"][field] != baseline["metadata"][field]:
            raise PolicyError("USAGE_STRICT_METADATA_CHANGED " + field)
    changed = []
    for record_id, value in sorted(current.items()):
        if not isinstance(value, dict):
            raise PolicyError("USAGE_RECORD_NOT_OBJECT")
        wanted = policy["usage_records"][record_id]
        if sorted(value) != wanted["membership"]:
            raise PolicyError("USAGE_FIELD_MEMBERSHIP_CHANGED " + record_id)
        current_types = {key: _type_name(item) for key, item in sorted(value.items())
                         if not (wanted["eligible"] and key in MUTABLE_FIELDS)}
        wanted_types = {key: item for key, item in wanted["types"].items()
                        if not (wanted["eligible"] and key in MUTABLE_FIELDS)}
        if current_types != wanted_types:
            raise PolicyError("USAGE_FIELD_TYPE_CHANGED " + record_id)
        strict_values = {key: item for key, item in value.items()
                         if not (wanted["eligible"] and key in MUTABLE_FIELDS)}
        if not _deep_equal(strict_values, wanted["strict"]):
            raise PolicyError("USAGE_STRICT_VALUE_CHANGED " + record_id)
        for field, before in wanted["mutable"].items():
            now = value[field]
            _validate_mutable(field, now)
            if field in COUNT_FIELDS and now < before:
                raise PolicyError("USAGE_COUNT_DECREASE " + record_id + " " + field)
            if field in TIME_FIELDS:
                before_time = _timestamp(before, null_allowed=True)
                now_time = _timestamp(now, null_allowed=before is None)
                if before is not None and now is None:
                    raise PolicyError("USAGE_TIMESTAMP_NULL_REGRESSION")
                if before_time is not None and now_time < before_time:
                    raise PolicyError("USAGE_TIMESTAMP_BACKWARDS")
            if not _deep_equal(before, now):
                changed.append(f"/{record_id}/{field}")
    return {"result": "PASS", "capture_id": capture["capture_id"],
            "source_id": capture["source_id"], "changed_json_pointers": changed,
            "old_strict": "PASS" if (capture["sha256"] == baseline["sha256"] and
                                         capture["metadata"] == baseline["metadata"]) else "OLD_STRICT_REJECT"}


def _manifest_path_valid(path, package):
    if not isinstance(path, str) or len(path) > 4096 or "\\" in path or any(ord(c) < 32 for c in path):
        return False
    pure = PurePosixPath(path)
    if not pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        return False
    try:
        return Path(path).is_relative_to(Path(package)) and path != str(package)
    except ValueError:
        return False


def validate_ledger_record(record, policy, seen_ids, *, window_start, window_end,
                           previous_timestamp=None):
    if not isinstance(record, dict) or set(record) != RECORD_KEYS:
        raise PolicyError("LEDGER_RECORD_SCHEMA_KEYS")
    if not isinstance(record["id"], str) or not ID_RE.fullmatch(record["id"]):
        raise PolicyError("LEDGER_ID_SCHEMA")
    if record["id"] in seen_ids:
        raise PolicyError("LEDGER_DUPLICATE_ID")
    if not isinstance(record["ts"], str) or not TS_RE.fullmatch(record["ts"]):
        raise PolicyError("LEDGER_TIMESTAMP_SCHEMA")
    stamp = _timestamp(record["ts"], null_allowed=False)
    if stamp < window_start or stamp > window_end:
        raise PolicyError("LEDGER_TIMESTAMP_OUTSIDE_BOUND_WINDOW")
    if previous_timestamp is not None and stamp < previous_timestamp:
        raise PolicyError("LEDGER_TIMESTAMP_BACKWARDS")
    if record["actor"] not in ("curator", "agent", "user"):
        raise PolicyError("LEDGER_ACTOR_SCHEMA")
    if record["action"] not in ("patch", "edit"):
        raise PolicyError("LEDGER_ACTION_SCHEMA")
    skill = record["skill"]
    if not isinstance(skill, str) or not SKILL_RE.fullmatch(skill) or skill not in policy["eligible_map"]:
        raise PolicyError("LEDGER_SKILL_NOT_PREBOUND")
    if type(record["evidence"]) is not dict or record["evidence"]:
        raise PolicyError("LEDGER_EVIDENCE_NOT_EMPTY_OBJECT")
    before, after = record["before"], record["after"]
    if type(before) is not list or type(after) is not list or not before:
        raise PolicyError("LEDGER_MANIFEST_SIZE")
    enforce_limit("manifest_items_max", len(before))
    if not _deep_equal(before, after):
        raise PolicyError("LEDGER_MANIFESTS_DIFFER")
    paths = []
    package = policy["eligible_map"][skill]["package"]
    for item in before:
        if type(item) is not dict or set(item) != MANIFEST_KEYS:
            raise PolicyError("LEDGER_MANIFEST_ITEM_SCHEMA")
        if not _manifest_path_valid(item["path"], package):
            raise PolicyError("LEDGER_MANIFEST_PATH_SCOPE")
        if not isinstance(item["sha256"], str) or not HASH_RE.fullmatch(item["sha256"]):
            raise PolicyError("LEDGER_MANIFEST_DIGEST_SCHEMA")
        paths.append(item["path"])
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise PolicyError("LEDGER_MANIFEST_ORDER_OR_DUPLICATE")
    expected = policy["eligible_map"][skill]["manifest"]
    if not _deep_equal(before, expected):
        raise PolicyError("LEDGER_MANIFEST_NOT_COMPLETE_BOUND_INVENTORY")
    return stamp


def _parse_new_lines(raw, policy, session, *, window_start, window_end):
    lines = _jsonl_lines(raw)
    seen = set(session["seen_ids"])
    latest = (_timestamp(session["last_timestamp"], null_allowed=False)
              if session["last_timestamp"] else None)
    records = []
    for line in lines:
        enforce_limit("line_bytes_including_lf_max", len(line))
        value = strict_json(line[:-1])
        latest = validate_ledger_record(value, policy, seen, window_start=window_start,
                                        window_end=window_end, previous_timestamp=latest)
        seen.add(value["id"])
        records.append(value)
    return records, seen, latest


def evaluate_ledger(policy, session, capture, *, window_start, window_end):
    baseline = policy["ledger_baseline"]
    previous = base64.b64decode(session["previous_ledger_raw_base64"])
    original = base64.b64decode(baseline["raw_base64"])
    raw = capture["raw"]
    meta = capture["metadata"]
    for field in LEDGER_STRICT:
        if meta[field] != baseline["metadata"][field]:
            raise PolicyError("LEDGER_STRICT_METADATA_CHANGED " + field)
    if meta["st_size"] != len(raw):
        raise PolicyError("LEDGER_CAPTURE_SIZE_BINDING")
    if len(raw) < len(previous) or len(raw) < len(original):
        raise PolicyError("LEDGER_SHRINK")
    if raw[:len(original)] != original:
        raise PolicyError("LEDGER_ORIGINAL_PREFIX_CHANGED")
    if raw[:len(previous)] != previous:
        raise PolicyError("LEDGER_PREVIOUS_PREFIX_CHANGED")
    suffix = raw[len(previous):]
    total_bytes = session["appended_bytes"] + len(suffix)
    enforce_limit("append_total_bytes_max", total_bytes)
    records, seen, latest = _parse_new_lines(suffix, policy, session,
                                             window_start=window_start, window_end=window_end)
    total_records = session["appended_records"] + len(records)
    enforce_limit("appended_records_max", total_records)
    previous_meta = session["previous_ledger_metadata"]
    if suffix:
        if meta["st_size"] <= previous_meta["st_size"]:
            raise PolicyError("LEDGER_GROWTH_METADATA_MISMATCH")
        for field in ("st_mtime_ns", "st_ctime_ns"):
            if meta[field] < previous_meta[field]:
                raise PolicyError("LEDGER_TIME_METADATA_BACKWARDS " + field)
    elif meta != previous_meta:
        raise PolicyError("LEDGER_UNCHANGED_BYTES_METADATA_CHANGED")
    next_session = {**session,
                    "previous_ledger_raw_base64": base64.b64encode(raw).decode("ascii"),
                    "previous_ledger_metadata": meta,
                    "previous_ledger_sha256": capture["sha256"],
                    "seen_ids": sorted(seen),
                    "appended_records": total_records,
                    "appended_bytes": total_bytes,
                    "last_timestamp": latest.isoformat(timespec="microseconds") if latest else session["last_timestamp"]}
    return {"result": "PASS", "capture_id": capture["capture_id"],
            "source_id": capture["source_id"], "appended_this_boundary": len(records),
            "appended_total": total_records, "appended_bytes_total": total_bytes,
            "old_strict": "PASS" if (capture["sha256"] == baseline["sha256"] and
                                         meta == baseline["metadata"]) else "OLD_STRICT_REJECT",
            "next_session": next_session}


def evaluate_lock(policy, capture):
    baseline = policy["lock_baseline"]
    if capture["raw"] or capture["metadata"]["st_size"] != 0:
        raise PolicyError("LOCK_NOT_EMPTY")
    if capture["metadata"] != baseline["metadata"] or capture["sha256"] != baseline["sha256"]:
        raise PolicyError("LOCK_NINE_FIELDS_OR_CONTENT_CHANGED")
    return {"result": "PASS", "capture_id": capture["capture_id"],
            "source_id": capture["source_id"], "old_strict": "PASS"}


def evaluate_root_and_manifests(policy, bundle):
    root = bundle["root"]
    before = policy["root_baseline"]
    for field in ROOT_STRICT:
        if root["metadata"][field] != before["metadata"][field]:
            raise PolicyError("ROOT_STRICT_METADATA_CHANGED " + field)
    if _root_persistent_entries(root) != policy["persistent_entries"]:
        raise PolicyError("ROOT_PERSISTENT_ENTRY_SET_CHANGED")
    if any(TEMP_RE.fullmatch(name) for name in root["entries"]):
        raise PolicyError("PERSISTENT_TEMP_AT_BOUNDARY")
    if bundle["manifests"] != {name: item["manifest"] for name, item in policy["eligible_map"].items()}:
        raise PolicyError("STRICT_PACKAGE_INVENTORY_CHANGED")
    return {"result": "PASS", "capture_id": root["capture_id"]}


def approved_baseline_acceptance(result):
    required = {
        "STRICT_INPUT_INTEGRITY": "PASS",
        "APPROVED_BOOKKEEPING_SEMANTICS": "PASS",
        "CAPTURE_BINDING_COHERENT": "YES",
        "REJECTED_OR_UNRESOLVED_EVENTS": 0,
        "COVERAGE_COMPLETE": "YES",
    }
    return all(result.get(key) == value for key, value in required.items())


def public_bundle(bundle):
    return {"root": {key: value for key, value in bundle["root"].items() if key != "entries"},
            "usage": public_projection(bundle["usage"]),
            "lock": public_projection(bundle["lock"]),
            "ledger": public_projection(bundle["ledger"]),
            "capture_binding": bundle["capture_binding"], "coherent": bundle["coherent"],
            "manifest_counts": {name: len(rows) for name, rows in bundle["manifests"].items()}}


def private_bundle(bundle):
    return {"root": bundle["root"], "usage": private_projection(bundle["usage"]),
            "lock": private_projection(bundle["lock"]), "ledger": private_projection(bundle["ledger"]),
            "capture_binding": bundle["capture_binding"], "coherent": bundle["coherent"],
            "manifests": bundle["manifests"]}
