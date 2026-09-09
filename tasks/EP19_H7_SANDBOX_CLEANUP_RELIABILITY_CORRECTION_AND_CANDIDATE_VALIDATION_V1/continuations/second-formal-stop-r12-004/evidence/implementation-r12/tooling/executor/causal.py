"""Bounded lossless causal occurrences for executor receipts and exceptions."""
from __future__ import annotations

import hashlib
import uuid

SCHEMA = "ep19-structured-causal-error-v2"
RECEIPT_ATTRIBUTES = (
    "boundary_decision_receipt", "strict_decision_receipt", "preflight_receipt",
    "final_failure_receipt", "runner_gate_receipt", "native_observe_receipt",
)
MAX_CONTEXTS_PER_OCCURRENCE = 32


def _new_id(prefix):
    return prefix + "-" + uuid.uuid4().hex


def _object_id(value, kind, signature):
    """Return a stable process-local ID for one exception occurrence/context."""
    attribute = "_ep19_causal_ids"
    identities = getattr(value, attribute, None)
    if not isinstance(identities, dict):
        identities = {}
        try:
            setattr(value, attribute, identities)
        except BaseException:
            pass
    key = kind + ":" + repr(signature)
    if key not in identities:
        identities[key] = _new_id(kind)
    return identities[key]


def _context(owner, role, stage, association, **extra):
    signature = (role, stage, association, tuple(sorted(extra.items())))
    value = {"context_id": _object_id(owner, "context", signature),
             "parent_context_id": None, "role": str(role), "stage": str(stage),
             "association": str(association)}
    value.update(extra)
    return value


def _normalized(row, *, role, stage, association, index, owner=None):
    value = dict(row)
    value["schema"] = SCHEMA
    value.setdefault("role", role)
    value.setdefault("stage", stage)
    value.setdefault("association", association)
    value.setdefault("leaf_index", index)
    value.setdefault("occurrence_id", (_object_id(owner, "occurrence", index)
                                         if owner is not None else _new_id("occurrence")))
    value["error_type"] = str(value.get("error_type", "UNKNOWN"))
    value["reason"] = str(value.get("reason", ""))
    contexts = value.get("contexts")
    value["contexts"] = [dict(item) for item in contexts] if isinstance(contexts, list) else []
    return value


def _append_context(row, context):
    value = dict(row)
    contexts = [dict(item) for item in value.get("contexts", [])]
    if any(item.get("context_id") == context["context_id"] for item in contexts):
        value["contexts"] = contexts
        return value
    if len(contexts) >= MAX_CONTEXTS_PER_OCCURRENCE:
        value["context_overflow"] = True
        value["contexts"] = contexts
        return value
    outer = next((item for item in reversed(contexts)
                  if item.get("parent_context_id") is None), None)
    if outer is not None:
        outer["parent_context_id"] = context["context_id"]
    contexts.append(dict(context))
    value["contexts"] = contexts
    return value


def _leaf(error, role, stage, association):
    context = _context(error, role, stage, association)
    value = _normalized({"error_type": type(error).__name__, "reason": str(error)},
                        role=role, stage=stage, association=association, index=0,
                        owner=error)
    return _append_context(value, context)


def rows(error, role="secondary", stage="UNSPECIFIED", association="same-operation"):
    """Return every occurrence with stable identity and inner-to-outer contexts."""
    existing = getattr(error, "causal_errors", None)
    if isinstance(existing, list) and existing:
        context = _context(error, role, stage, association)
        result = [_append_context(_normalized(row, role=role, stage=stage,
                    association=association, index=index), context)
                  for index, row in enumerate(existing)]
        result = unique(result)
        try:
            error.causal_errors = result
        except BaseException:
            pass
        return result
    children = list(getattr(error, "exceptions", ()))
    if children:
        group_context = _context(error, role, stage, association,
                                 context_kind="exception-group")
        result = []
        for index, child in enumerate(children):
            child_rows = rows(child, role=role, stage=stage,
                              association=f"{association}/group-child-{index}")
            for row in child_rows:
                result.append(_append_context(row, group_context))
        result = unique(result)
        try:
            error.causal_errors = result
        except BaseException:
            pass
        return result
    result = [_leaf(error, role, stage, association)]
    try:
        error.causal_errors = result
    except BaseException:
        pass
    return result


def _receipt_context_rows(error, values, role, stage, association):
    context = _context(error, role, stage, association, context_kind="receipt-transport")
    return [_append_context(_normalized(row, role=role, stage=stage,
                association=association, index=index), context)
            for index, row in enumerate(values)]


def receipt_rows(error, role="secondary", stage="UNSPECIFIED"):
    result = []
    for attribute in RECEIPT_ATTRIBUTES:
        receipt = getattr(error, attribute, None)
        if not isinstance(receipt, dict):
            continue
        for key in ("causal_errors", "secondary_failures"):
            value = receipt.get(key)
            if isinstance(value, list):
                result.extend(_receipt_context_rows(
                    error, value, role, stage, attribute + "/" + key))
    result.extend(rows(error, role=role, stage=stage))
    marker = getattr(error, "failure_marker_errors", ()) or ()
    if marker:
        result.extend(_receipt_context_rows(
            error, marker, "failure-marker-persistence", "FAILURE_MARKER_PERSISTENCE",
            "failure-marker"))
    return unique(result)


def unique(values):
    """Merge transports of one occurrence; never merge different same-text failures."""
    result = []
    positions = {}
    for index, row in enumerate(values):
        value = _normalized(row, role="secondary", stage="UNSPECIFIED",
                            association="same-operation", index=index)
        occurrence = value["occurrence_id"]
        if occurrence not in positions:
            positions[occurrence] = len(result)
            result.append(value)
            continue
        current = result[positions[occurrence]]
        merged = list(current.get("contexts", []))
        by_id = {item.get("context_id"): item for item in merged}
        for context in value.get("contexts", []):
            context_id = context.get("context_id")
            if context_id not in by_id:
                merged.append(dict(context))
                by_id[context_id] = merged[-1]
            elif (by_id[context_id].get("parent_context_id") is None and
                  context.get("parent_context_id") is not None):
                by_id[context_id]["parent_context_id"] = context["parent_context_id"]
        current["contexts"] = merged[:MAX_CONTEXTS_PER_OCCURRENCE]
        if len(merged) > MAX_CONTEXTS_PER_OCCURRENCE:
            current["context_overflow"] = True
    return result


def record(error, role="secondary", stage="UNSPECIFIED", association="same-operation", **extra):
    retained = rows(error, role=role, stage=stage, association=association)
    first = retained[0]
    value = {"schema": SCHEMA, "role": role, "stage": stage,
             "association": association, "leaf_index": 0,
             "occurrence_id": first["occurrence_id"],
             "error_type": type(error).__name__, "reason": str(error),
             "contexts": list(first.get("contexts", []))}
    if getattr(error, "errno", None) is not None:
        value["errno"] = error.errno
    value.update(extra)
    value["causal_errors"] = retained
    return value


def raise_composed(label, primary, failures, *, dimensions=None, primary_stage=None):
    """Raise primary plus every independent cleanup/persistence occurrence."""
    failures = list(failures)
    if primary is None and not failures:
        return
    if primary is not None and not failures:
        raise primary
    errors = ([primary] if primary is not None else []) + [item[2] for item in failures]
    failure = BaseExceptionGroup(label, errors)
    retained = []
    if primary is not None:
        retained.extend(rows(primary, role="primary", stage=primary_stage or label,
                             association="primary-operation"))
    for role, stage, error in failures:
        retained.extend(rows(error, role=role, stage=stage,
                             association="secondary-for-primary"))
    composition = _context(failure, "composition", label, "causal-composition",
                           context_kind="primary-secondary-composition")
    failure.causal_errors = unique(
        [_append_context(row, composition) for row in retained])
    inherited = dict(getattr(primary, "failure_dimensions", {}) or {}) if primary else {}
    inherited.update(dimensions or {})
    inherited["cleanup_failure"] = bool(failures)
    failure.failure_dimensions = inherited
    raise failure from None


def public_rows(values):
    """Public diagnostics retain occurrence topology/type/stage but no reason/path."""
    result = []
    for index, row in enumerate(values or ()):
        value = _normalized(row, role="secondary", stage="UNSPECIFIED",
                            association="same-operation", index=index)
        reason = value.pop("reason", "")
        value.pop("path", None)
        value.pop("primary_reason", None)
        value.pop("primary_causal_errors", None)
        value["reason_sha256"] = hashlib.sha256(reason.encode()).hexdigest()
        value["reason_exposed"] = False
        result.append(value)
    return result
