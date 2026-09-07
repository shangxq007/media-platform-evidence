# 前瞻 Owner 决策边界（本次不实施）

当前结论：未建立能满足 ORIGINAL shared-path preservation 的支持隔离。保持原合同，不能把私有副本、另一 shell/home、减少 Skill 调用或没有新端点差异解释为隔离成功。当前不创建 formal START、不运行产品门禁。

待 Owner 明确决定的具体提案为 `runtime-analysis/proposed-contract.json`，说明见 `runtime-analysis/RUNTIME_BOUNDARY_REPORT.zh-CN.md` §5；本提案不是 blanket Skills 豁免。

建议决策措辞：前瞻采用“双结果”原路径保全契约——旧 observer/旧谓词的 OLD_PASS/OLD_REJECT 必须原样保留；允许另行实现并独立审查一个仅针对已登记 `.usage.json` 已存在 record 的 view_count/use_count/last_viewed_at/last_used_at 事务的条件 reducer。仅当完整可信 writer/syscall/字节及字段差异证据、最终 entry-set 和目录 metadata 因果对账全部成立时，才可形成 `ORIGINAL_STRICT_CONTENT_PRESERVED_WITH_ACCOUNTED_BOOKKEEPING`。不得输出全字节/全元数据不可变。所有 instruction/support inputs、memories、未知路径/键、权限与未解释目录变化保持严格；未知归因、遗漏、overflow/gap、不完整证据全部拒绝。该提案的路径、字段、计数、临时文件和 lock 规则以所附 JSON/中文报告为整体，不能摘取只放宽部分。

这项决定目前 **NOT_APPROVED / NOT_ENACTED**。采纳提案本身也不等于实现、资格或独立 ACCEPT：需新的明确实施授权范围（新 reducer 的接受权限及可信审计机制）、风险控制验证和新 readiness，才可能建立下一次正式启动条件。当前 Owner 已授予的诊断实现/资格/证据发布工作不因此搁置。

若 Owner 不采纳，则原合同不变；本次没有通过权限、停其他进程、共享配置变化等方式建立原路径静止条件，也没有自行采用此类措施。不得回写任何历史 REJECT 或刷新其 baseline。
