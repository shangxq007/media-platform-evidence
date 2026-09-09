# r10 Part A：最终失败边界与生产 main fallback 只读预审

## 结论

- **B9-B-1：SUPPORTED_CLOSED_EXACT_SCOPE。** 实际 FINAL handler 原异常加 runtime/FINAL_FAILURE.json 写失败，现能在可用的 FORMAL_FAILURE.json 中保留原 occurrence/type/context、secondary 与冻结的拒绝 disposition。
- **B9-B-2：SUPPORTED_CLOSED_EXACT_NATIVE_MAIN_SCOPE。** 真实子进程调用生产 main/parser/dispatch/error emitter，保存 stderr 为可解析的脱敏 JSON，包含原异常与两个 sink 失败，原生退出1。不是只检查 helper 属性；也不是生产正式运行。
- **有限路径 audit 的整体 PASS 仍有一处具体可达缺口：B10-A-1 OPEN。** gate 诊断的旧 print emitter 在 stderr 写失败时仍可替换已组合的原 acquisition/gate 异常，导致尚可用的外层 FORMAL_FAILURE.json 只保存 stderr 异常。详见第五节。它不推翻上述两项精确闭合，也不是要求 stderr 耐久。

本报告仅 **advisory preformal**，不是 final independent acceptance、正式启动许可、产品门禁或 EP19 关闭。本分项不支持把 FINAL_FAILURE_PATH_AUDIT.r10.final-002.json 的 gate 分支乃至整份 PASS 无条件提升为全部实际失败出口已保留原因。

## 一、范围与证据身份

路径相对 J。E=implementation-r10/tooling/executor，Q=implementation-r10/tooling/qualification，W=writer-evidence-r10，F=fixtures-r10。

已读 Owner authorization 全文、r10 packet、WRITER_PACKET、r9 两分项完整最终报告、r10 final-002 writer 中文报告与失败路径 audit，实际 driver/causal/adapter/runner 调用点、r10 测试及来源包装器、保存 native/process/result/source snapshots 和持久保存的 fixture bytes。只做静态 AST/JSON/日志解析及 SHA-256；没有 import 被审模块、执行测试/loader/probe/preparation/baseline/formal，没有读取共享 ledger/usage 或凭据，没有修改实现或任何共享状态。

实际 driver SHA-256：`fbebf93117ecdc469e1b6d0767fdaf81e8c8268df54392d561c139994285be3a`。
同一 r10 测试体 SHA-256：`cc52670015283b685b6b0575b8b84dc59e98f9ba6eb5925cef7128412fa63bad`。

## 二、B9-B-1：生产 FINAL handler 与真实保存字节

E/external29_driver.py:625-633 为 FINAL/COVERAGE/SEAL 共用的实际 except；:406-441 先冻结 FINAL_ACCEPTANCE_REJECTED / IRREVERSIBLY_LATCHED_REJECT、原 causal rows、semantic_success_artifacts_allowed=False，再附到原异常并执行 runner.put(runtime/FINAL_FAILURE.json)。真实持久化失败时 causal.raise_composed 以原异常为 primary，写失败为 FINAL_FAILURE_RECEIPT_PERSISTENCE secondary；combined 上保留 receipt 与 persisted=False。不是依赖 Python 隐式 __context__。

外层 :641-653 保留 primary_error，formal_failure_document(:384-403)读它的 causal rows 和 final_failure_receipt；FORMAL_FAILURE.json 写失败仅追加 secondary。:444-470 与 :665-670 保留该组合及原 disposition 并抛向 main。E/causal.py 将 final_failure_receipt 纳入 receipt transport，仍按 occurrence_id 合并而不是按 message 去重。

Q/test_r10_final_boundary.py:58-150 调用了生产 formal()。准备、consume、baseline、graph 与其他前置 producer 被限定 fixture 替代；strict_check 在 FINAL 抛原 RuntimeError，实际 runtime/FINAL_FAILURE.json fd 的 os.write 抛 OSError；Runner.put 使用同一生产 durable/exclusive_bytes 底层。测试不会创建正式 namespace 或执行门禁。COVERAGE/SEAL 共用同一 except 的覆盖由静态 wiring 支持；不虚称三个阶段分别执行过注入。

:152-189 在临时目录 cleanup 前将实际 FORMAL_FAILURE.json 字节与失败内层空文件复制到持久 fixture 根，随后解析保存副本；本 reviewer 重新读取的是仍然存在的保存字节，不是只有测试内存断言。

| 保存运行 | FORMAL_FAILURE bytes | causal types | context 数 | 内层失败文件 bytes |
|---|---:|---|---|---:|
| F/red-r9-002/available-final-receipt | 8119 | OSError | 1 | 0 |
| F/green-r10-final-005/available-final-receipt | 15026 | RuntimeError、OSError | 5、3 | 0 |
| F/qualification-004/available-final-receipt | 15026 | RuntimeError、OSError | 5、3 | 0 |

GREEN 两份都含冻结 disposition 中的同一 original occurrence；所有 occurrence 唯一，context parent 引用在相应行内部可解析，拒绝 disposition 与 persisted=False 相符。空内层文件不算成功持久化。focused SHA-256：`33a3a4ef152ab9ed64fca440c1a0b01ef520809822bf3e564c61d14310135369`；integrated SHA-256：`f19d780e8adde65e50ebf33c883f8fbb0bfb0cc8ac84ca04ec6143e9177dc3fb`；RED SHA-256：`916a9b8baa8be598cf69862f0eaf3a6c75e4ac76de57a127532475d1a570f240`。

## 三、B9-B-2：真实生产 main 序列化，保存 stderr 非耐久保证

Q:191-301 由真实父 subprocess 捕获 stdout/stderr；子进程导入对应 executor，替换的仅 fixture producer，实际执行生产 main、parser、fixture dispatch 和 error reporter。bounded producer 使用实际 persist_final_boundary_failure、formal_failure_document、durable、formal_persistence_failure，两个实际 fd 分别写失败。该子测试并未再次执行完整 formal catch；完整 formal handler 是上一控制覆盖，正式 :665-670 → main:800-805 的组合由源码关联。生成的短 child script 所在 TemporaryDirectory 已清理，其脚本文本保存在相同测试体的 before/after 快照中，不能称为独立保存的 child 文件或独立 OS attestation。

E:488-536 白名单保留 occurrence/type/stage/association/context、reason_sha256 和公共 disposition，删除 reason body；:539-557 有界 JSON 与 os.write 短写循环，失败返回 False；main 返回1。正常成功分支不会因诊断变为 success。64 occurrence、32 contexts 和65536-byte限额是当前有限链的界限，不作任意深度无损承诺。

focused 与 integrated 的 F/<run>/native-main-fallback/STDERR.bin 各4255 bytes，均为单个 JSON；STDOUT.bin 均0 bytes；PROCESS.json 原生退出均1，stdout/stderr hash 与实际 bytes 匹配，PARSED.json 与实际 stderr JSON 相等。两份均有3个 unique occurrence：RuntimeError、OSError、OSError，context 数7/4/2，parent 引用均内部可解析，原拒绝 disposition 存在，未暴露私有 reason body。

focused stderr SHA-256：`70aad8f61027e9017ba46a394105e96cebde753159026e6a461dd58fb61b4bc2`；integrated：`ad82e35cb1c7a1bcea831b88ef66fbf0153386c0745e42cabef2f33f8617f219`。

stderr_transport=BEST_EFFORT_NOT_DURABLE、stderr_persistence_claim=False。这些是父进程保存的捕获 bytes，**不证明生产 stderr 耐久**。第三控制确实覆盖 emitter 的 os.write 不可用返回 False；它是 helper 单测，不冒称另一个真实 main 子进程不可用 stderr 控制。

## 四、source-bound RED/GREEN 与 retained 分支

| 运行 | native 控制结果 | native / wrapper | 每侧 source snapshot |
|---|---|---|---:|
| W/red-r9-002 | 3 FAIL | 1 / 0 | 80 |
| W/green-r10-final-005 | 3 PASS | 0 / 0 | 80 |
| W/qualification-004/integrated | 176 PASS | 0 / 0 | parent 119 |

全部 before/after 副本实际 SHA-256=snapshot_sha256=source_sha256，两个时点相等且与目前各自对应来源相同。RED 的 executor 来源是封存 implementation-r9，测试/包装器是 r10；三侧相同测试体 hash 已核对。argv 从原 implementation 路径运行，并非从 sources.before 副本运行。两个端点快照不构成执行中无瞬时改写的独立证明；PID 仅 writer-owned subprocess namespace 观察。

三个 RED 分别为：保存 receipt 缺 RuntimeError；生产 stderr 不是 JSON；旧版本没有 emitter。最后一项是新增能力缺失控制，不把它误写为 r9 原有正常保存功能退化。三个控制分开执行，前一断言失败没有跳过后一控制。r9 original-only 等三条原 preflight 控制在最终集成中仍全部 PASS。

独立从 Q 的 test class/method AST 重建176 unique 身份，等于保存 expected 和 native 实际集合；qualification_contract AST 的91 mandatory 等于保存清单。native identity/status 投影逐条等于 RESULT.controls 及 PROCESS.control_statuses；原生日志/结果 hash 匹配。RESULT.controls 的额外 expected/timestamp 字段不能用来制造假不相等。无 duplicate/missing/unexpected/failed/errored/skipped。

有限 acquisition/preflight 路径：boundary:119-123、latching_strict_check:163-169 调 adapter._latch_exception；adapter:45-68 在 marker 写失败时附 secondary 而不替换原异常。strict_baseline:205-211 将真实 close 错误与 original 组成 group。preflight:316-374 在实际 preflight.json 写前冻结拒绝并组合持久化失败；外层 formal:641-670 有原/次/cleanup 的明确传递。r9 精确 preflight closure retained。

gate 正常诊断传递：runner:530-538 真实 receipt 写失败附 runner_gate_receipt，driver:260-289 合并原及 marker rows；adapter.failed 后拒绝继续成功边界。final 内层写成功时保存明确拒绝并返回 FAIL summary；内层失败则走本轮修正。外层 failure marker、FORMAL_FAILURE 与 cleanup 写异常作为 secondary 进入 formal_persistence_failure。未要求在每一个成功保存文件中重复所有以后才发生的错误。

E/durability.py、executor_adapter.py、capture.py、observe.py、native_observe.py、runner.py、coverage.py、bookkeeping_v3.py 与 r9 byte-identical；保留已接受组件处置与观察限制，不能将 byte-identical 或176 PASS扩大为下节未覆盖相邻 emitter 的通过。

## 五、B10-A-1 OPEN：gate 的旧 stderr emitter 仍可替换原 structured cause

**静态可达，未运行 fresh probe/RED。** 这是 audit 明列 gate failure 与 stderr unavailable 的有限实际交界，不是随意假设任意函数抛错或新建无限故障要求。

具体路径：
1. 第一 gate 的 COMMAND_BEFORE 实际 strict acquisition（E:568 → :163-169 → :134-139 的 drain/capture）抛出错误。adapter._latch_exception 先置失败；实际 BOOKKEEPING_FAILURE.json 写失败时，:56-68 把 marker secondary 附回原异常。
2. execute_actual_graph:582-585 捕获原异常，merge_graph_exception 保留原+marker，并置 diagnostic_persistence_uncertain=True。此时原 structured rows 仍在局部 result 中。
3. :585 调旧 emit_persistence_uncertainty。它在 :300 使用无 try/except 的 print(..., file=sys.stderr, flush=True)。若当前 stderr 是断开的 pipe 或不可写 fd，该实际写点抛 BrokenPipeError/OSError。该函数没有将 result/原异常附到新错误，也没有返回失败但继续交付原 result。
4. :587 results[name]=result 尚未执行，函数也未返回；formal:624 的 results,stopped 赋值未完成，第一 gate 时外层 results 仍为初始化的 {}。formal:641-645 接到并保存的是 stderr 写异常。
5. 即使外层 FORMAL_FAILURE.json 仍可写，formal_failure_document 只从新 stderr 异常显式 attrs/causal rows 读取，不遍历 __context__，也不回收 graph 局部 result。因此原 acquisition occurrence 与 marker secondary 不进入这个尚可用的最终 receipt；若最终 sink 也失败，新增 main emitter 同样只能序列化已经被替换的 primary。

这是“可用 final sink 中丢原结构化原因”，不是“stderr 本身不能写却要求它耐久”。进程仍失败、adapter仍锁住，**不是接受绕过**。先前 r6:190-221、r7:217-252、r8:56-101 的正常 stderr 控制都保留原 scoped PASS；它们没有使此旧 print 写失败，新 r10 unavailable-stderr 控制仅 patch emit_native_failure 的 os.write，也未覆盖旧 print。不得据它们把 audit gate 分支 primary_retained=True、secondary_write_failure_composed=True 当成无条件成立。

建议 parent 在既有外部修正授权内对这一明确交界作定点处理并要求受影响保存证据；本 reviewer 不改实现、不执行测试。没有要求替换正常 gate 协议、重跑正式门禁、增加产品修复或扩展捕获窗口。

## 六、完整性、边界与交付

W/FINAL_MANIFEST.r10.final-002.sha256：2921条全部匹配；manifest hash `e41204d53530f3d683f465c41863991f0782d5bcdf642dacd8cbebb4bcbed9a5`。
W/FIXTURE_MANIFEST.r10.final-002.sha256：1347条全部匹配；manifest hash `4600040ca01e5f513c6693808d6259e71743aa2641c955126532e84c0c2d3910`。
审前/审后4404个输入文件 hash 完全相同，涵盖 r10 实现120文件、writer/fixtures、r9审查报告与 Owner/packet；未发现监控目录新增文件。产出仅本 part-a 的 EARLY_REPORT.zh-CN.md、REPORT.zh-CN.md、BEFORE.sha256.json、AFTER.sha256.json、MANIFEST.sha256。

静态解析过程中曾使用错误的集成日志/快照位置及 manifest 相对根，已按实际 PROCESS 指针、parent snapshot 位置和 manifest 根修正；没有因此判定材料缺失。批量输出截断后以限量源段与字段投影补读；无被审代码执行或伪造运行输出。

AR001..007/009/010 与先前已接受的有限因果、原生29/H733/timeout规则保持原范围；Owner 接受的 ledger 捕获间 overwrite-restore/truncate-regrow 限制不重开、不扩展到其他 protected 对象；不新增3600秒 attempt cap。完整 AR007 运行绑定/私有来源图由 parent 合并其他分项，本分项不自签。

产品预算3/3、正式1/2按授权与既有证据保持，本 reviewer 未消费任何正式预算。正式29门禁未执行，8000/29仅EXPECTED，EP19未关闭。parent应区分精确B9两项闭合、上述剩余有限审计缺口、正式准备/执行与最终独立接受；本报告不能单独构成正式 launch readiness。
