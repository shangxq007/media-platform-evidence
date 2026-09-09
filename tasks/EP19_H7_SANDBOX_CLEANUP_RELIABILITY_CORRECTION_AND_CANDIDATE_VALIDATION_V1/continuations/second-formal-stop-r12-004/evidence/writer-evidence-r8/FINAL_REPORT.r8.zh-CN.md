# r8 三项实际 AR008 因果传输缺陷修正与资格报告

## 结论

B7-008-1/2/3 已在 r8 外部执行器工程范围闭合，等待独立符合性接受。真实同体 RED 为 3/3 非 PASS，最终 GREEN 为 3/3 PASS；最终集成资格为 170 expected / 170 executed / 170 unique / 170 PASS，mandatory 85，FAIL/ERROR/SKIP/MISSING/UNEXPECTED/DUPLICATE 均为 0。只读 runtime loader PASS，绑定 exact `candidate-formal-002`、固定产品 SHA/tree/patch 和 118 个当前实现文件。AR010、AR001..007/009 与全部历史结果保持原处；历史缺失 provenance 仍为 `NOT_ESTABLISHED_NO_BACKFILL`。

## 固定字段

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（r8 causal transport correction）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- EXECUTOR_IDENTITY：runtime binding SHA-256 `5728eafccf0f13665c963cdaf9c3773a7fe76450f5251c2047b33514881d4b20`；loader PASS；117 bound tooling files
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR007_DISPOSITION：RETAINED_RESOLVED
- AR008_DISPOSITION：B7-008-1/2/3 CLOSED_ENGINEERING_PENDING_INDEPENDENT_ACCEPTANCE
- AR009_DISPOSITION：RETAINED_RESOLVED
- AR010_DISPOSITION：RETAINED_RESOLVED；r7 Part A 的 resolved 范围未重开
- AFFECTED_QUALIFICATION_RESULTS：authoritative RED 0/3；final GREEN 3/3；integrated 170/170
- QUALIFICATION_IDENTITY_ACCOUNTING：PASS；mandatory 85；全部集合差异与非 PASS 为 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；dependency SHA-256 `c9dd93afafa57e4c3f42a0530d64a55e272b8a17480f49b2fd7e24bff56bc048`；private bytes 未公开
- CONTINUOUS_PROTECTION_COVERAGE：既有 AR001 范围保持；没有新增 cutoff 后义务
- CAPTURE_COHERENCE_AND_LIMITS：既有边界时限、容量、共享 retry 与已接受 ledger 观察限制保持
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS；原 decision 先附着，marker fault 为关联 secondary；失败后 FINAL/COVERAGE/SEAL success 不可达
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（binding only；namespace 未创建）
- BASELINE_RESULT / PREFLIGHT_RESULT / START_CREATED：NOT_RUN / NOT_RUN / NO
- REQUIRED_GATES / PASSED_GATES / FAILED_GATES / NOT_RUN_GATES：29 / 0 / 0 / 29
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 EXPECTED
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED
- EP19_CLOSURE_CRITERIA_ACCOUNTING：PENDING parent formal 与独立接受
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 评审本 binding 后执行唯一 candidate-formal-002；随后独立评审
- PRODUCT_PUBLICATION / POST_PUBLICATION_SANITY：NOT_PERFORMED / NOT_RUN
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED
- PUBLIC_MANIFEST_SHA256：LOCAL_MANIFEST；文件 hash 在最终交接中报告
- STOP_REASON：R8_QUALIFIED_BINDING_COMPLETE_PARENT_OWNS_REAL_EXECUTION

## 三项修正

1. B7-008-1：`RunAdapter.boundary` 在任何可失败 marker 持久化前构造并附着原 boundary decision；marker 异常与原 REJECT 组合，并在 driver 最终失败结果中保存完整 decision、causal rows 和 persistence uncertainty。真实 Engine 仅进入一次 COMMAND boundary，gate 未 dispatch，后续 `final()` 被不可逆 latch 拒绝。
2. B7-008-2：`ep19-structured-causal-error-v2` 为每个实际异常 occurrence 分配稳定 ID，仅按 occurrence ID 合并重复 transport；每个 occurrence 保存最多 32 层 inner→outer context 与 parent edge。实际 `exclusive_bytes` 的 outer write primary、inner directory-fsync primary、file/directory 两个同文 close failure 全部保留，主次和资源 stage 可区分。
3. B7-008-3：`engineering_preflight` 保存 causal rows 和 `IRREVERSIBLY_LATCHED_REJECT` disposition，抛出携带 `preflight_receipt` 的 structured exception；`formal` 实际 catch path 调用同一个 `formal_failure_document`。私有 fixture 只注入 bounded capture producer，不运行 preparation/probe/baseline/formal，也未创建正式 namespace。

## 资格、失败迭代与来源

- `red-transport-001` 保留最初 fixture setup 迭代；不冒充 authoritative RED。
- `red-predecessor-002` 以 r7 predecessor snapshot 和最终相同测试体执行：3 个 control 全部非 PASS。
- `green-final-001`：同一测试体 SHA-256 `e447308b4ed7498102e1731e8235b3001666bbc342275b62d9915e0b95a321a9`，3/3 PASS；执行前后 test/executor/wrapper/dependency bytes 稳定。
- `qualification-001` 保留 167 PASS + 3 ERROR 的 finite dependency edge validator 失败；修正直接 validator 后，`qualification-002` 和最终 `qualification-003` 均 170/170 PASS。
- 最终集成 parent duration 21.464693081 秒，native/wrapper exits 0/0；inner native log SHA-256 `10d59de531aaea9e2b9c6b7c023db77deace1dfe8853875461165e5d69be6f6b`。
- `runtime-loader-001` 保留 r7 evidence-path guard 失败；修正 r8 path guard 后 `runtime-loader-002` PASS，duration 1.076788438 秒，native/wrapper exits 0/0。
- r7→r8 byte-derived patch SHA-256 `893f247589cadc932e4bdb18226347fd6e4dbd51d46407ce34cb7555d55ded56`；完整 64 位 source hashes 在 `SOURCE_HASHES.r8.final.json`。

## 不变边界

未修改或运行产品源码、产品测试、依赖、frontend、共享 Skill/Memory/ledger/usage；未执行 shared probes、preparation、baseline 或 formal；未创建/消费 `candidate-formal-002` namespace。原 29 commands/timeouts/matrix、H733、COMPILE freshness/completeness、isolated outputs、exclusive BOOTJAR、frontend/assets/static→resources→JAR、Lean、wrapper/init 与 finite dependency graph 均由当前 source binding 和 170-control qualification 保持，不将其冒称 fresh 产品 gate 结果。未自签独立接受，未 push/publish。
