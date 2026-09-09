# r10 Part B：完整资格、运行绑定来源与 retained contract 只读预审

## 结论

**SUPPORTED_EXACT_FINITE_SCOPE：176 unique / 91 mandatory 的已保存资格、固定 runtime binding 与当前有限依赖图核对通过；B9-B-1、B9-B-2 的精确修正获得支持。本分项未发现应重开修复的具体可达反例。** 不把该结论扩为全部异常图、任意未来 reader、正式运行环境或独立最终接受。

仅 advisory preformal，**不是 final independent acceptance、正式启动许可、产品门禁结果或 EP19 CLOSED**。Parent 必须合并 Part A；若其发现相邻实质问题，本分项的 scoped support 不覆盖该问题。AR001..007/009/010 retained，AR005/006 不重开；批准 A/B/C、Owner 已接受 ledger 捕获间限制、原生 timeout、H733 与已有 capture limits 不变，不新增 3600 秒 attempt 限额。

读取 Owner 全文、REPAIR_R10_PACKET、WRITER_PACKET、r9 两份完整最终审查、r10 final-002 report/matrix/reconciliation/provenance/failure audit/handoff、final-003 runtime binding 与实际源码、保存 native/process/result/snapshots。仅 Python 标准库 AST/JSON/regex/SHA256 静态解析，未 import 被审实现；无新测试、loader、probe、prepare、baseline、formal、产品命令、凭据读取或共享 bookkeeping 操作。写入仅本 part-b。工具一次错误猜测 integrated PROCESS 的层级，随后读取真实 integrated/PROCESS；不是缺失回执。一次长输出截断已对缺失 packet 补读。

路径相对 J：E=implementation-r10/tooling/executor，Q=implementation-r10/tooling/qualification，W=writer-evidence-r10，F=fixtures-r10。

## 1. 资格独立重建与真实 RED/GREEN

- 从 Q 全部 test_*.py 的 class/test 方法 AST 重建 **176 个、176 unique**，逐字等于 QUALIFICATION.expected_controls；不是读取摘要填数。
- E/qualification_contract.py 的固定集合静态提取 **91 mandatory**，与 receipt 精确相等；r9 的 88 全保留，只增加 test_r10_final_boundary 的三项。旧 test 源码均未改，原正常保存/preflight 控制仍 PASS。
- E/coverage.py:121-181 正式必经 consumer 保留源码、dependencies、mandatory、expected/actual、process argv/cwd、native 身份/status、duplicate/missing/unexpected/error/skip 与原生退出对账；不是仅看 totals/PASS。底层 identity_accounting 的拒绝规则未改变。

| 已保存执行 | 独立 native 解析 | native/wrapper | 每侧快照 |
|---|---|---|---|
| W/red-r9-002 | 3 unique、3 FAIL | 1/0 | 80 |
| W/green-r10-final-005 | 3 unique、3 PASS | 0/0 | 80 |
| W/qualification-004/integrated | 176 unique、176 PASS | 0/0 | parent 119 |
| W/runtime-loader-final-003 | VALIDATION PASS | 0/0 | 121 |

前三组 native 的精确顺序/身份/status 与 RESULT.controls 投影、PROCESS.control_statuses 完全相等；log/result hash 全匹配。最终 expected=executed=passed=176，无 duplicate/missing/unexpected/fail/error/skip。五项 qualification dependency 当前字节全匹配。parent log/result/hash/source maps 也相等。

相同测试体 SHA256：`cc52670015283b685b6b0575b8b84dc59e98f9ba6eb5925cef7128412fa63bad`；RED/GREEN/integrated 快照均相同。RED 实际 tested_tooling 指向 implementation-r9，runner:67-73 设置 EP19_TEST_EXECUTOR_ROOT；测试首部优先导入该 executor。RED 的 executor 原件、副本均与封存 r9 当前字节相同；测试/包装器来自 r10，不能说整个 RED 是 r9。

三个 RED 原因必须区分：第一在测试:177 读回只有 OSError、缺原 RuntimeError；第二在:284-286 解析真实 stderr 失败（旧版只有 traceback，非 structured JSON）；第三在:308 因实际 production emitter 缺失失败。第三是缺失输出功能控制，**不是已有 emitter 的 os.write 故障复现**；不得把三项都写成相同生产写失败。没有 setup ERROR，也未把原来 PASS 的旧控制改叫 RED。

80/80、119/119、121/121 before/after 的每份 source snapshot：实际 hash=snapshot_sha256=source_sha256，前后稳定，当前对应源字节也相同。argv 仍从 implementation 原路径执行，非 sources.before 执行；端点 hash 不升级为独立证明运行期间绝无瞬时改写。namespace PID 是 writer-owned subprocess 观察，不是 Hermes reviewer 独立 OS attestation。loader parent wrapper 自身不在 121 来源副本中，当前受 manifest 覆盖不等于执行前封存其自身。历史 NOT_ESTABLISHED_NO_BACKFILL 继续保留。

## 2. 实际失败序列化与保存 bytes

### B9-B-1 支持精确关闭

E/external29_driver.py:631-633 实际 FINAL/COVERAGE/SEAL handler 调用 persist_final_boundary_failure。:404-438 先冻结原 rejection/disposition/causal rows 并附到 original，明确 persisted=False，然后才执行 runner.put(runtime/FINAL_FAILURE.json)。实际写失败以原 error 为 primary、FINAL_FAILURE_RECEIPT_PERSISTENCE 为 secondary 经 causal.raise_composed 组合，附着原 receipt，不能像 r9 用写异常替换原结构化原因。

causal.py 仅新增 final_failure_receipt 为已知 receipt 属性；occurrence 合并规则、32 contexts cap 没变。formal_failure_document:398-402 传递 final boundary disposition/persisted，formal_persistence_failure:465-470 传至最终可用异常；formal:641-670 仍保存原 primary，marker/FORMAL_FAILURE/cleanup 写失败收集为 secondary。

测试:62-191 进入真实 formal() FINAL handler，fixture 替换 baseline、graph、observer/adapter 等不在本次执行授权内的生产工作，Runner.put 使用生产 durable，按实际 /proc/self/fd 所指 FINAL_FAILURE.json 注入 os.write 错误。它不证明真实29 graph 跑过，也不证明新的 adapter latch 全流程；后者 retained regression。可用最终 sink 经过真实耐久实现后 readback，再复制为 retained fixture。

本次直接读取 F/green-r10-final-005 与 F/qualification-004 的 available-final-receipt/FORMAL_FAILURE.json：各15026 bytes，hash 与 READBACK 相符，原 RuntimeError、secondary OSError、原 occurrence 均在；final disposition 为 IRREVERSIBLY_LATCHED_REJECT、inner persisted=False。空 FINAL_FAILURE.empty.bin 为0 bytes，不能算成功 receipt。RED 对应8119 bytes 只剩 OSError，与原缺陷一致。

### B9-B-2 支持实际 main/native 边界的有限关闭

E:794-806 的真实 main 调用 _dispatch_main，非 SystemExit 异常进入 emit_native_failure，然后返回1。测试子进程运行真实 main/parser/fixture dispatch，只把 fixture producer 换为有界私有产生器；它调用同一 final handler/formal_failure_document/fallback，并分别对两个真实 sink fd 注入写失败。这**不是完整 formal() 双 sink 故障端到端执行**；完整 formal handler 与 main fallback 是两条互补控制，实际 formal→fallback→main wiring 由静态追踪补充。

真实父进程保存的 STDOUT.bin 为空、子 native_exit=1；GREEN 与 integrated 的 STDERR.bin 各 **4255 bytes**，独立解析等于 PARSED.json，hash 等于 PROCESS。各有3个 unique occurrence（RuntimeError、OSError、OSError），9个 context IDs，所有非空 parent edge 可解析，无 occurrence truncation；disposition 保留，reason 原文键不存在、reason_exposed=false，三条 fixture 私有 reason body 均不在保存 stderr bytes 中。不是只检查 helper 对象自定义属性。

生产公用输出只取允许的 cause/disposition 字段，private reason 转摘要；实际样本不泄露原文。stderr 标注 BEST_EFFORT_NOT_DURABLE 与 persistence_claim=false；第三控制在真实 os.write 抛错时 emitter 返回False，无成功声明。65536 bytes/64 occurrences、32 contexts 是输出的有限上限，不主张任意深度 lossless；字节有界也不是 stderr 阻塞系统调用具有新 deadline 的证明，不新增该全域保证。

preflight、gate、cleanup、RESULTS 的 retained paths 没因本次把错误变成成功。若 FINAL_FAILURE 已成功而随后 RESULTS 写失败，原 final diagnostic 仍在其成功 sink，不能声称每一个 native document 都必然复制所有此前已保存事实。本报告只接受已证明的精确分支。

## 3. 固定身份、完整来源计数与有限 consumer 图

EXECUTOR_IDENTITY 为 binding 本身 SHA256：`39bf8a0f3a92b34116981ed814e51cc5966c24bb20901dc7c07c5ab6ad61c24b`，不是 source aggregate。

qualification：`298ac98360cade820cb355587030be791d0a93ee1ef7b08983b28564f0707a6d`。
dependency：`c6f4217a9e3bb16ac0a8fae4f368b59f9fb839c68d9782d8ebc63ea287ef95df`。

binding 固定 candidate `a29864343ed4f630b052c20d86c23b240f13cfd0`、tree `fd37409d0274662abbe86f69e3d963c05b379696`、patch `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`、parent `689ab9456461a8d19a72d059f5157092efc43aff`、canonical base `86d6aef94fd5e58da552e97c11473cff6eca734e` 与 Owner 和 binding_contract 常量相同，run_id 精确 candidate-formal-002。Git identity 的实际运行证明仍来自保存 loader；本 reviewer 未跑新 Git/产品命令。

- r10 implementation 共120个非 pycache 文件：**119 tooling + .source**。qualification/source maps、binding maps 与当前119字节完全相等；loader121副本=119 tooling+validator+binding。不能混用这些总数。
- 独立 AST 从 actual external29 entry 遍历本地 imports，得 **39 nodes / 125 edges**，逐项等于保存 reachable_local_graph。新增 final writer/main/serializer 五条 helper edge 能在实际 caller AST 找到；26条有限语义 edge 仍被 consumer 精确要求，不用文件名出现冒充执行本身。
- 8个 parser packages/216个文件的完整当前文件集合/hash 与 package graph 相同；90个 candidate consumer working bytes 与 candidate_source/working hashes相同；external helpers hash 全相等。29 command/dependency 逐条等于矩阵，矩阵与r9字节不变。
- dependency schema 必须最终为v6；旧schema不会因入口允许列表而跳过实际 closure。missing/unknown actual dependencies 仍拒绝。Vite 动态来源仍是未来 prepared candidate frontend node_modules，不是已验证正式 runtime/container/endpoint。
- 本分项未读 private-r10 map/inventory 原文或字节；仅对 binding/dependency 中的声明摘要交叉相等作核对。实际私有 eligible 内容校验由保存 loader 与 retained consumer source 支持，**不是本 reviewer 新的私有输入独立校验**。不由该摘要等值重新选择 Skill，也不宣称证明任意未来 reader 无依赖。

## 4. argparse、path guard 与 retained controls

qualification-001 保存失败为已有 CLI help test 返回1：当时 main 把 argparse 正常 SystemExit(0) 当错误；最终仅增加 except SystemExit: raise，恢复 argparse 原语义（help=0、解析拒绝非零），未改变 parser/accepted args 或 formal gates。旧 help test 字节不变，qualification-004 已真实PASS。不能把帮助退出恢复解读为成功 formal。

runtime-loader-001 明确保存 CONFIG_OUTSIDE_WRITER_EVIDENCE_R9；最终 binding_contract.py:32 只把封存目录 guard 平移至 writer-evidence-r10。exact_path absolute/resolve、预期hash、严格键集合、固定候选、唯一run_id、source universe、私有输入hash及依赖消费仍保留，未拓宽为任意路径/取消seal。

r9→r10 独立字节delta为9项，与 final-003 delta record逐条相等，无删除。runner、coverage、durability、artifacts、bookkeeping_v2/v3、boundary、capture、observe、native_observe、executor_adapter、binding_qualification 均与r9字节相同。AR001..007/009/010 的 retained regression 仍在176控制内，不以本次通过数重签未触及语义。

## 5. readiness 的精确剩余事项

1. Parent 合并本分项与 Part A，形成最终版本 implementation_review；independent_final_acceptance 保持 PENDING/REQUIRED。不得把writer CLOSED或本预审直接写成最终独立接受。
2. r10 handoff只是引用r9命令模板。实际执行前须把 implementation/private 路径、**B 的完整 final-003 文件名及 S 摘要**一并替换为本报告固定值；仅字符串 r9→r10 会指向旧 final.json、旧digest。模板中的 ABS_PARENT_DISPOSITION 与 ABS_PARENT_REVIEW 仍需真实产物，不是已有回执。这是待具化启动输入，不是要求新产品门禁。
3. 按既有顺序加载所需指令/工具许可，独占 prepare→identity→endpoints→revalidate→disposition，验证隔离与任务owned资源条件。保存 loader 仅固定绑定验证，不替代这些当前状态条件；本次未运行它们。
4. 条件满足后才由 parent 消费唯一 candidate-formal-002。consume 在 baseline 前；不能按START存在与否改预算、刷新失败baseline、换run_id或第三次尝试。产品3/3、formal1/2为保留账面状态，本审查不消费预算。
5. 真实29 gates、保全、8000 identities/29 skipped 的 ACTUAL 对账、最终独立评审及原权威EP19关闭条件仍待完成。29 NOT_RUN，8000/29仅EXPECTED；evidence发布≠工程通过≠独立接受，EP19未关闭，无产品merge/push/deploy/publication授权扩展。

## 6. 完整性与产物

W/FINAL_MANIFEST.r10.final-002.sha256 **2921/2921匹配**，自身SHA256 `e41204d53530f3d683f465c41863991f0782d5bcdf642dacd8cbebb4bcbed9a5`；r9 FINAL_MANIFEST **1406/1406匹配**。审查前后固定hash范围为 implementation-r9、implementation-r10、writer-evidence-r10 的3161个非pycache文件，全部不变，其中r10 implementation120个。该范围不是全机无变化保证；fixture saved bytes另与其保存readback/process/manifest核对。

本目录输出 EARLY_REPORT.zh-CN.md、SOURCE_HASHES.before.json、SOURCE_HASHES.after.json、STATIC_CHECKS.json、REPORT.zh-CN.md、MANIFEST.sha256。仅静态审查结果与报告，没有补造测试、运行证据或改动实现/历史/共享状态。
