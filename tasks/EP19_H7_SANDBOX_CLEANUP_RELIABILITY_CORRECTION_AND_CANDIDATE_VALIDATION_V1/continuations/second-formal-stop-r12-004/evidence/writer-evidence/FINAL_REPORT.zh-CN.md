# EP19 H7 外部执行器符合性纠正与候选资格报告

## 结论

Writer 范围已完成：八项外部缺陷 AR001/002/003/004/007/008/009/010 均已修正，AR005/006 fresh 回归未复发；最终一体化资格 `qualification-005` 实际为 **107/107 PASS，0 failure，0 error，0 skip，0 duplicate，0 missing，0 unexpected**。最终 driver、精确 29 门矩阵、完整源码差异、consumer/provenance closure 与 `candidate-formal-002` runtime binding 已交付。

本结论是本任务 writer 的工程资格结论，不是独立接受。依照 WRITER_PACKET，writer 未执行 shared preparation/probe/baseline/formal，也未创建 `candidate-formal-002` namespace；正式预算仍是 1/2 已用、1 次剩余。Parent 可先独立审核本包，再使用 `PARENT_HANDOFF_COMMANDS.md`；不得把本报告当成正式门禁结果。

## 固定身份与范围

- TASK：`EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1`
- CONTINUATION：`CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT`
- LANE：`BACKEND_VALIDATION`
- CANDIDATE_COMMIT_SHA：`a29864343ed4f630b052c20d86c23b240f13cfd0`
- CANDIDATE_TREE：`fd37409d0274662abbe86f69e3d963c05b379696`
- CANDIDATE_IMMEDIATE_PARENT：`689ab9456461a8d19a72d059f5157092efc43aff`
- PRODUCT_PATCH_SHA256：`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`
- PRODUCT_CHANGED_PATHS：`[]`
- PRODUCT_BEHAVIOR_CHANGED：`false`
- APPROVED_CONTRACT_CHANGED：`false`
- 最新授权 SHA-256：`b4e996d02931d722c959e9a4bbb1d0023ec0cd5e810b5b1a061299452816fd76`
- EXECUTOR_IDENTITY：`8471ab2daf22b0a71389502465ec63ab8d89474b7f538f223e71de9a9d7e86d7`
- 最终 source-binding canonical SHA-256：`b62d36bb48e098abd0e88f5ccb44ae144436a41c0944d5cbf607e82d61660cfc`
- 最终源差异 SHA-256：`a993b5ff49328f03a3854833d7b643d8e4485d9b2073e20320f93a21c62fe028`
- 原 29 门 matrix SHA-256：`57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`，复制前后相同。

只在 `implementation/`、`fixtures/`、`writer-evidence/`、`private/` 写入；`private/` 为 0700，两个私有输入为 0600。未改产品源码、测试、依赖、共享 Skills/Memory、ledger/usage、frontend lane、历史目录或 canonical checkout。旧 sealed `integration-001/FINAL_MANIFEST.sha256` 已以 `sha256sum -c --quiet` 实际复核，native exit 0。

## RED/GREEN 与最终资格

| 批次 | 实际结果 | native exit | native duration | native log SHA-256 |
|---|---:|---:|---:|---|
| red-group-1 | 4 个控制失败，确认 AR001/002 predecessor | 1 | 0.220999464s | `35fd0e5aaffd91c97b45688c863f2449ade0fd93ba7bbd482ab63ef66d361acb` |
| green-group-1b | 4/4 PASS | 0 | 0.367966507s | `1d06b7dc7a72d34d976ea510130d457ece5668ed457ac4098c3842a400b5b025` |
| red-group-2 | 2 FAIL + 1 ERROR + 1 PASS，确认 AR003/004 | 1 | 0.129949375s | `40c8fee9820ad46f00b48e15d1e19509cf8fddc47f0e8e4652726c23699c1af8` |
| green-group-2 | 4/4 PASS | 0 | 0.114064536s | `dd0cbbc08164408e97a06463d23873b3c43ad7dcf86618093ca92b965184ff1d` |
| red-group-3 | 5 ERROR，确认 AR007 所需 validator 缺失 | 1 | 0.119473967s | `5e7760d95aa147cbe191dd4869e5333a8a281d5d68422f23ddc38ee6d21ec0ea` |
| green-group-3 | 5/5 PASS | 0 | 0.108916131s | `e4ecb820ee789fdb685d67b41475772395768fd2153b17696f7e7427e2b00907` |
| red-group-4b | 5 FAIL + 1 PASS，确认 AR008/009/010 | 1 | 5.483677622s | `75d019d6e28cb2917651967344be8b67a968767f816286c09060c2e4b9cc872d` |
| green-group-4b | 6/6 PASS | 0 | 0.581151013s | `42c5f5e5a21442821148818e7fb2da5820bf1695f001ce6bc2a5ad8d4db0f45b` |
| qualification-005 | 107 unique PASS | 0 | 12.064699392s | `7c1994b8835f7726f1e3acda61c6f00d207bc0de50c108ba9a9eccf7c196b25f` |

`qualification-001` 真实失败于复制后 Owner 文件定位，`qualification-003` 真实失败于一次 native_observe 缩进回归；二者均保留。`qualification-002`、`qualification-004` 当时通过，但后续受影响源码继续变化，明确标为 stale/non-authoritative。最终权威资格仅为 `qualification-005`，其 QUALIFICATION/RESULT/PROCESS SHA-256 分别为 `752bc185136e74883925b851d80b34b988109642fe2571adc34e1debf86ecc09`、`393a9a37d2746342748c988b52a78ffea16b73aa729cd3bdb67de8e866b17c3e`、`4bc000464adc7c7e3835e05c40f3dcc89cd2979bfead36ba39d8ab8ba892aced`。

全部资格为 task-private fixture：`formal_attempt=false`、`product_tests=false`、`shared_preparation=false`、`shared_baseline=false`、`shared_probes=false`。

## AR001..AR010 disposition

详细逐项契约、源码、真实反例、RED/GREEN、外层入口与证据位置见 `CONFORMANCE_MATRIX.json`。

- AR001 RESOLVED：正式 driver 从 baseline strict capture 起持有同一 native watcher，贯穿 preflight/prestart、所有 command/gate 和 FINAL/COVERAGE/SEAL；祖先 identity endpoint 与事件流共同 fail-closed。
- AR002 RESOLVED：V3 路径恢复 exact temp regular/nlink/dev/uid/gid/mode0600、双向 cookie 与 source/target lifecycle；外部移入 usage、temp 移出、非法短寿命 temp 均真实拒绝。
- AR003 RESOLVED：每 boundary 记录 wall/monotonic 窗；正式默认使用保护起点或前一已接受 boundary 至实际 capture end，2099 隐藏上界与 wall rollback 均拒绝。
- AR004 RESOLVED：原始 framing 在 JSON parser 前拒绝 BOM/raw CR/CRLF/empty/partial/invalid UTF-8；escaped `\\r` 与 raw CR 区分。
- AR005 RESOLVED_PRESERVED_NO_REGRESSION：previous_usage 行为保留，fresh outer regression PASS。
- AR006 RESOLVED_PRESERVED_NO_REGRESSION：正式 CLI 仍无 bundle/coverage/strict 摘要注入口，fresh outer regression PASS。
- AR007 RESOLVED：mandatory control 集合独立固定；expected/executed/passed/failed/errored/skipped/missing/unexpected/duplicate 全核算。实际 fixed29 candidate/helper source closure、命令、applicability 与私有 map/inventory 均读取并 hash 校验。
- AR008 RESOLVED：证据 durable 后才提交 session/previous_usage/previous boundary；任一 capture/evaluate/write/binding 异常锁死 adapter；失败后不调用成功 FINAL/COVERAGE/SEAL。
- AR009 RESOLVED：统一 durability 对文件、直接父目录及每个新建嵌套目录执行 fsync；failure marker 自身失败也不解除进程内 latch。
- AR010 RESOLVED：file read、directory walk/list、manifest traversal、event drain/pending 均在循环内检查 deadline/cap；bundle 三次重试为共享 outer budget。潜在阻塞 acquisition 由可恢复 SIGALRM 控制，真实 slow-read 与 1200-file event flood 已验证。

Owner 已接受的 ledger 捕获间 overwrite-restore/truncate-regrow 不可见性仍原样披露，不冒称完整 syscall 历史；没有加入 3600 秒全 attempt 上限，也没有改变原 29 门命令、matrix 或 EXPECTED 8000/29。

## 依赖、eligible 与最终 binding

`DEPENDENCY_BINDING.v2.json` 的 validator 实际闭合四个来源角色：fixed29 consumer binding、current applicability、private eligible map、private strict inventory。它逐项验证 29 个命令、90 个 candidate source 条目、6 个 external helper、无 ledger argv/token reader，以及候选和 map hash。唯一 ledger consumer 是 `bookkeeping_v3.evaluate_ledger`；authorization、instruction/skill selection、candidate selection、gate/policy 和 rollback 均为 false；动态未知 reader 必须拒绝。

最终 runtime binding：`RUNTIME_BINDING.candidate-formal-002.final.json`，SHA-256 `cddfba09d509a2d777a543eee4ee9029a34b79811b0fdd534e059f2af4b709c7`。已通过 `binding_contract.load` 实际重载，绑定：

- exact run ID `candidate-formal-002`（任何后缀均拒绝）；
- fixed candidate/tree/parent/patch；
- 29 门 matrix 与 32 个 input inventory hash；
- 最新 Owner 授权；
- 最终 107-control qualification；
- dependency/applicability/private map/private inventory；
- 最终 source binding 与 exact patch。

实际 integrated driver 路径：`implementation/tooling/executor/external29_driver.py`。它不是 adapter-only：`formal` 会先 durable consume，再构建 policy/observer，完成连续 baseline/preflight/prestart，执行原完整 29-gate graph，逐门保存原生命令、exit、output/freshness/preservation/acceptance，并按首个依赖失败停止及补齐 NOT_RUN。Writer 未调用该 `formal`。

## 正式与 EP19 实际状态

- FORMAL_ATTEMPTS_USED：`1/2`
- SECOND_FORMAL_RUN_ID：`candidate-formal-002`（BOUND_BUT_NOT_CREATED_OR_CONSUMED）
- BASELINE_RESULT：`NOT_RUN_BY_WRITER`
- PREFLIGHT_RESULT：`NOT_RUN_BY_WRITER`
- START_CREATED：`false`
- REQUIRED_GATES：`29`
- PASSED_GATES：`0`
- FAILED_GATES：`0`
- NOT_RUN_GATES：`29`
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：`NOT_RUN`；EXPECTED identities=`8000`、EXPECTED skipped=`29`，实际 discovered/executed/passed/failed/errored/skipped/missing/unexpected/duplicate 均未预填。
- FINAL_PRESERVATION_RESULT：`QUALIFIED_ON_PRIVATE_FIXTURES_FORMAL_NOT_RUN`
- INDEPENDENT_REVIEW_RESULT：`REQUIRED_NOT_PERFORMED_BY_WRITER`
- EP19_CLOSED：`false`

剩余动作仅属于 parent/独立角色：审查本固定 source/binding/qualification/matrix；完成其拥有的实际 preparation/endpoints/disposition/revalidation；若条件仍满足，以唯一 namespace 执行第二次 formal；随后对原始正式结果作独立审查与既有关闭条件对账。若第二次失败，预算耗尽并停止，不得第三次。

## 发布与停止原因

- PRODUCT_PUBLICATION：`NOT_PERFORMED`
- POST_PUBLICATION_SANITY：`NOT_RUN`
- Evidence push：`NOT_PERFORMED_BY_WRITER`（WRITER_PACKET 明确禁止 writer evidence push）
- EVIDENCE_COMMIT_SHA / REVIEW_INDEX_URL / MACHINE_INDEX_URL / REMOTE_VERIFICATION：`NOT_APPLICABLE_LOCAL_HANDOFF`
- STOP_REASON：`WRITER_SCOPE_COMPLETE_INTEGRATED_QUALIFICATION_AND_BINDING_HANDOFF; PARENT_OWNS_PREPARATION_FORMAL_AND_INDEPENDENT_REVIEW`

这不是阻塞于重复批准；writer 获准范围已经完成。Parent 命令和不可复用边界见 `PARENT_HANDOFF_COMMANDS.md`。
