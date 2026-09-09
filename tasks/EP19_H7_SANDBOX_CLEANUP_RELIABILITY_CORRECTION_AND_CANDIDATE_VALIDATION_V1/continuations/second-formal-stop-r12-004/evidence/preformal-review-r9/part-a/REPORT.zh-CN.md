# r9 Part A：preflight 写失败与最终 sink transport 只读预审

## 结论

**B7-008-3 / B8-B-1：SUPPORTED_CLOSED_EXACT_FINITE_SCOPE。** r8 指出的实际 preflight.json 写失败替换原原因与 disposition，当前 r9 已按实际调用链修正；在本次限定链未发现新的可达阻断缺陷。B7-008-1/2 保留既有 scoped closure，AR001..007/009/010 保留原处置，不把本分项扩为全域重新接受。

仅 advisory preformal，**不是 final independent acceptance、产品门禁结果或正式启动许可**。没有运行任何测试/probe/loader/preparation/baseline/formal，没有导入被审代码；未读取凭据、共享 bookkeeping 原文或 runtime binding 的私有输入。仅在 J/preformal-review-r9/part-a 写入。产品3/3、formal1/2按 Owner/既有证据保留，本次未消费预算；29 gates 未由本审查执行，8000/29仅 EXPECTED。未改变批准契约、观察限制或增加任意深度要求。

已读 OWNER_AUTHORIZATION.verbatim.txt 全文、REPAIR_R9_PACKET.md、WRITER_PACKET.md、r8 两份最终报告、r9 writer final report/matrix/qualification reconciliation/provenance，以及下述实际源码、原生日志、process/result 与快照。路径相对 J：E=implementation-r9/tooling/executor，Q=implementation-r9/tooling/qualification，W=writer-evidence-r9。

## 1. 原失败先附着，真实 preflight 写失败后复合

- E/external29_driver.py:353-360 在捕获 original 后形成 ENGINEERING_PREFLIGHT_BLOCKED、IRREVERSIBLY_LATCHED_REJECT 与 causal.receipt_rows(original)。:361 先调用 :316-323 构造带 preflight_receipt、causal_errors 和 persisted=False 的 EngineeringPreflightBlocked，然后 :363 才调用可失败的 runner.put。
- :364-366 捕获**该实际写点**异常，:326-339 以原 reject 为 primary、真实 persistence 为 PREFLIGHT_RECEIPT_PERSISTENCE secondary 执行 causal.raise_composed，并在组合上保留完整 preflight_receipt、persisted=False。不是依赖 Python 隐式 __context__ 或把原原因降为一条 str。
- E/runner.py:27 → E/coverage.py:11-13 → E/durability.py:81-97 是生产 runner.put 链；durability 独占创建、实际 os.write、file fsync、close、parent fsync，嵌套 fsync/close 经 :28-37 和 causal composition 保留。Q fixture Runner.put 使用 driver.durable（:43-46），同样进入 exclusive_bytes；这是同一底层真实持久化实现，不声称测试导入了完整正式 runner/binding 环境。
- E/causal.py:79-100 保存 leaf error_type/occurrence，:152-178 仅按 occurrence_id 合并；:196-220 保留 primary/secondary contexts 与共同 composition。causal.py、durability.py、executor_adapter.py、boundary.py 与 r8 字节相同，r8 已限定接受的 nested write/fsync/close 拓扑没有被替换成 message 去重。本次有限 preflight→formal transport 不建立任意深度 lossless 保证，32 contexts 限制保持。
- 已失败 adapter 不再进入成功路径；Q:121-125 实际检查 adapter.failed、START 不存在、adapter.final() 被 NamespaceConsumed 拒绝。正式 :485 失败直接转 :508，不到 :486-495 的 START/graph/FINAL/COVERAGE/SEAL。

## 2. 最终保存与 sink 失败 fallback

E/external29_driver.py:384-398 的 formal_failure_document 同时带 causal rows、preflight disposition 和 preflight_receipt_persisted。正式 :508-520 先将原错误存入 primary_error；marker 与 FORMAL_FAILURE.json 写失败分别 append 到 secondary_errors，不回写 primary_error。资源 close 的错误经 :522-531 保留；:532-537 实际 raise formal_persistence_failure。

:401-422 的 fallback BaseExceptionGroup 包含原错误、所有 secondary、cleanup；formal_failure_causes 和 causal_errors 保留 occurrence rows，原 preflight_receipt 及 persisted 状态复制到 fallback。最终 sink 失败不冒称已生成耐久 receipt；原错误也不会因该 sink 的失败被替换。这个 helper 是正式 catch 的实际调用函数，不是测试专用 flatten。

### 精确执行证据及限制

Q/test_r9_preflight_persistence.py:90-118 仅在 bounded producer strict_capture 注入 original native RuntimeError + cleanup OSError；真实 engineering_preflight、adapter latch 与文件系统调用不被替换。:103-107 对 /proc/self/fd 指向的**实际 preflight.json fd**注入 os.write 错误，不是给原 capture exception 取一个 evidence-write 名字。

- original-only :142-154：真实读取 preflight.json；调用生产 formal_failure_document；通过生产 durable 写 FORMAL_FAILURE.fixture.json，写/fsync/close 后 :151 真正 JSON readback，验证原原因、disposition、NOT_RUN、downstream_dispatch=False。
- compound :156-177：验证附着 receipt 与 persisted=False，真实最终 durable 写后 :172 从磁盘读取，检查原 native/cleanup 与实际 preflight-write secondary，以及 persisted=False。已弥补 r8 仅内存 helper assertion 的缺口。
- final-sink :179-218：真实最终 exclusive write fd 再注入失败；:199-201 验证错误存在、最终路径只剩空 bytes，不能算耐久回执；:202-208 调生产 fallback builder，:214-217 检查 original 两叶与 preflight-write、final-sink 四种原因保留。

**不夸大证据**：测试没有运行整个 formal()，其 builder 返回异常对象供检查，没有实际从正式命令顶层抛出并记录 native traceback；生产 raise wiring 由上述静态代码核对。成功分支的磁盘 readback 确实在已保存 GREEN 对应测试内执行，不只是内存 helper；但 TemporaryDirectory cleanup（Q:29-32）已删除 fixture，本 reviewer 查到 focused fixture 根下无残留 FORMAL_FAILURE.fixture.json，不能说本次重新打开了当时的成功 receipt。

writer final report:7 的“核对原 native/cleanup occurrence”应按实际断言理解：Q:135-140 检查原因及 occurrence 去重，**没有逐叶直接断言 error_type、完整 context parent edges，且 final-sink 末尾只用 reason 检查两个新 secondary**。这些类型和上下文的保真是 source tracing + 保留 r8 causal/durability 证据，而非 r9 新增了全套拓扑断言。这是证据措辞边界，不是当前可达的丢失反例；不据此重开任意异常图契约。

## 3. 真正 source-bound RED / GREEN

| 保存运行 | 原生结果 | native / wrapper | 每侧快照 |
|---|---|---|---|
| W/red-r8-002 | 2 FAIL、1 PASS，3 unique | 1 / 0 | 79 |
| W/green-r9-final-002 | 3 PASS，3 unique | 0 / 0 | 79 |
| W/qualification-001/integrated | 173 PASS，173 unique | 0 / 0 | parent 118 |

RED 不是三项全部失败：original-only 在真实 r8 已 PASS，必须保留此前已经具备的正常保存能力。compound RED native:9-13 在 Q:160/131 因 receipt={} 缺 ENGINEERING_PREFLIGHT_BLOCKED 而失败；final-sink RED native:19-21 在 Q:214 因只剩 preflight-write 与 final-sink 原因、缺 original native leaf 而失败。这两项是缺陷断言 RED，不是 setup、缺 helper 接口或总数失败。RED 的 compatibility else :209-212 正是 r8 原正式分支的 rows 组合，不因缺新 helper 人工制造 RED。

RED 的 60 个 executor 文件逐个等于实际 implementation-r8；保存 runner:67-73 使用 EP19_TEST_EXECUTOR_ROOT 指向 tested r8 executor，测试:12-20 优先从该目录导入。RED/GREEN/integrated 的同一测试体 SHA-256：
`e95b6b5048c781dd8894f59712db150f12272b3b7472aeb0e34fe3ce1dc22941`。

所有上述快照副本逐个满足实际 hash=snapshot_sha256=source_sha256，before/after 一致。RED 时的 build_dependency_evidence.py、run_integrated_parent.py、run_source_bound_group.py 与当前有差异（保存历史，不追认成最终 wrapper）；final GREEN 79 个及 integrated 118 个均等于当前对应 bytes。独立解析 native 身份/status，与 result 控制字段投影及 process control_statuses 相等；log/result SHA-256 均匹配。wrapper_exit=0 仅说明 wrapper 来源稳定，不能把 RED native_exit=1 改成成功。red-r8-001 非权威迭代按 provenance 保留，不回填 NOT_ESTABLISHED_NO_BACKFILL。

## 4. retained 资格与绑定、完整性

静态 AST 从 Q 测试 class 方法重建173 unique identities，与 qualification expected/actual 完全相等；85 个 r8 mandatory 全部保留，r9 增3为88，与 qualification mandatory 清单精确相等。native/result/process 对账全 PASS，无 missing/unexpected/duplicate/fail/error/skip。5个 qualification dependencies 实际 hash 全匹配。本分项不重新签整个 AR007 finite consumer/private eligibility 图；维持已有范围，由 parent 合并其他分项。

runtime binding SHA-256：`3c06598cce6771acfb7451ac235bd5ac265fa76eec843726cb674f2861b9a4b2`；固定 candidate-formal-002、Owner 固定 SHA/tree/patch；118 tooling source 与当前 bytes 及 qualification source map 相同，qualification/dependency hash 相符。保存 runtime-loader-final-002 的 VALIDATION PASS，native/wrapper 0/0；120 snapshots（118 tooling + validator + binding）逐个同源且 before/after 稳定，native/validation/validator/binding hashes相等。本 reviewer 没有运行 loader、没有读取其 private 输入；namespace-local writer subprocess PID 不是独立 OS attestation。

本次 implementation-r9 审查前后119个非 pycache 文件（118 tooling + .source）SHA-256 完全一致；r8→r9 实际10个 added/changed，无删除，清单在 STATIC_CHECKS.json。保留的 adapter/causal/durability/boundary/observe/capture/runner/bookkeeping_v3 均与 r8 相同。没有因资格总数而推导未覆盖分支通过。

## 5. 最终处置和产物

- B7-008-3 / B8-B-1：支持精确有限 preflight→final sink 关闭。
- B7-008-1/2：保留既有 scoped closure；AR001..007/009/010 retained，不新增产品修复或观察门禁。
- 没有发现本分项需继续修实现的具体可达缺陷。Parent 仍需合并其他审查、既有正式前条件及最终独立接受；本报告不能单独提升为 formal readiness 或 EP19 CLOSED。
- 产物：EARLY_REPORT.zh-CN.md、SOURCE.before.json、SOURCE.after.json、STATIC_CHECKS.json、REPORT.zh-CN.md 与 MANIFEST.sha256。仅本 part-a 写入。

审查过程出现批量工具输出截断，已改为限定范围补读及程序化字段归约；一次 read_file 包装字段返回不匹配、一次静态字典未初始化与 integrated 控制含附加字段导致初步比对不匹配，均在只读解析层修正。没有运行被审实现或补造测试输出。
