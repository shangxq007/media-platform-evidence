# r11 Part B：资格／来源／运行绑定与精确交接只读预审

## 结论

**SUPPORTED_EXACT_FINITE_SCOPE**：保存的 178 unique / 93 mandatory 集成资格、source-bound RED/GREEN、最终 runtime binding 和有限 consumer 图核对通过。B10-A-1 在真实 driver 接入的 acquisition/write 与 native-gate/flush 两个独立 fixture 分支获得支持；B9 两项保持 r10 精确闭合。未发现本分项应重开实现修正的具体可达原因替换缺陷。

**仅 advisory preformal，不是 final independent acceptance、正式启动许可、产品门禁通过或 EP19 CLOSED。** Parent 仍须合并 Part A，并完成下述当前准备条件。本报告不把 imported call graph、端点 source snapshot 或 writer PID 提升为更强的运行证明。

路径相对 J；E=implementation-r11/tooling/executor，Q=implementation-r11/tooling/qualification，W=writer-evidence-r11。已全文读取 OWNER_AUTHORIZATION.verbatim.txt、REPAIR_R11_PACKET.md、WRITER_PACKET.md、r10 两分项最终报告，以及 final-002 writer report/matrix/provenance/reconciliation/runtime binding/handoff/emission audit。只用标准库 AST/JSON/regex/hash 静态解析；没有 import 被审实现、测试、loader、probe、preparation、baseline、formal 或产品命令；未访问共享 ledger/usage 或凭据。仅读取必要任务私有 map/inventory 与既有来源文档，输出摘要而非私有正文。

## 1. 独立资格身份与 native 对账

从 Q test_*.py 的 class/test method AST 独立重建178个身份，178 unique；逐字等于 QUALIFICATION.expected_controls。qualification_contract.py 固定集合独立提取93 mandatory，等于保存清单，均包含在实际执行中。旧全部 test 源码与r10字节一致；新增两项是r11两个独立方法。native 身份/status 的顺序投影与 RESULT.controls 完全相等，并等于 PROCESS.control_statuses。缺失、多余、重复、非PASS、mandatory缺失均空。

| 已保存运行 | native控制 | native/wrapper exit | 每侧来源副本 |
|---|---|---|---|
| red-r10-001 | 2 FAIL | 1/0 | 81 |
| green-r11-final-002 | 2 PASS | 0/0 | 81 |
| qualification-002/integrated | 178 PASS | 0/0 | parent 120 |
| runtime-loader-final-002 | VALIDATION PASS | 0/0 | 122 |

raw log、result、parent receipt 的hash相等；最终loader的native JSON等于VALIDATION，process绑定的log/validation/binding hash相等。coverage.py:121-181仍逐项验证source/dependency、expected/mandatory、原生status、重复/缺失/异常/skip、argv/cwd及process一致性，未退化为tests总数或PASS声明。

同一测试体SHA256：`08611fdad2b4ab8724642d3a5a298e8ee0307c71e0c9689f0c2c134034152c78`，RED/GREEN/integrated快照完全相同。RED两项实际失败在保存结果缺FIXTURE_GATE的独立断言，而非setup ERROR或按异常名字虚构反例；RED gate READBACK已记录真实child exit73，虽然旧FORMAL_FAILURE丢失该gate。这与修正后保留native73的最终receipt相区分。

## 2. 实际接受调用点、emission与保存字节

E/external29_driver.py:618-637在fallible print前先将result保存到results[name]，设stopped，并附至原异常runner_gate_receipt/graph_failure_results；:303-336将diagnostic作为新secondary occurrence组合。formal:692-704从combined取回graph结果，保存可用FORMAL_FAILURE。原gate/acquisition仍为primary，marker与diagnostic均保留；stderr delivered=false、persistence_claim=false、semantic_success_artifacts_allowed=false。

Q/test_r11_diagnostic_emission.py实际调用formal、execute_actual_graph、latching与继承生产RunAdapter的marker失败处理。fixture替换不获授权执行的准备、baseline、observer、gate producer等；acquisition producer实际读取缺失私有文件；gate producer实际启动Python子进程exit73，并构造带真实native事实的gate receipt。Runner.put走生产durability，marker目标的父级是真实普通文件；stderr对象由fixture注入，在生产print调用的write或flush方法抛错。**不是OS断管实测，也不是完整生产runner/29 gates执行**，但不是mock掉emitter或只命名异常。两项分别运行，第一项失败不压掉第二项。

直接读取最终保存FORMAL_FAILURE及READBACK，hash一致：
- focused acquisition：33330 bytes，`4caf6100c16cc494dcb35ef8861e00003cda9f57e11fff4cd6c091f2c9a6e8e0`；FileNotFoundError / RuntimeError(marker) / DiagnosticStderrFailure。
- focused gate：29694 bytes，`2f7fab3ecadaf4f2775de2c6bd9faca979f5b5971b7c41b32e5d9daf1212d66e`；NativeGateFailure / RuntimeError(marker) / DiagnosticStderrFailure；native73。
- integrated两份也各保留上述三个类型、unique occurrence、contexts和拒绝字段；context parent edge均在相应row内可解析。RED两份仅DiagnosticStderrFailure，符合原缺陷。

有限emission审计的覆盖等级必须保持：
1. external29 print(stderr,flush=True)：本轮真实production-handler fixture写/flush故障，支持精确关闭。
2. decision_evidence.compare stderr：本轮先持有comparison/persistence failure，再捕获诊断secondary；源码支持修正，集成回归通过，但没有新增该print失败的独立native控制。特别注意external29_driver.py:597把runner.compare_baseline替换为latching_strict_check，因此audit中“actual gate decision evidence”不能解读为本轮external29 gate真实跑过decision_evidence.compare；它是仍导入的有限runner依赖。
3. baseline_evidence.save stderr：先持有persistence failure，诊断异常追加secondary；同属导入的legacy runner.baseline，不是external formal strict_baseline，本轮无单独该emitter故障运行证明。
4. emit_native_failure os.write：r10真实main正常stderr与helper unavailable精确控制保留；best-effort非耐久。其他普通成功stdout并非本次“已持有原错误的诊断发射”分支。
5. tools/run_logged PROCESS_RECEIPT_WRITE_FAILED被writer明确排除为parent preparation wrapper；本分项不为其另签通过或新增任意未来emitter要求。

上述第2项属于审计覆盖标签需精确限定，不是发现接受绕过或缺少原原因的可达新反例。B9 FINAL sink/main精确控制仍在集成178中PASS，causal.py、adapter、runner、durability本身与r10均未改。

## 3. 来源字节、历史与无回填

implementation-r11为121个文件＝120 tooling＋.source；source hash文档前后map、binding source universe、资格before/after/最终map均与当前字节相等。r10→r11独立字节delta10项，逐项等于保存delta record，无删除；causal.py其实byte-identical，不能因矩阵列出它就称本轮改动过它。

W所有16份SOURCE_SNAPSHOT共1616条实际副本hash均=snapshot_sha256=source_sha256。RED、final GREEN、最终integrated、最终loader before/after分别稳定。final GREEN81、integrated120、loader122当前来源均无漂移。RED的build_dependency_evidence.py后续发生了已保存正常修改；旧副本没有被换为现版本。测试体相同不等于整个RED依赖宇宙等于GREEN。

superseded qualification-001/runtime-loader-final-001仍完整保留：VERSION.json旧副本与现版不同；.source/VERSION provenance-label修正已明确作为新的final-002资格与loader重跑，不追认旧receipt运行过新标签。NOT_ESTABLISHED_NO_BACKFILL保持原历史边界。

run_source_bound_group:67-73以实际tested_tooling环境选取executor，argv从implementation路径执行，而非sources.before副本执行。PID只为writer-owned subprocess namespace记录，源快照是运行前后端点，不证明执行中无瞬时改写。loader122副本含120 tooling＋validator＋binding；**loader parent wrapper自身不在执行前快照中**，虽被当前manifest覆盖也不提升为执行前独立封存。

## 4. 固定binding、有限依赖与retained契约

最终文件：`W/RUNTIME_BINDING.candidate-formal-002.r11.final-002.json`

SHA256 / EXECUTOR_IDENTITY：`2c0bd9206991c35dd46215f040c627a46079864eeb8a8825e06132a93ff4be9a`

qualification：`8ffce4ce3a1c3e8d1ca70c4026fa01e340370fb6efbf88a64afe3f13abd3688b`

dependency：`ba857659f35f97842057589e561de90bb992fad86c3312ba74a21c03d1adb389`

固定candidate a29864343ed4f630b052c20d86c23b240f13cfd0、tree fd37409d0274662abbe86f69e3d963c05b379696、parent689ab9456461a8d19a72d059f5157092efc43aff、canonical base86d6aef94fd5e58da552e97c11473cff6eca734e、patch bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690与Owner及consumer常量一致；run_id只能candidate-formal-002。Git运行身份由保存loader实际检查支持，本分项不重新运行Git或loader。

- 独立AST遍历实际entry的本地imports：39 nodes /126 edges，逐项等于保存graph；相对r10多出baseline_evidence→causal import。它是有限静态imports图，不证明每条函数路径本轮都执行过。
- parser graph8包/216文件，当前完整集合/hash相等；90 candidate working source与候选来源摘要相等；10 helper hash相等；29 command/dependency与matrix逐项相等。
- qualification全部dependency hash、binding inventories及reviewed_delta均相等。任务私有map/inventory hash与binding/dependency/applicability四向一致；eligible集合与既有origin文档声明逐项对应、origin文档hash相等。不公开私有正文，不由其重新选择Skill或声称任意未来reader不存在。
- dependency最终v6严格closure、missing/unknown拒绝规则保留；Vite动态来源仍是未来prepared candidate frontend node_modules，保存loader不是正式现态container/endpoint资格。
- matrix、旧tests、runner/coverage/adapter/boundary/bookkeeping_v2/v3/capture/observers/durability/artifacts/freshness/binding_qualification均byte-identical。AR001连续观察、AR002temp lifecycle、AR003捕获时钟、AR004framing、AR005/006回归、AR007绑定、AR009耐久、AR010有界获取保持原处置，不因总数重签全部语义。AR008只支持本轮精确emission修正及retained B9。
- A/B/C、原生29/H733/timeouts、现有capture限额与ledger捕获间Owner接受限制不变；不新增3600秒attempt cap，不重开已接受overwrite-restore限制。

## 5. 精确剩余准备条件（不是新产品门禁）

1. 合并两个r11预审，形成真实parent implementation_review=PASS文件，independent_final_acceptance保持PENDING/REQUIRED，不能拿writer CLOSED或本分项代替最终独立接受。
2. final-002 handoff已含**完整最终文件名与实际digest**，不再是r10的机械替换问题。ABS_PARENT_DISPOSITION / ABS_PARENT_REVIEW仍是待具化的真实绝对路径输入；disposition须满足既有instructions_preloaded、pending_required_instructions=[]、new_required_instruction_action=STOP及既有指令绑定要求。
3. handoff使用未绝对限定的python3；正式消费者coverage.py:163-165要求资格argv[0]精确等于当前sys.executable。已保存资格解释器为`USER_HOME/.hermes/hermes-agent/venv/bin/python3`。Parent必须在已有执行路由中确保python3解析到该执行身份（或使用该已验证绝对命令），不能认为任意python3都适用。本分项未执行当前PATH探测。
4. 先完成所有必要指令/许可和任务owned资源准备，独占prepare→identity→endpoints→revalidate→disposition。每步核实成功再继续；handoff代码块没有set -e/&&链，不能当成失败自动停止的脚本整体盲跑。保持现有隔离、Lean及container/endpoint等当前条件；保存loader不替代这些准备。此为操作具化，非新增契约或实现缺陷。
5. 唯一candidate-formal-002由parent条件满足后执行；consume在baseline之前。不能按START是否存在改预算、刷新失败baseline、换run ID、重用残缺现场或第三次尝试。formal1/2、product3/3保持账面状态；本分项没有消费。
6. 真正29门禁、8000身份/29 skips的ACTUAL对账、最终保全、独立最终接受、原权威EP19关闭条件及获授权证据交付仍未完成。29 NOT_RUN；8000/29仅EXPECTED。工程、独立接受、发布三者不互相替代；EP19未关闭，无产品merge/push/deploy授权扩展。

## 6. 完整性与交付

W/FINAL_MANIFEST.r11.final-002.sha256：1699/1699匹配，自身hash `4b9f63ee81a6facb3cebb776be1861a26b3589ce125ff648843b6d5885e3e742`。
W/FIXTURE_MANIFEST.r11.final-002.sha256：686/686匹配，自身hash `10cab564c75421405566495cfc4d7f17ae7e080a411d89db868aabd0caef1099`。
r10 FINAL_MANIFEST：2921/2921匹配，自身hash与旧review一致。全部保存结果核查见STATIC_CHECKS.json。

审前/审后hash范围为implementation-r10、implementation-r11、writer-evidence-r11、preformal-review-r10；1952文件完全一致，未见该范围新增或改写。fixture另由manifest和readback核对。写入仅本part-b的EARLY_REPORT、REPORT、STATIC_CHECKS、SOURCE_HASHES.before/after、MANIFEST；不是全机无变化证明。

审查中曾误猜integrated native文件名及process hash字段；随后按真实PROCESS.raw_log/log_sha256定位核对，并区分control_statuses的dict投影。未把解析错误当成材料缺失，未运行被审代码或补造执行证据。长输出使用限定段及机器字段补核，没有实施任何修复。
