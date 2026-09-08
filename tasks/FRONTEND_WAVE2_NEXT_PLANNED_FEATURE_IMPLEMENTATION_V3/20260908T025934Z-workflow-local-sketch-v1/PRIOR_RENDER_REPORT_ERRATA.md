# V2 Render 报告追加勘误（Owner 指定，两项）

原报告：IMPLEMENTATION_REPORT_ZH.md（V2 20260908T005153Z-project-render-summaries-v1）。原证据提交 ac035cdf9e942d1a0344a5f56cab63c76a94f487；manifest eae743636b840e3291cfc41c51cc5b4ecdb1004a7af381952b14f401e8f4e99f。原封存报告/提交保持原样；本文件仅追加纠正，不是产品修复。

1. 原报告“render.summaries.query 仅为前端消费提案”中的 key 不正确。实际 REAL_RENDER_SUMMARIES_QUERY_KEY 为 `render.job.summary.query`。支持源码：frontend/src/product/render-browser/source.ts；仍是前端消费提案，非接受的后端合同/授权证明。
2. 原报告 scope 描述错误纳入 workspace 且未准确列出 session。实际 RenderScope 与 scopeSchema 字段精确为 `principalId`, `tenantId`, `sessionId`, `projectId`。requestId、access projection、adapter identity 与组件 lifetime 提供额外隔离。Workspace 不在该请求 scope，不向代码补加。支持源码：frontend/src/product/render-browser/source.ts、RenderBrowser.tsx；原选择记录允许仅使用相关维度。

Owner 采纳 PASS_BOUNDED_WITH_REPORT_ERRATA；PRODUCT_CORRECTION_REQUIRED=NO。勘误没有触发旧产品重建/重测。旧交付记录仍为完整匿名 Git 字节核验、raw HTTP 216/219（三项 timeout），不是 219 个 HTTP 成功。
