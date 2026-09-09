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
import durability


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


def validate_provenance(app, private_map, private_inventory, dependency):
    import dependency_contract
    dependency_contract.validate(dependency, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")
    if app.get("private_manifest_sha256") != digest(private_map):
        raise RuntimeError("PRIVATE_ELIGIBLE_MAP_PROVENANCE_MISMATCH")
    if app.get("private_strict_inventory_sha256") != digest(private_inventory):
        raise RuntimeError("PRIVATE_STRICT_INVENTORY_PROVENANCE_MISMATCH")
    return True


def build(applicability, private_map, private_inventory, owner, dependency):
    applicability_path, private_path = Path(applicability), Path(private_map)
    app = json.loads(applicability_path.read_text())
    declared = json.loads(private_path.read_text())
    dependency_value = json.loads(Path(dependency).read_text())
    validate_provenance(app, private_path, private_inventory, dependency_value)
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
    durability.exclusive_bytes(path, raw, 0o600)


def main():
    parser = argparse.ArgumentParser()
    for name in ("applicability", "private_map", "private_inventory", "owner", "dependency", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    write_private(args.output, build(args.applicability, args.private_map, args.private_inventory,
                                     args.owner, args.dependency))


if __name__ == "__main__":
    main()
