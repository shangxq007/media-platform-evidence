# FRONTEND Wave2 Notification Inbox — 独立评审入口

**新实现树：`a8dc8bd3a0e4119e0a3a6bc8cdd18ed9ff789f72`；基线：`5c19a1045c3382140c62a84cf74ba3d4ec47e354`。INDEPENDENT_REVIEW=REQUIRED；真实集成NOT_ESTABLISHED。**

- [中文实现报告](IMPLEMENTATION_REPORT.md)
- [源码与before/after索引](SOURCE_INDEX.md) / [精确delta](SOURCE_DELTA.json) / [patch重放](PATCH_REPLAY.json)
- [行为与实际测试身份](SOURCE_TEST_MATRIX.md) / [最终563项原始结果](FULL_UNIT.json) / [157项针对性结果](TARGETED_FINAL.json) / [身份核算](TEST_ACCOUNTING.json)
- [adapter/fixture边界](ADAPTER_CONTRACT.md) / [真实集成待验收](INTEGRATION_ACCEPTANCE.md)
- [最终browser66项](browser-smoke-final/NATIVE_CHECKS.json) / [原生输入](browser-smoke-final/NATIVE_COMMANDS.json) / [HTTP口径](browser-smoke-final/HTTP_ASSERTIONS.json) / [请求事件](browser-smoke-final/BROWSER_HTTP_REQUESTS.json)
- [source/build binding](browser-smoke-final/TREE_BINDING.json) / [外部build入口](build/index.html)（须通过local HTTP server使用；不是部署服务）
- [preservation](PRESERVATION.json) / [变更允许集](ALLOWLIST.json) / [文档允许集](DOCUMENTATION_ALLOWLIST.json)
- [首次原生焦点失败](browser-smoke-01/FAILURE.txt) / [BODY诊断](browser-smoke-02/desktop-en-pre-escape-focus.json) / [修正报告](WRITER_FOCUS_CORRECTION_REPORT.md)

## 图像
- [桌面英文详情](browser-smoke-final/desktop-en-detail.png)
- [窄屏英文](browser-smoke-final/narrow-en-detail.png) / [原生滚动全文](browser-smoke-final/narrow-en-detail-scrolled.png)
- [窄屏中文](browser-smoke-final/narrow-zh-CN-detail.png) / [原生滚动全文](browser-smoke-final/narrow-zh-CN-detail-scrolled.png)
- [单条失败](browser-smoke-final/desktop-en-read-failure.png) / [整箱partial失败](browser-smoke-final/desktop-en-read-all-failure.png)
- [未配置](browser-smoke-final/desktop-en-unavailable.png) / [拒绝](browser-smoke-final/desktop-en-denied.png) / [未知](browser-smoke-final/desktop-en-unknown.png)
- [实际模拟目标导航](browser-smoke-final/supported-local-fixture-target.png)

## 已接受来源（非本任务新执行）
[Review与通知库存固定入口](https://github.com/shangxq007/media-platform-evidence/blob/395b64b9f5f64f4c38accad9159e596c602e1161/tasks/FRONTEND_WAVE2_FOCUSED_REVIEW_UX_CONVERGENCE_V1/20260907T121230Z-review-ux-v1/INDEX.md)

manifest只覆盖本包，不覆盖前后并发任务。发布后的精确commit/manifest/remote readback由任务receipts目录分离记录，避免自引用。历史失败不删除、不同树结果不混同。没有产品commit或发布。
