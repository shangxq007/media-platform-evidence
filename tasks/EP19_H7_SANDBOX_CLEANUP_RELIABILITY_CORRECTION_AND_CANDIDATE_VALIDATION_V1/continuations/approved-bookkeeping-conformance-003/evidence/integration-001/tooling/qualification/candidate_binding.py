"""Build the fresh external identity binding after parent dependency review.

Read-only product checks only.  This program does not prepare a run, establish a
baseline, invoke a gate, or write anywhere except the explicit output path.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
TREE = "fd37409d0274662abbe86f69e3d963c05b379696"
BASE = "86d6aef94fd5e58da552e97c11473cff6eca734e"
PARENT = "689ab9456461a8d19a72d059f5157092efc43aff"
PATCH_SHA256 = "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690"
OWNER_SHA256 = "4f431b08fda1066719b63d9753f5db202f5c1191371c33d9d99fed66dd5b01ff"
MATRIX_SHA256 = "57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_manifest(root):
    root = Path(root)
    return {str(path): digest(path) for path in sorted(root.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


def git(checkout, *args):
    return subprocess.check_output(["git", "-C", str(checkout), *args],
                                   env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).decode().strip()


def build(checkout, owner, dependency, qualification, matrix, tooling_root):
    checkout = Path(checkout).absolute()
    tooling_root = Path(tooling_root).absolute()
    owner, dependency, qualification, matrix = map(lambda value: Path(value).absolute(),
                                                    (owner, dependency, qualification, matrix))
    if git(checkout, "rev-parse", "HEAD") != CANDIDATE:
        raise RuntimeError("CANDIDATE_SHA_MISMATCH")
    if git(checkout, "rev-parse", "HEAD^{tree}") != TREE:
        raise RuntimeError("CANDIDATE_TREE_MISMATCH")
    patch = subprocess.check_output(["git", "-C", str(checkout), "diff", "--binary", PARENT, CANDIDATE],
                                    env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    if hashlib.sha256(patch).hexdigest() != PATCH_SHA256:
        raise RuntimeError("PRODUCT_PATCH_MISMATCH")
    if digest(owner) != OWNER_SHA256:
        raise RuntimeError("OWNER_DECISION_MISMATCH")
    if digest(matrix) != MATRIX_SHA256:
        raise RuntimeError("FIXED29_MATRIX_MISMATCH")
    q = json.loads(qualification.read_text())
    if q.get("schema") != "ep19-approved-bookkeeping-qualification-v3" or q.get("result") != "PASS":
        raise RuntimeError("QUALIFICATION_NOT_FRESH_PASS")
    executor_sources = source_manifest(Path(tooling_root) / "executor")
    qualification_sources = source_manifest(Path(tooling_root) / "qualification")
    if q.get("source_binding") != {**executor_sources, **qualification_sources}:
        raise RuntimeError("QUALIFICATION_SOURCE_BINDING_STALE")
    dep = json.loads(dependency.read_text())
    if dep.get("schema") != "ep19-writer-ledger-dependency-binding-v1":
        raise RuntimeError("LEDGER_DEPENDENCY_SCHEMA_STALE")
    if dep.get("result") != "PASS" or dep.get("ledger_role") != "OBSERVATION_INTEGRITY_ONLY":
        raise RuntimeError("LEDGER_DEPENDENCY_NOT_CLOSED")
    if dep.get("unbound_dynamic_readers"):
        raise RuntimeError("LEDGER_DYNAMIC_READER_UNBOUND")
    forbidden = {"authorization", "instruction_selection", "candidate_selection",
                 "gate_policy", "rollback", "ledger_list"}
    if forbidden & set(dep.get("ledger_consumers", [])):
        raise RuntimeError("LEDGER_FORBIDDEN_CONSUMER")
    return {
        "schema": "ep19-approved-candidate-binding-v3",
        "candidate_sha": CANDIDATE,
        "candidate_tree": TREE,
        "comparison_base": BASE,
        "immediate_parent": PARENT,
        "product_patch_sha256": PATCH_SHA256,
        "product_behavior_changed_in_continuation": False,
        "owner_decision": str(owner), "owner_decision_sha256": digest(owner),
        "dependency_review": str(dependency), "dependency_binding_sha256": digest(dependency),
        "qualification": str(qualification), "qualification_sha256": digest(qualification),
        "matrix": str(matrix), "matrix_sha256": digest(matrix),
        "executor_sources": executor_sources,
        "qualification_sources": qualification_sources,
        "ledger_use": "OBSERVATION_INTEGRITY_ONLY",
        "ledger_consumers": dep.get("ledger_consumers", []),
        "unbound_dynamic_readers": dep.get("unbound_dynamic_readers", []),
        "formal_attempt": False,
    }


def write_exclusive(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("ZERO_BINDING_WRITE")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    for name in ("checkout", "owner", "dependency", "qualification", "matrix", "tooling_root", "output"):
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    args = parser.parse_args()
    write_exclusive(args.output, build(args.checkout, args.owner, args.dependency,
                                       args.qualification, args.matrix, args.tooling_root))


if __name__ == "__main__":
    main()
