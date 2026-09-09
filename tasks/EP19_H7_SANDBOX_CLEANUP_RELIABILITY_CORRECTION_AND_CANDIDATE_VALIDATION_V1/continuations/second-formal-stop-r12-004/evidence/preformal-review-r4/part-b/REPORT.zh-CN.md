# r4 part-b 只读预审报告

## 结论

**AR007 RESOLVED（本轮具体有限 parser 图缺口）；AR008 OPEN；AR009 OPEN（主清理/辅助日志/初始失败 seal 已修，已存在 sealed 后的失败诊断封存仍遗漏）。**

新隔离 preparation 的实际完成状态 **NOT_ESTABLISHED**；本报告不启动 preparation，不把 loader PASS 当作正式运行或独立最终接受。旧无 tested-source 绑定的历史 RED/GREEN 精确字节仍 **NOT_ESTABLISHED**。本次为 advisory preformal，不是 final independent acceptance。

路径均相对 J：`implementation-r4/tooling/executor` 简称 E，`implementation-r4/tooling/qualification` 简称 Q，`writer-evidence-r4` 简称 W。已读 Owner 原文、REPAIR_R4_PACKET、r3 part-b、r4 final-003 report/matrix/runtime binding 和实际源码。没有导入被审模块、运行测试/探针/准备/正式门禁、修改产品或共享资源。仅写本 part-b。

## AR007 — RESOLVED：当前真实有限依赖图

- E/runner.py:68-77 在新 run preparation 明确调用 parser_tools.prepare；E/parsers.py:41-45 将实际 parser tools 参数改为该 run 的 `runtime/cache/frontend/parser-tools`，而非旧 D/tools。实际链为 runner:400-405 → freshness.py:40-49 → parsers → vite_closure.py:6-12 → vite_closure.mjs；不是假设的未来 plugin。
- E/dependency_contract.py:162-189 强制源码节点、parser callback/JS subprocess 等边，并独立 AST 重建 reachable_local_graph；:211-242 强制 helper 集与 FRONTEND_BUILD helper 边、实际 parser graph；:247-252 逐包全文件 digest。遗漏同 schema 节点或边不会被自报 `unresolved=[]` 放行。静态独立重建的 **38 Python nodes / 112 import edges** 与已绑定图相等。
- E/parser_tools.py:9-10,27-62 将四个实际直接 parser import 及可达 package dependencies 绑定至固定历史 source tree。实际校验 **8 packages / 216 files**，包版本、package.json hash、全文件集合/hash 精确相符：acorn 8.17.0（10 files）、postcss 8.5.15（55）、postcss-value-parser 4.2.0（9）、parse5 8.0.1（33）、entities 8.0.0（58）、nanoid 3.3.12（26）、picocolors 1.1.1（7）、source-map-js 1.2.1（18）。实际传递边：parse5→entities；postcss→nanoid/picocolors/source-map-js。完整定位和 hash 在 W/DEPENDENCY_BINDING.r4.final-002.json 的 actual_execution_scope.parser_package_graph；本次对账在 STATIC_VERIFICATION.json。
- source root 精确为 `USER_HOME/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/sources/frontend/frontend/node_modules`。该旧来源**仍是显式必需输入，不是可消失的历史注释**：loader 经 binding_contract.py:58-61 → dependency_contract.py:239-252 重读 source_graph；新 prepare 经 parser_tools.py:65-82 再读并逐文件校验复制。source root/必需包/必需依赖丢失在 :34-35/:55-57 拒绝，不会默认为无依赖。未执行新 prepare，因此不声称新 cache 已物化；不得在准备前删旧来源。
- 不要求任意未来 Vite plugin 全源码证明；candidate Vite 仍为 prepared frontend node_modules 的既有 runtime boundary（dependency_contract.py:236-238），未扩大契约。
- Q/test_r4_remaining.py:155-189 的现有负控确实对当前 v5 删除 node/edge，且日志 W/qualification-006/QUALIFICATION.native.log:135、green-focused-006/NATIVE.log:1 为 ok。没有把旧 schema 拒绝当成新 missing-edge 证明。

## AR008 — OPEN：正常 observer 返回的归类修了，异常/复合路径仍丢失或误判

### 已修复（RESOLVED）

E/native_observe.py:292-300 明确记录保护拒绝与 timeout 的终止原因；:335-342 独立保存 exit、protection、timeout 等；E/external29_driver.py:214-243 不再从非零 native exit 直接推出产品失败。Q/test_r4_remaining.py:191-249 确实运行私有 native child，经过真实 observer 后送 actual execute_actual_graph；现有 GREEN 支持保护/超时两条独立返回路径。它用 stub runner.run_gate（:211-218），不是完整 runner 的异常路径覆盖，也没有同时故障断言。

原 latch/接受推进修复仍保留：E/boundary.py:217-229 先写证据再推进 session/usage；E/executor_adapter.py:95-119 先 failed=True 后写 marker；driver:280-290 在 gate FAIL 后不进后续接受边界。

### B4-008-1 — OPEN：实际 parser 的证据/环境异常被标成产品断言失败

E/runner.py:401-405 在进入整个 parsers.parse 前设 `stage=PRODUCT_ASSERTION`；:424-436 只用 stage 把任何异常标成 product_assertion_failure=True，且关闭 wrapper/environment 的推导。实际 FRONTEND_BUILD parser 调 E/vite_closure.py:8-11 的 log durable open/fsync、subprocess launch、output fsync。这里的 OSError（例如 helper log 发布失败、node 无法启动）不是产品断言，却落入同一 PRODUCT_ASSERTION_FAILURE，evidence_persistence_failure=False（因为 :425 只识别另外两个 stage）。这与“独立产品/保全/环境/持久化维度”不符。

### B4-008-2 — OPEN：观察异常及 marker/最终 receipt 异常会丢失已有因果事实

E/native_observe.py:343-354 遇异常仅抛原异常/ExceptionGroup，不返回已执行 child 的 pid/exit、termination_causes、观察结果维度。实际日志 stream 的 fsync 位于 :288 的 context exit，能在 child 已退出或已被保护/timeout 终止后失败。runner:390-391 只有正常返回才合并 observed；异常进入 :421-437 时 r 仍 native_exit=None，native_invocation=False，cleanup_failure 默认 False，primary+cleanup 分组也未结构化解出。因此在复合存储/观察/清理故障中，已经发生的 native invocation/终止原因会消失。

另外 driver:281-285 已持有完整失败 result 后调用 adapter.fail；marker 写失败被 :291-294 捕获，并**新建** native_exit=None、无 failure_dimensions 的 result，覆盖先前事实。runner.py:486 最终 receipt put 失败也走同一简化路径。latch 仍 fail-closed，不是放行问题；是 Owner 要求的独立失败核算/因果证据仍不完整。现有 r4 控制不覆盖这些实际 runner/driver seam；不得用 139 PASS 关闭。

## AR009 — OPEN：具体发布顺序已修，seal 后失败证据仍不能封存

### 已修复（RESOLVED）

- E/freshness.py:8-36 对 regular/nlink=1 稳定读；:31 durable exclusive mirror 完成后，:32-33 复核原件身份及摘要，:35 unlink，:36 同步原父目录。durability.py:16-30,59-74 同步新父链、文件和发布父目录。原 cleanup-before-durable 缺口关闭。
- E/vite_closure.py:8-11 使用 durable stream；失败 returncode 在 stream 退出后才抛异常，成功 output 读取前同步。失败辅助原生日志不再仅靠后续成功 seal。
- runner.py:473-485 为普通初始/执行失败 durable 保存 failure-details，并调用 artifacts.seal_failure；失败 seal 异常保存 failure_evidence_error，**不会覆盖原 reason/error_type/traceback**。artifacts.py:83-91 不会把 FAIL 改为 PASS。Q/test_r4_remaining.py:251-314 的现有资格真实覆盖 mirror ordering、初始 acquisition failure 的 sealed copy 和真实 Node failure-log 路径；GREEN 日志:3-4 支持这一有限范围。

### B4-009-1 — OPEN：成功封存已建目录后转 FAIL，诊断 seal 确定性撞同一独占目录

E/artifacts.py:29-37 总是独占创建 `gate/sealed`；finalize :74-77 完成 copy/verify 后还调用 after_copy。E/runner.py:453-466 的实际 after_copy 包含 sealed acceptance digest、Git→resources→JAR 再校验，任何不符会在 sealed 已存在时抛错。runner:468-479 转 FAIL、写 failure-details 后再次调用 seal_failure → artifacts.seal → 对同一个 `gate/sealed` exclusive_directory，确定抛 FileExistsError（不是必须假设磁盘永久不可用）。诊断 failure-details 是后写的，不在原 immutable seal 中；runner:480-485 只能记 failure_evidence_sealed=False。

原生及已复制产物仍保留，不声称丢失所有日志；原始错误也仍保留。这一具体分支缺的是失败诊断必需证据的独立 immutable seal，不能以初始 acquisition failure seal 成功代替。不要覆盖或删除原 sealed；应保留原副本并为失败诊断建立不冲突的独占封存/引用。当前测试在 check_execution_seal 最初就注入错误（Q:282-284），没有走已有 sealed 后失败分支。该分支 fresh behavioral qualification 为 NOT_ESTABLISHED。

## 资格、运行绑定与 RED/GREEN 来源独立对账

- final-003 runtime digest：`90153fc4b2ffdb823599412c1d93161ea09f4245f9a42cf0bdba12c95efcd924`。**110 source files** 与 binding、qualification-006 source_before/source_after 及当前字节精确相符；owner/dependency/qualification/adapter/applicability/private-map/private-inventory 七项 hash 全相符；dependency 的四 source receipts 相符。90 candidate working-source hashes 与绑定 candidate source digest 相符（本次未重新执行 Git blob/tree/patch 验证，不追认该部分为 fresh Git 核验）。必要私有 origin hashes 与 eligible set 只做本地布尔核验，无正文输出。
- 独立逐行解析 W/qualification-006/QUALIFICATION.native.log：**139 expected /139 unique actual /139 PASS；FAIL/ERROR/SKIP/missing/unexpected/duplicate/invalid 为 0**；native identity/status 与 RESULT.controls 精确相等。原 RESULT 行还含时间/expected 字段，所以 raw row equality=False 不代表 identity/status 不同，STATIC_VERIFICATION 明确另列 native_identity_status_exact=True。AST 固定 mandatory **54** 全存在（不是“139 mandatory”）。PROCESS raw/result hash、5 项 qualification dependencies 全相符。
- W/qualification-006/PROCESS.json:2-10 完整 argv；:293 cwd；:296-302 log/exit/result digest；:307-531 before/after source。loader 真实必经 E/coverage.py:122-181 校验 source、完整 argv、receipt、逐身份状态及 mandatory 集，不只 PASS/totals。W/RUNTIME_BINDING_VALIDATION.r4.final-003.json:2-18 是**writer 现存 loader PASS**；本 verifier 没有执行 loader。
- 新 predecessor replay W/red-predecessor-004：5 controls，4 FAIL/1 ERROR，exit=1；新 GREEN W/green-focused-006：5 PASS，exit=0。两份 PROCESS:2-40、45-195 保存精确 argv/cwd/PID/时钟、dependency、71 executor+test files 的 before/after bindings、raw/result receipt linkage；本次这些 source 与现存 r3/r4 对应字节全部一致，dependency digest 相符。Q/run_source_bound_group.py:58-78 在子进程前/后 hash，:100-124 保存 receipt，未回填旧历史。
- RED 内容有明确边界：AR007 是真实 validate 通过后缺必需图节点断言失败（NATIVE.log:17-22）；AR009 mirror ordering 与 log fsync 是行为断言失败（:25-43）；AR008 在真实观察终止后因返回缺 failure_dimensions 出现 KeyError（:8-14），不是 import/function 不存在，但它**不是已经执行完所有归类断言或复合原因测试的证明**。cleanup RED 在 :43 已失败，后续 failed-gate sealing 子断言未执行，不能写作同一次 RED 已重现 seal 缺失。
- integrated qualification 是进程内 unittest runner：Q/build_integration_qualification.py:32 在测试 discovery/execution 前 hash，但该进程及 durability/qualification_contract 已加载（:6-7）；:48-58 的 native_exit 是按 unittest result 生成的内部回执，不是独立父进程观测退出。可证实测试边界源绑定及保存结果；不把 source_binding_before_launch 字段夸大成 OS 启动前所有 imported bytes 独立测量。focused wrapper 的来源绑定则确实发生于 Popen 前。旧无来源 receipts 的历史运行字节仍 NOT_ESTABLISHED。

## native29、权限及完整性

bindings.py、execution.py、matrix.py、compile_inventory.py、packaging.py、lean_materialization.py、namespaces.py 相对 r3 字节未变；矩阵 SHA-256 `57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`。未要求改变 native29 命令/超时、H733、固定候选、8000/29 EXPECTED、BOOTJAR 独占副本、COMPILE freshness/completeness、frontend assets、Git→resources→JAR 或 Lean。未新增 attempt 3600 上限；未重开 Owner 已接受 ledger 捕获间限制；没有任意未来 plugin 证明要求。

输入 hash 在首次源码详细审阅前建立；authority/r3 报告最初读后建立 baseline；随后发现的外部 package/input 在详细验证前扩展 scoped baseline。前后摘要见 HASH_VERIFICATION.json。主动写入只有本 part-b 的报告、hash manifests、静态对账与 findings。不存在实现/测试执行或正式预算消耗。
