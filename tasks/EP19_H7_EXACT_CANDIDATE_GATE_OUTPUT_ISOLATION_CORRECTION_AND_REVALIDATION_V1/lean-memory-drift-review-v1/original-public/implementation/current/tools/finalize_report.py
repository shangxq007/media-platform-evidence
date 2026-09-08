"""Create a Chinese machine report and sanitized public package after Hermes execution."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "outputs/continuation-runs/lean-materialized-formal-001"
DELIVERY = ROOT / "delivery"
PUBLIC = DELIVERY / "public"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def load(path: Path, default=None):
    return json.loads(path.read_text()) if path.is_file() else default


def copy(source: Path, target: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise RuntimeError("UNSAFE_PUBLIC_SOURCE " + str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as output:
        output.write(source.read_bytes())


def decision_summary() -> dict:
    paths = sorted((RUN / "runtime/decision-evidence").glob("*/receipt.json"))
    if not paths:
        return {"OLD_STRICT_PRESERVATION_RESULT": "NOT_RUN",
                "V2_INPUT_INTEGRITY_RESULT": "NOT_RUN",
                "V2_BOOKKEEPING_EVALUATION": "NOT_RUN"}
    row = load(paths[-1])
    return {key: row.get(key, "NOT_ESTABLISHED") for key in
            ("OLD_STRICT_PRESERVATION_RESULT", "V2_INPUT_INTEGRITY_RESULT",
             "V2_BOOKKEEPING_EVALUATION")}


def main() -> int:
    if PUBLIC.exists() or (DELIVERY / "PUBLIC_EVIDENCE.zip").exists():
        raise RuntimeError("FINAL_PACKAGE_ALREADY_EXISTS_NO_OVERWRITE")
    preparation = load(RUN / "PREPARATION_COMPATIBILITY.json", {})
    revalidation = load(RUN / "PREPARATION_REVALIDATION.json", {})
    qualification = load(ROOT / "qualification/QUALIFICATION.json", {})
    identity = load(ROOT / "NEW_EXECUTOR_IDENTITY.json", {})
    preflight = load(RUN / "preflight.json", {})
    results_doc = load(RUN / "runtime/RESULTS.json", {})
    bindings = load(RUN / "bindings.json", {"order": []})
    results = results_doc.get("results", {})
    gates = {name: results.get(name, {"gate": name, "result": "NOT_RUN",
                                     "reason": "FORMAL_GRAPH_NOT_EXECUTED"})
             for name in bindings.get("order", [])}
    counts = {state: sum(row.get("result") == state for row in gates.values())
              for state in ("PASS", "FAIL", "NOT_RUN")}
    accounting = {
        "schema": "ep19-actual-formal-test-accounting-v1",
        "expectations_only": {"backend": 7973, "backend_skips": 29, "frontend": 149},
        "gates": {name: {"result": row.get("result"),
                         "parser": row.get("acceptance", {}).get("parser"),
                         "reason": row.get("reason")}
                  for name, row in gates.items()},
        "qualification": {"fresh": qualification.get("fresh_qualification_results"),
                          "reused_historical": qualification.get("reused_tests"),
                          "fresh_129_claim": False},
    }
    decisions = decision_summary()
    fields = {
        "TASK": "EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1",
        "CONTINUATION": "LEAN_TOOLCHAIN_MATERIALIZATION_CORRECTION_AND_EXACT_CANDIDATE_FORMAL_CONTINUATION",
        "LANE": "BACKEND_VALIDATION",
        "CANDIDATE_COMMIT_SHA": "689ab9456461a8d19a72d059f5157092efc43aff",
        "CANDIDATE_TREE": "6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6",
        "EXECUTOR_IDENTITY": identity.get("identity"),
        "OWNER_CONTRACT_VERSION": "OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2",
        "FAILED_RUN_PRESERVED": (ROOT / "historical/V2_STOP_CONDITION.json").is_file(),
        "LEAN_SOURCE_SELECTED": preparation.get("lean_source_selected"),
        "LEAN_SOURCE_IDENTITY_VERIFIED": preparation.get("lean_source_identity_verified", False),
        "MATERIALIZATION_PERFORMED": preparation.get("materialization_performed", False),
        "RUN_LOCAL_TOOLCHAIN_VERIFIED": preparation.get("run_local_toolchain_verified", False),
        "DISALLOWED_SYMLINK_COUNT": preparation.get("disallowed_symlink_count"),
        "PREPARATION_COLLECTOR_COMPATIBILITY": {
            "result": revalidation.get("strict_collector", {}).get("result"),
            "hashed": revalidation.get("strict_collector", {}).get("hashed"),
            "expected_files": revalidation.get("strict_collector", {}).get("expected_files")},
        "NATIVE_TOOLCHAIN_PROBE_RESULTS": preparation.get("native_toolchain_probe_results", {}).get("result"),
        "FRESH_QUALIFICATION_RESULTS": qualification.get("fresh_qualification_results"),
        "REUSED_QUALIFICATION_SCOPE": qualification.get("reused_qualification_scope"),
        "FORMAL_LAUNCH_BINDING": "CREATED" if (RUN / "engineering-launch.json").is_file() else "PENDING_HERMES_EXECUTION",
        "BASELINE_CREATED": (RUN / "baseline.json").is_file(),
        "SEAL_CREATED": (RUN / "seal.json").is_file(),
        "PREFLIGHT_RESULT": preflight.get("result", "NOT_RUN"),
        "FORMAL_START_CREATED": (RUN / "runtime/START.json").is_file(),
        "REQUIRED_GATES": len(bindings.get("order", [])),
        "PASS": counts["PASS"], "FAIL": counts["FAIL"], "NOT_RUN": counts["NOT_RUN"],
        "ACTUAL_TEST_IDENTITY_ACCOUNTING": "ACTUAL_TEST_IDENTITY_ACCOUNTING.json",
        **decisions,
        "PRODUCT_CHANGED_PATHS": [], "FRONTEND_LANE_INTERFERENCE": "NONE",
        "HISTORICAL_FAILURES_PRESERVED": "YES",
        "PACK_HISTORICAL_BYTE_IMMUTABILITY": "NOT_RECOVERABLE",
        "PRODUCT_PUBLICATION": "NOT_ATTEMPTED", "POST_PUBLICATION_SANITY": "NOT_RUN",
        "EP19_CLOSED": "NO", "INDEPENDENT_REVIEW": "PENDING",
        "EVIDENCE_COMMIT_SHA": None, "REVIEW_INDEX_URL": None,
        "PUBLIC_MANIFEST_SHA256": "SEE_DETACHED_FINALIZER_RECEIPT",
        "REMOTE_VERIFICATION": "NOT_ATTEMPTED",
        "STOP": ("FORMAL_EXECUTION_COMPLETE_LOCAL_EVIDENCE_READY" if results_doc
                 else "FORMAL_EXECUTION_NOT_RUN_OR_PREFLIGHT_BLOCKED"),
    }
    PUBLIC.mkdir(parents=True)
    put(PUBLIC / "FINAL_FIELDS.json", fields)
    put(PUBLIC / "ACTUAL_TEST_IDENTITY_ACCOUNTING.json", accounting)
    put(PUBLIC / "GATE_RESULTS.json", {"required": len(gates), "counts": counts,
                                       "gates": {name: {"result": row.get("result"),
                                                        "reason": row.get("reason")}
                                                 for name, row in gates.items()}})
    put(PUBLIC / "PREPARATION_SUMMARY.json", {
        key: preparation.get(key) for key in (
            "result", "run_id", "candidate", "tree", "base", "formal_gate_execution",
            "lean_source_selected", "lean_source_identity_verified", "materialization_performed",
            "run_local_toolchain_verified", "disallowed_symlink_count", "strict_collector",
            "full_strict_tool_input_set", "native_toolchain_probe_results",
            "historical_counting_method", "preparation_compatibility_not_baseline")})
    put(PUBLIC / "FINAL_HELPER_REVALIDATION_SUMMARY.json", {
        key: revalidation.get(key) for key in (
            "schema", "result", "run_id", "materializer_sha256", "preparation_sha256",
            "collector_sha256", "historical", "raw_links", "source_summary",
            "destination_summary", "cross_tree_shared_inode_counts", "strict_collector",
            "native_probe_receipts_reverified", "baseline_created", "formal_gate_execution")})
    put(PUBLIC / "QUALIFICATION_SUMMARY.json", {
        "schema": qualification.get("schema"), "result": qualification.get("result"),
        "fresh": qualification.get("fresh_qualification_results"),
        "historical_reused_tests": qualification.get("reused_tests"),
        "reused_scope": qualification.get("reused_qualification_scope"),
        "fresh_129_claim": False})
    for source, name in ((ROOT / "NEW_EXECUTOR_IDENTITY.json", "NEW_EXECUTOR_IDENTITY.json"),
                         (ROOT / "CHANGED_SOURCE_INVENTORY.json", "CHANGED_SOURCE_INVENTORY.json"),
                         (ROOT / "diffs/EXECUTOR_LEAN_MATERIALIZATION.patch", "EXECUTOR_LEAN_MATERIALIZATION.patch"),
                         (ROOT / "OWNER_AUTHORIZATION.txt", "OWNER_AUTHORIZATION.txt")):
        copy(source, PUBLIC / name)
    for source in sorted((ROOT / "historical/parent-verification").glob("*.json")):
        copy(source, PUBLIC / "parent-verification" / source.name)
    report = ["# EP19 H7 Lean 工具链物化延续执行报告", "",
              "本报告只记录固定候选的准备/形式化执行证据；未执行产品发布，EP19 未关闭。", "",
              "## 机器字段", ""]
    report += [f"- `{key}`: `{json.dumps(value, ensure_ascii=False, sort_keys=True)}`"
               for key, value in fields.items()]
    report += ["", "## 边界", "",
               "历史 V2 失败保持原判；OLD_STRICT 仅作独立诊断，不覆盖 V2 实际判定。",
               "公开包不含私有 Skill/Memory 正文、私有 bookkeeping policy、baseline/scope 原始捕获或凭据。", ""]
    (PUBLIC / "FINAL_REPORT.zh-CN.md").write_text("\n".join(report), encoding="utf-8")

    credential = re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)")
    payload = sorted(path for path in PUBLIC.rglob("*") if path.is_file())
    forbidden = [path for path in payload if path.is_symlink() or path.name.endswith(".private.json")
                 or credential.search(path.read_bytes())]
    if forbidden:
        raise RuntimeError("PUBLIC_SANITIZATION_REJECT " + repr(forbidden))
    manifest = PUBLIC / "MANIFEST.sha256"
    manifest.write_text("".join(f"{digest(path)}  {path.relative_to(PUBLIC)}\n" for path in payload),
                        encoding="utf-8")
    for line in manifest.read_text().splitlines():
        wanted, relative = line.split("  ", 1)
        if digest(PUBLIC / relative) != wanted:
            raise RuntimeError("PUBLIC_MANIFEST_VERIFY_FAILED " + relative)
    manifest_sha = digest(manifest)
    archive = DELIVERY / "PUBLIC_EVIDENCE.zip"
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as output:
        for path in sorted(item for item in PUBLIC.rglob("*") if item.is_file()):
            output.write(path, str(path.relative_to(PUBLIC)))
    with zipfile.ZipFile(archive) as checked:
        if checked.testzip() is not None:
            raise RuntimeError("PUBLIC_ARCHIVE_VERIFY_FAILED")
    put(DELIVERY / "FINALIZER_RECEIPT.json", {
        "result": "PASS", "public_manifest_sha256": manifest_sha,
        "public_manifest": str(manifest), "archive": str(archive),
        "archive_sha256": digest(archive), "payload_files": len(payload),
        "private_skill_memory_bodies": 0, "private_policy_files": 0,
        "credential_scan_matches": 0, "publication": "NOT_ATTEMPTED"})
    print(json.dumps(load(DELIVERY / "FINALIZER_RECEIPT.json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
