# V11 Skill 通知定点事实说明

## 结论

**确认一次与 V11 父会话关联的 Skill 正文补丁，发生于 Outcome C 报告封存和最终回复之后。** 不仅是通知文字：既有 mutation ledger、当前文件哈希/mtime、同会话后台 review 日志相互印证。记录支持后台 self-improvement review 路径；不应归因于研究、部署、打包子代理，也不能只凭 ledger 的 `actor=curator` 归因于定时 Curator daemon。

此审查仅追加事实，不修改封存材料或该 Skill，不审查 Memory。机器证据及内容差异见同目录 `evidence.json`。

## 精确路径与写入证据

目标：`/home/user/.hermes/skills/software-development/provider-lifecycle-evaluation/SKILL.md`

- 既有记录：`/home/user/.hermes/skills/.curator_ledger.jsonl` 第 **622** 行，id `84d46702c3ee`，action `patch`，actor `curator`。
- 记录关联 session：`20260909_063817_8d228f`（V11 父会话）。
- ledger 时间：**2026-09-09T06:46:19.216703+00:00**，即北京时间 14:46:19。
- 记录 before SHA-256：`783d2041b782bdf99edc971d32cd75bfe605fd012c1632b72a201f05bf934fce`。
- 记录 after SHA-256 与本次读取实际哈希一致：`7e3e6038ef337e8fe2794b64387e8df895ba4c947322cfe6cc411b9a3728dc6e`。
- 当前文件 19312 bytes，mtime **2026-09-09T06:46:19.177346+00:00**，mtime_ns `1788936379177346282`。mtime 本身不是作者证明。
- 对该 ledger 条目逐路径比较，仅 `SKILL.md` before/after 改变；条目中的 **13 个 reference 路径哈希相同**。这不意味着本次重新验证了每个 reference 的当前文件，也不是全库无写入证明。

## 修改内容及旧版本证据等级

父会话 `state.db` message **289565** 的既有 `skill_view` 返回保存了修改前正文。其正文 UTF-8 SHA-256 恰与上述 ledger before 相同。**该历史工具返回不等于独立封存的旧磁盘文件哈希测量**；before 哈希的磁盘状态依据是 mutation ledger 自身的记录。

历史返回正文与当前正文的逐行比较，只新增一个 `### Read-only service pilot contract gate` 小节，位于 Phase 1 的 capability matrix 之后、Phase 2 之前。新增六条规则：

1. 区分官方文档、固定版本源码和实际运行字段/版本；镜像 digest 不证明运行版本或签名来源。
2. 真实读取须批准上游实际 organization 读取范围；单账号本地过滤不能缩窄上游权限，GET 不自动代表安全。
3. 字段映射保留缺失和未知；不能虚构 attempt、content version、artifact link 或实际发布时间。
4. 重复排期 ID 与无分页完整性须明确部分/省略或拒绝，不能虚构 occurrence ID。
5. fixture/test-only 权限不能升级成服务端授权；单用户试点不声称多租户授权。
6. 区分静态研究、合成测试、空实例、真实账号/记录/产物证据；草稿阻断不是仅缺凭据，setup error 不是行为测试结果。

完整重建 diff 保存在 `evidence.json`，标注其历史来源。**未在本次限定的父会话及初始子会话持久化 messages 中找到后台调用原始 `old_string/new_string` 参数或完整成功结果正文**；不把重建 diff 冒称原始工具补丁载荷。仅查看了 backup 根的目录名，没有获得与本次时间对应的独立旧文件快照；未扩展历史恢复调查。

## 时间链与封存边界

全部 UTC，日志原文为与这些时间一致的北京时间：

| 时间 | 既有证据 |
|---|---|
| 06:41:08 | Outcome C ZIP、MANIFEST、integrity-verification 文件 mtime |
| 06:43:26 | 父会话 message 289851 记录证据提交 `daed076a516eaa2a5c2819b623d4a2a8a63cb02c` 已准备 |
| 06:45:09 | `FINAL_REPORT_ZH.md`、`FINAL_DELIVERY.json`、detached receipt 写入；父会话 messages 289856–289857 |
| 06:45:17 | message 289859：当时 detached receipt 校验成功 |
| 06:45:45.993689 | message 289860：V11 Outcome C 最终回复 |
| 06:45:46.096 | `agent.log:12008`：同 session 新 review turn，提示开头为 `Review the conversation above and update the skill library. Be ACTIVE…` |
| 06:46:19 | `agent.log:12018`：`skill_manage completed`；目标 ledger 与文件 mtime 同时对应 |
| 06:46:30.997 | `agent.log:12027`：`agent.background_review: Background review complete: thread=bg-review calls=3 … result=skill` |

本次只重新核验直接相关的五个封存文件：最终报告、最终 JSON、Outcome C ZIP、MANIFEST、integrity-verification，**五者仍与既有 detached receipt 一致**。没有重跑全部产品/发布验收，也没有声称本次远端验证。

`FINAL_REPORT_ZH.md` 和 `FINAL_DELIVERY.json` 的 `SKILL_MEMORY_WRITES: 0` 出现在补丁之前。正确处理是保留封存文件并追加本说明：该字段不能继续作为覆盖后续后台 review 的绝对零写入结论。本次记录不证明该字段在写成时就已因本条补丁而错误；它证明随后出现了 Skill 正文变化。Memory 未审查，不能从该复合字段反推 Memory 有或无变化。

## 授权、归因与控制边界

- `INITIAL_BOUNDARIES.md` 明确 `All Skill/Memory writes forbidden by carried task practice`；`WRITER_BRIEF.md` 明确禁止 Skill/Memory。
- 初始研究/部署/打包子会话的原始任务 message **289570 / 289671 / 289736** 分别明确禁止 Skill/Memory 写入，精确节录见 JSON。
- 本次审阅的 V11 用户指令与这些任务记录未发现此前独立 Owner Skill 正文修改授权。自动 review 提示的存在不是独立 Owner 授权。更早无关会话未搜索，不作全历史不存在授权的绝对断言。
- 综合时间、同 session review 提示、成功工具日志、ledger 和 `bg-review result=skill`，后台 self-improvement 路径有直接运行记录支持；不是仅凭通知猜测。原始完整后台 prompt、调用参数与执行控制配置未获得，具体如何处理原任务禁写指令、是否被传递/覆盖/忽略未知。
- 因此可确认**后台路径发生了与 V11 记录禁写边界冲突的正文变化**；不能仅凭这组证据指认某个业务子代理主动越权，也不能宣称是定时 daemon。
- 本次未查看私人配置或凭据，未检查/操作任何控制开关、scheduler 状态、文件保护机制。日志证明自动 review 能发生，不证明当前有无可用的任务级抑制开关，更不证明已成功关闭。仅承诺本审查没有主动执行 Skill/Memory 写入，**不保证框架今后绝对零变化**。

## 本次审查的写入范围

仅创建本目录 `FACT_NOTE.md` 和 `evidence.json`；没有 Skill/Memory 正文修改、配置切换、删除、回滚或封存证据修改。工具读取/调用本身可能由运行框架记录日志或使用元数据，本说明不将这种运行框架活动包装为全系统零写入保证。该核查不改变适配器工作及其独立验收状态。
