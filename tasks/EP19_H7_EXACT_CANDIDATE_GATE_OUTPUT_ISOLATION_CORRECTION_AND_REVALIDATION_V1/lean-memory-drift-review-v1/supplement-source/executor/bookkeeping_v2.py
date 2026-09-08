"""Owner-authorized V2 verifier for one private Hermes bookkeeping sidecar.

The policy contains a bounded parsed baseline projection and is therefore marked
PRIVATE_NOT_FOR_PUBLIC_PACKAGE.  Public receipts expose hashes, counts, changed
JSON pointers and decisions, never Skill/Memory bodies or full usage records.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import os
import re
import stat

from preservation import FIELDS, absolute, identity, metadata, parent_fd


SCHEMA = "ep19-scoped-runtime-bookkeeping-v2"
OWNER_CONTRACT_VERSION = "OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2"
USAGE_PATH = Path("/home/user/.hermes/skills/.usage.json")
SKILLS_ROOT = USAGE_PATH.parent
LOCK_NAME = ".usage.json.lock"
TEMP_REGEX = r"^\.usage_[a-z0-9_]{8}\.tmp$"
MUTABLE_FIELDS = ("view_count", "use_count", "last_viewed_at", "last_used_at")
COUNT_FIELDS = frozenset(("view_count", "use_count"))
TIME_FIELDS = frozenset(("last_viewed_at", "last_used_at"))
ROOT_STRICT = ("st_dev", "st_ino", "st_mode", "st_uid", "st_gid", "st_nlink")
USAGE_STRICT = ("st_dev", "st_mode", "st_uid", "st_gid", "st_nlink")


class PolicyError(RuntimeError):
    pass


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError("DUPLICATE_JSON_KEY "+str(key))
        result[key] = value
    return result


def _nonfinite(value):
    raise PolicyError("NONFINITE_JSON "+value)


def strict_json(raw: bytes):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PolicyError("MALFORMED_JSON INVALID_UTF8") from exc
    try:
        value=json.loads(text, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    except PolicyError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PolicyError("MALFORMED_JSON "+str(exc)) from exc
    def finite(node):
        if isinstance(node,float) and not math.isfinite(node):raise PolicyError("NONFINITE_JSON EXPONENT_OVERFLOW")
        if isinstance(node,dict):
            for item in node.values():finite(item)
        elif isinstance(node,list):
            for item in node:finite(item)
    finite(value);return value


def _read_stable(path):
    """Return bytes and metadata from one FD-bound, non-symlink stable read."""
    path = absolute(path)
    with parent_fd(path) as (parent, name):
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise PolicyError("USAGE_NOT_REGULAR_OR_SYMLINK "+str(path))
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent)
        try:
            if metadata(before) != metadata(os.fstat(fd)):
                raise PolicyError("USAGE_PATH_BINDING_CHANGED "+str(path))
            chunks = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after_fd = os.fstat(fd)
            after_name = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_name):
                raise PolicyError("USAGE_CAPTURE_UNSTABLE "+str(path))
        finally:
            os.close(fd)
    raw = b"".join(chunks)
    return raw, metadata(before)


def _root_state(root):
    """Stable root identity and direct-child set; no child content is read."""
    root = absolute(root)
    with parent_fd(root) as (parent, name):
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            raise PolicyError("SKILLS_ROOT_NOT_DIRECTORY_OR_SYMLINK "+str(root))
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        try:
            if identity(before) != identity(os.fstat(fd)):
                raise PolicyError("SKILLS_ROOT_PATH_BINDING_CHANGED")
            names = sorted(os.listdir(fd))
            if sorted(os.listdir(fd)) != names:
                raise PolicyError("SKILLS_ROOT_ENTRY_CAPTURE_UNSTABLE")
            after_fd = os.fstat(fd)
            after_name = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if metadata(before) != metadata(after_fd) or metadata(before) != metadata(after_name):
                raise PolicyError("SKILLS_ROOT_CAPTURE_UNSTABLE")
        finally:
            os.close(fd)
    return {"metadata": metadata(before), "entries": names}


def _optional_lock_state(root):
    path = root / LOCK_NAME
    try:
        with parent_fd(path) as (parent, name):
            before = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise PolicyError("LOCK_NOT_REGULAR_OR_SYMLINK")
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=parent)
            try:
                if metadata(before) != metadata(os.fstat(fd)):
                    raise PolicyError("LOCK_PATH_BINDING_CHANGED")
                while os.read(fd, 1024 * 1024):
                    pass
                if metadata(before) != metadata(os.fstat(fd)) or metadata(before) != metadata(os.stat(name, dir_fd=parent, follow_symlinks=False)):
                    raise PolicyError("LOCK_CAPTURE_UNSTABLE")
            finally:
                os.close(fd)
    except FileNotFoundError:
        return {"state": "ABSENT", "path": str(path), "end_state": "MUST_REMAIN_ABSENT"}
    return {"state": "PRESENT", "path": str(path), "metadata": metadata(before),
            "end_state": "PRESERVE_EXACT_IDENTITY_TYPE_OWNER_GROUP_MODE_AND_METADATA"}


def _json_pointer(value):
    return str(value).replace("~", "~0").replace("/", "~1")


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


def _timestamp(value, *, allow_null):
    if value is None:
        if allow_null:
            return None
        raise PolicyError("TIMESTAMP_NULL_REGRESSION")
    if not isinstance(value, str) or not value:
        raise PolicyError("SCHEMA_TIMESTAMP_TYPE")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise PolicyError("SCHEMA_TIMESTAMP_FORMAT") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise PolicyError("SCHEMA_TIMESTAMP_NOT_UTC_AWARE")
    return parsed


def _validate_mutable(field, value, *, baseline=False):
    if field in COUNT_FIELDS:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise PolicyError("SCHEMA_COUNT_NONNEGATIVE_INTEGER "+field)
    elif field in TIME_FIELDS:
        _timestamp(value, allow_null=True)
    else:
        raise PolicyError("UNKNOWN_MUTABLE_FIELD "+field)


def _deep_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(_deep_equal(left[k], right[k]) for k in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(_deep_equal(a, b) for a, b in zip(left, right))
    return left == right


EXCLUDED_SKILL_DIRS=frozenset((".git",".github",".hub",".archive",".curator_backups",".venv","venv","node_modules","site-packages","__pycache__",".tox",".nox",".pytest_cache",".mypy_cache",".ruff_cache"))
SKILL_SUPPORT_DIRS=frozenset(("references","templates","assets","scripts"))

def _frontmatter_name(raw,path):
    lines=[line.strip() for line in raw.decode("utf-8",errors="replace")[:4000].split("\n")]
    fallback=path.parent.name
    if "---" not in lines:return fallback
    block=lines[lines.index("---")+1:];block=block[:block.index("---")] if "---" in block else block
    values=(line.split(":",1)[1].strip().strip("\"'") for line in block if line.startswith("name:"))
    return next((value for value in values if value),fallback)

def _discover_inventory(root):
    """Bounded direct scan mirroring installed local iter_skill_index_files semantics."""
    root=absolute(root);active=None;marker=root/"_org/.active_org"
    if marker.is_file() and not marker.is_symlink():active=marker.read_text(encoding="utf-8").strip() or None
    paths=[];org_root=str(root/"_org")
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs.sort();files.sort();has_skill="SKILL.md" in files
        for name in list(dirs):
            candidate=Path(directory)/name
            if candidate.is_symlink():raise PolicyError("INVENTORY_SYMLINK_DIRECTORY "+str(candidate))
        if directory==str(root) and "_org" in dirs and active is None:dirs.remove("_org")
        elif directory==org_root:dirs[:]=[name for name in dirs if name==active]
        dirs[:]=[name for name in dirs if name not in EXCLUDED_SKILL_DIRS and not (has_skill and name in SKILL_SUPPORT_DIRS)]
        if "SKILL.md" in files:paths.append(Path(directory)/"SKILL.md")
    entries=[]
    for path in sorted(paths):
        raw,meta=_read_stable(path);entries.append({"name":_frontmatter_name(raw,path),"path":str(path),"sha256":sha256(raw),"metadata":meta})
    selected={};duplicates={}
    for row in entries:
        if row["name"] in selected:duplicates.setdefault(row["name"],[selected[row["name"]]["path"]]).append(row["path"])
        else:selected[row["name"]]=row
    return {"scanner":"installed-local-iter_skill_index_files-compatible-v1","entries":entries,
            "selected":selected,"duplicates":duplicates,"selected_names":sorted(selected)}


def create_policy(usage_path=USAGE_PATH, *, owner_sha256, dependency_sha256, selection_binding):
    usage = absolute(usage_path); root = usage.parent
    if usage.name != ".usage.json":
        raise PolicyError("UNAUTHORIZED_BOOKKEEPING_TARGET")
    raw, usage_meta = _read_stable(usage)
    data = strict_json(raw)
    if not isinstance(data, dict) or any(not isinstance(k, str) for k in data):
        raise PolicyError("SCHEMA_ROOT_OBJECT_STRING_KEYS")
    if not stat.S_ISREG(usage_meta["st_mode"]) or usage_meta["st_nlink"] != 1:
        raise PolicyError("USAGE_LINK_COUNT_OR_TYPE")
    inventory=_discover_inventory(root);eligible=set(data)&set(inventory["selected_names"])
    records = {}
    pointers = []
    for record_id in sorted(data):
        value = data[record_id]
        if not isinstance(value, dict):
            raise PolicyError("SCHEMA_RECORD_OBJECT "+record_id)
        mutable = {};is_eligible=record_id in eligible
        for field in MUTABLE_FIELDS:
            if field in value and is_eligible:
                _validate_mutable(field, value[field], baseline=True)
                mutable[field] = value[field]
                pointers.append("/"+_json_pointer(record_id)+"/"+field)
        records[record_id] = {
            "eligible":is_eligible,
            "field_membership": sorted(value),
            "field_schema": {k: _type_name(v) for k, v in sorted(value.items())},
            "strict_values": {k: v for k, v in value.items() if not (is_eligible and k in MUTABLE_FIELDS)},
            "mutable_baseline": mutable,
            "inventory": inventory["selected"].get(record_id),
        }
    root_state = _root_state(root)
    persistent=[name for name in root_state["entries"] if re.fullmatch(TEMP_REGEX,name)]
    if persistent:raise PolicyError("PERSISTENT_RESERVED_TEMP_AT_BASELINE")
    return {
        "schema": SCHEMA,
        "contract_version": OWNER_CONTRACT_VERSION,
        "privacy": "PRIVATE_NOT_FOR_PUBLIC_PACKAGE",
        "target": str(usage),
        "skills_root": str(root),
        "owner_authorization_sha256": owner_sha256,
        "dependency_check_sha256": dependency_sha256,
        "selection_binding": selection_binding,
        "mutable_fields": list(MUTABLE_FIELDS),
        "eligible_record_ids": sorted(eligible),
        "ineligible_record_ids": sorted(set(records)-eligible),
        "eligible_json_pointers": pointers,
        "records": records,
        "inventory_manifest":inventory,
        "baseline_raw_sha256": sha256(raw),
        "baseline_usage_metadata": usage_meta,
        "baseline_root": root_state,
        "lock": _optional_lock_state(root),
        "temporary_namespace": {
            "root": str(root), "direct_child_only": True, "regex": TEMP_REGEX,
            "final_state": "ABSENT", "writer_attribution_required": False,
            "unavailable_short_lived_details": "OBSERVATIONAL_LIMIT_NOT_AUTOMATIC_REJECT",
        },
        "claims_not_made": ["ORIGINAL_ALL_BYTES_AND_METADATA_IMMUTABLE",
                            "COMPLETE_BOOKKEEPING_TRANSACTION_ACCOUNTING",
                            "GLOBAL_WRITER_ATTRIBUTION_ESTABLISHED"],
    }


def is_reserved_temp(path, root=SKILLS_ROOT):
    path, root = Path(path), Path(root)
    return path.parent == root and re.fullmatch(TEMP_REGEX, path.name) is not None


def _changed_metadata(before, current):
    return {k: {"before": before[k], "current": current[k]} for k in FIELDS if before.get(k) != current.get(k)}


def _reason(exc):
    return str(exc) if str(exc) else type(exc).__name__


def evaluate(policy):
    """Compare a fresh stable endpoint to the sealed private baseline projection."""
    result = {
        "schema": "ep19-scoped-runtime-bookkeeping-evaluation-v2",
        "OLD_STRICT_PRESERVATION_RESULT": "OLD_STRICT_REJECT",
        "V2_INPUT_INTEGRITY_RESULT": "REJECT",
        "V2_BOOKKEEPING_EVALUATION": "REJECT",
        "WRITER_ATTRIBUTION": "NOT_ESTABLISHED",
        "OBSERVATION_LIMITS": ["NO_COMPLETE_WRITER_OR_SYSCALL_LEDGER",
                               "SHORT_LIVED_TEMP_CONTENT_MAY_DISAPPEAR_BEFORE_OPEN"],
        "claim": "REJECT",
        "reasons": [],
        "changed_json_pointers": [],
        "observed_metadata_differences": {},
    }
    try:
        if policy.get("schema") != SCHEMA or policy.get("contract_version") != OWNER_CONTRACT_VERSION:
            raise PolicyError("STALE_OR_UNKNOWN_POLICY")
        usage = absolute(policy["target"]); root = absolute(policy["skills_root"])
        if usage != root / ".usage.json":
            raise PolicyError("POLICY_TARGET_BINDING")
        raw, current_meta = _read_stable(usage)
        current = strict_json(raw)
        if not isinstance(current, dict) or any(not isinstance(k, str) for k in current):
            raise PolicyError("SCHEMA_ROOT_OBJECT_STRING_KEYS")
        baseline_meta = policy["baseline_usage_metadata"]
        usage_diffs = _changed_metadata(baseline_meta, current_meta)
        result["observed_metadata_differences"]["usage_file"] = usage_diffs
        if not stat.S_ISREG(current_meta["st_mode"]):
            raise PolicyError("USAGE_NOT_REGULAR_OR_SYMLINK")
        if current_meta["st_nlink"] != 1:
            raise PolicyError("USAGE_LINK_COUNT")
        for field in USAGE_STRICT:
            if field == "st_mode" and current_meta[field] != baseline_meta[field]:
                raise PolicyError("USAGE_MODE_CHANGED")
            if field in ("st_uid", "st_gid") and current_meta[field] != baseline_meta[field]:
                raise PolicyError("USAGE_OWNER_GROUP_CHANGED")
            if field not in ("st_mode", "st_uid", "st_gid", "st_nlink") and current_meta[field] != baseline_meta[field]:
                raise PolicyError("USAGE_FILESYSTEM_BOUNDARY_CHANGED")

        current_root = _root_state(root)
        baseline_root = policy["baseline_root"]
        result["observed_metadata_differences"]["skills_root"] = _changed_metadata(baseline_root["metadata"], current_root["metadata"])
        if current_root["entries"] != baseline_root["entries"]:
            raise PolicyError("ROOT_ENTRY_SET_CHANGED")
        for field in ROOT_STRICT:
            if current_root["metadata"][field] != baseline_root["metadata"][field]:
                raise PolicyError("SKILLS_ROOT_STRICT_METADATA_CHANGED "+field)

        lock = policy["lock"]
        current_lock = _optional_lock_state(root)
        if lock["state"] != current_lock["state"]:
            raise PolicyError("LOCK_END_STATE_CHANGED")
        if lock["state"] == "PRESENT" and current_lock["metadata"] != lock["metadata"]:
            raise PolicyError("LOCK_METADATA_CHANGED")

        baseline_ids = sorted(policy["records"])
        if sorted(current) != baseline_ids:
            raise PolicyError("RECORD_MEMBERSHIP_CHANGED")
        if _discover_inventory(root)!=policy["inventory_manifest"]:
            raise PolicyError("SKILL_INVENTORY_BINDING_CHANGED")
        records = policy["records"]
        for record_id in baseline_ids:
            value = current[record_id]
            if not isinstance(value, dict):
                raise PolicyError("SCHEMA_RECORD_OBJECT "+record_id)
            baseline = records[record_id]
            if sorted(value) != baseline["field_membership"]:
                raise PolicyError("FIELD_MEMBERSHIP_CHANGED "+record_id)
            strict_values = {k: v for k, v in value.items() if not (baseline["eligible"] and k in MUTABLE_FIELDS)}
            if not _deep_equal(strict_values, baseline["strict_values"]):
                raise PolicyError("STRICT_VALUE_CHANGED "+record_id)
            for field, before in baseline["mutable_baseline"].items():
                now = value[field]
                _validate_mutable(field, now)
                if field in COUNT_FIELDS and now < before:
                    raise PolicyError("COUNT_DECREASE "+record_id+" "+field)
                if field in TIME_FIELDS:
                    before_time = _timestamp(before, allow_null=True)
                    now_time = _timestamp(now, allow_null=before is None)
                    if before is not None and now is None:
                        raise PolicyError("TIMESTAMP_NULL_REGRESSION "+record_id+" "+field)
                    if before_time is not None and now_time < before_time:
                        raise PolicyError("TIMESTAMP_BACKWARDS "+record_id+" "+field)
                if not _deep_equal(before, now):
                    result["changed_json_pointers"].append("/"+_json_pointer(record_id)+"/"+field)

        exact_old = (sha256(raw) == policy["baseline_raw_sha256"] and
                     current_meta == baseline_meta and current_root == baseline_root and current_lock == lock)
        result["OLD_STRICT_PRESERVATION_RESULT"] = "PASS" if exact_old else "OLD_STRICT_REJECT"
        result["V2_INPUT_INTEGRITY_RESULT"] = "PASS"
        result["V2_BOOKKEEPING_EVALUATION"] = "PASS"
        variation = bool(result["changed_json_pointers"] or usage_diffs or result["observed_metadata_differences"]["skills_root"])
        result["claim"] = ("STRICT_INPUTS_PRESERVED_WITH_SCOPED_BOOKKEEPING_VARIATION" if variation else
                           "STRICT_INPUTS_PRESERVED_NO_BOOKKEEPING_VARIATION")
        result["baseline_raw_sha256"] = policy["baseline_raw_sha256"]
        result["current_raw_sha256"] = sha256(raw)
        result["current_usage_metadata"] = current_meta
        result["current_root_metadata"] = current_root["metadata"]
        result["current_root_entry_set_sha256"] = sha256(json.dumps(current_root["entries"], ensure_ascii=False, separators=(",", ":")).encode())
        result["record_count"] = len(baseline_ids)
    except Exception as exc:
        result["reasons"].append(_reason(exc))
    return result


def assert_pass(evaluation):
    if evaluation.get("V2_INPUT_INTEGRITY_RESULT") != "PASS" or evaluation.get("V2_BOOKKEEPING_EVALUATION") != "PASS":
        raise PolicyError("V2_BOOKKEEPING_REJECT "+json.dumps(evaluation.get("reasons", [])))
    return evaluation


def capture_binding(policy, row):
    """Bind a generic Collector row to the exact bytes evaluated above."""
    path = policy["target"]
    if path not in row:
        raise PolicyError("BOOKKEEPING_CAPTURE_ROW_MISSING")
    captured = row[path]
    if captured.get("sha256") != policy["baseline_raw_sha256"] or captured.get("metadata") != policy["baseline_usage_metadata"]:
        raise PolicyError("BOOKKEEPING_BASELINE_CAPTURE_UNBOUND")
    return True
