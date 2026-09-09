# r11 gate diagnostic stderr 原因保留修正报告

## 结论

B10-A-1 已在精确实际路径闭合。r10 的 `execute_actual_graph` 在 `results[name]` 赋值前调用 `emit_persistence_uncertainty`；stderr 的 write/flush 异常会替换原 acquisition/gate 异常及 marker secondary。r11 先把结构化 result 写入 results 并附到 primary，再进行 best-effort stderr；若该诊断失败，则以 secondary occurrence 组合，交给可用的外层 `FORMAL_FAILURE.json`。stderr 仍非耐久 sink，失败不算交付或成功。

同一测试体 `08611fdad2b4ab8724642d3a5a298e8ee0307c71e0c9689f0c2c134034152c78` 的 predecessor RED 为 2/2 intended FAIL，最终 actual-path GREEN 为 2/2 PASS。acquisition 与 native gate 是独立测试；后者实际启动私有 Python child 并保存 native exit 73。两条都经过生产 `formal()`、实际 `execute_actual_graph()`、实际 adapter latch/marker 持久化失败及真实 print write/flush，不是只按异常名称模拟，也未 mock 掉 emission。保存的最终 receipt 已在临时目录清理前复制并重新 JSON readback。

完整集成资格为 178/178 PASS、178 unique、93 mandatory；duplicate/missing/unexpected/fail/error/skip/invalid-status 全为 0。runtime loader PASS，固定 120 个 tooling source、qualification `1ed9a6647cd6bbff66016f31778ccf1bf484f960f1c4d1e0a95181c97ee0cf6f`、dependency `ba857659f35f97842057589e561de90bb992fad86c3312ba74a21c03d1adb389` 与唯一 `candidate-formal-002`。PID 只是 writer-owned subprocess namespace 观察，不是独立 Hermes attestation。

B9-B-1/B9-B-2 保持 r10 两份完整审查支持的精确闭合范围。AR001..007/009/010、native29、H733、原生 timeout、有限依赖图、捕获限额和 Owner 已接受的 ledger 观察限制全部保留；AR005/006 未回归。未改变产品、测试预期、依赖、批准 A/B/C 契约或 gate matrix。

## Owner 最终字段

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（r11 external correction）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- EXECUTOR_IDENTITY：runtime binding SHA-256 `3246789277a6154e7a04d54a5b71ebf1bd44b66b7a03f329af091b467986e9cb`
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR007 / AR009 / AR010_DISPOSITION：RETAINED_RESOLVED
- AR008_DISPOSITION：B10_A_1_CLOSED_EXACT_ACTUAL_ACQUISITION_AND_GATE_SCOPE；r10 B9 exact closures retained
- AFFECTED_QUALIFICATION_RESULTS：focused 2/2 PASS；integrated 178/178 PASS
- QUALIFICATION_IDENTITY_ACCOUNTING：expected/executed/passed 178/178/178；mandatory 91+2=93；其余全 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；固定实际 consumer/source graph、private-r11 hash provenance 与 candidate loader 绑定
- CONTINUOUS_PROTECTION_COVERAGE：RETAINED_RESOLVED；未冒称本轮 formal coverage
- CAPTURE_COHERENCE_AND_LIMITS：RETAINED_RESOLVED；保留 native29/H733/timeouts/finite graph/批准 capture limits
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS_EXACT_SCOPE；available final sink 保存 primary/marker/diagnostic；stderr 无 durability claim
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（binding only；namespace 未创建）
- BASELINE_RESULT / PREFLIGHT_RESULT / START_CREATED：NOT_RUN / NOT_RUN / NO
- REQUIRED_GATES / PASSED_GATES / FAILED_GATES / NOT_RUN_GATES：29 / 0 / 0 / 29
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 EXPECTED
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED；r10 preformal reviews 为 advisory
- EP19_CLOSURE_CRITERIA_ACCOUNTING：外部 r11 资格与固定 binding 完成；正式29、最终独立接受及权威关闭对账待 parent
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 形成 r11 implementation review/现态 disposition；条件式执行唯一 candidate-formal-002；真实29/8000 identity 对账；最终独立接受与 EP19 关闭对账
- PRODUCT_PUBLICATION / POST_PUBLICATION_SANITY：NOT_PERFORMED / NOT_RUN
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / PUBLIC_MANIFEST_SHA256 / REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED（本 writer 不 push）
- STOP_REASON：R11_IN_SCOPE_CORRECTION_QUALIFICATION_AND_EXACT_BINDING_COMPLETE_PARENT_OWNS_CONDITIONAL_FORMAL

## 边界与历史

没有产品变更/产品测试/shared probes/preparation/baseline/formal，也没有创建正式 namespace。产品预算保持 3/3，正式预算保持 1/2。r10 与此前字节由 manifest 复核；缺失的历史 provenance 保持 `NOT_ESTABLISHED_NO_BACKFILL`。本报告不是 self independent acceptance、正式启动许可、产品发布或 EP19 CLOSED。
