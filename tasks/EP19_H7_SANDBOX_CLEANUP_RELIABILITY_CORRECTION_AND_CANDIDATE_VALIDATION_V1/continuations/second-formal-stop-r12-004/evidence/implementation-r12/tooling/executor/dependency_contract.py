"""Validate the reviewed fixed29 consumer and eligibility source closure."""
from pathlib import Path
import ast
import hashlib
import json

CANDIDATE = "a29864343ed4f630b052c20d86c23b240f13cfd0"
LEGACY_SOURCE_ROLES = frozenset({"fixed29_consumer_binding", "current_applicability",
                                 "private_eligible_map", "private_strict_inventory"})
REQUIRED_SOURCE_ROLES = LEGACY_SOURCE_ROLES | frozenset({"product_identity_delta",
                                                         "external_implementation_delta"})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reachable_local_graph():
    """Independently enumerate every local Python import reachable from the formal entry."""
    tooling=Path(__file__).resolve().parent.parent
    roots=(tooling/'executor',tooling/'qualification')
    start=tooling/'executor/external29_driver.py'
    pending=[start];seen=set();edges=[]
    while pending:
        source=pending.pop(0)
        if source in seen:continue
        seen.add(source)
        tree=ast.parse(source.read_text(),filename=str(source))
        imports=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imports.extend(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:imports.append(node.module.split('.')[0])
        for name in sorted(set(imports)):
            target=next((root/(name+'.py') for root in roots if (root/(name+'.py')).is_file()),None)
            if target is None:continue
            edge={'caller':str(source.relative_to(tooling)),'callee':str(target.relative_to(tooling)),'kind':'python-import'}
            edges.append(edge);pending.append(target)
    return {'entrypoint':str(start.relative_to(tooling)),
            'nodes':{str(path.relative_to(tooling)):digest(path) for path in sorted(seen)},
            'edges':sorted(edges,key=lambda row:(row['caller'],row['callee']))}


def _source_rows(value):
    rows = value.get("sources")
    required = REQUIRED_SOURCE_ROLES if value.get("schema")=="ep19-writer-ledger-dependency-binding-v7" else LEGACY_SOURCE_ROLES
    if not isinstance(rows, dict) or set(rows) != required:
        raise RuntimeError("DEPENDENCY_SOURCE_CLOSURE")
    for role, row in rows.items():
        if (not isinstance(row, dict) or set(row) != {"path", "sha256"} or
                not Path(row["path"]).is_absolute() or not Path(row["path"]).is_file() or
                digest(row["path"]) != row["sha256"]):
            raise RuntimeError("DEPENDENCY_SOURCE_BINDING " + role)
    return rows


def validate(value, *, matrix_path):
    if (value.get("schema") not in ("ep19-writer-ledger-dependency-binding-v2",
                                     "ep19-writer-ledger-dependency-binding-v3",
                                     "ep19-writer-ledger-dependency-binding-v4",
                                     "ep19-writer-ledger-dependency-binding-v5",
                                     "ep19-writer-ledger-dependency-binding-v6",
                                     "ep19-writer-ledger-dependency-binding-v7") or
            value.get("result") != "PASS" or
            value.get("ledger_role") != "OBSERVATION_INTEGRITY_ONLY" or
            value.get("ledger_consumers") != ["bookkeeping_v3.evaluate_ledger"] or
            value.get("unbound_dynamic_readers") != []):
        raise RuntimeError("DEPENDENCY_CONTRACT_REJECT")
    for key in ("authorization_source", "instruction_or_skill_selection_source",
                "candidate_selection_source", "policy_or_gate_criteria_source", "rollback_source"):
        if value.get(key) is not False:
            raise RuntimeError("DEPENDENCY_FORBIDDEN_ROLE " + key)
    sources = _source_rows(value)
    if value.get("schema")=="ep19-writer-ledger-dependency-binding-v7":
        product=Path(sources["product_identity_delta"]["path"])
        external=Path(sources["external_implementation_delta"]["path"])
        evidence=json.loads(product.read_text())
        if (product==external or sources["product_identity_delta"]["sha256"]!=
                "4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e" or
                evidence.get("schema")!="ep19-cleanup-identity-delta-v1" or
                evidence.get("candidate")!=CANDIDATE or evidence.get("delta_count")!=27):
            raise RuntimeError("PRODUCT_AND_EXTERNAL_DELTA_PROVENANCE_REJECT")
    matrix = json.loads(Path(matrix_path).read_text())
    fixed = json.loads(Path(sources["fixed29_consumer_binding"]["path"]).read_text())
    if (fixed.get("schema") not in ("ep19-fixed29-consumer-source-binding-v1",
                                     "ep19-fixed29-current-consumer-source-binding-v2",
                                     "ep19-fixed29-current-consumer-source-binding-v3",
                                     "ep19-fixed29-current-consumer-source-binding-v4") or
            fixed.get("count") != 29 or fixed.get("gate_set_exact") is not True or
            fixed.get("order_unique") is not True or
            fixed.get("matrix_sha256") != digest(matrix_path) or
            len(fixed.get("commands", [])) != 29):
        raise RuntimeError("FIXED29_CONSUMER_BINDING_REJECT")
    command_rows=fixed["commands"]
    commands = {row.get("gate"): row for row in command_rows}
    if len(commands)!=len(command_rows) or set(commands) != set(matrix["order"]):
        raise RuntimeError("FIXED29_COMMAND_IDENTITY_REJECT")
    for gate in matrix["order"]:
        row = commands[gate]
        if (row.get("command") != matrix["gates"][gate]["command"] or
                row.get("dependencies") != matrix["gates"][gate]["dependencies"] or
                row.get("argv_ledger_reference") is not False):
            raise RuntimeError("FIXED29_COMMAND_BINDING_REJECT " + gate)
    candidate_sources = fixed.get("candidate_sources")
    helpers = fixed.get("external_helpers")
    if not isinstance(candidate_sources, list) or not candidate_sources or not isinstance(helpers, list) or not helpers:
        raise RuntimeError("CONSUMER_SOURCE_UNIVERSE_EMPTY")
    checkout=Path(matrix_path).resolve().parents[4]/"checkout"
    source_by_path={row.get("candidate_path"):row for row in candidate_sources}
    if len(source_by_path)!=len(candidate_sources):
        raise RuntimeError("CANDIDATE_CONSUMER_SOURCE_DUPLICATE")
    command_sources={path for row in command_rows for path in row.get("direct_candidate_sources",[])}
    if not command_sources<=set(source_by_path):
        raise RuntimeError("CANDIDATE_COMMAND_SOURCE_EDGE_MISSING")
    for row in candidate_sources:
        rel=row.get("candidate_path")
        if (not isinstance(rel,str) or not rel or Path(rel).is_absolute() or ".." in Path(rel).parts or
                row.get("candidate") != CANDIDATE or row.get("working_matches_candidate") is not True or
                row.get("ledger_token_lines") != []):
            raise RuntimeError("CANDIDATE_CONSUMER_SOURCE_REJECT")
        working=Path(row.get("working_path",""))
        if (working != checkout/rel or not working.is_file() or digest(working)!=row.get("working_sha256_before") or
                digest(working)!=row.get("candidate_source_sha256")):
            raise RuntimeError("CANDIDATE_CONSUMER_SOURCE_BYTES_REJECT "+rel)
        local=set(row.get("literal_local_dependencies",[]))
        if not local<=set(source_by_path):
            raise RuntimeError("CANDIDATE_TRANSITIVE_SOURCE_EDGE_MISSING "+rel)
    for row in helpers:
        path=Path(row.get("path",""))
        if (row.get("ledger_token_lines") != [] or not path.is_absolute() or not path.is_file() or
                digest(path)!=row.get("sha256_before")):
            raise RuntimeError("EXTERNAL_HELPER_LEDGER_READER_REJECT")
    applicability = json.loads(Path(sources["current_applicability"]["path"]).read_text())
    if (applicability.get("schema") != "ep19-ledger-current-applicability-v1" or
            applicability.get("eligible_package_count") != len(applicability.get("eligible_packages", [])) or
            applicability.get("private_manifest_sha256") != sources["private_eligible_map"]["sha256"] or
            applicability.get("private_strict_inventory_sha256") != sources["private_strict_inventory"]["sha256"]):
        raise RuntimeError("ELIGIBILITY_PROVENANCE_REJECT")
    origins=applicability.get("instruction_source_bindings")
    if not isinstance(origins,list) or not origins:
        raise RuntimeError("INSTRUCTION_SOURCE_BINDING_MISSING")
    origin_map={row.get("path"):row.get("sha256") for row in origins if isinstance(row,dict)}
    if len(origin_map)!=len(origins):
        raise RuntimeError("INSTRUCTION_SOURCE_BINDING_DUPLICATE")
    for path,wanted in origin_map.items():
        source=Path(path or "")
        if not source.is_absolute() or not source.is_file() or digest(source)!=wanted:
            raise RuntimeError("INSTRUCTION_SOURCE_BYTES_REJECT")
    if not isinstance(applicability.get("selection_rule"),str) or not applicability["selection_rule"]:
        raise RuntimeError("INSTRUCTION_SELECTION_RULE_MISSING")
    private_map=json.loads(Path(sources["private_eligible_map"]["path"]).read_text())
    manifests=private_map.get("eligible_skills",{})
    packages=applicability.get("eligible_packages",[])
    if set(manifests)!={row.get("skill") for row in packages}:
        raise RuntimeError("INSTRUCTION_ELIGIBLE_SET_REJECT")
    for package in packages:
        origins_for_package=package.get("instruction_origins")
        if not isinstance(origins_for_package,list) or not origins_for_package:
            raise RuntimeError("INSTRUCTION_PACKAGE_ORIGIN_MISSING")
        skill_rows=[row for row in manifests[package["skill"]] if Path(row["path"]).name=="SKILL.md"]
        if len(skill_rows)!=1:
            raise RuntimeError("INSTRUCTION_SKILL_MD_BINDING_REJECT")
        for origin in origins_for_package:
            source_path=origin.get("source")
            if source_path not in origin_map:
                raise RuntimeError("INSTRUCTION_SOURCE_ORIGIN_REJECT")
            source_doc=json.loads(Path(source_path).read_text())
            source_rows=source_doc.get("files",source_doc.get("identities",[]))
            wanted_path=skill_rows[0]["path"]
            if not any(row.get("path")==wanted_path and
                       row.get("sha256")==origin.get("declared_skill_md_sha256") for row in source_rows):
                raise RuntimeError("INSTRUCTION_SOURCE_ORIGIN_REJECT")
    if value.get("schema") not in ("ep19-writer-ledger-dependency-binding-v6",
                                    "ep19-writer-ledger-dependency-binding-v7"):
        raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE_STALE_SCHEMA")
    scope=value.get("actual_execution_scope")
    executor=Path(__file__).resolve().parent
    required_nodes=("external29_driver.py","executor_adapter.py","boundary.py","bookkeeping_v3.py","causal.py",
                    "runner.py","decision_evidence.py","baseline_evidence.py",
                    "artifacts.py","durability.py","bindings.py","freshness.py",
                    "parsers.py","vite_closure.py","vite_closure.mjs","parser_tools.py",
                    "vite_resolution.mjs")
    if value.get("schema")=="ep19-writer-ledger-dependency-binding-v7":
        required_nodes=required_nodes+("execution.py","identity_delta.py","binding_contract.py","coverage.py")
    if not isinstance(scope,dict) or set(scope.get("source_nodes",{}))!=set(required_nodes):
        raise RuntimeError("ACTUAL_EXECUTION_SOURCE_EDGE_CLOSURE")
    for name,wanted in scope["source_nodes"].items():
        if digest(executor/name)!=wanted:
            raise RuntimeError("ACTUAL_EXECUTION_SOURCE_EDGE_BYTES "+name)
    expected_edges=[
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
        {"caller":"runner.run_gate[FRONTEND_BUILD]","callee":"vite_resolution.mjs","kind":"mandatory-auxiliary-process"},
        {"caller":"vite_resolution.mjs","callee":"vite.resolveConfig","kind":"runtime-prepared-package-api"},
        {"caller":"runner.prepare","callee":"parser_tools.prepare","kind":"python-call"},
        {"caller":"parser_tools.prepare","callee":"fixed parser package source graph","kind":"durable-materialization"},
        {"caller":"runner.run_gate[FRONTEND_BUILD]","callee":"freshness.require_fresh_outputs","kind":"python-call"},
        {"caller":"freshness.require_fresh_outputs","callee":"parsers.parse[FRONTEND_BUILD]","kind":"parser-callback"},
        {"caller":"parsers.parse[FRONTEND_BUILD]","callee":"vite_closure.validate","kind":"python-call"},
        {"caller":"vite_closure.validate","callee":"vite_closure.mjs","kind":"mandatory-auxiliary-process"},
        {"caller":"runner.run_gate","callee":"artifacts.finalize","kind":"immutable-evidence-copy"},
        {"caller":"artifacts.seal","callee":"durability.exclusive_bytes","kind":"durable-publication"}]
    if value.get("schema")=="ep19-writer-ledger-dependency-binding-v7":
        insertion=20
        expected_edges[insertion:insertion]=[
            {"caller":"external29_driver.preparation","callee":"external29_driver.modules","kind":"sealed-runtime-load"},
            {"caller":"external29_driver.preparation","callee":"runner.prepare","kind":"actual-cli-prepare-call"},
            {"caller":"runner.prepare","callee":"execution.verify_object_source","kind":"pre-namespace-source-verification"},
            {"caller":"execution.verify_object_source","callee":"identity_delta.validate","kind":"product-identity-json-consumer"},
            {"caller":"identity_delta.validate","callee":"product_identity_delta","kind":"exact-path-hash-schema-identity-native-receipt-validation"},
            {"caller":"binding_contract.load","callee":"external_implementation_delta","kind":"separate-external-patch-byte-binding"}]
    if scope.get("edges")!=expected_edges or scope.get("unresolved_actual_dependencies")!=[]:
        raise RuntimeError("ACTUAL_EXECUTION_SOURCE_EDGE_SEMANTICS")
    if scope.get("reachable_local_graph")!=reachable_local_graph():
        raise RuntimeError("ACTUAL_REACHABLE_LOCAL_GRAPH_CLOSURE")
    driver=(executor/"external29_driver.py").read_text()
    adapter=(executor/"executor_adapter.py").read_text()
    boundary=(executor/"boundary.py").read_text()
    runner=(executor/"runner.py").read_text()
    artifacts_source=(executor/"artifacts.py").read_text()
    vite=(executor/"vite_resolution.mjs").read_text()
    parsers=(executor/"parsers.py").read_text()
    closure=(executor/"vite_closure.py").read_text()
    closure_js=(executor/"vite_closure.mjs").read_text()
    parser_materializer=(executor/"parser_tools.py").read_text()
    if ("runner.run_gate(" not in driver or "self.engine.check(" not in adapter or
            "causal.raise_composed(" not in adapter or "formal_failure_document(" not in driver or
            "preflight_blocked_failure(" not in driver or
            "raise_preflight_receipt_persistence_failure(" not in driver or
            "formal_persistence_failure(" not in driver or
            "persist_final_boundary_failure(" not in driver or
            "emit_persistence_uncertainty(" not in driver or
            "raise_diagnostic_emission_failure(" not in driver or
            "emit_native_failure(" not in driver or
            "native_failure_document(" not in driver or
            "bk.evaluate_ledger(" not in boundary or "H/'vite_resolution.mjs'" not in runner or
            "artifacts.finalize(" not in runner or "durability.exclusive_bytes(" not in artifacts_source or
            "resolveConfig" not in vite or "require.resolve('vite')" not in vite or
            "parser_tools.prepare(run)" not in runner or "freshness.require_fresh_outputs(" not in runner or
            "import vite_closure" not in parsers or "vite_closure.validate(" not in parsers or
            "H/'vite_closure.mjs'" not in closure or "subprocess.run(" not in closure or
            "DIRECT_PACKAGES" not in parser_materializer or any(
                token not in closure_js for token in ("req('acorn')","req('postcss')",
                    "req('postcss-value-parser')","req.resolve('parse5')"))):
        raise RuntimeError("ACTUAL_EXECUTION_SOURCE_EDGE_SEMANTICS")
    helper_by_name={Path(row["path"]).name:row for row in helpers}
    required_helpers={"ExposureProbe.java","classpath.init.gradle","collect_frontend.mjs",
                      "compile.init.gradle","packaging.init.gradle","packaging.py","vite_resolution.mjs",
                      "vite_closure.py","vite_closure.mjs","parser_tools.py"}
    if set(helper_by_name)!=required_helpers:
        raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE")
    for name,row in helper_by_name.items():
        path=Path(row["path"])
        actual_lines=[index for index,line in enumerate(path.read_text().splitlines(),1)
                      if ".curator_ledger.jsonl" in line]
        if path!=executor/name or row.get("ledger_token_lines")!=actual_lines:
            raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE")
    expected_command_edges={row["gate"]:row["external_helpers_after_documented_owned_to_H_rewrite"]
                            for row in command_rows
                            if row.get("external_helpers_after_documented_owned_to_H_rewrite")}
    if scope.get("command_helper_edges")!=expected_command_edges:
        raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE")
    for gate,paths in expected_command_edges.items():
        if not paths or any(Path(path)!=executor/Path(path).name or Path(path).name not in required_helpers
                            for path in paths):
            raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE "+gate)
    frontend_helpers=set(expected_command_edges.get("FRONTEND_BUILD",[]))
    if {str(executor/name) for name in ("vite_resolution.mjs","vite_closure.py",
                                       "vite_closure.mjs","parser_tools.py")} - frontend_helpers:
        raise RuntimeError("ACTUAL_HELPER_EDGE_CLOSURE FRONTEND_BUILD")
    runtime_boundary=scope.get("runtime_dependency_boundary",{})
    if set(runtime_boundary)!={"vite","parser_packages"} or "prepared candidate frontend node_modules" not in runtime_boundary["vite"]:
        raise RuntimeError("ACTUAL_RUNTIME_DEPENDENCY_BOUNDARY")
    import parser_tools
    actual_parser_graph=parser_tools.source_graph()
    if scope.get("parser_package_graph")!=actual_parser_graph:
        raise RuntimeError("ACTUAL_PARSER_PACKAGE_GRAPH_CLOSURE")
    graph=scope["parser_package_graph"]
    if (set(graph.get("direct_packages",[]))!={"acorn","postcss","postcss-value-parser","parse5"} or
            not graph.get("nodes") or not graph.get("edges")):
        raise RuntimeError("ACTUAL_PARSER_PACKAGE_GRAPH_CLOSURE")
    for name,row in graph["nodes"].items():
        root=Path(row.get("root",""));package=root/'package.json'
        if (not row.get("version") or package!=Path(row.get("package_json","")) or
                digest(package)!=row.get("package_json_sha256") or
                {str(path.relative_to(root)):digest(path) for path in sorted(root.rglob('*')) if path.is_file()}!=row.get("files")):
            raise RuntimeError("ACTUAL_PARSER_PACKAGE_SOURCE_BYTES "+name)
    disposition=fixed.get("historical_source_disposition",{})
    if set(disposition)!={"PARENT_SOURCE_AFTER","SOURCE_BINDING_BEFORE"} or any(
            row.get("status")!="REPLACED_BY_CURRENT_BYTE_VERIFICATION" for row in disposition.values()):
        raise RuntimeError("HISTORICAL_SOURCE_REPLACEMENT_DISPOSITION")
    return True
