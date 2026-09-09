# r9 实际 preflight 持久化复合失败修正与候选绑定报告

## 结论

本轮在新 `implementation-r9/`、`fixtures-r9/`、`writer-evidence-r9/`、`private-r9/` 内完成 B7-008-3 / B8-B-1 的精确修正。r8 及此前历史经既有 source/manifest 核对保持不变。没有产品、产品测试、依赖、共享 Skill/Memory/bookkeeping、frontend、shared probe、preparation、baseline 或 formal 操作；没有创建 `candidate-formal-002` namespace，正式预算仍为 1/2。

实际 r8 RED 使用 `durability.exclusive_bytes` 在真实 `preflight.json` fd 写入点注入故障：原失败单独路径通过，复合 preflight 写失败与 final sink 失败各自失败。相同测试体 SHA-256 `e95b6b5048c781dd8894f59712db150f12272b3b7472aeb0e34fe3ce1dc22941` 对最终 r9 3/3 PASS。成功 final sink 走真实独占写、fsync、close 后读取 JSON 并核对原 native/cleanup occurrence、`IRREVERSIBLY_LATCHED_REJECT` 和 preflight 写 secondary；final sink 自身失败时不声称存在持久回执，实际 structured fallback 保留三层原因。

集成资格为 173/173 PASS、173 unique、0 duplicate/missing/unexpected/fail/error/skip；r8 的 85 个 mandatory 全部保留，并增加 3 个 r9 mandatory，最终 88。最终 runtime binding `3c06598cce6771acfb7451ac235bd5ac265fa76eec843726cb674f2861b9a4b2` 固定 `candidate-formal-002`、118 个 tooling source、qualification `10086042d1849b6060f6deb8cfa37a7683b8f35f095b19241dc26aa19f4cfaae` 和 dependency `fed1d09880cadb9b909bec60a006f1c8d93bd4394693ac06fe03e2882ce417e9`；只读 loader PASS，快照口径为 118 tooling + validator + binding = 120。PID 是 writer-owned subprocess namespace PID，不是独立 OS 证明。

## 关键字段

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（本轮限定 r9 writer correction）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- EXECUTOR_IDENTITY：runtime binding SHA-256 `3c06598cce6771acfb7451ac235bd5ac265fa76eec843726cb674f2861b9a4b2`
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR007 / AR009 / AR010_DISPOSITION：RETAINED_RESOLVED；未重开已接受观察限制或扩大契约
- AR008_DISPOSITION：CLOSED_EXACT_FINITE_PERSISTENCE_SCOPE；B7-008-1/2 retained，B7-008-3/B8-B-1 corrected
- AFFECTED_QUALIFICATION_RESULTS：focused 3/3 PASS；integrated 173/173 PASS
- QUALIFICATION_IDENTITY_ACCOUNTING：expected/executed/passed 173/173/173；mandatory 85+3=88；其余全 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；finite reachable local graph 39 nodes，actual helper edges 含 preflight/final persistence；private r9 bytes 与 r8 来源一致且目录 0700
- CONTINUOUS_PROTECTION_COVERAGE：RETAINED_RESOLVED，未冒称本轮 formal coverage
- CAPTURE_COHERENCE_AND_LIMITS：RETAINED_RESOLVED；64MiB/128/1MiB/8MiB/4096/128/3次5秒/4096 与无 3600 秒上限保持
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS_EXACT_SCOPE；失败不可达成功 FINAL/COVERAGE/SEAL
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（binding only；namespace 未创建）
- BASELINE_RESULT / PREFLIGHT_RESULT / START_CREATED：NOT_RUN / NOT_RUN / NO
- REQUIRED_GATES / PASSED_GATES / FAILED_GATES / NOT_RUN_GATES：29 / 0 / 0 / 29
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 EXPECTED
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED
- EP19_CLOSURE_CRITERIA_ACCOUNTING：PENDING parent formal、正式结果独立评审及既有关闭条件
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 对 r9 包独立评审后，按唯一 handoff 决定并执行 `candidate-formal-002`；随后独立接受与关闭对账
- PRODUCT_PUBLICATION / POST_PUBLICATION_SANITY：NOT_PERFORMED / NOT_RUN
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED
- PUBLIC_MANIFEST_SHA256：见 `FINAL_MANIFEST.r9.sha256` 文件本身 SHA-256（在生成后由 parent 核对）
- STOP_REASON：R9_QUALIFICATION_AND_FIXED_BINDING_COMPLETE_NO_FORMAL_AUTHORIZED_IN_THIS_PACKET

## 变更与证据边界

`engineering_preflight` 现在在任何可失败 receipt 写入前构造带完整 `preflight_receipt` 的原 reject；真实写失败通过 occurrence/context composition 作为 secondary。`formal_failure_document` 带出 disposition 和 `preflight_receipt_persisted`；相邻 `FORMAL_FAILURE.json` 写失败由正式 catch 使用的 `formal_persistence_failure` 返回完整 structured native fallback。未承诺任意深度图；沿用既有最多 32 contexts，有限实际链不丢 occurrence。

r8→r9 byte-derived delta 为 10 个 added/changed 文件，patch SHA-256 `b1629521879afd4efe621a805ed841a43d709a707011e447821b709899ca053f`。r8 writer manifest 1879 项、Part A manifest 6 项、Part B manifest 5 项均逐文件匹配。`red-r8-001` 的测试断言错误迭代原样保留，不作为 authoritative RED；`red-r8-002` 为精确 RED。

本报告不是独立接受、产品门禁结果或正式启动许可；没有 push/publish。可执行但未运行的 parent 命令位于 `PARENT_HANDOFF_COMMANDS.r9.md`。
