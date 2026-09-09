"""Parent-only policy builder for the prebound eligible package map.

Invoking this reads the real bookkeeping inputs and therefore belongs inside the
parent's protected baseline window.  Writer qualification imports only the pure
eligible-map adapter with disposable inputs.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import bookkeeping_v3 as bk


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def eligible_from_applicability(document):
    rows = document.get("eligible_packages")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("ELIGIBLE_APPLICABILITY_MISSING")
    result = {}
    for row in rows:
        if (not isinstance(row, dict) or row.get("eligible") is not True or row.get("errors") != [] or
                not isinstance(row.get("skill"), str) or not isinstance(row.get("package_root"), str)):
            raise RuntimeError("ELIGIBLE_APPLICABILITY_REJECT")
        if row["skill"] in result:
            raise RuntimeError("ELIGIBLE_APPLICABILITY_DUPLICATE")
        result[row["skill"]] = row["package_root"]
    bk.enforce_limit("eligible_skills_max", len(result))
    return result


def build(applicability, private_map, owner, dependency):
    applicability_path, private_path = Path(applicability), Path(private_map)
    app = json.loads(applicability_path.read_text())
    declared = json.loads(private_path.read_text())
    if declared.get("schema") != "ep19-eligible-package-manifest-candidate-v1":
        raise RuntimeError("PRIVATE_ELIGIBLE_MAP_SCHEMA")
    packages = eligible_from_applicability(app)
    policy = bk.create_policy(
        owner_sha256=digest(owner), dependency_sha256=digest(dependency),
        eligible_names=packages)
    actual = {name: row["manifest"] for name, row in policy["eligible_map"].items()}
    if actual != declared.get("eligible_skills"):
        raise RuntimeError("PREBOUND_ELIGIBLE_MANIFEST_CHANGED")
    policy["applicability_sha256"] = digest(applicability_path)
    policy["prebound_eligible_map_sha256"] = digest(private_path)
    return policy


def write_private(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("ZERO_POLICY_WRITE")
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser()
    for name in ("applicability", "private_map", "owner", "dependency", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    write_private(args.output, build(args.applicability, args.private_map,
                                     args.owner, args.dependency))


if __name__ == "__main__":
    main()
