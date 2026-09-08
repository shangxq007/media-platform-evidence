"""Read-only Hermes preparation review. It never creates baseline or review acceptance."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import coverage
import runner


def main() -> int:
    run = runner.runpath("lean-materialized-formal-001")
    required = [run / name for name in (
        "prepare.json", "bindings.json", "namespaces.json", "lean-materialization.json",
        "preparation-collector.json", "PREPARATION_COMPATIBILITY.json",
        "PREPARATION_REVALIDATION.json")]
    if not all(path.is_file() and not path.is_symlink() for path in required):
        raise RuntimeError("PREPARATION_CAPSULE_INCOMPLETE")
    if any((run / name).exists() for name in
           ("baseline.json", "seal.json", "preflight.json", "runtime/START.json")):
        raise RuntimeError("REVIEW_EXPECTED_PRE_BASELINE_STATE")
    preparation = json.loads((run / "PREPARATION_COMPATIBILITY.json").read_text())
    materialization = json.loads((run / "lean-materialization.json").read_text())
    revalidation = json.loads((run / "PREPARATION_REVALIDATION.json").read_text())
    qualification_path = Path(json.loads((run / "prepare.json").read_text())["qualification"])
    qualification = json.loads(qualification_path.read_text())
    closure = coverage.qualification_inputs(qualification_path)
    identity = runner.verify_executor_identity()
    repositories = runner.identities(run)
    checks = {
        "preparation": preparation.get("result") == "PASS",
        "not_baseline": preparation.get("preparation_compatibility_not_baseline") is True,
        "materialization": materialization.get("result") == "PASS",
        "preferred_source": materialization.get("selected_source") == "PREFERRED_HISTORICAL_MATERIALIZED",
        "files": materialization.get("destination_summary", {}).get("file_count") == 4617,
        "symlinks": materialization.get("destination_summary", {}).get("symlink_count") == 0,
        "specials": materialization.get("destination_summary", {}).get("special_count") == 0,
        "aliases": materialization.get("destination_summary", {}).get("shared_inode_alias_count") == 0,
        "collector": preparation.get("strict_collector", {}).get("result") == "COMPLETE",
        "native_probe": preparation.get("native_toolchain_probe_results", {}).get("result") == "PASS",
        "final_helper_revalidation": revalidation.get("result") == "PASS",
        "full_strict_tool_inputs": revalidation.get("strict_collector", {}).get("result") == "COMPLETE"
            and revalidation.get("strict_collector", {}).get("hashed") == 4627
            and revalidation.get("strict_collector", {}).get("expected_files") == 4627,
        "cross_tree_inode_isolation": revalidation.get("cross_tree_shared_inode_counts") == {
            "preferred_destination": 0, "preferred_raw": 0, "destination_raw": 0},
        "system_fallback_absent": preparation.get("native_toolchain_probe_results", {}).get("system_fallback") is False,
        "fresh_19": qualification.get("fresh_tests") == 19 and qualification.get("tests") == 19,
        "historical_129_only_reused": qualification.get("reused_tests") == 129,
        "historical_v2_applicable": coverage.historical_v2_qualification_qualified(qualification),
        "formal_capsule_applicable": coverage.formal_boundary_qualified(qualification),
        "full_capsule_applicable": coverage.full_capsule_reuse_qualified(qualification),
        "three_exact_repositories": len(repositories["repositories"]) == 3,
    }
    result = {
        "schema": "ep19-hermes-readonly-preparation-review-v1",
        "result": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks, "qualification_closure_entries": len(closure),
        "executor_identity": identity["identity"],
        "independent_review": "PENDING",
        "baseline_created": False, "formal_start_created": False,
    }
    print(json.dumps(result, indent=2))
    return int(result["result"] != "PASS")


if __name__ == "__main__":
    raise SystemExit(main())
