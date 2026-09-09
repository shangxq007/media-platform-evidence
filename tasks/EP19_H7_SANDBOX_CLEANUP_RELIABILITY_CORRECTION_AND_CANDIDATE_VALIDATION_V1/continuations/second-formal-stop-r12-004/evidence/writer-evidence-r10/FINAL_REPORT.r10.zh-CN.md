# r10 最终边界持久化与生产 structured stderr fallback 修正报告

## 结论

本轮在新 `implementation-r10/`、`fixtures-r10/`、`writer-evidence-r10/`、`private-r10/` 内关闭 B9-B-1 与 B9-B-2。r9 及此前历史保持不变。没有产品、产品测试、依赖版本、共享 Skill/Memory/bookkeeping、frontend、shared probe、preparation、baseline 或 formal 操作；没有创建 `candidate-formal-002` namespace，正式预算仍为 1/2。

相同测试体 `35061728fbe0b0dc96a7e87554110dbda34e2ecc514281429d24cda794be46fa` 的实际 predecessor RED 为 3/3 FAIL；最终 source-bound GREEN 为 3/3 PASS。第一个控制进入生产 `formal()` 的实际 FINAL handler，在实际 `runtime/FINAL_FAILURE.json` fd 注入写失败，再从真实 `FORMAL_FAILURE.json` 读回，核对原 RuntimeError、secondary OSError、occurrence、contexts、types、`IRREVERSIBLY_LATCHED_REJECT`。第二个控制由真实父进程捕获生产 `main()` 子进程 stdout/stderr；两个实际私有 sink 写均失败时，子进程非零、stdout 空、stderr 为单一可解析 JSON，保存 3 个 unique occurrence 与完整有限 context，并且不输出私有 reason body。stderr 标注 `BEST_EFFORT_NOT_DURABLE`；stderr 自身失败返回 false，不产生成功或持久性声明。

最终集成资格 176/176 PASS、176 unique、91 mandatory，duplicate/missing/unexpected/fail/error/skip 均为 0。固定 runtime binding SHA-256 `d87db39c3f5ffa1801073bf45d564cc726c4409d23d3dd8939396a2921150f9e`；只读实际 loader PASS，绑定 119 tooling source、qualification `ad42f0561d6bdf4be3c38496ac831fa0cd07ab9e872e7d00eb1bbe4913b5b297`、dependency `c6f4217a9e3bb16ac0a8fae4f368b59f9fb839c68d9782d8ebc63ea287ef95df` 和固定 candidate/tree/patch。PID 仅为 writer-owned subprocess namespace 观察，不是独立 OS attestation。

## 关键字段

- TASK：EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
- CONTINUATION：CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT（r10 external correction）
- LANE：BACKEND_VALIDATION
- CANDIDATE_COMMIT_SHA：a29864343ed4f630b052c20d86c23b240f13cfd0
- CANDIDATE_TREE：fd37409d0274662abbe86f69e3d963c05b379696
- PRODUCT_PATCH_SHA256：bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690
- PRODUCT_CHANGED_PATHS：[]
- EXECUTOR_IDENTITY：runtime binding SHA-256 `d87db39c3f5ffa1801073bf45d564cc726c4409d23d3dd8939396a2921150f9e`
- APPROVED_CONTRACT_CHANGED：NO
- AR001..AR007 / AR009 / AR010_DISPOSITION：RETAINED_RESOLVED
- AR008_DISPOSITION：CLOSED_EXACT_FINITE_FINAL_BOUNDARY_AND_NATIVE_FALLBACK_SCOPE
- AFFECTED_QUALIFICATION_RESULTS：focused 3/3 PASS；integrated 176/176 PASS
- QUALIFICATION_IDENTITY_ACCOUNTING：expected/executed/passed 176/176/176；mandatory 88+3=91；其余全 0
- DEPENDENCY_AND_ELIGIBLE_BINDING：PASS；有限实际依赖图、r10 main/serializer/final writer edges 与 private r10 hash provenance 已绑定
- CONTINUOUS_PROTECTION_COVERAGE：RETAINED_RESOLVED；未冒称本轮 formal coverage
- CAPTURE_COHERENCE_AND_LIMITS：RETAINED_RESOLVED；保留有限图、H733、原生29、timeout 与批准 capture limits
- EVIDENCE_DURABILITY_AND_FAILURE_LATCH：PASS_EXACT_SCOPE；stderr 仅 best-effort、无 durability claim
- FORMAL_ATTEMPTS_USED：1/2
- SECOND_FORMAL_RUN_ID：candidate-formal-002（binding only；namespace 未创建）
- BASELINE_RESULT / PREFLIGHT_RESULT / START_CREATED：NOT_RUN / NOT_RUN / NO
- REQUIRED_GATES / PASSED_GATES / FAILED_GATES / NOT_RUN_GATES：29 / 0 / 0 / 29
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：NOT_RUN；8000/29 仅 EXPECTED
- FINAL_PRESERVATION_RESULT：NOT_RUN_FORMAL
- INDEPENDENT_REVIEW_RESULT：NOT_CLAIMED
- EP19_CLOSED：NO
- REMAINING_BLOCKERS：parent 对 r10 包独立评审、条件式执行唯一 candidate-formal-002、真实29门禁与最终独立接受/关闭对账
- PRODUCT_PUBLICATION / POST_PUBLICATION_SANITY：NOT_PERFORMED / NOT_RUN
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / REMOTE_VERIFICATION：LOCAL_ONLY_NOT_PUBLISHED
- STOP_REASON：R10_QUALIFICATION_AND_FIXED_BINDING_COMPLETE_NO_FORMAL_IN_SCOPE

## 历史与边界

`qualification-001` 的 argparse compatibility 失败和 `runtime-loader-001` 的 r9 路径 guard 失败均原样保留；未覆盖、未回填。r9→r10 byte delta 为 9 个 added/changed 文件，patch SHA-256 `bf9f6c29a87ae21515aba268a2f9b2ee194a736379637b3264ab8fc0667c5d4b`。本报告不是独立接受、产品门禁结果、正式启动许可或发布结果。
