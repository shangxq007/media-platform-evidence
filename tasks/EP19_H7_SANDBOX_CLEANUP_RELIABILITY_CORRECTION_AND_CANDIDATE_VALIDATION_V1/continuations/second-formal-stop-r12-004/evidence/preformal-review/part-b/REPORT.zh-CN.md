# continuation-004 / preformal-review / Part B

状态：COMPLETE_ADVISORY；结论：AR006 保持已解决，AR007/008/009 尚不能声明全部闭合。不是独立最终接受，也不是启动 formal 的批准。源码定位均相对 `J/implementation/tooling/`，证据定位相对 J。

## 审查边界与方法

完整读取 `OWNER_AUTHORIZATION.verbatim.txt`，读取 writer 最终报告、符合性矩阵、final runtime binding、qualification-005 原生日志与两个结果/进程回执、实际 driver 及直接调用链，并回看 integration-review-002 两份报告及旧依赖声明。仅静态源码、JSON、字节哈希和原生日志身份对账；未导入或执行 executor，未运行测试、probe、preparation、baseline、formal 或产品命令。仅必要读取任务私有 map/inventory，未输出其内容；没有读取共享 ledger/usage。所有人工交付写入仅本 part-b。

正式预算按上下文为 1/2；本审查未消费尝试，也未重新检查正式 namespace 当前状态。产品固定候选、tree、patch 未修改。Owner 接受的 ledger 捕获之间 overwrite-restore/truncate-regrow 限制不作为缺陷；不新增全 attempt 3600 秒上限。

## 现成证据的实际对账

`STATIC_VERIFICATION.json` 是本次独立静态读取结果，不是重跑资格：

- qualification-005：107 controls，107 unique，全部 PASS；原生日志解析出 107 个 ok 身份，与 RESULT controls 精确集合一致；无 missing/unexpected/duplicate。
- 源码独立固定 `REQUIRED_AFFECTED_CONTROLS` 为 22 身份，全部在现成回执中；expected/mandatory 不再仅由结果总数替代。
- PROCESS native_exit=0，raw_log 定位与日志 SHA-256 一致；QUALIFICATION 的五项直接 dependencies 实际字节 hash 均匹配。
- tooling 106 个被绑定文件的当前全集，与 runtime final binding 和 qualification-005 的 source_binding 均精确一致。没有发现源 hash stale。
- runtime 的 owner/dependency/qualification/adapter/applicability/private-map/private-inventory hash 全部吻合；dependency 四个 source 角色的文件 hash 亦吻合。
- 私有 eligible map 身份集合及每包 canonical manifest hash 与 applicability 一致。六个旧 helper 摘要与当前同名 helper 字节 hash 本次比较一致。因此不指控本包现成回执伪造、helper 已变化或 map 被调包。

这些真一致性不自动证明下列接受谓词或来源闭包完整。

## B007-1 — HIGH：实际 consumer/source closure 仍是有限旧证据被提升为完整结论

依据：Owner 173–183、261–272；`executor/dependency_contract.py:15-24,27-69`；`executor/binding_contract.py:58-65,73-78`；`qualification/policy_builder.py:42-68`；writer `DEPENDENCY_BINDING.v2.json`、`INPUT_FIXED29_CONSUMER_BINDING.json`、`INPUT_CURRENT_APPLICABILITY.json`。

新的 validator 确实要求四类 source、精确消费者字段、动态 reader 空集合、29 个命令与 matrix 相同，修正了旧版本缺少 sources 默认为空的缺陷。但它只对四份文件本身 hash：candidate_sources 仅需非空，并检查自报 candidate/working_matches_candidate/ledger_token_lines；helpers 仅需非空及 ledger_token_lines=[]。没有读取 candidate_path/working_path 或 helper path，没有验证这些行的 candidate_source_sha256/sha256_before，没有独立构造或核对执行源身份全集与实际命令的依赖边。

现成 INPUT_FIXED29 是旧 `dependency-review/FIXED29_CONSUMER_BINDING.json` 的同 hash 支持材料（375dba8145c478b0e48bf76bdfb3090a7d3b27a096beaee845566cd803d93b25）；其 boundary 明说不覆盖 arbitrary plugins/readers、runtime binaries、transitive third-party bodies、dynamic paths 或 future K/tooling，且不是 formal readiness。六个 helper 行仍定位历史 formal-tooling，而不是当前 continuation-004。旧 dependency 的 sources 还包括 PARENT_SOURCE_AFTER 和 SOURCE_BINDING_BEFORE；新 required source universe 没有这两个证据。仅增加 `ledger_consumers=[bookkeeping_v3.evaluate_ledger]` 与 `unbound_dynamic_readers=[]` 不构成这些边的来源证明或缺边拒绝机制。

同类 eligibility 深层 provenance 缺口：applicability 的 instruction_source_bindings/selection_rule/每包 instruction_origins 不被 dependency validator 核验；policy_builder 验当前 map 的 manifest，却不独立验证选择来源全集。当前 hash/map 自洽已核对，但不能宣称已完成全部实际消费者与指令选择来源闭合。此结论不要求证明任意未来插件安全；要求对实际批准执行路径和已声明来源给出有边界的正面证明，未知实际依赖保持阻断。

修正要求：保留旧材料的原适用范围；从实际 current driver、命令、helpers 和已批准实际消费者来源构造并校验完整身份/依赖边；对旧来源遗漏给明确有证据的替代或不适用裁决。不能用新无 reader 声明替代。修正后的源码必须重新绑定资格。

## B007-2 — MEDIUM：强制资格校验仍有兼容分支及状态/原生日志一致性缺口

依据：`executor/coverage.py:119-147`；`executor/qualification_contract.py:30-61`；`qualification/build_integration_qualification.py:32-58`。

优点：新 v2 路径强制 22 mandatory identities，并核验 result.controls、expected、unique 和标准 FAIL/ERROR/SKIP/duplicate/missing/unexpected；不再是旧总数校验。

剩余静态路径：
1. coverage 接受 v1 和 v2，但 mandatory/identity reconciliation 仅在 v2 分支。runtime loader 只 pin qualification bytes，不强制 v2 schema；标准 binding builder 强制 v2，故现成 final binding 不走此兼容缺口。不能把 builder 的可选离线路径当 formal 必经校验的替代。
2. identity_accounting 未要求 actual 属于 PASS/FAIL/ERROR/SKIP，也未要求 passed 身份集合等于 expected；unknown actual 不进入任何拒绝状态集合，只要身份/行数相同，其 accounting.result 仍可为 PASS。expected 自身 duplicate 也没有在该 validator 独立拒绝（正常 builder 会拒绝）。这是静态谓词分析，未构造/执行伪造 receipt。
3. coverage 校验 PROCESS native_exit 和日志 hash，却不解析原生日志逐身份/状态，也不核验 PROCESS.argv 对资格程序及 PROCESS.raw_log 对 q.raw_log 的一致性。正常生成器生成的本次证据确实一致；必经接受器未独立保证该一致性。

处置 AR007：OPEN（显著修正，但来源闭包和全部强制路径未闭合）。现成 107 PASS 不被否定，不宣称运行过任何新的反例。

## B008-1 — MEDIUM：接受状态顺序修复，但 adapter 全异常 latch 尚不成立

依据：Owner 187–192；`executor/boundary.py:205-218`；`executor/executor_adapter.py:39-78,79-105,107-109`；`executor/external29_driver.py:65-75,175-194,227-250`。

已解决旧核心反例：Engine 先 write_evidence 完成 private/public publication，之后才提交 session、previous_usage、前次 wall/monotonic boundary。engine.check 的异常进入 adapter.fail；fail 第一条即 `self.failed=True`，failure marker 自身异常也不解除 latch。

尚漏异常边：RunAdapter.boundary 的 `_require_live()` 在 try 之外。state_path 的 is_file/read_text/JSON parse 或 attempt identity 绑定异常直接抛出，不设置 failed、不保存 failure。这之后若暂态 I/O 恢复，同对象仍可接受下一 boundary。consume_for_baseline 亦在 baseline 的 boundary try 之外，且在 marker durable write 完成前先赋 attempt_id。这些是实际 adapter 调用链，不是 bundle 注入 API。

实际 formal 外层的改进必须保留：图内任何异常使 stopped=True，跳过所有剩余 gate；结束处 stopped guard 禁止成功 FINAL/COVERAGE/SEAL。故不能复用旧报告“正式图捕获失败后仍继续成功 FINAL”的结论，亦没有证明正式入口整体 PASS 或自动重跑可达。图内 strict/observer 获取异常位于 adapter 外，外层虽然 stopped，却没有统一 adapter.fail；符合当前 formal 停止，但不满足 Owner 的 adapter 任一绑定/采集异常永久失败要求。fixture evidence-failure 只覆盖 engine write 异常，不能证明上述所有路径。

处置 AR008：OPEN / PARTIALLY_RESOLVED。修正要求：将 live-state/consume/binding 及正式 boundary 获取异常纳入统一不可逆 adapter latch，诊断持久化失败不能使之恢复；保留 formal stopped guard。未执行故障注入。

## B009-1 — HIGH：通用 durability 已修，但调用者预建目录仍绕过嵌套发布持久性

依据：Owner 194–199；`executor/durability.py:15-30,33-48`；`executor/runner.py:67-79`；`executor/external29_driver.py:46-55,101-110`；`executor/coverage.py:9-11`；`executor/boundary.py:36-54`。

已解决部分：通过 ensure_directory 新建的每层目录均 fsync 父目录和自身；exclusive_bytes 完整写入、fsync 文件、fsync 直接父目录；boundary private/public、adapter failure、formal consume、policy private 和 sequence durable 均使用此 helper。现有 consume 标记存在（包括空/部分 regular file）时，O_EXCL/exists 拒绝同 namespace 新尝试；failure marker 写失败仍保持当前 adapter latch。

剩余实际 formal 来源路径：runner.prepare 用普通 mkdir(parents=True) 创建 run 及 runtime 目录树，无对应父目录发布 fsync。consume_formal 后续 exclusive_bytes 看到 run 已存在，ensure_directory 不再 fsync 新建祖先的父目录；只 fsync marker 和 run，不能证明 run 在 continuation-runs、以及 outputs 祖先中的目录项已持久化。若崩溃丢失未持久 namespace 目录，现有 same-namespace exists guard 无法根据消失的 consume 文件记住消费。这是缺失崩溃保证的静态推导，不是已执行掉电实验，也不宣称常规重启一定会丢文件。

第二处独立可达缺口：strict_check 先普通 mkdir runtime/strict-decisions，再 durable 文件；helper 见目录已存在，只 fsync strict-decisions，不 fsync 将它发布在 runtime 的目录项。其 private/public bookkeeping 兄弟目录 fsync 不能替代本目录发布。

此外 coverage.put/runner.put 仍普通 open('x')，formal 的 seal.json、START、preflight、FINAL_FAILURE、RESULTS 等接受/失败相关输出没有统一 fsync。严格 boundary 两份证据的 helper 顺序已修正，但不能据此声称整个实际入口证据持久化流程统一完成。strict_check 还在 durable 之后才补写 continuous_* 并可能将内存结果改为 REJECT（101–110）；磁盘 receipt 不反映最终观察结果，应把最终决定与所需事件先定型再发布。这不被解释为总正式结果可 PASS。

处置 AR009：OPEN / PARTIALLY_RESOLVED。修正要求：在实际 namespace/strict-directory 创建处使用可验证的 durable publication，或正式 consume 前验证并同步完整所需目录发布链；所有必需接受/失败证据使用统一流程；不要只修通用 helper 而保留绕过调用点。

## AR006 回归与 native gate 保留

AR006：RESOLVED_PRESERVED（原 finding 范围）。formal CLI 在 external29_driver.py:359-366 仍无 bundle/coverage/strict 参数；65–75 由真实 observer 提供事件，Engine 110 调实际 capture_bundle。formal modules→binding_contract.load 固定候选/tree/patch/parent/base、exact run ID、matrix/inventory、source bytes；formal 212–220 验输入路径/hash再构造 adapter。内层 fixture 可注入不是实际 CLI 漏洞。AR007 来源语义缺口与 AR008/009 持久性不重新混成原 AR006。

Native29 保留：matrix 与 sealed integration-001 字节完全一致，SHA-256 `57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`；execution.py、bindings.py、matrix.py 对旧版无源码差异；runner.py 仅 Owner hash 改动。实际调用依旧 runner.run_gate，保留原 command rewrite、timeout、native observer、freshness/dependency、精确解析、COMPILE inventory、packaging/immutable artifact-copy 等接受链，不以 fixture 的 29 次空子进程替代产品门禁。没有新增 attempt-wide 3600 秒限制；bindings 中原有每门 timeout 代码保持，不据此重新解释原契约。8000/29 只在 summary 的 expected 字段，未变成实际 passed。

## 最终处置与交付

| AR | 本次处置 | 主要依据 |
|---|---|---|
| AR006 | RESOLVED_PRESERVED | 正式 CLI 不接受制造成功的摘要输入；强制当前来源绑定保持 |
| AR007 | OPEN | B007-1 实际依赖/eligible 深层来源未闭合；B007-2 必经身份/状态/日志校验缺边 |
| AR008 | OPEN_PARTIALLY_RESOLVED | engine 证据先于状态已修；live-state/consume 等异常未全部 latch；formal stopped guard 已修 |
| AR009 | OPEN_PARTIALLY_RESOLVED | helper 文件与目录 fsync 已修；预建 namespace/strict 目录及其他必需输出绕过 |

早期报告 `PARTIAL.zh-CN.md` 保留；完整报告为本文件。`SOURCE_HASHES.early.json` 记录早期已读源码；`SOURCE_HASHES.before.json` / `SOURCE_HASHES.after.json` 与 `HASH_VERIFICATION.json` 记录 scoped 来源哈希及审查结束再核对；`STATIC_VERIFICATION.json` 保存现成回执/source/matrix 的字节与身份对账。hash 清单不是整个历史 sealed manifest 的重新验收。

本审查完成，不是建议停止范围内修复；parent 仍应按授权修复这些外部实现遗漏并重新绑定受影响资格。当前不能把 writer “八项全部 RESOLVED”作为本 part 的接受结论。不发布、不改产品、不创建正式 namespace、不修改实现或 sealed 材料。
