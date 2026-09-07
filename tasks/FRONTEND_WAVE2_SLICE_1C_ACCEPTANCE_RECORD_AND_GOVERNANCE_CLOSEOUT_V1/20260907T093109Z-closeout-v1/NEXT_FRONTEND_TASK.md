# 唯一建议下一项：command discovery/accessibility convergence

## 既有计划位置与命名

现有计划：`FRONTEND_WAVE2_SELECTION_AND_CANVAS_INTERACTION_DECISION_RECOVERY_V1`，实际文件及字节副本见 `SOURCE_INDEX.json` / `sources/wave2-plan.md:53–55`，条目原名 **command discovery/accessibility convergence**，其后才是 focused Review UX。该计划没有“Slice1D”编号。本简报使用原条目，不为它创造新切片序号；本次状态 PREPARED_NOT_IMPLEMENTED。

## 用户场景与当前剩余工作

创作者在 Canvas/NLE/Review 当前上下文中打开统一命令面板，以键盘和搜索发现可用本地操作，知道操作目标及不可用原因，不必试点隐藏入口，也不误把 synthetic proposal 当成已授权业务操作。

只读 source finding：`frontend/src/components/design-system/index.tsx:154–166` 当前 PaletteAction/PaletteContent 用 label filter 和 native button 列表；已有 no-match 文案、disabled reason、InteractionDialog。`frontend/src/interaction/InteractionShell.tsx:106–117` 已从当前 Selection 派生 inspect/reveal/clear/Agent/read-only compare 等命令并通过 store.dispatch；因此不重造 command registry 或 action router。剩余可交付 UI 工作应限定为该既有面板的键盘搜索结果导航、结果/不可用说明的可访问关联与状态公告，并验证 scope 改变后的当前上下文，不宣称现有 focus trap、搜索或共享 dispatcher 尚未实现。

## Included / Excluded

Included：在现有命令面板内使搜索输入与结果形成可理解的键盘导航；搜索改变时活动结果重置/重解算；支持 ArrowUp/Down 与 Home/End 的面板内候选导航，Enter 仅触发当下可执行命令，保留 Tab/native button 路径；无结果状态与结果数量采用 en/zh-CN 可访问公告；不可用动作原因通过可访问描述关联，而非授予权限；命令目标与 Selection count/primary 上下文一致。

Excluded：新业务操作、快捷键全局重映射框架、路由/Selection lifetime 改造、selection bookmarks/storage/history、Canvas gestures、Review 新功能、Timeline/History/permission 权威、真实 Agent/OperationPlan 集成、backend API/build/static/dist、竞品重新选型、A/B 布局重开、产品 commit/publication。

## 预期文件与设计依据

预期有界路径（未来授权时核定逐路径 allowlist）：
- `frontend/src/components/design-system/index.tsx`（现有 PaletteContent）
- `frontend/src/components/design-system/index.test.tsx` 若为新增测试文件需未来授权逐路径确认和现有 path ledger 分类；当前没有该既存测试文件，不把它冒充现有 authority。优先复用 `frontend/src/interaction/InteractionShell.test.tsx`。
- `frontend/src/interaction/InteractionShell.tsx`、`InteractionShell.test.tsx`（仅必要的 command projection/interaction 验证）
- `frontend/src/components/app-shell/AppShell.tsx` 及其现有 tests（仅如 shell invocation 真正受影响）
- `frontend/src/localization/catalogs.ts`、`source-manifest.json`（新增文案）
- `frontend/src/styles/foundation.css`（仅必要 focus/disabled/overflow 样式）

权威设计路径：`docs/architecture/governance/frontend-product-information-architecture-v1.md` 的 Commands and keyboard architecture、Accessibility、Responsive behavior；`frontend/governance/agent-shell-convergence/DESIGN.md:5–11` 的单一 Selection、typed action lowering、A-only horizontal Studio、单 contextual inspector 与统一 InteractionDialog；`frontend/governance/pre-freeze-closure-v1/DESIGN.md` 的 creator-first 层级与 synthetic boundaries。这些已存在设计是本任务依据，不选择新竞品。旧 `layout-convergence/UX_LAYOUT_ALTERNATIVE_A/README.md` 曾写 human selection required；其后 A-only design 是后续收敛记录，不把旧行复活为必须重选 A/B 的 blocker。

本 brief 提议沿用 native buttons 的导航模式，不擅自引入 role=application 或替代性全局 listbox authority。若未来 executor 认为必须改成 combobox/listbox，应先给出具体焦点/ARIA 合约供 review，不将这项具体缺失决策替换为全站 redesign。

## Interaction、context、permission、mock 边界

所有 toolbar/palette/shortcut/Agent 入口继续经过现有 ProductAction/InteractionIntent；registry 是 discovery，不是另一执行权威。面板 query、活动候选与 focus 是 local ephemeral；不得持有另一份可执行 Selection snapshot。执行时由当前 store 的 scope/lifetime/revision 和 adapter resolution 决定本地 action 是否仍有效，失效/消失的命令不能按旧缓存对象执行；context 变化重新投影，不把路由变成 Selection writer。

Backend 仍是 canonical authorization authority；EffectiveAction 投影缺失/unknown/malformed 时 fail closed；当前 synthetic fixture 与 `SYNTHETIC_EFFECTIVE_ACTION_PROJECTION` 标签维持，不将 feature flag、Agent、搜索可见性、disabled reason 或“本地支持”升级为业务权限。只读 query 仍走已有 gateway，canonical mutations 仍 lower 到既有后端 application/Operation 合约；generic canonical Apply 保持 disabled。

真正 backend gaps 已存在：`frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` 的 UXW1-006（discover/prepare）、UXW1-007（execute），及 `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md` 的 FB-GAP-002（effective access）。此次本地面板键盘/公告无需新 backend contract；不追加重复条目、不启动后端。若未来扩展真实语义操作，必须在既有需求表写 scenario/consumer、gap、permission/failure、mock 与 integration acceptance，不能通过本 brief 偷渡。

## 聚焦验收与 impact-based validation（仅未来执行）

1. 打开面板焦点进入搜索；搜索筛选后 keyboard navigation 的候选可见，边界确定；no-match 不残留可执行旧候选。
2. Enter/Space、Tab 路径与 pointer invocation 命中同一 stable command ID/dispatcher；disabled item 不执行且原因可被辅助技术关联；Escape/focus restoration 沿用 InteractionDialog。
3. IME composition、editable 输入与浏览器/OS reserved shortcuts 不误执行；不新设全局监听处理 Canvas shortcuts。
4. Selection/primary、project/surface/lifetime 改变后 stale candidate 不执行；无第二 Selection store 或 permission cache。
5. en/zh-CN 搜索结果/空态/原因和 status 公告正确，stable IDs 与 locale 独立；长标签及移动宽度可读，不遮住关闭/搜索。
6. semantic unavailable/unknown 与 synthetic 两类解释保持诚实；本地动作无新 server mutation，query/canonical 已有边界不变。

未来仅跑受影响面板/interaction/localization tests、相关 type/lint/architecture checks；是否需要 native keyboard/accessibility smoke 和定向 build 由该未来 task 的影响与授权决定，只验证新面板行为，不重跑已接受 pagehide/validator qualification。不得把本 brief 当作本 closeout 已执行测试的凭据。物理设备/OS IME/屏幕阅读器没有真实运行就标未建立。

## Dependencies 与具体未来授权

原计划要求 independently accepted Selection/Canvas slices 后推进此条目。当前 bounded 技术结论已采纳；formal Slice1C ledger 集成和整体 acceptance 未声明，因此严格按原顺序自动开始 implementation 的条件未获证明。Owner 可在审阅本包后明确接受整体 Slice1C 范围，或明确授权该独立 local-UI continuation 不等待 formal ledger integration；这不 waive H4/dist freeze gates。

NEXT_FRONTEND_TASK_ELIGIBILITY=PREPARED_CONDITIONAL_ON_EXPLICIT_BOUNDED_IMPLEMENTATION_AUTHORIZATION
可以在产品 publication 前独立开展；不要求 backend lane 静止。H4/dist 不是该 local UI 功能的技术依赖，但仍限制未来 freeze。当前 task 不包含任何实施授权；未来需明确 allowlist、上列焦点/键盘契约、scope 隔离和 impact-based validation 后再执行。未实现本切片。
