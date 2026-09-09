# external29 实际集成与定向资格结果

结论：缺失的 actual29 driver 已在全新 `integration-001` 中完成。它复用并封存原有 29 门执行图及其输出隔离、COMPILE 新鲜度/完整性、前端候选资产闭包、materialized Lean、Git→Gradle resources→JAR 映射和原生门接受逻辑；同时把一个长生命周期的 V3 `BoundaryObserver`、`Engine`、`RunAdapter` 接到 baseline、preflight、prestart、每条 command 前后、gate、final、coverage、seal。

正式入口只有 `external29_driver.py formal`。该入口先以 O_EXCL+fsync 写入唯一 `FORMAL_ATTEMPT.json`，再注册 observer、构建真实 private policy、建立 baseline，并顺序进入 preflight/prestart/29 图。没有可独立调用的 baseline 或 preflight 子命令，因此不能产生 orphan policy/baseline，也不能把失败 namespace 复活。任一失败保留失败层、原生日志和完整 29 项 PASS/FAIL/NOT_RUN 对账，不调度后续门、不重建 baseline、不提供第三次入口。

V3 与旧保护的衔接是窄委托：legacy native observer 只把 exact usage/lock/ledger 及精确 usage temp 事件交给连续 V3 observer；其他 instruction、Memory、source、Owner、config、executor、matrix、binding、qualification、candidate 和运行工具仍走原 strict inventory、endpoint capture、command-native observer 和 seal。Ledger 依赖仍为 `OBSERVATION_INTEGRITY_ONLY`，不参与授权、指令/skill、候选、gate policy 或 rollback 选择。

当前 fresh qualification 为 `qualification-005`：87 tests、87 unique、0 duplicate、0 failure、0 error、0 skip，native exit 0。它重新执行了原 71 个 V3 affected controls，并新增 16 个 driver controls。真实 disposable FS/inotify 控制证明：合法 usage+空 lock+ledger 变化可贯穿 29 个 trivial fixture gates；strict package 写在第 1 门后拒绝且只调度 1 门、其余 28 NOT_RUN；watch loss、capture failure 在 dispatch 前拒绝；另核对 exact29 matrix、真实 command 数组、wrapper/init 存在及缺失拒绝、单 marker 顺序、无独立 baseline/preflight、8000/29 期望保留。所有 fixture 明示 `formal_attempt=false`、`product_gate_execution=false`。

历史 `green-009`、旧 158/13、旧 H7 33 和 `candidate-formal-001` 未修改。71 个 affected controls 在当前集成源码上已 fresh 重跑；旧 158/13 仅对 89 个 byte-identical copied inputs 和未变化的 gate implementation 作适用性引用，不被重标为 fresh。五个资格迭代全部保留，`qualification-005` 是加入 wrapper/init 缺失拒绝后的当前最终源码绿色。旧 runtime bindings/identity 也作为 stale 历史保留，当前只使用 `RUNTIME_BINDING_LAUNCH_READY.json`。

实际只读候选绑定 CLI 已对 checkout 成功：SHA `a29864343ed4f630b052c20d86c23b240f13cfd0`，tree `fd37409d0274662abbe86f69e3d963c05b379696`，patch SHA256 `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`，tracked status 无输出，29 门且 101 个 integration source/input 文件绑定；binding reload 与实际 runner import 均 PASS。Executor identity 为 `806d9fe2ee59c4cc7a7d142bb0f0a12f6d56d1c402f27c978c4b3df280312e78`。

本次没有运行 product tests、shared preparation、endpoint probes、Gradle、native product gate、baseline、preflight 或 formal attempt。正式预算仍为已用 1/2、剩余 1。新 run namespace 尚未创建；`candidate-formal-001` 原失败现场不变。Parent 的现成命令在 `PARENT_COMMANDS.md`，所需的两个 parent 实际 attestation 输入及精确 schema 在 `INPUTS_NEEDED.json`。它们是实现复核/指令预加载事实，不是新的 Owner 批准请求。

Ledger 的已接受限制不变：覆盖 capture 之间完成的 overwrite-restore 或 truncate-regrow 不可由普通 inotify+endpoint prefix 证明检测；actor 不证明 writer。没有伪造此类检测能力。

最终状态：`INDEPENDENT_REVIEW=REQUIRED`，`EP19_CLOSED=NO_PENDING_INDEPENDENT_REVIEW`，`PRODUCT_PUBLICATION=NOT_PERFORMED`，`POST_PUBLICATION_SANITY=NOT_RUN`。完整机器字段见 `INTEGRATION_RESULT.json`。
