# r5 part-b 只读预审最终报告

## 结论
**B4-009-1 RESOLVED；AR007 RETAINED_RESOLVED；native29 保留。** 本 part-b 未发现上述限定范围内需要阻断的新增实现缺陷。此为 advisory preformal，**不是 final independent acceptance，不授权或启动 formal**。AR008 的完整裁决由对应分项汇总，本报告仅核验失败 supplement 相关因果传递。

新 isolated preparation 未运行，仍 NOT_ESTABLISHED；writer 现有 runtime-loader PASS 不能替代实际准备、正式门禁或独立接受。产品冻结，产品修复预算3/3、formal1/2未改变；8000/29仍只是 EXPECTED。

路径缩写：E=`implementation-r5/tooling/executor`；Q=`implementation-r5/tooling/qualification`；W=`writer-evidence-r5`。已读 Owner 原文、r5 packet、writer packet、r4 part-b report/findings、r5 final report/matrix/final-002 runtime binding/reconciliation，以及实际源码和现存测试日志。仅静态读取、AST/JSON/日志解析与 hash 对账；未导入被审模块，未执行 tests/probes/preparation/baseline/formal，未改产品、源码、共享 ledger/usage、Skill/Memory 或凭据。私有输入只做必要本地 hash/集合核验，不输出正文。

## AR009：既有成功 seal 后转失败的缺口关闭

- E/artifacts.py:76-84 先建立独占 sealed 副本并把 rows 放入 receipt，verify 后调用 after_copy；只有 after_copy 成功才写 PASS。runner.py:490-509 保留真实 sealed acceptance digest 与 Git→resources→JAR 后验检查，异常转 FAIL。
- E/artifacts.py:86-125 对初始失败仍走 PRIMARY_FAILURE_SEAL；若 sealed 已存在，不重建、不覆盖、不删除原目录。先 verify 原 manifest，再建立独立 `failure-supplement/` 独占目录。binding.json 绑定原 seal manifest 的规范 SHA256、run_id、producer_gate、candidate/tree、failure-details 原路径及 digest；000000 保存 failure-details 原字节。原 seal 保持可验证。
- E/artifacts.py:127-144 的补充校验复核原 seal、binding digest/身份、payload hash/长度及精确目录成员。不是仅在报告里宣称绑定。成功分支只能在完整校验后设置 failure_evidence_sealed=True，且 seal_failure 从不改为 PASS。
- E/runner.py:510-529 先持久保存 failure-details（error_type/reason/traceback/stage/dimensions/causal_errors/primary/secondary），再封存。supplement 发布失败只追加独立 failure_evidence_error/failure_supplement_error/secondary_failures，置 evidence_persistence_failure=True，保留原 reason、traceback 和 FAIL；最终 receipt 也写不出时 :530-538 把完整 runner_gate_receipt 挂到异常，不返回成功。driver.py:325-346 将失败 latch、合并既有原因并停止后续 gate，不执行成功 COMMAND_AFTER/GATE。
- 耐久路径：coverage.py:11-13 → durability.exclusive_bytes:59-74，O_EXCL/O_NOFOLLOW、文件 fsync、直接父 fsync；新目录链 ensure_directory:16-30、exclusive_directory:34-40 同步新目录及发布父目录。private/public/consume 的继承 durability 机制未被 supplement 绕开。本次没有模拟断电，不能把静态 fsync 机制描述成物理 crash 实测。
- Q/test_r5_remaining.py:425-494 通过实际 runner.run_gate→artifacts.finalize→after_copy 失败→seal_failure，真实建立原 sealed 和 supplement。独立测试分别断言原 seal 和绑定补充可验证，以及 supplement 持久化失败保留主原因/独立错误/FAIL。它们不是仅直接调用 reducer；但 native observe、parser、候选仓库检查在这些测试中被 fixture stub，coverage.put 也为 fixture dump。**它们证明真实 runner/artifact 文件封存分支，不等于完整真实产品 native gate、所有 fsync 故障点或 crash 实测。** 真 durability helper用于 seal/supplement，正式 coverage.put 的耐久性由源码及保留的相关控制支撑。
- 现存 RED red-predecessor-003/NATIVE.log:105-110 实际在 failure_evidence_sealed 断言失败；另一独立 supplement-error 控制 :16-22 因 r4 缺字段 KeyError。不能说后者已经在 r4 注入到不存在的 supplement writer。GREEN green-focused-005 两项均 PASS，qualification-003 同身份均 PASS。未用初始 seal 失败测试冒充已存在 sealed 的分支。

边界：若原 sealed 本身不完整或遭改变，verify 拒绝，不能声称产生了“绑定有效原成功 seal”的补充；异常仍是失败。存储完全失效时无法保证新的磁盘证据，但当前进程不会继续成功，原 cause 仍通过内存 receipt/异常链传递。这不是新的重试许可。

## AR007：当前真实有限依赖与运行绑定保持

- 独立 AST 重建 formal entry 的可达本地 Python 图，与绑定精确一致：**38 nodes /112 import edges**。实际 parser chain 仍为 runner.prepare→parser_tools.prepare；run_gate→freshness callback→parsers→vite_closure.py→vite_closure.mjs。dependency_contract.py:162-242 强制具体节点、边、helper 集、FRONTEND_BUILD helper edges、实际 graph；不靠 unresolved=[] 自声明放行。
- 实际读取固定 source root 下每包文件，核对 **8 packages /216 files** 与 package.json/hash/版本；全相符。acorn10、postcss55、postcss-value-parser9、parse5 33、entities58、nanoid26、picocolors7、source-map-js18。parse5→entities；postcss→nanoid/picocolors/source-map-js。
- 必需来源仍可用：`USER_HOME/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/sources/frontend/frontend/node_modules`。它是**显式运行前必需输入**，不能在隔离 prepare 前删除。binding loader→dependency_contract:239-252 重读，parser_tools:27-62 对缺 direct package/必需 dependency 拒绝；prepare:65-82 再逐文件 hash 校验并耐久复制到本 run cache。新 cache 实际物化未核验，因为未运行 preparation。
- candidate Vite 保持 prepared candidate frontend node_modules 的既有 runtime boundary。不提出任意未来 plugin 全源码证明，不扩大 parser package scope。
- runtime final-002 的 **111 source entries** 与当前字节、qualification before/after 精确相符；七类绑定输入 hash、四 dependency source receipts、90 candidate working-source hashes 与绑定 candidate-source hash、helper hashes 全相符。私有 origin hashes 与 eligible set 本地布尔核验通过。本次未重新执行 Git tree/patch 身份验证，不追认工作文件 hash 核验为 fresh Git attestation。
- 必经 coverage.qualification_inputs:122-181 校验 mandatory 固定集、每身份状态及 missing/unexpected/duplicate/invalid 等、完整 argv/cwd、source before/after/current、process/raw/result linkage，不只 totals/PASS。engineering_preflight:296 仍调用它。

## 资格完整性与来源限制

静态独立解析 qualification-003 原生日志和 RESULT/PROCESS：**152 expected /152 unique actual /152 PASS，FAIL/ERROR/SKIP/missing/unexpected/duplicate=0**；mandatory **67** 从 AST 固定集合取得并与资格列表精确相符。native identity/status 与 result 完全一致，process ids/status、raw/result digest、五项 qualification dependencies、before/after/current source 全相符。完整 argv、cwd、PID、时钟及布尔核验在 STATIC_VERIFICATION.json。

Focused GREEN green-focused-005：13 PASS，native_exit0/wrapper_exit0，72个 source before/after/current、dependency before/after/current、日志/result hash 全相符。

RED red-predecessor-003：13 controls，10 FAIL/2 ERROR/1 PASS，native_exit1/wrapper_exit0；before=after，dependency/log/result linkage 相符。**不能笼统说 RED 的72个 source 与当前全部相同**：test_conformance_corrections.py 和 test_r4_remaining.py 两个被一并纳入 manifest 的支持文件后来变更。被实际选中的 test_r5_remaining.py 和 r4 executor 字节均与 RED 绑定相符；其余两文件旧字节当前精确恢复 NOT_ESTABLISHED，本审查未回填。命令只选择 test_r5_remaining.R5FailureTransitionControls；该测试文件未导入上述两个支持测试文件。因此此差异是明确的历史 manifest 范围限制，不否定已绑定的 AR009 两项 RED 行为；不要把整个 RED source tree 写成“与 final 全相同”。

Integrated build_integration_qualification.py:7 在 source_before:32 之前已 import durability/qualification_contract；:48-58 的 native_exit 为 unittest 结果推导、PID 为自身。这是测试边界前/后来源记录及进程内结果回执，**不是独立父进程证明 OS 启动前所有 imported bytes**。Focused run_source_bound_group.py:58-78 则确实在 Popen 前/后 hash、记录真实子进程 exit/PID/墙钟/单调时钟。保持 r4 已说明的这个证明边界，不把 reused 历史结果改为 fresh。

## native29 与完整性

矩阵与 r4 字节完全相同，SHA256 `57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`。bindings.py、execution.py、matrix.py、compile_inventory.py、packaging.py、lean_materialization.py、namespaces.py、freshness.py、parser_tools.py、dependency_contract.py 均与 r4 字节相同。runner 的 sealed recheck、COMPILE freshness/completeness、BOOTJAR独占副本与Git→resources→JAR、frontend资产闭包、Lean和checkout/output隔离未删除；不改 native29 原命令/超时/接受契约、H733 或8000/29 EXPECTED。没有新增3600秒 attempt上限，也不重开 Owner 接受的 ledger 捕获间观察限制。

W/FINAL_MANIFEST.r5.sha256 静态读取核验 **1144 entries 全部相符**。最终runtime binding SHA256：`004aa36b9c2d7c1b92071d3b7ff02656af1cba34c4e8d67b47d3f38adafbd432`；dependency：`6b5ce0887bc522c4353b7bb85a292cdf6096f1fafa752821a4006b28f15e47d6`；qualification：`cd09689d3a9d21093a8b286baa89d82f53cf617ac795523cad66367aeee8ec54`。

## 交接

此范围支持 parent 继续条件核对，不是单凭本报告消耗第二次正式预算的结论。保留 fixed parser 来源，先由 parent 完成其授权范围内的隔离准备/其余审查条件，再决定唯一 candidate-formal-002。formal未运行；final independent acceptance/EP19 closure仍未建立。

产出仅本 part-b：早期报告、最终报告、前后输入hash、静态对账、findings、manifest。输入主范围前后hash稳定情况见 HASH_VERIFICATION.json；外部 package/私有输入只是本次单点核验，不冒充对其整个审查窗口的连续观察。静态核验脚本曾有一次缺少函数return的本地解析错误，已纠正后完成真实对账；未触发任何被审执行路径。
