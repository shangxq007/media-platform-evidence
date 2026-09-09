# V11 单渠道只读集成试点：Outcome C 本地阻塞阶段审查报告

## 1. 结论与验收边界

**Outcome C — 实施/验证被真实环境阻塞，不能改称 Outcome B，更不是 Outcome A。** 本包完成的是离线证据整理、公开材料选择、原件哈希核对、中文报告/机器报告与独立完整性验证，不是可运行 adapter、前端集成或产品验收。所有证据发布字段为 **NOT_YET_PUBLISHED**；父任务之后才可单独进行安全的 evidence-only 发布，不能视为本报告已经发布。

判定依据为 `writer/WRITER_HANDOFF.md`、`writer/BLOCKER.json`、`deployment/DEPLOYMENT_HANDOFF.md` 与 `deployment/final-runtime-state.json`。研究与各阶段交接均按其阶段解释：研究中的“未部署/不授权部署”是研究阶段声明，不能抹除后续已授权准备及实际依赖镜像拉取；deployment 的准备成功也不能覆盖 writer 的明确停止。

## 2. 已完成与缺失

| 项目 | 真实结果 | 不可声称 |
|---|---|---|
| 官方契约恢复、字段映射、源码/镜像 pin | STATIC；研究原有 145 checks、32 sources、9 image manifests、52 mapping targets | 新的运行测试、签名供应链证明、线上版本核验 |
| GET allowlist | 恰好 2：`/integrations`、`/posts` | GET 天然安全、单账号上游权限 |
| adapter 与测试源草稿 | 两份原件 SHA-256 已核对；UNVERIFIED / INCOMPLETE | 功能完成、安全验收、RED→GREEN |
| 合成 HTTP 验证 | 最终 1 项 setup error、0 项行为断言执行、0 项通过 | 完成合成边界验证 |
| 前端 pilot receipt/access 消费 | 未实施，隔离 runnable host 未实施 | 真实数据已进入日历/列表/详情 |
| 部署配置 | digest-pinned、实际 compose config 成功、一次性容器网络前提检查成功（既有回执） | Postiz 应用启动或 ready |
| Postiz 镜像 | 300 秒有界拉取超时；最终 exact-image exists exit 1 | 注册表必然故障、应用缺陷 |
| 空实例检查 | NOT_RUN_NO_POSTIZ_INSTANCE | 成功空列表或实际为空 |
| 真实账号/记录/artifact/attempt | 无实际读取；关系未建立 | 真实只读集成或真实发布闭环 |
| V10 adoption / FB-GAP-014 / enablement / scope ledgers | 未更新，pending | 已落实到现有产品文档 |
| 本地证据包 | 选择、消敏、哈希、zip 完整性验证 | 产品通过或发布完成 |

## 3. 阻塞、失败与停止

### Writer 明确拒绝

既有执行命令 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pilot` 在真实合成 upstream `asyncio.start_server(self.up, '127.0.0.1', 0)` 创建 socket 时失败：`PermissionError: [Errno 1] Operation not permitted`，继而 `OSError: could not bind on any address out of [('127.0.0.1', 0)]`。最终为 1 setup error，**行为断言执行数为 0，不是 1 assertion**。本次整理未重跑、提权、改网络路径、借容器旁路或用 mock 替代。socket 原生完整输出不在 `adapter-red.log`：它由交接和 BLOCKER 结构记录引用先前会话回执，本包不伪造缺失原生日志。

`writer/adapter-red.log` 保留更早一次 `ModuleNotFoundError: No module named 'pilot'` 导入失败，1 loader error。它不是后续 socket 错误的原生日志，也不是有意义的行为 RED。两次失败分开记录，不相加为通过数。

### Deployment 有界超时与保留状态

Postiz immutable image 拉取达到 300 秒后被终止，没有 retry。Postiz 从未启动；没有应用 HTTP/public/private API、数据库读取、账号/OAuth/发布调用。既有最终回读为零容器、零 volume、无 task-created network、无 scoped engine/conmon 进程、配置端口无监听；engine 默认 podman 网络定义仍在。**五个依赖镜像仍保存在隔离私有存储，可能残留部分 Postiz 下载/cache/tmp；私有一次性密钥、局部 tooling 与配置仍保留。** 这不是运行中的服务，也不是全部清理。本整理没有再次操作或遍历该状态。

局部 Compose 安装曾产生 python-dotenv 与 Hermes 的环境依赖冲突警告；安装使用 task-local `--target tools`，交接说明 Hermes 安装未修改。research/citation-verification.json 保留早期 strict citation exit 1（未引用全部已登记来源）；research/verification.json 中后续普通 citation 一致性检查通过但仍有 unused-source warnings。不能把 strict 失败删除或改写为全面高覆盖引用验证。上述均保留原阶段证据。

## 4. 身份与范围

- V10 接受的实际树：`afc966ad4872e6dd65997281c75fe49e7aaed376`，不是当前 HEAD。
- 产品 HEAD：`f5e19cf53fd010eea2935dd29557e82a879e042c`。本整理只读核查 HEAD、branch、index SHA、stash，以及 RECOVERY 中明确列出的 1016 个前端/治理文件：内容零差异，HEAD/branch/index/stash 均与 RECOVERY 一致。详见 `PRODUCT_RECHECK.json`。未重新生成 Git tree，未断言全仓库无新增文件。
- adapter 原件 `pilot.py` SHA-256：`8541bd38f906c167bc309f31463de3e0c5cfbc8df932bf61b690b62a198c70b9`。
- adapter 原件 `test_pilot.py` SHA-256：`d9387c09071bb8d8edeb7e246b9ba0dd9b4ade194c8030c6195221df5e0d31fa`。
- 本地 draft identity 是文件 SHA，不是产品 candidate commit，也不是运行成功身份。两文件均保持原草稿；任何静态代码意图不作为执行证明。
- 上游 candidate `v2.23.0`，源码 `1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9`；compose source `dd4969e5e694cd009619a0d53cff14c21104580b`。
- Postiz candidate image：`ghcr.io/gitroomhq/postiz-app@sha256:785f97312f66a347fb96cdccc4ded5a33ced69a672c89a9adc8054e7d6a21dc5`；实际 upstream version **NOT_RUN**，未部署实例版本不是 candidate 值。
- 无产品写入/commit/freeze/merge/push/index/stash 操作；无 backend/EP19 执行与读取，无 Skill/Memory 变更。仅创建 taskroot 的 `evidence-prep/`。

## 5. 静态协议、映射与授权

以下仅转述包内 `research/OFFICIAL_CONTRACT_REVIEW.md` 及 `endpoint-allowlist.json`、`v10-field-mapping.json`；其中官方 URL、原研究引用编号、日期、引用摘录和 pins 保留于研究文件，不作新网络获取。

- 默认拒绝，仅 GET integrations 和 posts；posts 仅 `startDate/endDate`。不开放 `customer/group`，没有 account query filter，没有该 public 方法的 pagination cursor/page/limit/total/hasMore。不能借用私有 getPostsList。
- 原始 `Authorization` key/token，不额外加 Bearer；凭证只能由获授权的服务端引用提供。读取作用域是组织级，服务端过滤 exact integration.id 并不缩小上游权限。必须明确组织级读取同意，或既有单渠道隔离组织；不得按名称或首项选账号。
- 独立 owner-local principal/session/workspace/project/source/owner/access/query 绑定是待实现验证的本地权威，不得把 V10 fixture/test-only 权限或 origin 改名成生产权限。
- integration.id/name/identifier 可作账号 id/name/platform；post.id 与 integration.id 作计划/账号引用；Project 映射必须本地明确授权。内容 summary 需内容访问权限。title/copyVersion 不补造。
- QUEUE → scheduled，验证后的 publishDate 仅 scheduledAt；PUBLISHED → published、ERROR → failed，但实际发布时间/attempt time unknown；DRAFT 为 unscheduled。保留 rawStatus，未知状态 fail closed。
- `intervalInDays != null` 或 actualDate 行必须排除并标 partial，递归重复原 ID 不生成 occurrence/attempt；其余重复 ID 拒绝。限定日期、response bytes、读取次数、超时、local cap；bounded/partial 不是全项目完整快照。该策略尚未通过 adapter 测试。
- releaseId 仅供给的 external reference；releaseURL 不是 OutputArtifact，不 fetch/download/preview，也不反推 ID。attempt/OutputArtifact/copyVersion 关系 **MISSING/NOT_ESTABLISHED**。空 artifacts/attempts/externalPublications 是“不提供关系”的投影建议，不是真实查询无记录。
- 固定 base/version/IP、禁重定向/任意 URL/未知 route/method/body/cookie/private API/DB；400、401/403、404、429、5xx、无效 JSON、超时、取消及 stale response 必须区分。401 不唯一证明 key 错误；文档速率限制互相冲突，不宣称无限读取或固定 quota。
- GET OAuth/connect 路由亦拒绝；创建/编辑/取消计划、删除、retry-send、上传、发送、下载预览、账号连接均未执行也未授权。

## 6. 前端、七门与治理文档

没有 V11 前端变更，因此日历/list/inspection/timezone/filter/focus/lifecycle 的 V10 既有表现不算 V11 新验收。V10 full945、lint46 仅是初始 brief/边界中的历史参考，不是本次测试实测；其余历史七门明细本任务未重建。

V11 adapter behavioral suite、affected frontend tests、full suite、typecheck、lint、architecture controls、external build、浏览器观察均未获得新的完成结果：adapter blocked，其他 NOT_RUN。这不是 gate bypass，也不满足 B。UI 两项可选微调（长说明压缩、月卡账号短标签）未实施。

V10 bounded adoption 的 Owner 意向仅在本次 brief 中存在，**现有 adoption review/planning 未更新**。FB-GAP-014、BACKEND_ENABLEMENT_REQUESTS.tsv、scope/classification/path ledgers 均 pending；不能把本报告当作这些产品文档已落实。H4 Proposal A、正式 Slice1C 与真实发布功能仍分离。

## 7. 继续所需最小条件

1. 由 Owner 在明确允许 loopback socket 的获准环境恢复：先全面审查/修正现有草稿，补齐真实 HTTP 的授权/作用域/错误/重定向/大小/时间/递归/重复/取消/429/写路由/重复读取测试，取得真实行为 RED→GREEN；本报告不授权现在重跑或旁路。
2. 实施独立 pilot frontend receipt/access 与隔离 host；保留默认 unavailable 和 V10 fixture；补齐受影响七门、浏览器证据及现有治理文档。
3. 部署需另行恢复有界镜像获取，重新核查 pins/隔离边界/端口碰撞，不能放宽 host networking、默认路由、注册或凭证边界。仅启动空实例也不能满足真实账号集成；不得创建账号来清门。
4. 真实读取前需明确实例/base/IP、实际版本、已有凭证使用权、唯一 integration 与稳定 Project/principal/session/workspace/source/owner 关系、组织范围读取同意、日期窗、读取量、内容权限及实际记录可用性。当前均未建立，未获取凭证。
5. future send 另需 account、content、artifact、immediate-or-scheduled、one-send、idempotency、result 明确授权；本任务没有发送。

## 8. 公开安全、材料计数和完整性

deployment 只按原 public-artifact-manifest **19 个显式成员**取值，每个原件 bytes/SHA 均验证；另取 23 个明确指定边界/草稿/交接/研究文件，合计 **42 个来源文件**。没有递归遍历 private/、tools/ 或打包整个 taskroot。原件哈希与公开副本哈希分列在 SOURCE_SELECTION.json，公开副本消敏本地绝对路径与 task-private IPv4；不是假称所有公开副本字节与原件一致。源码副本仍是 UNVERIFIED/INCOMPLETE，不要执行其中历史 runbook。

扫描仅针对选择的公开字节：高置信私钥/token/JWT 模式检查与敏感字段人工分类；fixture 中 synthetic-local-token、synthetic-upstream-key、PRIVATE_COPY/PRIVATE_OTHER/PRIVATE_ERROR、private.invalid 是合成测试值，不是私有账号或实际 endpoint。Compose 仅空值、环境占位符与 [REDACTED]；公共源码摘录可能有官方 example defaults，绝不作为凭证使用。loopback/容器 service name 是本任务隔离配置，不是真实私人实例授权；未公开真实账号/私有 endpoint。保留 private 路径字面引用是为解释隔离/保留状态，不代表读取或打包其内容。扫描不是数学意义的不存在任何秘密证明，不读取密钥来比对，也不发布密钥哈希。

`MANIFEST.json` 定义最终 payload 精确路径/bytes/SHA，`V11_OUTCOME_C_LOCAL_REVIEW.zip` 仅含这些 payload 文件及相同 manifest。`verify_integrity.py` 在独立进程重新读取 zip 和 payload，验证无重复/越界成员、成员数与 hashes 一致；只做完整性，不导入 adapter 或执行 deployment。它的结果为 `integrity-verification.json`，包含 zip/manifest/report/machine 的精确 SHA 与计数。验证输出与 zip hash 置于 zip 外以避免自引用。完整性 PASS 只表示打包正确，不表示产品验收。精确最终数值以该回执为准。

## 9. 发布字段

publication_status、evidence_repository、evidence_branch、evidence_commit、review_url、report_url、manifest_url、zip_url、zip_download_url、verification_url、remote_readback、remote_hash_verification、independent_public_review 均 **NOT_YET_PUBLISHED**。本地 zip 不是远程下载地址；没有产品提交或发布。父任务如发布，必须重新读回确切目标并记录远端证据，不能追溯性把本地报告改称已经完成 A/B。
