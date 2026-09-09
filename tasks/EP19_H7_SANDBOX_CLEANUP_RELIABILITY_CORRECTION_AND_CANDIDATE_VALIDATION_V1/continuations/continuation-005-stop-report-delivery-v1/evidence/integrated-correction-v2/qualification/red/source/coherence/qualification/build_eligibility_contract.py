"""Build the final contract only after real review and control evidence exist."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import durability
import eligibility_coherence as coherence

CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
TREE = "fd37409d0274662abbe86f69e3d963c05b379696"
PARENT = "689ab9456461a8d19a72d059f5157092efc43aff"
PATCH = "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690"
AUTHORIZATION = "EP19_ELIGIBILITY_COHERENCE_RECOVERY_AND_CONTROLLED_CLOSURE_V1"
SUCCESSOR = "EP19-ELIGIBILITY-COHERENCE-RECOVERY-SUCCESSOR-V1"
PREDECESSOR = "EP19-EXACT-CANDIDATE-CANONICAL-PUBLICATION-V1"


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ("private-map", "strict-inventory", "instruction-identities",
                 "semantic-acceptance", "dependency", "qualification",
                 "adapter-qualification", "matrix", "implementation-review",
                 "control-plane-implementation", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    mapping = coherence.load(args.private_map)["eligible_skills"]
    strict_source = coherence.load(args.strict_inventory)
    strict = [{"path": row["path"], "sha256": row["sha256"]}
              for row in strict_source["entries"]]
    instructions = coherence.load(args.instruction_identities)["files"]
    semantic = coherence.load(args.semantic_acceptance)
    review = coherence.validate_review(args.implementation_review)
    packages = []
    for skill, manifest in sorted(mapping.items()):
        skill_rows = [row for row in manifest if Path(row["path"]).name == "SKILL.md"]
        if len(skill_rows) != 1: raise RuntimeError("PACKAGE_SKILL_MD_REJECT " + skill)
        packages.append({"skill": skill, "package_root": str(Path(skill_rows[0]["path"]).parent),
                         "manifest": manifest})
    chain = {"candidate": CANDIDATE, "tree": TREE, "product_patch_sha256": PATCH,
        "matrix_sha256": digest(args.matrix), "dependency_sha256": digest(args.dependency),
        "qualification_sha256": digest(args.qualification),
        "adapter_qualification_sha256": digest(args.adapter_qualification),
        "semantic_acceptance_sha256": digest(args.semantic_acceptance),
        "implementation_review_sha256": digest(args.implementation_review),
        "control_plane_implementation_sha256": digest(args.control_plane_implementation)}
    seed = {"candidate": CANDIDATE, "tree": TREE, "chain": chain,
            "strict_inventory": coherence.identity(strict), "instructions": coherence.identity(instructions)}
    contract_id = "ep19-coherence-" + coherence.identity(seed)[:24]
    value = {
        "schema": coherence.SCHEMA, "contract_id": contract_id,
        "task": AUTHORIZATION, "capture_root": str(__import__("bookkeeping_v3").PRODUCTION_ROOT),
        "fixture_only": False,
        "candidate_identity": {"candidate": CANDIDATE, "tree": TREE,
            "immediate_parent": PARENT, "product_patch_sha256": PATCH},
        "attempt_authority": {"authorization_id": AUTHORIZATION, "run_id": "candidate-formal-003",
            "global_ordinal": 3, "historical_consumed": "2/2", "new_allowance_total": 1,
            "new_allowance_used_before": 0, "retry_authorized": False,
            "historical_attempt_ids": ["candidate-formal-001", "candidate-formal-002"]},
        "limits": dict(coherence.EXPECTED_LIMITS), "packages": packages,
        "strict_inventory": strict, "instruction_projection": instructions,
        "semantic_acceptance": {"path": str(args.semantic_acceptance.resolve()),
            "sha256": digest(args.semantic_acceptance), "decision": semantic["decision"],
            "accepted_inputs": semantic["accepted_inputs"], "six_axis_exclusions_bound": True,
            "historical_author_approval": False, "shared_mutation_authorized": False},
        "version_chain": chain,
        "preparation": {"required_receipts": sorted([
            "PREPARATION_COMPATIBILITY.json", "PREPARATION_DISPOSITION.json",
            "PREPARATION_REVALIDATION.json", "PREPARED_ENDPOINTS.json", "bindings.json",
            "lean-materialization.json", "preparation-collector.json", "prepare.json"]),
            "disposition_name": "PREPARATION_DISPOSITION.json"},
        "control_plane": {"successor_id": SUCCESSOR, "predecessor_id": PREDECESSOR,
            "authorization_id": AUTHORIZATION,
            "implementation_sha256": digest(args.control_plane_implementation)},
        "privacy": {"raw_inputs": "PRIVATE_LOCAL_ONLY", "public_whole_inventory": False,
                    "semantic_exclusions_bound": True},
    }
    coherence.validate_contract(value)
    raw = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
    durability.exclusive_bytes(args.output, raw, 0o600)
    print(json.dumps({"contract_id": contract_id, "file_sha256": hashlib.sha256(raw).hexdigest(),
                      "identity_sha256": coherence.identity(value)}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
