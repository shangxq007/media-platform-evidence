# EP19 H7 既有 timeout 实验审查与交付补充报告

记录时间：2026-09-08T19:38:32.600001+00:00。任务：EP19_H7_EXISTING_TIMEOUT_EXPERIMENT_REVIEW_AND_DELIVERY_CLOSEOUT_V1；LANE=BACKEND_VALIDATION。

## 五项结论

1. **本次只证明一个带观测补丁的 timeout 尝试没有复现历史 cleanup 失败。** 原始返回 PROCESS_TIMEOUT、cleanup.completed=true、survivors=[]、captureStreamsClosed=true；Java native exit=0。结论限定为 `NOT_REPRODUCED_IN_ONE_INSTRUMENTED_ATTEMPT`。不是原候选通过 RUNTIME_PREFLIGHT，也不证明历史误报、清理可靠性或产品缺陷关闭。
2. **清理决策表达式和原调用相对次序保留，但不是严格无行为影响或完全等价。** 同步 /proc 采样、JSON 编码、锁、后台 journal 与计时插入关键路径；根注册在 deadline 初始化前，原 survivor 前增加状态采样。入口根进程条件从数字 PID 重查改为保留句柄。后者是明确的接受观测机制差异，不应笼统写“原接受条件完全未变”。没有发现改变 grace、轮询、TERM/KILL 决策或 completed/primaryFailure 公式的产品修复。详见 [补丁审查](PATCH_BEHAVIOR.zh-CN.md)。
3. **unresolvedRisk 是保守的身份状态证据不足标记，不是残留存活判决。** 根 529945 为 unknown_start_identity，sleep 529949 和 timeout 529948 为 identity_mismatch；最终均为 not_resampled，即使保留句柄 isAlive=false 也触发 true。529946 的 missing_proc_entry 分支不触发。自有根 waitFor=true 已记录；没有后代本方回收证明。没有确认需要当前终止处置的对象，本任务未查询任何当前 PID，保留历史证明限制，不修改该布尔值。
4. **Owner 一次实验授权及会话在启动前收到该授权已建立；完整工具审批恢复链未建立。** user 消息 285277（2026-09-08T15:07:57Z）早于 16:06:26Z 实验启动请求；285340 明确允许本地准备重提交，285350 为实际成功响应，285702 记录实验控制器 exit 0。不能由此单独推定所有审批条件均满足，也不能只引用最早只读限制宣称无授权。此前“因越界而停止”的无条件判断应撤回为待独立核对的限定结论。见 [授权追加说明](AUTHORIZATION_ADDENDUM.zh-CN.md)，原文保留。
5. **唯一技术主建议：经独立评审、另行授权后，进行一个只针对失败态身份消失/不一致分类的有界补充诊断实验，不先修产品。** 决定性缺项不是再获一个 exit=0，而是原 survivor 非空时、身份绑定的状态与信号到 capture 后的时间线，并保留失败身份比较的每个左右值和失败阶段。本任务不修改记录器、不新增实验、不跑正式门禁。详见 [最小下一步](MINIMUM_NEXT_ACTION.zh-CN.md)。

## 身份、历史与复用

固定 candidate commit：689ab9456461a8d19a72d059f5157092efc43aff；tree：6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6。独立实验副本 HEAD/tree 本次 Git 只读核对匹配；不是已提交的新产品候选。

实验完整内容摘要 727188350f96bce9843426fd98f21661dc997de0f0b74052314b7f16944d38d5 是既有 path/mode/SHA256 清单身份，本次复用该历史身份记录，不重做完整源码 census。观测 patch 的实测 SHA256 为 41897cf4ca6463168be38ccaa800b9bb6fd8827b2170dc02cb9acf7eab77aa8d。

本次新鲜核验 37 个依赖文件摘要（其中旧 manifest 为摘要锚，其他 36 项与其条目匹配）；6 个原始源码与固定 Git blob 相同；6 个实验源码/README 与实验副本相同；计划绑定的 127 个执行输入摘要全部匹配。所有逐项结果见 [SOURCE_VERIFICATION.json](SOURCE_VERIFICATION.json)。未重编译、未运行历史脚本。manifest 证明当前选定字节与既有清单一致，不证明历史作者或抗篡改时间戳。

历史 baseline/seal/START 关联、旧全量文件与归档核验、Lean/V2/baseline qualification 按既有恢复记录复用，不报告为本次新执行。当前读取 `/home/user/Documents/03-大模型上下文-精简版.md` 全文，仅作决策上下文，不公开全文，不作实现证明。

历史 run `baseline-sequence-formal-001` 的 GATE_ACCOUNTING 逐 gate 计数仍为 29 必需、9 PASS、1 FAIL、19 NOT_RUN，失败 RUNTIME_PREFLIGHT native/wrapper=1。原 XML 记录 survivors=[489968]、enginePid=489967、engineClientReaped=true、workloadProcessesContained=false、captureStreamsClosed=true。旧 PID 只作为记录字段。

## 证据入口

- [授权来源及勘误](AUTHORIZATION_ADDENDUM.zh-CN.md) / [必要来源摘录](AUTHORIZATION_SOURCES.json)
- [patch 行为影响](PATCH_BEHAVIOR.zh-CN.md)
- [有界时间线](TIMELINE.zh-CN.md) / [逐事件机器对应表](TIMELINE.json)
- [unresolvedRisk](UNRESOLVED_RISK.zh-CN.md)
- [唯一最小下一步](MINIMUM_NEXT_ACTION.zh-CN.md)
- [机器索引](MACHINE_INDEX.json)、[字节清单](PUBLIC_MANIFEST.sha256)
- [原报告原字节副本](sources/REVIEW_INDEX.zh-CN.md)、[实际 patch](sources/instrumentation.patch)、[计划及命令](sources/EXPERIMENT_PLAN.json)
- [原始结果](sources/runtime/result.json)、[控制器回执](sources/runtime/controller-receipt.json)、[原时间线](sources/runtime/timeline.jsonl)、[独立收尾](sources/runtime/teardown.json)

## 交付与停止边界

本目录是新增补充材料，不修改原实验目录、正式失败证据或产品内容。仅必要源码、原始日志及必要授权摘录公开；私人会话、凭据、Skill/Memory 正文及无关清单不公开。原历史报告有旧发布状态和较早“0 次”语境，均以其历史时间解释，不作为当前启动许可。

本次 local/remote 最终状态由目录外 detached DELIVERY_RECEIPT.json 记录，避免提交或 manifest 自引用。公开机器索引中的交付状态为封包阶段状态，不冒充之后的远端核验；完整 fixed-commit URL 与实际发布 SHA 见 detached 回执及最终答复。

独立评审 REQUIRED；EP19_CLOSED=NO_PENDING_INDEPENDENT_REVIEW；产品发布 NOT_PERFORMED。没有产品修复、executor/observer/接受规则修改、门禁或实验重跑；不触及并行前端 ref、工作区、进程、测试或证据。不建立全系统保全扫描。任务未调用 Skill/Memory 写入；工具框架可能产生缓存和 usage bookkeeping，这不是无全局文件变化断言。
