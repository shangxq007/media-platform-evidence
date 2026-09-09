# V10 官方参考研究：发布工作区、日历与只读检查

## 结论与证据边界

**这是独立背景研究，不是代码审查、实现证明或 V10 验收。** 本次只读取用户指定的官方网页与本地 WRITER_BRIEF.md，并在 research/ 内写入研究材料；未访问产品代码，未登录 Postiz/Buffer，未连接社交账户，未调用发布接口，未部署、修改凭据或进行远程写入。

- Postiz 可作为未来供应商候选：官网描述可视日历与多渠道发布；公开 API 明确将 UI 的 channel、API 的 integration 定义为“已连接的社交媒体账户”。因此账户不能被平台名替代。[1][2]
- Buffer 官方日历文档适合参考视图切换、渠道/状态过滤、点击条目检查以及按网络定制文案的组织方式；这些是文档描述，不是本项目已有能力。[6]
- 本项目 V10 应保持“本地、只读、供应商中立”的范围。下文所有契约建议均为 **FRONTEND_CONSUMPTION_PROPOSAL / REAL_BACKEND_CONTRACT_NOT_ESTABLISHED**，不授予任何前端枚举或 Postiz 字段后端 DTO 权威地位。

## 1. 实际访问日期与恢复情况

当前时间由 `date --iso-8601=seconds` 实际读取：`2026-09-09T12:15:03+08:00`；UTC 输出：`2026-09-09T04:15:03+00:00`。下表为浏览器实际读取时间，均为 UTC；对应中国标准时间同为 2026-09-09。

| 来源 | 实际读取时间（UTC） | 读取结果 | 页面更新日期核验 |
|---|---|---|---|
| Postiz 官网 [1] | 2026-09-09T04:15:48.166822+00:00 | 实时 DOM 正文成功 | 页面元数据 `article:modified_time=2026-04-27T05:50:08+00:00`；是网页声明的修改时间，不是功能上线/部署日期 |
| API introduction [2] | 2026-09-09T04:16:04.465982+00:00 | 实时 DOM 正文成功 | 所检查 time/日期 meta 无结果；更新日期未核实 |
| OAuth [3] | 2026-09-09T04:16:05.882711+00:00 | 实时 DOM 正文成功 | 同上；没有可确认的修订日期 |
| Docker Compose [4] | 2026-09-09T04:16:23.880166+00:00 | 实时 DOM 正文成功 | 同上；正文版本迁移提示不是更新日期 |
| Buffer 原始 HTML [5] | 2026-09-09T04:16:32.411793+00:00；重读 04:16:51.836338+00:00 | 只有 `Go to Buffer` / `Powered by` 空壳，未取得文章正文 | 无可确认日期；不能凭标题或空壳声称读到全文 |
| Buffer 官方同文 Markdown [6] | 2026-09-09T04:17:23.991406+00:00 | 实时官方正文恢复成功；没有使用第三方存档 | frontmatter 有 title/description/canonical_url/md_url，无发布日期或修订日期 |

初始 `web_extract` 对五个 URL 的批次请求失败，原始错误为：`DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content. Set web.extract_backend to firecrawl, tavily, keenable, exa, or parallel.` 这是工具后端能力问题，不是五个站点全部封禁。随后使用真实浏览器读取。

Buffer 原 URL 等待后仍为空壳，原因未确证，不能断言是登录墙或 WAF。搜索发现同域官方 `.md` 地址，浏览器从 `https://support.buffer.com/articles/how-to-use-buffers-calendar-feature-FSSKbH32DN.md` 转至含 `/en-us/` 的最终地址，取得与原文章同名、同标识符的 Markdown 正文。[5][6]

搜索结果对旧 `/article/651-how-to-use-the-new-calendar-feature-on-buffer` 链接标注 `July 23, 2026`，但没有打开并证实其正文日期；**不把搜索摘要日期当作文章更新时间**。原始搜索结果保存于 `raw-buffer-search.json`。没有任何供应商运行版本被本次核实。

## 2. 官方原文证据与 V10 启示

### 2.1 账户不等于平台

API 原文：
> The Postiz UI uses the term channel, while the API uses integration. They refer to the same thing: a connected social media account.[2]

示例将 `integration.id` 与 `settings.__type` 分开；文档称平台有各自的 settings schema。[2]

**V10 建议（非官方 DTO）：** 用稳定账户标识作为筛选与关联键，显示来源提供的账户名与独立平台标签；同一平台的两个账户必须保留两行/两个身份，不按平台图标、名称、显示顺序推断同一账户。Postiz integration ID 只能作为未来适配器中的外部标识，不能成为本领域唯一身份体系。

OAuth 响应中 `id` 被解释为授权用户关联的 organization ID，而不是社交账户 ID。[3] **因此建议**区分本地主体/Workspace/Project、供应商组织、已连接发布账户与平台类型；来源组织身份不等于本地资源授权。

### 2.2 日历、列表与过滤

Postiz 官网原文：
> Plan, generate, and schedule posts automatically to 30+ social media networks — then review and edit everything in a visual calendar.[1]

这是营销页的能力描述，不能由此证明其日历的完整过滤规则、列表共享查询、详情结构或权限行为。[1]

Buffer 文档明确提供 Week / Month 切换；可从 All Channels 选择多个渠道；All Posts 下可筛选 All Posts、Drafts、Sent Posts、Scheduled Posts、Pending Approval；另有 Tags 筛选。[6]

Buffer 月视图文档说明最多显示 5,000 条，超过时建议使用周视图或渠道过滤。[6] **V10 建议：** 借鉴“筛选后看日历、点击条目检查”的信息组织，但不能复制该数值作为本系统上限。列表与月历应共享当前 Project 的同一查询与来源；完整/有界/部分结果必须显式表达，日历没有条目不等于后端没有数据。搜索、稳定排序、选中日议程与返回上下文是本地任务要求，不能声称已由这些网页证明。

Buffer 还描述空周推荐发帖时段与拖拽改期、创建、编辑、删除。[6] **这些不进入 V10：** 普通未接入入口应明确不可用，不生成推荐槽或虚构数据；仅实现月历、月份导航、今日、选中日议程、溢出入口与只读详情，不引入周视图、拖拽改期、保存/发布等有副作用操作。

### 2.3 时间与时区

Buffer 原文说明浏览器自动检测当前时区并显示在顶部；渠道时区不同于计算机时区时，日历换算展示但实际发布时间不变；日历本身不能查看每个渠道设置的时区。[6]

**可借鉴的是“显示时区与计划时刻分离”，不是照搬自动检测策略。** V10 按用户授权采用显式可选显示时区；切换只影响呈现，不改来源计划。计划时间、实际发布时间、抓取/观察时间分别标识；到期不能推定已发布。

Postiz API 的 schedule 示例包含带 `Z` 的 `date` 字段，但示例日期 `2024-12-14T10:00:00.000Z` 是请求样例，不是文档更新时间，也不足以证明完整时区/DST 语义。[2]

**契约待定项：** 绝对时刻需明确 offset/UTC；无时区、非法值与未安排分别处理；日历桶字段、查询区间端点与显示时区写明。缺失时间不能默认为今天，也不能把纯日期隐式当 UTC 零点。DST、跨午夜、月末/闰年与一天不一定 24 小时属于本地设计/验证要求，不是已从供应商产品验证的行为。Buffer 文档用 EST/BST 举例但没有给出具体日期，不应将该例固定差值写成时区换算算法。[6]

### 2.4 详情与内容版本

Buffer 描述点击日历条目后选择铅笔图标进入预览/编辑；多渠道创建时可点击 `Customize for each network` 定制 caption、hashtags 并调整各渠道内容。[6]

Postiz 示例的每个 `posts` 项带独立 `integration`、`value` 与 `settings`。[2] **这些支持“一个创作内容可能面向多个账户/平台有不同文案”的设计动机，但不证明供应商具有不可变内容版本 ID、版本历史、跨渠道版本血缘或本项目 DTO。** `value` 数组也不能直接等同于版本历史。

**V10 只读详情建议：** 仅显示授权来源提供的标题/摘要、Project、账户、平台文案版本引用、OutputArtifact 稳定逻辑引用及允许的元数据；分别展示计划、实际、抓取时刻与原始/未知状态。PublicationAttempt 与 ExternalPublication 关系须显式提供，多次尝试、同平台多账户结果不得合并或按名称/时间推断；没有安全导航能力时仅显示惰性逻辑引用，不借供应商预览/URL 绕过访问控制。上述模型是本地提案，不是从 Postiz/Buffer 页面导出的既有实现。

## 3. 未来 provider-neutral 契约待确认项

下表均为研究建议，非已建立后端契约；不要求 V10 新增后端或接入 Postiz。

| 待确认边界 | 建议与理由 |
|---|---|
| 身份与授权 | principal/session/Workspace/Project/source/owner 显式绑定；本地账户 ID 与供应商组织/集成 ID 分离；listing 权限不推导内容/文件/外链访问权限；来源自报 allowed 不能代替本地授权 |
| 查询结果 | 搜索、账户/原始状态过滤、稳定排序、分页、完整性与过滤空/真实空/部分空区分；列表和日历保持同一查询上下文 |
| 时间 | 计划时刻与实际发布、观察时刻分开；明确日历桶、区间与显示时区，未知/无效/未安排独立 |
| 内容与产物 | OutputArtifact 与账户内容版本以稳定 ID 关联；明确元数据权限及不可变性/版本定义，不能用文案文本或数组顺序当版本键 |
| 状态与关联 | stable intent、PublicationAttempt、ExternalPublication 分层；原始状态与映射状态并存，保留 unknown、多次尝试和多个账户结果 |
| 未来执行链 | 单一调度权威、幂等键、重复防御、超时结果不明与对账机制另行设计；不要同时让本地与供应商调度器各自当权威 |
| 适配器 | 只通过已审查的公开 API/文档适配；隔离供应商状态、字段和版本依赖，不耦合 Postiz 数据库、内部路由或私有 API |
| 生命周期 | 同可信上下文刷新保留浏览状态；主体/项目/来源/权限变化撤回详情，拒绝旧请求与旧回调，避免相同 ID 复用导致旧详情复活 |

Postiz API 文档区分 401、403、404、429、5xx，还指出删除时某特定缺失 ID 情况可能错误表现为 500。[2] **未来适配建议：** 保留结构化原始错误并安全映射，不能普遍把 500 当成功、把 404 当无权限或把计划创建响应当实际发布成功；V10 不执行删除或重试发送。

## 4. OAuth 与自托管：仅候选接入约束，不执行

OAuth 文档说明 Authorization Code flow，令牌可调用相同 Public API；授权码十分钟失效且只能使用一次，兑换需 server-side POST；要求校验 state。文档同时称 OAuth token 不过期，但用户可撤销，轮换 client secret 不撤销现有 token。[3]

**建议：** 将此记录为 Postiz 当次文档行为，不把“永不过期”写成供应商中立契约；未来需覆盖撤销、失效、授权失败及供应商差异。凭据、授权回调与令牌兑换留在后端/安全边界，前端只接收安全连接状态。本次没有创建 OAuth app、获取或使用任何凭据。

Docker Compose 文档提示 v2.11.2 → v2.12.0+ 的 Temporal 迁移，说明 Compose 仓库及 dynamicconfig 才是维护中的部署来源，并警示服务、镜像、环境变量会随版本变化。[4] **这不是最新发布版本证明，也不是可运行部署的验证。** 未来试点必须独立核验供应商版本、依赖和调度责任；本次未 clone 该仓库、未拉取镜像、未启动 Docker/Temporal，也不生成部署方案。

## 5. 可追溯文件与未证明事项

- `source-1.txt` 至 `source-4.txt`：实际浏览器获取的 Postiz 原文。
- `source-5.txt`：Buffer 原 HTML 空壳，明确不是文章正文。
- `source-6.txt`：同域官方 Buffer Markdown 原文（含 canonical/md URL）。
- `raw-browser-results-1.json`、`raw-browser-results-2.json`、`raw-buffer-retry.json`、`raw-buffer-markdown.json`：实际 URL、标题、读取 UTC、元数据/正文片段与正文文件定位；正文不重复嵌入。
- `raw-buffer-search.json`：官方 Markdown 发现过程的真实搜索结果。
- `retrieval-status.json`：时间命令、工具失败与来源覆盖记录。
- `citation-ledger.json`：机械生成的引用映射及逐字证据。

未证明：实际 Postiz/Buffer 登录后 UI、发布/重试/调度行为、产品运行版本、账户权限实际效果、版本历史 API、完整分页契约、后端 DTO、V10 代码实现或验收通过。页面图片/视频没有展开检查，不能把其 alt 文本当视觉实测。官方文档可以指导信息组织，不能替代本项目实现证据。

## Sources

[1] https://postiz.com
    > "Plan, generate, and schedule posts automatically to 30+ social media networks — then review and edit everything in a visual calendar."
[2] https://docs.postiz.com/public-api/introduction
    > "The Postiz UI uses the term channel, while the API uses integration. They refer to the same thing: a connected social media account."
[3] https://docs.postiz.com/public-api/oauth
    > "OAuth tokens do not expire. Users can revoke access at any time from Settings > Approved Apps in their Postiz dashboard."
[4] https://docs.postiz.com/self-host/installation/docker-compose
    > "Always pull the file from the repository rather than copying a snapshot. The services, images, and environment variables change between releases, and the repository is the canonical source."
[5] https://support.buffer.com/en-us/articles/how-to-use-buffers-calendar-feature-FSSKbH32DN
    > "Go to Buffer"
[6] https://support.buffer.com/en-us/articles/how-to-use-buffers-calendar-feature-FSSKbH32DN.md
    > "Click ***Customize for each network*** to customize the caption, add hashtags, and adjust your post for each channel you're posting to."
