# r8 Part B：原因 occurrence/context、资格来源、运行绑定只读预审

## 结论与边界

**B7-008-2 在当前有限实际嵌套持久化与 transport 范围支持 scoped closure；AR007/009 retained。不能据此宣称 AR008 整体无残余。** 另发现实际 preflight 失败回执写入仍可替换原异常（下述 B8-B-1，交 Part A/parent 合并）。本报告仅 advisory preformal，非 final independent acceptance，非正式启动许可。

读取 Owner 全文、r8 packet、r7 Part B 全文及 writer r8 final report/matrix/reconciliation/provenance/binding/full manifest；只执行静态 AST、JSON、native 日志解析及文件 SHA-256。未导入或运行 executor、测试、loader、产品门禁、probe、preparation、baseline、formal；未读取共享 ledger/usage 原文或凭据，未写其他目录。产品3/3、formal1/2按委派保持；29 gates 全 NOT_RUN，8000/29仅 EXPECTED。历史 NOT_ESTABLISHED_NO_BACKFILL 不回填，不重开已接受 ledger 捕获间观察限制。

下文路径相对 J；E=implementation-r8/tooling/executor，Q=implementation-r8/tooling/qualification，W=writer-evidence-r8。完整可机器核对数据在 STATIC_CHECKS.json。

## B7-008-2 scoped closure：真实原因身份、嵌套上下文与落盘

- E/causal.py:19-32,79-84 将 exception occurrence 的 UUID 绑定到异常对象，而不是 error text、stage 或 leaf_index 去重。:152-178 唯一合并键是 occurrence_id；两个独立同文 OSError 即便 stage 相同也不会因为文本相等合一。不是以 message dedup 冒充资源去重。
- :196-220 每层 primary/secondary composition 有共同 context_id；内层保留 primary role，作为外层 cleanup 时追加 publishing-parent-fsync / secondary-for-primary，:60-76 用 parent_context_id 接到外层；不覆盖原 role。:87-100 已有 rows 也追加本次 transport context，修复 r7 的 existing-rows 早退。
- 实际调用 E/durability.py:81-97：outer write 主异常、file close 次异常、parent fsync 次异常；parent fsync 又经 :28-37 形成 inner fsync 主异常与 directory close 次异常。inner leaf 的 BODY_OR_NATIVE primary → DIRECTORY_FSYNC_AND_CLOSE_FAILURE composition → PUBLISHING_PARENT_FSYNC secondary → EXCLUSIVE_BYTES_BODY_AND_PUBLICATION_FAILURE composition，与 outer write leaf 共享外层 composition。并非只剩两个互不相关的 primary-operation。
- Q/test_r8_transport.py:103-156 实际执行 exclusive_bytes，按实际 fd 指向注入 write/fsync 故障，close 先真实关闭后对两个资源抛相同文本。:138-140 调实际 adapter latch 后读回真实 BOOKKEEPING_FAILURE.json 的 decision；:141-156 检查两条 close、两个 occurrence_id、不同资源 stage，以及内层 primary、外层 secondary 和实际父边。E/executor_adapter.py:45-52 将这些 rows 送入实际 fail 持久化。
- 该测试不是完整 formal，也不运行产品；临时目录由 :29-32 清理，因此本次没有一份永久保留的成功 fixture marker 可另行打开。证据是固定源码中的实际 JSON readback/assertions + 真实 native PASS，不伪称 reviewer 读到了仍存在的该 marker。测试未直接逐条 assert outer-write 共享 composition，但这一关系可由上述源代码构造与真实序列化路径确定。
- E/preservation.py:136-143 按 occurrence flatten；E/boundary.py:218,232-234；E/runner.py:329-333,524-537；E/external29_driver.py:249-280 均使用 occurrence merge/receipt transport，无恢复 r7 的文本去重。AR009 durability.py、artifacts.py 与 r7 字节相同；runner 的改动限于三处 causal.unique，原独占 seal/failure supplement、原 seal 绑定、不覆盖历史及 failure latch 未被放宽。

### 因果深度的限定

MAX_CONTEXTS_PER_OCCURRENCE=32（E/causal.py:12）。:66-69 与 :175-177 在超限时截断 contexts 并标 context_overflow；**没有截断 occurrence rows，也没有把同文 causes 合并**。该标记不是额外 acceptance gate，源码没有 overflow consumer，故不能叫“任意深度 lossless”。

本次实际嵌套 publication → adapter latch → receipt merge/driver → final serializer 是有限失败链：每层只追加对应 context；同一 signature 的重复 transport 直接返回；失败后不继续跨29门禁累计同一异常。就上述已发生且受控的写入/fsync/close组合，必要 inner/outer 关系在 cap 前建立，未找到可达的32层截断反例，不新增任意深度异常图契约。未知外部异常组任意嵌套、多路径任意重入不在本 scoped closure 内；不把测试 PASS 提升为任意图性质的证明。

## B8-B-1：邻接实际 preflight write fault 仍丢原原因（OPEN，交 parent 合并）

E/external29_driver.py:325-334 捕获原 strict/boundary 异常 original，并把完整 causal rows 放进局部 result；但 :335 `runner.put(run/'preflight.json',result)` 在保护 original 的 try 外。若此实际证据写入失败，:336-340 的 EngineeringPreflightBlocked 与 preflight_receipt 赋值不可达，向 formal :448-458 传播的只有新 write 异常。formal_failure_document :348-361 只读传入错误的 causal/receipt 属性，E/causal.py:87-122 不读取 Python __context__/__cause__ 来恢复这个局部 original。

因此原 preflight native/capture cause 和 ENGINEERING_PREFLIGHT_BLOCKED disposition 可从最终 FORMAL_FAILURE.json 丢失，尽管先前 marker 可能保有原诊断，且停止/失败仍保持。这是当前明确写入路径，不是新增未来图要求，也不是成功绕过。

Q/test_r8_transport.py:190-196 将名为 evidence-write-secondary 的 OSError 放进注入 strict_capture 的组合中；:199-218 的实际 preflight.json 写入仍成功。这证明组合进入 preflight 后的正常保存传播，不证明 preflight 回执自身写入失败的组合。结论来自静态可达性，**本 reviewer 未运行新 RED**。建议在已有授权修正范围保留 original/result，再把实际 put failure 作为关联 secondary 传递；不要求重跑产品/正式门禁。本项不撤销 B7-008-2 的限定闭合，但阻止把本分项当作整体 AR008 CLOSED 背书。

## 精确资格、producer 与快照

| 已保存执行 | 原生日志身份结果 | native/wrapper | before/after snapshot |
|---|---|---|---|
| red-predecessor-002 | 3 unique：2 ERROR、1 FAIL | 1/0 | 78，全部副本hash相等 |
| green-final-001 | 3 unique PASS | 0/0 | 78，全部副本hash相等 |
| qualification-003 integrated | 170 unique PASS | 0/0 | parent117，全部当前字节相等 |
| runtime-loader-002 | VALIDATION PASS | 0/0 | 119，全部当前字节相等 |

RED 中60个 executor 文件逐个等于 r7 实际 predecessor；RED/GREEN 相同测试体 SHA-256 `e447308b4ed7498102e1731e8235b3001666bbc342275b62d9915e0b95a321a9`。RED B7-008-2 是读回后 occurrence_id KeyError，不是 setup 失败；初始 red-transport-001 单独保留。GREEN 首条 unittest 中夹有 sanitizer JSON，随后独立行 ok；首次简单整行解析只得2条，已按原始 prefix/status 配对纠正为3条，不能将 parser 误差认定 writer 漏测。

本地 AST 从 Q 自身 class 定义重建170个 test identities，精确等于 qualification expected；从 qualification_contract 独立提取85 mandatory，完整包含且清单相等。原生日志与 result 顺序/身份/status、process control_statuses、raw/result hashes均相等；无 missing/unexpected/duplicates/FAIL/ERROR/SKIP。五 qualification dependencies 全部 hash 相等。

Q/build_integration_qualification.py:33-40 在运行前 discovery expected；E/coverage.py:121-181 的正式消费者强制 source、dependencies、native/process/result、mandatory expected、argv/cwd、unique 与 status 对账；E/qualification_contract.py:93-130 保留 invalid status、expected duplicates、missing/unexpected 和每个非PASS拒绝，并非只看170/PASS。

focused GREEN 之后 binding_contract.py/run_integrated_parent.py/run_source_bound_group.py 有变更，旧 source copies 原样留存；不能把 GREEN 的 wrapper 称为最终当前 wrapper。最终 qualification-003 的117 source map、parent before/after、当前 tooling、runtime source_binding 精确相等。parent/native/result hashes 相符。PID 是 writer-owned subprocess namespace-local PID，非 host PID/独立 OS attestation；loader validator 的 PID/namespace 与 parent receipt 相符。runtime-loader parent 自身 run_loader_parent_r8.py 不在其119份快照中（tooling+validator+binding）；其当前文件在 full manifest，不能据此追认其执行前自身源码已由该快照封存。保存 loader PASS 的精确范围是所示 validator/输入/源码和 native 回执，不冒充 reviewer fresh loader 或产品检验。

qualification-001 的167 PASS+3 ERROR、runtime-loader-001 的旧路径 guard 失败保留；修复后最终资格与 loader 新运行，不把失败改成成功。历史缺失来源保持 NOT_ESTABLISHED_NO_BACKFILL。

## AR007 finite graph、runtime binding 与身份用语

- 静态独立重建 actual entry 本地 import graph：39 nodes /125 edges，与 dependency 完全相等；8 parser packages /216 files 当前hash全部相符，四 source receipt hashes相符。只做私有清单摘要hash，不输出其正文，不推导新的 instruction selection。
- E/dependency_contract.py r8 diff 仅增加三条实际 helper edges 和 causal/formal serializer 调用检查；:166-192 保留 exact nodes/edges、unresolved=[]及真实 import graph 相等；:215-256 保留 helper/parser/prepared-candidate Vite 边界。没有以弱化检查修复 qualification-001。
- E/binding_contract.py:32 仅把精确 r7 evidence 根改为精确 r8 根；:23-25 的 absolute/resolve guard、:33 的config hash、strict schema、fixed candidate/tree/patch、:51 exact candidate-formal-002、source universe 和 qualification/dependency 绑定保持。
- **118 是 implementation source index（117 tooling + `.source`）；117 是 runtime source_binding 的工具文件数；119 是 loader snapshot（117 tooling + validator + binding）。** writer report 首段“loader…118 个当前实现文件”应改为这三个明确口径；不是存在一个118项 runtime tooling map。
- writer 字段 EXECUTOR_IDENTITY 明确标成“runtime binding SHA-256”，实际值为 `5728eafccf0f13665c963cdaf9c3773a7fe76450f5251c2047b33514881d4b20`。它是配置 binding 字节hash，不是另行发明的 source aggregate identity；本报告不生成替代 executor identity。
- qualification SHA-256 `8d908adca46c8481a3bad2603744f6a1601839c17b2b8e1889b362236d6c5155`；dependency SHA-256 `c9dd93afafa57e4c3f42a0530d64a55e272b8a17480f49b2fd7e24bff56bc048`；三者及当前绑定逐项验证相符。

## 完整性与产出

r7→r8 实际13项 added/changed，与 delta 每行 before/after/path 相等。source-index 的 r7/r8 完整映射相符。final patch SHA-256 `893f247589cadc932e4bdb18226347fd6e4dbd51d46407ce34cb7555d55ded56`。W/FINAL_MANIFEST.r8.sha256 的1879项全hash匹配，manifest SHA-256 `3845ff4761d54fc3b73bb0116e513b878c4121d1b32698bcb0d9ad1c85ba1a44`。

本次 implementation-r8 SOURCE_BEFORE.json / SOURCE_AFTER.json 完全相同。只创建本 part-b 的 EARLY_REPORT.md、STATIC_CHECKS.json、SOURCE_BEFORE.json、SOURCE_AFTER.json、本报告及 MANIFEST.sha256。部分工具输出截断后，相关 source/矩阵单独补读；未执行被审代码。Parent 应合并 B8-B-1，不以本 B7-008-2 scoped closure 或170 PASS代替整体符合性及 final independent acceptance。
