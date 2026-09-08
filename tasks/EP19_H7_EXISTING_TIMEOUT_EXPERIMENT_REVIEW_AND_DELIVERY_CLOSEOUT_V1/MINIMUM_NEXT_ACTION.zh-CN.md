# 唯一最小下一步（本任务不执行）

**主建议：独立评审后另行授权一次“失败态身份分类”的有界补充诊断实验；不先修产品、不重跑整套正式门禁。**

- 精确验收阻塞：原候选 RUNTIME_PREFLIGHT 的 cleanup.completed 断言失败仍有效（历史 survivor=[489968]）；29 门中另有 19 NOT_RUN。实验不是门禁替代，独立评审也仍未完成。
- 已排除的范围：本次数据排除了“本次原 survivor 实际非空却被报告为空”、“本次 capture 未完成导致 completed=false”、“本次未保存 timeout 主失败”、“本次依赖单独 teardown 发信号才把原 cleanup 改成成功”。不能把这些排除转移到历史失败。
- 决定性缺证：需要在原 survivor 非空的失败点取得身份绑定的实际状态、信号结果和至 capture 完成后的连续对应，并保存每次身份比较的阶段、before/after startInstant、registered/observed startTicks 和读取错误类型。现有一次非复现缺少失败态本身；仅补齐这次 mismatch 解释仍不足以证明历史唯一原因。
- 拟变更组件：只改未来独立实验副本的 TimeoutDiagnosticRecorder 身份失败记录，以及必要的数据序列化/主入口输出；保持 LocalBoundedProcessLauncher 和 BubblewrapSandboxProcessLauncher 清理规则、workload、250ms、never、grace、轮询、survivor 位置与原接受规则。根断言的保留句柄适配应在新实验合同里明确承认局限，不冒称原测试逐字等价。
- 必要验证范围：记录器合成输入的消失/不一致/拒绝分类与写入完整性、静态 patch 行为审查、独占输入身份绑定，然后至多一次单场景；无 detector 探针、无全测试方法、无自动重试。如果仍未复现，仍只报告单次未复现，不循环搜集失败。
- 为何更有针对性：全套门禁只能再给 pass/fail，现有失败点不保存区分运行、退出竞争、回收、信号权限的决定性字段。先补该窄证据缺口比消耗 29 门更直接。
- 现有证据不足以决定任何产品修复；不得延长超时、删除 completed 断言或忽略 survivor。若未来证据支持修改 sandbox-isolation-module，必须形成新的产品 commit/tree，并验证共享清理调用者（Local、Bubblewrap、Container 路径）及受影响正式范围；不能归入原 689ab9456461a8d19a72d059f5157092efc43aff。

这是一个待独立评审及新授权的技术动作建议，不是当前执行许可。当前 ADDITIONAL_EXPERIMENT_ATTEMPTS_AUTHORIZED=0。本任务停止，不自动实施。
