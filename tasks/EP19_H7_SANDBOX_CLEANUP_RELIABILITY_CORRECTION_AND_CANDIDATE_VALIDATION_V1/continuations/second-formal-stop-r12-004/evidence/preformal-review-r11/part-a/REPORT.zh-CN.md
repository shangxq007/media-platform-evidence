# r11 Part A：B10-A-1 与有限诊断 emission 审查

## 结论

**B10-A-1：SUPPORTED_CLOSED_EXACT_ACTUAL_ACQUISITION_WRITE_AND_GATE_FLUSH_SCOPE。** r10 指出的先 stderr、后 result ownership 缺口已在实际 driver 中修正。已保存 predecessor RED 两项均 FAIL，最终 focused GREEN 两项均 PASS；本 reviewer 重新解析实际保留下来的 FORMAL_FAILURE.json，确认 acquisition/gate primary、marker secondary、diagnostic secondary 三个 occurrence，以及拒绝 disposition、上下文和 gate 原生退出保留。未发现要求重开这一精确修正的具体可达缺口。

有限 emission audit 获**分层支持**：driver 为实际故障控制加磁盘回执；decision/baseline 直接依赖为静态 ownership/except 证明及集成回归，不冒称分别做过新的 stderr 故障注入。r10 main 正常/最佳努力/不可用行为保留。本结论仅 **advisory preformal**，不是 final independent acceptance、正式启动许可、工程29门禁通过或 EP19 CLOSED。

## 范围与方法

已读取完整 OWNER_AUTHORIZATION、REPAIR_R11_PACKET、WRITER_PACKET、r10 两分项最终报告、r11 final-002 writer 报告/matrix/emission audit，以及实际 driver、adapter、runner、causal、decision/baseline emitter、r11 测试与 source-bound wrapper。仅静态源文/AST、JSON、原生日志和 SHA-256 核对。未 import/执行被审实现、测试、探针、loader、准备、baseline、formal，未读凭据或共享 bookkeeping；全部写入仅本 part-a。

以下路径相对 J：E=implementation-r11/tooling/executor；Q=implementation-r11/tooling/qualification；W=writer-evidence-r11；F=fixtures-r11。

当前 driver SHA256：`9113ff32a75edf8ee00ecec976cccb70b5c0e226ce88b386973e913e8a3ade4c`。
相同 r11 测试体 SHA256：`08611fdad2b4ab8724642d3a5a298e8ee0307c71e0c9689f0c2c134034152c78`。

## 一、实际 ownership 与最终出口

- E/external29_driver.py:618-626：adapter latch 后合并原异常和 marker rows，先 results[name]=result、stopped=True，先附 exc.runner_gate_receipt 与 exc.graph_failure_results，再进入 :631-634 的真实 print emitter。原错误不再只留在尚未交付的局部变量中。
- :304-336 将真实 print/write/flush 抛错记录为 DIAGNOSTIC_STDERR_EMISSION secondary，保留原 primary，并将同一 result/results 附到组合异常；拒绝 semantic success，明确 stderr delivered=False、persistence_claim=False。
- formal :692-704 从组合异常回收 graph_failure_results，经 formal_failure_document :420-439 和 causal.receipt_rows 保存至可用 FORMAL_FAILURE.json。causal.py 按 occurrence_id 合并 receipt/exception/marker transport；不是依赖隐式 __context__。
- adapter :45-68 的真实 _latch_exception/fail 保留 marker 错误而不替换 acquisition/gate 原错误。runner :530-538 的 receipt 持久化错误也先附 runner_gate_receipt；本次未把它改成成功。
- 保存回执不保证包含以后发生的所有错误：formal 随后重写失败 marker 或 cleanup 的新错误经 formal_persistence_failure 传出，不能声称较早成功写入的 FORMAL_FAILURE 自动更新。此限制不妨碍本次要求的 primary+首次 marker+stderr 三元组已经保存。

## 二、控制真实程度、RED/GREEN 与保存 bytes

Q/test_r11_diagnostic_emission.py :87-247 调用生产 formal、execute_actual_graph、adapter latch 与真实 print(...,flush=True)。不执行正式 namespace 或真实产品门禁：前置 modules/consume/baseline/observer/boundary 等由限定 fixture producer 替代。

acquisition 在第二次 strict_capture producer 对真实缺失私有文件 read_bytes，得到 FileNotFoundError；gate producer 真正 Popen 私有 Python child，原生退出73，再以带 native receipt 的 NativeGateFailure 交给生产 driver handler。gate 的 Runner.run_gate 是限定 producer，不是完整生产 runner.run_gate/29 graph 执行。marker 使用实际 durability 路径，父路径为普通文件而非目录，获得实际 RuntimeError；不是仅凭异常名称模拟 marker。

stderr 替换为 FailingDiagnosticStream，**实际生产 print 未被 mock 掉**；acquisition 的 write 抛错，gate 的 flush 抛错。它是有限受控 stream method 故障，不冒称真实 OS broken pipe/fd 故障或全域 stderr 耐久测试。两测试独立执行，RED 第一项失败不遮蔽第二项。RED 在 result 缺 FIXTURE_GATE 的断言失败；不是 setup ERROR。

测试在临时目录清理前复制实际生产 durable 写出的 FORMAL_FAILURE.json 到持久 fixture 目录，再 JSON readback。本 reviewer 核对的是这些仍在磁盘的 bytes，不是只读测试内存属性或 writer 摘要。

| F 下运行 | acquisition bytes / types | gate bytes / types | 原生控制结果 |
|---|---|---|---|
| red-r10-001 | 11946 / 仅 DiagnosticStderrFailure | 9761 / 仅 DiagnosticStderrFailure | 2 FAIL，native1 / wrapper0 |
| green-r11-final-002 | 33330 / FileNotFoundError、RuntimeError、DiagnosticStderrFailure | 29694 / NativeGateFailure、RuntimeError、DiagnosticStderrFailure | 2 PASS，native0 / wrapper0 |
| qualification-002 | 33308 / 同 GREEN acquisition | 29694 / 同 GREEN gate | 集成178 PASS，native0 / wrapper0 |

六份 READBACK 的 bytes/hash 全与文件相等。GREEN 与集成每份三个 unique occurrence，无 context overflow，所有非空 parent_context_id 在该 occurrence 内可解析；acquisition contexts 为6/4/6，gate为8/4/6。原 gate result=FAIL，semantic_success_artifacts_allowed=False，diagnostic_persistence_uncertain=True，stderr delivery 为 BEST_EFFORT_STDERR_FAILED_RETAINED_IN_FINAL_SINK，非成功/非耐久。gate native_exit=73 与 READBACK 相等；acquisition native_invocation=False。write 路径1次write/0次flush，flush路径2次write/1次flush。

注意：RED gate READBACK 已有真实 child exit73，但当时最终 FORMAL_FAILURE 的 gate result 丢失，所以 writer audit 的 RED native_exit=null 是**最终 receipt 投影**，不能解读成 RED 没启动 child。

focused acquisition receipt SHA256：`4caf6100c16cc494dcb35ef8861e00003cda9f57e11fff4cd6c091f2c9a6e8e0`。
focused gate receipt SHA256：`2f7fab3ecadaf4f2775de2c6bd9faca979f5b5971b7c41b32e5d9daf1212d66e`。
其余四份摘要、context计数及readback投影见 STATIC_CHECKS.json。

## 三、有限 emission-site audit

| 真实位置 | ownership / failure 处置 | 支持层级 |
|---|---|---|
| external29_driver:300 print(stderr,flush=True) | :623-626 先拥有原 result/exception；:304-336 追加 diagnostic secondary；:695-704 回收最终落盘 | 实际 write/flush RED/GREEN 与集成保存回执 |
| decision_evidence.compare:273-293 | comparison rejection 与 persistence rows 在 :275-281 先构造 failure；print异常仅追加 secondary，仍 raise 原 evidence failure | 静态直接依赖闭合；没有专门新故障控制的声明 |
| baseline_evidence.Evidence.save:52-68 | evidence persistence failure 在 :54-56 先拥有；print/flush 非预期异常附 secondary；fsync OSError/AttributeError best effort | 静态导入依赖闭合；legacy baseline 非 external formal strict_baseline；不扩大为任意 baseline 原因链保证 |
| external29_driver.emit_native_failure:575-593 / main:853起 | main 已拥有 caught error；os.write 失败返回False，main仍返回1 | r10 精确行为 retained，实际子进程 stderr 与不可用 helper control |

额外静态扫描实际 executor Python 的 stderr/print 出口：adapter没有文本 emitter；driver:811 的 fixture result 已先 durable，:828 identity输出已先持久化；runner:613 属 legacy preflight结果stdout，不是本轮 formal异常 emitter。subprocess stderr=STDOUT 是捕获配置，不是错误处理 print。tools/run_logged.py 属 parent准备包装器，不执行、不更改，不纳入本次有限 driver/adapter异常范围。这是有限清单，不是任意未来 emitter、任意对象方法抛错或全机保证。

## 四、r10 retained 行为与来源核对

main、emit_native_failure、native_failure_document、formal_persistence_failure、persist_final_boundary_failure 函数源段与r10逐字相等；test_r10_final_boundary.py也相同。集成的三条r10控制仍PASS。F/qualification-002/native-main-fallback 的实际 STDERR.bin 为4255 bytes，STDOUT.bin为空，PROCESS native_exit=1，两个hash吻合，实际stderr JSON=PARSED.json；RuntimeError/OSError/OSError三个occurrence的contexts为7/4/2。stderr SHA256 `baee81acb4d54ecdc43fe0b819a2a4769aab12d8418b0ef18a56662bd7b8c9c9`。BEST_EFFORT_NOT_DURABLE与persistence_claim=False不变。不可用stderr仍是os.write helper控制，不能冒称另一完整main子进程注入。

source snapshots：RED81/侧、focused GREEN81/侧、integrated parent120/侧。各保存副本的实际hash=snapshot_sha256=source_sha256，before/after稳定。GREEN及集成全部对应当前源；RED的 executor来源为implementation-r10，测试/wrapper来源为r11。同一r11测试体摘要相同。RED中 build_dependency_evidence.py 的历史快照与**当前final**不同，但历史两侧自洽且未被覆盖；不把当前final source冒充执行过RED，不因正常后续修订否定真实历史反例。

argv由源路径执行，快照不是执行目录；端点hash不是独立证明运行中绝无瞬时修改。PID为writer-owned subprocess namespace观察，不是独立Hermes OS attestation。

独立AST重建Q下178 unique身份，等于保存expected/actual；qualification_contract字面常量93 mandatory与保存集合一致。原生日志解析的身份/status逐项等于PROCESS及RESULT投影，RED/ focused /integrated日志与RESULT hash全部匹配；集成178 PASS，无duplicate/missing/unexpected/fail/error/skip。完整runtime consumer/私有来源与launch绑定由parent合并另一分项，不用本分项替代。

## 五、完整性与剩余条件

W/FINAL_MANIFEST.r11.final-002.sha256：1699条全部匹配，自身 `4b9f63ee81a6facb3cebb776be1861a26b3589ce125ff648843b6d5885e3e742`。
W/FIXTURE_MANIFEST.r11.final-002.sha256：686条全部匹配，自身 `10cab564c75421405566495cfc4d7f17ae7e080a411d89db868aabd0caef1099`。
本次限定审前/审后源码集合为E和Q直接Python文件73项，hash完全不变；不是全implementation所有语言文件或全证据树前后不变保证。读入证据完整性另由上述manifest及保存回执核对。

保留AR001..007/009/010原有限处置与AR005/006回归，不新增3600秒attempt cap，不重开Owner已接受ledger捕获间overwrite-restore限制，也不扩展到其他protected对象。未修改产品、契约、预期、依赖或共享状态；产品3/3与formal1/2为授权保留状态，本reviewer未消费预算。

剩余是parent合并分项、形成r11 implementation review及现态disposition、完成既有条件式准备/唯一formal尝试、真实29门禁及8000/29 ACTUAL对账、最终独立接受与权威关闭条件；本报告不代替其中任何项。未发现本part-a精确B10-A-1范围的新实质blocker。

审查工具曾输出截断，已分段补读必要源文；曾猜测集成NATIVE.log路径不存在，随后按PROCESS.raw_log核对真实文件；静态mandatory初次解析未展开frozenset，随后按实际AST参数重建93项。均未运行被审代码或伪造运行结果。

产物：EARLY_REPORT.zh-CN.md、REPORT.zh-CN.md、SOURCES.before.json、SOURCES.after.json、STATIC_CHECKS.json、MANIFEST.sha256。仅报告与静态核对数据；无实现修改。
