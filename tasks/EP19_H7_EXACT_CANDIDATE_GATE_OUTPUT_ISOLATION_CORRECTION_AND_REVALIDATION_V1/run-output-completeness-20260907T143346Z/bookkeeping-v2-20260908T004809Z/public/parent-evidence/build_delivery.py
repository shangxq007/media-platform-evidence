from pathlib import Path
import json,hashlib,shutil,re,time,sys,zipfile
P=Path(__file__).resolve().parents[1]; A=P/'parent-analysis'; D=P/'delivery'; U=D/'public'; U.mkdir(parents=True,exist_ok=False)
R=P/'outputs/continuation-runs/bookkeeping-v2-formal-001'
def h(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,j):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
def cp(s,t):
 assert s.is_file() and not s.is_symlink(),s
 t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s,t)
stop=json.loads((A/'STOP_CONDITION.json').read_text()); policy=json.loads((R/'bookkeeping-policy-v2.private.json').read_text())
sys.path.insert(0,str(P/'executor'));import runner,coverage
identity=runner.verify_executor_identity()['identity'];assert identity==stop['executor_identity']
original=runner.exact(runner.O/'sources/backend');copies=runner.identities(R)
put(A/'CANDIDATE_CLOSING.json',{'result':'PASS','candidate':runner.SHA,'tree':runner.TREE,'base':runner.BASE,'original_tracked_paths':len(original),'run_repositories':copies,'task_product_source_edits':0})
raw=(A/'PARENT_QUALIFICATION.native.log').read_text();ids=[m.group(1) for m in re.finditer(r'^test_\S+ \(([^)]+)\) \.\.\.',raw,re.M)];assert len(ids)==129 and len(set(ids))==129
m=json.loads((runner.O/'GATE_EXECUTION_MATRIX.json').read_text());assert len(m['gates'])==29
account={'qualification':{'discovered':129,'executed':129,'pass':129,'skip':0,'failure':0,'error':0,'missing':0,'unexpected':0,'duplicate':0,'identities':ids},'formal':{'discovered':0,'executed':0,'pass':0,'skip':0,'failure':0,'error':0,'missing':'NOT_EVALUATED_NO_DISCOVERY','unexpected':'NOT_EVALUATED_NO_DISCOVERY','duplicate':'NOT_EVALUATED_NO_DISCOVERY'},'expectations_only':{'full_backend':7973,'full_backend_skips':29,'candidate_frontend':149}}
put(A/'ACTUAL_TEST_IDENTITY_ACCOUNTING.json',account)
put(A/'GATE_RESULTS.json',{'required':29,'pass':0,'fail':0,'not_run':29,'gates':{k:{'result':'NOT_RUN','reason':'STRICT_BASELINE_CAPTURE_INCOMPLETE_BEFORE_START'} for k in m['gates']}})
fields={'TASK':runner.O.name,'CONTINUATION':'SCOPED_RUNTIME_BOOKKEEPING_CONTRACT_V2_IMPLEMENTATION_AND_FORMAL_VALIDATION','LANE':'BACKEND_VALIDATION','CANDIDATE_COMMIT_SHA':runner.SHA,'CANDIDATE_TREE':runner.TREE,'EXECUTOR_IDENTITY':identity,'OWNER_CONTRACT_VERSION':runner.OWNER_CONTRACT_VERSION,'V2_CONTRACT_IMPLEMENTED':'YES','BOOKKEEPING_FIELD_DEPENDENCY_CHECK':'PASS_BOUNDED_FIXED_MATRIX_INPUTS_NOT_GLOBAL_NONSEMANTIC','STRICT_SCOPE_RETAINED':'YES_CAPTURE_FAILED_CLOSED','BOOKKEEPING_SCOPE':{'target':policy['target'],'fields':policy['mutable_fields'],'eligible_records':len(policy['eligible_record_ids']),'eligible_pointers':len(policy['eligible_json_pointers'])},'OLD_STRICT_PRESERVATION_RESULT':'NOT_ESTABLISHED_INCOMPLETE_FULL_CAPTURE; BOOKKEEPING_ENDPOINT_PASS','V2_INPUT_INTEGRITY_RESULT':'INCOMPLETE_CAPTURE','V2_BOOKKEEPING_EVALUATION':'PASS_POST_FAILURE_ENDPOINT_ONLY','WRITER_ATTRIBUTION':'NOT_ESTABLISHED','OBSERVATION_LIMITS':['NO_FORMAL_WINDOW','12_STRICT_TOOL_SYMLINKS_REJECTED','NO_GLOBAL_WRITER_OR_TRANSACTION_LEDGER','ENDPOINT_BOOKKEEPING_PASS_IS_NOT_FULL_PRESERVATION_PASS'],'FRESH_QUALIFICATION_RESULTS':{'executor_suite_pass':129,'parent_suite_pass':129,'parent_suite_fail':0,'parent_suite_error':0,'qualified_inputs_checked':114},'REUSED_QUALIFICATION_SCOPE':'FILTERED_COMPONENT_HASH_AST_AND_NATIVE_RECEIPT_APPLICABILITY; SEE_REUSE_LEDGER; DOES_NOT_PROVE_SELECTED_RAW_LEAN_MATERIALIZATION_READINESS','FORMAL_LAUNCH_BINDING':'INCOMPLETE_BASELINE_CAPTURE_NO_SEAL_NO_PREFLIGHT_NO_LAUNCH_RECEIPT','FORMAL_START_CREATED':False,'REQUIRED_GATES':29,'PASS':0,'FAIL':0,'NOT_RUN':29,'ACTUAL_TEST_IDENTITY_ACCOUNTING':'parent-evidence/ACTUAL_TEST_IDENTITY_ACCOUNTING.json','A_B_C_CORRECTIONS':'RETAINED_IMPLEMENTATION_AND_COMPONENT_QUALIFICATION; FORMAL_NOT_RUN','PRODUCT_CHANGED_PATHS':[],'FRONTEND_LANE_INTERFERENCE':'NONE','HISTORICAL_FAILURES_PRESERVED':'YES_CURRENT_REFERENCED_HISTORY_BYTE_CHECKS_ZERO_DIFFERENCES','PACK_HISTORICAL_BYTE_IMMUTABILITY':'NOT_RECOVERABLE','PRODUCT_PUBLICATION':'NOT_PERFORMED','POST_PUBLICATION_SANITY':'NOT_RUN_PRODUCT_NOT_PUBLISHED','EP19_CLOSED':False,'INDEPENDENT_REVIEW':'PENDING','EVIDENCE_COMMIT_SHA':'NOT_PUBLISHED_AT_PACKAGE_TIME','REVIEW_INDEX_URL':'NOT_PUBLISHED_AT_PACKAGE_TIME','PUBLIC_MANIFEST_SHA256':'DETACHED_AFTER_MANIFEST_CREATION','REMOTE_VERIFICATION':'NOT_PERFORMED_AT_PACKAGE_TIME','STOP':'YES_STRICT_BASELINE_CAPTURE_FAILURE_SCENE_PRESERVED_NO_RETRY'}
put(A/'FINAL_FIELDS.json',fields)
cp(A/'FINAL_REPORT.zh-CN.md',U/'FINAL_REPORT.zh-CN.md');put(U/'FINAL_FIELDS.json',fields)
for f in (P/'public').iterdir():
 if f.is_file():cp(f,U/'implementation-snapshot'/f.name)
for folder in ['executor','preimages/executor','dependency']:
 for f in (P/folder).rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ['.pyc']:cp(f,U/'source'/folder/f.relative_to(P/folder))
for f in (P/'qualification').iterdir():
 if f.is_file() and f.suffix in ['.py','.json','.log']:cp(f,U/'qualification'/f.name)
for attempt in (P/'qualification').glob('attempt-*'):
 for f in attempt.iterdir():
  if f.is_file() and f.suffix in ['.json','.log']:cp(f,U/'qualification'/attempt.name/f.name)
for f in A.iterdir():
 if f.is_file() and f.suffix in ['.json','.md','.log','.py']:cp(f,U/'parent-evidence'/f.name)
for name in ['RECOVERY.json','OWNER_AUTHORIZATION.txt','PARENT_REVIEW.md','CODEX_BRIEF.md','CHANGED_SOURCE_INVENTORY.json','NEW_EXECUTOR_IDENTITY.json']:
 cp(P/name,U/'authority'/name)
for name in ['prepare.json','identity.json','namespaces.json','bindings.json','source-recovery.json','scope.json']:
 cp(R/name,U/'run-evidence'/name)
private={'usage_policy_local_path':str(R/'bookkeeping-policy-v2.private.json'),'usage_policy_sha256':h(R/'bookkeeping-policy-v2.private.json'),'policy_private_content_published':False,'eligible_record_ids_sha256':hashlib.sha256(json.dumps(policy['eligible_record_ids'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'eligible_json_pointers_sha256':hashlib.sha256(json.dumps(policy['eligible_json_pointers'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),'eligible_record_count':len(policy['eligible_record_ids']),'eligible_pointer_count':len(policy['eligible_json_pointers']),'baseline_created':False,'seal_created':False,'formal_start_created':False}
put(U/'PRIVATE_EVIDENCE_BINDING.json',private)
index={'authoritative_report':'FINAL_REPORT.zh-CN.md','final_fields':'FINAL_FIELDS.json','stop':'parent-evidence/STOP_CONDITION.json','qualification':'qualification/QUALIFICATION.json','reuse':'qualification/REUSE_LEDGER.json','dependency':'source/dependency/DEPENDENCY_CHECK.json','executor_identity':identity,'private_binding':'PRIVATE_EVIDENCE_BINDING.json','source_and_preimages':'source/','phase_snapshot_warning':'implementation-snapshot is pre-formal-attempt evidence; parent final report supersedes readiness claims, especially raw Lean cache preparation','publication_note':'Post-publication commit/remote readback lives in detached final receipt; never self-hash a commit into its own payload'}
put(U/'INDEX.json',index)
(U/'INDEX.md').write_text('# 审查入口\n\n**V2 implemented / parent qualification 129 PASS / formal baseline capture BLOCKED / 29 NOT_RUN.**\n\n- [最终中文报告](FINAL_REPORT.zh-CN.md)\n- [最终工程字段](FINAL_FIELDS.json)\n- [实际停止条件](parent-evidence/STOP_CONDITION.json)\n- [实际 identities](parent-evidence/ACTUAL_TEST_IDENTITY_ACCOUNTING.json)\n- [资格 capsule](qualification/QUALIFICATION.json)\n- [机器索引](INDEX.json)\n- [私有证据摘要绑定](PRIVATE_EVIDENCE_BINDING.json)\n\nimplementation-snapshot 是早期阶段证据，不代表最终 readiness。产品未发布，EP19 未关闭。\n')
files=sorted(x for x in U.rglob('*') if x.is_file()); bad=[]
for f in files:
 data=f.read_bytes()
 if f.is_symlink() or f.name.endswith('.private.json') or re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)',data):bad.append(str(f.relative_to(U)))
assert not bad,bad
rows=[{'path':str(f.relative_to(U)),'size':f.stat().st_size,'sha256':h(f)} for f in files];put(U/'MANIFEST.json',{'schema':'ep19-evidence-manifest-v1','files':rows,'payload_count':len(rows)})
manifest=h(U/'MANIFEST.json');zip_path=D/'EP19_V2_EVIDENCE.zip'
with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for f in sorted(U.rglob('*')):
  if f.is_file():z.write(f,str(f.relative_to(U)))
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert set(z.namelist())=={str(f.relative_to(U)) for f in U.rglob('*') if f.is_file()}
 for f in U.rglob('*'):
  if f.is_file():assert z.read(str(f.relative_to(U)))==f.read_bytes()
receipt={'payload_files':len(rows),'public_files_including_manifest':len(rows)+1,'manifest_sha256':manifest,'zip_sha256':h(zip_path),'zip_members':len(rows)+1,'private_policy_files_published':0,'credential_format_scan_matches':0,'result':'PASS_LOCAL_BYTES_MANIFEST_ZIP','executor_identity':identity}
put(D/'LOCAL_PACKAGE_VERIFICATION.json',receipt);print(json.dumps(receipt))
