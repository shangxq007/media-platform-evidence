# r7 Part B：AR008 因果回执、资格来源与 AR007/009 只读预审

## 结论

**AR008 无保留 CLOSED 不获支持：三个具体残余仍 OPEN。** r6 的摘要化丢叶子已在主要 preservation/boundary/adapter/runner 点修复；真实保存资格支持这些精确修正，但尚未证明所有嵌套身份/主次关系及最终传递。AR007 有限实际依赖和 AR009 原持久化、不可变 supplement 机制保持支持。

本报告仅 advisory preformal，不是 final independent acceptance 或正式启动许可。已全文读取 Owner authorization、r7 packet、writer packet、两份 r6 final review，以及 r7 final report/matrix/reconciliation/delta/provenance。未导入/运行被审模块，未执行测试、probe、preparation、baseline、formal、进程检查或信号操作；无共享 ledger/usage/凭据读取，无产品修改。仅静态源码、AST/JSON/native 日志及字节 hash；只写本 part-b。下述 OPEN 都是静态可达性，不冒充 fresh RED。

路径均相对 J：E=implementation-r7/tooling/executor，Q=implementation-r7/tooling/qualification，W=writer-evidence-r7。

## B7-008-1 — boundary 已拒绝 + failure marker 失败仍先丢原始 decision

**OPEN。** E/executor_adapter.py:108-115 仅把 engine.check 包在 try 内；当 check 正常返回 REJECT，:116-121 先 `self.fail(phase,result)`，之后才创建 BoundaryReject 并附 boundary_decision_receipt/causal_errors。fail :124-135 在真正持久化前已经 failed=True。若该 marker 的 write/fsync/close 发生异常，:118-120 永远不执行，原 REJECT 的 capture/evaluation 原因只在局部 result 中，抛出的只是 marker ExceptionGroup。

真实 driver :349-351 调这条 boundary；:364-366 因 adapter.failed 已真不再 _latch_exception。此时局部 gate result=None，merge_graph_exception :260-277 只能接到 marker 异常。原 boundary primary 与 marker secondary 关联从最终 gate result / formal RESULTS 路径丢失。失败依然停止，**不是成功绕过**；即使单独 boundary evidence 已保存，最终 receipt 不再绑定/保留该原因。

Q/test_r7_remaining.py:170-215 覆盖 boundary failure 且 marker 成功；:217-252 的 marker 组合控制又在 :238 mock 掉 driver.boundary，改由 Runner 抛 RuntimeError 进入 _latch_exception。因此两个 PASS 不覆盖它们组合后的真实分支。限定修正应在调用 fail 前建立并保留原 decision，marker 失败作为关联 secondary；不需要新产品门禁。

## B7-008-2 — 新 causal rows 仍不是 lossless 嵌套身份/主次拓扑

**OPEN。** E/causal.py:13-19 使用 setdefault 保留旧 role/stage/association；:27-30 一旦有 causal_errors 就直接采用原平铺 rows，不记录这次封装的外层关系。:97-103 对 primary/每个 failures 调 rows 后再 unique。:62-73 的去重键明确忽略 leaf_index，且相同 stage/role/reason/association 的不同异常没有独立事件标识。

两个当前实际调用例，不是未来 plugin 要求：

1. E/preservation.py:49-53 逐个祖先 fd close 失败都用 ANCESTOR_FD_CLOSE，经 :19-22 同一 secondary-for-primary。两个独立 fd 的相同 OSError 原因/类型变成相同 rows，被 unique 合一；无法识别两个叶子。Q/r7:183-185 的真实 close 后抛相同原因恰可产生这一类重复，断言 :211-213 只查 reason 存在，不查个数或身份。
2. E/durability.py:28-37 directory fsync + close 组合，作为 :96 publishing-parent-fsync 的失败再嵌套进 exclusive_bytes :97。内层 fsync row 是 role=primary / association=primary-operation。外层 causal.raise_composed :100-102 本应把它标为相对 file-write primary 的 publishing-parent secondary，但 rows 的 existing 分支保留内层字段并不保存外层边。因此 file write 与 parent-directory fsync 可以在最终 marker rows 中都呈 primary-operation，失去哪个 primary 对应哪个 secondary。内存 ExceptionGroup.exceptions 保有结构，但 receipt 序列化只有扁平 rows，不能用 traceback 或内存组替代落盘关联。

原始嵌套叶子 **类型与原因已改善**（causal.rows:31-39 递归未知 group；preservation.error:65-68、capture_files:136-143；boundary:149-153,218,229-238），但“所有叶子及 grouping/primary-secondary identity”仍过度宣称。需稳定操作/组/叶子身份与显式父边，且不要把独立重复事件当重复 transport 去重。

## B7-008-3 — 实际 preflight transport 仍退化为 str + 通用异常

**OPEN。** E/external29_driver.py:316-332 的必经 engineering_preflight 调 latching_strict_check 与真实 boundary。:327 捕获后仅 problems.append(str(exc))，v3=None；:328-331 保存的 preflight.json 无 causal rows；:332 又抛一个全新 RuntimeError，未附原 receipt/causal_errors。外层 formal :425-433 对这个新错误构造 FORMAL_FAILURE，causal_rows 无法恢复已被丢弃的实际 capture/cleanup/marker 叶子。已有 marker 可能保存更丰富原始诊断，但 preflight→最终 failure 传递没有关联它。

这正是 r7 packet:6 要求审计“finite actual serialization sites”的现存位置，不要求新增观察窗口或任意扩展。应保留原 structured error/receipt 并传播到 preflight/final，而不是从组摘要恢复原因。

## 精确支持的修正与测试边界

- r6 B6-008-1 marker 原组叶子摘要损失：E/adapter:45-63 对 _latch_exception 路径改为 causal.rows 并附 primary_causal_errors；driver:249-293 合并原 receipt 和 marker，不再早退。这条精确 seam 得到 Q/r7:217-252 支持，但不覆盖 B7-008-1。
- r6 supplement 序列化：E/runner:507-527 保留原 gate 事实、supplement 叶子；:528-536 最终 receipt 写失败附 runner_gate_receipt。Q/test_r7_runner_supplement.py:14-68 实际调用 runner.run_gate/原 seal 后补充路径；真实 workload observe 是替身 (:25-34,58)，directory failure 是 :43-49 主动用 _composed 构造，不是实际三个底层 syscall 同时失败。它验证真实 runner 序列化，不是完整 native 产品执行。
- Q/r7 的 saved-receipt 控制确实读取 BOOKKEEPING_FAILURE.json (:208-213) 并看 driver result；不是仅 flattened helper。但 :201 全局 fstat MemoryError 最先发生在 preservation.parent_fd:40 的祖先检查，尚未达到 Collector.read 的目标文件 read。其原因存在断言不能升级为所有嵌套叶子身份/类型/拓扑的证明，也没有读取最终 runtime/RESULTS.json。临时 fixture 会清理；本 reviewer 审查保存源码/成功断言与 native PASS，没有伪造一份保留下来的成功 fixture receipt。
- AR009 retained：E/artifacts.py:86-143 原 seal 先 verify，再独占 failure-supplement，绑定原 seal digest、candidate/tree/run/gate/details；原 seal 不覆盖。durability.py:28-140 保留文件、父目录和嵌套目录发布及独立 release 尝试。失败 latch 与 consume 状态不复活。此项不是物理断电实测，也不豁免上述 AR008 诊断残余。

## 保存执行与来源独立静态核验

详见 STATIC_CHECKS.json，计数来自解析，不采用 writer 总数代替验证。

| 保存运行 | native unique/status | native/wrapper | snapshot entries |
|---|---|---|---|
| red-predecessor-001 | 5 FAIL | 1/0 | 75 |
| green-final-001 | 5 PASS | 0/0 | 76 |
| red-runner-supplement-001 | 13 PASS + 1 FAIL | 1/0 | 77 |
| green-runner-supplement-001 | 14 PASS | 0/0 | 77 |
| qualification-003 | 167 PASS | 0/0 | 116 |
| runtime-loader-001 | 保存 VALIDATION PASS | 0/0 | 118（116 tooling + validator + binding） |

各 focused/integrated native id/status 与 RESULT projection、PROCESS statuses 精确一致；raw log/result hashes 相符。167 expected 从测试文件本地定义的方法 AST 重建，精确等于 qualification expected；82 mandatory 从 qualification_contract 固定集合 AST 提取且全部真实执行。无重复/缺失/多余/FAIL/ERROR/SKIP。五 qualification dependency hashes 全相符。

每个上述运行的 before/after SOURCE_SNAPSHOT 所指副本逐个 hash，副本 hash=source_sha256=执行绑定；pre/post 相等。Q/run_source_bound_group.py:62-77,102-130 记录实际 wrapper 所在 qualification、选中 test、executor；Q/run_integrated_parent.py:36-64 对 final tooling 做 parent prelaunch/postreturn。实际 RED 的 r7 executor 路径当时仍是 predecessor 字节，后续已变化但旧副本保留，不以当前字节取代。两组 RED/GREEN 选中 test 完全同字节；supplement focused 的旧测试 hash 与当前不同，当前增加 load_tests:71-73 排除 imported helper，因此 focused14并不冒充 integrated 中14新增身份，最终整合只新增该自身 control。

green-final 后 binding_contract/qualification_contract/run_integrated_parent 有后续变化；runner focused 后 binding_contract/qualification_contract/supplement test 有后续变化。各旧 source copies 正确保留。qualification-003 的全部116当前字节等于执行 before/after、parent copies、final runtime source_binding；loader 118副本同当前。这里是 writer-owned parent subprocess 回执，PID 是 namespace-local child PID，不是 host PID、Hermes 独立 OS attestation，也不将其升级 final acceptance。历史 r6 RED wrapper 精确 producer **NOT_ESTABLISHED_NO_BACKFILL** 保留（W/PROVENANCE_DISPOSITION:10-12）；不回填。

## AR007 有限图与 final runtime binding

binding SHA256=`62b9e4d91ba7ac238269161180f5c6f29950b27dc6eebb887a5e6a48ce741b31`。qualification/dependency/source map 相符，exact run_id=candidate-formal-002。实际 loader source W/validate_runtime_binding_r7.py:17-37 调 binding_contract、coverage.qualification_inputs、dependency_contract、required runtime files 及只读 Git；保存 VALIDATION PASS 与 parent log/validator/binding/validation digests 全相符。**本 reviewer 未重跑 loader/Git/candidate preparation。** 固定 candidate/tree/patch 按 Owner和已保存 loader 保持，不称 fresh Git 重物化。

E/driver:36-41,316-320 的实际必经链，E/binding_contract:30-65 严格 source/输入/依赖/schema/exact run；coverage:121-181 强制 mandatory、native/result/process/source reconciliation；qualification_contract:90-128 非 PASS、缺失/多余/重复拒绝，未改成只比较 PASS/total。

静态从 actual entry 独立重建本地 import graph：**39 nodes /125 edges**，与 dependency 完全相等（包括新增 causal.py）；8 parser packages /216 files 全当前 hash 相符，四 source receipt hashes 相符。E/dependency_contract:162-252 保留真实 source nodes/import graph、helper edges、parser graph；candidate Vite仍限于 prepared candidate frontend node_modules。未要求任意未来 plugin 图。没有重新推导 Owner instruction selection，也不输出 private 正文或把 hash检查当全窗口连续观察。

## Delta、历史与交付

r6→r7 非 pycache 文件 byte diff独立生成 **22 changed/added files**，精确等于 delta record，含 preservation.py；final.patch 与 additive final-002.patch 字节相同。原 manifest 2856项、final-002 manifest 2860项逐文件 hash全相符。r6错误 delta仅作为保留历史，不追改。

产品修复3/3、formal1/2按委派保持，未消费第二次；formal baseline/preflight/gates NOT_RUN，8000/29仅 EXPECTED。本分项不撤回 AR007/009既有范围，不重开 ledger捕获间 overwrite-restore/truncate-regrow限制，不扩展 Memory例外，不新增3600秒attempt上限。

Parent应合并本三个具体残余与 Part A，不采纳 writer“只剩formal”的无保留交接。只需已授权范围内受影响修正/资格/最终绑定，不能把当前167 PASS抹掉，也不能用它证明未覆盖分支。

产出仅本目录 EARLY_REPORT.md、EARLY_FINDINGS.md、STATIC_CHECKS.json、本报告与 MANIFEST.sha256。读取曾输出截断，已补读；静态核验脚本先后遇 read_file 返回结构、loader log字段差异、AST import索引错误，均已改用实际字段/节点选择完成核验；未执行候选或触碰共享状态。
