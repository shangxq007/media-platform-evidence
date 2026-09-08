"""Bind the completed preparation to the final current helper bytes."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import coverage
import lean_materialization as lm
import lean_preparation
from preservation import Collector


def main() -> int:
    run = ROOT / "outputs/continuation-runs/post-governance-formal-001"
    destination = run / "runtime/cache/backend/formal-tools/lean-4.19.0-linux"
    source = lm.inspect_tree(lean_preparation.PREFERRED, allow_file_links=False)
    target = lm.inspect_tree(destination, allow_file_links=False)
    raw = lm.inspect_tree(lean_preparation.RAW, allow_file_links=True)
    historical = lm.verify_historical_membership(source, lean_preparation.HISTORICAL)
    raw_check = lm.compare_raw_source(raw, lean_preparation.HISTORICAL)
    if lm._projection(source) != lm._projection(target):
        raise RuntimeError("REVALIDATION_FILE_PROJECTION_MISMATCH")
    if lm._directory_projection(source) != lm._directory_projection(target):
        raise RuntimeError("REVALIDATION_DIRECTORY_PROJECTION_MISMATCH")
    source_inodes = {(row["dev"], row["ino"]) for row in source["files"]}
    target_inodes = {(row["dev"], row["ino"]) for row in target["files"]}
    raw_inodes = {(row["dev"], row["ino"]) for row in raw["files"]}
    intersections = {"preferred_destination": len(source_inodes & target_inodes),
                     "preferred_raw": len(source_inodes & raw_inodes),
                     "destination_raw": len(target_inodes & raw_inodes)}
    if any(intersections.values()):
        raise RuntimeError("REVALIDATION_CROSS_TREE_SHARED_INODE " + repr(intersections))
    init_root = run / "runtime/cache/backend/gradle/init.d"
    tools = lean_preparation._resolved_runtime_tools()
    expected = [str(destination / row["path"]) for row in target["files"]]
    expected += [str(init_root / "ep19-packaging.gradle"), *map(str, tools)]
    collector = Collector(roots=[destination, init_root], files=tools,
                          expected_nonempty=[destination, init_root],
                          expected_files=expected).capture()
    if collector["result"] != "COMPLETE" or collector["hashed"] != len(set(expected)):
        raise RuntimeError("REVALIDATION_STRICT_COLLECTOR_REJECT")
    prior = json.loads((run / "PREPARATION_COMPATIBILITY.json").read_text())
    probe = prior["native_toolchain_probe_results"]
    if probe.get("result") != "PASS" or probe.get("system_fallback") is not False:
        raise RuntimeError("REVALIDATION_NATIVE_PROBE_BINDING")
    for row in probe["receipts"]:
        if coverage.digest(row["raw_log"]) != row["log_sha256"] or row["native_exit"] != 0:
            raise RuntimeError("REVALIDATION_NATIVE_PROBE_RECEIPT")
    result = {
        "schema": "ep19-lean-preparation-final-helper-binding-v1", "result": "PASS",
        "run_id": run.name, "materializer_sha256": coverage.digest(ROOT / "executor/lean_materialization.py"),
        "preparation_sha256": coverage.digest(ROOT / "executor/lean_preparation.py"),
        "collector_sha256": coverage.digest(ROOT / "executor/preservation.py"),
        "historical": historical, "raw_links": raw_check,
        "source_summary": {key: source[key] for key in
                           ("file_count", "directory_count_including_root", "symlink_count",
                            "special_count", "shared_inode_alias_count")},
        "destination_summary": {key: target[key] for key in
                                ("file_count", "directory_count_including_root", "symlink_count",
                                 "special_count", "shared_inode_alias_count")},
        "cross_tree_shared_inode_counts": intersections,
        "strict_collector": {"result": collector["result"], "hashed": collector["hashed"],
                             "expected_files": len(set(expected)),
                             "roots": [str(destination), str(init_root)],
                             "resolved_runtime_binaries": [{"path": str(path), "sha256": coverage.digest(path)} for path in tools]},
        "native_probe_receipts_reverified": len(probe["receipts"]),
        "baseline_created": False, "formal_gate_execution": False,
    }
    coverage.put(run / "PREPARATION_REVALIDATION.json", result)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
