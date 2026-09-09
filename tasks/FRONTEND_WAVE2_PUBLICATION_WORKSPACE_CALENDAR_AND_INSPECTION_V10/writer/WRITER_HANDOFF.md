# V10 Writer 交接：发布工作区、月历与只读检查

Writer 实现已完成，源码接口稳定，交由 Hermes 执行最终七门禁、完整测试身份核对、外部构建、原生 Chromium 检查与交付。**本文件不是独立评审、最终验收或产品交付声明。未创建提交，未冻结产品 SHA，未操作真实 index、HEAD、stash 或远端。**

## 实现与边界

在现有 Project AppShell 中新增 `/w/$workspaceId/projects/$projectId/publication`，导航显示 `Publication workspace` / `发布工作区`，成熟度 PREVIEW。普通入口显示 `Publication source not connected` / `尚未连接发布数据源`，没有默认 fixture、URL 开关、发布账号连接、发布或假成功按钮。

显式隔离 host 提供当前 Project 的数据后，可进行内容搜索、稳定账号 ID 筛选、原始来源状态筛选、显式来源时间升降序、筛选重置、刷新/重读、列表与月历切换、上一月/下一月/今天/选择日期、日期 agenda、多条同日记录与 overflow、详情检查和有上下文的关闭返回。筛选在两个视图间共享；刷新保留 query/date/zone/view/scroll，并恢复仍存在的 Selection。刷新时撤下旧详情，校验成功也不自动重新打开。同 ID 再出现不恢复旧详情。

Calendar 采用显式 `timeField` (`scheduledAt | publishedAt | unscheduled | unknown`)。只把严格的带 offset/Z 绝对时间放入日历；毫秒精度，支持 1–3 位小数。日期字符串、无 offset、缺失/null、非法公历日期和 `-00:00` 均不确定。未排期与不确定日期分别列出，不会归入今天。未来计划时间、实际发布时间、尝试时间、获取时间分别标识；到期不代表发布，未返回不代表不存在。按 civil date 枚举月份，Intl 按显式时区转换；月份区间为本地起日包含、下一月起日不包含，不按每个本地日 24 小时计算。列表时间排序的相同时间使用 plan ID 确定顺序，无有效时间置后。UTC 是清晰可选的初始显示时区，不是未知来源时间的默认解释。可选时区共 8 个，见组件内 `displayZones`。

详情保留计划、尝试、ExternalPublication 的独立 ID 和显式关联。一个平台的两个账号不合并。展示得到单独许可的 title/summary/copyVersion、Project、账号、OutputArtifact 逻辑引用和允许元数据、各类时间、尝试关联、原始/未知状态与允许的失败摘要。外部 URL 全部省略；没有 Artifact 稳定目标及独立访问谓词，因此没有跳转/预览/下载/公共链接，只有允许的惰性逻辑引用及限制说明。

复用 SelectionProvider、LOCAL_EPHEMERAL dispatcher、SurfaceAdapter 与 InteractionDialog。仅扩展 `PUBLICATION` 展示 Selection kind，避免冒充 NODE/CLIP，不赋予任何移动/重命名/规范操作权限。真实 SDK 可信同会话续期保留浏览；身份、权限、scope、adapter、owner 或 Selection lifetime 变化取消/隔离旧请求及保留回调。**原生会话 retirement 后旧 source binding 被禁止再次读取；host 必须提供新的 scope/owner binding。** 这修复了测试发现的“撤下后立即通过旧 host 重读”问题。旧 dismiss 也不能关闭同 ID 的新 dialog occurrence。

## 实际契约、计划与缺口

先读实际 foundation/AppShell/Operation/EffectiveAccess/Selection、V9 生命周期、现有 IA/检查点、backend requests、gap/current/classification ledgers，再写 `SCOPE_AND_CONTRACT.md`，随后测试与产品代码。`before.json` 记录适用根 AGENTS 和真实 Git 状态。Owner 明确 no-commit/no-freeze 高于 AGENTS 候选 SHA 冻结要求；未编辑指令。历史 Vue AppShell 文档的暂停/旧路由说明是设计历史，当前 Owner 和实际 React foundation 优先。

仓库中没有既有 Publication surface、Publication 查询或真实 access 契约。恢复 **DOM-PUBLICATION-001 = PROPOSAL**：OutputArtifact → PublicationAttempt → ExternalPublication，计划/intent 单独标识；ObservationSet 的历史 `observedAt` 与原始平台指标语义保留为未来提案，本次无指标实现。

**FRONTEND_CONSUMPTION_PROPOSAL；REAL_BACKEND_CONTRACT_NOT_ESTABLISHED。** TypeScript 类型、状态和 `test-only.publication.*` access key 只用于前端隔离验证，不是 backend DTO/权限 authority。Source 的 self-allowed flag 没有授权效力。host 的 EffectiveAccessCatalog 分别提供 list、各 plan content、各 artifact metadata 许可，检查匹配 key、SERVER、AVAILABLE 和五因子 SATISFIED/NOT_APPLICABLE。SERVER 样式的测试输入也只证明前端验证，不证明真实权限。

响应检查请求 ID、principal/tenant/session/Workspace/Project/source、完整 query、稳定 version、complete/bounded/partial、每类唯一 ID、显式 plan/account/artifact/attempt/external 关系。受限 copy/artifact/failure 值先裁剪，再进入 Selection 和 DOM；未知字段及 URL 被 schema 丢弃。未来 backend 必须先裁剪响应，客户端 DOM 省略不构成保密边界。

复用现有台账并新增 **FB-GAP-014**（没有相关现存 Publication ID），不塞进 NLE/Render/Scene-Shot。最低未来真实场景：固定 frontend/backend/adapter 版本，一个 Project 可发布 OutputArtifact + 一个 account/content version → backend stable intent → 单一 scheduler → PublicationAttempt/ExternalPublication 实际 success/failure/unknown。需约定身份/访问、分页/完整性、timezone/time、元数据裁剪、raw+mapped statuses、关联、idempotency/重复防御、安全错误/凭证过期及 Postiz adapter 版本依赖。Postiz 单通道技术试点和真实发布分别授权，本次不接 private API/DB，不使用 OAuth/凭据，不实现后端。

现有 IA 中追加 Owner **新**优先级：V9 有界接受后 Publication 第一，完整 NLE editing/Agent 后续；热力图/跨平台分析延期。现有 UX review 追加 V9 有界接受，保留长标题 inspector 布局限制，不修改密封报告、不声称完整 NLE/媒体/平台访问/产品/EP19/Slice1C 关闭。H4 Proposal A 只在 current/classification 追加准确新路径，历史 ledger 不变，无 debt-zero 或门禁削弱。

## 原生 RED → GREEN 与校验

每个运行目录都有 `command.json`（精确 argv、cwd、UTC 起止、exit）和未经改写的 `output.log`。Vitest/ESLint 原生 JSON 是 `results.json`。总表在 `RUN_SUMMARY.json`，测试身份在 `targeted-identity.json`，warning 身份在 `lint-identity.json`。

| 运行 | 原生结果 | 说明 |
|---|---|---|
| red-01 / red-02 | exit 1 | 路径/配置启动失败，不算行为 RED；临时误建的空嵌套目录经普通 mv/rmdir 纠正，无早期工作删除 |
| red-03 | exit 1，0 collected | 新模块缺失，不算行为断言 RED |
| red-behavior | exit 1，16 = 1 pass + 15 fail | 最小 unavailable shell 下真实行为 RED；其断言保留 |
| green-01 | exit 0，19 pass | 16 Publication + 3 registry |
| lifecycle-red | exit 1，66 = 64 pass + 2 fail | 真正旧会话重读缺陷；另一个是新测试点击 view switch 前已分离 DOM，改为查询当前 agenda，不削弱原有断言 |
| lifecycle-green | exit 0，66 pass | 真实生命周期修复后通过 |
| final-targeted | exit 0，194 pass，0 fail/pending | 8 个受影响 suite |
| final-typecheck | exit 0 | `npm run typecheck` |
| final-lint | exit 0，46 warnings，0 新身份 | 与 V9 `validation-03/LINT.json` 的 file/rule/severity/line/column/end/message 完全相同 |
| final-architecture | exit 0，PASS | 首次扫描 calendar label `bucket` 被 raw-storage guard 拒绝，改为 `calendarField`；guard 与 controls 源码未改 |
| architecture-controls | exit 0，TAP 131/131 pass | 原 negative controls 完整保留 |
| final-evidence | exit 0 | scope、HEAD/index/stash、hash、原生 JSON 算术与 `git diff --check` 校验 |

最终 targeted **194 = 170 个 baseline 保留身份 + 24 个新增身份，0 移除/重复**。新增为 22 个 Publication 测试、1 个 V10 route/native-session 测试，以及既有 AppShell 参数化测试因新 surface 自然增加的 `shared notification entry has exactly one fail-closed entry on publication`。AppShell 测试源码没有改动。现有 registry 精确数组仅增加新 surface，不删除或放松以前的断言。两个既有 InteractionShell 非法路由测试仍有 TanStack notFound 提示，原日志保留。

覆盖 unavailable/loading/complete empty/partial empty/filter empty/error/restricted/retry；严格 offset/日期、月末/年末/闰年/跨午夜/DST；同平台双账号、过滤/稳定 ties；独立多尝试/外部未知状态；secret sentinels 及受限元数据省略；按钮非 submit、dialog Tab/Escape/focus、长标题；late receipts/abort、真正保留的 filter/date/view/open/refresh/dismiss handlers、owner/访问/身份变化、同 ID 不复活、刷新消失后的 Selection 和安全焦点；timezone/view/refresh 保留上下文；真实路由及 SDK 事件 mock 的续期/retirement。

最终相关命令（cwd=`frontend/`，report 输出均为当前 taskroot/writer 下绝对路径；完整 argv 在对应 command.json）：

```text
node node_modules/vitest/vitest.mjs run src/product/publication src/app/routeTree.test.tsx src/foundation/surfaceRegistry.test.ts src/interaction src/components/app-shell/AppShell.test.tsx src/localization --configLoader runner --no-cache --reporter=default --reporter=json --outputFile=<writer>/final-targeted/results.json
npm run typecheck
node node_modules/eslint/bin/eslint.js src --format json --output-file <writer>/final-lint/results.json
npm run architecture:guard
npm run architecture:guard:test
```

未执行最终完整 918 baseline 重验、build、browser 或 backend/EP19 门禁。Hermes 应按最终源码重新执行既定七门禁与完整身份核对，而不是把此 targeted 数字当成完整结果。

## 稳定显式 host 接口与原生 Chromium 检查入口

入口导出在 `frontend/src/product/publication/PublicationWorkspace.tsx`：

```tsx
<PublicationSourceProvider source={stableSource}>
  <RouterProvider router={router} />
</PublicationSourceProvider>

// 独立验证 host 也可直接复用现有 owner；不要再套第二个 Selection owner。
<LocalizationProvider initialLocale="en">
  <SelectionProvider scope={{ surfaceId: 'publication', workspaceId: 'w', projectId: 'p' }}>
    <PublicationWorkspace workspaceId="w" projectId="p" tenantId="tenant"
      source={stableSource} now={() => new Date('2024-03-10T12:00:00Z')} />
  </SelectionProvider>
</LocalizationProvider>
```

`source` prop 优先于 Provider，未提供时 unavailable。`now` 仅为可选测试时钟（默认真实 Date）；不改变 source 时间。原路由仍由 ProjectFrame 校验 Workspace/Project/tenant；完整路由验证 host 需用既有 platformClient 测试边界提供一致的 Workspace context，不能把 fixture 当成真实 Project/access。V10 route test 有完整可执行例子；writer 未创建浏览器适配器。Parent 可在外部 evidence host 明确导入 `publication/testing.ts` 的 `source()` / `receipt(request, overrides)` / `grant(key)`；该文件没有 vitest import，产品入口不导入它。样例日期是 2024-03，可使用 direct host 的 `now`，或者由 parent 显式提供当前月份数据。请保持 source.owner、adapter 稳定，仅在真实验证上下文变化时以不可变新值更新 scope/access/owner；不要每次 render 调用 source()。

`types.ts` 为完整接口。核心 request：

```ts
{
  scope: { principalId, tenantId, sessionId, workspaceId, projectId, sourceId },
  requestId,
  query: { kind: 'project-publication-snapshot', limit: 200 }
}
```

`adapter.origin='isolated-verification'`，`read(request, signal): Promise<unknown>`。成功 receipt 须 echo request 三项并提供 `status:'ok'`, `version`, `completeness`, `accounts[]`, `plans[]`, `artifacts[]`, `attempts[]`, `externalPublications[]`；时间可省略/null，所有显式关系必须在 snapshot 内成立。失败 receipt echo request 并给 `status:'unavailable'|'restricted'|'error'`；抛错只显示通用消息。没有周期 polling 或自动重试。权限 key 导出 `LIST_KEY`、`contentKey(planId)`、`artifactKey(artifactId)`。

建议原生 selector/labels：

| 用途 | EN | 中文 / 稳定结构 |
|---|---|---|
| 普通入口 | Publication source not connected | 尚未连接发布数据源 |
| 主区域 | region: Publication workspace | 发布工作区；shell `[data-surface="publication"]` |
| 搜索 | Search supplied publications | 搜索已提供的发布内容 |
| 账号 / 状态 | Account / Source status | 账号 / 来源状态；select value 为稳定 ID / raw status |
| 排序 | Sort by chosen source time | 按选定来源时间排序；asc/desc |
| 重置 / 读取 | Reset filters / Refresh publications / Retry publications | 重置筛选 / 刷新发布数据 / 重新读取发布数据 |
| 视图 | List / Calendar | 列表 / 日历；aria-pressed |
| 时区 | Display timezone | 显示时区；UTC、America/New_York、Asia/Shanghai 等 |
| 月份 | Previous month / Next month / Today | 上个月 / 下个月 / 今天 |
| 日期 | button aria-label=`YYYY-MM-DD` | aria-pressed 所选；aria-current=date 今天；可见非纯颜色文字 |
| overflow | `2 more · 2024-03-10` | `另有 2 项 · 2024-03-10` |
| 日期 agenda | region: Selected day agenda | 所选日期列表 |
| 分离日期 | region: Unscheduled / Indeterminate date | 未排期 / 日期不确定 |
| 结果滚动区 | region: Publication results | 发布结果；`.ff-publication-results` |
| 详情 | dialog: Publication details | 发布详情；`.ff-publication-details` |
| 关闭 | Close publication details | 关闭发布详情；Escape / backdrop 同样可用 |

行按钮 accessible name 是许可 title，否则稳定 plan ID；account select 展示 supplied name + platform + ID。同日两个 preview 和 overflow 均不改变 source 日期，选日后 agenda 展示该日所有已提供匹配项。可检查 EN/中文、桌面和窄屏、长标题/无空格文案、月份末尾、timezone 跨日、Tab/Escape 焦点、刷新/重试、隔离 host 变更及旧回调。窄屏主要通过日期按钮与 agenda 浏览，非 week/drag/reschedule。

## 精确文件与保全

相对 V9 actual baseline，修改 15 个既有文件、新增 7 个。`changed-paths.json`、`SOURCE_MANIFEST.json` 与 **V10-only.patch** 是准确清单/内容；不要把 `git diff HEAD` 中前期的大量未提交工作归为 V10。

既有修改：

```text
docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md
docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv
docs/architecture/governance/frontend-product-information-architecture-v1.md
docs/architecture/governance/frontend-product-path-classification-v1.tsv
frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv
frontend/governance/UX_WAVE_1_REVIEW.md
frontend/src/app/routeTree.test.tsx
frontend/src/app/routeTree.tsx
frontend/src/components/app-shell/AppShell.tsx
frontend/src/foundation/surfaceRegistry.test.ts
frontend/src/foundation/surfaceRegistry.ts
frontend/src/interaction/model.ts
frontend/src/localization/catalogs.ts
frontend/src/localization/source-manifest.json
frontend/src/surfaces/FoundationPages.tsx
```

新增：

```text
frontend/src/product/publication/PublicationWorkspace.tsx
frontend/src/product/publication/PublicationWorkspace.test.tsx
frontend/src/product/publication/model.ts
frontend/src/product/publication/model.test.ts
frontend/src/product/publication/types.ts
frontend/src/product/publication/testing.ts
frontend/src/product/publication/publication.css
```

Recovery 的其余 **994 文件 hash 不变**，删除 0、未预期路径 0。已改 baseline 原文保存在 `baseline-changed/`，V10 patch 可独立审阅。真实 index SHA256 保持 `675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`；HEAD=`f5e19cf53fd010eea2935dd29557e82a879e042c`，parent=`01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`，branch=`agent/frontend-wave2-product-ux-v1`，stash 未变。`SOURCE_MANIFEST.json` SHA256=`6f8bd89e6bf9b511fb8ca3fee711755f0eff8042ebc2bea212c6ec3a6e34246e`。无 candidate commit；该 SHA256 是文件清单摘要，不是 Git tree/acceptance SHA。

没有 backend/EP19、tracked dist/backend static、依赖/build config、Skill/Memory、AGENTS、auth 全局实现或 architecture guard 修改；没有 stage/commit/reset/clean/stash/merge/push/deploy/远端 mutation。没有真实凭据、账号连接或发送；没有 publication scheduler/Agent/NLE/Workflow/analytics 扩展。父级独立最终 reviewer 未被请求，writer 到此交接，不启动评审。
