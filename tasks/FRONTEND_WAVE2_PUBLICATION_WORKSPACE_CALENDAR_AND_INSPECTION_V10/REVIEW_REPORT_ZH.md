# V10 小型本地证据评审包

**仅已存在证据的打包和完整性核验；不是产品验收或独立最终评审。发布字段封为 NOT_YET_PUBLISHED，不猜测未来commit。产品不提交、不freeze、不merge/push/deploy。**

最终 actual tree `afc966ad4872e6dd65997281c75fe49e7aaed376`。最终证据以 validation-02 和 browser-v10-final02 为准；早期 handoff 的194/未验状态是历史，不能覆盖更正后的197/945与两轮native记录。

## 审查入口

- [完整V10补丁](validation-02/TASK_DELTA.patch) · [before/after哈希](validation-02/SOURCE_DELTA.json)
- [最终七门禁](validation-02/REQUIRED_GATE_SUMMARY.json) · [完整测试身份](FULL_TEST_IDENTITIES.json) · [完整lint身份](FULL_LINT_IDENTITIES.json)
- [最终浏览器交接](browser-v10-final02/BROWSER_HANDOFF.md) · [父四图视觉记录](BROWSER_PARENT_VERIFICATION.json)
- [更正前视觉问题](VISUAL_CORRECTION_01.md) · [更正交接及RED/GREEN](writer/CORRECTION_01_HANDOFF.md)
- [官方参考研究及原始来源](research/OFFICIAL_REFERENCE_RESEARCH.md) · [完整原始brief](WRITER_BRIEF.md)

## 全部字段

### TASK

FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10

### LANE

FRONTEND

### FRONTEND_BRANCH

refs/heads/agent/frontend-wave2-product-ux-v1

### REF

refs/heads/agent/frontend-wave2-product-ux-v1

### REQUIREMENTS_RECOVERY

完整 WRITER_BRIEF.md 原文随包。使用 brief 与本次明确补充字段；不声称已恢复父会话未提供的逐字原始字段名。

### PRIOR_V9_REVIEW_ADOPTION_RECORDED

YES_BOUNDED：既有 UX_WAVE_1_REVIEW.md 追加本地 navigation/locate/selection/metadata 与生命周期修复的有界采纳。长标题 inspector 限制保留；不是完整 NLE editing、媒体播放、平台访问或产品/EP19/Slice1C 关闭。sealed V9 未改。

### PRIOR_V9_EVIDENCE

```json
{
  "commit": "41cb3d631e2851cc2c7c0ee83b90b2522c1193ef",
  "manifest_sha256": "77505e42e41ff3956b253c00ab392521cd6375ae97aeb51cbea34db618485072",
  "source": "WRITER_BRIEF.md"
}
```

### PLAN_SOURCE_AND_ITEM

```json
{
  "source": "validation-02/source/docs/architecture/governance/frontend-product-information-architecture-v1.md",
  "scope": "writer/SCOPE_AND_CONTRACT.md",
  "priority": "Owner 新优先级：V9 有界接受之后 publication workspace 第一；完整 NLE editing/Agent 后续；Postiz 单通道技术试点及真实发布分别授权；heatmap/跨平台analytics延期。不是原计划一直如此。"
}
```

### BASELINE_IMPLEMENTATION_TREE

37d003fc4f55faf166cd836a6ea93d77eb8b6a1e

### FINAL_IMPLEMENTATION_TREE

afc966ad4872e6dd65997281c75fe49e7aaed376

### CANDIDATE_COMMIT

NOT_CREATED

### EXISTING_HEAD

f5e19cf53fd010eea2935dd29557e82a879e042c

### USER_VISIBLE_OUTCOME

现有 Project AppShell 新增 PREVIEW 发布工作区。普通没有 source 时明确尚未连接，不默认注入数据。显式隔离 host 下可搜索、按稳定账号ID和原始状态过滤、按明确来源时间稳定排序、重置、刷新/重读、列表/月历切换、日期agenda、只读详情和有上下文返回。无真实发送或假成功按钮。

### REUSED_SURFACES_AND_CONTRACTS

复用 ProjectFrame/AppShell/routeTree、设计 primitives、i18n、SelectionProvider 单一 owner、LOCAL_EPHEMERAL dispatcher、SurfaceAdapter、InteractionDialog；PUBLICATION selection kind 不赋予 canonical 操作权限。

### CALENDAR_AND_LIST_BEHAVIOR

月视图、前后月、今天、选中日agenda、多条同日记录与overflow；当前日/选择/状态不只用颜色。列表/月历共享查询和过滤；同平台多账号独立；相同时刻用plan ID稳定打破平局。窄屏日期agenda，无周视图/拖拽/改期。未排期与不确定时间分开，永不自动归今天。

### TIMEZONE_AND_TIME_SEMANTICS

显式可选显示时区，仅改变呈现不更改来源计划；UTC是可见初始显示选项，不推断未知时间。timeField明确scheduledAt/publishedAt/unscheduled/unknown。严格offset/Z绝对时刻；date-only、offsetless、缺失/非法/-00:00不确定并禁用对应日历归组。civil date月边界左闭右开；支持月末/跨年/闰年/跨午夜/DST，不假设每日24h。due不等于published，省略不等于不存在；不是NLE media time。

### PUBLICATION_DOMAIN_MODEL

DOM-PUBLICATION-001=PROPOSAL。OutputArtifact、独立plan/intent、PublicationAttempt、ExternalPublication 显式稳定关系；多次attempt及多账号结果不合并。未来 ObservationSet observedAt 与raw平台语义保留，未实现metrics。

### FRONTEND_CONSUMPTION_CONTRACT_STATUS

FRONTEND_CONSUMPTION_PROPOSAL

### REAL_BACKEND_CONTRACT_STATUS

REAL_BACKEND_CONTRACT_NOT_ESTABLISHED

### SOURCE_AND_QUERY_BOUNDARIES

隔离provider绑定principal/session/tenant/Workspace/Project/source/access/owner；响应校验request/scope/query echo、唯一ID、版本、required关系及complete|bounded|partial。无配置=unavailable而非empty；frontend enums与test-only权限不是backend DTO authority。

### OPERATION_AND_PERMISSION_BOUNDARIES

EffectiveAccess各项验证，source self-allowed无授权效力；list许可不推导content/artifact/link许可。受限值在DOM/title/aria/data/Selection前移除。外链省略；Artifact仅获许可的惰性逻辑引用，无安全目标与访问predicate时不导航，不preview/download。客户端裁剪不能代替真实后端保密边界。

### SELECTION_INSPECTION_AND_FOCUS_RESULT

允许的标题/摘要、Project、账号、平台copy version、artifact元数据、scheduled/actual/fetched时间、明确attempt关系与raw未知状态。关闭恢复有效launcher或安全fallback；刷新撤详情，同ID再现不自动复活。长summary窄屏换行且内部滚动，关闭仍可见（父代表图证据）。

### CONTEXT_AND_STALE_RESULT_HANDLING

可信有效同会话正常续期保留浏览；真实身份/访问/Project/source/owner/Selection lifetime变化撤数据和详情，abort并generation/ownership拒绝旧响应和保留回调；retired source binding不能自动重读。有效同上下文刷新/视图/关闭保留query/date/zone/scroll/focus；消失清selection。不是任意SDK陈旧事件全面隔离保证。

### MOCK_AND_REAL_DATA_BOUNDARIES

实际native Chromium和实际产品route/组件，loaded source与SDK/access/Project为显式isolated fixture。普通无fixture构建只有真实loopback bootstrap503后Workspace unavailable；另有Project-only fixture不挂Publication provider，实际route呈现source-not-connected，不能当真实集成。light为外部DOM主题probe不是产品主题切换集成。

### POSTIZ_INTEGRATION_STATUS

NOT_PERFORMED

### OFFICIAL_RESEARCH

research/OFFICIAL_REFERENCE_RESEARCH.md（2026-09-09实际访问；原始网页和引用台账随包）。Postiz/Buffer只能作信息组织参考，account不等于platform、显示zone不改schedule；文档非实现/运行版本证明。Buffer原HTML空壳与官方Markdown恢复均保留。无部署/OAuth/账户连接/私有API/DB耦合。

### PRODUCT_CHANGED_PATHS

```json
[
  "frontend/src/app/routeTree.test.tsx",
  "frontend/src/app/routeTree.tsx",
  "frontend/src/components/app-shell/AppShell.tsx",
  "frontend/src/foundation/surfaceRegistry.test.ts",
  "frontend/src/foundation/surfaceRegistry.ts",
  "frontend/src/interaction/model.ts",
  "frontend/src/localization/catalogs.ts",
  "frontend/src/localization/source-manifest.json",
  "frontend/src/product/publication/PublicationWorkspace.test.tsx",
  "frontend/src/product/publication/PublicationWorkspace.tsx",
  "frontend/src/product/publication/model.test.ts",
  "frontend/src/product/publication/model.ts",
  "frontend/src/product/publication/publication.css",
  "frontend/src/product/publication/testing.ts",
  "frontend/src/product/publication/types.ts",
  "frontend/src/surfaces/FoundationPages.tsx"
]
```

### DOCUMENTATION_CHANGED_PATHS

```json
[
  "docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md",
  "docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv",
  "docs/architecture/governance/frontend-product-information-architecture-v1.md",
  "docs/architecture/governance/frontend-product-path-classification-v1.tsv",
  "frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv",
  "frontend/governance/UX_WAVE_1_REVIEW.md"
]
```

### EXACT_SOURCE_DELTA

```json
{
  "paths": 22,
  "modified": 15,
  "added": 7,
  "endpoints": "validation-02/SOURCE_DELTA.json",
  "full_patch": "validation-02/TASK_DELTA.patch",
  "source": "validation-02/source",
  "before": "validation-02/before-source"
}
```

### TARGETED_TEST_RESULTS

```json
{
  "passed": 197,
  "failed": 0,
  "source": "validation-02/TARGETED.json"
}
```

### FULL_TEST_IDENTITY_ACCOUNTING

```json
{
  "baseline": 918,
  "retained": 918,
  "final": 945,
  "added": 27,
  "removed": 0,
  "duplicates": 0,
  "failed": 0,
  "skipped": 0,
  "complete_identities": "FULL_TEST_IDENTITIES.json",
  "native": "validation-02/FULL_UNIT.json",
  "baseline_native": "baseline-v9/FULL_UNIT.json"
}
```

### LINT_IDENTITY_ACCOUNTING

```json
{
  "baseline": 46,
  "retained": 46,
  "final": 46,
  "added": 0,
  "removed": 0,
  "errors": 0,
  "identity": "frontend-relative file + entire native message object",
  "source": "FULL_LINT_IDENTITIES.json"
}
```

### REQUIRED_FRONTEND_GATE_RESULTS

```json
{
  "required": 7,
  "invoked": 7,
  "passed": 7,
  "source": "validation-02/REQUIRED_GATE_SUMMARY.json",
  "gates": [
    {
      "name": "targeted",
      "exit_code": 0,
      "command": [
        "./node_modules/.bin/vitest",
        "run",
        "src/product/publication",
        "src/interaction",
        "src/app/routeTree.test.tsx",
        "src/foundation/surfaceRegistry.test.ts",
        "src/components/app-shell/AppShell.test.tsx",
        "src/localization",
        "--configLoader",
        "runner",
        "--no-cache",
        "--reporter=json",
        "--outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/TARGETED.json"
      ]
    },
    {
      "name": "typecheck",
      "exit_code": 0,
      "command": [
        "npm",
        "run",
        "typecheck"
      ]
    },
    {
      "name": "lint",
      "exit_code": 0,
      "command": [
        "./node_modules/.bin/eslint",
        "src/**/*.{ts,tsx}",
        "--format",
        "json",
        "--output-file",
        "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/LINT.json"
      ]
    },
    {
      "name": "architecture",
      "exit_code": 0,
      "command": [
        "node",
        "scripts/frontend-architecture-guard.mjs"
      ]
    },
    {
      "name": "architecture-controls",
      "exit_code": 0,
      "command": [
        "node",
        "scripts/frontend-architecture-guard.test.mjs"
      ]
    },
    {
      "name": "full",
      "exit_code": 0,
      "command": [
        "./node_modules/.bin/vitest",
        "run",
        "--configLoader",
        "runner",
        "--no-cache",
        "--reporter=json",
        "--outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/FULL_UNIT.json"
      ]
    },
    {
      "name": "build-final",
      "exit_code": 0,
      "command": [
        "./node_modules/.bin/vite",
        "build",
        "--configLoader",
        "bundle",
        "--outDir",
        "/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/validation-02/build",
        "--manifest",
        "--emptyOutDir"
      ]
    }
  ],
  "raw": "validation-02/gates"
}
```

### FOCUSED_BROWSER_SCENARIOS_AND_CHECK_COUNTS

```json
{
  "per_run": {
    "matrix-01": {
      "scenarios": 17,
      "pass": 16,
      "fail": 1,
      "assertions": 121,
      "assertions_pass": 121,
      "assertions_fail": 0
    },
    "matrix-02": {
      "scenarios": 18,
      "pass": 18,
      "fail": 0,
      "assertions": 125,
      "assertions_pass": 125,
      "assertions_fail": 0
    },
    "matrix-03": {
      "scenarios": 18,
      "pass": 18,
      "fail": 0,
      "assertions": 125,
      "assertions_pass": 125,
      "assertions_fail": 0
    }
  },
  "green_runs": [
    "matrix-02",
    "matrix-03"
  ],
  "green_scenario_executions": 36,
  "distinct_scenario_ids": 18,
  "distinct_user_journeys": 17,
  "cross_cutting_audit_ids": [
    "V10-10"
  ],
  "green_assertion_executions": 250,
  "distinct_assertions": 125,
  "assertion_repetitions": 125,
  "all_screenshots": 230,
  "green_screenshots": 154,
  "contrast_min_by_theme": {
    "dark": 14.322753879741615,
    "light": 16.119468339438853
  }
}
```

### BROWSER_NETWORK_RESULT

browser-v10-final02/NETWORK_TOTALS.json与每轮native/Fetch/receiver原始stream随包。两轮各零mutation/blocked/forwarding；Network、interception、receiver三stream不相加为唯一request。真实接口、IdP、凭据、发布服务均未接入。

### VISUAL_REVIEW_SCOPE

```json
{
  "source": "BROWSER_PARENT_VERIFICATION.json",
  "parent_actual_final_images": 4,
  "final_green_images_included": 154,
  "all_final02_images_including_failure": 230,
  "historical_parent_images": 3,
  "observations": "更正后select可读；中文placeholder；长详情换行/内部滚动/关闭可见；日历selected/overflow清楚；isolated no-source中文清楚。仅父记录的四图，不声称154全部人工审阅。",
  "packager_visual_acceptance": "NOT_PERFORMED"
}
```

### BUILD_MANIFESTS

```json
[
  "validation-02/build/.vite/manifest.json",
  "validation-02/build/BUILD_PAYLOAD_MANIFEST.json",
  "browser-v10-final02/build/BUILD_PAYLOAD_MANIFEST.json",
  "browser-v10-final02/FINAL_HASH_BINDING.json"
]
```

### BUILD_CHUNKS

BUILD_CHUNK_RECONSTRUCTION.json：大JS按UTF8最多96000字节分块，显式顺序/每块SHA/原始SHA；原JS也保留。按order拼接应逐字节相同。

### BACKEND_REQUIREMENTS_UPDATED

YES_EXISTING_LEDGERS_ONLY

### NEW_BACKEND_REQUIREMENTS

FB-GAP-014

### BACKEND_GAPS

既有BACKEND_ENABLEMENT_REQUESTS.tsv与API gap ledger更新。未来固定frontend/backend/adapter版本，一个Project publishable OutputArtifact+account/content version→backend stable intent→单一scheduler→attempt/external actual success/failure/unknown。身份授权、paging/completeness、时间/zone、metadata裁剪、raw/mapped状态、关系、幂等/重复防御、安全错误/凭据失效和Postiz版本依赖待建。

### BACKEND_CHANGES

NONE

### TRACKED_DIST_CHANGES

NONE

### BACKEND_STATIC_CHANGES

NONE

### REAL_INTEGRATION_PERFORMED

NO

### EP19_STATUS

UNCHANGED_NOT_CLOSED

### BOUNDED_PRESERVATION_RESULT

```json
{
  "source": "validation-02/SOURCE_DELTA.json",
  "preserved_paths": 994,
  "real_index_unchanged": true,
  "writer": "writer/preservation.json",
  "correction": "writer/correction-01/preservation.json",
  "parent": "BROWSER_PARENT_VERIFICATION.json",
  "parent_hash_rows_checked": 10414,
  "parent_mismatches": 0,
  "scope": "包装者仅复制与核对所选原始字节、source endpoints及封包。未重跑产品gate/browser；不代替父后续追加source/manifest核验。"
}
```

### H4_RECONCILIATION_STATUS

H4 Proposal A append-only exact-path记录更新于既有current/classification；历史ledger未改，不声称H4全面reconciliation或debt-zero。

### FORMAL_SLICE1C_LEDGER_STATUS

SEPARATE_UNCHANGED_NOT_CLOSED；本任务不完成formal Slice1C治理。

### FAILURE_AND_CORRECTION_HISTORY

writer red01/02启动失败与red03无模块不算行为RED；red-behavior真实15fail→green；lifecycle真实retirement重读修复。保留历史architecture bucket扫描失败/恢复与131controls。旧browser quote/reference/restricted oracle历史完整logs/runner，非产品通过重标。父三图发现白底浅字和中文Search：correction red-contrast 17=15pass+2fail→197green，CSSOM非native视觉。final02初次build依赖symlink缺失失败、matrix01 7200字fixture超过4000上限导致失败，改外部fixture3600后matrix02/03各125green，未弱化原53断言。

### PRODUCT_COMMIT_FREEZE_MERGE_PUSH

NOT_PERFORMED

### PRODUCT_PUBLICATION

NOT_PERFORMED

### INDEPENDENT_REVIEW

REQUIRED

### INDEPENDENT_REVIEW_EXECUTION

NOT_PERFORMED_STOP_BEFORE_REVIEW

### STOP

YES_LOCAL_PACKAGING_ONLY

### STOP_REASON

本角色只做本地证据打包和完整性核验；不构成产品或独立最终验收。不启动独立review；远端evidence发布与detached回执留给parent。

### LOCAL_REPORT

REVIEW_REPORT_ZH.md

### LOCAL_MANIFEST

MANIFEST.sha256

### OMISSIONS

OMISSIONS.json

### SELECTED_BYTES_PROVENANCE

SELECTED_ORIGINALS.json

### EVIDENCE_DELIVERY_STATUS

NOT_YET_PUBLISHED

### EVIDENCE_PUBLICATION_STATUS

NOT_YET_PUBLISHED

### EVIDENCE_COMMIT_SHA

NOT_YET_PUBLISHED

### REVIEW_INDEX_URL

NOT_YET_PUBLISHED

### MACHINE_INDEX_URL

NOT_YET_PUBLISHED

### PUBLIC_MANIFEST_SHA256

NOT_YET_PUBLISHED

### REMOTE_VERIFICATION

NOT_YET_PUBLISHED

## 封包与审查边界

V9 schema/scripts作为只读provenance保留。原件完整保留；依赖、cache/profile/home、Git objects/index、整个snapshot和无关历史不入包。历史重复截图省略的每个原图大小/SHA/理由见 OMISSIONS.json；最终154green和76失败轮截图全部入包，修正前三张父实际查看图与其他failure图保留。大JS原字节和UTF8分块均保留，按BUILD_CHUNK_RECONSTRUCTION顺序重建。

MANIFEST.sha256覆盖payload每个文件（自身除外）；ZIP含manifest，独立验证器检查本地/ZIP完整集合、重复项、SHA与CRC、原件保全及重建，PACKAGE_VERIFICATION.json仅位于密封payload外。credential scan只扫描所选bytes，不读取真实凭据或全局存储；fixture literal逐项分类，未解决命中阻止seal。模式扫描不能证明任意秘密绝不存在。后续parent发布必须detached回执，不回填密封manifest形成递归。

## 完整授权 brief（原文）

# V10 bounded frontend writer authority
TASK=FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10
Workspace=/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1
Taskroot=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10
Baseline actual tree=37d003fc4f55faf166cd836a6ea93d77eb8b6a1e; baseline full tests=918; prior46 lint warnings must be identity-preserved. Read taskroot RECOVERY.json. V9 evidence commit41cb3d631e2851cc2c7c0ee83b90b2522c1193ef; manifest77505e42e41ff3956b253c00ab392521cd6375ae97aeb51cbea34db618485072. Prior task sibling FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9 holds baseline snapshot validation-03 and final report.

Owner explicitly authorizes implementation, routine correction, tests and external build, not just planning. Preserve all prior uncommitted work, real index, HEAD, stash. NO product commits/freezes/merge/push/deploy; NO reset/clean/stash; NO backend, EP19, tracked dist/backend static, Skill/Memory edits. Read applicable AGENTS; Owner no-commit requirement supersedes root freeze-SHA rule, record conflict not edit instructions. Only frontend and existing relevant docs/architecture/governance changes; external evidence under taskroot. No credentials or remote mutations by writer. Actual tool denial: STOP, do not retry or bypass. Hermes does final capture/gates/browser/delivery; do not build browser adapter until source stable.

## Discovery and planning before code
Read existing frontend-foundation-checkpoint-a-implementation-v1.md, frontend-product-information-architecture-v1.md, AppShell/Operation/EffectiveAccess/Selection designs, BACKEND_ENABLEMENT_REQUESTS.tsv, frontend-backend-application-api-gap-ledger-v1.md and current scope/path classification ledgers. Search publication/social/scheduling actual implementation. Recover DOM-PUBLICATION-001 as PROPOSAL: OutputArtifact -> PublicationAttempt -> ExternalPublication; metrics historical ObservationSet with observedAt, raw platform semantics retained (metrics not implemented this task). Append in EXISTING planning priority authority: Owner newly prioritizes publication workspace first after V9 bounded acceptance; full NLE editing/Agent later; Postiz single-channel technical pilot/real publication separate; heatmap/cross-platform analytics deferred. Do not claim original priority already had this ordering or create parallel roadmap.
Append V9 bounded acceptance to existing review record, not sealed report: local navigation/locate/selection/metadata and recorded lifecycle fixes accepted; no real NLE/full editing/media playback/platform access integration; long-title inspector layout limitation remains; no product/EP19/Slice1C closure.
Write writer/SCOPE_AND_CONTRACT.md with exact proposed files, recovered contracts, instructions and priority before implementation; then implement continuously.

## User outcome and surfaces
Use existing AppShell/design primitives/i18n/InteractionDialog/Selection owner+dispatcher. Expand existing publication surface if present, otherwise add Publication workspace in existing IA/navigation (no new global shell).
Ordinary no-source entry clearly not connected, no fixture fallback or harness jargon. Full local discovery/inspection/return flow exclusively via explicit isolated verification host injection. No real backend/social/Postiz integration.
List: current-Project supplied-content search, account and source-status filters, explicit-time stable sort with deterministic ties, reset, refresh/retry, detail and contextful return. Platform != account: stable account IDs and supplied names, two accounts same platform remain distinct, no inferred ownership.
Calendar: month, previous/next month/today, selected day agenda; shared list query/filter/source; explicit selectable display timezone; multiple same-day rows + overflow entry; current day/selected day/status not color-only. Narrow screen day agenda acceptable. No week/drag/reschedule. Unscheduled stays separate, never today. Future scheduled versus historical published timestamps distinct; due != published, omitted != absent.
Details: only permitted supplied title/summary, Project, account, platform copy version, stable OutputArtifact logical refs/permitted metadata, scheduled/actual/fetched timestamps, explicit attempt relationships, raw/unknown statuses, safe failure summaries and ExternalPublication stable IDs. Plans/attempts/external objects separate: multiple attempts and account results preserved, no inferred links by names/order/time. Reuse stable artifact navigation only when existing target and access predicate actually support it; otherwise inert safe logical ref + limitation. No preview/download/public-link bypass.

## Time semantics
Calendar dates/timezones NOT NLE media time. Strict absolute instants with offset/UTC; missing/invalid/offsetless = indeterminate + calendar disabled. Do not parse YYYY-MM-DD as UTC midnight for local display. Explicit chosen source bucket field and date interval endpoints; unscheduled vs invalid distinguish. Correct month ends/year/leap/cross-midnight/DST; never assume each day24h. Timezone switch presentation-only, source schedule immutable. Reuse suitable actual existing tools, no invented defaults for unknown source times.

## Consumption/access/lifecycle
First inspect whether real query/access contracts exist. Otherwise mark boundary FRONTEND_CONSUMPTION_PROPOSAL and REAL_BACKEND_CONTRACT_NOT_ESTABLISHED, frontend enums not backend DTO authority. Provider-neutral, not Postiz DB/private API tied.
Explicit isolated provider bound to principal/session/Workspace/Project/source/access and owner. Validate request/response identities/query scope/unique IDs/required relationships/completeness complete|bounded|partial. Unconfigured unavailable. Do not trust source self-allowed boolean as authorization. Reuse EffectiveAccess; simulated access proves frontend only. Listing != artifact/copy/link permission. Omit restricted values completely from DOM/title/aria/data/logs, not just label. External URLs default inert sanitized reference or omitted; never direct credentials/OAuth.
Same trustworthy valid session renewal preserves browsing via existing V8/V9 lifecycle, no global auth rewrite. Real identity/access/project/source/owner change withdraw data+details, abort old request + generation/ownership reject late responses and retained old date/filter/dismiss callbacks. Details cannot revive on same ID reuse. Errors/restricted/invalid responses remove accessless details. Same-context refresh/view switch/close preserve query/date/scroll/focus when valid; disappearance clears selection + safe focus fallback.

## Documentation backend contract gaps
Reuse publication requirement ID if relevant; otherwise new ID by actual convention (do not stuff into NLE/Render). Update ONLY existing BACKEND_ENABLEMENT_REQUESTS.tsv + gap ledger, linked local scenarios. Future minimum: one Project publishable OutputArtifact + one account/content version -> backend stable intent -> single scheduler -> PublicationAttempt/ExternalPublication -> actual success/failure/unknown. Record identity/access, query paging/completeness, timezone/time, artifact metadata access, raw+mapped statuses, attempts/external links, idempotency/duplicate defense, errors/credential expiry, Postiz adapter version/dependency. No backend implementation, EP19 budget or waiting for backend.
New paths exact in existing current/classification ledgers, retain H4 Proposal A append rules, formal Slice1C remains separate, no debt-zero claims or guard weakening. Existing architectural expected-path inventory may be extended exact paths with negative controls intact.

## Verification and handoff
Use meaningful RED->GREEN behavior tests, preserve native logs with commands/time/exit in taskroot/writer. Test unavailable/loading/complete empty/partial empty/filter empty/error/restricted/retry; month/year/leap/timezone/midnight/DST; unscheduled; same-platform accounts; shared filters/stable ties; multi-attempt/channel/unknown; restricted secret sentinels absent; close/focus; contexts/late requests/real retained callbacks/nonrevival; same-context refresh/view preserve. Native form buttons explicit type=button unless actual submit. Do not inflate repeated field tests or change valid pre-existing assertions to pass.
Run targeted tests, typecheck, lint, architecture+controls before declaring interface ready. Outputs outside product (use taskroot). No product dist build. Parent executes final seven gates and918 identity accounting,46 warning identity check. Finish writer/WRITER_HANDOFF.md Chinese: exact changes, contracts/gaps, RED/GREEN/raw commands, remaining limits, stable explicit-host injection interface and ordinary route + labels/selectors for parent native Chromium validation, planned backend IDs, exact paths. Stop only writer role after complete implementation; don't claim independent acceptance or delivery. No independent final reviewer is requested: owner stops before that review.

Official UI research permitted, not implementation proof: https://postiz.com/ ; https://docs.postiz.com/public-api/introduction ; https://docs.postiz.com/public-api/oauth ; https://docs.postiz.com/self-host/installation/docker-compose ; https://support.buffer.com/en-us/articles/how-to-use-buffers-calendar-feature-FSSKbH32DN . Dated official reference research is now available at taskroot/research/OFFICIAL_REFERENCE_RESEARCH.md (actual access 2026-09-09). Read and cite it when updating existing planning/docs: account != platform; display timezone changes presentation not schedule; provider functions are not this product's implementation evidence. Buffer original HTML was empty; same-domain official Markdown recovered. This additive reference does not expand scope. Do not deploy Postiz/iframe/connect accounts, save/schedule/cancel/publish/retry-send/approval backend/bulk/scheduler/heatmap/recommendation/metrics-score/reminders/notifications/media/Agent/NLE/Workflow expansion or fake success button.
