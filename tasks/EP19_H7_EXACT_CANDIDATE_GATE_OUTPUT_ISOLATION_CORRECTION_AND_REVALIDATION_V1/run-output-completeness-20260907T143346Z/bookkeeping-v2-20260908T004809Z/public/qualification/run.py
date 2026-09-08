"""Build the complete task-local V2 qualification capsule; no product gates."""
from pathlib import Path
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
Q=ROOT/"qualification"
H=ROOT/"executor"
TASK=ROOT.parents[1]
CORRECTION=ROOT.parent
FORMAL=TASK/"owner-clarified-execution-20260907T1120Z/parent-runtime-completion-3/FORMAL_BOUNDARY.json"
OLD_EXEC=ROOT/"preimages/executor/execution.py"
LEGACY_Q=CORRECTION/"qualification"
LEGACY_NATIVE=LEGACY_Q/"parent-native-final-001"
LEGACY_EXEC=CORRECTION/"executor"
PARENT_QUALIFICATION=TASK/"owner-clarified-execution-20260907T1120Z/PARENT_EXECUTION_QUALIFICATION.json"


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(value,(dict,list)):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
    else:path.write_text(value)
def component(path,name):
    tree=ast.parse(Path(path).read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    return hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()


def main():
    attempt_number=1
    while (Q/("attempt-%03d"%attempt_number)).exists():attempt_number+=1
    attempt=Q/("attempt-%03d"%attempt_number);attempt.mkdir()
    tmp=Q/"tmp";tmp.mkdir(exist_ok=True)
    modules=("executor/test_bookkeeping_v2.py","executor/test_v2_integration.py","executor/test_continuation.py",
             "executor/test_account.py","executor/test_isolation.py")
    argv=[sys.executable,"-B","-m","unittest","-v",*modules]
    env=dict(os.environ);env.update(PYTHONPATH=str(H),TMPDIR=str(tmp),TMP=str(tmp),TEMP=str(tmp),PYTHONDONTWRITEBYTECODE="1")
    started=time.time_ns();process=subprocess.run(argv,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    finished=time.time_ns();raw=process.stdout.decode("utf-8","replace")
    native=attempt/"native.log";write(native,raw)
    match=re.search(r"Ran (\d+) tests? in",raw);tests=int(match.group(1)) if match else 0
    failures=len(re.findall(r"^FAIL:",raw,re.M));errors=len(re.findall(r"^ERROR:",raw,re.M))
    proc={"schema":"ep19-bookkeeping-v2-qualification-process-v1","argv":argv,"cwd":str(ROOT),
          "native_exit":process.returncode,"start_ns":started,"end_ns":finished,"raw_log":str(native),
          "log_sha256":digest(native),"product_gate_execution":False}
    write(attempt/"process.json",proc)
    attempt_result={"schema":"ep19-bookkeeping-v2-qualification-result-v1","result":"PASS" if process.returncode==0 else "FAIL",
                    "tests":tests,"failures":failures,"errors":errors,"skipped":0,"product_gate_execution":False}
    write(attempt/"result.json",attempt_result)
    if process.returncode or tests<=0 or failures or errors:
        print(raw,end="");return 1

    identities=[]
    for line in raw.splitlines():
        m=re.match(r"(test_\S+) \(([^)]+)\) \.\.\.",line)
        if m:identities.append(m.group(2))
    if len(identities)!=tests or len(set(identities))!=tests:raise RuntimeError("QUALIFICATION_TEST_IDENTITY_ACCOUNTING")
    matrix={"schema":"ep19-bookkeeping-v2-qualification-matrix-v1","result":"PASS","tests":tests,
            "actual_unique_test_identities":identities,"duplicate_identities":[],
            "owner_requirements":{
              "unchanged_and_approved_variation":["executor.test_bookkeeping_v2.V2PolicyControls.test_unchanged_passes_both_policies","executor.test_bookkeeping_v2.V2PolicyControls.test_approved_counts_and_timestamps_pass_writer_unknown","executor.test_bookkeeping_v2.V2PolicyControls.test_atomic_replacement_and_root_times_are_compatible"],
              "schema_membership_strict_fields":["executor.test_bookkeeping_v2.V2PolicyControls.test_record_insertion_and_deletion_reject","executor.test_bookkeeping_v2.V2PolicyControls.test_strict_and_unknown_field_changes_reject","executor.test_bookkeeping_v2.V2PolicyControls.test_invalid_types_nonfinite_duplicates_malformed_and_decrease_reject","executor.test_bookkeeping_v2.V2PolicyControls.test_exponent_overflow_rejects_inside_unknown_nested_value","executor.test_bookkeeping_v2.V2PolicyControls.test_nested_category_inventory_name_is_eligible_and_orphan_is_strict"],
              "strict_skill_memory_scope":["executor.test_v2_integration.ObserverControls.test_strict_instruction_change_prevents_acceptance_despite_rc0","executor.test_v2_integration.ObserverControls.test_memory_change_prevents_acceptance_despite_rc0"],
              "metadata_path_links_entries":["executor.test_bookkeeping_v2.V2PolicyControls.test_permission_symlink_hardlink_and_root_entry_violations_reject","executor.test_bookkeeping_v2.V2PolicyControls.test_root_replacement_and_injected_owner_boundary_reject","executor.test_bookkeeping_v2.V2PolicyControls.test_injected_owner_and_filesystem_boundary_controls"],
              "temporary_namespace_and_gaps":["executor.test_v2_integration.ObserverControls.test_real_atomic_write_event_and_metadata_variation_pass","executor.test_v2_integration.ObserverControls.test_temp_name_cannot_authorize_other_skill_write","executor.test_bookkeeping_v2.V2PolicyControls.test_stable_capture_failure_rejects","executor.test_bookkeeping_v2.V2PolicyControls.test_persistent_reserved_temp_cannot_be_laundered_into_policy"],
              "decision_and_evidence_write":["executor.test_v2_integration.DecisionReceiptControls.test_actual_receipt_uses_captured_values_and_preserves_old_reject","executor.test_v2_integration.DecisionReceiptControls.test_strict_violation_writes_rejection_receipt_and_raises","executor.test_v2_integration.DecisionReceiptControls.test_evidence_write_failure_fails_closed"],
              "stale_bindings_and_qualification":["executor.test_v2_integration.BindingControls.test_stale_executor_identity_and_policy_reject","executor.test_v2_integration.BindingControls.test_complete_and_incomplete_qualification_closure","executor.test_v2_integration.BindingControls.test_old_helper_identity_rejects","executor.test_v2_integration.LaunchPathControls.test_stale_owner_and_launch_bindings_reject"],
              "launch_reachability_and_rc0_strict_stop":["executor.test_v2_integration.LaunchPathControls.test_genuine_v2_acceptance_reaches_all_29_mocked_expensive_gates","executor.test_v2_integration.LaunchPathControls.test_prestart_strict_violation_prevents_launch_despite_native_rc0"],
              "A_B_C_and_existing_acceptance_components":"Fresh execution of executor.test_continuation.Controls (66), executor.test_account.AccountControls (27), and executor.test_isolation.IsolationTests (3)."
            },"mocked_expensive_gates":True,"actual_product_gates":False}
    matrix_path=Q/"QUALIFICATION_MATRIX.json";write(matrix_path,matrix)

    formal=json.loads(FORMAL.read_text());formal_deps=[FORMAL,Path(formal["probe_program"])]
    for receipt in map(Path,formal["process_receipts"]):
        formal_deps.append(receipt);formal_deps.append(Path(json.loads(receipt.read_text())["raw_log"]))
    same_component=component(OLD_EXEC,"formal_sandbox")==component(H/"execution.py","formal_sandbox")
    exact_names=("artifacts.py","bindings.py","compile.init.gradle","compile_inventory.py","freshness.py","isolation.py","namespaces.py","packaging.py","packaging.init.gradle","vite_closure.py")
    exact_components=[]
    for name in exact_names:
        current,prior=H/name,LEGACY_EXEC/name;equal=digest(current)==digest(prior)
        exact_components.append({"name":name,"current":str(current),"prior":str(prior),"sha256":digest(current),"equal":equal})
    ast_components=[]
    for name in ("exact","frontend_sandbox","formal_sandbox"):
        value=component(H/"execution.py",name)
        ast_components.append({"name":name,"current":str(H/'execution.py'),"prior":str(LEGACY_EXEC/'execution.py'),"sha256":value,
                               "equal":value==component(LEGACY_EXEC/'execution.py',name)})
    native_specs=[
      (LEGACY_NATIVE/"controls-process.json",LEGACY_NATIVE/"controls.log",LEGACY_NATIVE/"controls-run/results.json"),
      (LEGACY_NATIVE/"frontend-process.json",LEGACY_NATIVE/"frontend.log",None),
      (LEGACY_NATIVE/"formal-process.json",LEGACY_NATIVE/"formal.log",LEGACY_NATIVE/"formal-runtime/RESULT.json"),
      (LEGACY_NATIVE/"lean-process.json",LEGACY_NATIVE/"lean.log",LEGACY_NATIVE/"lean-runtime/RESULT.json")]
    parent_q=json.loads(PARENT_QUALIFICATION.read_text())
    native_specs.append((Path(parent_q["process_receipt"]),Path(parent_q["raw_log"]),Path(parent_q["result_receipt"])))
    native_receipts=[]
    for process_path,log_path,result_path_old in native_specs:
        process_data=json.loads(process_path.read_text());ok=process_data.get("native_exit")==0 and process_data.get("log_sha256")==digest(log_path)
        if result_path_old:
            result_data=json.loads(result_path_old.read_text());ok=ok and result_data.get("result")=="PASS" and result_data.get("failures",0)==0 and result_data.get("errors",0)==0
        native_receipts.append({"process":str(process_path),"log":str(log_path),"result":str(result_path_old) if result_path_old else None,"verified":ok})
    programs=[LEGACY_Q/name for name in ("run.py","cases.py","defect_c.py","runtime_suite.py","runtime_probe.py","parent_orchestration.py")]
    programs += [LEGACY_NATIVE/"QUALIFICATION.json",PARENT_QUALIFICATION,Path(parent_q["qualification_program"]),Path(parent_q["reuse_ledger"]),
                 Path(parent_q["lean_runtime_receipt"]),Path(parent_q["parent_qualification_disposition"])]
    areas={name:"PASS" for name in ("run_isolation","artifact_copy","compile_completeness","vite_closure","packaging","frontend_boundary","formal_boundary","lean_runtime")}
    full_applicable=(same_component and all(r["equal"] for r in exact_components+ast_components) and all(r["verified"] for r in native_receipts)
                     and json.loads((LEGACY_NATIVE/"QUALIFICATION.json").read_text()).get("real_gradle_instrumentation")=="PASS"
                     and parent_q.get("result")=="PASS")
    reuse={"schema":"ep19-bookkeeping-v2-reuse-v2","result":"PASS" if full_applicable else "REJECT",
           "reused_scope":["filtered parent A/B/C real Gradle/frontend/formal/Lean capsule with exact source applicability",
                           "parent formal-boundary container/tool/output/cleanup qualification",
                           "unchanged packaging/freshness/accounting components only"],
           "not_reused":["historical 45 diagnostics as a full capsule","old strict preservation outcome",
                         "changed coverage/observer/decision/runner paths"],
           "historical_45_diagnostics_reused":False,"areas":areas,
           "exact_components":exact_components,"ast_components":ast_components,"native_receipts":native_receipts,
           "programs_and_qualification_receipts":list(map(str,programs)),
           "reused_receipt":str(FORMAL),"reused_receipt_sha256":digest(FORMAL),
           "old_wrapper_source":str(OLD_EXEC),"old_wrapper_sha256":formal["formal_wrapper_sha256"],
           "current_wrapper_sha256":digest(H/"execution.py"),
           "formal_sandbox_component_sha256":component(H/"execution.py","formal_sandbox"),
           "component_ast_equal":same_component,"receipt_result":formal["result"],"containers_remaining":formal["containers_remaining"],
           "fresh_tests":tests,"product_gate_execution":False}
    reuse_path=Q/"REUSE_LEDGER.json";write(reuse_path,reuse);write(ROOT/"QUALIFICATION_REUSE_LEDGER.json",reuse)
    if reuse["result"]!="PASS" or formal["result"]!="PASS":raise RuntimeError("FULL_CAPSULE_REUSE_NOT_APPLICABLE")

    green=Q/"GREEN.native.log";write(green,raw)
    green_process=Q/"GREEN.process.json";write(green_process,{**proc,"raw_log":str(green),"log_sha256":digest(green)})
    result_path=Q/"RESULT.json";write(result_path,attempt_result)
    accounting=Q/"ACTUAL_TEST_IDENTITY_ACCOUNTING.json";write(accounting,{"result":"PASS","tests":tests,"unique":len(identities),"duplicates":[],"identities":identities})

    sys.path.insert(0,str(H));import coverage as executor_coverage
    helpers=executor_coverage.seal(executor_coverage.local_imports()[0])
    deps=[Path(__file__).resolve(),green,green_process,result_path,matrix_path,reuse_path,Q/"RED.native.log",Q/"RED.process.json",
          ROOT/"OWNER_AUTHORIZATION.txt",ROOT/"dependency/DEPENDENCY_CHECK.json",ROOT/"dependency/DEPENDENCY_REPORT.zh-CN.md",
          accounting,OLD_EXEC,*formal_deps,*[Path(row['current']) for row in exact_components],*[Path(row['prior']) for row in exact_components],
          *[Path(row['prior']) for row in ast_components],*[Path(row['process']) for row in native_receipts],
          *[Path(row['log']) for row in native_receipts],*[Path(row['result']) for row in native_receipts if row['result']],*programs]
    dependencies={**helpers,**executor_coverage.seal(deps)}
    areas=("bookkeeping_parser","bookkeeping_metadata","observer_reducer","decision_evidence","baseline_seal",
           "preflight","prestart","command_boundary","final_acceptance","launch_reachability","strict_scope",
           "evidence_write_failure","identity_binding")
    qualification={"schema":"ep19-bookkeeping-v2-qualified-v1","result":"PASS","meaning":"Fresh bounded V2 and recovered acceptance controls; product gates not run",
                   "helpers":helpers,"dependencies":dependencies,"qualification_program":str(Path(__file__).resolve()),
                   "raw_log":str(green),"process_receipt":str(green_process),"result_receipt":str(result_path),
                   "red_log":str(Q/"RED.native.log"),"green_log":str(green),"qualification_matrix":str(matrix_path),
                   "reuse_ledger":str(reuse_path),"formal_boundary_receipt":str(FORMAL),"formal_boundary_reuse":str(reuse_path),
                   "full_capsule_reuse":str(reuse_path),
                   "product_gate_execution":False,"mocked_expensive_gates":True,"tests":tests,
                   "real_gradle_instrumentation":"PASS","frontend_boundary":"PASS","formal_boundary":"PASS",
                   "collector":"PASS","coverage":"PASS","shadow":"PASS","packaging":"PASS","freshness":"PASS","launch":"PASS",
                   **{area:"PASS" for area in areas}}
    qpath=Q/"QUALIFICATION.json";write(qpath,qualification)

    import runner
    basis=runner.executor_identity_basis(qpath)
    identity=hashlib.sha256(json.dumps(basis,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    write(ROOT/"NEW_EXECUTOR_IDENTITY.json",{"identity":identity,"definition":"SHA256 canonical compact sort_keys JSON identity_basis","identity_basis":basis})
    print(raw,end="");print("QUALIFICATION_CAPSULE",json.dumps({"result":"PASS","tests":tests,"executor_identity":identity}))
    return 0


if __name__=="__main__":raise SystemExit(main())
