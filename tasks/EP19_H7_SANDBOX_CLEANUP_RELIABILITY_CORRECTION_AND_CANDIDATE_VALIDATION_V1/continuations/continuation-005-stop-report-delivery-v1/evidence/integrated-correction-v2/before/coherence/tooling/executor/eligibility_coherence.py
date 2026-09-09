"""Strict, bounded eligibility coherence shared by admission and formal policy.

The expected and actual identities recorded for a decision are derived from the
same in-memory comparison.  Diagnostic persistence never performs a recapture.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import os
import re
import time

import bookkeeping_v3 as bk
import durability

SCHEMA = "ep19-bounded-eligibility-coherence-v1"
SEMANTIC_DECISION = "ACCEPTED_EXACT_INPUTS_FOR_BOUNDED_PROSPECTIVE_TASK_USE"
HASH_RE = re.compile(r"[0-9a-f]{64}")
SKILL_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}")
DIFFERENCE_LIMIT = 128
EXPECTED_LIMITS = {
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
CONTRACT_KEYS = {
    "schema", "contract_id", "task", "capture_root", "fixture_only",
    "candidate_identity", "attempt_authority", "limits", "packages",
    "strict_inventory", "instruction_projection", "semantic_acceptance",
    "version_chain", "preparation", "control_plane", "privacy",
}
PACKAGE_KEYS = {"skill", "package_root", "manifest"}
ROW_KEYS = {"path", "sha256"}


class CoherenceError(RuntimeError):
    def __init__(self, reason, *, comparison=None, diagnostic_errors=()):
        super().__init__(reason)
        self.primary_reason = reason
        self.comparison = comparison
        self.diagnostic_errors = list(diagnostic_errors)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CoherenceError("DUPLICATE_JSON_KEY " + str(key))
        result[key] = value
    return result


def load(path):
    try:
        return json.loads(Path(path).read_bytes().decode("utf-8"), object_pairs_hook=_pairs)
    except CoherenceError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise CoherenceError("STRICT_JSON_REJECT " + str(path)) from exc


def _require(condition, reason):
    if not condition:
        raise CoherenceError(reason)


def _canonical_absolute(value, reason):
    _require(isinstance(value, str) and value, reason)
    path = Path(value)
    _require(path.is_absolute() and ".." not in path.parts and str(path) == os.path.normpath(str(path)), reason)
    return path


def _validate_rows(rows, *, label, root=None, nonempty=True):
    _require(isinstance(rows, list) and (rows or not nonempty), label + "_MISSING")
    _require(len(rows) <= EXPECTED_LIMITS["manifest_items_max"], label + "_LIMIT")
    paths = []
    for row in rows:
        _require(isinstance(row, dict) and set(row) == ROW_KEYS, label + "_UNKNOWN_OR_MISSING_FIELD")
        path = _canonical_absolute(row.get("path"), label + "_NONCANONICAL_PATH")
        if root is not None:
            _require(path.is_relative_to(root) and path != root, label + "_OUT_OF_SCOPE")
        _require(isinstance(row.get("sha256"), str) and HASH_RE.fullmatch(row["sha256"]), label + "_HASH")
        paths.append(str(path))
    _require(len(paths) == len(set(paths)), label + "_DUPLICATE")
    _require(paths == sorted(paths), label + "_NONCANONICAL_ORDER")
    return paths


def validate_contract(value, *, allow_fixture=False):
    _require(isinstance(value, dict) and set(value) == CONTRACT_KEYS, "COHERENCE_CONTRACT_UNKNOWN_OR_MISSING_FIELD")
    _require(value.get("schema") == SCHEMA, "COHERENCE_CONTRACT_SCHEMA")
    _require(isinstance(value.get("contract_id"), str) and value["contract_id"], "COHERENCE_CONTRACT_ID")
    _require(value.get("fixture_only") is False or allow_fixture and value.get("fixture_only") is True,
             "FIXTURE_CONTRACT_FORBIDDEN")
    root = _canonical_absolute(value.get("capture_root"), "CAPTURE_ROOT_NONCANONICAL")
    if not value["fixture_only"]:
        _require(root == bk.PRODUCTION_ROOT, "PRODUCTION_CAPTURE_ROOT_MISMATCH")
    _require(value.get("limits") == EXPECTED_LIMITS == bk.LIMITS, "COHERENCE_LIMITS_CHANGED")
    candidate = value.get("candidate_identity")
    _require(isinstance(candidate, dict) and set(candidate) == {
        "candidate", "tree", "immediate_parent", "product_patch_sha256"
    }, "CANDIDATE_IDENTITY_SCHEMA")
    _require(all(isinstance(candidate.get(key), str) and re.fullmatch(r"[0-9a-f]{40}", candidate[key])
                 for key in ("candidate", "tree", "immediate_parent")), "CANDIDATE_IDENTITY_VALUE")
    _require(isinstance(candidate.get("product_patch_sha256"), str) and
             HASH_RE.fullmatch(candidate["product_patch_sha256"]), "PRODUCT_PATCH_IDENTITY_VALUE")
    attempt = value.get("attempt_authority")
    _require(isinstance(attempt, dict) and set(attempt) == {
        "authorization_id", "run_id", "global_ordinal", "historical_consumed",
        "new_allowance_total", "new_allowance_used_before", "retry_authorized",
        "historical_attempt_ids"
    }, "ATTEMPT_AUTHORITY_SCHEMA")
    _require(attempt.get("global_ordinal") == 3 and attempt.get("historical_consumed") == "2/2" and
             attempt.get("new_allowance_total") == 1 and attempt.get("new_allowance_used_before") == 0 and
             attempt.get("retry_authorized") is False, "EXACT_NEW_ATTEMPT_BUDGET_REJECT")
    _require(attempt.get("historical_attempt_ids") == ["candidate-formal-001", "candidate-formal-002"],
             "HISTORICAL_ATTEMPT_LINK_REJECT")
    _require(isinstance(attempt.get("run_id"), str) and attempt["run_id"] not in attempt["historical_attempt_ids"],
             "NEW_RUN_ID_NOT_UNIQUE")
    packages = value.get("packages")
    _require(isinstance(packages, list) and 0 < len(packages) <= EXPECTED_LIMITS["eligible_skills_max"],
             "PACKAGE_SCOPE_MISSING_OR_LIMIT")
    names = []
    flattened = []
    roots = []
    for package in packages:
        _require(isinstance(package, dict) and set(package) == PACKAGE_KEYS,
                 "PACKAGE_UNKNOWN_OR_MISSING_FIELD")
        name = package.get("skill")
        _require(isinstance(name, str) and SKILL_RE.fullmatch(name), "PACKAGE_SKILL_INVALID")
        package_root = _canonical_absolute(package.get("package_root"), "PACKAGE_ROOT_NONCANONICAL")
        _require(package_root.is_relative_to(root) and package_root != root, "PACKAGE_ROOT_OUT_OF_SCOPE")
        _validate_rows(package.get("manifest"), label="PACKAGE_MANIFEST", root=package_root)
        _require(str(package_root / "SKILL.md") in {row["path"] for row in package["manifest"]},
                 "PACKAGE_SKILL_MD_MISSING")
        names.append(name); roots.append(package_root); flattened.extend(package["manifest"])
    _require(len(names) == len(set(names)), "PACKAGE_DUPLICATE")
    _require(names == sorted(names), "PACKAGE_NONCANONICAL_ORDER")
    _require(len({str(path) for path in roots}) == len(roots), "PACKAGE_ROOT_DUPLICATE")
    strict_rows = value.get("strict_inventory")
    _validate_rows(strict_rows, label="STRICT_INVENTORY")
    _require(strict_rows == sorted(flattened, key=lambda row: row["path"]), "STRICT_INVENTORY_MANIFEST_PROJECTION_MISMATCH")
    instructions = value.get("instruction_projection")
    instruction_paths = _validate_rows(instructions, label="INSTRUCTION_PROJECTION")
    inventory = {row["path"]: row["sha256"] for row in strict_rows}
    _require(all(inventory.get(row["path"]) == row["sha256"] for row in instructions),
             "INSTRUCTION_PROJECTION_OUTSIDE_INVENTORY")
    semantic = value.get("semantic_acceptance")
    _require(isinstance(semantic, dict) and set(semantic) == {
        "path", "sha256", "decision", "accepted_inputs", "six_axis_exclusions_bound",
        "historical_author_approval", "shared_mutation_authorized"
    }, "SEMANTIC_ACCEPTANCE_SCHEMA")
    semantic_path = _canonical_absolute(semantic.get("path"), "SEMANTIC_ACCEPTANCE_PATH")
    _require(semantic_path.is_file() and digest(semantic_path) == semantic.get("sha256"),
             "SEMANTIC_ACCEPTANCE_BYTES_CHANGED")
    decision = load(semantic_path)
    _require(semantic.get("decision") == SEMANTIC_DECISION == decision.get("decision"),
             "SEMANTIC_ACCEPTANCE_DECISION")
    _require(semantic.get("accepted_inputs") == decision.get("accepted_inputs"),
             "SEMANTIC_ACCEPTANCE_INPUTS_MISMATCH")
    _require(semantic.get("six_axis_exclusions_bound") is True and
             semantic.get("historical_author_approval") is False and
             semantic.get("shared_mutation_authorized") is False,
             "SEMANTIC_ACCEPTANCE_EXCLUSIONS_MISSING")
    accepted = {row.get("path"): row.get("sha256") for row in semantic["accepted_inputs"]}
    _require(len(accepted) == len(semantic["accepted_inputs"]) and
             all(path in instruction_paths and inventory.get(path) == wanted for path, wanted in accepted.items()),
             "ACCEPTED_INPUT_NOT_IN_EXACT_PROJECTION")
    for key in ("version_chain", "preparation", "control_plane", "privacy"):
        _require(isinstance(value.get(key), dict), key.upper() + "_SCHEMA")
    return value


def validate_version_chain(contract, config, review):
    chain = contract["version_chain"]
    required = {
        "candidate", "tree", "product_patch_sha256", "matrix_sha256", "dependency_sha256",
        "qualification_sha256", "adapter_qualification_sha256", "semantic_acceptance_sha256",
        "implementation_review_sha256", "control_plane_implementation_sha256",
    }
    _require(set(chain) == required, "VERSION_CHAIN_UNKNOWN_OR_MISSING_FIELD")
    actual = {
        "candidate": config.get("candidate"), "tree": config.get("tree"),
        "product_patch_sha256": config.get("product_patch_sha256"),
        "matrix_sha256": config.get("matrix_sha256"),
        "dependency_sha256": config.get("dependency_sha256"),
        "qualification_sha256": config.get("qualification_sha256"),
        "adapter_qualification_sha256": config.get("adapter_qualification_sha256"),
        "semantic_acceptance_sha256": contract["semantic_acceptance"]["sha256"],
        "implementation_review_sha256": digest(review),
        "control_plane_implementation_sha256": config.get("control_plane_implementation_sha256"),
    }
    _require(chain == actual, "MIXED_VERSION_CHAIN_REJECT")
    _require(config.get("eligibility_contract_sha256") == identity(contract),
             "RUNTIME_ELIGIBILITY_CONTRACT_IDENTITY_REJECT")
    return actual


def validate_review(review):
    value = load(review)
    _require(value.get("implementation_review") == "PASS" and
             value.get("independent_final_acceptance") in ("PENDING", "REQUIRED"),
             "INDEPENDENT_IMPLEMENTATION_REVIEW_REQUIRED")
    return value


def validate_control_plane(contract, control, *, allow_fixture=False):
    value = load(control)
    required = {
        "schema", "result", "fixture_only", "successor_id", "predecessor_id",
        "authorization_id", "candidate", "tree", "product_patch_sha256",
        "historical_formal_consumed", "new_formal_total", "new_formal_used",
        "global_next_ordinal", "successor_registered", "ledger_route_ready",
        "publication_route_ready", "dependencies_ready", "idempotency_key",
        "live_state_mutated_by_writer", "implementation_sha256",
    }
    _require(isinstance(value, dict) and set(value) == required, "CONTROL_PLANE_EVIDENCE_SCHEMA")
    _require(value.get("schema") == "ep19-original-control-plane-admission-evidence-v1" and
             value.get("result") == "PASS", "CONTROL_PLANE_EVIDENCE_NOT_PASS")
    _require(value.get("fixture_only") is False or allow_fixture and value.get("fixture_only") is True,
             "CONTROL_PLANE_FIXTURE_FORBIDDEN")
    expected = contract["control_plane"]
    for key in ("successor_id", "predecessor_id", "authorization_id"):
        _require(value.get(key) == expected.get(key), "CONTROL_PLANE_IDENTITY_REJECT " + key)
    _require(value.get("implementation_sha256") == expected.get("implementation_sha256"),
             "CONTROL_PLANE_IMPLEMENTATION_REJECT")
    candidate = contract["candidate_identity"]
    for key in ("candidate", "tree", "product_patch_sha256"):
        _require(value.get(key) == candidate[key], "CONTROL_PLANE_CANDIDATE_REJECT " + key)
    _require(value.get("historical_formal_consumed") == "2/2" and
             value.get("new_formal_total") == 1 and value.get("new_formal_used") == 0 and
             value.get("global_next_ordinal") == 3, "CONTROL_PLANE_BUDGET_REJECT")
    _require(all(value.get(key) is True for key in (
        "successor_registered", "ledger_route_ready", "publication_route_ready", "dependencies_ready"
    )), "CONTROL_PLANE_READINESS_REJECT")
    _require(value.get("live_state_mutated_by_writer") is False, "WRITER_LIVE_STATE_MUTATION_REJECT")
    _require(isinstance(value.get("idempotency_key"), str) and value["idempotency_key"],
             "CONTROL_PLANE_IDEMPOTENCY_MISSING")
    return value


def validate_control_consumption(contract, receipt, *, admission_control_sha256, allow_fixture=False):
    value = load(receipt)
    required = {"schema", "result", "fixture_only", "successor_id", "authorization_id",
        "candidate", "formal_attempt_id", "historical_formal_consumed", "new_used_before",
        "new_used_after", "global_ordinal", "auto_retry", "idempotency_key", "transaction_id",
        "implementation_sha256", "admission_control_evidence_sha256", "performed_by_parent"}
    _require(isinstance(value, dict) and set(value) == required, "CONTROL_PLANE_CONSUME_EVIDENCE_SCHEMA")
    _require(value.get("schema") == "ep19-original-control-plane-formal-consume-evidence-v1" and
             value.get("result") == "PASS", "CONTROL_PLANE_CONSUME_NOT_PASS")
    _require(value.get("fixture_only") is False or allow_fixture and value.get("fixture_only") is True,
             "CONTROL_PLANE_CONSUME_FIXTURE_FORBIDDEN")
    expected = contract["control_plane"]
    _require(value.get("successor_id") == expected.get("successor_id") and
             value.get("authorization_id") == expected.get("authorization_id") and
             value.get("implementation_sha256") == expected.get("implementation_sha256"),
             "CONTROL_PLANE_CONSUME_IDENTITY_REJECT")
    _require(value.get("candidate") == contract["candidate_identity"]["candidate"] and
             value.get("formal_attempt_id") == "EP19-CANDIDATE-FORMAL-OWNER-EXTENSION-001",
             "CONTROL_PLANE_CONSUME_ATTEMPT_REJECT")
    _require(value.get("historical_formal_consumed") == "2/2" and
             value.get("new_used_before") == 0 and value.get("new_used_after") == 1 and
             value.get("global_ordinal") == 3 and value.get("auto_retry") is False,
             "CONTROL_PLANE_CONSUME_BUDGET_REJECT")
    _require(value.get("admission_control_evidence_sha256") == admission_control_sha256,
             "CONTROL_PLANE_CONSUME_ADMISSION_LINK_REJECT")
    _require(value.get("performed_by_parent") is True and
             all(isinstance(value.get(key), str) and value[key] for key in ("idempotency_key", "transaction_id")),
             "CONTROL_PLANE_CONSUME_TRANSACTION_REJECT")
    return value


def validate_preparation(contract, run):
    run = Path(run)
    preparation = contract["preparation"]
    _require(set(preparation) == {"required_receipts", "disposition_name"}, "PREPARATION_CONTRACT_SCHEMA")
    receipts = preparation["required_receipts"]
    _require(isinstance(receipts, list) and receipts == sorted(set(receipts)) and receipts,
             "PREPARATION_RECEIPT_LIST_REJECT")
    for name in receipts:
        _require(isinstance(name, str) and Path(name).name == name and (run / name).is_file(),
                 "PREPARATION_RECEIPT_MISSING " + str(name))
    disposition_path = run / preparation["disposition_name"]
    disposition = load(disposition_path)
    _require(disposition.get("result") == "READY" and disposition.get("run_id") == run.name,
             "PREPARATION_NOT_READY")
    expected_instructions = {row["path"]: row["sha256"] for row in contract["instruction_projection"]}
    supplied = disposition.get("instruction_inputs")
    inventory = disposition.get("instruction_inventory")
    _require(isinstance(supplied, dict) and isinstance(inventory, dict), "PREPARATION_INPUT_CAPTURE_MISSING")
    roots = [Path(row["package_root"]) for row in contract["packages"]]
    def scoped(source):
        result = {}
        for raw_path, wanted in source.items():
            path = _canonical_absolute(raw_path, "PREPARATION_NONCANONICAL_PATH")
            if any(path.is_relative_to(root) for root in roots):
                result[str(path)] = wanted
        return result
    _require(scoped(supplied) == expected_instructions, "PREPARATION_INSTRUCTION_PROJECTION_REJECT")
    expected_inventory = {row["path"]: row["sha256"] for row in contract["strict_inventory"]}
    _require(scoped(inventory) == expected_inventory, "PREPARATION_STRICT_INVENTORY_PROJECTION_REJECT")
    return {"disposition_path": str(disposition_path), "disposition_sha256": digest(disposition_path),
            "receipt_sha256": {name: digest(run / name) for name in receipts}}


def actual_from_policy(policy):
    return {name: row["manifest"] for name, row in sorted(policy["eligible_map"].items())}


def capture_actual(contract, phase):
    started_wall = time.time_ns(); started_mono = time.monotonic_ns()
    packages = {row["skill"]: row["package_root"] for row in contract["packages"]}
    eligible = bk.bind_eligible_packages(Path(contract["capture_root"]), packages)
    actual = {name: row["manifest"] for name, row in sorted(eligible.items())}
    return capture_record(actual, phase, started_wall, started_mono)


def capture_record(actual, phase, started_wall_ns=None, started_monotonic_ns=None):
    started_wall_ns = time.time_ns() if started_wall_ns is None else started_wall_ns
    started_monotonic_ns = time.monotonic_ns() if started_monotonic_ns is None else started_monotonic_ns
    finished_mono = time.monotonic_ns(); finished_wall = time.time_ns()
    return {"phase": phase, "started_wall_ns": started_wall_ns, "finished_wall_ns": finished_wall,
            "started_monotonic_ns": started_monotonic_ns, "finished_monotonic_ns": finished_mono,
            "complete": True, "actual": actual,
            "capture_id": identity({"phase": phase, "actual": actual, "started_wall_ns": started_wall_ns,
                                    "finished_wall_ns": finished_wall, "finished_monotonic_ns": finished_mono})}


def _add(differences, classification, package, path=None, expected=None, actual=None):
    differences.append({"classification": classification, "package": package, "path": path,
                        "expected_sha256": expected, "actual_sha256": actual})


def compare(contract, capture):
    expected = {row["skill"]: row["manifest"] for row in contract["packages"]}
    actual = capture.get("actual")
    differences = []
    if not isinstance(actual, dict):
        _add(differences, "ACTUAL_CAPTURE_SCHEMA", None)
        actual = {}
    expected_names = list(expected)
    actual_names = list(actual)
    if actual_names != sorted(actual_names):
        _add(differences, "PACKAGE_ORDER", None)
    for name in expected_names:
        if name not in actual:
            _add(differences, "PACKAGE_MISSING", name)
    for name in actual_names:
        if name not in expected:
            _add(differences, "PACKAGE_EXTRA", name)
    for name in sorted(set(expected) & set(actual)):
        rows = actual[name]
        if not isinstance(rows, list):
            _add(differences, "MANIFEST_SCHEMA", name); continue
        paths = [row.get("path") for row in rows if isinstance(row, dict)]
        if len(paths) != len(rows) or any(set(row) != ROW_KEYS for row in rows if isinstance(row, dict)):
            _add(differences, "MANIFEST_UNKNOWN_OR_MISSING_FIELD", name)
        if paths != sorted(paths):
            _add(differences, "PATH_ORDER", name)
        for path, count in Counter(paths).items():
            if count > 1:
                _add(differences, "PATH_DUPLICATE", name, path)
        expected_rows = {row["path"]: row["sha256"] for row in expected[name]}
        actual_rows = {row.get("path"): row.get("sha256") for row in rows if isinstance(row, dict)}
        package_root = Path(next(row["package_root"] for row in contract["packages"] if row["skill"] == name))
        for path in paths:
            try:
                candidate = _canonical_absolute(path, "ACTUAL_PATH_NONCANONICAL")
                if not candidate.is_relative_to(package_root) or candidate == package_root:
                    _add(differences, "PATH_OUT_OF_SCOPE", name, path)
            except CoherenceError:
                _add(differences, "PATH_NONCANONICAL", name, path)
        for path in sorted(set(expected_rows) - set(actual_rows)):
            _add(differences, "PATH_MISSING", name, path, expected_rows[path], None)
        for path in sorted(set(actual_rows) - set(expected_rows), key=lambda item: str(item)):
            _add(differences, "PATH_EXTRA", name, path, None, actual_rows[path])
        for path in sorted(set(expected_rows) & set(actual_rows)):
            if expected_rows[path] != actual_rows[path]:
                _add(differences, "CONTENT_HASH_MISMATCH", name, path,
                     expected_rows[path], actual_rows[path])
    total = len(differences); bounded = differences[:DIFFERENCE_LIMIT]
    expected_id = identity(expected); actual_id = identity(actual)
    result = "PASS" if not differences and capture.get("complete") is True else "REJECT"
    return {
        "schema": "ep19-eligibility-coherence-comparison-v1", "result": result,
        "primary_reject": None if result == "PASS" else bounded[0]["classification"] if bounded else "CAPTURE_INCOMPLETE",
        "contract_id": contract["contract_id"], "phase": capture.get("phase"),
        "capture_id": capture.get("capture_id"), "capture_started_wall_ns": capture.get("started_wall_ns"),
        "capture_finished_wall_ns": capture.get("finished_wall_ns"),
        "capture_started_monotonic_ns": capture.get("started_monotonic_ns"),
        "capture_finished_monotonic_ns": capture.get("finished_monotonic_ns"),
        "capture_complete": capture.get("complete") is True,
        "expected_identity": expected_id, "actual_identity": actual_id,
        "expected": expected, "actual": actual, "difference_count": total,
        "differences": bounded, "difference_limit": DIFFERENCE_LIMIT,
        "differences_truncated": total > DIFFERENCE_LIMIT,
        "differences_omitted": max(0, total - DIFFERENCE_LIMIT),
    }


def public_projection(comparison):
    return {key: comparison[key] for key in (
        "schema", "result", "primary_reject", "contract_id", "phase", "capture_id",
        "capture_started_wall_ns", "capture_finished_wall_ns", "capture_started_monotonic_ns",
        "capture_finished_monotonic_ns", "capture_complete", "expected_identity", "actual_identity",
        "difference_count", "differences", "difference_limit", "differences_truncated",
        "differences_omitted",
    )}


def _write(path, value, mode):
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
    durability.exclusive_bytes(path, raw, mode)


def persist(comparison, private_path, public_path):
    errors = []
    for label, path, value, mode in (
        ("private", private_path, comparison, 0o600),
        ("public", public_path, public_projection(comparison), 0o400),
    ):
        try:
            _write(path, value, mode)
        except BaseException as exc:
            errors.append({"sink": label, "path": str(path), "error_type": type(exc).__name__,
                           "reason": str(exc)})
    if errors:
        raise CoherenceError(comparison.get("primary_reject") or "COHERENCE_DIAGNOSTIC_PERSISTENCE_REJECT",
                             comparison=comparison, diagnostic_errors=errors)
    if comparison["result"] != "PASS":
        raise CoherenceError(comparison["primary_reject"], comparison=comparison)
    return public_projection(comparison)


def evaluate_capture(contract, capture, private_path, public_path):
    comparison = compare(contract, capture)
    return persist(comparison, private_path, public_path)
