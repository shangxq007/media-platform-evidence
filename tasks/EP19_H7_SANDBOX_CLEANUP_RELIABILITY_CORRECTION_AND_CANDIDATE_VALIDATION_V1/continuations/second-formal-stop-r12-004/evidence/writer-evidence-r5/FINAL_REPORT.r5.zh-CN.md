# r5 失败转换闭合、实际资格与最终运行绑定报告

## 结论

本轮只在 `implementation-r5/`、`fixtures-r5/`、`writer-evidence-r5/`、`private-r5/` 写入。r4 及此前历史完整保留。残余 formal cleanup、异常因果分类/保留、成功 seal 后失败补充封存已经闭合；AR001—AR007 的既有解决行为和有限契约未回退。

源绑定 RED 为 `red-predecessor-003`：13 个独立控制中 10 FAIL、2 ERROR、1 PASS（产品断言保持分离的既有控制）；GREEN 为 `green-focused-005`：13/13 PASS。集成资格 `qualification-003` 为 **152/152 PASS**，unique 152，mandatory 67；FAIL/ERROR/SKIP/missing/unexpected/duplicate/invalid 均为 0。native log、RESULT、PROCESS、源码 before/after/current 均精确对账。

## 固定身份与完整 hash

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（本 writer 仅执行 r5 correction/qualification/binding）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- matrix SHA-256：57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e
- dependency SHA-256：6b5ce0887bc522c4353b7bb85a292cdf6096f1fafa752821a4006b28f15e47d6
- qualification SHA-256：cd09689d3a9d21093a8b286baa89d82f53cf617ac795523cad66367aeee8ec54
- runtime binding SHA-256：004aa36b9c2d7c1b92071d3b7ff02656af1cba34c4e8d67b47d3f38adafbd432
- implementation patch SHA-256：0da4ce2a7042cdab3e97e34db08f52be622e87446ac7518de13474f94c201d6b

## 关闭内容

- formal cleanup：`continuous.close` 与 `observer.close` 独立尝试；原始失败、两个 cleanup 失败及 cleanup receipt 持久化失败均聚合。Watch 构造失败的 fd cleanup 也不再覆盖原始 add/watch 原因。
- AR008：native exceptional receipt 保存已启动 child、exit、termination、observer 与 cleanup 事实；runner 在 parser、fsync/evidence、environment、辅助 process 和 product assertion 的真实边界独立分类；driver 保留 gate 主原因，并把 marker/receipt 持久化故障作为 secondary。
- AR009：若 `sealed/` 已存在，保持其不可变；`failure-supplement/` 以 O_EXCL 新建，绑定原 seal manifest digest、run、gate、candidate/tree 和 failure-details digest。补充写失败保持原错误并单独报告，绝不转成功。
- AR007 保留：local graph 38/112，parser packages 8/216；固定 parser source root 未删除、未扩展为任意未来 plugin 契约。

## 实际状态字段

- EXECUTOR_IDENTITY：由最终 runtime binding 的 111 个 source entries 及 inputs 绑定；loader PASS
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR007_DISPOSITION：RETAINED_RESOLVED
- AR008..AR010_DISPOSITION：CLOSED
- AFFECTED_QUALIFICATION_RESULTS：13/13 focused GREEN；152/152 integrated PASS
- QUALIFICATION_IDENTITY_ACCOUNTING：expected/executed/passed 152/152/152；其他状态全 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；private 内容不公开
- CONTINUOUS_PROTECTION_COVERAGE：既有 r4 解决行为保持
- CAPTURE_COHERENCE_AND_LIMITS：既有批准限制保持；捕获间 overwrite-restore/truncate-regrow 历史限制仍保留
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS_BY_SOURCE_BOUND_FIXTURE_QUALIFICATION
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（仅 binding，namespace 未创建）
- BASELINE_RESULT/PREFLIGHT_RESULT/START_CREATED：NOT_RUN/NOT_RUN/NO
- REQUIRED_GATES/PASSED_GATES/FAILED_GATES/NOT_RUN_GATES：29/0/0/29（第二次未执行）
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 expected
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED
- EP19_CLOSURE_CRITERIA_ACCOUNTING：PENDING formal 与独立接受
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 条件执行 candidate-formal-002；之后独立评审
- PRODUCT_PUBLICATION：NOT_PERFORMED
- POST_PUBLICATION_SANITY：NOT_RUN
- EVIDENCE_COMMIT_SHA/REVIEW_INDEX_URL/MACHINE_INDEX_URL/PUBLIC_MANIFEST_SHA256/REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED
- STOP_REASON：R5_WRITER_SCOPE_COMPLETE_PARENT_OWNS_CONDITIONAL_FORMAL

旧无 tested-source 绑定的历史结果继续为 NOT_ESTABLISHED，未回填。没有产品源码/测试/依赖变化，没有产品测试、共享 probe/preparation/baseline/formal，未创建 formal namespace，未消费第二次尝试，未自签独立接受或发布。
