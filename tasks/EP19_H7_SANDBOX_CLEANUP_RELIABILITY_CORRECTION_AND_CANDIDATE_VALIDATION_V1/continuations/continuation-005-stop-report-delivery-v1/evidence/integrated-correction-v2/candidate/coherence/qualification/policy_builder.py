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
import eligibility_coherence as coherence


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


def validate_provenance(app, private_map, private_inventory, dependency, *, allow_fixture=False):
    if not allow_fixture:
        import dependency_contract
        dependency_contract.validate(dependency, matrix_path=ROOT / "candidate-inputs-v3/GATE_EXECUTION_MATRIX.json")
    if app.get("private_manifest_sha256") != digest(private_map):
        raise RuntimeError("PRIVATE_ELIGIBLE_MAP_PROVENANCE_MISMATCH")
    if app.get("private_strict_inventory_sha256") != digest(private_inventory):
        raise RuntimeError("PRIVATE_STRICT_INVENTORY_PROVENANCE_MISMATCH")
    return True


def build(applicability, private_map, private_inventory, owner, dependency, *,
          coherence_contract=None, coherence_private=None, coherence_public=None,
          capture_phase="FORMAL_POST_CONSUME", allow_fixture=False):
    applicability_path, private_path = Path(applicability), Path(private_map)
    app = json.loads(applicability_path.read_text())
    declared = json.loads(private_path.read_text())
    dependency_value = json.loads(Path(dependency).read_text())
    validate_provenance(app, private_path, private_inventory, dependency_value, allow_fixture=allow_fixture)
    if declared.get("schema") != "ep19-eligible-package-manifest-candidate-v1":
        raise RuntimeError("PRIVATE_ELIGIBLE_MAP_SCHEMA")
    packages = eligible_from_applicability(app)
    contract = None
    if coherence_contract is not None:
        contract = coherence.validate_contract(coherence.load(coherence_contract), allow_fixture=allow_fixture)
        contract_packages = {row["skill"]: row["package_root"] for row in contract["packages"]}
        if packages != contract_packages:
            raise coherence.CoherenceError("APPLICABILITY_CONTRACT_PROJECTION_REJECT")
        declared_packages = declared.get("eligible_skills")
        expected_manifests = {row["skill"]: row["manifest"] for row in contract["packages"]}
        if declared_packages != expected_manifests:
            raise coherence.CoherenceError("PRIVATE_MAP_CONTRACT_SUBSTITUTION_REJECT")
        inventory_value = json.loads(Path(private_inventory).read_text())
        projected_inventory = [{"path": row["path"], "sha256": row["sha256"]}
                               for row in inventory_value.get("entries", [])]
        if projected_inventory != contract["strict_inventory"]:
            raise coherence.CoherenceError("PRIVATE_INVENTORY_CONTRACT_SUBSTITUTION_REJECT")
    started_wall = __import__("time").time_ns()
    started_mono = __import__("time").monotonic_ns()
    policy = bk.create_policy(
        root=Path(contract["capture_root"]) if contract is not None else bk.PRODUCTION_ROOT,
        owner_sha256=digest(owner), dependency_sha256=digest(dependency),
        eligible_names=packages, fixture=bool(contract and contract["fixture_only"]))
    actual = {name: row["manifest"] for name, row in policy["eligible_map"].items()}
    if contract is not None:
        if coherence_private is None or coherence_public is None:
            raise coherence.CoherenceError("FORMAL_COHERENCE_DIAGNOSTIC_TARGETS_REQUIRED")
        capture = coherence.capture_record(actual, capture_phase, started_wall, started_mono)
        policy["eligibility_coherence"] = coherence.evaluate_capture(
            contract, capture, coherence_private, coherence_public)
    elif actual != declared.get("eligible_skills"):
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
