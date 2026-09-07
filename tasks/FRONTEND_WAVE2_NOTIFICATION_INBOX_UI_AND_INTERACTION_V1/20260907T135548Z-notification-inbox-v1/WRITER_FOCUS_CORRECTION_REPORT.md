# 通知收件箱原生焦点修正 — Writer 报告

本次仅执行 BROWSER_FOCUS_CORRECTION.md，在原 WRITER_TASK.md / OWNER_TASK.md 范围内修复 toolbar read-all 禁用导致焦点落到 BODY 的问题。没有独立验收或原生浏览器通过声明。

## 范围与保留

- 工作树：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`。
- 分支：`agent/frontend-wave2-product-ux-v1`。
- HEAD：`f5e19cf53fd010eea2935dd29557e82a879e042c`；父提交：`01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`；前后不变。
- 原任务采用的 dirty baseline：`5c19a1045c3382140c62a84cf74ba3d4ec47e354`；本修正输入的原生验证 source tree 由修正任务记录为 `039bedca1a0056eb613ee695c1afcaf1aff20385`。本次不重新宣称验证这些既有 tree。
- 根 AGENTS.md 适用全部修改；祖先及目标目录没有其他适用 AGENTS.md。当前 Owner 禁止 freeze/commit 的明确授权优先于根文件的冻结验证流程；耐久规则对齐仍是单独治理事项。无新增权限问题或实际工具拒绝。
- 仅修改 `frontend/src/product/notifications/NotificationInbox.tsx`（展示/交互源文件）和既有 `NotificationInbox.test.tsx`（行为测试）。全部使用原地写入。
- 四个 DOCUMENTATION_ALLOWLIST.json 路径由 Hermes 拥有，保留其已有 dirty 修改，不计为 writer 修改。本次前后四文件 SHA-256 均相同，详见 `focus-correction-evidence/scope-result.json`。
- 全部 7954 个受检 Git tracked/非忽略 untracked 文件中，仅上述两个变化，7952 个保持相同；没有新增路径或意外变化。HEAD、index diff、stash 前后相同。既有源文件、共享 InteractionDialog、AppShell、Selection、Review、Canvas、样式、本地化及 source manifest 保持原样。
- 无 staging、commit、freeze、merge、push、远端操作、发布、build、browser、全套测试、旧 validator、架构 guard 或后端测试。没有创建最终候选提交，也没有 main 集成。以前的报告和失败记录保持原样。

## 实现

给现有 read-all 原生按钮增加模块内 ref。通过既有 mutation 校验并获得同步操作锁后，如果该按钮仍是当前焦点，就在 busy 禁用提交前将焦点移至现有活动 All/Unread 筛选按钮。这个按钮在 mutation pending、刷新、成功 count=0 和失败时均保持可用，因此 Escape 仍可冒泡到未修改的 InteractionDialog，关闭后由原 primitive 恢复入口焦点。

没有等待异步完成再强制恢复焦点，也没有新增全局键盘监听。若另一个有效控件已拥有焦点，不执行移动；用户随后移到 Refresh 或自行 blur，也不会在 read-all 完成时被拉回。原 unread 行消失焦点意图及其取消逻辑、旧操作 ownership、重复抑制和 context 生命周期完全不变。unknown count、count=0 禁用、单条及 inbox-wide action support 条件、确认后重新查询语义均未改动。

## RED → GREEN 与限制

在生产修改之前，新增 10 个行为用例并运行 RED。64 个 inbox 用例中 59 通过、5 失败：en/zh-CN × 成功/失败的 4 个用例重现 BODY 焦点，另一个重现 pending 时从实际焦点派发 Escape 无法关闭。全部原有 54 个 inbox 用例通过。随后应用上述源文件修正，首次 GREEN 全部通过，没有放宽原断言。

新增用例涵盖：两种语言下 read-all pending；延迟 reconciliation 后确认 count=0/Unread 空列表及继续禁用；失败保留 2 个未读且重新启用；从实际焦点发送 Escape 并恢复入口；pending 时关闭并忽略 late completion；成功/失败中移到 Refresh、移走后又 blur 回 BODY 时不抢焦点；toolbar 没有焦点时程序激活也不改变其他有效控件。

happy-dom 不实现 Chromium 禁用按钮时的原生焦点丢失，而且拒绝对 disabled 按钮调用 blur。因此测试仅在禁用后的 toolbar 仍拥有焦点时，临时移除 DOM disabled 标志以发送 blur，随即恢复；该模型不会干扰已经完成的同步焦点转移。Escape 始终派发到 `document.activeElement`，没有直接派发到 dialog 来隐藏 BODY 问题。这是明确建模的单元输入，不等于原生 Chromium、屏幕阅读器或物理设备证明。

| 检查 | 总数 | 通过 | 失败 | 跳过/pending | 运行错误 | 退出码 |
|---|---:|---:|---:|---:|---:|---:|
| RED-01 inbox | 64 | 59 | 5 | 0 | 0 | 1 |
| GREEN-01 targeted | 157 | 157 | 0 | 0 | 0 | 0 |
| Typecheck | — | — | — | — | — | 0 |
| Scoped ESLint | — | — | — | — | — | 0 |

GREEN 构成：inbox 64 + adapter 44 + AppShell 36 + localization 13 = 157。`test-summary.json` 从机器可读 assertion records 统计并核对报告总数；无 todo。typecheck/lint 日志为空。生产源文件及测试在 GREEN 后没有修改。原始 JSON、完整失败、stdout/stderr、命令和退出码都在 `focus-correction-evidence/`。

## 身份与精确命令

没有 Git 写操作或新候选 SHA。以下工作文件 SHA-256、完整前后文件哈希清单和 `focus-correction.patch` 标识本次实际增量；不能把它们误称为已冻结 Git tree。

- `frontend/src/product/notifications/NotificationInbox.tsx`
  - Before SHA-256: `98524d03360b971d7789b2b9624534df23e1b4f39ea3f3b426b3067faf0bc4d3`
  - After SHA-256: `9c8fe17ec79523d04a42b4c6c214b0942e0c25de345866d7b869ff0252ca5861`
- `frontend/src/product/notifications/NotificationInbox.test.tsx`
  - Before SHA-256: `bb0a9a833906a21c1741cd16555161c238e880938231057b002aa7b0b566c31a`
  - After SHA-256: `a46b4eee16ae06112bf97f9162617110ac394dfb3b66f4bcf06b76f7b78cca0c`

最终工作文件清单 `focus-correction-evidence/after-hashes.json` SHA-256：`1ed27b74a67cab1b5612190c2f0ec1d2864a6f72b179c64a6020fe7f7aa38784`。

工作目录：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`；退出码 `1`。

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/focus-correction-evidence/RED-01.json src/product/notifications/NotificationInbox.test.tsx
```

工作目录：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`；退出码 `0`。

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/focus-correction-evidence/GREEN-01.json src/product/notifications/NotificationInbox.test.tsx src/product/notifications/adapter.test.ts src/components/app-shell/AppShell.test.tsx src/localization/localization.test.tsx
```

工作目录：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`；退出码 `0`。

```sh
./node_modules/.bin/tsc --noEmit
```

工作目录：`/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`；退出码 `0`。

```sh
./node_modules/.bin/eslint src/product/notifications/NotificationInbox.tsx src/product/notifications/NotificationInbox.test.tsx
```

## Hermes 后续验证

仍需由 Hermes 进行原生 Chromium 独立验证：Unread 点击 read-all 后立刻检查焦点仍在活动筛选按钮；延迟回执/刷新及 count=0 后从实际焦点发送 Escape，检查关闭及入口恢复；同样检查失败和移到 Refresh 后不抢焦点。保留 smoke-01/02 失败证据，不能将本报告或 happy-dom GREEN 当成原生通过。

不需要新的文案、source-manifest key、路径分类或 ledger 更新；四个文档仍由 Hermes 管理。真实 inbox adapter、权限、持久化和投递缺口没有变化。

REAL_BACKEND_INTEGRATION=NOT_ESTABLISHED
REAL_NOTIFICATION_DELIVERY=NOT_PERFORMED
INDEPENDENT_REVIEW=REQUIRED
PRODUCT_COMMIT_FREEZE_MERGE_PUSH=NOT_PERFORMED
PRIOR_ACCEPTED_WORK_REOPENED=NO
