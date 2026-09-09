# r6 异常组合、owned resource 与候选绑定闭合报告

## 结论

本轮只新增/写入 `implementation-r6/`、`fixtures-r6/`、`writer-evidence-r6/`、`private-r6/`；r5 与全部历史原样保留。r5 part-a 的四个实际残余路径已闭合，AR007/AR009 保持解决，29-gate matrix 与 H733/COMPILE/BOOTJAR/隔离/frontend assets/static→resources→JAR/Lean/wrappers 均未改变。批准契约未改变。

精确最终 RED `red-predecessor-004` 使用 r5 executor：9 identities，8 FAIL、1 ERROR、native exit 1。最终 GREEN `green-focused-006` 使用相同测试体 SHA-256 `52b8f8a633d5529c8770c03ffaa083b5cd704051db4f43c6a27207a933427591`：9/9 PASS、native exit 0。二者均由 parent wrapper 记录 argv/cwd/PID/wall+monotonic timing/native log/result/source before+after/dependency hash；完整支持文件 manifest 只作上下文，实际导入分类见 `FOCUSED_SOURCE_CLASSIFICATION.r6.final.json`，历史缺失绑定不回填。

最终集成资格 `qualification-005`：161 expected / 161 executed / 161 unique / 161 PASS；FAIL/ERROR/SKIP/MISSING/UNEXPECTED/DUPLICATE/invalid 均 0，mandatory 76。其自写 PROCESS 只作为内部结果回执，不冒充独立 OS launch；另有 parent PID 9、native exit 0、wrapper exit 0、21.353878s 与 prelaunch/post-exit 113-file source hash 精确回执。

## AR008 / AR010 闭合

- BoundaryObserver 构造 primary 与 fd close secondary 形成稳定 causal graph；ancestor/collector/inventory/capture 所有已拥有 fd 均独立 close。
- durable stream 明确拥有 raw fd 与 stream；fdopen 失败也释放 raw fd；body/native、flush、file fsync、stream close、raw fd close、parent fsync 独立尝试和聚合。仅 primary 且 cleanup 正常时保持原异常类型兼容。
- Vite helper/native 主失败与后续 fsync/close 维度同时进入 `causal_errors`/`failure_dimensions`。
- native exception 无论 main child 是否已退出，都用 ChildScope 排除既有 children 后保存的 PID/birth identity 收尾；真实 fixture 证明 parent exit、setsid descendant 存活、observer exception 后 descendant 被终止/回收。无 pgrep、无全机扫描、无猜测重用 PID。permission/unknown/PID reuse/timeout 分开记录。
- attached runner receipt + final receipt write failure + marker write failure全部进入最终 gate result；marker 不可写时输出不含路径和异常文本的 sanitized native uncertainty record，绝不继续成功 FINAL/COVERAGE/SEAL。

## 固定身份与状态

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（本轮仅 r6 correction/qualification/binding）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- EXECUTOR_IDENTITY：runtime binding SHA-256 `000519c86183cccb2c326d27f023435fa58745f7a7076eef873be83a74538283`；loader PASS，113 source files
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR006_DISPOSITION：RETAINED_RESOLVED
- AR007_DISPOSITION：RETAINED_RESOLVED
- AR008_DISPOSITION：CLOSED
- AR009_DISPOSITION：RETAINED_RESOLVED
- AR010_DISPOSITION：CLOSED
- AFFECTED_QUALIFICATION_RESULTS：focused 9/9；integrated 161/161
- QUALIFICATION_IDENTITY_ACCOUNTING：PASS，mandatory 76，所有非 PASS/集合差异为 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；dependency `90d26dad27d327869b220da4c98d34e5c5334e9aada7c00dc7ecc879dba50295`，private 内容不公开
- CONTINUOUS_PROTECTION_COVERAGE：既有 AR001 范围保持
- CAPTURE_COHERENCE_AND_LIMITS：既有时限/容量/共享 boundary retry 保持；批准的 ledger 捕获间限制保持，不扩大
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS_BY_SOURCE_BOUND_PRIVATE_FIXTURES
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（binding only，namespace 未创建）
- BASELINE_RESULT / PREFLIGHT_RESULT / START_CREATED：NOT_RUN / NOT_RUN / NO
- REQUIRED_GATES / PASSED_GATES / FAILED_GATES / NOT_RUN_GATES：29 / 0 / 0 / 29
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 EXPECTED
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED
- EP19_CLOSURE_CRITERIA_ACCOUNTING：PENDING parent formal 与独立接受
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 按 binding 条件执行唯一 candidate-formal-002，随后独立评审
- PRODUCT_PUBLICATION / POST_PUBLICATION_SANITY：NOT_PERFORMED / NOT_RUN
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / PUBLIC_MANIFEST_SHA256 / REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED
- STOP_REASON：R6_QUALIFIED_IMPLEMENTATION_AND_BINDING_COMPLETE_PARENT_OWNS_CONDITIONAL_FORMAL

未改产品源码、产品测试、依赖、共享 Skill/Memory/ledger/usage/frontend；未运行产品测试、共享 probes/preparation/baseline/formal；未创建 formal namespace、未消费第二次正式尝试、未自签独立接受、未发布。
