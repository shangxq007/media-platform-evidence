# 治理后新 baseline 尝试：停止与交付报告

## 结论
**BLOCKED_BASELINE_CREATION；不是独立接受。** 已进行真实新运行准备，并唯一一次调用原一次性执行器；baseline 创建在 `BOOKKEEPING_BASELINE_CAPTURE_UNBOUND` 停止。未产生完整 baseline、seal、preflight、START 或 executor RESULTS，29 门均 NOT_RUN（0 PASS / 0 FAIL / 29 NOT_RUN）。这是 baseline 阶段退出 1，不是将某个未调用产品 gate 标为 FAIL。未重试、刷新 baseline、改 predicate 或自动关闭 EP19。

## Owner 说明与历史保全
原话：**“记忆漂移是因为我对hermes记忆与skills做了治理。”**
`OWNER_CLARIFICATION.json` 保存当前完整授权第 1 节来源和追加记录 UTC 时间。该说明是 Owner 提供的运维上下文，不是历史 PID/syscall 证据。历史运行保持 **0 PASS / 1 FAIL / 28 NOT_RUN**；CHANGE_IMPACT 在 GATE_BOUNDARY、产品 native 命令前失败，native_exit=null、wrapper_exit=1。历史 NOT_ESTABLISHED 未改写。

新 namespace 从治理后状态出发，不要求 intentional Skills/Memory 差异等于旧 baseline，也不放宽 Memory-root ctime。新 baseline 本次没有成功形成，不能声称治理后的输入已通过正式封存或后续持续保持。历史选定 1,909 个控制文件的 hash/所记录 metadata 端点相等；这不证明未知历史 pack 区间的字节不变。

## 已真实执行与复用
- 读取指定精简上下文、候选 AGENTS/CLAUDE 和验证记录。原字节复制最新 Lean continuation executor；只修改新 tools wrapper 的 run ID。
- 新运行 `post-governance-formal-001`：三份 detached checkout，每份 7,634 个 tracked 文件核对固定候选；无 Git alternates、共享 Git-object inode；sources、Git 管理路径、cache/tmp/build/gate-output 按旧设计独立绑定。
- 治理范围递归捕获 COMPLETE：metadata-only 91、content-changed 7、added 1、removed 0，capture errors 0。详情及路径只保留本地私有对账。观测是顺序端点，不是原子事务或连续观测。
- 另单列旧 runtime-source 审计摘要的 4 项变化，不归因 Owner：它们不在固定 standalone executor imports、旧 baseline 或 qualification 的实际闭包。固定验证实现/封存的依赖闭包核对未见差异；这不是批准其他 Hermes runtime 漂移。
- 新 run-local materialized Lean 严格 collector/revalidation 各覆盖 4,627 个输入，unsupported symlink=0，native probes 已执行并成功。未重引入 symlink-preserving distribution。
- 历史 Lean 19 与 V2 129 控制仅复用，新的 helper 绝对路径重绑定及 identity 重算；本次 fresh control tests=0。qualification 原字段 fresh_tests=19 是旧胶囊来源，不是本次新跑。
- COMPILE freshness、frontend asset closure、静态资源→Gradle→JAR mapping、H7 33-rule semantics、immutable artifacts 和同值决策绑定实现原样保留，但本次没有任何 gate outcome 可证明这些检查运行成功。

## 精确失败边界与执行偏差
`executor/runner.py:95–114`：先生成 policy/scope，再 `observe.snapshot`，随后在第 107 行调用 `capture_binding(policy,before)`；只有后续成功才写 baseline。
`executor/bookkeeping_v2.py:431–438`：比较捕获 target 行的 `sha256` 与 policy `baseline_raw_sha256`，以及 `metadata` 与 `baseline_usage_metadata`，任一不等即抛出本次错误。
现有异常分支未保存 `before` map，故不能分别判定是哪一分量不等、具体时间或 writer。保留部分 policy/scope 与原生 traceback，不用新现场采样冒充失败时端点。V2 完整判定及 strict preservation 均 NOT_ESTABLISHED。

**执行方偏差：** 我在 one-shot launcher 启动后才调用 `skill_view(name=github-pr-workflow)`，未完全遵守先完成指令加载再建立 baseline 的顺序。该调用可能更新 bookkeeping，不能排除其参与本次失败；没有完整端点或 syscall 记录，不把可能性写成唯一技术归因。之后的上下文压缩要求重载发生在进程退出后，亦不用于补造历史值。未调用 memory/skill_manage 写正文或执行治理；不据此宣称 runtime metadata 无变化。

## 测试与后续边界
原图 29 门未启动；没有新 test discovery/XML，actual missing/unexpected/duplicate 均 NOT_ESTABLISHED，不能把 7,973 历史 identities 和 29 expected skips 视为本次 outcome。候选前端 reference 仅适用本 backend candidate，不引用发展中的 frontend 分支测试。
下一步是独立审阅本次启动顺序偏差与失败捕获限制；任何重试须另行授权。无需再询问 Owner 是否进行了治理。产品 source 改动=0，frontend development lane 改动=0，产品发布未执行。

## 交付及公开边界
本 payload 是执行方证据，不是独立 ACCEPT。历史证据已发布的固定提交和新核对见 `PRIOR_DELIVERY_LINKS.json`；不覆盖旧 payload。新发布只新增 task namespace。
本地私有 `POST_GOVERNANCE_RECONCILIATION.private.json`、`POST_GOVERNANCE_CAPTURE.private.json`、部分 scope/policy 与完整 qualification inventory 不发布；无 Memory/Skill 正文、凭据或无关 workspace 清单。公开哈希不能代替对私有原件的获授权本地审阅。
`INDEX.json`、`MANIFEST.sha256` 和源码/原生日志支持审阅重构。包内 publication 字段仅说明 payload freeze 时状态，固定提交、manifest 摘要、匿名 Git/Raw 结果写入包外本地 FINAL_FIELDS/REMOTE_VERIFICATION，避免自引用或递归发布。

## 必需最终字段（发布前冻结值）
```json
{
  "TASK": "EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1",
  "CONTINUATION": "OWNER_GOVERNANCE_ACKNOWLEDGEMENT_AND_FRESH_BASELINE_FORMAL_REVALIDATION",
  "LANE": "BACKEND_VALIDATION",
  "OWNER_GOVERNANCE_ACKNOWLEDGEMENT_RECORDED": "YES",
  "ATTRIBUTION_SOURCE": "OWNER_STATEMENT",
  "TECHNICAL_WRITER_PID_SYSCALL_ATTRIBUTION": "NOT_ESTABLISHED",
  "CANDIDATE_BASE_SHA": "86d6aef94fd5e58da552e97c11473cff6eca734e",
  "CANDIDATE_COMMIT_SHA": "689ab9456461a8d19a72d059f5157092efc43aff",
  "CANDIDATE_TREE": "6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6",
  "EXECUTOR_IDENTITY": "a12852f845ce4df6a657f4d93086a7401b382a5f2851bb38e840d5e45ea698ee",
  "POLICY_IDENTITY": {
    "contract": "OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2",
    "run_specific_policy_sha256": "fbaba109a6b5bcbde235de109674f6ad3ba32e7af6db1f350af053dee3ec2c1e",
    "status": "CREATED_BUT_NOT_SEALED_BASELINE_FAILED"
  },
  "HISTORICAL_FAILED_RUN_PRESERVED": "YES_1909_SELECTED_CONTROLS_HASH_AND_METADATA_EQUAL_PLUS_OLD_CHECKOUT_TRACKED_IDENTITIES",
  "HISTORICAL_FAILURE_RECLASSIFIED": "NO",
  "POST_GOVERNANCE_INPUT_RECONCILIATION": {
    "result": "COMPLETE",
    "hashed_files": 2015,
    "counts": {
      "METADATA_ONLY": 91,
      "CONTENT_CHANGED": 7,
      "ADDED": 1
    },
    "capture_start_ns": 1788848256732579361,
    "capture_end_ns": 1788848257129159674,
    "capture_errors": 0,
    "private_details": "LOCAL_ONLY",
    "outside_governance_endpoint_differences": 0,
    "runtime_audit_source_hash_differences": 4,
    "runtime_difference_disposition": "Separate source-level dependency applicability record; not attributed to Owner; not in executor imports or old baseline/qualification closure"
  },
  "NEW_RUN_ID": "post-governance-formal-001",
  "NEW_BASELINE_IDENTITY": "NOT_ESTABLISHED_BASELINE_CREATION_FAILED",
  "BASELINE_PURPOSE": "NEW_POST_GOVERNANCE_RUN",
  "OLD_BASELINE_MODIFIED": "NO",
  "PRESERVATION_CONTRACT_RELAXED": "NO",
  "LEAN_PREPARATION_RESULT": {
    "result": "PASS",
    "strict_collector": "COMPLETE",
    "captured_files": 4627,
    "disallowed_symlink_count": 0,
    "native_probe_result": "PASS",
    "revalidation_result": "PASS"
  },
  "FRESH_QUALIFICATION_RESULTS": {
    "fresh_control_tests": 0,
    "fresh_run_local_native_probes": 3,
    "fresh_preparation_collector_result": "COMPLETE",
    "fresh_revalidation_collector_result": "COMPLETE"
  },
  "REUSED_QUALIFICATION_SCOPE": "Historical Lean 19 and V2 129 controls; byte-identical helpers, verified dependency closure and new absolute-path binding. Historical schema fresh_tests=19 is provenance, not this run fresh test count.",
  "CHECKOUT_AND_OUTPUT_ISOLATION": "PASS_THREE_DETACHED_EXACT_CHECKOUTS_NO_ALTERNATES_NO_SHARED_GIT_OBJECT_INODES_RUN_LOCAL_OUTPUTS",
  "PREFLIGHT_RESULT": "NOT_RUN_BASELINE_CREATION_FAILED",
  "START_RECORD_STATUS": "ABSENT",
  "REQUIRED_GATES": 29,
  "PASSED_GATES": 0,
  "FAILED_GATES": 0,
  "NOT_RUN_GATES": 29,
  "ACTUAL_TEST_IDENTITY_ACCOUNTING": {
    "discovered": 0,
    "executed": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "missing": "NOT_ESTABLISHED_NO_TEST_DISCOVERY",
    "unexpected": "NOT_ESTABLISHED_NO_TEST_DISCOVERY",
    "duplicates": "NOT_ESTABLISHED_NO_TEST_DISCOVERY",
    "backend_reference": 7973,
    "backend_expected_skips": 29,
    "candidate_frontend_reference": 149,
    "gate_graph_started": false
  },
  "NATIVE_AND_WRAPPER_EXIT_ACCOUNTING": {
    "baseline_process_exit": 1,
    "one_shot_process_exit": 1,
    "gate_native_exits": "NOT_RUN",
    "gate_wrapper_exits": "NOT_RUN",
    "raw_result_file": "NOT_CREATED_BY_EXECUTOR",
    "failure": "BOOKKEEPING_BASELINE_CAPTURE_UNBOUND"
  },
  "OLD_STRICT_PRESERVATION_RESULT": "NOT_ESTABLISHED_NEW_BASELINE_NOT_COMPLETED",
  "V2_INPUT_INTEGRITY_RESULT": "NOT_ESTABLISHED_BASELINE_BINDING_REJECTED",
  "OBSERVATION_SCOPE_AND_LIMITS": [
    "Sequential defined-scope endpoints, not atomic or continuous",
    "New baseline before-map not persisted on this exception; cannot determine whether hash or metadata component triggered",
    "Late publication skill loading after launcher start is executor sequence deviation; possible bookkeeping contributor, not independently attributed cause",
    "Private inventories/policy/bodies omitted from public package; authorized local review needed",
    "Owner explanation applies to historical Memory drift, not automatically to this new baseline failure"
  ],
  "PRODUCT_SOURCE_CHANGES": 0,
  "FRONTEND_DEVELOPMENT_LANE_CHANGES": 0,
  "PACK_HISTORICAL_BYTE_IMMUTABILITY": "NOT_RECOVERABLE",
  "PRODUCT_PUBLICATION": "NOT_PERFORMED",
  "POST_PUBLICATION_SANITY": "NOT_RUN",
  "EP19_CLOSED": "NO_PENDING_INDEPENDENT_REVIEW",
  "EVIDENCE_COMMIT_SHA": "NOT_PERFORMED_AT_PAYLOAD_FREEZE",
  "REVIEW_INDEX_URL": "Recorded in local post-publication FINAL_FIELDS.json",
  "MACHINE_INDEX_URL": "Recorded in local post-publication FINAL_FIELDS.json",
  "PUBLIC_MANIFEST_SHA256": "Recorded in local detached receipt; excluded from payload to avoid digest cycle",
  "REMOTE_VERIFICATION": "NOT_PERFORMED_AT_PAYLOAD_FREEZE",
  "INDEPENDENT_REVIEW": "REQUIRED",
  "STOP": "YES"
}
```
