# CORRECTION 01 Writer 交接

已完成有界源码修正，未提交。浏览器视觉验收仍由 Parent 在新 actual-tree 捕获及七门禁后执行；本次未运行浏览器、未构建、未建立新 build binding。此前 browser pass 只证明记录的有界行为，不代表视觉验收。

## 精确增量

仅修改以下 3 个文件。以本轮开始时的实际工作区为基线，完整增量见 [CORRECTION_01.patch](correction-01/CORRECTION_01.patch)，前后 SHA-256 见 [SOURCE_MANIFEST.json](correction-01/SOURCE_MANIFEST.json)。既有 V10 patch、handoff、截图和 manifests 均未改写。

- `frontend/src/product/publication/publication.css`：Publication toolbar 的 account/status/sort/timezone 原生 select 使用既有 `--surface-2` / `--text-primary`，并显式设置 option 的同一前景/背景；边框、圆角、padding 使用既有表单 tokens `--border-default` / `--radius-md` / `--space-2`。选择器仍仅作用于 Publication toolbar。全局主题和其他 CSS 规则未改。
- `frontend/src/product/publication/PublicationWorkspace.tsx`：给 Search 显式传入 `placeholder={text('search')}`。实际共享 primitive 的缺省 placeholder 是英文 `Search`；现有 catalog 的 `publication.search` 已有英文 `Search supplied publications` 和中文 `搜索已提供的发布内容`，因此复用既有翻译，无 catalog 或 source-manifest 修改。
- `frontend/src/product/publication/PublicationWorkspace.test.tsx`：追加 dark/light 实际组件四个 select 及其 options 的计算色彩对比度回归，和中文可见 placeholder 回归。旧测试断言全部保留，未改几何或点击 oracle。

## 缺陷证据与修复结果

原规则是 `background: var(--ff-panel, white); color: inherit`。实际主题未定义 `--ff-panel`，暗色根前景为 `#E8EAED`，因此出现白底浅字。使用仓库真实 tokens/foundation/publication CSS 及实际渲染组件，在 happy-dom CSSOM 中读取计算颜色；针对 happy-dom 保留的 `inherit` / 透明背景，显式沿祖先解析。对比度使用 sRGB 相对亮度，门槛 4.5:1。

| 主题 | 修复前前景 / 背景 | 修复前对比度 | 修复后前景 / 背景 | 修复后对比度 |
| --- | --- | --- | --- | --- |
| dark | `#E8EAED` / white | 1.2053:1，失败 | `#E8EAED` / `#181B20` | 14.3228:1 |
| light | `#111827` / white | 17.7397:1 | `#111827` / `#F3F4F6` | 16.1195:1 |

[computed-colors.json](correction-01/computed-colors.json) 包含四个 select 和各 option 的逐项值，原始输出保存在 red-contrast/affected-green 的 output.log。**这些是 DOM 模拟环境的计算色彩证据，不是原生 Chromium 新截图或系统 option 弹层的视觉证明。** Parent 仍需查看新桌面/窄屏、EN/中文结果及原生选项显示。

真正 RED：`red-contrast` 为 17 = 15 passed + 2 failed（暗色对比度 1.2053 < 4.5；中文 placeholder 实际为 Search），0 pending/errors。修复后相同断言全绿。前两个调试运行也完整保留：`red` 在错误 cwd 下找不到 Vitest，不能算行为 RED；`red-behavior` 中 CSS raw import 被 Vitest 默认 CSS 处理清空，两项样式测试出现 `No effective color`，另有真实中文失败。测试后改为已有 Canvas 测试采用的 `readFileSync` 读取真实 CSS，得到上述有效 red-contrast；没有降低断言。

## 验证 receipts

每项精确 argv/cwd/UTC 起止/exit 在对应目录 `command.json`，原生输出在 `output.log`；测试和 lint 的原生 JSON 在 `results.json`。汇总见 [RUN_SUMMARY.json](correction-01/RUN_SUMMARY.json)。执行 cwd 为工作区 `frontend/`，命令均通过本轮 `correction-01/run.py <运行目录> <下列命令>` 留存。

```text
node node_modules/vitest/vitest.mjs run src/product/publication src/app/routeTree.test.tsx src/foundation/surfaceRegistry.test.ts src/interaction src/components/app-shell/AppShell.test.tsx src/localization --configLoader runner --no-cache --reporter=default --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/writer/correction-01/affected-green/results.json
npm run typecheck
node node_modules/eslint/bin/eslint.js src --format json --output-file /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_PUBLICATION_WORKSPACE_CALENDAR_AND_INSPECTION_V10/writer/correction-01/lint/results.json
npm run architecture:guard
npm run architecture:guard:test
```

- affected-green：exit 0；8 suites，197 = 197 passed + 0 failed + 0 pending，0 errors；保留原 writer 194 个测试身份，新增 3，移除/重复 0。见 `test-identity.json`。
- typecheck：exit 0。
- lint：exit 0；0 errors、46 warnings。所有 message 对象与原 writer/final-lint 原生报告身份完全相同；见 `lint-identity.json`。
- architecture：exit 0，PASS；既有 guard 源码未改。
- architecture-controls：exit 0；原生 TAP 131 = 131 pass，fail/cancelled/skipped/todo 均 0。见 `architecture-controls-counts.json`。
- `git diff --check`：exit 0；本轮保全/差异/报告算术核验脚本 `python correction-01/finalize.py` 成功。

## 保全、指令与后续边界

已读取 VISUAL_CORRECTION_01.md、WRITER_BRIEF.md、原 WRITER_HANDOFF.md、RECOVERY.json 和适用根 AGENTS.md；祖先与嵌套搜索未发现其他适用指令。最新 Owner 不提交/不 freeze 要求优先于根 AGENTS 候选 SHA 冻结规则；记录冲突，不编辑治理指令，指令对齐属于另行治理范围。无 Skill/Memory、后端、远端或集成操作。

分支：`agent/frontend-wave2-product-ux-v1`。HEAD：`f5e19cf53fd010eea2935dd29557e82a879e042c`，parent：`01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`。这些仅记录既有提交身份，不是本轮 candidate commit。真实 index SHA-256：`675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`。HEAD/parent/branch/index/stash 均与本轮前相同；7,985 个其他工作区文件 hash 不变，新增/删除源文件 0。原证据 10,369 个文件 hash 全部保留，包含早期截图。见 [preservation.json](correction-01/preservation.json) 和 `before.json`。本轮证据自有新 manifest，不替换旧 manifest。

Parent 下一步：捕获新 actual tree、执行既定七门禁，再做新的原生视觉验证和 build binding。普通真实 Publication 路由的 source-not-connected 仍未在原生浏览器中覆盖；按 correction brief，由 Parent 单独启用 Project fixture、省略 Publication provider，标明“isolated Project context”，不声称真实集成。本 Writer 交接不构成独立最终验收或交付。
