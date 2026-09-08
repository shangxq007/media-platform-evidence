# V6 Scene / Shot 只读发现与检查 — 本地交付报告

## 状态与决定

- 状态：IMPLEMENTATION_VALIDATED_LOCAL_REVIEW_READY；独立接受尚未完成。
- 本轮恢复依据：Owner 最新明确“批准，继续执行”，仅恢复 classification8 有界补正及最终验证/本地证据。正常工具审批通过，未绕过新 denial。
- 已选功能：PROJECT_SCOPED_SCENE_SHOT_DISCOVERY_AND_READ_ONLY_INSPECTION。没有启动后续 Render / Workflow / NLE / Agent 优先项。
- 未 freeze、commit、merge、push 或远端发布；真实 index 不变。此包只准备交父控制器独立核验及证据发布。

## 精确身份与范围

- 前端工作树：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`。
- 分支：`refs/heads/agent/frontend-wave2-product-ux-v1`；HEAD `f5e19cf53fd010eea2935dd29557e82a879e042c`。
- 已接受 V5 工作内容树：`f62687609a556dff204fc6939416c11abd45f945`。
- 原停止树：`efd0659678306aee5679db900dcee31a2f8a0a64`，未冻结/未接受。
- 最终未提交实现树：`31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`，外部 index/object materialization，非 HEAD tree 冒充。
- V5→最终共 17 个 changed paths（8 新增 Production 文件、9 既有文件）；本次恢复相对 stopped tree 仅 1 个当前分类表变更。
- 根 AGENTS.md 适用，Owner no-freeze/no-Git-mutation 覆盖常规候选冻结规则；无其它范围放宽。无 Skill/Memory 内容编辑。

## 修正与历史失败

原 `final-validation-01/gates/architecture.log` 为真实 FAIL：UNCLASSIFIED_FRONTEND_PATHS=8。targeted/type-policy/lint 当时 native exit 0，architecture native exit 1，后续 gate 当时未执行，不转记成功。此前扩展 allowlist 的调用曾因等待批准超时、0 tool calls 被阻断。

新批准后先核对停止树的实际 bytes/modes/membership、HEAD/index 和 236 个已记录受保护文件；随后 Codex-router acc3 仅在当前 `docs/architecture/governance/frontend-product-path-classification-v1.tsv` 追加 8 行 REUSE 与逐文件 rationale。旧前缀字节保留，controller 复核准确八路径。历史 `h4-frontend-product-surface-disposition-ledger-v1.json`、guards、产品和测试未因这次分类修正改动。

此前 writer 的 RED/GREEN、owner retirement、host-supplied binding、身份预检、稳定 Reset、StrictMode 与 invalid/error 修正保留于 writer 原始记录及 appendices。当前报告以最后修正源码为准，不采用 writer 初始报告中已被 superseded 的虚构固定 real-server key 描述。

## 实现及安全边界

现有 Project Production 注册入口经 ProductionPage → ProductionBrowser，沿用 AppShell、共享 Selection owner、InteractionDialog 与 localization。普通未配置路径明确 unavailable 且不发送 Production 读请求，不自动生成真实身份/成员关系/权限。

显式隔离 fixture source 或未来真实 host 可注入只读 adapter：请求仅包含五维 supplied scope 与 requestId；前端另外用 access/read binding、adapter identity、Selection store lifetime、generation/AbortSignal 做隔离。真实 host 必须给出自己的已约定 SERVER read-key 匹配投影，V6 没有提供实际 agreed endpoint/permission/DTO。

浏览已有 supplied Scene ID/name/description，按 supplied status 筛选、稳定 name+ID 排序、reset；选择 Scene 后只显示显式关联 Shots；共享对话框只检查 supplied identity/name/description/status/version 和安全来源引用。返回保留当前查询/筛选/排序/Scene 与 launcher focus。name/version/status 等不由前端捏造，opaque source 值按字面展示。

loading/refresh/cancel/retry、source error、invalid receipt、stale、unknown/denied/unavailable/unsupported、empty/no-match/no-related、missing/supplied-empty 与 bounded 均有区别。严格校验 request scope/receipt、重复/歧义 identity、异 Project、无效或重复/缺失关系、引用 kind/Project/bounds。只读本地引用详情不执行任意外链、storage URL、download 或目标资源授权。

没有 create/delete/rename/status/member/order/assignment/render/workflow/timeline/preference/canonical/persistent write。Scene/Shot 未伪装成 Selection 的 NODE/CLIP/LANE，没有新的全局 authority。没有 backend 分支、任务、进程、runtime、gates 或 evidence 编辑，也没有要求并行 backend stationarity。

## 最终 exact-source 七 gates（全新执行）

原始 commands/containment/elapsed/native exit 位于 `validation/gates/*.json`，完整 stdout/stderr 位于同名 `.log`；执行图 `validation/FINAL_VALIDATION_PLAN.json`。所有 gates 使用外部 exact tree snapshot，bwrap 中仓库与 snapshot 只读，构建输出明确重定向外部 build。未刷新 tracked frontend dist 或 backend static。

| gate | 真实结果 |
|---|---|
| targeted-final | native 0；204/204 passing；0 failed/skipped |
| type-policy (`npm run typecheck`) | native 0 |
| lint (全部 src ts/tsx) | native 0；46 个历史 warning identities 完全相同，新增/消失均 0 |
| architecture | native 0；UNCLASSIFIED_FRONTEND_PATHS=0 |
| architecture-controls | native 0；Node TAP 120 passed，0 fail/cancel/skip/todo |
| full-frontend-final | native 0；797/797 passed，38 reporter 文件，0 fail/skip |
| build-final | native 0；外部 multi-entry Vite build + 明确 fixture.html |

完整 identity 对账以 `[relative file, ancestorTitles array, exact title]` multiset，读取 V5 原始 reporter 724 unique passed：最终 797，新增 73、移除 0、duplicate 0、失败 0、跳过 0。不是文本 test declaration 计数；完整两端名单和 hashes 都在 `validation/TEST_IDENTITY_ACCOUNTING.json`。focused Production 72 个实例同时包含在 204 targeted 和 797 full 中，不能相加膨胀。

V5 历史数字（724 full /299 targeted /+20−0 /7 gates /32 browser）仅是被采纳历史事实，不是 V6 新结果。

## 真实浏览器及构建证据

最终 Chromium `browser-final-02` 对同一 build 36/36 检查通过，19 张真实截图，1440×1000、768×1024、390×844。普通应用入口 unavailable，另一个显式 localhost fixture host 在原最终注册 route tree 外注入 ProductionSourceProvider；该 host 不是产品 URL fixture 功能。native pointer、Tab/Enter/Escape/ArrowDown、Control+A/Input.insertText 覆盖 Scene→Shot→return，宽窄 search/status/sort/reset/no-match/empty/error/retry；另有 loading/cancel-late-reply/bounded/invalid/stale/denied。

原始 `browser/NATIVE_COMMANDS.json`、`NATIVE_CHECKS.json`、`PER_CHECK_COMMAND_WINDOWS.json` 保留每项 expected/actual/source tree 和输入窗口。DOM locators/scrollIntoView、locale helper、fixture outcome/delay/resolution、disposable localStorage 中惰性模拟 auth marker、CDP focus emulation 全部明确披露；不是物理键盘设备、触摸、IME、screen-reader、真实 backend/auth 或真实 bfcache 验证。

最终 browser assertion/Chromium/wrapper native exit 都为 0。fixture server 是完成后主动 SIGTERM：exit −15；remaining ports 空，不伪报 server native 0。仅模拟 `/api/v1/me/dashboard` GET；Production HTTP 请求 0、HTTP mutation 0。

首次浏览器 run 的 29 pass/15 图是同树较窄覆盖，保留但不累加；扩充 narrow 核心流程后完整重跑最终 36 项。无 browser 产品失败或 source 修正。

完整 emitted 输出为 **14 个文件**（本次 multi-entry，包括 fixture entry/html 和 manifest），不是照搬前代“8 文件”数字。所有 14 文件 HTTP served bytes 等于 disk SHA256，required asset references missing=0。历史 `/vite.svg` 可选 icon 在两份 HTML 的引用仍缺失，浏览器产生一次对应 404；不是缺 JS/CSS。大于 500kB chunk 警告保留，未增依赖或调整阈值。开发型 React DevTools info 日志来自所构建现有配置，未抹去；无 Runtime.exceptionThrown。

所有原 JS 完整收录；较大 JS 额外有 Unicode 边界有序 review chunks 与 reconstruction map，拼接逐字节等于原 JS。

## 可视化复核与已知局限

已读取全部 19 图 contact sheet，以及 desktop Scene 与 narrow 中文 Shot 原图。desktop 两列、字面标签、模拟/只读提示清楚；narrow controls 堆叠，浏览区域需纵向滚动，未承诺所有 Scene 首屏显示。narrow Shot 对话框当前在较低位置打开，有内部竖向滚动；截图底部不能一次显示全部引用说明，不把 document-width PASS 解释为无滚动/全内容首屏。关闭按钮可见，Escape/焦点返回经过验证。中文界面内的英文 Scene/Shot/opaque status 是 supplied data，非前端翻译推断。设备/IME/屏幕阅读器人工接受仍待完成。

## V5 保留与 backend 对接处置

现有 UX_WAVE_1_REVIEW 已追加被采纳 V5 technical review 和限制：title/position history 上限 50，一次 completed group drag 为一条，各 title input change 一条，不恢复 Selection/camera，不持久化，不是 canonical Revision undo。此次没有改动这些产品代码。

现有 IA 记录优先序 SceneShot > Render observability > Workflow UX > bounded NLE > Agent creative，仅首项获授权。IA 原文仍含其历史 documentation-only 阶段的 runtime disclaimer/recommended step；不得用那些历史段落否定本次真实执行，亦不据此启动旧 F2 或后续实现。

复用 `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` 与既有 gap ledger 的 FB-GAP-007，覆盖 supplied fields/identity/explicit relations/access/nondisclosure/bounded/version/context/stale/safe refs，复用 FB-GAP-001/002/004/008 边界。只提出一次未来固定 frontend tree/build + backend version 的 controlled Project readonly 联调，authorized/denied/error/stale 与 zero writes；没有真实 integration 或 backend 授权。

## 本地包与复核入口

`REVIEW_INDEX.md` / `REVIEW_INDEX.json` 提供两端每 changed path、完整 patch、before/final endpoints、完整 frontend supporting source/scripts/config、原测试 logs/native exits、合同映射、backend 文档、14 build outputs、19 screenshots 与历史失败。

完整 V5→final binary/full-index patch 在 disposable 外部 index replay，native apply=0，write-tree 精确等于 `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`。真实 index/HEAD/分支和最终 scoped 1004 paths bytes/modes/membership 一致；986 个 allowlist 外 baseline paths 与 236 个已记录历史/dist 文件无差异。此为有界保留声明，不是全系统/并行后端 stationary 声明。

本地生成器执行 manifest 与 ZIP 每 entry 哈希/解压完整性核验；结果在 task root `LOCAL_PACKAGE_VERIFICATION.json`（detached，不制造 self-hash 循环）。父控制器应先独立核对 index/manifest/receipt，再按其授权仅发布 evidence；本轮 remote mutations=0。此报告不宣称独立接受或产品发布。
