"""Assemble public-safe local evidence; excludes private policy/usage projections."""
from pathlib import Path
import difflib
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1];CURRENT=ROOT/"executor";PRE=ROOT/"preimages/executor"

def dh(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n" if isinstance(value,(dict,list)) else value)

def main():
    current={p.relative_to(CURRENT) for p in CURRENT.iterdir() if p.is_file()}
    prior={p.relative_to(PRE) for p in PRE.iterdir() if p.is_file()}
    rows=[];patch=[]
    for rel in sorted(current|prior):
        before=PRE/rel;after=CURRENT/rel
        bh=dh(before) if before.is_file() else None;ah=dh(after) if after.is_file() else None
        if bh==ah:continue
        rows.append({"path":str(Path("executor")/rel),"change":"ADDED" if bh is None else "REMOVED" if ah is None else "MODIFIED",
                     "preimage":str(before) if bh else None,"before_sha256":bh,"after_sha256":ah,
                     "mode":oct(after.stat().st_mode&0o777) if after.exists() else None})
        old=before.read_text(errors="replace").splitlines(True) if before.is_file() else []
        new=after.read_text(errors="replace").splitlines(True) if after.is_file() else []
        patch.extend(difflib.unified_diff(old,new,fromfile=str(before) if bh else "/dev/null",tofile=str(after) if ah else "/dev/null"))
    inventory={"schema":"ep19-bookkeeping-v2-changed-source-inventory-v1","result":"PASS","changed_count":len(rows),
               "changed":rows,"unchanged_executor_files":len(current&prior)-sum(1 for r in rows if r['change']=='MODIFIED'),
               "product_changed_paths":[],"git_mutations":False,"formal_product_gates_run":False}
    write(ROOT/"CHANGED_SOURCE_INVENTORY.json",inventory);write(ROOT/"diffs/EXECUTOR_V2.patch","".join(patch))

    identity=json.loads((ROOT/"NEW_EXECUTOR_IDENTITY.json").read_text())['identity']
    final={"TASK":"EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1",
      "CONTINUATION":"SCOPED_RUNTIME_BOOKKEEPING_CONTRACT_V2_IMPLEMENTATION_AND_FORMAL_VALIDATION","LANE":"BACKEND_VALIDATION",
      "CANDIDATE_COMMIT_SHA":"689ab9456461a8d19a72d059f5157092efc43aff","CANDIDATE_TREE":"6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6",
      "EXECUTOR_IDENTITY":identity,"OWNER_CONTRACT_VERSION":"OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2",
      "V2_CONTRACT_IMPLEMENTED":"YES","BOOKKEEPING_FIELD_DEPENDENCY_CHECK":"COMPLETE_WITH_TASK_LOCAL_BINDING_REQUIREMENTS",
      "STRICT_SCOPE_RETAINED":"YES","BOOKKEEPING_SCOPE":{"target":"/home/user/.hermes/skills/.usage.json","fields":["view_count","use_count","last_viewed_at","last_used_at"]},
      "OLD_STRICT_PRESERVATION_RESULT":"QUALIFICATION_OBSERVED_OLD_STRICT_REJECT_FOR_APPROVED_VARIATION; FORMAL_NOT_RUN",
      "V2_INPUT_INTEGRITY_RESULT":"QUALIFICATION_PASS; FORMAL_NOT_RUN","V2_BOOKKEEPING_EVALUATION":"QUALIFICATION_PASS; FORMAL_NOT_RUN",
      "WRITER_ATTRIBUTION":"NOT_ESTABLISHED","OBSERVATION_LIMITS":["NO_COMPLETE_WRITER_OR_SYSCALL_LEDGER","SHORT_LIVED_TEMP_CONTENT_MAY_DISAPPEAR_BEFORE_OPEN"],
      "FRESH_QUALIFICATION_RESULTS":{"tests":129,"pass":129,"fail":0,"errors":0,"skipped":0},
      "REUSED_QUALIFICATION_SCOPE":"Filtered prior full capsule: exact unchanged A/B/C components, equal execution function ASTs, and bound native logs/process/results; see qualification/REUSE_LEDGER.json",
      "FORMAL_LAUNCH_BINDING":"IMPLEMENTED_AND_QUALIFIED_PARENT_COMMANDS_READY","FORMAL_START_CREATED":"NO","REQUIRED_GATES":29,"PASS":0,"FAIL":0,"NOT_RUN":29,
      "ACTUAL_TEST_IDENTITY_ACCOUNTING":{"unique":129,"duplicates":0},"A_B_C_CORRECTIONS":"RETAINED","PRODUCT_CHANGED_PATHS":[],
      "FRONTEND_LANE_INTERFERENCE":"NONE","HISTORICAL_FAILURES_PRESERVED":"YES","PACK_HISTORICAL_BYTE_IMMUTABILITY":"NOT_RECOVERABLE",
      "PRODUCT_PUBLICATION":"NOT_PERFORMED","POST_PUBLICATION_SANITY":"NOT_RUN","EP19_CLOSED":"NO","INDEPENDENT_REVIEW":"PENDING",
      "EVIDENCE_COMMIT_SHA":None,"REVIEW_INDEX_URL":None,"REMOTE_VERIFICATION":"NOT_PERFORMED",
      "STOP":"BOUNDED_IMPLEMENTATION_AND_QUALIFICATION_COMPLETE; PARENT_FORMAL_EXECUTION_PENDING"}
    write(ROOT/"FINAL_FIELDS.json",final)

    public=ROOT/"public";public.mkdir(exist_ok=True)
    sources=[ROOT/"OWNER_AUTHORIZATION.txt",ROOT/"IMPLEMENTATION_REPORT.zh-CN.md",ROOT/"PARENT_COMMANDS.md",ROOT/"PROGRESS.md",
             ROOT/"CHANGED_SOURCE_INVENTORY.json",ROOT/"diffs/EXECUTOR_V2.patch",ROOT/"NEW_EXECUTOR_IDENTITY.json",ROOT/"FINAL_FIELDS.json",
             ROOT/"dependency/DEPENDENCY_REPORT.zh-CN.md",ROOT/"dependency/DEPENDENCY_CHECK.json",
             ROOT/"qualification/RED.native.log",ROOT/"qualification/RED.process.json",ROOT/"qualification/GREEN.native.log",
             ROOT/"qualification/GREEN.process.json",ROOT/"qualification/RESULT.json",ROOT/"qualification/QUALIFICATION.json",
             ROOT/"qualification/QUALIFICATION_MATRIX.json",ROOT/"qualification/REUSE_LEDGER.json",
             ROOT/"qualification/CURRENT_PRIVATE_SCHEMA_PROBE_SUMMARY.json"]
    copied=[]
    for source in sources:
        name=source.relative_to(ROOT).as_posix().replace("/","__")
        target=public/name;shutil.copyfile(source,target);copied.append(target)
    payload="".join(f"{dh(p)}  {p.name}\n" for p in sorted(copied))
    write(public/"PAYLOAD.sha256",payload)
    payload_sha=dh(public/"PAYLOAD.sha256")
    index={"schema":"ep19-bookkeeping-v2-public-index-v1","result":"LOCAL_PACKAGE_COMPLETE","executor_identity":identity,
           "payload_manifest_sha256":payload_sha,"private_exclusions":["per-run bookkeeping-policy-v2.private.json","raw .usage.json records/values","Skill/Memory bodies"],
           "product_gates":"NOT_RUN","publication":"NOT_PERFORMED","independent_review":"PENDING"}
    write(public/"INDEX.json",index)
    manifest="".join(f"{dh(p)}  {p.name}\n" for p in sorted([*copied,public/'PAYLOAD.sha256',public/'INDEX.json']))
    write(public/"MANIFEST.sha256",manifest)
    public_sha=dh(public/"MANIFEST.sha256")
    final["PUBLIC_MANIFEST_SHA256"]=public_sha;write(ROOT/"FINAL_FIELDS.json",final)
    write(ROOT/"MACHINE_INDEX.json",{"schema":"ep19-bookkeeping-v2-machine-index-v1","result":"LOCAL_IMPLEMENTATION_AND_QUALIFICATION_COMPLETE",
          "executor_identity":identity,"qualification":str(ROOT/'qualification/QUALIFICATION.json'),"qualification_tests":129,
          "changed_source_inventory":str(ROOT/'CHANGED_SOURCE_INVENTORY.json'),"diff":str(ROOT/'diffs/EXECUTOR_V2.patch'),
          "parent_commands":str(ROOT/'PARENT_COMMANDS.md'),"public_manifest":str(public/'MANIFEST.sha256'),"public_manifest_sha256":public_sha,
          "formal_start_created":False,"required_gates":29,"pass":0,"fail":0,"not_run":29,"publication":"NOT_PERFORMED"})
    print(json.dumps({"changed":len(rows),"public_files":len(copied)+3,"public_manifest_sha256":public_sha,"executor_identity":identity}))

if __name__=="__main__":main()
