"""Build the affected-fresh plus historical-applicability qualification capsule."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "executor"))
import coverage


def main() -> int:
    old_path = ROOT.parent / "bookkeeping-v2-20260908T004809Z/qualification/QUALIFICATION.json"
    old = json.loads(old_path.read_text())
    fresh_path = ROOT / "qualification/FRESH_RESULT.json"
    process_path = ROOT / "qualification/FRESH.process.json"
    log_path = ROOT / "qualification/FRESH.native.log"
    fresh = json.loads(fresh_path.read_text())
    process = json.loads(process_path.read_text())
    if fresh.get("result") != "PASS" or fresh.get("tests") != 19 or fresh.get("unique") != 19:
        raise RuntimeError("FRESH_AFFECTED_QUALIFICATION_NOT_PASS")
    if process.get("native_exit") != 0 or process.get("log_sha256") != coverage.digest(log_path):
        raise RuntimeError("FRESH_PROCESS_BINDING")
    if old.get("result") != "PASS" or old.get("tests") != 129:
        raise RuntimeError("HISTORICAL_V2_QUALIFICATION_NOT_PASS")

    exact_names = ("namespaces.py", "artifacts.py", "compile_inventory.py",
                   "vite_closure.py", "packaging.py", "freshness.py", "preservation.py")
    exact_rows = []
    for name in exact_names:
        current = ROOT / "executor" / name
        prior = ROOT / "preimages/executor-v2" / name
        if coverage.digest(current) != coverage.digest(prior):
            raise RuntimeError("UNCHANGED_COMPONENT_DRIFT " + name)
        exact_rows.append({"name": name, "current": str(current), "prior": str(prior),
                           "sha256": coverage.digest(current), "result": "PASS"})
    ledger_path = ROOT / "qualification/MATERIALIZATION_REUSE_LEDGER.json"
    ledger = {
        "schema": "ep19-lean-materialization-reuse-ledger-v1", "result": "PASS",
        "historical_v2_qualification": str(old_path),
        "historical_v2_qualification_sha256": coverage.digest(old_path),
        "historical_129_controls": {"status": "REUSED_PER_HASH_AND_APPLICABILITY_SCOPE",
                                    "fresh_claim": False, "tests": 129},
        "fresh_affected_controls": {"status": "PASS", "tests": fresh["tests"],
                                    "unique": fresh["unique"], "duplicates": fresh["duplicates"],
                                    "result": str(fresh_path), "process": str(process_path),
                                    "log": str(log_path)},
        "exact_unchanged_components": exact_rows,
        "affected_new_components": [str(ROOT / "executor/lean_materialization.py"),
                                    str(ROOT / "executor/lean_preparation.py"),
                                    str(ROOT / "executor/test_lean_materialization.py"),
                                    str(ROOT / "executor/test_lean_binding.py")],
        "retained_contract": "A/B/C, V2 four-field policy, OLD_STRICT diagnostic semantics, actual-decision capture, unchanged strict Collector",
        "formal_boundary_reuse": old["formal_boundary_reuse"],
        "full_capsule_reuse": old["full_capsule_reuse"],
        "formal_product_gate_execution": False,
    }
    coverage.put(ledger_path, ledger)

    helpers = {str(path): coverage.digest(path) for path in coverage.local_imports()[0]}
    dependencies = dict(old["dependencies"])
    extra = [
        old_path, ROOT / "qualification/run_fresh.py", ROOT / "qualification/build.py",
        fresh_path, process_path, log_path, ledger_path,
        ROOT / "BOUNDED_TASK.md", ROOT / "OWNER_AUTHORIZATION.txt",
        ROOT / "inputs/LEAN_CACHE_MATERIALIZATION.historical.json",
        ROOT / "historical/V2_STOP_CONDITION.json", ROOT / "historical/V2_FINAL_FIELDS.json",
        ROOT / "HERMES_REVIEW_NOTES.md",
        ROOT / "historical/parent-verification/LOCAL_AUTHORITY_VERIFICATION.json",
        ROOT / "historical/parent-verification/PRIOR_REMOTE_VERIFICATION.json",
    ]
    extra += [path for path in (ROOT / "qualification/attempts").rglob("*") if path.is_file()]
    extra += [path for path in (ROOT / "tools").rglob("*") if path.is_file()]
    extra += [ROOT / "preimages/executor-v2" / name for name in exact_names]
    dependencies.update(helpers)
    dependencies.update({str(path): coverage.digest(path) for path in extra})
    document = {key: old[key] for key in (
        "real_gradle_instrumentation", "frontend_boundary", "formal_boundary", "collector",
        "coverage", "shadow", "packaging", "freshness", "launch", "bookkeeping_parser",
        "bookkeeping_metadata", "observer_reducer", "decision_evidence", "baseline_seal",
        "preflight", "prestart", "command_boundary", "final_acceptance",
        "launch_reachability", "strict_scope", "evidence_write_failure")}
    document.update({
        "schema": "ep19-lean-materialization-qualified-v1", "result": "PASS",
        "tests": fresh["tests"], "fresh_tests": fresh["tests"], "reused_tests": 129,
        "failures": fresh["failures"], "errors": fresh["errors"], "skipped": fresh["skipped"],
        "unique": fresh["unique"], "duplicates": fresh["duplicates"],
        "fresh_qualification_results": {key: fresh[key] for key in
                                        ("tests", "pass", "failures", "errors", "skipped", "unique", "duplicates")},
        "reused_qualification_scope": "Historical V2 129 controls only per bound bytes and unchanged applicability; not a fresh-129 claim",
        "historical_v2_qualification": str(old_path),
        "materialization_reuse_ledger": str(ledger_path),
        "fresh_result": str(fresh_path), "fresh_process": str(process_path),
        "fresh_log": str(log_path),
        "qualification_program": str(ROOT / "qualification/run_fresh.py"),
        "raw_log": str(log_path), "process_receipt": str(process_path),
        "result_receipt": str(fresh_path),
        "formal_boundary_receipt": old["formal_boundary_receipt"],
        "formal_boundary_reuse": old["formal_boundary_reuse"],
        "full_capsule_reuse": old["full_capsule_reuse"],
        "lean_materialization": "PASS", "link_chain_rejection": "PASS",
        "collector_compatibility": "PASS", "native_probe_binding": "PASS",
        "run_preparation_binding": "PASS", "identity_binding": "PASS",
        "product_gate_execution": False, "mocked_expensive_gates": True,
        "helpers": helpers, "dependencies": dependencies,
    })
    qualification = ROOT / "qualification/QUALIFICATION.json"
    coverage.put(qualification, document)
    coverage.qualification_inputs(qualification)
    print(json.dumps({"result": "PASS", "fresh_tests": fresh["tests"],
                      "reused_tests": 129, "qualification": str(qualification)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
