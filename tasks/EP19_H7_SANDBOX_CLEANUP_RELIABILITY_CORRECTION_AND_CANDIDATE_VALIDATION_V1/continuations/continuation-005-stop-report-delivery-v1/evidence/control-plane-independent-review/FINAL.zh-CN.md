# EP19 控制面独立技术审查最终报告

## 结论

**REJECTED — 存在有限且实质性的控制面合规阻断。** 不批准 `control-plane-repair/parent-handoff/AFTER_INDEPENDENT_REVIEW_ONLY.sh`，不授权安装、live successor 登记、formal 消耗、slot 操作、direct-FF、publication 或 closure。

这不是泛化的新审计范围。结论只针对既有 writer contract 要求的原控制面单机制、queue/ledger/slot 一致性、真实 evidence 消费、direct-FF 精确例外和 handoff 安全。固定候选身份本身没有被本审查否定；但候选资格没有成为 live 安装事实。

## 已确认的静态事实

- 实际 canonical executable 仍是共享 Hermes Skill 的 `canonical_publication_control.py`，当前 SHA-256 与 preserved predecessor 同为 `6c30fa0a6b43ed07595f53db1fb53eea914ae64c7ebc98435bc80816c6275362`。
- 原根的拟安装路径 `scripts/ep19_successor_acceptance.py` 和 `contracts/ep19-successor-acceptance-v1.json` 均不存在；GREEN 未安装。
- live queue/ledger/slot SHA-256 分别仍为 `932d2aa25537bffde4a1e67136caea81a3e7890031940f4ce882276dae2557bc`、`59ca64f07916713d979ba16c100e040c93a5a9b5cc26b04376ee925de8b20348`、`7fd276cd37129b13cef92510fa4ccafb0b6e8f5125d045cccc333a914fce863d`；successor 数为 0，旧 EP19 仍为 old86d6 / `RELEASED_FAILED` / `PUBLISHED_POST_PUBLICATION_SANITY_BLOCKED`。
- contract 固定 a298 candidate/tree/parent/patch，预算为历史 formal 2/2、新增 1/0，产品 3/3、新增 0；这些声明与 Owner packet 一致，且本审查未消费或改变预算。
- 父任务声明的 69 项 `control-plane-repair/MANIFEST.sha256` 核验结果被接受为输入；该事实不能替代下述语义/call-chain 合规。

## 实质阻断

### CP-01：新实现构成未协调的第二 writer，原 reader 不会对 partial transaction fail closed

GREEN 在 `ep19_successor_acceptance.py:124-140` 自建 `.ep19-successor-acceptance.lock`，并在 `:245-305` 以 journal → queue → ledger 顺序提交。实际 predecessor 的 `QueueControl.load/transition`（`canonical_publication_control.py:345-404`）既不取得该锁，也不读 ledger 或 `.ep19-successor-acceptance-recovery.json`；它会直接读取或覆盖 `queue.json`。原 CLI 的 acquire/freeze 路径还会在 slot 操作、queue transition、字段补写之间分别落盘（`:893-928`）。

因此：

- 两个 `SuccessorAcceptanceControl` 实例之间的测试串行化成立，不代表与实际 `QueueControl` writer 串行化；原 writer 可在 GREEN load 与 replace 之间写入并被覆盖。
- `AFTER_QUEUE_WRITE` 后 GREEN 自己的 `inspect()` 会看到 journal 并拒绝，但原 `QueueControl.get/load` 不会；partial queue 可被原 call chain 消费。
- GREEN `inspect()` 只比对其自身 contract-version events 和 `APPLIED_TRANSACTIONS`（`:343-364`）；原 `QueueControl.transition` 既不记该 transaction 集，也不追加 ledger，因此不能证明整个原 call chain 的 queue/ledger coherence。

这违反“原单一控制机制”“复用/补全同一 locks/version protocol”和 partial/uncertain 对所有原 reader fail closed。

### CP-02：direct-FF 例外只有声明和 closure payload，没有接入原 slot/publication 协议

contract 中 a298 candidate/tree 的静态绑定是精确的；但运营链不成立：

- 原 `SlotControl.authorize_publication`（predecessor `:523-588`）只签发 `EXACT_NORMAL_PUBLICATION_ONLY`，要求冻结的 integration、Parent 1/Parent 2 两父协议。
- GREEN 不读取 `slot.json`，不调用/扩展 `SlotControl`，也没有从 engineering acceptance 经 QUEUED/slot/出版/readback 到 CANONICAL 的 direct-FF transition。
- GREEN closure 仅接收调用者提供的 `SLOT_HOLDER`、`FRESH_MAIN_IS_ANCESTOR=true`、`NO_RACE=true` 和 `CANONICAL_READBACK.RESULT=PASS`（GREEN `:620-645`）。
- GREEN 测试 `test_ep19_successor_acceptance.py:249-254` 直接改 fixture queue，把 successor 设置为 `CANONICAL` 和 `PUBLISHED`；这正好绕过了待证明的实际 call chain。

所以例外虽在字段上 candidate-bound，却不是原 slot/state protocol 中可执行、可验证的 candidate-bound exception；现有 receipt 也不足以证明实际 fresh-main ancestry/no-race/readback。

### CP-03：acceptance 是可自报的 PASS，不是对 evidence bytes 的核验

`_evidence_pass`（GREEN `:101-109`）仅要求 result/acceptance 字符串、非空 path 和 64-hex 摘要；它不检查路径是文件、不读字节、不比对 SHA-256，也不解析 receipt 的 candidate/gate/native exit/actor 语义。`record_formal_result`（`:482-525`）和 `record_engineering_acceptance`（`:527-575`）同样只检查 path/hash 语法。

测试明确证明的是这一弱语义：`test_ep19_successor_acceptance.py:224-246` 使用不存在的 `evidence/*.json` 与 `"1"*64` 至 `"6"*64`，仍在 `:301-329` 得到成功 closure。因此 10/10 GREEN 只能证明自报 payload 被实现接受，不能作为真实 formal、29 gates、seal、independent engineering review、canonical readback、sanity 或 independent closure evidence。

独立性也未由 receipt 建立：closure 只比较三个 actor 字符串不相等；handoff 只计算调用者给定 review 文件的 hash，不解析其 machine decision、review scope、reviewed source/contract hashes或 reviewer route。把环境变量设为 `APPROVED` 可以覆盖文件正文中的拒绝结论。

### CP-04：handoff 会无条件安装第二机制，覆盖保护和端到端幂等均不成立

handoff `:46-48` 无条件创建原根 `scripts/`、`contracts/` 并以 `install` 覆盖目标；没有“目标必须 absent”或“目标必须等于已知 before/相同 bytes”的 compare-and-swap。两文件也不是成对原子安装；资格失败会留下已安装的部分状态。更根本地，这两个原根路径不是 actual shared Skill executable 的原位置，安装它们会固化 CP-01 的第二机制。

live 登记的 key 在 GREEN writer 内可 replay，但 handoff 本身不可 replay：成功登记后的再次执行会在 `:58` 因 successor count 必须为 0 而退出，尚未到 `register-successor` 的 idempotent replay。这不能安全覆盖“登记已提交、脚本在 inspect/readback 前中断”的典型不确定状态。

## deny 证据与唯一必要管理动作

静态包内唯一可定位的实际拒绝回执是 `green/results/handoff-guard.exit-code.txt` 的 `64` 和相邻 stderr 的 `independent technical review approval is required`。它只证明缺 review 环境变量时脚本自己的 guard 拒绝，**不证明**原根或共享 Skill 写入会被操作系统、ACL 或 sandbox 实际拒绝。

writer 报告中的 managed-sandbox 描述、uid/gid/mode 以及未附原始回执的 `/tmp` cleanup 叙述都不能提升为“实际安装被拒”。本审查不建议重试、sudo、chmod、换 wrapper 或其他 bypass。

当前明确有效的 deny 是权限边界本身：本任务禁止修改共享 Skill，而 actual executable 就在该共享 Skill。唯一必要管理动作是：**停止并废弃当前 handoff；由 Owner/共享 Skill 管理者显式另行授权一个有权维护 actual canonical controller 的执行者，在 shared Skill 的原 `canonical_publication_control.py`、其 protocol/test 中完成下列同机制修正。** 这不是对当前脚本的重试，也不是授予 bypass。

## 有限再提交条件

1. 在 actual canonical controller 内合并 successor/acceptance；所有 queue/ledger writer 与 reader 使用同一 state transaction lock、版本前置和 journal fail-closed 语义，并定义与既有 slot lock 的一致顺序。不得保留独立 `ep19_successor_acceptance.py` writer。
2. 在原 `SlotControl`/CLI 中实现 a298 专属 direct-FF exception 分支；必须从真实 slot holder、精确 candidate/tree、fresh-main ancestry/no-race receipt、canonical readback推进状态，且不得放宽其他候选的默认两父协议。
3. 所有 formal/gate/seal/review/readback/sanity/closure receipt 必须实际读取文件、核对给定 SHA-256、解析 native/acceptance/candidate/gate/actor 语义；独立 review machine decision 必须由脚本解析，不能由环境变量自封。
4. 替换 handoff 为 expected-before/absent-or-identical 的安全安装和真正端到端可重放流程；中断后相同 key/timestamp 能 inspect/recover/replay，不覆盖未知目标 bytes。
5. 用 actual `QueueControl` + `SlotControl` + 合并后的 acceptance consumer 做 source-bound synthetic integration tests，覆盖跨原 writer 的并发、partial journal 对原 reader 的拒绝、direct-FF 例外与默认两父路径隔离、真实 receipt bytes/digest、handoff 中断重放。纠正后回到本次既有独立技术审查关口进行常规 Sol 复核；这不是新增 ledger、gate 或 review round。

在以上四类实现/交付修正及同一既有审查关口复核完成之前，当前机器判定保持 REJECTED。本报告不要求产品/formal/网络执行，也不授权 live 操作。

## 本审查未做事项

未运行任何测试/probe/product/formal；未执行 handoff；未安装；未写 live queue/ledger/slot；未获取 slot；未读写凭据或网络；未修改共享 Skill/Memory；未修改实现。只新增 `control-plane-independent-review/` 报告、machine verdict 与 hashes。
