# V9 NLE 基线契约与高风险检查

## 范围与证据约束

只读源码分析，**不是 V9 candidate 独立验收**；未运行测试、构建或浏览器，未读取 live worktree、凭据或运行时路由，未改产品/Skill/Memory、未执行 Git 写入。唯一任务产物为本文。

基线根目录：`/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/validation-01/snapshot`。下列引用均相对此目录。父 verifier 提供基线 tree `0289714b2d4094db210b55681fa4f6a8135f7054`、已核对 7977 blobs；本文不重复声称完成该核对。

已读根 `AGENTS.md`，未发现嵌套 AGENTS。其第 22 行要求 freeze，与本次 Owner 明确禁止 commit/freeze 冲突，按第 9–14 行优先级遵守 Owner；本阶段仅基线分析，不读取 live Git 状态、不生成 candidate SHA、不执行通用 skill 的建 worktree/测试流程。治理文档本身未修改。

## 关键结论：现有 NLE 没有可靠的 loaded tracks/clips 数据

1. **`RevisionDetail` 不是时间线快照。** 它只有 revision 元数据、变更摘要、changeCount；`TimelineQueryGateway` 仅 HEAD/list/detail/compare。比较条目只有 kind/entityId/action，不能还原完整轨道、片段、顺序、起止时间或媒体映射。后端 detail DTO 同样只有摘要和 patchOpCount，并非前端漏映射了完整几何。`supported=false` 的默认零计数更不能解释成“空时间线”。引用：`frontend/src/product/timeline/gateways.ts:43–98`；`frontend/src/api/app/timeline-query.gateway.ts:43–76,107–137`；`platform-app/src/main/java/com/example/platform/web/render/TimelineRevisionController.java:347–368,431–466`。
2. **HEAD 有权威身份，没有几何或 FPS。** 适配器核对 requested Project 和双 revision ID；timelineId 来自 productId。历史请求固定 `limit:50`，没有分页游标/完整历史保证；显式 revision 选择只允许当前列表成员。不能用最新列表项推 HEAD，也不能把未列出的 revision 称为不存在。引用：`frontend/src/api/app/timeline-query.gateway.ts:83–120`；`frontend/src/product/timeline/NleWorkspace.tsx:96–113,299–328`。
3. **实际渲染不是 loaded inventory。** `TimelinePresentation` 不接收 revision/track/clip 投影，只接收模拟 playhead、playing、手工 draft ghost 和回调；V1/A1 写死，合成片段需显式开关，区间固定为 4–9 simulated steps；ghost 来自未提交表单字符串，不是已加载或已接受片段。引用：`frontend/src/product/timeline/NleWorkspace.tsx:161–191,224–245,525–532`。
4. **source/capability 也不补足数据。** 默认 AssetGateway 固定 UNAVAILABLE；CapabilityGateway 固定 UNKNOWN；即使注入 source pins，也只有 asset/stream/artifact/digest，无位置/时长。NLE 仅显示 pins 数量，不建立片段库存。引用：`frontend/src/api/app/asset.gateway.ts:1–7`；`frontend/src/api/app/capability.gateway.ts:1–7`；`frontend/src/product/timeline/gateways.ts:153–167`；`frontend/src/product/timeline/NleWorkspace.tsx:341–359`。
5. 后端确有单独 revision snapshot handler，但它不在当前 TimelineQueryGateway，也未接入 NLE；存在 handler 不等于已有获准的 loaded projection。不得为 V9 偷接 snapshot、restore、Operation 或新媒体授权路径。引用：`platform-app/src/main/java/com/example/platform/web/render/TimelineRevisionController.java:166–176,371–391,445–446`；`frontend/src/product/timeline/gateways.ts:93–98`。

**验收含义：** 本次可实现、可验的主路径是明确标注的 bounded local 导航/检查；若声称“真实 loaded clips 导航”，必须证明本次允许范围内实际有数据生产者→校验→scope/revision 绑定→消费链。新增仅供测试注入的类型/fixture、摘要推算或空列表包装，均不能单独建立该结论。真实数据 unavailable、显式空数据和 synthetic/local fixture 必须分开表达。

## exact-time 语义边界

- 前端 `exactMediaTime` 仅校验最长 64 字符的带可选正负号整数/正分母有理数字符串，并原样返回；不做约分、数值比较、非负校验、区间校验或后端 long 范围校验。它接受的负值/超大整数不等于后端语义可接受。`buildDraft` 只另外校验 rate 为正 safe integer；rate 不是 FPS。引用：`frontend/src/product/timeline/types.ts:17–21,48–60`；`frontend/src/product/timeline/NleWorkspace.tsx:70–93`。
- 后端 MediaTime 为非负 long ticks/正 long timeScale，归一化且运算使用 checked arithmetic；帧换算必须显式提供 frame rate。非权威 double reporting 不是时间权威。引用：`shared-kernel/src/main/java/com/example/platform/shared/time/MediaTime.java:6–56,84–94,109–129,224–235`。
- 全局 Selection 时间仍是 `SIMULATED_STEP_0_20` number，`setTime` 会 round/clamp/sort；NLE reducer 同样 round/clamp。现有 Inspector/Agent 将它显示为模拟步数，不能直接塞有理秒/帧，否则静默失真。引用：`frontend/src/interaction/model.ts:9,41,135–140`；`frontend/src/product/timeline/editor-state.ts:1–2,353–354`；`frontend/src/interaction/InteractionShell.tsx:49,111`。
- **V9 检查优先级高：** 精确值保留字符串/精确有理数语义；不同分母比较、等价表示、区间边界及反向/空区间、超 safe-integer 输入、非法分母/小数/空白要有明确结果。像素/slider 数字只能是显示近似，不能反写成 canonical 时间；模拟步长不能叫 frame，不能默认 24/25/30 FPS，也不能把 timer 模拟叫真实播放。上述是待验标准，本文没有运行这些用例。

## Selection、Inspector、生命周期的风险

### 单一 owner 与陈旧上下文

- SelectionProvider 用 workspace/project/surface 建 owner；scope 改变新 lifetime；pagehide 同步 retire，pageshow 创建新 owner；adapter 卸载 retire。只允许一个活动 adapter。引用：`frontend/src/interaction/SelectionContext.tsx:6–34,45–51`；`frontend/src/interaction/model.ts:68–84,128–134`。
- Dispatcher 只从当前 inventory 唯一解析对象，按 lifetime/revision 拒绝旧 selection/proposal，canonical 类别始终拒绝；rename/reveal 需当前已选对象且 adapter supports。inventory 显式复制有限字段，**随手给 SelectedObject 附加时间字段会被丢弃**，不能以类型扩展代替数据流接通。引用：`frontend/src/interaction/model.ts:76–120,145–171,197–202`。
- NLE 现有 `useSurfaceAdapter` 已占 owner，V9 不可另起 competing selection store/adapter。检查点击、键盘、toolbar、Inspector、Agent 指向同一 primary；数据消失/fixture 关闭/切 revision 时旧 selection、reveal 和提案应失效。不能只清组件高亮而保留旧 dispatcher callback。

### EffectiveAccess 不等于授权，也尚未自动覆盖 NLE retirement

- 默认 catalog 是 fail-closed placeholder，非真实五因素服务器投影；query key 只有 access keys，不能据此认定 tenant/session 绑定已经成立。`getEffectiveAccess(null key)` 的 presentation AVAILABLE 不是 canonical grant。引用：`frontend/src/foundation/platformClient.ts:81–108`；`frontend/src/foundation/effectiveAccess.tsx:38–79`。
- ProjectContext 当前只产生 LOADING/ERROR/BLOCKED；recentProjects 仅用于 label，不能证明 Workspace→Project 关系。ProjectFrame 在 LOADING/ERROR 撤掉 shell，BLOCKED 允许 provisional presentation。引用：`frontend/src/foundation/projectContext.tsx:24–39`；`frontend/src/surfaces/FoundationPages.tsx:85–95`。
- **基线只有 WorkflowProjectShell** 将 tenant/context/access factors/error/session retirement 编入 shell key，并同步监听既有 retirement 通知；NLE 走普通 ProductAppShell，而普通 SelectionProvider key 只有 workspace/project/surface。因此不能把 Workflow 已有的 access/session retirement 能力宣称为 NLE 已具备。引用：`frontend/src/surfaces/FoundationPages.tsx:93–112`；`frontend/src/components/app-shell/AppShell.tsx:177–179`；`frontend/src/interaction/SelectionContext.tsx:6–10`。
- V9 应重点验同路径 tenant/context/access error/五因素变化及既有 session retirement 后，旧 owner/导航回调/Inspector draft 是否同步失效；恢复不得复活旧输入。可复用既有通知实现局部边界，不应重写全局 OIDC、伪造 access key 或把 AVAILABLE 接成授权新路径。

### 导航异步与对话框

- HEAD 和 explicit revision selection 有 generation guards；apply/readback 期间锁定 revision 导航，导航 reload 延迟到 readback 释放。必须保持这些边界，尤其快速 A→B 选择、切项目、卸载后迟到响应，以及 APPLIED/NO_OP 后 readback 失败只能重读不能重 apply。引用：`frontend/src/product/timeline/NleWorkspace.tsx:279–339,361–382,413–506`。
- 基线 selection-start 只清 comparison，不清旧 selected；UNAVAILABLE 只改 phase，保留旧 server；比较失败消息又可能被末尾清空。因此 V9 Inspector 若接这些字段，需明确 loading/stale/error，不可把旧 detail 当新请求成功。引用：`frontend/src/product/timeline/editor-state.ts:173–211,351–352`；`frontend/src/product/timeline/NleWorkspace.tsx:370–382`。
- InteractionDialog 已有 focus entry、Tab 边界、Escape stopPropagation、backdrop close 和 connected-launcher 焦点恢复；应复用而非另做不一致的 modal。键盘导航不可劫持输入/组合输入/快捷键修饰键或 dialog 内的 Escape/Home/End。引用：`frontend/src/interaction/InteractionDialog.tsx:6–34`；`frontend/src/product/timeline/NleWorkspace.tsx:199–219`。
- 普通 SelectionInspector 的 mobileOpen 是独立 boolean，不随 primary/lifetime 绑定；Workflow 分支已有更严格 owner 绑定。重点验关闭/清选择/换对象/换 owner 后，NLE 移动检查框是否意外重开或复用旧草稿，以及焦点是否回到仍存在的触发器。引用：`frontend/src/interaction/InteractionShell.tsx:54–83`。

## 交给父 verifier 的最高风险验收清单

- **P0 数据诚实性：** 默认真实网关只提供 metadata；绝不以摘要/ghost/synthetic 伪装 loaded tracks/clips，不增加未授权读取或写入链。
- **P0 权威隔离：** 本地跳转/选取/检查/缩放不触发 preview/apply/restore/render/media 授权；既有高级 Operation 流程、确认与 readback 不被绕过。
- **P0 owner 退休：** scope、tenant/access/session、pagehide/pageshow、unmount 后旧回调和 proposal 失效；恢复新 lifetime，不恢复旧 draft/selection。
- **P1 时间正确性：** 精确有理数字符串与模拟步数隔离，输入失败可见，不用 float/FPS 猜测形成权威，不声称真实播放。
- **P1 检查一致性：** 单 owner、唯一对象解析、primary 一致、空/缺失/stale/加载失败区分；只有真实当前 inventory 的目标可 reveal。
- **P1 交互可达性：** 输入与 dialog 不被 timeline 快捷键干扰；Tab/Escape/焦点恢复及移动检查框生命周期有效。

以上均为基线源码约束与待验风险；未对 writer 的 V9 实现作 PASS/FAIL 判定。
