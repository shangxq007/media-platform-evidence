# r3 生产路径符合性修正与绑定报告

## 结论

本轮在 Owner 既有授权和 `REPAIR_R3_PACKET.md` 限定范围内完成六项剩余生产路径修正。AR001、AR002、AR007、AR008、AR009、AR010 均有真实 r2 前驱行为 RED、r3 GREEN、受影响回归、集成资格和最终 loader/binding 对账。AR003、AR004、AR005、AR006 的既有有效修正保持通过。

本结论是工程符合性和 parent handoff，不是实现者自签独立接受。未执行产品测试、shared probe/preparation/baseline/formal，未创建 `candidate-formal-002` namespace；正式预算仍为 1/2。

## 固定身份与范围

- candidate：`a29864343ed4f630b052c20d86c23b240f13cfd0`
- tree：`fd37409d0274662abbe86f69e3d963c05b379696`
- immediate parent：`689ab9456461a8d19a72d059f5157092efc43aff`
- patch SHA-256：`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`
- 29-gate matrix SHA-256：`57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`
- checkout tracked status：空；builder 已只读核验 SHA/tree/parent/patch。
- 仅新增/修改 `implementation-r3/`、`fixtures-r3/`、`writer-evidence-r3/`、`private-r3/`；r2 与历史未覆盖。
- `private-r3/` 为 0700；两份私有输入为 0600，正文未写入公开报告。

## 六项处置

完整当前源码 call graph、path coverage、RED 原因、GREEN 和证据路径见 `CONFORMANCE_MATRIX.r3.final.json`。

- AR001：SEAL capture 和最终 identity 后，先声明统一 cutoff，再受控移除 watch 并排空 cutoff 前已排队事件，最后 close。先前在最后 drain 与 identity/close 间写入 Memory 的事件现在进入最终 durable decision 并拒绝；不声称 cutoff 后继续观察。
- AR002：production `observer_seed` 保持 applicability 的 package-only 形状；rebind 精确比较 root、paths 和 `name -> package` 投影，同时要求正式 policy 的 manifest enrichment。真实 helper seed → rebind → 0600 visible temp → cookie 配对 rename 正控通过，负边界回归保持。
- AR007：dependency schema v4 绑定当前 9 个实际 source nodes、结构化执行边、当前 rewritten command/helper edges 和实际 `vite_resolution.mjs -> vite.resolveConfig` 边；不扩展为任意未来 plugin 证明。mandatory loader 要求 Python、`-B`、程序、flag 顺序和值、output/fixture/log/process/result 路径完全相等，并继续逐身份对账原生日志与 receipts。
- AR008：实际 `runner.run_gate` 捕获的 binding/capture/evidence FAIL 在 driver 返回后立即分类并永久 latch adapter，任何 `COMMAND_AFTER/COMMAND/GATE` 接受边界之前停止；native nonzero 与 integrity/environment 分类保留。
- AR009：实际 gate namespace、XML、native log、probe args、sealed immutable copies 统一走 durable helpers；文件 fsync、直接父目录以及新建目录发布父链均在 PASS 前完成。BOOTJAR 独立副本和既有语义检查未弱化。
- AR010：实际 native command-end identity stat 复用 guarded validator；BoundaryObserver fd 后 inventory 全部进入 cleanup 区；inotify init、metadata root/parent acquisition 受 deadline guard；ChildScope close 异常也不再阻止 watcher close。延迟 stat 在共享边界限额内拒绝，constructor inventory 故障 fd 前后对账相等。

## RED / GREEN / 集成资格

- 有效 predecessor RED：`writer-evidence-r3/red-predecessor-004/`，native exit 1，8 个控制中 7 FAIL + 1 ERROR。该 ERROR 是预期生产异常 `OBSERVER_POLICY_BINDING_MISMATCH eligible_map`；其余分别证明被遗漏行为错误接受或资源/时限/持久性断言失败。原生日志 SHA-256 `63c10d1bc29da006455424fe9cb91bc985d526e18552b0bbef6d7336a16afae6`，0.774296799 秒。
- focused GREEN：`writer-evidence-r3/green-focused-002/`，8/8 PASS，native exit 0，日志 SHA-256 `9db81cc27205b128db1e684693501b19415420c4b5912367ac5f0694c54caabb`，0.613459103 秒。
- 最终 integrated qualification：`writer-evidence-r3/qualification-004/`，134 expected / 134 executed / 134 PASS；0 FAIL、0 ERROR、0 SKIP、0 missing、0 unexpected、0 actual duplicate、0 expected duplicate、0 invalid status；49 mandatory affected controls；native exit 0；18.61047679 秒；日志 SHA-256 `1821f6c780b576c59e13ff9dac72c35f9aa4caf3d75cc97dd50eb26078473de1`。
- qualification SHA-256：`62caa2c0fdd3e7dd0b51b13ff1ab45edab333dcfa674007e6bd3765d271c65f4`。
- r2 历史 126 PASS 未作为 fresh 结果复用；本轮 fresh 总数为 134。

较早 `red-predecessor-001/002/003` 和 `qualification-001` 是保留的独立调试迭代，未覆盖、未冒充最终证据。`qualification-002/003` 是后续通过迭代，但最终绑定仅引用代码最后变化后的 `qualification-004`。

## 来源、依赖与运行绑定

- 当前 source/path matrix：`CONFORMANCE_MATRIX.r3.final.json`，SHA-256 `ed3a631d3a29ec97d27d6dce3705a05ab5ae2fd1129155bd6fe2a96d11230ebb`。
- r2→r3 patch：`IMPLEMENTATION.r2-to-r3.final.patch`；初始复制 hash stream 精确一致，最终 source manifest 共 108 项。
- delta review：`IMPLEMENTATION_DELTA_REVIEW.r3.final.json`，SHA-256 `e9523c6c6e8d2ae47493a2fb450819c1b534902c50934f06a229310748a14f6f`。
- current fixed29 consumer binding：`INPUT_FIXED29_CONSUMER_BINDING.r3.final-002.json`，SHA-256 `1126bbc5487894cc420dff1f94c6e581149dc0fe31afa6fb4a8c201538412919`。
- dependency binding：`DEPENDENCY_BINDING.r3.final-002.json`，SHA-256 `2ed075d86bc65683d90f902b4663187cee9186f16f09a9a8df341fadb80088d5`。
- 最终 runtime binding：`RUNTIME_BINDING.candidate-formal-002.r3.final.json`，SHA-256 `b4c7ffba65c6b3b070d767f45ad30c9d372adc24363f93bceb282e7ba597e51b`。
- mandatory runtime loader validation：PASS，source 108、qualification closure 6、精确 run ID `candidate-formal-002`，见 `RUNTIME_BINDING_VALIDATION.r3.final.json`（SHA-256 `5b7e340d09252cdaeacac5db785179f7702215346e6d6c95da86a8bebcd33eb7`）。

最终 binding 仅接受新 `writer-evidence-r3` 路径，已消除 r2 loader 路径硬编码。builder 和 loader 均使用实际 fixed candidate 只读核验，没有创建正式 namespace。

## 保留约束与交接

29 条命令、原生 timeout、H733、COMPILE freshness/completeness、checkout/output isolation、frontend asset closure、Git→resources→JAR、BOOTJAR immutable copy、Lean、wrappers/init 均未因本轮修改而弱化。8000/29 仍只是正式运行预期，不填作实际通过字段。Owner 已接受的 ledger capture 间 overwrite-restore/truncate-regrow 限制保持原边界，不扩展到其它 protected objects。

Parent 若独立 review 通过，只能使用 `PARENT_HANDOFF_COMMANDS.r3.md` 中绑定 SHA 和精确 run ID；本报告不授权第三次尝试、不替代独立最终接受或正式结果。
