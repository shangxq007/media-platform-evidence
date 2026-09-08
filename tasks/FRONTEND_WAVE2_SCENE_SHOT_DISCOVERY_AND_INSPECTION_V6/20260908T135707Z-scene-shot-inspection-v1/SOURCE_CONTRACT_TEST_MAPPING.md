# V6 源码—契约—实际测试映射

Exact source tree `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`. 以下身份全部出自 fresh FULL_UNIT.json 的结构化执行结果且 passed；完整 797 身份及 724 基线在 validation/TEST_IDENTITY_ACCOUNTING.json。这里列出全部 73 新增身份，不使用文本 it() 次数代替参数化展开。

## 逐源码区域的展开执行身份

### frontend/src/surfaces/FoundationPages.tsx: ProductionPage; frontend/src/app/routeTree.tsx: existing production route
- `["frontend/src/app/routeTree.test.tsx", ["runtime route registration and deep-link restoration"], "registers the Project Production consumer with exact route scope and no implicit fixture or request"]` — passed

### frontend/src/product/production/ProductionBrowser.tsx:34-70 owner lifetime/StrictMode reconciliation;92-99 cleanup
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "remains initially usable under the actual StrictMode-style host lifecycle"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears a ready snapshot on InteractionStore owner retirement and rebinds only to a fresh pageshow store"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "rejects a pending reply after InteractionStore owner retirement"]` — passed

### frontend/src/product/production/ProductionBrowser.tsx:140-151 local browse;184-217 controls/explicit relations;221-246 shared readonly detail/reference rendering
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "accepts the isolated fixture only through an explicit source prop or provider injection"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "browses only explicitly related Shots, preserves missing fields, and exposes no mutation or arbitrary URL"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "searches, filters, sorts and resets Scenes locally while retaining controls after detail close"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "keeps Reset reachable for populated filters and preserves Reset focus after restoring defaults"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "distinguishes empty snapshots, no related Shots, bounded snapshots and missing supplied values"]` — passed

### frontend/src/product/production/ProductionBrowser.tsx:55-63 session key;77-138 guarded load/cancel;153-182 distinct failure presentation
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "uses one stable Refresh/Cancel/Retry control, drops cancelled replies, and never steals moved focus"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing unavailable state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing denied state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing unknown state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing unsupported state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing error state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "clears content and renders nondisclosing stale state with opaque supplied explanation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "fails closed on invalid relations and never retains old content"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "keeps a rejected source request retryable and distinct from invalid snapshot validation"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires a valid pending reply on principalId change"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires a valid pending reply on tenantId change"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires a valid pending reply on sessionId change"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires a valid pending reply on workspaceId change"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires a valid pending reply on projectId change"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "retires pending replies on adapter/access replacement and unmount"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query a malformed required principalId context"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query a malformed required tenantId context"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query a malformed required sessionId context"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query a malformed required workspaceId context"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query a malformed required projectId context"]` — passed
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "does not query denied/unknown sources and is unavailable with no injected source"]` — passed

### frontend/src/product/production/ProductionBrowser.tsx:78-79 catalog use; frontend/src/localization/catalogs.ts: shell.productionBrowser EN/zh-CN
- `["frontend/src/product/production/ProductionBrowser.test.tsx", ["ProductionBrowser Scene and Shot discovery"], "localizes the complete bounded workflow in Chinese while preserving supplied values literally"]` — passed

### frontend/src/product/production/model.ts:148-160 selectScenes/sceneStatusValues
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "filters only supplied Scene display fields and status, then sorts stably by name and ID"]` — passed

### frontend/src/product/production/model.ts:21-56 schemas;121-145 parseProductionSnapshot
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "accepts an owned bounded snapshot with explicit stable Scene-to-Shot relations and safe references"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 0"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 1"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 2"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 3"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 4"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 5"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 6"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 7"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 8"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 9"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 10"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 11"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 12"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 13"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 14"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 15"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 16"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 17"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 18"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 19"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 20"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 21"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 22"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "rejects malformed, ambiguous, foreign, orphaned, unsafe, unbounded, or mismatched results 23"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing unavailable failure receipts"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing denied failure receipts"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing unknown failure receipts"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing unsupported failure receipts"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing error failure receipts"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "preserves nondisclosing stale failure receipts"]` — passed

### frontend/src/product/production/model.ts:14-19 identity;61-119 context/access/source disposition
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "keys all identity, scope, access, and source ownership inputs"]` — passed
- `["frontend/src/product/production/model.test.ts", ["bounded Scene and Shot production projection"], "requires exact real and simulated access projections and never treats viewability as permission"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "accepts an arbitrary explicitly host-agreed SERVER access binding and rejects a mismatched binding"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "rejects malformed required principalId before a source can be ready"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "rejects malformed required tenantId before a source can be ready"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "rejects malformed required sessionId before a source can be ready"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "rejects malformed required workspaceId before a source can be ready"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "rejects malformed required projectId before a source can be ready"]` — passed

### frontend/src/product/production/simulatedSource.ts: unavailableProductionSource/createSimulatedProductionSource; source.tsx: explicit provider
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "defaults unavailable without transport and retains the supplied route scope without inventing identity"]` — passed
- `["frontend/src/product/production/model.test.ts", ["explicit Production source boundaries"], "creates simulated data only from an explicit supplied identity and never reads URL, storage, or transport"]` — passed

## 验证语义与边界
- `model.test.ts:62-89` 的 24 个参数化负例：无值/错误对象/旧 requestId/五维错 scope/Scene 或 Shot 重复/跨种类 ID 冲突/异 Project Scene 或 Shot/无 Scene 或无 Shot 的关系/一 Shot 多 Scene/重复关系/无关系 Shot/异 Project 引用/不支持的引用 kind/缺失 UNSUPPORTED 解释/空版本/越界 limit/多余 envelope 字段。具体输入与原始身份均可查源文件；不把未测形态推成全面证明。
- Projection 只校验已提供字段。`name` 可省略/null、非空字符串；description 可省略/null/空字符串。UI 显示未提供与已提供空内容，revision 显示的是 supplied version，不推断 canonical Revision。
- read request 实际只有 scope(principalId,tenantId,sessionId,workspaceId,projectId) 与 requestId。access、read binding、adapter identity、Selection store lifetime 和 generation 是额外本地隔离维度，不冒充 request DTO 字段。
- `HOST_AGREED` 是 host 注入契约标志，不证明集成已经 agreed；实际 SERVER key 必须由未来 host 提供。普通入口无 adapter 使用 unavailable，不发请求。
- Shot 列表只使用显式 relations。ReferenceList 只做本地来源引用详情显示/unsupported 原文解释，不执行跳转或下载；未建立目标资源访问授权。
- Selection 仍由共享 store 管理，不把 Scene/Shot 伪装 NODE/CLIP/LANE；空 surface adapter 仅生命周期使用。没有新增 global action authority。
- `browser/NATIVE_CHECKS.json` 的 36 项及 `PER_CHECK_COMMAND_WINDOWS.json` 对应真实最终 build；原始 Input/DOM helper/fixture 调度分别保留。宽窄 return/search/filter/reset/empty/error/retry native 覆盖，不把 DOM assistance 宣称为物理输入。

## 现有 guards 的机制及盲区
- seven-gate graph 沿用现有脚本；architecture guard 源码与 tests 完整收录 context/frontend/scripts。当前分类由 filesystem census 对比当前 TSV，八路径补正是增加事实分类，不改变约束或阈值。
- 120 个 architecture controls 由 Node TAP 实际执行。正控扫描现行树，负控以命名源码/导入/路径/语法模式变体注入验证；原始 TAP 保留所有身份。
- guards 混合 AST/文本/path 规则，不等于全程序类型、行为或安全证明。范围外动态路径、未知命名间接写法和 backend 实际权限不由 guard 证明；类型、组件、完整 unit 和浏览器是互补证据。
- guard 源码完全未改；与 stopped/V5 的 bytes 相同。新增 Production 数据校验主要由 schema/model/component tests 验证，而非宣称新增 guard 对其全覆盖。
