# integration-001 只读集成复核：Part A

状态：COMPLETE_ADVISORY_PART_A。仅 advisory 静态源码复核，不是独立最终接受。

## AR001 — OPEN

外层确实补入全 Skills/Memory 递归清单、其他 strict inputs、native command 内递归 watcher 与祖先 watcher；因此原 beta/support.txt 持续正文变化不是仍完全漏检。未闭合的是跨整个 protected window 的 strict/ancestor 连续性：baseline native watcher 在 BASELINE 后关闭，之后每条 native command 各建各关；长期 V3 watcher 只有 skills root 与 eligible 包。strict_check 是 endpoint，不保存 .hermes 等祖先跨边界身份。parent_fd 只在单次读取内核对 dev/ino/mode，不能补偿命令间祖先变化；历史 protected inventory 不含 /、/home、/home/user、/home/user/.hermes。coverage 源码也明确声明命令间 gap。

- `integration-001/tooling/executor/coverage.py:50-61,88-96`
- `integration-001/tooling/executor/preservation.py:10-13,21-36,80-98`
- `integration-001/tooling/executor/native_observe.py:31-39,75-80,227-239,273-288`
- `integration-001/tooling/executor/external29_driver.py:81-118,142-158,167-180,199-218`
- `integration-001/tooling/executor/observe.py:119-127`
- `integration-001/tooling/executor/runner.py:320-334,381-384`

静态推导（未执行）：baseline native watcher 关闭后、下一条 native watcher 注册前，改变 skills 之上的 .hermes 祖先 mode（仍可读），不修改其子路径内容。长期 V3 没有该祖先 watch；下一次 parent_fd 将新 mode 当本次 wanted，strict rows 未包含该祖先，因而没有跨基线比较或连续事件证据。此为静态路径推导，未操作共享目录。
## AR002 — OPEN

外层没有恢复 V2 temp 生命周期：V3 路径提前返回委托类别，绕过可见 temp 元数据检查；resolve_bookkeeping 对 V3 直接返回，原 V2 cookie 双向配对逻辑不执行。连续 V3 reducer 仅凭类别及无其他 reasons 即全量 resolved。

- `integration-001/tooling/executor/native_observe.py:59-61,97-109,164-175`
- `integration-001/tooling/executor/observe.py:39-48,68-104`
- `integration-001/tooling/executor/bookkeeping_v3.py:495-505`
- `integration-001/tooling/executor/external29_driver.py:74-79,85-103`

静态推导（未执行）：精确 temp 名在 root 创建后移出至不受保护目录，或外部文件 MOVED_TO exact usage：合法 endpoint 和最终 temp 缺席不能证明配对来源；不配对 cookie 不被 V3 拒绝。可见 temp 的 mode/uid/gid/dev/nlink 检查亦被委托绕过。
## AR003 — OPEN

formal 创建 RunAdapter 时未传实际 capture 时间窗；Engine 默认结束为 datetime.max，检查记录时间仅依赖该固定窗。time.time_ns 被记录或混入 capture ID，不被用于实际捕获上界或跨捕获 wall-clock 回退校验。

- `integration-001/tooling/executor/external29_driver.py:196-208`
- `integration-001/tooling/executor/executor_adapter.py:38-42`
- `integration-001/tooling/executor/boundary.py:93-125,157-162`
- `integration-001/tooling/executor/bookkeeping_v3.py:368-382`
- `integration-001/tooling/executor/capture.py:101-108`

静态推导（未执行）：在当前年份捕获合法 2099 年 ts 的新 ledger 行，若其余 schema/manifest/事件均满足，2099 小于 datetime.max，因此此时间判定通过。没有执行此构造。
## AR004 — OPEN

新增与历史 ledger framing 均未显式拒绝 CR；splitlines(keepends=True) 的 CRLF 行通过 endswith(LF)，line[:-1] 仍含 CR，JSON 解码允许该尾随空白。外层将 ledger 完全委托 V3，不增加 framing 检查。

- `integration-001/tooling/executor/bookkeeping_v3.py:181-195,416-430`
- `integration-001/tooling/executor/native_observe.py:59-61,164-166`
- `integration-001/tooling/executor/external29_driver.py:85-103`
- `integration-001/tooling/executor/bookkeeping_v3.py:81-103`

静态推导（未执行）：满足其余要求的 JSON record + CRLF，在当前 framing/strict_json 链路不因 CRLF 被拒绝；不是已运行 parser 试验。
## AR005 — RESOLVED

针对原 finding 的“合法 usage 变化后不变边界被误拒绝”已修复：Engine 保存 previous_usage 的真实 hash/metadata，事件要求比较前次成功 capture，而 old_strict 仍比较原 policy baseline。formal 全程复用同一 adapter/Engine，command 后紧接 gate 可保持不变且不要求新 usage 事件。仅关闭原误拒绝，不意味着整个 usage 语义/证据持久性已验收。

- `integration-001/tooling/executor/boundary.py:104-105,121,129-142,168-170,185-189`
- `integration-001/tooling/executor/bookkeeping_v3.py:311-353`
- `integration-001/tooling/executor/observe.py:81-83`
- `integration-001/tooling/executor/external29_driver.py:174-180,208-218`
- `integration-001/tooling/executor/executor_adapter.py:85-91`

## 边界
未执行测试、探针、正式准备或正式门禁；未读取共享 usage/ledger/lock。没有产品或 sealed source 修改，没有 replacement candidate。正式预算仍按上下文为 1/2；本复核没有消耗尝试。87 资格回执不是穷尽覆盖证明；1357 manifest entries 是 parent 已核对的上下文，不冒称本复核重新验证全部。Ledger 隐蔽 overwrite-restore/truncate-regrow 是 Owner 接受的观察限制，不列作缺陷；不要求 3600 秒上限。历史 writer NOT_ESTABLISHED。

## 契约依据与证据边界

Proposal 路径相对于 K 的父目录（前一 continuation），Owner 路径相对于 K。当前 Owner 决定优先于历史 proposal 未批准状态及 3600 秒上限。

### AR001 契约
- `OWNER_DECISION.verbatim.txt:严格正文/Memory 保护、规定祖先身份、覆盖无缺口`
- `continuation-review-001/rejection/NARROW_RULE_PROPOSAL.json:31,36-45`
- `continuation-review-001/ledger-proposal/LEDGER_CONTRACT_PROPOSAL.json:203-204,243-259`

历史 task inventory 补证：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/PROTECTION_SCOPE.json`，JSON pointer `/protected`；不含 /、/home、/home/user、/home/user/.hermes；只读取历史 task evidence，未读共享目录。

### AR002 契约
- `OWNER_DECISION.verbatim.txt:B 保留精确临时文件规则`
- `continuation-review-001/rejection/NARROW_RULE_PROPOSAL.json:33,59`

### AR003 契约
- `OWNER_DECISION.verbatim.txt:C.9 时间校验；拒绝新增 3600 秒上限`
- `continuation-review-001/ledger-proposal/LEDGER_CONTRACT_PROPOSAL.json:147,330`

### AR004 契约
- `OWNER_DECISION.verbatim.txt:C.9 严格 UTF-8/JSONL`
- `continuation-review-001/ledger-proposal/LEDGER_CONTRACT_PROPOSAL.json:208`

### AR005 契约
- `OWNER_DECISION.verbatim.txt:B 合法 V2 变化接受，所有后续边界同规则`
- `continuation-review-001/rejection/NARROW_RULE_PROPOSAL.json:37-39`

静态审阅 test_external29_integration.py:26-27 及 external29_driver.py:272-293：allowed fixture 先合法改变 usage，后经重复 command/gate；本复核未重新执行，不把 reported 87 receipts 当成正式路径穷尽覆盖。

## 只读保全与交付

对 71 个 integration 工具源码以及指定授权/评审/提案/历史 scope 输入，共 78 个文件做 scoped SHA-256 before/after；差异 0。详见 `SOURCE_HASHES.before.json`、`SOURCE_HASHES.after.json`、`HASH_VERIFICATION.json`。不是对全部 sealed manifest 的重新认证。

结果：{"RESOLVED": 1, "OPEN": 4, "NOT_ESTABLISHED": 0}。所有五条均完成 source disposition；AR006..AR010 不在本 Part A 范围。没有复用失败 delegation 的完成结论；无本次工具阻塞。
