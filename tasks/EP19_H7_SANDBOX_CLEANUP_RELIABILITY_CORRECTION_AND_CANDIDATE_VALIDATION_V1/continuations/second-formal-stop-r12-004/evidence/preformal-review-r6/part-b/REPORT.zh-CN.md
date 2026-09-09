# r6 part-b 只读预审报告

## 结论

**AR007 有限依赖闭合、AR009 原 seal/不可变 failure supplement 机制及 native29 契约保留；r5 的单一 marker 丢失和 Vite body+fsync 精确反例得到修正。但 AR008 的“所有复合持久化原因进入最终结果”仍有具体源码遗漏，不能无保留标为 CLOSED。**

本报告为 advisory preformal，不是 final independent acceptance、正式启动许可或产品门禁结论。未运行被审模块、测试、probe、preparation、baseline、formal；未创建正式 namespace、未消费正式预算。仅阅读、AST/JSON/native log 解析、SHA256 与禁用 optional locks/replace objects 的只读 Git 查询。私有信息只在本地做必要摘要/集合核验，不输出原文；未读取共享 ledger/usage 或凭据。只写本 part-b。

已读完整 Owner authorization、r6 repair packet、writer packet、两份 r5 完整报告、r6 final report/matrix、final-003 runtime binding 及实际 implementation-r6。路径：E=implementation-r6/tooling/executor；Q=implementation-r6/tooling/qualification；W=writer-evidence-r6。

## B6-008-1：复合 marker / supplement 持久化异常仍在序列化时丢叶子原因

**OPEN，阻断无保留 AR008 全闭合；这是静态源码可达分支，不冒充 reviewer fresh RED。**

1. E/runner.py:543-551 在最终 receipt 写失败时，把已有 gate 原因、native事实、receipt persistence secondary 放入 runner_gate_receipt，抛出异常。
2. E/external29_driver.py:373-375 对该异常调用实际 RunAdapter._latch_exception。E/executor_adapter.py:114-125 先置 failed=True，再经 _durable_exclusive→durability.exclusive_bytes 写失败 marker。
3. E/durability.py:106-122 已允许“write/file-fsync 主失败 + fd-close/parent-fsync 次失败”组合；:22-42 把各叶子原因放入 ExceptionGroup.exceptions / causal_errors，保留独立阶段。
4. **E/executor_adapter.py:50-56 捕获 marker_error 后，只保存 type(marker_error).__name__ 和 str(marker_error)，没有保存或展开 causal_errors / exceptions。** ExceptionGroup 的字符串只是组标题及子异常数量，不包含那些 write/fsync/close 叶子原因。局部异常被吞下，挂到原 gate异常的 failure_marker_errors 仅有这份摘要。
5. r6 driver:248-302 的合并现在确实不再丢掉此摘要，然而无法恢复已被 adapter 丢弃的叶子原因；sanitized log 同样只看已串行化的 rows。因此原 gate+最终 receipt失败+单一marker失败有保留，**不能提升为复合marker内全部错误已保留**。并不导致成功继续：失败 latch 与停止下一 gate 保持。
6. 同类直接持久化分支 E/runner.py:530-542 对 failure-details / supplement 发布异常仍仅 type+str，secondary_failures也仅存组字符串；若新 durability helper在 supplement写入发生 write/fsync+close/parent-fsync组合，叶子原因同样不进入最终 receipt。原始 gate 原因仍在，原 seal机制未退回，但“所有secondary persistence errors”不成立。

限定修正是让上述现有两处诊断传递保留已产生的 causal rows/嵌套错误，并保持失败状态；无需新产品门禁、任意plugin图、whole-host进程规则、历史回填或重开ledger观察限制。

资格解释：Q/test_r6_remaining.py:190-221 实际调用 execute_actual_graph，但 Runner抛手工 attached receipt，Adapter为替身，直接附加单一marker错误；它不执行真实 RunAdapter.fail→exclusive_bytes。r5 supplement控制仍为单个注入错误。因此9/9及161/161不覆盖上述复合叶子序列化遗漏。不要据此抹掉已经通过的精确控制，也不能用它们证明这个未覆盖分支。

## 已支持的精确闭合与保留

- **r5 A5-008-4 单一marker seam：CLOSED_SUPPORTED。** driver causal_rows不再遇attached receipt早返，merge_graph_exception总是并入marker rows，并保留已有secondary；uncertain标志和sanitized native记录在保存的GREEN/parent log可见。实际 runner最终receipt错误保留已有secondary，driver不会覆盖它们。
- **Vite helper body + stream fsync：CLOSED_SUPPORTED。** durability.exclusive_stream:145-165 独立尝试flush/file fsync/stream close/raw fd close/parent fsync；_composed保留ViteClosureFailure的helper维度和真实stream fsync次因。vite_closure.py:15-24不吞该ExceptionGroup；parsers.parse:19-29对已带failure_dimensions的异常原样传播；runner:340-382保留causal rows与dimensions。Q:123-138 使用真实exclusive_stream和真实文件fd，subprocess.run非零由替身返回，fsync为真实调用点注入；不是实际Node helper非零与故障fsync全链实测，也不是产品gate运行。
- **AR009原 seal / supplement：RETAINED_RESOLVED，受上面复合错误报告限制。** artifacts.py与r5字节相同，:86-143先verify原seal，再独占创建failure-supplement；绑定原manifest digest、run/gate/candidate/tree、details digest及精确成员。原seal不覆盖，补充不能把FAIL改PASS。runner:523-542保留原原因并把补充失败标为evidence failure。继承r5的真实原seal后after_copy失败与补充失败两个controls在最终资格仍PASS。文件/父目录/新嵌套发布继续经durability，未模拟物理断电。

## AR007 有限依赖与native29

- 静态独立重建formal入口实际本地import graph：**38 nodes /112 edges**，与dependency scope完全一致。required node hashes、四source receipts、10 helper绑定、90候选工作源hash全部相符；候选工作源同时等于绑定candidate-source hash。
- 实际固定parser源仍在：`USER_HOME/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/sources/frontend/frontend/node_modules`。**8 packages /216 files**逐文件/版本/package.json相符。parse5→entities；postcss→nanoid/picocolors/source-map-js；direct acorn/postcss/postcss-value-parser/parse5保持。不得在隔离prepare前删掉这些必需来源。
- dependency_contract.py:162-252验证具体调用边、实际import图、FRONTEND_BUILD helper及实际package graph；parser_tools.prepare:65-82在独立run cache复制并再核hash。candidate Vite仍是prepared candidate frontend node_modules边界；没有引入任意未来plugin证明。
- applicability/private map/inventory绑定与instruction origin、eligible集合本地核验通过，仅布尔汇总。这里未重新推导Owner选择规则，也不把新声明文件当来源证明。
- native29 matrix与全部candidate-inputs-v3文件均同r5字节；29 command/dependency rows精确相同。bindings/execution/matrix/packaging/compile_inventory/lean_materialization/freshness/namespaces/parser_tools/dependency_contract/artifacts及Vite helpers等保留。COMPILE freshness/completeness、BOOTJAR独占副本、Git static→resources→JAR、frontend资产、H733、Lean、checkout/output和wrapper/init规则未被本轮撤销。
- 没有新3600秒attempt上限；Owner接受的ledger捕获之间overwrite-restore/truncate-regrow限制保持，不扩展到其他protected对象。

## 资格、来源、父进程回执与runtime binding

独立native状态解析（focused日志中sanitized stderr插入导致status分行，已按pending identity解析），并与RESULT/PROCESS精确对账：

| 保存运行 | native unique | 状态 | native/wrapper exit | source before/after |
|---|---:|---|---|---|
| red-predecessor-004 | 9 | 8 FAIL /1 ERROR | 1/0 | 73相等 |
| green-focused-006 | 9 | 9 PASS | 0/0 | 74相等且全为当前字节 |
| qualification-005/integrated | 161 | 161 PASS | 0/0 | 113相等且全为当前字节 |

161 expected由当前绑定测试源码AST重建，与声明expected完全一致；76 mandatory从qualification_contract固定集合AST取得，精确一致且无missing。native身份/status/result/process/raw和result digest精确相符；无missing/unexpected/duplicate/FAIL/ERROR/SKIP。qualification五dependency hash相符。旧reused71/158等保持各自范围，不称fresh产品运行。

**RED来源限制：** 同一选中测试体digest为`52b8f8a633d5529c8770c03ffaa083b5cd704051db4f43c6a27207a933427591`；RED实际r5 executor全部当前保留字节相符。但73条context中4条当前不相符：build_dependency_evidence.py、run_source_bound_group.py、test_conformance_corrections.py、test_r4_remaining.py。其中build_dependency_evidence.py及两个support测试文件并非本次选中的测试执行体；**run_source_bound_group.py却是实际parent producer，不能归为未执行support。** RED producer旧hash `080ae009b0390066d6614f985022c3d6b01c0d53131fdeb20835865cae5e6226`，不同于最终wrapper `e5cb0fc5c74bfd73c0eb711c4ccc24b678240c0d4824c845bef8a57cd6f8331a`，也不同于保存r5 wrapper。当前旧wrapper精确字节恢复NOT_ESTABLISHED；不回填，不声称最终wrapper已运行RED。该限制不否定已绑定选中测试体/被测r5源码及原生失败日志。

**父进程回执界限：** integrated自写PROCESS只是内部结果，开始hash前已import durability/qualification_contract。另有Q/run_integrated_parent.py实质Popen前后113-source manifest、communicate返回码、argv/cwd、wall/monotonic。W/qualification-005/PARENT_PROCESS.json的0/0与21.353877741s，source/current和native/result digest相符；loader-parent亦相符，0/0、1.012990898s。**这些是writer-owned parent subprocess回执，不是Hermes parent独立签发或OS独立attestation。字段pid=9来自child.pid，是namespace-local child PID，不是host PID或wrapper父PID。** 没有外部来源可把它升级为独立证明；也不新增一个“必须独立OS attestation才可审查”的门禁。

最终binding=`RUNTIME_BINDING.candidate-formal-002.r6.final-003.json`，SHA256=`000519c86183cccb2c326d27f023435fa58745f7a7076eef873be83a74538283`。**113 source entries**全当前相符，和qualification / parent pre/post source精确相等，七类输入hash及reviewed delta相符。已有runtime-loader-004真实脚本调用binding_contract、coverage qualification、dependency、runtime files及只读Git，保存PASS；本review未重跑loader。额外只读Git确认HEAD=`a29864343ed4f630b052c20d86c23b240f13cfd0`、tree=`fd37409d0274662abbe86f69e3d963c05b379696`、immediate parent精确、patch=`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`、tracked status clean。

## 报告纠正及交接

**B6-DOC-1：IMPLEMENTATION_DELTA_RECORD.r6.final.json.changed_runtime_files漏列preservation.py。** 实际改变9个runtime文件；完整bound patch与source manifests已包含此文件，故为报告索引遗漏，不是未绑定源码，也不要求重跑产品gate。

W/FINAL_MANIFEST.r6.sha256的208 entries全部hash相符。本review334个已捕获输入前后不变；外部parser源与必要private来源只做单点核验，不冒充整个窗口连续保护。

产品修复3/3、formal1/2保持委派状态；本review未消费尝试。baseline/preflight/formal NOT_RUN，29 REQUIRED/0 PASS/0产品门禁FAIL/29 NOT_RUN；8000/29只是EXPECTED。isolated preparation、正式结果、final independent acceptance和EP19关闭仍未建立。

Parent应将B6-008-1作为已有范围内具体残余与part-a合并处置，不接受writer“仅剩formal”的无保留表述。AR007/009原机制、精确已修复seam及真实161 PASS无需被抹去；修复导致源码改变后按Owner已有affected资格/最终绑定要求更新，不把旧runtime结果追认为新实现运行。

产出：EARLY_REPORT.md、EARLY_FINDINGS.md、INPUT_HASHES.before/after.json、STATIC_VERIFICATION.json、HASH_VERIFICATION.json、FINDINGS.json、本报告和MANIFEST.sha256。工具输出曾截断，已分项补读；未发生被审执行或任何共享修改。
