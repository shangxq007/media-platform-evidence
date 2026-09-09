# r2 实际 preformal 审查 — part-b

## 结论与权限

**AR007、AR008、AR009 仍 OPEN_PARTIALLY_RESOLVED；AR006 原 finding 为 RESOLVED_PRESERVED。当前不支持“八项全部符合、可据此进入正式”的结论。**

本报告是只读 advisory preformal，不是正式执行后独立最终接受。仅审查当前 `implementation-r2/tooling`、`RUNTIME_BINDING.candidate-formal-002.final-r2.json` 与 `qualification-003`，并保留 r1 part-b 限定结论。未运行被审实现、测试、反例、probe、preparation、baseline 或 formal；未创建正式 namespace，未编辑源码、产品或历史证据。本审查自身不消费正式预算，状态仍为 1/2。所有主动持久输出仅在 `preformal-review-r2/part-b`。

读取 Owner 原文、REPAIR_REVIEW_PACKET、旧 part-b 完整报告、writer r2 final report 与 matrix 后，按实际源码重新裁决；writer 126 PASS/source107 不是符合性证明。已读 qualification 测试源码仅用于判定证据范围，不执行测试。

## 已核对的现成证据与实际运行绑定

- final-r2 binding SHA-256：`c5f872ad3522de981370f2d8d214b1a16afe585bb75a6e3bbec4e0dc4cb47c68`。
- binding 和 qualification 的 source_binding 与当前 tooling 排除 outputs/__pycache__ 后的 **107 文件**精确相同；现成资格 `qualification-003`，其 5 个 dependency 文件 hash 相符。loader 返回的“6 文件 closure”包括 qualification 自身，不误称 6 个 dependencies。
- **126 expected / 126 unique expected / 126 actual / 126 native unique / 126 PASS**；无 actual duplicate，native identity/status 与 RESULT 精确一致，expected 集合相等。41 mandatory controls 从 qualification_contract AST 的固定集合取值，全部存在。PROCESS native_exit=0，raw_log 路径与 digest 相等。现成 argv 的程序、输出和 fixture 目录确实对应 qualification-003。详见 STATIC_VERIFICATION.json。
- owner/dependency/qualification/adapter/applicability/任务私有 map/inventory 的 binding hash 均相符；90 candidate source 的工作字节以及固定候选 Git blob 字节均与声明 SHA-256 相等；6 当前 helper 字节相符。instruction source 两份身份文档 hash 相符，逐包来源行与声明相符，eligible set 与任务私有 map 相等。只读取必要任务私有 provenance，未输出其正文、未读取共享 ledger/usage 正文、未使用凭据。
- 固定 candidate/tree/patch/parent/base 由 binding_contract.py:43-65 强制，run ID 精确为 candidate-formal-002。上述是实际绑定与存量材料一致性，不意味着正式路径已运行或依赖语义完整。

## B2-007-1 — HIGH：当前 consumer/source edge closure 仍未完全来源化

**处置：OPEN。** `dependency_contract.py:70-87` 现在真实读取候选与 helper bytes，:94-127 增加 instruction origin 字节及来源行核验；这是真修复，不复用旧“只 hash 四个 JSON、不读取源码”的结论。历史 PARENT_SOURCE_AFTER/SOURCE_BINDING_BEFORE 也已有显式替代裁决。

但 `qualification/build_dependency_evidence.py:28-51` 从旧 fixed 文件沿用 candidate/command/dependency 列表，仅把六个 external_helpers 行换成当前文件；:39-42 将 ledger_token_lines 直接写空，:60-69 直接声明 consumer/unknown 集合及三条边。`dependency_contract.py:67-82` 只检查自报 local/direct 集合是自报 universe 的子集，未从真实源码对账边；:128-146 对四文件 hash 加三个源码 substring 判定，并要求自报 unresolved_actual_dependencies=[]。读取字节本身不等于证明空 reader。

**当前可定位的不一致**：fixed `commands[*].external_helpers_after_documented_owned_to_H_rewrite` 仍定位历史 formal-tooling；validator :53-58 根本不读取该字段。实际 `runner.py:378-380` 的 FRONTEND_BUILD 必经辅助命令调用当前 `vite_resolution.mjs`，后者 :3-4 调当前 Vite resolveConfig；此 helper 不在六行 fixed helper universe，也未在三条 actual_execution_scope 边中说明。107 source hash 包含它，证明版本被 pin，但不是 reader/依赖边来源证明。`coverage.local_imports` 的 Python import census 同样不能替代明确辅助进程/JS 配置选择边的语义裁决。

旧 fixed boundary 仍明确排除 arbitrary/future readers、runtime binaries、transitive third-party bodies、dynamic paths；本报告**保留这些旧证据限制**，不要求任意未来插件普遍安全。要求的是把本次已存在且源码可达的 helper/配置/消费者边纳入有限实际来源图，精确连接当前路径、明确委托已有 runtime preparation 的边界，不以 `unresolved=[]`/固定 consumer 字段作为证明。现成 byte-valid 90/6/107 不能消除该差别。instruction provenance 已核对相符，不另凭空声称实际包选择已错。

## B2-007-2 — MEDIUM：强制身份/日志修复成立，完整 argv 对账仍缺失

**处置：OPEN_PARTIAL。** `qualification_contract.py:49-87` 已拒绝 invalid actual status、expected duplicate、actual duplicate、missing/unexpected、FAIL/ERROR/SKIP，并要求 passed 精确等于 expected。coverage.py:122 不再接受旧 external29 v1 分支；:150-161 解析逐身份原生 unittest 日志并拒绝重复、身份或状态不符。原 B007-2 的这些缺口可以关闭。

剩余 `coverage.py:145-149` 仅要求 argv 为 list、len>=3、argv[2] 为程序路径及包含 --output/--fixture-root；未校验 argv[0:2]、完整长度/参数形状、参数值、重复或额外 flag，也未将 --output 的值对账到本次 RESULT/log/PROCESS 目录及 fixture-root 绑定。builder :44-46 正常写入完整 argv 不能代替正式必经 loader 的完整核验。本次 qualification-003 的 argv 实际自洽，**不认定它被篡改或执行失败**；这是接受谓词静态缺口，未构造伪造 receipt。旧 adapter71/formal158/capsule13 与 34/4/10/27 等历史证据均仅保留原适用范围，不改称 fresh 产品资格。

## B2-008-1 — HIGH：adapter 主边界已 latch，但 gate 内部异常仍可后续接受

**处置：OPEN_PARTIAL。** 已闭合路径：

| 异常路径 | 当前源码与判断 |
|---|---|
| _require_live / state parse / identity | adapter.py:95-102 已移入 try，异常不可逆 latch |
| consume_for_baseline | :66-85 包围 consume 异常，durable marker 后才赋 attempt_id |
| Engine capture/evaluate/write | :95-105 → fail；boundary.py:217-229 先 private/public durable 后推进 session/previous usage/clocks |
| attach constructor | :36-41 包围 attach；构造期间 Engine binding 失败在返回对象之前终止，不认定存在可复用成功 adapter |
| driver observer boundary acquisition | external29_driver.py:69-117 包围获取并 latch |
| strict acquisition | :157-163 latching_strict_check 包围实际 strict 调用 |
| failure marker 再失败 | adapter.fail :109 先置 failed；_latch_exception :47-50 保持 true |
| formal setup/baseline exception | formal 外层 :296-303 在有 adapter 时尝试 fail，并退出；consume 先于 adapter，保留单次 namespace |

**遗漏是实际 graph seam**：runner.run_gate :333 的 check_execution_seal、:387 的 native observer、gate 内 capture/evidence 写入异常，在 :411-412 或 :442-443 转为 result=FAIL，未通知 adapter；随后 external29_driver.execute_actual_graph :236 返回后仍执行 :237 COMMAND_AFTER strict、:238 COMMAND、:239 GATE，直到 :244 才检查 result 并 stopped。例如 gate 内暂态 seal read/绑定异常恢复后，后续严格 endpoint 合法时，同一个尚未 latch 的 adapter 可以继续接受并提交 COMMAND/GATE 边界。这是源码明确顺序，不需要伪造 bundle，也未执行故障注入。

driver :240-242 自己捕获的非 latching 异常同样没有统一 adapter.fail。直接公开 attach_consumed_attempt 方法 :52-64 也未自包 latch，但正式构造调用已经包围，不把不存在的正式再次 attach 路径作为主要 blocker。

**重要保留**：:244 停止后续 gate，formal :281-287 仍禁止成功 FINAL/COVERAGE/SEAL；不宣称整场 FAIL 可以变 PASS。要求在 gate failure receipt/异常跨回 driver 时先锁死 adapter，再允许诊断性收尾；不得继续语义成功边界。现成 strict/transient-live/consume 控制只覆盖各自路径，不覆盖这个 gate 内部返回 FAIL seam。

## B2-009-1 — HIGH：run/strict/top-level 输出已持久化，gate namespace/sealed evidence 仍绕过

**处置：OPEN_PARTIAL。** 已关闭旧具体路径：

- runner.prepare :71-81 使用 ensure_directory 逐层 fsync 发布 run/runtime/init.d；consume_formal :49 在 marker 前同步 ROOT 到 run 的现有 task-local chain。
- strict_check :143-150 在 continuous 最终决定定型后使用 durable directory 和 file，旧“磁盘 PASS、内存 REJECT”的写入顺序在此处已修。
- coverage.put :11-13 → durability.exclusive_bytes；runner.put :26 委托它，因此 START、preflight、seal.json、FINAL_FAILURE、RESULTS 和 gate JSON receipt 文件均具 file + 直接父 fsync。
- private/public bookkeeping、policy、sequence consume、formal consume/failure、adapter failure 均调用统一 helper；部分已存在 consume regular file 仍阻止 O_EXCL 重用。failure marker 写不出不解除内存失败。

**仍有必需实际 call sites**：

1. `runner.run_gate :330` 普通 gate.mkdir；后续 durable receipt 仅 fsync 此 gate 目录，不 fsync 发布其目录项的 runtime/gates。prepare 预建 runtime/gates 不能替代后来每个 gate 子目录的发布。consume chain 在 gate 创建之前同步，也不能补未来目录项。
2. `artifacts.seal :29,33` 普通 mkdir sealed 与 open('xb') 写全部独立 evidence copy，无文件或目录 fsync；`finalize :72-79` 读回验证后直接将 gate result 设 PASS。`runner :415-444` 正式必经此处，包含 native receipts/log、COMPILE/build 输出、BOOTJAR 独立副本等必需证据。最后 fsync gate receipt 不会递归 fsync sealed 文件和 sealed 目录。
3. `runner.archive_xml :304-305`、`native_observe.run :267-292` 也保留普通 XML/native log 写入；当前独立封存复制链没有补足 durability。不是要求修改产品命令，而是外部证据发布调用点的已有契约。

所以统一 helper 与 top-level START/seal 文件已修不能推出全部必需 evidence durable。此为缺失崩溃保证的静态推导，未运行掉电实验，亦不声称每次崩溃必丢。修正范围可限定外部 gate/evidence publication 与相关实际调用点；保留 O_EXCL、独立副本、内容/来源 recheck，不弱化既有接受标准。

## AR006 回归与 native29

**AR006 RESOLVED_PRESERVED（原 finding 范围）**：formal parser :418 无 bundle/coverage/strict 注入；driver.boundary :95-110 提供真实 observer 数据与 evidence_dir；Engine :114 调实际 capture_bundle；formal :249/263-272 强制当前 binding、私有输入路径/hash 与实际 policy。内层 fixture 的 bundle 参数不是正式 CLI 接受路径。AR007 来源语义缺口不重命名为 AR006。

r2 matrix 与 r1 字节一致，SHA-256 `57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`。execution.py、bindings.py、matrix.py 对 r1 完全一致；runner.py 只新增 durability import 与 prepare 目录发布修正，run_gate/native command/timeout/接受语义源码未改。仍调用原 29-gate runner，不以 fixture 29 个空子进程替代。不存在本次新增 attempt-wide 3600 秒限制；8000/29 仍仅 EXPECTED。已有 freshness、COMPILE inventory、独立 artifact copy、frontend closure、static→resources→JAR、Lean 与隔离链不得因本报告要求被弱化。

## 审查边界与文件

报告不授权或执行 formal，不重新消费预算、不修改产品、不发布证据；未启动独立最终接受。已批准 ledger 捕获间 overwrite-restore/truncate-regrow 限制保持，不扩展到其它 protected 对象，也不列为新缺陷。

`PARTIAL.zh-CN.md` 为早期报告；`FINDINGS.json` 为四项具体 finding；`STATIC_VERIFICATION.json` 为原生/绑定/源码字节对账；`SOURCE_HASHES.before.json` / `SOURCE_HASHES.after.json` / `HASH_VERIFICATION.json` 为 scoped 完整性记录。初始 implementation-r2/writer-evidence-r2 snapshot 在源码审查前建立，扩展的候选、任务私有、来源与 r1 对比材料在纳入范围时加入；不宣称这是整个历史封存 manifest 的重新验收。

本 part 完成。需要继续修正的是上述实际有限消费者边、完整 argv 接受器、gate failure→adapter latch、gate/sealed evidence durable publication；修正后重新绑定受影响资格。不得用 writer 正常退出、126 PASS 或文件名 final-r2 代替这些接受结论。
