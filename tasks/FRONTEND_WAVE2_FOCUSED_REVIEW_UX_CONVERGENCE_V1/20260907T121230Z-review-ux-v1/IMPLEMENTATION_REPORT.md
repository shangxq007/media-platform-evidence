# 受限 Review UX 实现与验证报告

## 交付结论

**已完成受限本地实现、适用前端门禁、定向 Chromium 验证及通知只读盘点；等待独立评审。不是产品提交、冻结、发布或整体 Slice1C 关闭。** 补充检查中的 unused 诊断和只读快照缓存写入拒绝均保留，未包装成“所有检查都通过”。

- TASK：`FRONTEND_WAVE2_FOCUSED_REVIEW_UX_CONVERGENCE_V1`；LANE：`FRONTEND`。
- 分支：`refs/heads/agent/frontend-wave2-product-ux-v1`。
- 已采纳基线实现树：`43038f740997d0ebb3a8c67f293da7edab563fdb`。
- 最终实现树：`5c19a1045c3382140c62a84cf74ba3d4ec47e354`（外部 Git 对象身份，不是产品 commit）。
- 产品 HEAD 保持 `f5e19cf53fd010eea2935dd29557e82a879e042c`；真实 index 保持不变。
- 产品/展示/测试路径 **7**，现有需求文档路径 **2**，合计 **9**；无新生产模块。

## 实现结果

Review 优先展示服务器投影的项目名、修订编号、message 和可解析日期；完整 Workspace/Project/修订 ID 可以展开查看，不制造缺失的元数据。两端选择保持显式、有序，不自动选任意版本或触发比较。选定/请求中/结果的版本对各自关联；逆序保持逆序传给既有 gateway。

每次新请求、版本对编辑、Workspace/Project 切换或卸载都会让旧 completion 失效。新请求清除旧成功结果，失败不展示前次成功；原生按钮和既有 dispatcher 均防止 pending 重复调用，并按当前 GatewayResult.retryable 控制重试。首次草稿中过度保留失败版本对的 Map 已在未冻结实施期删除；不新增权限缓存。返回旧版本对后需要新的显式查询，由后端重新判定，而不是复活历史权限判断。

展示区分：history loading/empty/one/ready、缺失/相同/不合法版本对、比较 loading/success、supported all-zero、unsupported summary、非零 summary 但无 entity details、过滤为空、denied/network/unavailable/其他 gateway failure。保留 opaque code/message/details；不会从错误造成功或空结果。SemanticDiff 展示已有 asset counters 和完整 entityChanges，无客户端 canonical diff 运算或新分页。重复 history ID 不被当成两个不同修订；不截断非重复历史/实体结果。

所有新增本地文案/帮助/accessible names 使用现有 en/zh-CN catalogs。原生 labels/describedby、tabs/panels、关联 ID disclosure、结果/错误 status 与窄布局已验证。异步不调用 focus；原生 disabled Compare 在请求开始会自然失焦，用户 Shift+Tab 到 To 选择器后，结果不会抢回焦点。共享 SemanticDiff 保持原 props 与 NLE 消费兼容，shared CSS 改动限 Review/diff 包裹/布局。

Merge、generic canonical Apply、visual diff、conversation/checks/approval/rejection/comments/mentions/协作持久化均未实现或启用。单 Workspace、水平 Studio 导航、Inspector、Selection 生命周期、command projection、网关和路由契约未改。

## 执行验证

| 项目 | 实际结果 | 证据 |
|---|---|---|
| 首次 TDD | 30 个测试：14 pass / 16 fail | RED.json / RED.log |
| 第一实现后定向 | 49/49 pass，历史草稿行为由后续修正覆盖 | GREEN-04.json / WRITER_REPORT.md |
| 源码复核修正 RED | 51 个：43 pass / 8 fail；初次含超长 fixture，修正后第二次为预期行为失败 | CORRECTION-RED-01/02.json |
| 修正 writer GREEN | 51/51 pass | CORRECTION-GREEN-01.json |
| 外部最终定向（Review/SemanticDiff/NLE） | **68/68 pass** | TARGETED_FINAL.json |
| 稳定后完整前端套件 | **440/440 pass，28 files，0 skips/pending/todo**；只运行一次 | FULL_UNIT.json / gates/full-frontend-final.* |
| 测试身份核对 | 较已采纳报告增加41，删除/重命名0；旧执行仅用于计数比较，没有重跑旧任务 | TEST_ACCOUNTING.json |
| 现行 typecheck | `npm run typecheck` **PASS**；根 tsconfig strict，noUnusedLocals/Parameters=false | gates/type-policy.* |
| lint | **0 errors，46 既存 warnings**；去除 npm 标题、归一化路径后诊断与既有证据相同 | gates/lint.* / LINT_BASELINE_COMPARISON.json |
| localization | **21/21 pass**，属于完整套件，不重复累加 | LOCALIZATION_RESULTS.json |
| architecture | guard PASS，controls **120/120 pass** | gates/architecture* |
| Vite 新构建 | PASS；8 个外部产物；保留 >500kB chunk warning，未更改构建设置 | gates/build-* / BUILD_MANIFEST.sha256 |
| Chromium | **39/39 pass，exit 0**；1440×1000 / 390×844，en / zh-CN | browser-smoke-final/ |

### 补充检查与未夸大的边界

额外 `tsc -p tsconfig.app.json --noEmit --incremental false` 启用更严格 unused 规则，报告 **40** 个 TS6133/TS6196 诊断，均位于与已采纳树字节相同的非本任务路径；本轮 changed-path 诊断0。现行根配置允许 unused，因此现行 typecheck PASS 与该补充检查失败不是同一命令，也不互相替代。没有重跑前项任务或扩大到清理旧源文件。

额外 Node composite 检查参数不兼容 incremental=false，并尝试写 `snapshot/frontend/tsconfig.node.tsbuildinfo`，被只读挂载拒绝（TS6379、TS5033/EROFS）。**该操作已停止，无目标文件、无产品写入、无改权限/改输出重试、无 restore 隐藏。** 记录见 NODE_TYPECHECK_DENIAL.json。若要得到补充 Node/app-unused 的 clean 结果，需要另行处理所列旧文件与 Node 检查输出策略；不将其包装成本轮已通过检查。

### 浏览器及 mock 限制

使用既有 Chromium/CDP helpers 和一个本任务 Review fixture，无通用新生命周期 harness。输入是 CDP 的原生 pointer/key 事件，另有 DOM scroll/locale/geometry/ARIA 读取及 focus emulation；HTTP 是本地确定性 mock，通过未修改的生产查询 gateway，**不是后端集成证据**。受控乱序/context/unmount 在 unit tests 中验证。未测试物理设备、屏幕阅读器语音、真实 OS IME。

保留 smoke-01 缺 TREE_BINDING、smoke-02 误要求 disabled 原生按钮保焦、smoke-03 末尾过宽 POST 断言的失败记录；仅修正任务外部 fixture/断言，源码/新构建身份未变。最终记录21个本地 GET、9次显式 ordered compare；既有 shell 有4次 POST `/api/v1/dev/auth/token`，全部由本地 mock 拒绝403、无令牌和授权、无转发。最终校验严格限定这一已知拒绝请求，**不声称所有 POST=0**。Review/canonical mutation、notification endpoint、真实后端请求均0。

## 通知盘点及需求记录

源证据：当前前端基线树 `43038f740997d0ebb3a8c67f293da7edab563fdb`；可用后端参考为 Git 对象 commit `86d6aef94fd5e58da552e97c11473cff6eca734e`（发现时 local origin/main，不宣称最新远端/活跃后端候选）。盘点 A–G，逐项区分代码、wrapper、route、契约、mock/实际 transport、集成证据。

确认：inbox list/read-state service 存在；paginated wrapper 与 list(limit) 不同；read-all service 不等于 Controller endpoint；部分 providers 无外部发送即回 SENT；settings 文档是 design/contract candidate；当前 shell 没有 durable 通知 UI。Novu 有实际 HTTP transport 代码，但没有验证配置、凭据、实际交付。完整参数/响应/route 与权限限度见 inventory/NOTIFICATION_CAPABILITY_INVENTORY.md。

追加 **4 个消费者需求** UXW2-NTF-001..004，关联 FB-GAP-010..013，分别为 inbox、settings/subscriptions/bindings、admin queries/input、真实 delivery/verify/test/retry。两个现有账本各有对应记录，**不是8个独立需求**；原记录字节前缀保留。通知不阻塞本轮 Review，不授权通知 UI 或 backend 实施。通知请求、投递、浏览器权限、通知配置/凭据读取均0；另有 Owner 明确允许的证据 Git 临时认证，与通知隔离。

## 保全及治理

前端真实 HEAD/index 不变，最终完整工作树字节/模式与外部树核对通过；preexisting dirty 实现作为基线保留。tracked frontend dist 8个、backend static 3个均字节未变；依赖/lock/build config/历史 H4 ledger 未改。未触碰或要求并行 backend HEAD/refs/worktree/runtime 不变。

H4 Proposal A 与 tracked-dist Proposal A 保持采纳：本任务不做 H4 reconciliation；正式 Slice1C ledger integration 未在此执行；后续 freeze 前 reconcile/集成责任仍在。未重开先前 Canvas/pagehide/validator 任务。产品 commit/freeze/merge/push/publication 都未执行；无 EP19/Roadmap #23/Second Wave 解禁。Skill/Memory 写入0，没有新增 census。

## 证据和评审

SOURCE_DELTA.json、TASK_DELTA.patch 为本任务精确9路径 delta；COMPLETE_IMPLEMENTATION.patch 同时保留产品 HEAD 至当前树的已有脏实现，不能把所有 inherited changes 算成本轮。source/ 与 before/ 为逐路径原字节。BUILD_BINDING.json 将新构建及 manifest 绑定最终树；不是前一 bundle。

公開包只含本任务相关源/原始结果/截图/盘点与派生索引；不含私有配置、完整个人上下文、账号 home/browser profiles、凭据或无关历史包。MANIFEST.sha256 覆盖公开 payload；提交身份与远端逐字节验证放在 detached receipt，避免自引用 hash。固定提交链接以实际 Git 发布/readback 为准，不代替 reviewer acceptance。

`INDEPENDENT_REVIEW=REQUIRED`
`STOP=YES`
