# unresolvedRisk 精确解释

来源：`sources/instrumented-source/diagnostic/com/example/platform/sandbox/TimeoutDiagnosticRecorder.java:448–454`（teardown 的最终 unresolved 计算）；Main:54/163 为初始或异常默认 true；本次最终是 Recorder 正常计算，不是未执行 teardown 的初值。具体代码行号由源表核验，参阅机器来源索引。

规则：identitiesDropped != 0，或 finalSnapshots 任一非 matching_identity / isAliveObserved 非 false / state=Z，则保守 true；例外是 missing_proc_entry 或因 missing_proc_entry 退休后的 not_resampled。这次 identitiesDropped=0，触发者如下。

| 对象（均为历史实验身份） | startTicks / startInstant UTC | 最终记录 | 是否触发 |
|---|---|---|---|
| root bwrap 529945 | 13456901 / 2026-09-08T16:06:27.010Z | isAlive=false；not_resampled，unknown_start_identity | 是 |
| sleep 529949 | 13456903 / 2026-09-08T16:06:27.030Z | isAlive=false；not_resampled，identity_mismatch | 是 |
| timeout 529948 | 13456903 / 2026-09-08T16:06:27.030Z | isAlive=false；not_resampled，identity_mismatch | 是 |
| namespace bwrap 529946 | 13456901 / 2026-09-08T16:06:27.010Z | isAlive=false；not_resampled，missing_proc_entry | 否 |

根 unknown 来自 timeline:36；其已注册 ticks 非空，结合代码支持当时 startInstant 无法取得的分支，但未保存当时 null 的直接字段，属代码与事件的推断。两后代 mismatch 首见 timeline:18/20；同一标签合并了 startInstant 不同、跨 stat 读取变动或 ticks 不同等分支，缺少实际比较左右值，不能区分退出竞争、PID 复用或身份信息变化。

`cleanup.completed=true` 来自更早原 survivors 空与 capture 完成的布尔公式；`unresolvedRisk` 来自后来的诊断收尾身份可观察性，两者不同时间、不同范围。engineClientReaped 字段是 survivor 派生标签；真正自有 root Process.waitFor=true 在 timeline:67–68 / teardown.rootWait，支持自有根等待完成。不能用它证明本方 waitpid 回收全部后代。

没有确认的 Z 状态、匹配身份下仍存活的最终对象，收尾 actions 全 none；**没有证据要求当前人工终止一个已确认存活对象**。这不等于全机或所有遗漏对象无残留证明。本任务没有当前 PID/名称扫描、信号、工作负载启动或目录清理；CURRENT_OBSERVATION=NOT_PERFORMED。保留历史身份分类与后代回收证明限制，不将 unresolvedRisk 改为 false。
