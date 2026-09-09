# continuation-004 r2 外部执行器符合性修正报告

## 结论

r2 工作执行器已完成：六项 preformal 实质 finding（AR001/002/007/008/009/010）均有真实行为前驱 RED、修正后 GREEN 和最终集成资格；AR003/004/005/006 回归保持。最终新鲜资格为 **126 expected / 126 executed / 126 PASS**，0 failure、0 error、0 skip、0 missing、0 unexpected、0 duplicate、0 invalid status；41 个 affected mandatory identity 由源码固定集合独立于实际输出。

本轮严格遵守 repair packet：只写 `implementation-r2/`、`fixtures-r2/`、`writer-evidence-r2/`、`private-r2/`；r1 hash stream 仍为 `84af516b…a541`，未改动。没有运行产品测试、共享 preparation/probe/baseline/formal，没有创建 `candidate-formal-002` namespace，没有消费第二次正式尝试。

## 固定身份与源码

- TASK：`EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1`
- CONTINUATION：`CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT`
- LANE：`BACKEND_VALIDATION`
- CANDIDATE_COMMIT_SHA：`a29864343ed4f630b052c20d86c23b240f13cfd0`
- CANDIDATE_TREE：`fd37409d0274662abbe86f69e3d963c05b379696`
- CANDIDATE_IMMEDIATE_PARENT：`689ab9456461a8d19a72d059f5157092efc43aff`
- PRODUCT_PATCH_SHA256：`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`
- PRODUCT_CHANGED_PATHS：固定历史候选的 5 路径；本轮产品变化为 0。精确列表见下文机器索引。
- EXECUTOR_IDENTITY：`c6b13e1a53c48f737999eba846845b7169e2f6ac23052d8bfa6d3208f7729dbd`
- RUNTIME_BINDING_SHA256：`c5f872ad3522de981370f2d8d214b1a16afe585bb75a6e3bbec4e0dc4cb47c68`
- IMPLEMENTATION_PATCH_SHA256：`b97f4716c625f768819dfa3f3a448885bd4e00aaa716ffd7d8ea565086a6954f`
- GATE_MATRIX_SHA256：`57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`，与 r1 完全相同。
- APPROVED_CONTRACT_CHANGED：`NO`。

## 实质修正

AR001：strict receipt 改为第二次 drain/identity adjudication 后再持久化；普通边界也把 continuous 事件写入决策。最终 SEAL 使用 Engine capture 后的 final event source，drain 两个 observer、拒绝任何 post-capture event、关闭观察器、记录真实 `observation_ended_monotonic_ns` 后才落盘，且明确不声称端点之后仍观察。真实 Memory-like 写入已从“磁盘 PASS、内存 REJECT”修正为持久 REJECT；组合 SEAL receipt 含实际 continuous event。

AR002：seed observer 在 watch 建立时取得必要 metadata baseline，并在 production policy 建成后以 root/paths/eligible-map 精确一致性 rebind。合法可见 0600 temp 经同一 seed→policy wiring、真实 inotify 和 paired rename 正控通过；外部移入、移出、坏 mode、cookie/source/target 负控继续拒绝。

AR007：强制 formal qualification 只接受 v2；UNKNOWN status、expected/actual duplicate、passed 集合不精确全部拒绝。mandatory loader 解析原生 unittest log 并逐 identity/status 与 RESULT 对账，同时校验 PROCESS argv、raw_log、native_exit 和 digest。当前 29 命令、90 个 candidate source、6 个当前 r2 helper、driver→runner→boundary→ledger 边和 instruction origin 均读取真实字节验证；缺少的旧 PARENT_SOURCE_AFTER/SOURCE_BINDING_BEFORE 被明确替换为当前字节验证，不提升旧有限材料的适用范围；未知实际依赖继续阻断，不要求任意未来 plugin。

AR008：`_require_live`、consume、attach/binding、Engine、evidence、observer 和 strict acquisition 异常都进入同一个不可逆 latch。failure marker 自身失败不会清除内存 latch；接受状态仍仅在证据成功持久化后推进。失败后只能保存诊断，不能生成成功 FINAL/COVERAGE/SEAL；真实暂态失败后恢复同对象的三个前驱均从错误接受变为拒绝。

AR009：`runner.prepare` 的 run/runtime 目录改为逐层发布 fsync；formal consume 在写 marker 前同步已有 task-local ancestor chain；strict-decisions 不再普通 mkdir；`coverage.put` 统一使用 exclusive file fsync + 直接父 fsync，因此 START、preflight、seal、FINAL_FAILURE、RESULTS 及 gate receipts 走同一持久流程。实际 strict call-path fsync trace 已从缺失 runtime 父目录修正为包含其发布链。final strict/SEAL receipt 均在最终观察决定定型后写入。

AR010：bookkeeping file stat/open/read/postread stat、directory readdir、manifest traversal、observer read/temp lstat、native dynamic tree acquisition、strict preservation inventory及 decision JSON 读取均使用绝对共享 deadline 的 raising SIGALRM guard；没有声称 handler 抛异常时 PEP475 必然重启。readdir 改为增量 `scandir`，在保留第 N+1 项之前拒绝；动态已拒绝子树不再先扫描。真实 postread stat delay、temp metadata delay、持续增长、事件洪泛和目录 over-capacity 均通过，资源由 finally/close 收尾。

AR003/004：实际 wall/monotonic 窗口、previous accepted lower bound、clock rollback、raw CR/CRLF 与 escaped CR 区分回归通过。AR005：合法 usage 改变后的不变边界与 allowed 29-step fixture 通过。AR006：formal CLI 仍无 bundle/coverage/strict 成功注入，binding 和实际 capture 必经。

逐条源码、反例、RED/GREEN、外层入口和证据定位见 `CONFORMANCE_MATRIX.r2.json`。

## 资格、依赖与运行绑定

- 前驱 RED `red-preformal-002`：11 个真实控制中 10 FAIL + 1 ERROR；错误原因是合法 seed temp 的实际 `KeyError: usage_baseline`，不是缺函数/导入。其余明确显示错误接受或实际超时。
- 最终 predecessor GREEN `green-preformal-002`：11/11 PASS。
- final-observation/dependency/bounds 增补 `green-postfix-001`：7/7 PASS。
- affected regression：group1 4/4、group2 5/5、group4 6/6 PASS。
- 最终 qualification-003：126/126 PASS，native exit 0，18.062253056 秒；原生 log SHA-256 `76abbe…18f8`。
- `coverage.qualification_inputs` 在最终 binding 环境下实际返回 PASS，核对 6 个 closure 文件、全部 126 native identities/statuses、PROCESS/RESULT 和 107 个当前 source-binding 文件。
- dependency binding SHA-256：`5058b308…023`；private map/inventory 保持本地 mode 0600，父目录 mode 0700。
- 旧 adapter71/formal158 只按 qualification receipt 中明示的未变适用范围保留，不改称 fresh；本轮 126 项全部是 r2 fixture-only fresh controls，不是产品测试。

## 正式状态与交接

- FORMAL_ATTEMPTS_USED：`1/2`。
- SECOND_FORMAL_RUN_ID：`candidate-formal-002`（仅 binding，namespace 未创建）。
- BASELINE_RESULT：`NOT_RUN_R2`。
- PREFLIGHT_RESULT：`NOT_RUN_R2`。
- START_CREATED：`NO`。
- REQUIRED_GATES：`29`。
- PASSED_GATES：`0`。
- FAILED_GATES：`0`。
- NOT_RUN_GATES：`29`。
- FULL_BACKEND_TEST_IDENTITY_ACCOUNTING：`NOT_RUN`；8000 / 29 仅保留 EXPECTED，不填入实际字段。
- FINAL_PRESERVATION_RESULT：`QUALIFIED_SYNTHETIC_PATH_ONLY_FORMAL_NOT_RUN`。
- INDEPENDENT_REVIEW_RESULT：`NOT_PERFORMED_BY_WRITER`。
- EP19_CLOSURE_CRITERIA_ACCOUNTING：工程 r2 handoff 条件已形成；正式29门、独立接受、原权威账本追加、当前候选产品发布和发布后 sanity 仍未发生。
- EP19_CLOSED：`NO`。
- PRODUCT_PUBLICATION：`NOT_PERFORMED`。
- POST_PUBLICATION_SANITY：`NOT_RUN`。

Parent 的真实命令已固化在 `PARENT_HANDOFF_COMMANDS.r2.md`。这不是重复审批提案；是已授权范围内完成后的可执行交接。正式和 shared preparation/probe 未在本轮越权执行。

## 停止与剩余条件

REMAINING_BLOCKERS：没有已知 r2 工程符合性 blocker；剩余是 parent-owned 的实际 preparation/formal、随后与实现者分离的独立审查，以及既有关闭/发布条件。STOP_REASON=`AUTHORIZED_R2_CORRECTION_AND_QUALIFICATION_COMPLETE_PARENT_FORMAL_EXCLUDED_BY_PACKET`。

证据未发布；EVIDENCE_COMMIT_SHA、REVIEW_INDEX_URL、MACHINE_INDEX_URL、PUBLIC_MANIFEST_SHA256、REMOTE_VERIFICATION 均为 `NOT_PERFORMED`。本轮未使用凭据或网络发布。
