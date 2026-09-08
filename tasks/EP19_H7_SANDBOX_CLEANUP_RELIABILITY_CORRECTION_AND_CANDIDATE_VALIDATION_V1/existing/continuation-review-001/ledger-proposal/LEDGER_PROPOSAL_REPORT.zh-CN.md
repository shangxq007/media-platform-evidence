# EP19 ledger 精确窄契约补充提案

**结论：可提交可执行的“NOOP manifest 子集追加”新契约，但未审批、未实现、未 qualification；默认仍 strict。** 这不是“所有 JSONL 追加安全”，也不是为 FIRST 补签。机器可审议规范见 `LEDGER_CONTRACT_PROPOSAL.json`，其中跨字段、事件与生命周期约束与字段 schema 同为强制条款，不能只跑 JSON Schema 即宣称通过。

## 1. 已证实的当前实现与未知的历史

- `tools/skill_ledger.py:66–85,246–266`：路径由 profile-aware home 下 skills/.curator_ledger.jsonl 产生；writer 以 UTF-8 append mode 写 JSON+LF。恰好输出 `id,ts,actor,action,skill,evidence,before,after`；id 为 UUID4 的12位小写十六进制，ts 为 UTC isoformat，actor 为 curator/agent/user。action/skill/evidence/manifests 没有封闭 schema 校验；没有 writer 锁、fsync 或 syscall 追加历史证明。
- 同文件 `101–133,269–303`：manifest 项为 `{path,sha256}`，snapshot 会写独立 blobs，失败是 best-effort。禁用/失败可能返回 None，调用方可落入空 before。因此 `before==after==[]` 不是 NOOP 证明。blob 写不因 ledger 豁免而获准。
- `tools/skill_manager_tool.py:695–777`：成功 mutation 后记录；普通 evidence 可含 session_id/file_path；delete 可含 absorbed_into/archived。`tools/skill_usage.py:557–580` 的 archive/restore 先移动文件并改 suppression/state，再记 ledger。`hermes_cli/curator.py:410–458` 的 purge 先删除再追加。不能把 ledger 当与正文/政策必然无关的 usage 计数。
- `skill_ledger.py:306–323`：reader 跳过部分坏行，按 skill 过滤、逆序、limit；get_entry 取第一个匹配 ID。追加即能改变展示/选择，重复 ID 可遮蔽旧目标。`338–402` rollback 真正写 before 文件、删除 after-only 文件，pre-rollback 即使 before==after 也不是安全记录类别；delete/archive/purge 还会补历史 package。`hermes_cli/curator.py:384–407,467–488` 提供显示/选择/执行入口。**即使允许的 NOOP 行日后被 rollback，也能将当时内容写回；不可承诺不影响任意未来 reader。**
- 以上仅说明读取时源码，不说明 FIRST 使用同一 writer。**历史 writer=UNKNOWN / NOT_ESTABLISHED 保留。** actor 字段不能用于归因。

FIRST 报告 `:5–9,23–27` 证明 baseline 在 observation 被拒绝，ledger 两次 hash 不同和 mask2/8；不含旧/新原始字节与前缀比较。两个 hash 无法推导增长量、公共前缀或合法记录；当前源码的 append mode 更不能替代历史证据。FIRST 失败不可撤销、重写或用后来读取追认。原 lock-close/capture 提案仍不足以处理 ledger。

## 2. 两个选项与建议

1. **保留 strict**：无需 ledger 新范围；任何 ledger modify 继续拒绝。这是未获新批准时的默认。
2. **可选 NOOP_MANIFEST_APPEND_SUBSET**：仅当前 action 名 `patch|edit`，不是发明 `action=noop`。只接受 `evidence={}`、非空完整 before/after manifest 深相等且与独立 strict inventory 同一 package 全量相等的追加。任何 session_id（虽当前 writer 可产生）也拒绝；这是刻意比当前 writer 更窄的权限，不保证下次后台追加可通过。

**不建议“所有 schema 合法记录追加”**：它容纳真实 body/path 变化、删除、恢复、rollback 和自由 evidence。若同时强制独立 strict body 不变，很多记录必然被拒，仍不能称全部记录无语义；若放宽 strict 则直接越权。即便放宽到所有 before==after 行，也会放进 pre-rollback 等有明确后续操作语义的类别，故不采纳。

## 3. 精确文件、字段和事件规则

仅 `/home/user/.hermes/skills/.curator_ledger.jsonl`，default profile，原已存在 regular、nlink=1。同一 dev/ino/mode/uid/gid/nlink、祖先身份和持久目录 entry set 保持；禁止创建、链接、替换、rotate、rename、截断、旧前缀改写。size 只增且等于捕获字节数，mtime/ctime 仅随已裁决的增长批次非递减；内容不变则九字段全相等。不新增 root 元数据豁免。

新行 exact keys 共八个；拒绝额外/重复 key、无效 UTF-8、BOM、CR、空行、NaN/Infinity、尾垃圾或未结束 LF。id 必须在旧前缀及全部新行唯一；ts 必须是合法 UTC `+00:00`、可选六位微秒，在本次绑定 wall-clock 窗口内且新行非递减；时钟回退拒绝。skill 必须为预绑定有限白名单的 exact 名称。manifest 只许 `{path,sha256}`，路径须是预绑定 package 内 exact canonical regular 路径、排序唯一、含 SKILL.md 且完整；不得空集、缺失捕获、跨包或有 symlink/dot segment。每个 digest 在独立 strict 捕获仍相同。具体正则、长度和交叉谓词见 JSON。

仅 exact `mask==2` 或 `mask==8` 且 cookie=0 进入 PENDING；组合 mask/其他位一律拒绝，不按文件名一键忽略。零事件只能对应内容与元数据不变；只有 close-write 可在九字段全等时裁决 unchanged；存在 modify 必须对应正增长、完整合格行，并在同一 boundary 批次收到 close-write。事件可合并，不将它们伪装成逐 syscall 配对或身份记录。所有 pending/半行必须在当前 command/gate boundary 前结束，否则拒绝。attrib/create/delete/move/watch-loss/overflow/unmount/unknown、无覆盖变化或证据写失败均拒绝。

保留起始长度 N0/hash H0，每次真实捕获还验证原始 `[0:N0]` 的 H0 和上一捕获 `[0:Nprev]` 的 Hprev，长度不下降；仅新增 suffix 可按新 schema 裁决。旧行保留字节、只为 framing/ID 去重做必要解析，不把旧类别变成新增行许可。未来私有 validator 可在内存解析，不发布旧 ledger、记录 ID、session 或正文；本任务没有读取 shared ledger body。

**观测能力边界必须写进 Owner 决定**：inotify 与稳定端点/prefix hash 不能区分“真正追加”和两次捕获之间 overwrite-restore / truncate-regrow 后再追加。源码 open('a') 也不能约束 UNKNOWN 外部 writer。提案禁止这些操作，但最多证明各受覆盖捕获点原/前一前缀不变，不证明完整 syscall 历史。Owner 若要求证明任何瞬间从未改写，则现有观测机制无法满足，必须保持 strict；不能用本方案声称已证明纯追加。若接受这种有限观察保证，必须显式批准，不得偷换为全历史证明。严格 Skill/Memory 事件包括写后恢复始终拒绝，不适用该 ledger 局限豁免。

## 4. Start / mid / end 与依赖

- **Start**：绑定 exact schema/policy/Owner、有限 eligible map、strict inventory、reader/source closure、matrix、executor/candidate/qualification。连续 file+parent watch 完成后才做权威 stable capture，严格输入不得有注册间隙。相同 FD 的 stat/read/stat 和路径身份核验；同一真实 bytes 产生 hash/解析/投影，collector 与 policy 同一 capture ID。缺失/未知一律拒绝，不补造原件。
- **Mid**：持续保留事件，每个 preflight/prestart/gate/command boundary 验证双前缀、所有新行、独立严格对象与完整覆盖。不可把后来重读值回填到旧比较。只有 ledger 观测子谓词新增；usage 的 V2 四字段、exact temp、单独 lock 与 capture 条款仍独立。
- **End**：连续覆盖下 final capture+drain，无新未解释事件、无 pending/半行，strict 全量通过。保留真实 old-strict hash delta、native exits、所有失败证据；新 predicate 不抹去事实。

新有限预算是待批准政策而非现场测量：单次窗口≤3600s；旧前缀≤64MiB；新行≤128；单行含 LF≤1MiB；累计追加≤8MiB；manifest≤4096项；eligible skills≤128；每 boundary stable capture 最多3次且累计≤5s；pending≤4096。超限 failclosed，不自动扩容或重开 baseline。

Ledger 在已读 reader 中依赖审计/rollback 选择；不见于这些直接函数的技能选择逻辑不等于全局无依赖。本任务验收必须封闭并绑定实际执行矩阵的消费路径：**不得把变化 ledger 作为授权、指令/候选选择、policy/gate 输入**，不得运行 ledger-list/rollback 或引入未绑定动态 reader。ledger 仍进入真实 raw inventory/capture，只将获准差分交给专门 semantic predicate，不从 inventory 消失。该依赖闭包若无法提供或 qualification 不通过，确定动作就是保持 strict，而非凭名字放行。对任意未来 reader 不作承诺。

## 5. 资格验证、重绑与权限校正

JSON 列出有限正反控制：unchanged、close-only、单/多合法 NOOP 行、同源 capture；前缀损坏、shrink/replace/rename/link、重复 ID/key、未知 evidence/action、空/缺 manifest、changed manifests、strict body/Memory 写后恢复、watch gap/overflow、超限/时钟回退、旧 binding/证据失败等。**全部 PLANNED_ONLY，未运行测试/probe/baseline**；隐蔽改写恢复是能力边界反例，不能伪报普通 observer 能检测。

受影响闭包包括 observe/reducer、ledger parser/prefix/coherent capture、bookkeeping 组合、baseline old-strict veto 与 decision-evidence、scope/inventory/sequence/coverage/seal，及 preflight/prestart/每 gate/boundary/final。须重新 qualification 与 source-applicability；Owner/policy/schema/eligible map/capture 协议/matrix/executor/candidate/qualification hashes 全量重绑。旧 qualification 仅在未变依赖可证明适用时局部引用，不整包继承，不修补 FIRST。

**权限校正**：当前 continuation 已授权范围内 implementation/qualification，并给出第二尝试 CONDITIONAL；不照抄旧 rejection 报告“常规实施另获批准/再求一次 routine run 许可”的过期描述。本次仅 READONLY 提案。真正新增 ledger（及另选 lock/capture）契约差异仍须 Owner 明确批准；批准、资格验证、完整新 binding/readiness 都满足前，第二尝试仍 BLOCKED。本报告不消费预算，也不是独立接受。

## 6. 证据与交付边界

只读直接相关源码/调用点和任务 rejection 报告；搜索曾命中 tests 源码引用，未打开测试正文、未执行任何测试。未读取 shared ledger/private usage、credentials、宿主历史/当前状态扫描；未改 source/config/Skills/Memory 或服务/进程。只新建本 proposal 目录的报告、JSON、manifest。源码引用的 SHA256 与行号列于下表；这只是当前读取内容的绑定，不是历史 writer 的身份认证。

- `/home/user/.hermes/hermes-agent/tools/skill_ledger.py`；行 37–85, 101–133, 246–303, 306–402；SHA256 `bf7e80b0705ccd80d6307e308f6b2cbcae875585055b2f3e62b768b0168b0c34`。
- `/home/user/.hermes/hermes-agent/tools/skill_manager_tool.py`；行 695–777；SHA256 `87f088f543adbac9723ef196336f424adf2afd15a6c71c5e0e2918173df1a386`。
- `/home/user/.hermes/hermes-agent/tools/skill_usage.py`；行 557–580；SHA256 `82702d4736a8fc81ceb4dd5e6ce9706aa242102c84277c474c661e659a6f1aed`。
- `/home/user/.hermes/hermes-agent/hermes_cli/curator.py`；行 384–407, 410–488；SHA256 `e9562dd6772fd128f4a498b859b493d2af8e8d7e91467af45921d4fc99c98d62`。
- `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/continuation-review-001/rejection/FIRST_REJECTION_REPORT.zh-CN.md`；行 1–61；SHA256 `a3ae6064d2a9bbd04423e9fb9193ff818d26fc34ac8768552acde067be96eb0c`。
- `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/continuation-review-001/rejection/NARROW_RULE_PROPOSAL.json`；行 1–73；SHA256 `484986355e33c200793936056056cb1fd72a175ef2ba36a7ec1d19b7abc9d821`。
