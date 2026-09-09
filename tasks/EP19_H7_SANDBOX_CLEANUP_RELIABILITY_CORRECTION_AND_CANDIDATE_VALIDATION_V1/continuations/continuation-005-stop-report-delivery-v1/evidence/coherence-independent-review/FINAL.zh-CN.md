# coherence-implementation-v1 独立实现复核最终报告

## 精确裁决

**REJECTED — 存在四项有限、可定位的实现阻断，不能给出 scoped implementation PASS。**

这不是新 review program，也不新增 acceptance gate。裁决仅针对 `coherence-implementation-v1` 的 `final-006` 实现及其既有证据。集成与真实 readiness 继续为 **BLOCKED**：实际独立控制面候选已被 `control-plane-independent-review/FINAL.zh-CN.md:3-7` 明确裁决为 `REJECTED`，不是“仅未安装”；其源码、contract、自报 PASS 或 readiness 声明均不得作为可信控制面证据。本复核不授权修改实际共享 canonical controller。

## 有限实现阻断

### COH-IR-01：当前交付精确绑定的是已被否决的第二控制机制

`INTEGRATION_REQUIREMENTS.json:16-35` 仍要求被否决候选的实现摘要 `b8c1d9…bd4a`，consume 要求在 `:36-49` 再次固定同一摘要；既定父命令还在 `PARENT_SEQUENTIAL_COMMANDS.md:17-31`、`:36-55` 把 contract/runtime binding 指向独立的 `scripts/ep19_successor_acceptance.py`。而控制面独立审查已确认 actual canonical executable 仍是共享 Skill 的 `canonical_publication_control.py`（`control-plane-independent-review/FINAL.zh-CN.md:9-15`），并证明该独立 writer 与原 reader/lock/journal 不一致（`:19-29`）、direct-FF 未接入原 slot 协议（`:31-40`）、证据可自报（`:42-48`）、handoff 会固化第二机制（`:50-54`）。

因此，`binding_contract.py:73-76` 对一个文件做 SHA-256 并不能把它提升为 actual canonical controller；`build_eligibility_contract.py:46-52,78-80` 和 `build_runtime_binding.py:71-80` 只传播该文件摘要。当前交付的控制面身份链本身已经失效，不能按 writer 报告的“reconcile 后继续”处理。

### COH-IR-02：关键 PASS 回执仍是字段自报，真实 admission 可被伪造后触发消费

`eligibility_coherence.py:218-223` 对 implementation review 只检查两个字符串；没有要求 machine schema、reviewed source/diff/dependency hashes、review scope 或独立 reviewer route。`eligibility_coherence.py:226-258` 对控制面 admission evidence 只解析调用者文件中的固定字段和布尔值，没有读取/核对 queue、ledger、slot、journal 或 actual canonical controller 产生的原始回执字节。`:261-289` 的 consume validator 同样只检查自报字段、非空 transaction/idempotency 字符串及一个 control-evidence 摘要，不核验真实事务/readback，也不把 consume 事务绑定到具体 `ADMISSION.json` 字节。

更直接地，`eligibility_admission.py:26-54` 对既存 `ADMISSION.json` 仅检查顶层字段和 comparison 的 `result=PASS`、phase、complete、空 differences；它不重新计算 comparison，不要求 comparison schema/contract/capture identity，不检查 expected/actual 身份相等，也不要求私有 capture 与公开 comparison 的真实持久化同源。`external29_driver.py:660-687` 随后接受这些文件并立即调用本地 consume。故一个字段自洽但未实际运行 admission 的 JSON 可以越过“失败时零消费”边界。`integrated-qualification-005` 的 fixture 本身使用手工构造的 review/control/consume PASS（`test_eligibility_coherence.py:72-84,258-270`），没有覆盖真实 receipt bytes/readback 的负例。

这与“real receipt checking / no fabricated PASS”直接冲突；控制面候选的 `REJECTED` 使这一缺陷不能再以“精确实现摘要可信”来补足。

### COH-IR-03：精确有限输入没有在最终 contract/runtime consumer 中闭合，允许替换或缩小 protected projection

有限输入生成物本身记录了 7 packages、107 members、15 instructions、105 exact reuse、2 accepted changes（`coherence-private-v1/candidate-002/INPUT_BUILD_RECEIPT.json:9-23`），接受决定固定三份输入及 SHA-256（`input-semantic-review/FINDINGS.json:77-92`），并明确要求后续消费者使用该精确决定而非“文件存在即绑定”（`input-semantic-review/FINAL_REPORT.zh-CN.md:41-42`）。

但最终 builder 没有落实这个不可替换约束：

- `build_eligibility_contract.py:27-39` 接受任意调用者路径的 map/inventory/instruction/semantic 文件；`:56-71` 直接传播内容和一个调用者提供文件的 hash，没有核对 `final-006` dependency 中的精确 source path/hash，也没有强制 7/107/15 或精确三项 accepted input。
- 通用 `validate_contract` 只要求 package 数在 1..128、manifest 每包不超 4096，并验证内部投影一致（`eligibility_coherence.py:139-187`）；它不固定本候选的 package/member/instruction 数或名称。
- `build_runtime_binding.py:48-50` 只在调用者提供的 applicability/map/inventory 三者之间核对摘要；`:55-60` 只把 contract 核到 candidate/attempt。虽然 `dependency_contract.validate` 会验证 `final-006` 中记录的精确 sources，代码没有要求这些 sources 就是当前传入的 applicability/map/inventory/semantic/contract 来源。`policy_builder.py:43-70` 也只做同类内部 provenance 与 package-name/root 比较。

因此，可另造一个内部自洽、范围更小的 map/inventory/applicability/semantic 文件组，同时让独立的 `final-006` dependency 验证原 candidate-002 文件；builder/runtime 仍可接受替代组。admission 随后只捕获替代 contract 的投影。这既未真正消费精确有限语义接受，也可弱化 protected scope。

### COH-IR-04：真实 admission 输出路径没有受任务私有范围约束

真实 CLI 对 `--output` 只声明为任意 `Path`（`external29_driver.py:909-913`），`eligibility_admission.py:57-63,77-93` 将其绝对化后直接作为私有/公开比较和 `ADMISSION.json` 的父目录，没有验证它属于 run 或 `coherence-private-v1`。底层 `durability.exclusive_bytes` 会创建缺失的祖先目录（`durability.py:40-50,81-97`）。只要 OS 权限允许，真实 admission 可在任意可写位置创建文件，包括受保护输入树；既定父命令给出的安全路径不能代替消费者端 fail-closed 约束。

## 已支持但不足以翻转裁决的部分

- admission 与 formal policy 确实共享 `eligibility_coherence`：admission 在 `eligibility_admission.py:63-80` 验证 contract 并捕获，formal policy 在 `policy_builder.py:65-83` 用同一 comparator 对 post-consume capture 判定。
- 正常 admission 路径在写回执前两次拒绝已有 formal/baseline/START 标记（`eligibility_admission.py:70-82`），自身只写 coherence evidence 和 admission receipt（`:77-93`）。但 COH-IR-02 使 formal 对“实际执行过该 admission”的证明不成立。
- formal 的本地顺序是先写 global ordinal 3、history `2/2`、new `0→1` 的 `FORMAL_ATTEMPT.json`（`external29_driver.py:49-66`），再建 policy，并拒绝复用 admission capture ID（`:686-707`）。该本地编码不能替代已被否决的全局控制面事务。
- comparator 记录同次 capture 的 expected/actual、phase/time、完整性、128 条差异上限及截断信息（`eligibility_coherence.py:329-417`）；private/public 两个 sink 独立尝试，保留 primary reject 与 secondary persistence errors（`:420-450`）。这部分实现及 `test_eligibility_coherence.py:175-211,240-256` 的 source-bound 负例受支持。
- 当前 `integrated-qualification-005` 记录 191 tests、191 unique、0 failure/error/skip/duplicate，且 source binding stable（`integrated/QUALIFICATION.json:931-933`，`integrated/RESULT.json:1853-1860`）；`final-006` patch 只新增 12 个 `test_` identity、没有删除/改名 `test_` identity，mandatory set 在 `qualification_contract.py:4-111` 固定为 106。因此现有静态证据支持本次快照的 179+12 与 94+12 记账，不把它提升为真实 readiness。
- 精确输入语义接受本身有效且保持 task-only：`input-semantic-review/FINAL_REPORT.zh-CN.md:3-14,35-42`。问题是 COH-IR-03 所述最终 consumer 没有把它不可替换地闭合。

## 状态与停止边界

- 本审查未运行 test、loader、probe、prepare、admission、formal 或产品门；未访问网络、凭据或 live state；未安装、修复或写共享 Skill/Memory/产品；未消费 formal 预算。
- 历史 formal 保持 `2/2`；新增预算保持恰好 `1 total / 0 used`；下一全局 ordinal 仍为 3。不得依据本报告执行 admission、consume、formal、slot、direct-FF、publication 或 closure。
- 本裁决不接受、安装或修复被否决控制面候选，也不授予任何人更改 actual shared canonical controller 的权限。
- 精确 disposition 到此停止：`coherence-implementation-v1/final-006 = REJECTED`；`integration_ready=false`；`formal_ready=false`；`real_readiness=BLOCKED`。

