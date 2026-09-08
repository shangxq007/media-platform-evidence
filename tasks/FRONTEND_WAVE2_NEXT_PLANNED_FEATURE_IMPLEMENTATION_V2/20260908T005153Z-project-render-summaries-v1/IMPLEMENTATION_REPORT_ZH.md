# V2：显式 Project 范围的 Render 摘要发现与只读检查

## 结论与决策
已完成一个有界前端增量，工程验证通过，等待独立评审。没有创建产品提交、freeze、merge、push、部署或发布。此报告是发布前技术记录；实际证据提交与远端回读另以 detached 交付回执记录，不能把打包成功当作已发布。

接受基线：`0b76ac9352ad40fc155c7203ed69f6362b0db89f`。
最终实现树：`afc520c2fb8da37961cc6931e71743256b60a3e5`。产品 HEAD 仍为 `f5e19cf53fd010eea2935dd29557e82a879e042c`，真实 index 未变。实现是既有 dirty 工作树，不是 HEAD tree；完整任务 patch 在外部 index 重放精确得到最终树。

## 已采纳的前序评审
Owner 的 Projects `PASS_BOUNDED` 已追加到原 `frontend/governance/UX_WAVE_1_REVIEW.md`。141 文本 payload、630/232 测试身份、36 Chromium 记录、17 分块/6 JS、8 构建文件和截图是 Owner 采纳的独立记录审查，不是本轮重新执行，也不是 ChatGPT 全包核验或真实后端接受。前序 detached 收据保持 BLOCKED_AS_REPORTED，未重试、未塞入新包绕过限制。历史 H4、Slice1C 等更广泛状态不变。

## 选择、范围与用户结果
来源为 checkpoint-a 的 Compact surface design records → Operations（搜索/筛选/排序、读取投影）以及 IA 的 Operations/Renders 和既有 FB-GAP-005。当前 route 原本只有不可用工具栏。选择既有局部工作流中的这一缺口，不把历史候选或计划标题升级成新的后端能力；未发明 Slice、里程碑或全局 Render 合同。

`/operations/renders` 现在接入共享 AppShell 与 InteractionDialog。提供 ID/profile 搜索、既有 status 筛选、稳定 ID 正反序、重置、只读五字段详情（job ID、Project ID、Timeline snapshot ID、profile、status）；加载/取消加载/重试/刷新、错误、空、limited 等状态齐备。英文与简体中文沿用原设计与本地化；外部 profile/ID 作为不透明文本渲染。不是完整全局 inventory，不默认挑选 Project，也不从共享 Project provider 的 synthetic token 推断来源。

ordinary unconfigured 仍 unavailable。只允许显式本机 fixture 或注入 source；真实 source 必须使用既有 EffectiveAccess 的 SERVER AVAILABLE 投影，缺失/unknown/denied 不制造权限。`render.summaries.query` 仅为前端消费提案。不会在真实失败时回退模拟数据。React component/source、principal/tenant/workspace/project/lifetime/access/request 身份变更会清除/退休旧请求和内容；没有无关 Selection/revision 耦合。

没有 job cancel/retry/create、artifact/下载/交付、provider/worker/runtime 操作，也没有第二个 command registry、权限引擎或 canonical store。取消按钮只取消列表加载。Projects 源注入、普通 unavailable、WorkspaceHome 旧 query、localhost 边界与只读行为均未改；受影响测试保留其回归。

## 变更与依赖
产品/测试等前端路径 10，文档 5；5 个新路径已在现有 path ledger 分类。见完整 SOURCE_DELTA、before/source 端点与 task patch。两份既有 backend requirement 文档澄清 FB-GAP-005；新增后端需求 ID 为 0。消费者场景、资源范围、proposed 输入输出、权限/失败、异步生命周期与后续 integration criteria 已写入。没有后端实现改动。

## 最终树的真实验证
- 受影响测试：282/282。
- 完整前端：680/680，34 文件；630 基线新增 50，移除 0，重复 0，skip 0，失败 0。
- 必需 typecheck、lint、architecture guard、外部 build 全部 exit 0；architecture controls 120/120。
- lint 46 旧 warnings，新增 0，身份比对无增减；不是“零 warning”。
- Native Chromium：33/33；断言 runner 与 Chromium 均 exit 0。fixture server 在验证后由本任务 SIGTERM，exit -15；端口残留 0。
- 外部构建 8 文件，逐个实际 HTTP 服务哈希一致；required 资源缺失 0，历史可选 `/vite.svg` 缺失保留。
- Build manifest SHA-256：`8baf07f203de0d181d7976023e5f417ab2862fd33ffbeb7fac455af2dfd735d7`。
- 16 个有序 UTF-8 分块重建全部 6 个 JS 原始字节，与原件长度/hash 一致。
- 977 个 allowlist 外基线范围路径及 410 个有界历史/dist 文件检查无差异；没有要求 backend lane、EP19 或全局系统静止。

首次 writer 1204 秒（进程实测）；修正树最终 gate/记账调用实测约 47.99 秒（包含并发，不是门禁 CPU 时间求和）；最终 native 调用 13.3 秒。这些不是整任务 wall time。

## 保留的失败及辅助边界
首次 RED 是缺少新模块产生的导入错误，不是合格行为 RED，也不能宣称严格逐项 RED-GREEN 证明。后续一次 57/58 failure 属于新测试对加载时已退休 search 控件的错误前提；修正为稳定外部焦点哨兵后 58/58，记录未删。首次最终 architecture gate 在旧树 `4b5c9132d8b3c122bc89b2e5acda3b38494ea7a6` 因新 local alias 命中历史禁用名称失败；只改为直接消费原导出 `RenderJobSummary`，未改 schema 或 guard，重新绑定并执行最终门禁。

浏览器 final-01 使用了错误的 helper URL 入参，final-02 把未映射 Backspace 发送成私用字符；均为外部 harness 错误，原失败/退出保留。final-03 修正接口使用，在同一最终 build 上通过；没有因此重建产品。截图视觉检查：桌面五字段可读，窄屏中文详情和关闭入口可见，长 ID 换行；未见页面水平溢出。

可信 CDP 键盘/指针与 isTrusted 记录用于核心交互；DOM inspection/scroll、locale helper、viewport 与 CDP focus emulation、React fiber 上显式 fixture 延迟/resolve 注入另行披露。不是真实认证、物理手机/IME、屏幕阅读器语音或后端集成。浏览器测试创建的 profile/cache/home 从技术包中排除，不发布私有配置。

## 一个后续可选集成场景
只考虑“一个明确 Project 的安全 Render 摘要读取与本地检查”。届时固定 frontend tree 与实际 served build、backend version、接受的 adapter/contract、受控 principal/tenant/workspace/project 和数据。允许的请求仅为约定 Project-scoped 只读摘要查询，禁止所有写操作；覆盖一个正常搜索/检查路径与 denied/error/context 切换后 stale-result。缺失投影仍 fail closed。不要求整个平台或 EP19 完成，本次未执行。

## 停止点
工程完成不等于独立评审或产品 release。Skill/Memory 指令正文写入 0。本任务止于该功能评审，不自动启动第二功能。

INDEPENDENT_REVIEW=REQUIRED
PRODUCT_PUBLICATION=NOT_PERFORMED
STOP=YES
