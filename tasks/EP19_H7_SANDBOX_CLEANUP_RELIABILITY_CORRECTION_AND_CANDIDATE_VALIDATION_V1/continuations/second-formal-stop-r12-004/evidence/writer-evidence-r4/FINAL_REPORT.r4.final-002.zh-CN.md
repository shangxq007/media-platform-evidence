# r4 四项生产路径修正、真实资格与运行绑定报告

## 结论

本轮仅在新建 `implementation-r4/`、`fixtures-r4/`、`writer-evidence-r4/`、`private-r4/` 内完成 AR007、AR008、AR009、AR010 四项剩余缺陷。最终源绑定集成资格为 **139/139 PASS**；失败、错误、跳过、缺失、意外、重复和无效状态均为零；mandatory controls 为 54。运行 loader 为 **PASS**，精确绑定 `candidate-formal-002`。

未修改产品源码、产品测试、依赖版本或业务行为；未运行产品测试、shared preparation/probe/baseline/formal，未创建正式 namespace，正式预算仍为 1/2。未自签独立接受，也未发布证据。

## 固定身份

- candidate：`a29864343ed4f630b052c20d86c23b240f13cfd0`
- tree：`fd37409d0274662abbe86f69e3d963c05b379696`
- immediate parent：`689ab9456461a8d19a72d059f5157092efc43aff`
- patch SHA-256：`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`
- matrix SHA-256：`57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`
- runtime binding SHA-256：`56b21d7689daad6c34ce76eccb3c6a4884a0a7c3fe81ed2180239b3c0fdb9383`

## 四项关闭

- AR010：`strict_baseline` 明确持有 Watch，只有成功返回时移交；所有捕获、边界、toolchain、seal、证据或返回前失败均关闭。原始失败与 cleanup 失败以 `BaseExceptionGroup` 同时保存。真实 r3 replay 显示 fd 5 泄漏；r4 fd 集合前后相等。
- AR007：实际链 `runner -> freshness -> parsers.py -> vite_closure.py -> vite_closure.mjs` 已进入强制图。辅助进程直接使用的 `acorn`、`postcss`、`postcss-value-parser`、`parse5` 及可达传递依赖共 8 个包，均绑定固定 source root、version、package.json SHA-256、完整文件 SHA-256 和依赖边。缺节点或边的同 schema 图均拒绝；不声称覆盖任意未来 plugin。
- AR008：native invocation/exit、product assertion、observer preservation、timeout/cancellation、wrapper/environment、evidence persistence、cleanup 分维保存。实际保护拒绝及超时均由外层 observer 终止子进程并保留原因，非零 exit 不再单独推导产品失败；复合原因不相互覆盖。
- AR009：cleanup preimage 文件与父目录先 durable，再复核原件身份/摘要，之后 unlink 并同步原目录。Vite helper native log 在成功或失败均走 durable stream，成功结果在读取前同步。runner 失败路径写入 durable failure detail 并建立独立 immutable seal，不再因 result=FAIL 跳过。

## 来源与历史限制

`red-predecessor-003` 是针对未修改 r3 的新 task-private replay，运行前后均记录实际 executor/test/dependency hashes、argv、cwd、PID、开始/结束、native/wrapper exit、结果 receipt linkage、control IDs 和原生日志；不是对旧 focused receipts 的追认。旧 receipts 缺 tested-source hash 的限制继续为 `NOT_ESTABLISHED`，从未回填。`red-predecessor-001` 的 fixture config 错误和 `qualification-001` 的两个集成回归失败均原样保留。

最终 focused 为 5/5 PASS，最终 integrated 为 139/139 PASS。完整矩阵见 `CONFORMANCE_MATRIX.r4.final-002.json`；parent 命令见 `PARENT_HANDOFF_COMMANDS.r4.final-002.md`。
