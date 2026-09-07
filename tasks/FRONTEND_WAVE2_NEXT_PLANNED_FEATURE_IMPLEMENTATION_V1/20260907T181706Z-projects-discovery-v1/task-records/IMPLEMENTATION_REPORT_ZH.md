# 最近项目发现与只读检查 — 实现报告

## 结论与身份

**本地实现及必需验证完成，等待独立评审。真实集成未建立，产品未提交或发布。** 此报告是提交证据前的实现报告；后续证据仓库提交及匿名回读由独立 delivery receipt 记录，不改变本报告覆盖的产品身份。

- TASK：`FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1`；LANE：`FRONTEND`。
- 分支：`refs/heads/agent/frontend-wave2-product-ux-v1`。
- 接受基线实现树：`c1d45edff185a99f3a961a9b29598ea2b34d0f18`。
- 最终实现树：`0b76ac9352ad40fc155c7203ed69f6362b0db89f`。
- 产品 HEAD：`f5e19cf53fd010eea2935dd29557e82a879e042c`，真实 index 未变；实现树不是 HEAD。
- 10 个产品/测试路径、5 个文档路径变化；5 个新增 Projects 路径已经登记到现有分类/当前范围记录，未创建新 Slice 或接受账本。

## 选题依据与范围

选自 `docs/architecture/governance/frontend-foundation-checkpoint-a-implementation-v1.md` 第 250–265 行的 **Compact surface design records → Workspace → PRIMARY_ACTIONS: search Projects, inspect recent work**。IA 的 Six surface families → Workspace / Home 同样要求查找 Projects。源码原有 Projects 页仅提供 dashboard 最近项目卡片、名称过滤及 disabled Open，没有完整检查、筛选/排序/重置、刷新/取消/重试流程。

因此补齐这个已有部分工作流，而不是增加空页面。选择、Canvas/pagehide、命令发现、Review、通知已接受工作均不重新打开；Scene/Shot/Workflow/Render 等仍需决策恢复的方向不冒充接受需求。沿用已有 A-only shell、共享设计原语和 InteractionDialog，不替换设计参考项目。

## 用户可见行为

在既有 `/w/$workspaceId/projects` 路由：

1. 从名称或描述做本地文字搜索；根据原样投影状态筛选；按名称排序，同名时以不透明 ID 稳定消歧；无匹配时可重置过滤。
2. 检查选中条目的名称、描述、项目 ID、投影状态和投影创建时间。它是只读投影，不是 canonical 项目详情、存在证明或打开权限。
3. 支持加载、取消、刷新、重试；加载/失败时清除旧内容；区分未配置、unknown、denied、unsupported、error、已加载空快照和本地无匹配。
4. 最近项目快照有明确 bounded/limited 说明，不将其说成完整项目清单或全量服务端搜索。
5. 英文和简体中文界面；不透明名称、描述、状态、错误解释保持原文，尖括号内容不会作为 HTML 执行。
6. 共用对话框键盘约束、Escape 关闭和 launcher 焦点恢复。Refresh/Cancel/Retry 使用同一个稳定按钮，状态变化不会移除持焦控件，也没有异步抢焦点。

### 重要行为边界变化

普通 Projects 路径现在使用明确的应用适配器注入边界，而不继续把旧 `/me/dashboard` 包装器当成此消费者的认证/session/权限协议。未配置时如实 unavailable，不发送项目查询。**WorkspaceHome 既有查询消费者未改。** 这是一项刻意的 fail-closed 边界变化，不是“真实项目列表已经集成”的声明。

只在 localhost/127.0.0.1/[::1] 且明确 `projectsFixture=1` 时启用内存示例；显示 SIMULATED PROJECT DATA。可以再加 `projectsFixtureEmpty=1`、`projectsFixtureLimited=1` 或 `projectsFixtureFailure=denied|unknown|unsupported|unavailable|error` 观察对应状态。样例不授予真实权限，不使用 localStorage 冒充持久化。

## 架构、权限与生命周期

复用既有 `ProjectSummary`、EffectiveAccess、AppShell、设计原语和 InteractionDialog。页面本地检查只有一个 LOCAL_EPHEMERAL 分派入口；没有第二命令注册表、权限系统、Selection store、通知中心或服务端 Revision。Open/Create、canonical Apply、Timeline gateway 和所有真实命令均未开放。

real-origin 来源必须同时具备 `SERVER` 投影来源和精确的前端建议 key `project.recent.query`；示例有独立 fixture key 和 development 投影来源。更改 origin 标签本身不能将模拟变为真实查询权限。该 key 仍是**前端消费建议，不是已接受服务端 Operation/接口**。组件检查不证明服务端授权。

请求绑定 principal、tenant、session、Workspace、request、adapter/access 和组件生命周期。旧请求取消/卸载、身份或来源切换后，其有效旧回执也不能重新展示内容。测试包含真正 pending 的旧请求、匹配其旧身份的成功回执、principal-null logout、相同身份 adapter 替换；没有添加无关媒体 Selection 维度。

## 后端需求与未来小范围集成

追加澄清现有 `UXW1-001` / `FB-GAP-001`，关联既有 `FB-GAP-009`；没有新增需求 ID、端点、DTO 或已接受 Operation。既有记录保留历史决策，并补齐消费者场景、身份/资源作用域、建议输入输出、权限/失败/partial 语义、并发生命周期和未来验收条件。

`NEW_BACKEND_REQUIREMENTS=NONE` 指本轮没有新需求 ID 或后端实现；真实只读来源仍依赖已记录缺口。

未来只集成一个路径：固定本报告最终前端树和构建，另行同意并固定后端最近项目投影适配器版本；使用两个 principal/tenant、一个允许 Workspace、一个拒绝场景和一个 limited 快照的受控数据。验证安全摘要、限量说明、拒绝/错误不泄露旧数据、logout/switch 后旧回执隔离；不打开项目、不创建或进行 canonical 写入。后端具体版本和建议协议接受尚未确定。本轮模拟验证不是这项真实集成。

## 实际验证

所有最终结果都绑定 `final-validation-02/` 的最终树：

| 项目 | 结果 |
|---|---|
| Projects 有界修正 focused tests | 53/53（执行器迭代证据） |
| 最终受影响特性及共享消费者测试 | 232/232 |
| 最终完整前端套件 | 630/630，32 文件 |
| 相对 576 基线的测试身份 | 新增 54、移除 0、重复 0、跳过 0、失败 0 |
| required typecheck、lint、架构 guard | 全部 exit 0 |
| 架构 controls | 120/120 |
| lint 身份对账 | 原有 46 条；新增 0、移除 0 |
| 原生 Chromium 工作流 | 36/36；断言、harness、Chromium exit 均为 0 |
| 构建/服务绑定 | 8 个输出 HTTP 字节全部匹配；必需引用缺失 0 |
| 外部请求、真实后端请求、项目 HTTP 查询、canonical 请求 | 均为 0 |

构建 manifest SHA-256：`b5246980b450e1aef495f9b6f5c096d0f623a6ee0320ade21e7f6ea63b1b44fd`。

既存精确 `/vite.svg` favicon 仍缺失，保留为历史 optional icon 例外，不将其计为必需模块缺失。构建输出始终在外部目录；没有先写 tracked dist/backend static 再清理的操作。

浏览器采用 native CDP pointer、Tab、Enter、Escape、方向键和文字键输入。明确披露辅助：CDP focus emulation、DOM 语言切换/scrollIntoView、React fiber 中显式模拟 adapter 的可控延迟/失败。没有直接调用产品 handler 替代 UI 交互。scope 切换的详细证明是组件测试，不冒充原生真实认证。桌面 1440×1000、窄屏 390×844 是模拟视口；没有物理设备或屏幕阅读器语音证明。fixture 服务最终 SIGTERM 清理，Chromium 是 Browser.close 后自然 exit 0，二者不混淆。

最终截图已人工视觉检查：英文和中文详情可读、关闭按钮可见、字面尖括号内容被保留、没有可见对话框横向裁切。窄屏截图背景已滚动，页首模拟来源横幅不在该截图视口内；截图本身不证明键盘行为，图册明确标识所有数据为 fixture。

## 保留的迭代与纠正

- 初轮 RED：44 项，9 通过/35 预期失败，针对可编译行为 scaffolds，不是 import 错误。所有 GREEN 中间失败、歧义查询及过强旧回执断言修正均保留。
- 有界源码复核确认稳定控件、投影来源和初始 reason 展示缺口；也保留反证：原先多数身份切换测试已具有真实 pending 旧回执，只有 adapter 替换等个别覆盖需校准。修正前 RED 为 48/53 和 47/53，随后 53/53。
- 初轮执行器额外局部 TypeScript 配置尝试的失败与后续结果保留；不是 required 最终 typecheck 的替代品，未修改产品配置。执行器报告里的任何未来 freeze/integration 措辞不构成本任务授权。
- 控制面一次状态文档查询遗漏 external Git object alternates，错误推断路径不在树中。此推断有独立纠正记录；查询失败没有改产品文件。实际历史状态文档存在，现以追加章节记录 Owner 接受的通知修正和本次功能。
- 首轮完整门禁及浏览器已在树 `b8ae3ab305963e8f9b1a232660d33f64af8a359c` 全部通过。交付核对发现状态文档误写计划章节号；只改一处文档引用，运行时/测试源码未变。旧结果保留，随后针对最终树重新执行所需门禁、外部构建和浏览器，而不是把旧树结果重新标记为最终树。每个被验证树的完整套件各执行一次。

## 保全、交付与停止

真实 HEAD/index、原有 dirty work、非前端内容、tracked dist/backend static、既有 H4 和 Slice1C 状态/发布门禁保留。对已登记历史 public/build 范围的 674 个文件逐字节检查，差异 0；不声称监控了所有并行任务的全部外部状态，也不要求后端泳道停驻。

本任务发出的 Skill/Memory 正文写入为 0；基线纳入的正文文件未观察到内容或同正文 mtime 漂移。usage/curator 或其他并行新增文件不属于这个零值的归因范围。

包提供完整差异、所有修改前后端点、必要共享源码、测试身份、原始门禁/浏览器记录、截图、构建和 ordered JS chunks。完整 patch 已在新外部 index 重放，得到精确最终树；真实 index 未改。

下一步仅为独立评审。证据发布不等于产品提交、冻结、推送、部署或验收；不启动另一功能。
