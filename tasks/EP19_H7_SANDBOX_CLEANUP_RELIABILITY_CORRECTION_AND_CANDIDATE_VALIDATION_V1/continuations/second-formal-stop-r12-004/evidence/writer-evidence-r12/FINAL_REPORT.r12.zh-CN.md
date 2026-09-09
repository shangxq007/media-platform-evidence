# r12 实际 preparation consumer 集成修正报告

## 结论

本轮在授权范围内完成。实际缺失 API 已由 `bc.exact_path` 修正，且 runtime binding 将产品身份 JSON 与外部实现 patch 分成两个强制字段。source-bound predecessor RED 精确复现 `AttributeError` 与 reason hash `97863e69…a790`；相同测试体和 wrapper 的 GREEN 通过。最终集成资格 179/179 PASS（94 mandatory），最终只读 loader 调用真实 `verify_object_source`/`identity_delta.validate` 后 PASS。

r11 readiness 的 loader PASS 仅证明 loader，未证明 real prepare seam；本报告作追加更正，不覆盖旧清单。r12 私有 CLI 控制真实经过 parser→modules→runner.prepare→verify_object_source→identity_delta.validate，并在预先存在的私有 sentinel 处停止，因此不声称完成 clone/Lean/container preparation。实际 parent preparation、endpoint、revalidate、disposition、baseline、formal 均未运行。

## 固定身份与分离 provenance

- candidate `a29864343ed4f630b052c20d86c23b240f13cfd0`；tree `fd37409d0274662abbe86f69e3d963c05b379696`；product patch `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`。
- product identity DELTA `TASK_ROOT/candidate-preparation/native-delta-001/DELTA.json`，SHA-256 `4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e`，27个历史实际 JUnit identity；只读消费，不重跑生产者，也不把历史结果称 fresh。
- external implementation delta `J/writer-evidence-r12/IMPLEMENTATION.r11-to-r12.final-003.patch`，SHA-256 `9f6b4a89ddb6e0a263992f921421005a98e476b1127b0c8be6a92026877c0621`；13个 r11→r12 字节差异。它只证明外部实现差异，不进入产品 JSON consumer。
- final binding `RUNTIME_BINDING.candidate-formal-002.r12.final-003.json`，SHA-256 `bb1a2592d4d5d0c39e10f8d3e7a04b368f531773f5f8f6736d27b02aaf1fbefe`；dependency `5bdc207141695de9ba4306114976a95e7ccf9aca63f143b36a6bb705568b3fde`；qualification `4938fd95c18897b40903a6d1edbda5a696b6c49a0351742a844ea43447a72521`。

## RED / GREEN 与负控

- RED：native 1 / wrapper 0，source snapshots stable；`AttributeError` reason hash与 parent 摘要相等；正式 namespace 未创建。
- GREEN：native 0 / wrapper 0；正确产品身份到达预存在 sentinel；external patch 误放 identity、错误 product schema、candidate identity、product hash、缺失字段与 config seal 均在任何新副作用前拒绝。
- 私有资格前置替代只做 sealed source check；没有替换 binding loader、runner.prepare、Git source verifier 或 identity validator，不是 Lean/container proof。

## AR 与保留边界

AR001..006、AR008..010 为 r11 精确处置的 fresh 179 regression；AR007 增加实际 prepare consumer、两类 delta provenance 和 v7 dependency edges 后闭合。AR005/006 未回归。native29/H733、原生 timeout、64MiB/128/1MiB/8MiB/4096/128/3次5秒/4096 pending 限额与 Owner 接受的 ledger 捕获间观察限制均未变。没有新增3600秒 attempt cap。

## 状态

PRODUCT_CHANGED_PATHS=[]；APPROVED_CONTRACT_CHANGED=NO；product budget=3/3；formal attempts=1/2。candidate-formal-002 仅绑定，真实 namespace不存在；29门仍0 PASS/0 FAIL/29 NOT_RUN；8000/29仍只为EXPECTED。INDEPENDENT_REVIEW=NOT_CLAIMED；EP19_CLOSED=NO；publication/sanity未执行。

Parent 应使用 `RUNTIME_BINDING.candidate-formal-002.r12.final-003.json` / `bb1a2592d4d5d0c39e10f8d3e7a04b368f531773f5f8f6736d27b02aaf1fbefe`，严格按 `PARENT_HANDOFF_COMMANDS.r12.final.md` 单步、回读、失败不重试。fixture manifest：2533项，SHA-256 `1915317569b74463e8c312a6480072d25b5066ca7384d29fefa19cc6214ceac9`。

## 限制与工具事实

一次删除本轮生成 `__pycache__` 的清理命令被工具明确拒绝，未重试；所有 source/delta/binding/qualification 枚举均显式排除 `__pycache__`，其存在不进入执行器身份。没有绕过工具拒绝。
