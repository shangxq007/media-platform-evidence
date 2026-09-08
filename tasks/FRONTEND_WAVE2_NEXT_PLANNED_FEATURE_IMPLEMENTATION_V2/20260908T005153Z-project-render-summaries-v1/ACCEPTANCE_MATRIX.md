# 有界验收与证据

- 计划和缺口：SELECTION_AND_SCOPE.md，plan-source/ 原文，最终 SOURCE_DELTA.json。
- 搜索/筛选/排序/reset/只读详情：RenderBrowser.test.tsx 与 TARGETED_FINAL.json；native profile-search、native-status-filter、native-id-desc、reset-list、five-fields。
- 权限/来源/未知/拒绝/unsupported/error：source.test.ts 与完整执行身份；native query-*、ordinary-unconfigured-no-list。
- request/scope/lifetime retirement：source/RenderBrowser 测试的展开身份；native loading-retires-content、late-cancelled-success-ignored、retry-recovers。
- 焦点/原生键盘：native-tab-reaches-inspect、tab-inside-dialog、escape-restores-launcher、loading/cancel focus；NATIVE_INPUT_TRUST.json；模拟延迟注入，不是真服务。
- 英文/中文/窄屏和安全文本：对应截图、no-html-injection、narrow-no-page-overflow；截图人工视觉检查不是辅助技术实机验证。
- accepted shared消费者：受影响命令包含 Projects、通知Inbox、AppShell、InteractionShell、localization、routes；完整套件额外覆盖其他既有功能，未重开其评审。
- build/served/patch identity：BUILD_MANIFEST.json、SERVED_ARTIFACTS.json、PATCH_REPLAY.json；静态资源引用发现有 scope 限制，完整输出字节 census 独立核验。
- 架构 guard/controls：gates 原始日志与命令/树/退出；这是可执行静态边界检查，不证明实际后端 authorization。

全部上述结论绑定 final-validation/FINAL_TREE.txt；attempts 和 browser-final-01/02 是历史失败，不冒充最终通过。
