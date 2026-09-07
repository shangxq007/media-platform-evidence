# 通知能力只读盘点

## 状态、身份和边界

结论：**源码盘点完成；通知 UI 未实现，端到端集成证据未建立。不是通知中心验收。**
前端身份是已采纳的脏实现树 `43038f740997d0ebb3a8c67f293da7edab563fdb`，不是产品 HEAD；通知消费者/路由/API 文件本轮未改。后端只读取本地 `origin/main` 在任务发现时指向的不可变提交 `86d6aef94fd5e58da552e97c11473cff6eca734e` 的 Git 对象；不声称它是远端最新或并行后端候选。未 checkout、访问并行后端工作树、运行后端、发送通知或测试投递、请求浏览器权限、读取通知凭据。

每个所引文件的 Git blob、SHA-256、身份和原字节副本见 [SOURCE_IDENTITIES.json](SOURCE_IDENTITIES.json)；路由检索范围和具体映射行见 [ROUTE_SEARCH.json](ROUTE_SEARCH.json)。该盘点未调用任何业务 API；集成状态全部是源码观察，不是运行验证。最初只读分析委托因供应商 HTTP 402 失败，没有产物；Hermes 直接完成本盘点，该失败不计作证据。

## A–G 能力矩阵

| 类别 | 后端代码 | 前端 API wrapper | 当前可路由 UI / shell | 契约对齐 | mock/stub 与实际 transport | 集成证据 / 具体缺口 |
|---|---|---|---|---|---|---|
| A 瞬时 Toast / status | 不需要 durable notification 后端 | Toast 无 API；业务组件各自 status | design-system `Toast` 函数存在、role=status；当前 src 中无 Toast 调用点；Review 等现有加载/结果 status 可见 | Toast 的 title/message/onDismiss 是本地 props，不能当 inbox | 本地 React 渲染，非投递、非持久化 | Toast 组件存在不证明全局通知入口接通；AppShell 实际是 Commands、Agent、资产/Inspector 和 unavailable activity，不含通知铃铛 |
| B durable inbox / unread / read | NotificationInboxService 有 insert/list/unreadCount/markAsRead/markAllAsRead，使用 jOOQ 表；Controller 只暴露 list(limit) 与单条 read；MeController 另有空列表/READ 回执 stub | me.ts 同时有 legacy `/me/notifications` 和 inbox wrappers，含 read-all | 无当前通知 inbox route，也无 Bell/Dropdown/页面源码 | **不对齐**：前端分页包 vs 后端 list；read-all service 存在但 Controller 映射未发现 | wrapper 是实际 Axios 请求，不是 mock；后端 durable service 存在，legacy `/me/notifications` 是 stub | 未验证持久化/租户隔离/错误协议；缺口 FB-GAP-010 |
| C 系统事件通知 | NotificationEventHandler 有 Render/Artifact/Timeline/Review 等 Spring listener，legacy handle 写 event 并调用 provider；SpringNotificationEventPublisher.publishToUser 有偏好/订阅过滤、delivery record 与 IN_APP inbox 创建 | event catalog GET /notifications/events；admin publishEvent wrapper | 无系统通知展示入口 | 仅部分源码关联；事件监听存在不证明每个事件都投递到正确用户 inbox | listener/provider/数据库代码为真实执行路径；某些 providers 仍 stub，不能从 SENT 推断收件人收到 | 未建立事件→授权收件人→持久化 inbox→前端的整链；不把 docs 事件数量或 seeded 定义当实际触发覆盖 |
| D 管理公告 / targeting | 事件定义管理、`system.announcement` 定义方向、通用 publish 和按 userId 的 publisher 存在；未建立专用公告/audience/publish-result 契约 | admin notification wrappers 存在，但 events/delivery/provider 路由名称和包不对齐 | 无通知 admin 页面登记；不能把文档所称页面视作当前实现 | **不对齐**；通用 event publisher 不是已验收定向公告系统 | 实际 Axios wrappers；若手动调用可能写事件/投递，本次完全未调用 | 缺口 FB-GAP-012；权限不能从 Admin 注释推断，需后续 scoped action 验证 |
| E 偏好 / 订阅 | ChannelBinding、Subscription、Preference service/controller 存在；查询偏好可能创建默认记录，故本次只读代码不发 GET | me.ts 有 catalog/channels/subscriptions/preferences 方法 | notification-settings 文档明确 Design/contract candidate、frontend paused；所指 Vue 页面当前不存在 | **不对齐**：创建 binding/更新 subscription/批量/偏好更新回包不满足 wrapper 声明，默认 subscription 可含 null 字段 | wrappers 实际传输；验证 binding 直接设 VERIFIED、test 只校验/记 audit，不能当外部验证 | 缺口 FB-GAP-011；quiet hours/digest 字段持久化不证明调度行为落实 |
| F Email/SMS/webhook/Novu | Email、SMS、Webhook send 直接返回 SENT；Mock 记录数据库；Novu 有条件化 RestClient HTTP POST 路径 | channel verify/test、admin delivery retry/providers wrappers 存在 | 无可路由投递设置/监控 UI | 外部协议和部署参数未核验；本地成功回执不能当真实发送 | Email/SMS/Webhook 为 stub；Mock 是持久化模拟；Novu 是实际 transport **代码**，本次未启用/请求 | 缺口 FB-GAP-013；不把 Novu 类存在称为可用投递，重试 Controller 只返回 RETRY_QUEUED |
| G 浏览器 / OS push | channel string 接受 PUSH 不等于 Web Push service；所检 providers 无 PUSH 实现 | 未发现 Notification.requestPermission / PushManager / serviceWorker 订阅桥接；openreplay captureNotifications 是观测选项 | 无权限请求、订阅控制或系统通知入口 | 未建立 | 无本任务执行；PUSH 字符串、第三方观测配置不能充当实际 push | 暂无已接入能力，不新增猜测性 backend endpoint 要求；需要未来单独授权场景/协议 |

上述矩阵各行共享明确前后端身份；不能把源文件存在、wrapper 存在、路由存在、契约对齐和真实集成合并为一个 AVAILABLE 状态。

## 路径、参数、响应逐项核对

**公共前缀差异：**当前 `frontend/src/api/index.ts:9` 的 Axios baseURL 是 `/api/v1`。本后端参考的 NotificationController 类映射 `/api`，MeController `/api/me`。所检 web/security Java 未发现版本前缀别名；未核验运行时反向代理/动态映射，因此完整传输路由对齐仍未建立，不能静默删掉 v1 来声称匹配。下表先列 wrapper 的相对路径，后端列完整源码路径；所有调用均未执行。

| 消费场景 / wrapper | 请求与前端预期 | 后端参考源码 | 判定 |
|---|---|---|---|
| getMyNotifications | GET `/me/notifications`, page,size,status → notifications,total,page,size,unreadCount | MeController:208–224 `/api/me/notifications` 返回空 notifications、0 total/unread；单条 read 回 status READ 无 inbox service 调用 | 除前缀外包形似，但为 stub，非 durable inbox |
| getNotificationInbox | GET `/me/notifications/inbox`, page,size → items,total,page,size,unreadCount | NotificationController:377–387 GET `/api/me/notifications/inbox`, **limit 默认50** → `List<NotificationInboxItem>` | 参数、分页/未读 envelope 不匹配；不擅自补 total |
| markInboxNotificationRead | POST `/me/notifications/inbox/{id}/read`, Promise<void> | :390–411 同相对路径；返回 id/read/readAt；找不到时返回普通 Map(error=NOT_FOUND)，没有 ResponseEntity 404 | wrapper 忽略业务失败包，不能把 HTTP 成功当 read 成功 |
| markAllInboxNotificationsRead | POST `/me/notifications/inbox/read-all` | inbox service 有 markAllAsRead；所检 Controller 无该路由 | 方法名不是 endpoint 证据 |
| getNotificationChannels | GET `/me/notification-channels` → binding[] | :169–179 返回 listUserBindings，包含真实 domain fields | 字段/非空/敏感目的地公开策略需对齐；controller直接返回 domain 对象不证明公开 DTO 安全 |
| bindNotificationChannel | POST 同路径，channelType,destination,webhookSecret → 完整 Binding | CreateChannelBindingRequest 只有 channelType,destination；controller:181–195 回 bindingId/channelType/verificationStatus | 请求多余字段及回包不匹配；不读取或验证实际 secret |
| verify/test/disable/delete binding | POST verify/test/disable；DELETE binding → void | :214–277 路由段存在；verify 直接置 VERIFIED；test 未调用 provider；回 map | route 形似不等于验证/投递真实成功；本次不触发 |
| getNotificationSubscriptions | GET → subscription[]（多个字段声明为非空 string） | :281–291 listSubscribableEvents；没有存储订阅时投影 null subscriptionId/tenantId/time | 非空声明不可靠 |
| updateNotificationSubscription | PUT /.../{eventKey}, enabled/channels → 完整 Subscription | :293–308 回 eventKey/enabled/channels 三字段 | 回包缺字段 |
| batchUpdateNotificationSubscriptions | POST /.../batch-update, updates → results/errors 包 | :310–322 返回 List；service stream 遇异常不产生逐项 errors 包 | envelope/partial failure 不匹配 |
| getNotificationPreferences | GET → Preference 含 preferenceId/tenantId/userId | :328–346 回 globalEnabled/channelEnabled/eventEnabled/quietHours*/digestMode/criticalOverride | wrapper 身份字段缺失；wrapper 未声明 eventEnabled |
| updateNotificationPreferences | PUT Partial<Preference> → 完整 Preference | :348–371：缺 globalEnabled/criticalOverride 默认 true；回三字段 globalEnabled/digestMode/criticalOverride | Partial 的保留语义和完整回包均未对齐 |
| getNotificationEventCatalog | GET /notifications/events → catalog[] | :146–152 返回 listUserConfigurableEvents | 存在相对映射/兼容字段子集；全前缀/权限/运行包未验证 |
| admin list/detail/deliveries | /tenants/{tenantId}/notifications[/{id}[/deliveries]] → list/object/list | :59–96 三者均返回 queryService.listDeliveries；detail 未用 notificationId；query service 无该 ID 过滤 | 详情形状/过滤语义不符合消费者；TenantGuard 不能证明数据隔离完备 |
| admin retryNotification | POST /tenants/.../retry → void | :98–108 仅返回 RETRY_QUEUED | 没有队列或实际 retry 证据 |
| admin publishEvent | POST /notifications/events, type/tenantId/payload | :115–124 需要 CreateNotificationEventRequest(eventType,subjectId,payload) | type/eventType、subjectId 缺失，不匹配 |
| admin event definition CRUD/archive | `/admin/notifications/event-definitions...` | :417–488 `/api/admin/notifications/events...` | 路由名不匹配；不能将定义编辑等同定向公告发布 |
| admin getDeliveryLogs/retryDelivery | `/admin/notifications/delivery-logs...`, page/size/status/channel/eventKey/tenantId → items,total,page,size | :493–511 `/api/admin/notifications/deliveries`, List 无这些分页过滤参数；retry 仅 map | 路由、参数、包和重试含义不对齐 |
| admin getProviderStatus | `/admin/notifications/providers` → ProviderStatus[]（成功率/延迟等） | :531–544 `/api/admin/notifications/provider-status` → novu/local enabled map | 不匹配；不得伪造成功率/延迟 |

## 关键源码补充与权限边界

- InboxService 按 userId 查询/read；存在 unreadCount/markAllAsRead 不代表 HTTP 暴露。单条更新先读 ID+userId，后按 ID 更新；列表/计数 SQL 没有显式 tenant 条件。当前用户从 request 的 jwt.subject 解析，不信任客户端 user header；多租户/RLS/拦截器覆盖未做运行验证，应在集成门禁验证而不是宣告越权或安全通过。
- NotificationController 的 admin 标签主要是文档注释；注释不授予管理权限，也不证明生产授权。未来要验证 principal、tenant/workspace/resource scope、effective action、跨租户非披露失败。已有 FB-GAP-002 仍是共同权限要求，不重复建立新权限模型。
- EmailNotificationProvider / SmsNotificationProvider / WebhookNotificationProvider 的 send 方法只有返回 `DeliveryResult("SENT", ...)`；没有 SMTP、SMS SDK、HTTP dispatch。WebhookSigner/UrlValidator 的存在不改变 send 是 stub 的结论。
- NovuNotificationProvider:87–96 使用 RestClient `.post().uri("/events/trigger")`，构造 workflowId/to.subscriberId/payload 并配置 Authorization header。这只是源码中的外部传输路径；版本匹配、配置、凭据、实际 delivery 均未验证。沒有读取其配置/凭据或请求该 endpoint。
- MockNotificationProvider 保存 delivery record 后返回 SENT，属于持久化模拟，不是外部收件人回执；NotificationProviderRouter 在无匹配时可 fallback Mock。
- `docs/frontend/notification-settings.md` 开头的 design/contract candidate 声明明确优先于后文现在时措辞；`docs/observability/notification-center.md` 中 Bell/Dropdown/MyNotificationsPage、admin UI、投递完成等说明不能覆盖本次源码观察。所指 Vue 文件当前前端及该后端参考树均未找到。

## 需求登记与后续

只登记四个已确认的消费集成缺口：FB-GAP-010 / UXW2-NTF-001（durable inbox），FB-GAP-011 / UXW2-NTF-002（偏好/订阅/binding），FB-GAP-012 / UXW2-NTF-003（admin 查看/配置/精确 targeting 输入），FB-GAP-013 / UXW2-NTF-004（真实投递与失败/重试回执）。对应现有两个 ledger 的 append-forward delta，而非新权威账本。缺少前端页面本身不被记成 backend endpoint 缺失。

以上缺口不阻塞本轮 read-only Review UX 验收，也不自动排进并行 backend lane。本任务通知 endpoint 调用、实际投递、通知权限请求、通知配置/凭据读取均为 0；单独获准的证据 Git 认证不用于通知。后续须单独授权通知 UI 与 scoped contract/integration tests，才可改变通知能力状态。
