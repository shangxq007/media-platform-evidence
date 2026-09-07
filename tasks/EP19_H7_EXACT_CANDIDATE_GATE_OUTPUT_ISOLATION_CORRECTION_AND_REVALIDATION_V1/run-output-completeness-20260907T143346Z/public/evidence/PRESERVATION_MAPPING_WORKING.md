# 保全适用性工作映射（readiness 前，不是独立接受）

任务：EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1
续行：RUN_OUTPUT_ISOLATION_AND_ARTIFACT_COMPLETENESS_CORRECTION

本表只解释现有要求与本轮授权的路径角色绑定。尚未对未完成的新 executor 宣告符合。所有代码行号以原任务根为基准；新版本的实现行号和资格证据在 readiness 时追加，不回写历史。

| 原始要求/来源 | 受保护角色/路径 | 现有观察/拒绝 | 本轮验收所需证据 |
|---|---|---|---|
| inputs/original-shadow_monitor.py:29–31；owner-clarified-execution-20260907T1120Z/OWNER_DECISION.txt:121–125 | 新 run/backend 和 candidate frontend 是 PRIMARY；canonical 是另一个受保护角色，不能混称 PRIMARY | 原 owned/observe.py:59–64 对 protected、Git metadata、非声明仓库写事件拒绝；端点相等不抵消事件 | 新 run exact Git bytes/modes/index/HEAD/tree；实际 watch scope；命令事件与端点；无 prohibited event |
| inputs/MONITOR_CONTRACT.txt:10–12；OWNER_DECISION.txt:143 | canonical .git/index、既有对象/pack/HEAD/refs；旧失败 checkout | canonical index 内容及既有捕获元数据继续严格；不得套用 SHADOW index exception | 内容 hash 与 dev/ino/mode/uid/gid/size/mtime/ctime/nlink，实际事件；历史 staged semantics 仍 NOT_ESTABLISHED |
| inputs/original-shadow_monitor.py:17–21,33–38；OWNER_DECISION.txt:127–148 | 仅新 run 的 disposable SHADOW；仅三条 jooq authority files 和 index/index.lock 条件例外 | 原始 staged-entry reducer；HEAD/refs不变；undeclared/unclassified拒绝；最终候选内容一致 | 真实 before/after entries、digest、events、三项负控、完整最终内容；接受函数重算 reducer，不接受 pending |
| qualification/CONTINUATION_PRESERVATION_CONTRACT.md“任何观察到的 IN_ATTRIB 仍拒绝，Skill 使用元数据没有例外” | /home/user/.hermes/skills 与 /home/user/.hermes/memories；指令正文、.usage.json、目录 metadata分开报告 | 原 owned/observe.py:59 对指令目录事件拒绝；原 owned/coverage.py:38–42 捕获完整 instruction 集合 | 正文/运行时文件/目录变化分别列账；不排除 .usage.json，不刷新 expected hashes，不用停止后 reload 推断早期写者；正式 sealed run 内不调用 Skill 工具 |
| OWNER_DECISION.txt:165–170,194–198；最新 Owner §§4–6 | versioned helpers、imports、矩阵、契约、instrumentation、parser dependency bytes | 封存执行输入；与 declared runtime outputs 区分 | 完整输入 manifest、版本 diff；运行前后 seal核验；未知 drift直接拒绝 |
| OWNER_DECISION.txt:37–46,171；原 PROTECTION_SCOPE.json.cross_lane | refs/heads/agent/frontend-wave2-product-ux-v1 及已列出的 exact refs/logs/worktree metadata；不测试或冻结其开发源码 | 原 owned/observe.py:53,90–105 精确例外与 transient lock 条件；不是任意 canonical metadata豁免 | paired exact target更新、锁最终缺失、commit解析；不要求该开发 HEAD/index/worktree固定 |
| owner-clarified-execution-20260907T1120Z/ENGINEERING_MAPPING.md:3,14 | 新增 shared loose objects 的既有条件映射 | 当前实现原 owned/observe.py:106–134要求 exact frontend ref可达、zlib完整、Git对象hash、非symlink；现存metadata仍strict | 保留已有版本间解释差异：旧契约写pending，后续mapping明确 supersedes该解释；不据本次检查自行扩大例外或归因 writer。若资格/来源不能绑定，readiness拒绝 |
| 最新 Owner §§4–7 | 新 run checkout/build/cache/tmp；每 gate独占复制证据 | 旧 mutable artifact binding 已被采纳为待修正缺陷，不能沿用作符合性证明 | A/B fixture、独立inode、copy hash/size、run/candidate/producer绑定、后续篡改/删除拒绝；compile task graph和asset closure必须参与PASS；JAR副本复验 |

## 历史证据边界

RECOVERY.json 已验证原 public/MANIFEST.sha256 为 78ddad64194ad9fe9e10359716e55bf76231f27992ead3f06198cb3e42990425，88 个 payload 成员全匹配。实际交付文本未发现字面量 PASS=***，因此未改原包。

原 29 门禁：5 PASS、1 FAIL、23 NOT_RUN；ARCHITECTURE native=-15，断言完成未建立，工程 FAIL_PRESERVATION。177 observations=174 rejected+3 authorized frontend。54 rejected paths不等于closing differences。canonical index端点内容相等而替换/metadata事件发生；历史 staged semantics、writer与Skill正文修改均未建立；.usage.json和目录metadata变化保留。新三项validator修正不解释或消除旧保全失败。

HISTORICAL_RUN_FILES_BEFORE.json 对现存旧 run 文件单独记录大小和hash；它是本轮开始时的保全基线，不是恢复历史连续不可变证明。PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE。

## 运行决策规则

PENDING独立审查本身不是工程门禁前置阻塞。完成修正、实际资格、正确路径绑定、current baseline和sealed input后，才作一次 readiness决定。不能因环境可能有其他写者就虚构已失败，也不能保证它们将静止；若current baseline/实际观察拒绝则保留证据，按Owner停止，不恢复现场。

发布：既有 approval timeout / 禁止重试或换工具绕过的限制仍有效；目前没有合法解除的证据，不获取凭据、不尝试push。本地修正与资格不受该发布限制阻断。

INDEPENDENT_REVIEW=REQUIRED
FORMAL_GATE_READINESS=NOT_ESTABLISHED
