# r9 Part B：资格、运行绑定、来源与最终失败序列化只读预审

## 结论

**173 unique / 88 mandatory 的真实保存资格、固定运行绑定及有限依赖图核对通过；精确 preflight.json 修正获得支持。但相邻 runtime/FINAL_FAILURE.json 持久化失败仍可能替换原 structured cause（B9-B-1 OPEN），不支持整体无保留 CLOSED 或据此启动正式执行。**

本报告是 advisory preformal，不是 independent final acceptance、正式启动许可或产品门禁结果。AR007、AR009/010 既有组件处置 retained；AR009 底层 durable publisher 未回归，不等于全部上层异常集成闭合。AR005/006 保持此前处置；未新增契约、任意深度保证、观察窗口、3600 秒 attempt 限额或产品门禁，未重开 Owner 已接受 ledger 捕获间观察限制。

路径相对 J。E=implementation-r9/tooling/executor，Q=implementation-r9/tooling/qualification，W=writer-evidence-r9。

## 审查边界

读取 Owner authorization 全文、WRITER_PACKET、r9 packet、r8 两分项完整报告、r9 report/machine/matrix/reconciliation/provenance/binding/manifest/handoff、实际源码与保存 native/process/result/source copies。只执行静态 AST/JSON/native 解析及 SHA-256；未 import 被审模块、运行测试、loader、probe、preparation、baseline、formal 或产品命令。私有 r9 map/inventory 只校验绑定摘要，不输出正文；没有读取共享 ledger/usage、凭据或变更共享状态。唯一写入本 part-b。

implementation-r9 的119文件前后 hash 全相等。产品3/3、正式1/2按委派与保存证据保持；本次未消费预算。正式29门禁仍29 NOT_RUN，8000/29仅 EXPECTED，EP19未关闭。

## 一、精确 native 身份和必经 consumer

独立从全部 test_*.py 的 class/test 定义静态重建173身份，逐字等于 QUALIFICATION.expected_controls；从 qualification_contract.py AST提取88 mandatory，逐字等于保存清单，r8原85全部保留，增加三条：

- test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_actual_preflight_write_failure_is_secondary_to_original_disposition
- test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_final_failure_sink_fault_retains_available_original_and_secondaries
- test_r9_preflight_persistence.R9ActualPreflightPersistenceControls.test_original_preflight_failure_alone_has_real_saved_final_readback

| 保存运行 | native identity/status | native / wrapper | 每侧来源副本 |
|---|---|---|---|
| red-r8-002 | 3 unique：1 PASS、2 FAIL | 1 / 0 | 79 |
| green-r9-final-002 | 3 unique PASS | 0 / 0 | 79 |
| qualification-001/integrated | 173 unique PASS | 0 / 0 | parent118 |
| runtime-loader-final-002 | VALIDATION PASS | 0 / 0 | 120 |

native行的精确身份/顺序/status与RESULT.controls相同，process.control_statuses相同；native/result hash相同。集成expected/actual集合完全相等，无duplicate/missing/unexpected/failed/errored/skipped。五 qualification dependencies 全部hash匹配。完整身份列表及检查结果见STATIC_CHECKS.json，不按writer摘要盲填总数。

Q/build_integration_qualification.py:32-37在执行前绑定源、发现expected并强制mandatory；E/coverage.py:121-181在实际qualification consumer检验source/dependencies、native/process/result、精确mandatory、身份accounting、argv/cwd、source稳定与原生日志身份状态。E/qualification_contract.py:96-134拒绝重复预期/实际、缺少/额外、非法status与非PASS，不是只比较173/PASS。

## 二、不可变 predecessor 与实际来源证明

79/79、118/118、120/120 before/after每份副本的实际hash均等于snapshot_sha256=source_sha256，两个时点映射相同。RED中的r8 executor副本与当前封存r8字节匹配；RED使用r9测试/包装器，不能把整个RED来源称为r8。RED时的build_dependency_evidence.py、run_integrated_parent.py、run_source_bound_group.py三个r9文件与最终版本不同，原副本原样保留；不是最终wrapper运行过历史RED。

相同测试体SHA-256：`e95b6b5048c781dd8894f59712db150f12272b3b7472aeb0e34fe3ce1dc22941`。RED/GREEN/集成各before/after测试副本全部相等。red-r8-001只是保留的断言迭代，不冒充authoritative RED。red-r8-002第一失败在test:160/131读到空preflight_receipt；第二在:214原native leaf不在最终可用rows中，确为目标缺陷，不是setup失败。

最终focused、集成和loader副本均与当前对应来源一致；qualification/source_binding、before_launch、after_execution、parent/child maps、runtime118 tooling map完全一致。parent argv与子receipt所示执行文件/输出/fixture相符，pid=9、namespace pid:[4026534934]互相对应；这些是**writer-owned subprocess观察和namespace PID，不是Hermes reviewer独立OS attestation**。

快照是原路径在执行前后保存的字节副本；argv仍从原implementation路径执行，不是“从sources.before目录执行”。本审查不将两个端点hash升级为独立证明运行期间不存在瞬时改写。

loader保存120份=118 tooling+validator+binding；validator和binding与当前hash相同，VALIDATION/native/process hashes及pid/namespace关联相同。`run_loader_parent_r9.py`自身不在这120份快照中，虽然当前文件受完整manifest覆盖，不能追认它执行前自身源码已封存。本次没有fresh loader。历史缺失来源仍`NOT_ESTABLISHED_NO_BACKFILL`，不回填。

r8→r9实际byte delta10项，逐条before/after/status/path等于delta record；predecessor118、successor119（118 tooling+.source）。patch SHA-256：`b1629521879afd4efe621a805ed841a43d709a707011e447821b709899ca053f`。r8 writer manifest1879条、Part A6条、Part B5条全匹配，保留历史不可变性。

## 三、AR007：固定身份、有限实际图与运行边界

runtime binding SHA-256：`3c06598cce6771acfb7451ac235bd5ac265fa76eec843726cb674f2861b9a4b2`。
qualification SHA-256：`10086042d1849b6060f6deb8cfa37a7683b8f35f095b19241dc26aa19f4cfaae`。
dependency SHA-256：`fed1d09880cadb9b909bec60a006f1c8d93bd4394693ac06fe03e2882ce417e9`。

EXECUTOR_IDENTITY按writer定义是runtime binding的字节hash，不另造source aggregate身份。

固定candidate `a29864343ed4f630b052c20d86c23b240f13cfd0`、tree `fd37409d0274662abbe86f69e3d963c05b379696`、patch `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`、immediate parent `689ab9456461a8d19a72d059f5157092efc43aff`、canonical base `86d6aef94fd5e58da552e97c11473cff6eca734e`与Owner/绑定及binding_contract硬约束一致。唯一run_id为candidate-formal-002；binding仅不代表namespace或正式结果。

独立AST遍历实际external29_driver入口的本地imports，得到39 nodes/125 edges，节点hash与边逐条等于dependency图。8 parser packages/216 files当前hash全部匹配；四source receipts及owner/applicability/private摘要等绑定全部匹配。固定29条command/dependency逐项相等，matrix与r8字节不变，因此原生命令/timeout规则未在本轮改变。90个candidate consumer当前working bytes与保存candidate_source hashes相同，external helper hashes全匹配。未重新运行Git/产品命令，candidate Git identity运行核对仍是已保存loader证据，不冒称fresh Git attestation。

有限图不覆盖任意未来reader；当前unknown actual dependencies仍拒绝。E/dependency_contract.py:171-220增加的是实际preflight/final helper检查，未把缺失reader默认为不存在。runtime Vite仍限未来prepared candidate frontend node_modules，parser graph是另一个固定来源范围，不能称本次已经验证了正式容器、endpoint或prepared runtime。私有eligible来源由既有applicability/source关系消费；本审查仅摘要绑定核对，不重新进行Skill选择。

## 四、精确preflight修正与retained因果/持久化路径

E/external29_driver.py:316-339先构造带preflight_receipt与原causal_errors的EngineeringPreflightBlocked，再:361-374执行实际preflight.json写。失败时原failure为primary、实际persistence异常为secondary，附persisted=False；成功时persisted=True。E/formal_failure_document:384-398带原disposition与causal rows，formal:511-518使用该函数并在FORMAL_FAILURE.json失败时收集secondary；:532-537调用同一个formal_persistence_failure，内存异常保留原/次/cleanup rows。

Q/test_r9_preflight_persistence.py:103-118对真实preflight.json fd的os.write注入，真实engineering_preflight、latching与durability transport未mock掉。成功final sink :149-152、170-177走真实exclusive write/fsync/close后JSON读回；final sink失败:187-201对实际fd注入且断言空文件不等于durable receipt。正常preflight失败及复合写失败的精确修正获支持。

但测试临时目录由:30-32清理。本审查读的是源断言+native PASS，不是仍存在的FORMAL_FAILURE.fixture.json，也没有运行正式FORMAL_FAILURE。断言重点是reason、disposition、occurrence唯一；不能把它描述为逐项assert所有error_type/context父边的独立完整测试。

E/causal.py与r8字节相同：unique合并键为occurrence_id，不按message/stage去重；相同文本独立异常不会合并。durability.py、artifacts.py、executor_adapter.py、capture.py、observe.py、native_observe.py、runner.py及coverage.py与r8相同，AR009/010已接受组件处置retained。32 context cap仍是有限实际链范围，不宣称任意深度lossless。

## 五、剩余问题与readiness限制

### B9-B-1 OPEN：相邻FINAL_FAILURE.json写失败仍替换原structured cause

**静态可达，未运行fresh RED。** E/external29_driver.py:490-500捕获FINAL/COVERAGE/SEAL实际异常后，:497无保护地runner.put(runtime/FINAL_FAILURE.json,原诊断)。如果该真实写点抛OSError或嵌套write/fsync/close组合，:508-509外层except收到写异常，primary_error被设置为新写异常。

:511 formal_failure_document → :392 causal_rows → causal.receipt_rows/rows只读显式rows/group/receipt，不遍历Python隐式__context__，也不读取前一个局部FINAL异常或旧marker。因此FORMAL_FAILURE.json的structured causal_errors缺原FINAL拒绝occurrence/context，写异常变成primary。:532 fallback也使用这个被替换后的primary_error。Python traceback字符串可能保留原文本，但不是保留原结构化cause/disposition；已有marker也未在该serializer中重新关联。

失败仍退出，不是接受绕过。本点是r9 packet明确要求审计的有限相邻错误路径，不是新增窗口/任意深度要求。应在既有授权外部修正内保留原FINAL异常与诊断、组合该实际写失败，再经真实final sink/fallback传递；本review不修改代码或执行测试。此问题足以阻止整体无保留CLOSED。

### B9-B-2：failed final sink的实际native输出证明未建立

Q/test:202-217调用builder得到内存exception并检查属性，未raise进真实formal catch，也未捕获/读回其实际stderr。生产:532-537确实raise该helper返回对象，因此支持“可用structured exception保留”，但main:661-666没有把formal_failure_causes或preflight_receipt显式序列化为native JSON。正常Python exception-group traceback不会自动输出这些自定义属性；该分支不能据当前测试声称已经把全部occurrence/context落入native diagnostic。preflight复合分支中的包装failure在:316-339尚未通过raise-from绑定original，不能靠成功写分支:374的链代替它。

这是**当前证据/输出范围限制**，不把不存在的durable receipt说成已保存，也不新增任意深度要求。parent合并时应明确区分“helper中可用异常”与“实际最终native输出”。

### parent剩余动作（本分项不执行）

1. 合并Part A和上述OPEN，完成获授权的相邻错误写点修正及受影响真实qualification/source/binding更新；不要用173 PASS覆盖未测分支。
2. 对最终封存版本形成implementation review，保持final independent acceptance=PENDING/REQUIRED。现handoff两个ABS_PARENT_*变量仍须是真实parent disposition/review，不是已生成回执。
3. 按既有顺序完成instruction加载、独占prepare、identity/endpoints/revalidate、preparation disposition、隔离与当前任务owned资源条件。这里没有fresh准备/endpoint或baseline证明。
4. 条件满足才由parent消费唯一candidate-formal-002；consume在baseline前，失败不刷新/改名重试，不超出1次剩余正式预算。
5. 真实29-gate结果、保全、独立最终评审及原权威关闭条件仍待完成；evidence发布与工程/独立接受分开。不能据本报告称EP19关闭或产品发布。

## 六、完整性与产出

W/FINAL_MANIFEST.r9.sha256的1406条全匹配，manifest自身SHA-256：`56a9c714b0412b7d9f671d7ded3418bbe192967355604edcd0073ce71155068c`。

本目录包含早期报告、早期发现、SOURCE_HASHES.before/after、STATIC_CHECKS.json、本报告及MANIFEST.sha256。全部实现119文件审前审后不变。工具批量输出曾截断，相关r8报告缺段与实际driver/causal/qualification消费者已分段补读；未将截断当作证据缺失或运行新探针。只读审查没有其他实现、历史或共享状态修改。
