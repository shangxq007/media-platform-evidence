# 通知单条已读焦点连续性：有界修正验证报告

## 结论与评审边界

**焦点遗漏已在原始基线构建的自然 Chromium 行为中复现，已作通知局部最小修正，并完成最终验证；需要独立评审。** 本报告记录工程证据，不代替 Owner/独立评审接受，不授权产品冻结或发布。

最初独立审查只有静态源码与已有测试检查，**不是审查者新增的原生浏览器复现**。本 continuation 的 `browser-baseline-02` 才是新执行的自然 Chromium 复现。

## 基线与修改范围

- 分支：`refs/heads/agent/frontend-wave2-product-ux-v1`；产品 HEAD 始终 `f5e19cf53fd010eea2935dd29557e82a879e042c`。
- 基线脏工作内容树：`a8dc8bd3a0e4119e0a3a6bc8cdd18ed9ff789f72`；修正后工作内容树：`c1d45edff185a99f3a961a9b29598ea2b34d0f18`。二者都不是本次新产品提交。
- 初始 985 个范围内路径、字节及执行模式与基线一致，无额外前端变化。最终整个该工作树 7954 个文件与物化树相符，缺失/新增/字节或模式不符均为 0。
- 真实 Git index SHA-256：`675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`，前后未变；产品 HEAD、分支、porcelain 路径集合未变。原先未跟踪文件仍未跟踪，不能因此用 HEAD 代替实现树。
- 本次产品变化只有 `NotificationInbox.tsx` 和 `NotificationInbox.test.tsx`。完整补丁见 [TASK_DELTA.patch](TASK_DELTA.patch)，端点哈希见 [SOURCE_DELTA.json](SOURCE_DELTA.json)，可检查 [修正源码](source/frontend/src/product/notifications/NotificationInbox.tsx) 和 [修正测试](source/frontend/src/product/notifications/NotificationInbox.test.tsx)。外部 index 重放得到精确最终树；`git diff --check` exit 0。
- 后端实现、tracked frontend dist、backend static、共享 InteractionDialog、路由、认证、permission 架构、adapter contract、目录文案均未修改。没有第二个 Slice1C 台账或 H4 reconciliation；H4 Proposal A 与 tracked-dist 政策不变。

## 缺陷与最小修正

基线 mark() 只在 read-all 按钮持焦时同步转移焦点。单条按钮禁用会在 Chromium 自然失焦到 BODY；BODY 不在 InteractionDialog 的 Escape 处理子树内。All 成功时行仍保留，因此不能借助 Unread 行删除恢复。pending、延迟失败/无效回执/rejection，以及确认已读后的 reconciliation 失败均覆盖。

修正让两个 read onClick 都显式传入 `event.currentTarget`；mark() 仅在该 initiatingControl **实际拥有 document.activeElement** 时，于 busy/disable 之前将焦点移至当前 All/Unread 筛选按钮。移除不再需要的 readAllButton ref。**采用筛选按钮是本次实施选择，不是将 Reviewer 的具体控件偏好当作新 Owner 冻结。**

不增加全局键盘监听、焦点计时器或异步强制回收。mutation owner、generation、abort、query、原 Unread 行删除恢复逻辑保持不变。用户主动移到 Refresh 后 completion 不抢焦点；程序调用 read.click() 而 Refresh 持焦也不抢焦点。旧 closed mutation 的 completion 不得解锁新 mutation；原 single/all 重复与重叠抑制、身份/adapter 更换和卸载 retirement 由保留的组件测试及新 close/reopen 用例保护。未新增 Selection 写入或 canonical Operation 调用，AppShell 关联测试通过。

## RED/GREEN：不改写失败历史

| 执行 | 真实结果 | 解释 |
|---|---:|---|
| 初次组件命令 | exit 1，未收集测试 | readonly `.vite-temp` 配置加载失败；不是产品 RED。改用现有 `--configLoader=runner`，未松绑或改配置 |
| Stage1 focused RED | 68 pass / 9 fail / 77，exit 1 | 64 原有测试通过，13 新增用例中 4 为已通过保护；1 项明确建模 blur |
| 校准后 RED2 | 68 pass / 9 fail / 77，exit 1 | 产品仍精确基线；将新测试过度限定的同行详情控件校准为稳定筛选控件，仍有意义地失败 |
| 首次 GREEN | 75 pass / 2 fail / 77，exit 1 | 两个旧参数化模型无条件要求 BODY，与同步避免失焦冲突；失败保留 |
| 最终 focused GREEN | 77/77，exit 0 | 旧模型仅在 read 按钮仍实际持焦时模拟 blur，保留原测试身份与最终 moved-away/no-reclaim 断言 |
| 最终受影响范围 | 170/170，exit 0 | 通知组件77、adapter44、AppShell36、localization13 |
| 最终完整前端 | 576/576，30 文件，exit 0 | 仅最终树全套执行一次；相对原563新增13，移除0、重复0、skip0、fail0 |

所有命令、日志、JSON 与退出码分别保留在 `writer-red/`、`writer-green/`、`gates/`。新测试标题校准映射及文案断言纠正见 `writer-green/TEST_REVISION.md`。原有 64 个测试的**身份**保留，其中两个参数实例的 modeled-blur 前置条件适配了预防行为；并非宣称原始测试源码全部逐字不变。完整身份使用 `[relative file, ancestorTitles array, title]` 对账，见 [TEST_IDENTITY_ACCOUNTING.json](TEST_IDENTITY_ACCOUNTING.json)。

Happy-dom 不实现 Chromium 原生禁用 blur。8 个 RED 检查的是禁用按钮仍持焦而非稳定启用控件，1 个补充显式建模 BODY 失焦；它们均不冒充原生证据。

## 原生 Chromium 结果与实际焦点

浏览器：`Chrome/149.0.7827.55`；桌面 1440×1000，窄屏 390×844；English 和简体中文。CDP focus emulation 与 viewport emulation 已披露，不是物理手机或 OS 辅助技术测试。

基线与最终执行的 **58 条 assertion identity + expression 完全相同**，见 [NATIVE_COMPARISON.json](NATIVE_COMPARISON.json)。基线 24 pass / 34 fail，断言 runner exit 1；最终 58/58，断言 runner/harness exit 0，Chromium 正常 Browser.close exit 0。基线浏览器由清理器 SIGTERM（-15）结束，不把它记作正常 native process exit 0。两轮 fixture 均为 task-owned 本地 receiver；最终端口已关闭。

| 场景 | 基线新观察 | 修正后观察与断言 |
|---|---|---|
| All 即时成功（原 fixture，无 adapter 注入） | 行保留、BODY、Escape 无法关闭 | All 持焦、行仍保留、Escape 关闭并恢复 launcher |
| All 单条 pending | 按钮 disabled 后 BODY | All 持焦、实际键盘 Escape 可关闭，late completion 不重开 |
| 延迟成功/失败/invalid/reject | BODY，未读正确也不能证明键盘连续性 | All/全部持焦；失败未冒充已读；Escape 与 launcher 恢复通过 |
| 确认已读后 reconciliation loading/failure | BODY | 全部在 loading 与失败后均持续持焦 |
| Unread 成功移除行 | pending BODY，完成后原恢复机制有效 | pending 与完成均未读按钮持焦 |
| inbox-wide read-all | 原焦点行为正确 | pending/成功/Escape 仍正确 |
| 主动移到 Refresh/程序化激活 | 保护项通过 | 无 focus theft；程序化场景明确使用 DOM click |
| close/reopen 新旧 mutation | 独立关闭前需原生 close 按钮建立前提 | 实际 Escape 可关闭；旧完成不解锁新 read，不抢焦点 |
| pending 时 Tab | 本次路径能重新进入对话框 | 留在对话框内可用控件 |

基线 `pending-late-does-not-reopen` 的关闭前提因 Escape 失败未成立，是**依赖性失败**，不是独立证明“旧结果重新打开”。不将 34 条失败当作 34 个不同缺陷，也不宣称所有 Tab 操作都失效。

原生激活通过 Tab 到达真实按钮后 Enter；Escape 使用可信 `Input.dispatchKeyEvent`，未先点击其他控件掩盖失焦。记录每步 activeElement、focus/keydown 的 trusted 标志、原生命令、截图。观察见 `browser-*/FOCUS_OBSERVATIONS.json` 与 `*-events.json`，不是从对话框可见或 unread count 推断成功。

外部 controlled adapter 通过 React fiber 找到**显式 simulated InboxSession** 的 source adapter，仅在浏览器内包装 markRead/markAllRead/list，使用明确 resolve/reject 边界；不修改 bundle 或产品 adapter 合同，不注入 BODY.focus/blur。通过 `holdList` 暴露 reconciliation。导航重新创建 fixture；所有注入代码随原始 `focus_smoke.py` 提供。测试挂载/轮询基础设施有既有等待，但**不靠任意 sleep 制造 pending 竞态**。

两个启动失败保留：baseline-01 的 continuation 相对 venv 路径错误，以及 final-01 TREE_BINDING 键名不匹配。均未运行浏览器断言，不算产品 RED 或 PASS。修正外部 helper 后使用新目录完整执行。

## 最终门禁、构建和可检索交付

Typecheck、lint、architecture guard、architecture controls 120/120 均 PASS。lint 0 errors、46 个既有 warnings；仅规范化确切 snapshot 路径后，新旧完整 lint 日志逐字一致，新增诊断0。没有重开 app-unused、Node cache、pagehide/validator 或后端验证。

新构建输出到本 continuation 外部 `build/`，没有写 tracked dist/backend static；Vite effective outDir 在调用 build 前解析断言。完整 8 个 emitted 文件 SHA-256 清单：

`BUILD_MANIFEST_SHA256=e60cf138d6c8771967362173c1fe8314954af48f766e4c37ab6616d811ebd164`

27 条静态资源引用中必需资源缺失0；1 条历史可选 `/vite.svg` favicon 缺失。已证明 baseline/current `frontend/index.html` 字节相同且旧构建同样无该文件。初版 helper 将全部 href 一律视为必需而失败，其原记录保留；现在只精确分类既有 `rel=icon`，没有新增文件、改产品或重建旧实现。不是“所有资源引用都存在”的无条件结论。

最终运行前逐个读取本地 HTTP 的 8 个 emitted 文件，与磁盘原始字节哈希全部一致；完整 source→tree→build manifest→served artifact→browser binding 可追溯。

旧构建和新构建都保留既有 JSX source metadata，较长 external snapshot 路径会扩展 bundle 文本；并非只凭 bundle 字节差量推断产品变化。说明见 `BUILD_COMPARISON_DISCLOSURE.json`。CSS 字节未变，其他 JS **不宣称字节可复现相等**；未修改 build config 来清理这项历史元数据。

`baseline-build/` 保留原 8 个文件，旧 main JS **未重建、未更改字节**。`review-chunks/` 提供新旧较大 JS 的 UTF-8 边界原始分块（4 文件、41 部分）；[RECONSTRUCTION_MAP.json](RECONSTRUCTION_MAP.json) 含顺序/偏移/大小/逐块与原文件 SHA-256，串接已核验与原始文件逐字节相等。无需依赖 GitHub 大文件预览。

## 网络、安全与未完成集成

最终页级记录 HTTP(S) 请求91，本地 receiver 请求70（含8个额外服务字节核验及 health/导航等）；它们是不同观察口径。13 次 auth-bootstrap POST 均由本地 mock 403 拒绝且未转发；真实 backend 请求0、notification HTTP 请求0、页级外部请求尝试0。基线对应 auth POST13、真实后端0；不是把模拟 read 当持久化。浏览器禁用后台网络并用 host resolver 限制外部解析；页级 CDP 计数不充当全 OS 网络审计。

普通未配置路径保持 unavailable/unknown，未知未读数不转成0；read-all 仅限 adapter 声明 inbox support。真实 identity subscription、后端持久化、tenant/resource authorization、分页/read-all HTTP 合同、delivery 仍待集成。没有 localStorage 通知持久化、静默 mock fallback、已知不匹配的通知 API、browser permission 请求、OS push、settings/admin。未验证物理设备、屏幕阅读器语音、真实通知送达。

## 历史与发布边界

前次563/563、157/157、66/66 native exit0 是**历史结果**，不是本修正树的新结果。前次 read-all 焦点失败与修正、mock/network/device 限制均保留。前次 evidence commit `e18b98413069deb983f5d9785fdafb8f9d9c4ba0` 与 manifest `42b5ee08df4990bd379c239ff2f02a01027f4e88d2346897f1e21c56061ffb56` 不变。374 个历史文件哈希核验无变化，含原361文件公开包与旧build；没有要求后台 EP19 lane stationary，也没有执行它的门禁。

本包为新追加 continuation，产品 commit/freeze/merge/push/publication/deployment 均未执行。工程封包后才进行证据仓库追加发布；固定 evidence commit、最终 manifest 哈希与匿名远端回读结果在**分离的交付回执**中，避免报告/manifest 自引用哈希循环。证据发布不等于产品发布。下一步仅独立评审。

## 工程最终字段（交付字段在分离回执）

```text
TASK=FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1
CONTINUATION=SINGLE_READ_FOCUS_CONTINUITY_CORRECTION_AND_VALIDATION
LANE=FRONTEND
FRONTEND_BRANCH=refs/heads/agent/frontend-wave2-product-ux-v1
BASELINE_IMPLEMENTATION_TREE=a8dc8bd3a0e4119e0a3a6bc8cdd18ed9ff789f72
FINAL_IMPLEMENTATION_TREE=c1d45edff185a99f3a961a9b29598ea2b34d0f18
PRODUCT_CHANGED_PATHS=2
BASELINE_REPRODUCTION_RESULT=REPRODUCED_NATIVE; RED2=68_PASS_9_FAIL
MODELED_VS_NATIVE_EVIDENCE=SEPARATE; HAPPY_DOM_MODEL_DISCLOSED; CHROMIUM_NATURAL_BLUR_REPRODUCED
ALL_SINGLE_READ_FOCUS=PASS
UNREAD_SINGLE_READ_FOCUS=PASS
PENDING_ESCAPE_AND_LAUNCHER_RESTORE=PASS
FAILED_READ_FOCUS=PASS
RECONCILIATION_FAILURE_FOCUS=PASS
NO_FOCUS_THEFT=PASS
CLOSE_REOPEN_STALE_COMPLETION=PASS
READ_ALL_REGRESSION=PASS
TARGETED_TEST_RESULTS=170/170; NOTIFICATION_COMPONENT=77/77
FULL_TEST_IDENTITY_ACCOUNTING=BASELINE=563; FINAL=576; FILES=30; ADDITIONS=13; REMOVALS=0; DUPLICATES=0; SKIPS=0; FAILURES=0
REQUIRED_FRONTEND_GATES=PASS; TYPECHECK,LINT,ARCHITECTURE; CONTROLS=120/120; NEW_LINT_DIAGNOSTICS=0; EXISTING_WARNINGS=46
FOCUSED_BROWSER_RESULTS=58/58; NATIVE_CHROMIUM_EXIT=0; ASSERTION_EXIT=0; HARNESS_EXIT=0
BUILD_MANIFEST_SHA256=e60cf138d6c8771967362173c1fe8314954af48f766e4c37ab6616d811ebd164
REAL_BACKEND_REQUESTS=0
NOTIFICATION_HTTP_REQUESTS=0
BACKEND_CHANGES=0
TRACKED_DIST_CHANGES=0
BACKEND_STATIC_CHANGES=0
NEW_BACKEND_REQUIREMENTS=0
HISTORICAL_EVIDENCE_PRESERVED=YES; 374_CHECKED_0_CHANGED; PRIOR_PUBLIC_PACKAGE_361_FILES_UNCHANGED
REAL_BACKEND_INTEGRATION=NOT_ESTABLISHED
PRODUCT_PUBLICATION=NOT_PERFORMED
INDEPENDENT_REVIEW=REQUIRED
STOP=YES
```
