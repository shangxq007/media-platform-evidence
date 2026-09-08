# V7 渲染可观测性：本地独立评审包

**状态：已实现并完成限定工程验证；独立评审 REQUIRED。** 基线 `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee` → 未冻结实现树 `414d6ed80f6d4c01699d56403a043b84b390d1e7`。禁止产品提交、冻结、合并或发布；此包尚未远程发布。

## 交付与验证

- 原有 Render 表面扩展；9 个产品/测试/本地化路径及 6 个治理文档路径，共 15 个变化路径。新增一个样式文件，已在两个当前分类账中登记。
- 七项最终树门禁全部 exit 0；定向 173/173，完整前端 789/789，架构控制 120/120。Lint 0 错误、46 警告。
- 完整测试身份：原始 797；保留 748，替换删除 49，新增 41，最终 789；失败/跳过/重复均为 0。不得表述为“原 797 个测试全部不变”。所有身份及原始 reporter 均保留。
- 最终浏览器 46/46 检查，30 张截图；15 个发射文件逐字节 HTTP 哈希吻合。Chromium 与检查脚本自然 exit 0；fixture 服务按预期 SIGTERM -15，端口无残留。
- 外部构建共 15 个文件，含真实应用与独立 fixture 入口及两个 HTML；不是继承 V6 的 14 文件计数。必需资源无缺失；两个 HTML 均引用同一个历史缺失可选 `/vite.svg`，没有把其 404 当作应用资源 PASS。

## 真实/模拟、权限与行为边界

普通应用未配置时仅显示不可用；真实服务器契约、授权和集成均未建立。单独 loopback fixture host 只用于显式模拟验证，未在产品增加 URL fixture 开关。源状态、时间、失败、尝试和制品字段均作为只读投影；未知状态不推断成功/失败，任务可见性不授予制品读取。有效进度仅按已验证同单位数值计算，140/100 等有限无效值保留原值但不钳制、不给百分比。查询重试不等于任务重试。

## 本次发现、纠正与保留记录

首次 PTY `codex-router` 因 PATH command-not-found 退出 127；原日志保留，随后使用已发现的绝对路径启动，不是工具权限绕过。主 writer 与修正 writer 均 exit 0。主 writer 的预期 TDD RED、类型错误及中间失败保留；第二 writer 用三个失败回归证明了测试专用键重新标记与缺失原始进度字段问题，再完成修正及非空生命周期断言。最终七门禁只有一个精确树版本，全部成功。

writer 报告观察到 external `package_local.py` 并发改变：这是 controller 在 writer 运行期间补充本地打包字段及生成目标保全记录的已知改动（本会话 patch receipts），不是产品漂移、writer 越界或对不明漂移的吸收。其原始观察记录保留。初始 writer 的 shell-expanded lint 警告数 13 不具完整递归范围；最终实际递归 lint 为 46 警告/0 错误，前者不转用。

第一次浏览器执行 43 检查/27 截图通过，保留为先前成功执行。随后在同一只读构建上加入制品/失败尝试/窄屏制品下部可见性检查并完整重跑；最终口径为 46/30，而不是相加 89。

## 视觉与验证限制

已逐张审看代表性最终截图：桌面列表、身份详情、下部制品与失败尝试、中文窄屏列表及下部详情。窄屏信息和长字面值换行，发现控件、源披露与收据占据较多首屏；完整任务/详情需要垂直及内部滚动。深滚动时共享对话框标题/关闭按钮不持续显示，Escape 关闭和返回启动器焦点已验证。DOM scrollIntoView 是披露的辅助，不是物理触摸滚动认证。文档宽度通过不代表首屏全部可见或完整移动端可用性验收。

未执行物理设备、触控、虚拟键盘、OS IME、屏幕阅读器或真实后端/权限/跨进程集成。源码中的 pagehide/pageshow 生命周期是模拟组件事件证据，不是新做的真实 bfcache 生命周期资格验证。H4、正式 Slice1C 与发布仍单列，不宣称治理欠账清零。

## 本地打包校正

首轮打包在有界令牌形状扫描处停止，未生成 seal/ZIP。匹配来自两个 writer 状态记录中无关共享仓库 stash 分支名称里的 `task-` 子串，并非已证实凭据。已保留首轮未封装目录与原始本地 writer 记录；最终公开就绪副本省略这两个无关 stash 描述字段，记录原始文件、被省略值及清理后副本的 SHA-256。产品源码、补丁、测试和浏览器原始输出不因此改写。详见 `SANITIZATION_RECEIPT.json`；清理后的扫描再执行，结果以实际 seal 为准。

## 原始证据与离线复核入口

- `validation/TASK_DELTA.patch`：完整 binary/full-index 补丁；`PATCH_REPLAY.json` 证明外部索引重放得到同一最终树。
- `validation/source/` 与 `validation/before-source/`：所有改变路径最终/基线完整字节；`context/`：完整前端源码、测试、类型、守卫、依赖配置及实际决策文档。
- `validation/gates/`：每门精确命令、containment、native exit、原始输出；`FULL_UNIT.json`/`TARGETED_FINAL.json` 与原始 `V6_FULL_UNIT.json` 可复算身份。
- `browser/`：最终原生指令、断言、HTTP/服务字节哈希、截图、辅助和退出记录；`prior-browser-attempts/` 保留前次成功执行。
- `validation/build/`：完整构建文件；大 JS 保留原始字节并提供有序 UTF-8 review chunks 与重建表。
- `MANIFEST.sha256` 排除自身；`REVIEW_INDEX.json` 不包含自身/后生成 manifest；archive/hash 在外部 detached receipt 中，避免自哈希循环。

## 必需交付字段

### TASK

FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7

### LANE

FRONTEND

### FRONTEND_BRANCH

refs/heads/agent/frontend-wave2-product-ux-v1

### PRIOR_V6_REVIEW_ADOPTION_RECORDED

YES — existing frontend/governance/UX_WAVE_1_REVIEW.md append; Owner adoption of fixed-evidence static read-only frontend review; prior evidence commit 7362b5e9e2e6df680b03a9666d5b8db264d9e413, manifest 08ff3f82a0b607e28e98b24acf1db0eb1d868bd304fef784a63a9b34157e0e33; not real contract/permission/integration acceptance

### SELECTED_FEATURE

Render observability only; STOP before Workflow UX

### PLAN_SOURCE_AND_ITEM

docs/architecture/governance/frontend-product-information-architecture-v1.md — adopted priority Scene/Shot > Render observability > Workflow UX > bounded NLE editing > Agent-assisted creative; existing /operations/renders increment

### BASELINE_IMPLEMENTATION_TREE

31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee

### FINAL_IMPLEMENTATION_TREE

414d6ed80f6d4c01699d56403a043b84b390d1e7

### PRODUCT_CHANGED_PATHS

```json
[
  "frontend/src/app/routeTree.test.tsx",
  "frontend/src/localization/catalogs.ts",
  "frontend/src/localization/source-manifest.json",
  "frontend/src/product/render-browser/RenderBrowser.test.tsx",
  "frontend/src/product/render-browser/RenderBrowser.tsx",
  "frontend/src/product/render-browser/fixture.ts",
  "frontend/src/product/render-browser/render-browser.css",
  "frontend/src/product/render-browser/source.test.ts",
  "frontend/src/product/render-browser/source.ts"
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

### REUSED_RENDER_SURFACES_AND_CONTRACTS

Existing /operations/renders -> RenderBrowser; existing provider, EffectiveAccess, shared Selection owner, InteractionDialog, horizontal shell/design/localization. Inspected RenderJobSummary, render-jobs API, legacy result list/detail; richer observability does not exist in the five-field agreed type. No parallel center/registry/permission or legacy transport invocation.

### RENDER_CONSUMPTION_CONTRACT_STATUS

FRONTEND UNAGREED consumer proposal; no agreed HTTP endpoint, server permission key or canonical DTO claimed. Real read requires host-supplied matching HOST_AGREED binding and SERVER EffectiveAccess; generic visibility, proposal and test-only keys rejected.

### USER_VISIBLE_OUTCOME

Bounded supplied Render ID/name discovery, source-supported status filter, stable name/ID sort, reachable reset, manual refresh/query retry/loading cancel, readonly task detail, return preserving filters and launcher focus. EN/zh-CN; unconfigured ordinary route unavailable.

### PROGRESS_AND_STATUS_SEMANTICS

Unknown source statuses literal/neutral. Source value/unit/total/totalUnit/stage retained, including invalid finite values. Percent only finite consistent units, positive total, 0<=value<=total; never clamp or synthesize ETA/status/time. Source times literal; frontend successful-fetch time separately labelled.

### FAILURE_AND_ATTEMPT_BOUNDARIES

Validated supplied user-safe summary/code/time only; React text, strict shape and bounded disclosure checks. Explicit attempt identities/ordinals/task/parent/retry links only; no generated history. Task status and attempt status separate; missing/empty/bounded/complete distinct.

### ARTIFACT_ACCESS_BOUNDARIES

Supplied readonly safe ID/name/type/literal availability/version/explicit task link. Missing/empty/bounded/denied/unavailable/unknown/stale/inspectable metadata distinct. Metadata/task visibility grants no Artifact read. No verified typed destination/independent access receipt, therefore no open/download/URL action.

### PERMISSION_AND_ACTION_BOUNDARIES

EffectiveAccess authoritative projection; no visibility/role/testkey/client-flag authorization. Query retry is not render retry. No submit, execution cancel, rerender, task retry, artifact delete/publish, workflow/timeline/canonical mutation, provider/worker/billing/quota calls.

### CONTEXT_AND_STALE_RESULT_HANDLING

principal/tenant/session/Project, complete access projection, binding, adapter and Selection owner lifetime key the session; replacement/unmount/retirement aborts reads and clears data/dialog. Generation fences late success/rejection. StrictMode registration and ready/pending retirement tested. Explicit stale failure clears data; stale successful source snapshot is labelled stale, not called fresh.

### MOCK_AND_REAL_DATA_BOUNDARIES

Ordinary application has no implicit fixture URL switch, default account or real query. Separate loopback opt-in host wraps exact registered route tree with simulated identity/access and controlled adapter. Dashboard fixture reads and inert disposable auth marker are harness-only. No real integration.

### TARGETED_TEST_RESULTS

```json
{
  "passed": 173,
  "total": 173,
  "failed": 0,
  "pending": 0,
  "report": "validation/TARGETED_FINAL.json"
}
```

### FULL_TEST_IDENTITY_ACCOUNTING

```json
{
  "baseline": 797,
  "final": 789,
  "files": 38,
  "passed": 789,
  "failures": 0,
  "skips": 0,
  "added": 41,
  "removed": 49,
  "duplicates": 0,
  "retained_baseline_identities": 748,
  "report": "validation/TEST_IDENTITY_ACCOUNTING.json",
  "interpretation": "49 replaced identities are confined to the two rewritten Render suites; unknown-status rejection, hardcoded proposal binding and product URL fixture expectations intentionally superseded. Consolidated schema cases reduce expanded identity count. Not a claim that all 797 old identities remain. All unrelated identities retained."
}
```

### REQUIRED_FRONTEND_GATE_RESULTS

```json
{
  "required": 7,
  "passed": 7,
  "architecture_controls": {
    "tests": 120,
    "pass": 120,
    "fail": 0,
    "skipped": 0
  },
  "lint": {
    "problems": 46,
    "errors": 0,
    "warnings": 46
  },
  "commands": "validation/FINAL_VALIDATION_PLAN.json",
  "raw": "validation/gates/"
}
```

### FOCUSED_BROWSER_RESULTS

```json
{
  "checks": 46,
  "passed": 46,
  "failed": 0,
  "screenshots": 30,
  "served_files": 15,
  "served_hash_differences": 0,
  "browser": "Chromium CDP headless; focus emulation; desktop 1440x1000 and narrow 390x844 EN/zh-CN",
  "assistance": "DOM locale/locator/scrollIntoView and explicit source-mode/delay controls disclosed",
  "native_exits": {
    "processes": [
      {
        "name": "smoke",
        "pid": 538942,
        "exit": 0,
        "terminated_by_task": false
      },
      {
        "name": "chrome",
        "pid": 538791,
        "exit": 0,
        "terminated_by_task": false
      },
      {
        "name": "fixture",
        "pid": 538772,
        "exit": -15,
        "terminated_by_task": true
      }
    ],
    "remaining_ports": []
  },
  "not_certified": "physical device/touch/virtual keyboard/OS IME/screenreader; width pass not mobile certification"
}
```

### BUILD_MANIFEST_SHA256

2dcf0c845b06036ada04b083ad279de202d5a550f8793490cda5ef7e9d3b4d7e

### BACKEND_REQUIREMENTS_UPDATED

YES — existing FB-GAP-005 in both requested records; future bounded pinned frontend/backend controlled-Project readonly authorized/denied/error/stale and zero-write acceptance described, not performed

### NEW_BACKEND_REQUIREMENTS

No new requirement IDs; richer UNAGREED FB-GAP-005 consumption details only. No full-platform prerequisite.

### BACKEND_CHANGES

0 task-authorized backend source changes; no backend lane audit or stationarity requirement

### TRACKED_DIST_CHANGES

0; named frontend/dist 8 files byte/mode/membership preserved, fresh runtime built externally

### BACKEND_STATIC_CHANGES

0 generating-command changes; configured backend static destination 3 files byte/mode/membership verified before/after final gates/browser; product mounts read-only

### REAL_INTEGRATION_PERFORMED

NO

### BOUNDED_PRESERVATION_RESULT

PASS — final 1005 scoped paths match exact tree bytes/modes/membership; 990 baseline paths outside allowlist unchanged; real index/HEAD/branch preserved. Previous V6 public package/receipt/archive hashes preserved. No whole-repo/parallel-backend/whole-host stationarity claim.

### H4_RECONCILIATION_STATUS

UNCHANGED / unresolved historical dispositions retained; guards not changed, no debt-closure claim

### FORMAL_SLICE1C_LEDGER_STATUS

UNCHANGED / separate authority and review; no closure or release claim

### PRODUCT_COMMIT_FREEZE_MERGE_PUSH

NOT_PERFORMED; original HEAD f5e19cf53fd010eea2935dd29557e82a879e042c retained; no real-index staging

### PRODUCT_PUBLICATION

NOT_PERFORMED

### EVIDENCE_DELIVERY_STATUS

LOCAL_SANITIZED_REVIEW_PACKAGE; local manifest/archive verification recorded in detached LOCAL_PACKAGE_VERIFICATION.json; parent independently verifies and separately publishes

### EVIDENCE_COMMIT_SHA

NOT_ESTABLISHED — child did not publish

### REVIEW_INDEX_URL

NOT_ESTABLISHED — LOCAL_REVIEW_PACKAGE/REVIEW_INDEX.md only

### RAW_REVIEW_INDEX_URL

NOT_ESTABLISHED — no remote publication

### MACHINE_INDEX_URL

NOT_ESTABLISHED — LOCAL_REVIEW_PACKAGE/REVIEW_INDEX.json only

### PUBLIC_MANIFEST_SHA256

NOT_ESTABLISHED — public publication not performed; local manifest hash belongs in detached receipt, not a self-referential report

### REMOTE_VERIFICATION

NOT_PERFORMED by child

### INDEPENDENT_REVIEW

REQUIRED — no implementation acceptance claimed

### STOP

BEFORE_WORKFLOW_UX; parent independent review and separately authorized evidence-only publication only

