"""Build source-backed r2 fixed29/dependency evidence without executing product code."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
EXECUTOR=ROOT/"executor"
sys.path.insert(0,str(EXECUTOR))
import durability
import dependency_contract
import parser_tools


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    durability.exclusive_bytes(path,(json.dumps(value,indent=2,sort_keys=True)+"\n").encode(),0o400)


def main():
    parser=argparse.ArgumentParser()
    for name in ("historical-fixed","applicability","private-map","private-inventory",
                 "product-identity-delta","external-implementation-delta",
                 "output-fixed","output-dependency"):
        parser.add_argument("--"+name,type=Path,required=True)
    args=parser.parse_args()
    fixed=json.loads(args.historical_fixed.read_text())
    for row in fixed["candidate_sources"]:
        working=Path(row["working_path"])
        actual=digest(working)
        if actual!=row["candidate_source_sha256"] or actual!=row["working_sha256_before"]:
            raise RuntimeError("CURRENT_CANDIDATE_SOURCE_BYTES_REJECT "+row["candidate_path"])
    historical_helpers={Path(row["path"]).name:row for row in fixed["external_helpers"]}
    current_helpers=[]
    for name in sorted(set(historical_helpers)|{"vite_resolution.mjs","vite_closure.py",
                                                "vite_closure.mjs","parser_tools.py"}):
        row=historical_helpers.get(name)
        path=EXECUTOR/name
        if not path.is_file():raise RuntimeError("CURRENT_HELPER_MISSING "+name)
        token_lines=[index for index,line in enumerate(path.read_text().splitlines(),1)
                     if ".curator_ledger.jsonl" in line]
        current_helpers.append({"path":str(path),"sha256_before":digest(path),
                                "lines":len(path.read_text().splitlines()),"ledger_token_lines":token_lines,
                                "ledger_scan_token":".curator_ledger.jsonl",
                                "replaces_historical_path":row["path"] if row else None,
                                "historical_sha256":row["sha256_before"] if row else None})
    helper_paths={Path(row["path"]).name:row["path"] for row in current_helpers}
    for command in fixed["commands"]:
        command["external_helpers_after_documented_owned_to_H_rewrite"]=[
            helper_paths[Path(path).name]
            for path in command.get("external_helpers_after_documented_owned_to_H_rewrite",[])]
    frontend=next(row for row in fixed["commands"] if row["gate"]=="FRONTEND_BUILD")
    frontend["external_helpers_after_documented_owned_to_H_rewrite"] = sorted(set(
        frontend["external_helpers_after_documented_owned_to_H_rewrite"] +
        [helper_paths[name] for name in ("vite_resolution.mjs","vite_closure.py",
                                        "vite_closure.mjs","parser_tools.py")]))
    fixed["schema"]="ep19-fixed29-current-consumer-source-binding-v4"
    fixed["external_helpers"]=current_helpers
    fixed["historical_fixed_source"]={"path":str(args.historical_fixed.resolve()),
                                      "sha256":digest(args.historical_fixed)}
    fixed["historical_source_disposition"]={
        "PARENT_SOURCE_AFTER":{"status":"REPLACED_BY_CURRENT_BYTE_VERIFICATION",
                               "replacement":"candidate_sources working_path bytes + fixed candidate/tree runtime binding"},
        "SOURCE_BINDING_BEFORE":{"status":"REPLACED_BY_CURRENT_BYTE_VERIFICATION",
                                 "replacement":"current external_helpers bytes + full runtime source_binding"}}
    write(args.output_fixed,fixed)
    sources={
        "fixed29_consumer_binding":{"path":str(args.output_fixed.resolve()),"sha256":digest(args.output_fixed)},
        "current_applicability":{"path":str(args.applicability.resolve()),"sha256":digest(args.applicability)},
        "private_eligible_map":{"path":str(args.private_map.resolve()),"sha256":digest(args.private_map)},
        "private_strict_inventory":{"path":str(args.private_inventory.resolve()),"sha256":digest(args.private_inventory)},
        "product_identity_delta":{"path":str(args.product_identity_delta.resolve()),"sha256":digest(args.product_identity_delta)},
        "external_implementation_delta":{"path":str(args.external_implementation_delta.resolve()),"sha256":digest(args.external_implementation_delta)}}
    nodes=("external29_driver.py","executor_adapter.py","boundary.py","bookkeeping_v3.py","causal.py",
           "runner.py","execution.py","identity_delta.py","binding_contract.py","coverage.py",
           "decision_evidence.py","baseline_evidence.py",
           "artifacts.py","durability.py","bindings.py","freshness.py",
           "parsers.py","vite_closure.py","vite_closure.mjs","parser_tools.py",
           "vite_resolution.mjs")
    command_helper_edges={row["gate"]:row["external_helpers_after_documented_owned_to_H_rewrite"]
                          for row in fixed["commands"]
                          if row["external_helpers_after_documented_owned_to_H_rewrite"]}
    dependency={"schema":"ep19-writer-ledger-dependency-binding-v7","result":"PASS",
        "scope":"finite actual r12 external29 preparation consumer plus retained driver/adapter, commands/helpers, parser package graph, product identity evidence, external implementation delta, and eligibility origins",
        "ledger_role":"OBSERVATION_INTEGRITY_ONLY","ledger_consumers":["bookkeeping_v3.evaluate_ledger"],
        "unbound_dynamic_readers":[],"authorization_source":False,
        "instruction_or_skill_selection_source":False,"candidate_selection_source":False,
        "policy_or_gate_criteria_source":False,"rollback_source":False,"sources":sources,
        "actual_execution_scope":{"source_nodes":{name:digest(EXECUTOR/name) for name in nodes},
            "edges":[
                {"caller":"external29_driver.execute_actual_graph","callee":"runner.run_gate","kind":"python-call"},
                {"caller":"external29_driver.boundary","callee":"executor_adapter.RunAdapter.boundary","kind":"adapter-dispatch"},
                {"caller":"executor_adapter.RunAdapter.boundary","callee":"boundary.Engine.check","kind":"python-call"},
                {"caller":"executor_adapter.RunAdapter.boundary","callee":"causal.raise_composed","kind":"rejection-plus-marker-composition"},
                {"caller":"boundary.Engine.check","callee":"bookkeeping_v3.evaluate_ledger","kind":"python-call"},
                {"caller":"external29_driver.engineering_preflight","callee":"external29_driver.latching_strict_check","kind":"mandatory-preflight-call"},
                {"caller":"external29_driver.engineering_preflight","callee":"external29_driver.preflight_blocked_failure","kind":"structured-rejection-before-persistence"},
                {"caller":"external29_driver.engineering_preflight","callee":"runner.put","kind":"actual-preflight-receipt-persistence"},
                {"caller":"external29_driver.engineering_preflight","callee":"external29_driver.raise_preflight_receipt_persistence_failure","kind":"original-plus-persistence-composition"},
                {"caller":"external29_driver.formal","callee":"external29_driver.formal_failure_document","kind":"formal-error-serialization"},
                {"caller":"external29_driver.formal","callee":"external29_driver.formal_persistence_failure","kind":"final-sink-native-fallback"},
                {"caller":"external29_driver.formal","callee":"external29_driver.persist_final_boundary_failure","kind":"actual-final-boundary-receipt-handler"},
                {"caller":"external29_driver.persist_final_boundary_failure","callee":"runner.put","kind":"actual-final-failure-receipt-persistence"},
                {"caller":"external29_driver.persist_final_boundary_failure","callee":"causal.raise_composed","kind":"original-plus-final-receipt-persistence-composition"},
                {"caller":"external29_driver.execute_actual_graph","callee":"external29_driver.emit_persistence_uncertainty","kind":"best-effort-nondurable-gate-diagnostic"},
                {"caller":"external29_driver.execute_actual_graph","callee":"external29_driver.raise_diagnostic_emission_failure","kind":"original-owned-before-diagnostic-composition"},
                {"caller":"external29_driver.raise_diagnostic_emission_failure","callee":"causal.raise_composed","kind":"primary-plus-diagnostic-emission-composition"},
                {"caller":"runner.compare_baseline","callee":"decision_evidence.compare","kind":"actual-gate-decision-evidence"},
                {"caller":"external29_driver.main","callee":"external29_driver.emit_native_failure","kind":"production-native-error-boundary"},
                {"caller":"external29_driver.emit_native_failure","callee":"external29_driver.native_failure_document","kind":"bounded-sanitized-stderr-serialization"},
                {"caller":"external29_driver.preparation","callee":"external29_driver.modules","kind":"sealed-runtime-load"},
                {"caller":"external29_driver.preparation","callee":"runner.prepare","kind":"actual-cli-prepare-call"},
                {"caller":"runner.prepare","callee":"execution.verify_object_source","kind":"pre-namespace-source-verification"},
                {"caller":"execution.verify_object_source","callee":"identity_delta.validate","kind":"product-identity-json-consumer"},
                {"caller":"identity_delta.validate","callee":"product_identity_delta","kind":"exact-path-hash-schema-identity-native-receipt-validation"},
                {"caller":"binding_contract.load","callee":"external_implementation_delta","kind":"separate-external-patch-byte-binding"},
                {"caller":"runner.run_gate[FRONTEND_BUILD]","callee":"vite_resolution.mjs","kind":"mandatory-auxiliary-process"},
                {"caller":"vite_resolution.mjs","callee":"vite.resolveConfig","kind":"runtime-prepared-package-api"},
                {"caller":"runner.prepare","callee":"parser_tools.prepare","kind":"python-call"},
                {"caller":"parser_tools.prepare","callee":"fixed parser package source graph","kind":"durable-materialization"},
                {"caller":"runner.run_gate[FRONTEND_BUILD]","callee":"freshness.require_fresh_outputs","kind":"python-call"},
                {"caller":"freshness.require_fresh_outputs","callee":"parsers.parse[FRONTEND_BUILD]","kind":"parser-callback"},
                {"caller":"parsers.parse[FRONTEND_BUILD]","callee":"vite_closure.validate","kind":"python-call"},
                {"caller":"vite_closure.validate","callee":"vite_closure.mjs","kind":"mandatory-auxiliary-process"},
                {"caller":"runner.run_gate","callee":"artifacts.finalize","kind":"immutable-evidence-copy"},
                {"caller":"artifacts.seal","callee":"durability.exclusive_bytes","kind":"durable-publication"}],
            "command_helper_edges":command_helper_edges,
            "runtime_dependency_boundary":{"vite":"resolved from the prepared candidate frontend node_modules and fixed package-lock during the FRONTEND_BUILD auxiliary",
                "parser_packages":"exact source roots, versions, dependency edges, package.json hashes, and complete copied file hashes are bound in parser_package_graph"},
            "parser_package_graph":parser_tools.source_graph(),
            "reachable_local_graph":dependency_contract.reachable_local_graph(),
            "unresolved_actual_dependencies":[]},
        "accepted_limit":"No assertion about arbitrary future readers; any unknown actual dependency blocks."}
    write(args.output_dependency,dependency)
    print(json.dumps({"fixed":digest(args.output_fixed),"dependency":digest(args.output_dependency)},sort_keys=True))
    return 0


if __name__=="__main__":raise SystemExit(main())
