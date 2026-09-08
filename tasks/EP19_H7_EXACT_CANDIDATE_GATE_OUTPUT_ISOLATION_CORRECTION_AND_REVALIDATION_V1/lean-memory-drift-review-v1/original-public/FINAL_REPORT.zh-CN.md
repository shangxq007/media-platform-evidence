# EP19 H7 固定候选实际执行与停止报告

## 结论

Hermes 已完成唯一获授权的正式执行窗口。执行在第一个必需门 `CHANGE_IMPACT` 的 `GATE_BOUNDARY` 保存检查处停止：冻结 baseline 跨命令间隙发生漂移。产品原生命令未调用，因此 `native_exit=null` 表示 `NOT_INVOKED`，不是产品测试失败；包装器以 1 退出。未重试、未刷新 baseline、未发布产品或证据，EP19 未关闭。

最终顶层判定为 `OLD_STRICT_REJECT`、`V2_INPUT_INTEGRITY_RESULT=REJECT`、`V2_BOOKKEEPING_EVALUATION=PASS`。这里的 bookkeeping PASS 只适用于获准的四字段评估，不能覆盖顶层 strict/input-integrity REJECT。writer attribution 仍为 `NOT_ESTABLISHED`。

## 实际测试身份核算

后端 7973（预期 skip 29）与前端 149 均只是预期。由于首门在产品命令前被拒，实际产品套件发现数和执行数均为 0；pass/fail/error/skip 均为 0。missing、unexpected、duplicate 保持 `NOT_EVALUATED_SUITES_NOT_INVOKED`，不伪造完整套件 reconciliation。另有 preparation 范围的 fresh qualification 19/19 PASS；历史 129 仅按 hash/application scope 复用，不称为 fresh 129。

## 29 个必需门

| # | Gate | Result | Reason | Product native | Native exit | Wrapper exit |
|---:|---|---|---|---|---:|---:|
| 1 | `CHANGE_IMPACT` | `FAIL` | `FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP` | `NOT_INVOKED` | `None` | `1` |
| 2 | `H7_FOCUSED` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 3 | `H7_ENTRY` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 4 | `H7_MUTATIONS` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 5 | `ARCHITECTURE_SYNTAX` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 6 | `ARCHITECTURE` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 7 | `GRADLE_PREFLIGHT` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 8 | `COMPILE` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 9 | `AFFECTED_INTEGRATION` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 10 | `RUNTIME_PREFLIGHT` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 11 | `SHADOW` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 12 | `CLASSIFIER_TEST` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 13 | `GITOPS_STAGING` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 14 | `GITOPS_STAGING_EGRESS` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 15 | `GITOPS_PRODUCTION` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 16 | `GITOPS_PRODUCTION_EGRESS` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 17 | `FRONTEND_INSTALL` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 18 | `FRONTEND_LINT` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 19 | `FRONTEND_IDENTITIES` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 20 | `FRONTEND_COLLECTION` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 21 | `FRONTEND_TEST` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 22 | `FRONTEND_BUILD` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 23 | `FORMAL` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 24 | `SEMGREP` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 25 | `FULL_BACKEND` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 26 | `APPLICATION_CLASSPATH` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 27 | `APPLICATION_PROBE` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 28 | `FOUNDATION` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |
| 29 | `BOOTJAR` | `NOT_RUN` | `PRIOR_REQUIRED_FAILURE` | `NOT_INVOKED` | `None` | `None` |

## 保存与准备证据

实际差异投影共 3 项，只有 metadata/delta/hash，不含 Skill/Memory 正文。Memory root 的 `metadata.st_ctime_ns` 从 `1788838990891651268` 变为 `1788839301436583201`；Skills root 及获准 usage metadata 也有差异。嵌套 evaluator PASS 保持其限定语义。

Lean 历史文件 membership 为 4617 regular files；目录为 449（含 root）。最终同一 strict Collector 对 4617 Lean 文件、1 Gradle init 与 9 unique runtime binaries 共完成 4627 项捕获。真实 native probe 的 version/prefix/import+proof 三次退出均为 0，使用 run-local Lean，无 system fallback。

三个隔离 clone 的只读 Git 精确性检查为 `PASS`；formal 后 product worktree changed paths 为 `[]`。固定 base 到 candidate 的四条 tracked candidate diff 另列于 SOURCE_CLONE_VERIFICATION.json，不与本 continuation 的 product edit 混淆。

V2 historical originals/copies、unchanged helper preimages、旧 reporter identity hash 的重新核对结果为 `PASS`。新 post-run reporter 明确不进入已封存 executor identity。

## 未解决的历史事实

以下事实均原样保留：旧执行 5 PASS / 1 FAIL / 23 NOT_RUN；ARCHITECTURE 终止与 FAIL_PRESERVATION；既往 command-gap drift；后续 Lean capture 失败的 29 NOT_RUN；历史 writer unknown/NOT_ESTABLISHED 与 decision/coverage 缺口；`PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE`。V2 不回溯重分类这些失败。

## 发布边界

`PRODUCT_PUBLICATION=NOT_ATTEMPTED`，`EVIDENCE_COMMIT_SHA`、`REVIEW_INDEX_URL` 与 remote verification 均待 parent。manifest 的真实摘要在包顶层 detached `FINAL_FIELDS_WITH_MANIFEST.json`，避免 manifest self-hash 循环。

## 机器字段

- `TASK`: `"EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1"`
- `CONTINUATION`: `"LEAN_TOOLCHAIN_MATERIALIZATION_CORRECTION_AND_EXACT_CANDIDATE_FORMAL_CONTINUATION"`
- `LANE`: `"BACKEND_VALIDATION"`
- `CANDIDATE_COMMIT_SHA`: `"689ab9456461a8d19a72d059f5157092efc43aff"`
- `CANDIDATE_TREE`: `"6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6"`
- `EXECUTOR_IDENTITY`: `"e4631b979d1b96dd40f852011d450878876838266710e4413241ab6b720e374c"`
- `OWNER_CONTRACT_VERSION`: `"OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2"`
- `FAILED_RUN_PRESERVED`: `true`
- `LEAN_SOURCE_SELECTED`: `"/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/owner-clarified-execution-20260907T1120Z/prepared-tools/lean-4.19.0-linux"`
- `LEAN_SOURCE_IDENTITY_VERIFIED`: `true`
- `MATERIALIZATION_PERFORMED`: `true`
- `RUN_LOCAL_TOOLCHAIN_VERIFIED`: `true`
- `DISALLOWED_SYMLINK_COUNT`: `0`
- `PREPARATION_COLLECTOR_COMPATIBILITY`: `{"composition": "4617_LEAN_PLUS_1_GRADLE_INIT_PLUS_9_UNIQUE_RUNTIME_BINARIES", "expected_files": 4627, "hashed": 4627, "result": "COMPLETE"}`
- `NATIVE_TOOLCHAIN_PROBE_RESULTS`: `{"native_exits": [0, 0, 0], "result": "PASS", "system_fallback": false}`
- `FRESH_QUALIFICATION_RESULTS`: `{"duplicates": 0, "errors": 0, "failures": 0, "pass": 19, "skipped": 0, "tests": 19, "unique": 19}`
- `REUSED_QUALIFICATION_SCOPE`: `"Historical V2 129 controls only per bound bytes and unchanged applicability; not a fresh-129 claim"`
- `FORMAL_LAUNCH_BINDING`: `{"executor_identity": "e4631b979d1b96dd40f852011d450878876838266710e4413241ab6b720e374c", "status": "CREATED_AND_USED_ONCE"}`
- `BASELINE_CREATED`: `true`
- `SEAL_CREATED`: `true`
- `PREFLIGHT_RESULT`: `{"engineering_blockers": [], "result": "ENGINEERING_READY"}`
- `FORMAL_START_CREATED`: `true`
- `REQUIRED_GATES`: `29`
- `PASS`: `0`
- `FAIL`: `1`
- `NOT_RUN`: `28`
- `ACTUAL_TEST_IDENTITY_ACCOUNTING`: `"ACTUAL_TEST_IDENTITY_ACCOUNTING.json"`
- `OLD_STRICT_PRESERVATION_RESULT`: `"OLD_STRICT_REJECT"`
- `V2_INPUT_INTEGRITY_RESULT`: `"REJECT"`
- `V2_BOOKKEEPING_EVALUATION`: `"PASS"`
- `PRODUCT_CHANGED_PATHS`: `[]`
- `FRONTEND_LANE_INTERFERENCE`: `"NONE"`
- `HISTORICAL_FAILURES_PRESERVED`: `{"architecture": "FAIL_PRESERVATION", "command_gap_drift": "PRESERVED", "historical_decision_and_coverage_gaps": "PRESERVED", "lean_failed_run": {"FAIL": 0, "NOT_RUN": 29, "PASS": 0}, "old_gate_counts": {"FAIL": 1, "NOT_RUN": 23, "PASS": 5}, "writer_attribution": "NOT_ESTABLISHED"}`
- `PACK_HISTORICAL_BYTE_IMMUTABILITY`: `"NOT_RECOVERABLE"`
- `PRODUCT_PUBLICATION`: `"NOT_ATTEMPTED"`
- `POST_PUBLICATION_SANITY`: `"NOT_RUN_PRODUCT_NOT_PUBLISHED"`
- `EP19_CLOSED`: `false`
- `INDEPENDENT_REVIEW`: `"PENDING"`
- `EVIDENCE_COMMIT_SHA`: `"NOT_ATTEMPTED"`
- `REVIEW_INDEX_URL`: `"PENDING"`
- `PUBLIC_MANIFEST_SHA256`: `"DETACHED:../FINAL_FIELDS_WITH_MANIFEST.json"`
- `REMOTE_VERIFICATION`: `"NOT_ATTEMPTED"`
- `STOP`: `"YES_FORMAL_STOP_FIRST_GATE_CHANGE_IMPACT_GATE_BOUNDARY_FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP_PRODUCT_NATIVE_NOT_INVOKED_WRAPPER_EXIT_1_NO_RETRY"`

## STOP

`YES_FORMAL_STOP_FIRST_GATE_CHANGE_IMPACT_GATE_BOUNDARY_FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP_PRODUCT_NATIVE_NOT_INVOKED_WRAPPER_EXIT_1_NO_RETRY`
