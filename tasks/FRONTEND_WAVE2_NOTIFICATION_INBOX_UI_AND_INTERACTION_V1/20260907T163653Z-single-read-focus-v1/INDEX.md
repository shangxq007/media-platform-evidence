# 通知单读焦点连续性修正：独立评审入口

**结论：自然 Chromium 复现成立，通知局部最小修正与最终验证完成；等待独立评审。没有产品发布。**

- TASK: `FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1`
- CONTINUATION: `SINGLE_READ_FOCUS_CONTINUITY_CORRECTION_AND_VALIDATION`
- 基线实现树：`a8dc8bd3a0e4119e0a3a6bc8cdd18ed9ff789f72`
- 最终实现树：`c1d45edff185a99f3a961a9b29598ea2b34d0f18`（未提交工作内容）
- 变化：2 个通知路径；最终 170/170 targeted、576/576 全套、120/120 architecture controls、58/58 focused Chromium。
- 本页在新 continuation 包内，原 frontend/backend evidence 路径未修改。

## 阅读顺序

1. [中文完整报告](IMPLEMENTATION_REPORT_ZH.md) / [机器索引](INDEX.json)
2. [精确任务 patch](TASK_DELTA.patch)、[前后哈希](SOURCE_DELTA.json)、[最终源码](source/frontend/src/product/notifications/NotificationInbox.tsx)、[最终测试](source/frontend/src/product/notifications/NotificationInbox.test.tsx)
3. [基线自然复现](BASELINE_REPRODUCTION.md)、[组件 RED2](writer-green/RED2.md)、[首次 GREEN 的模型失败](writer-green/GREEN_ATTEMPT1.md)、[focused GREEN](writer-green/REPORT.md)
4. [全套身份对账](TEST_IDENTITY_ACCOUNTING.json)、[最终门禁](FINAL_GATE_BINDINGS.json)、[原始全套 JSON](FULL_UNIT.json)、[lint 对比](LINT_COMPARISON.json)
5. [新旧 58 条原生对照](NATIVE_COMPARISON.json)、[基线 activeElement](browser-baseline-02/FOCUS_OBSERVATIONS.json)、[最终 activeElement](browser-final-02/FOCUS_OBSERVATIONS.json)、[最终 native commands](browser-final-02/NATIVE_COMMANDS.json)、[最终退出与清理](browser-final-02/TEARDOWN.json)
6. [新 build manifest](BUILD_MANIFEST.json)、[HTTP 服务字节核验](browser-final-02/SERVED_ARTIFACTS.json)、[大型 JS 原字节/分块索引](ASSET_REVIEW_INDEX.md)、[重建顺序和哈希](RECONSTRUCTION_MAP.json)
7. [范围和历史保全](PRESERVATION.json)、[历史前次报告](historical/FINAL_REPORT.md)、[构建元数据说明](BUILD_COMPARISON_DISCLOSURE.json)

## 图像（辅助，activeElement 以机器记录为准）

- [旧 All 成功](browser-baseline-02/immediate-all.png)
- [新 All 成功桌面](browser-final-02/immediate-all.png)
- [新简中窄屏失败](browser-final-02/all-fail.png)
- [新 reconciliation 失败](browser-final-02/all-reconcile-fail.png)

## 限制

真实 backend / notification HTTP 为0；最终13次 auth-bootstrap POST 被本地 mock拒绝。模拟数据显式可见，identity/persistence/authorization/delivery未集成；未验证物理设备、屏幕阅读器语音或OS push。Happy-dom modeled blur 与 Chromium自然观察分开。保留既有可选 `/vite.svg` favicon缺失；必需JS/CSS引用完整。所有源代码/构建/日志按原字节保存，分块是附加副本，不重写旧JS。

[原固定评审入口](https://github.com/shangxq007/media-platform-evidence/blob/e18b98413069deb983f5d9785fdafb8f9d9c4ba0/tasks/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/20260907T135548Z-notification-inbox-v1/INDEX.md)

`MANIFEST.json` 覆盖除自身外的全部 payload；其 SHA-256 及固定 evidence commit/匿名远端回读以分离交付回执给出，避免自引用。
