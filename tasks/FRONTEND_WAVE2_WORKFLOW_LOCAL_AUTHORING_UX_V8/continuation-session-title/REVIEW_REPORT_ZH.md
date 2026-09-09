# V8 原任务续作：会话连续性与节点标题布局修正

TASK=FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8
CONTINUATION=SESSION_CONTINUITY_AND_NODE_TITLE_LAYOUT_CORRECTION
LANE=FRONTEND
FRONTEND_BRANCH=refs/heads/agent/frontend-wave2-product-ux-v1
BASELINE_IMPLEMENTATION_TREE=bbbc029452ad635835e976b57701f6ce0cb812a7
FINAL_IMPLEMENTATION_TREE=0289714b2d4094db210b55681fa4f6a8135f7054

## 修正结论

正常续期：在已建立且 SDK 能提供足够可信稳定会话标识的同一上下文中，保留节点、标题、位置、选择、检查器及未完成输入。不是所有 IdP/会话无条件保留：缺失必要 sid 或有效性未知时仍失败关闭。
真实身份/上下文变化：仍退役旧草图和旧 Selection 所有权。主动登出开始及明确失效同步退役；UserLoaded 身份变化在读取当前 SDK User 后退役，在其 callback Promise 完成前生效。
晚到结果：旧读取 generation、卸载后的回调及当前已建立新会话时的旧 UserLoaded 通知均有行为证据。SDK 不提供操作 generation；旧操作若实际覆盖当前 SDK 存储，以及无身份载荷的旧失效信号，无法证明其旧归属，仍失败关闭。本能力不是全场景旧事件隔离 PASS。
长标题：卡片 border-box 高120px，标题最多两行/40px，默认下一行间隔136px。最长合法120字符不缩短、不修改原始数据；中文、连续 ASCII 和混合文本受控。完整标题在可访问名称及检查器读取/编辑，不以 hover 为唯一检查途径。窄视口保留横向滚动画布，不声称全部节点同时可见。

## 认证契约依据

实际安装 oidc-client-ts 3.5.0。UserLoaded 同时用于静默续期、登录加载；不是退出语义。使用 SDK 当前 User 的 issuer、包含配置 client 的 audience、sub、可选 sid、已有 tenantId/tenant_id 及语义 scope 比较；不使用 token 字符串、expiry 变化、整个 User 或无关 metadata 作为身份键。sid 是证明此连续性能力的必要观测，不是新增 IdP 登录强制字段。首次可信读取建立基线；先订阅、后读取，revision/activity 拒绝旧异步返回。读当前状态而非应用事件载荷，避免旧通知遮蔽正在建立的新身份。自动续期未关闭。

复用既有 Workspace/Project/tenant、effective-access 和 Selection owner 来源；访问观测时间及解释文本变化不再无条件重建宿主，实际决策/因素变化仍退役。当前 Project 是 provisional BLOCKED，服务端 session-bound Project/access 完整契约仍未建立；本地编辑不授权保存或执行。AUTH_CONTRACT.md、SDK_INSPECTION.txt 给出实际版本源代码依据。没有第二套认证/权限系统、持久化或草图自动恢复。

## 前序评审与本轮证据

Owner 采纳的独立评审确认前序 V8 主要功能，但暂缓整体接受：所有 UserLoaded 均清空及长标题侵入需要修正。前序170/869、25场景75次300断言是历史，不是本轮结果。旧485载荷清单逐字节复核，无缺失/额外/重复或哈希差异；旧 ZIP486条目及原始哈希一致。旧报告、ZIP、manifest、两次HTTP408和旧测试不覆盖。

本轮先执行正常续期 RED，再最小修正；另一个 RED 暴露“旧通知使正在建立的新身份被忽略”的初始修正竞态，已修正并保留失败。writer 最终178定向通过；父级扩大到原现行选择器最终191/191通过。RED 中有按名称选择导致的跳过，不能冒充最终全量跳过。旧错误预期有 expectation-mapping.json 与原始测试身份对账。

最终七门禁：定向191/191、类型检查、Lint、架构守卫、架构控制、完整890/890、普通真实依赖外部构建均 exit0。全量基线869，保留867、新增23、移除2、重复0、失败0、跳过0。46条旧 Lint warnings 逐条完全一致，新增0、移除0、errors0。普通构建与模拟 fixture 构建分离；普通构建不注入 SDK 模拟。

保留的执行失败：最初 PTY PATH 缺少 router(exit127)；随后 writer 因证据目录未纳入 workspace-write 而停止（外层exit0不等于实施成功），添加已授权目录后完成。一次错误cwd测试解析失败未安装依赖。普通及fixture的runner配置加载均遇 __dirname 兼容失败，改外部加载方式为bundle而不改产品。父级七门禁及浏览器修正各有审批超时0内部调用；Owner 分别明确允许重新触发正常审批后获放行，不把聊天授权伪造为原生审批回执。初次fixture重复React导致bootstrap失败；仅外部依赖dedupe修正后另建build-03。focused-02误以四张卡第四张换行，修正外部脚本为第五张后focused-03通过。所有失败保持独立，不反写通过。

最终浏览器：7个场景 × 两个视口(1440×1000、390×844)，14/14场景执行、88/88断言、36不同检查名、52重复断言、26截图。只计focused-03；更早失败不并入通过分母。英文本地UI测试中文/ASCII/混合120字符标题。检查原生CDP指针/键盘、DOM定位/focus/scroll辅助、模拟视口；Workspace/access/OIDC当前存储及事件明确在外部SDK边界注入，实际产品wrapper/route host保留。无真实IdP/backend、物理设备、IME或屏幕阅读器验收。13个fixture服务文件字节匹配，无应用网络写入/草图存储变化/未捕获异常；可选vite.svg 404及React信息消息披露。task服务/浏览器退出、端口回收。父级代表截图复查完成，不宣称26张全审。全源清单绑定为执行后核计，不伪造为执行前seal。

## 产品端点与范围

HEAD=f5e19cf53fd010eea2935dd29557e82a879e042c
REAL_INDEX_SHA256=675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e
HEAD/index/stash 保持。实际树7977个blob路径与工作区字节/执行模式匹配；1005范围路径仅8项本轮变化，其余997项保全。补丁在独占外部index/object重放，得到相同最终树，不写产品Git对象/index/ref。

PRODUCT_CHANGED_PATHS:
- frontend/src/auth/oidcClient.ts
- frontend/src/surfaces/FoundationPages.tsx
- frontend/src/styles/foundation.css
- frontend/src/app/routeTree.test.tsx
- frontend/src/product/workflow-sketch/WorkflowSketch.test.tsx
DOCUMENTATION_CHANGED_PATHS:
- frontend/governance/UX_WAVE_1_REVIEW.md
- frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv
- docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md

SOURCE_DELTA.json 与补丁包含每项前后端点SHA256。既有UXW1-002、FB-GAP-001/002复用记录真实session/Project/access及IdP联调边界，无新账本，无后台接口/身份提供方配置/全局安全策略变更。H4债务、tracked-dist政策不变。

SESSION_CONTINUITY_BASIS=INSTALLED_OIDC_CLIENT_TS_3.5.0_CURRENT_USER_STABLE_SESSION_AND_EXISTING_CONTEXT
SAME_SESSION_RENEWAL_PRESERVATION_RESULT=PASS_WHEN_TRUSTED_CONTINUITY_AVAILABLE
TRUE_CONTEXT_RETIREMENT_RESULT=PASS_IN_EXECUTED_SDK_AND_APPLICATION_BOUNDARIES
STALE_EVENT_AND_ASYNC_RACE_RESULT=PASS_FOR_OBSERVABLE_GENERATIONS_WITH_DOCUMENTED_UNTAGGED_SDK_LIMITS
NODE_TITLE_LAYOUT_RESULT=PASS_DESKTOP_AND_NARROW_WITH_HORIZONTAL_BOARD_SCROLL
TARGETED_TEST_RESULTS=191_PASSED_0_FAILED_0_SKIPPED
FULL_TEST_IDENTITY_ACCOUNTING=BASELINE_869_RETAINED_867_ADDED_23_REMOVED_2_FINAL_890_DUPLICATE_0_FAILED_0_SKIPPED_0
REQUIRED_FRONTEND_GATE_RESULTS=7_OF_7_PASS
FOCUSED_BROWSER_SCENARIOS_AND_CHECK_COUNTS=7_SCENARIOS_14_RUNS_88_ASSERTIONS_36_DISTINCT_52_REPEAT_26_SCREENSHOTS
MOCK_AND_REAL_IDENTITY_PROVIDER_LIMITS=SDK_BOUNDARY_SIMULATED_REAL_IDP_AND_BACKEND_NOT_VALIDATED
BUILD_MANIFEST_SHA256=1475537355aec52b29cec72e97bbc7991c60eb6882a1c3825434a9825ef4ea0b
BACKEND_REQUIREMENTS_UPDATED=EXISTING_UXW1_002_AND_FB_GAP_001_002
BACKEND_CHANGES=0
TRACKED_DIST_CHANGES=0
BACKEND_STATIC_CHANGES=0
BOUNDED_PRESERVATION_RESULT=PASS_AT_RECORDED_ENDPOINT
PRODUCT_COMMIT_FREEZE_MERGE_PUSH=NOT_PERFORMED
PRODUCT_PUBLICATION=NOT_PERFORMED
LOCAL_EVIDENCE_STATUS=VERIFY_WITH_PACKAGE_MANIFEST_AND_DETACHED_RECEIPT
PUBLIC_EVIDENCE_STATUS=NOT_YET_ATTEMPTED_FOR_CONTINUATION_AT_PACKAGE_SEAL
EVIDENCE_COMMIT_SHA=SEE_NONRECURSIVE_LOCAL_DELIVERY_RECEIPT
REVIEW_INDEX_URL=SEE_NONRECURSIVE_LOCAL_DELIVERY_RECEIPT
MACHINE_INDEX_URL=SEE_NONRECURSIVE_LOCAL_DELIVERY_RECEIPT
PUBLIC_MANIFEST_SHA256=SEE_NONRECURSIVE_LOCAL_DELIVERY_RECEIPT
REMOTE_VERIFICATION=NOT_YET_RUN_AT_PACKAGE_SEAL
INDEPENDENT_REVIEW=REQUIRED
STOP=YES

这是待独立评审的修正V8，不是接受/产品发布。发布状态在本地独立detached回执中追加核实，不反写密封包，避免递归回执链。未启动NLE/Agent新功能、EP19、正式Slice1C或产品发布门禁收尾。Skill/Memory正文写入0。
