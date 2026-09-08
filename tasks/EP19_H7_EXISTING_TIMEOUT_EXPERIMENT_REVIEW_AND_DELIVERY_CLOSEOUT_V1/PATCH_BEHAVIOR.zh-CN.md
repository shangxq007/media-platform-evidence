# 观测补丁行为影响审查

依据：原始源码六文件与固定 Git blob 字节相同；实验副本六文件与保存版本相同。`sources/instrumentation.patch:1–157` 为两个 launcher 的全部既有文件 diff；三个新 Java 类及 README 是实验入口/记录器，不是产品修复。

| 检查项 | 核对与分类 |
|---|---|
| workload | Main:91–102、timeline:1；仍为 /usr/bin/timeout 30 /usr/bin/sleep 30；参数未改 |
| launcher timeout | Main:93 为 250ms；原 deadline 公式未改，但 rootStarted 在 deadline 初始化前增加耗时，实际启动到 deadline 的时间不保证相同 |
| cancellation | Main:102 为 SandboxCancellation.never()，未改 |
| TERM/KILL | Local diff:122–156：保持 reverse-PID 后代 TERM→根 TERM→等待→存活后代 KILL→存活根 KILL→等待；不是按树深度；包装器每次调用原 API 一次，异常记录后重新抛出。实际这次仅 TERM，KILL 未触发 |
| grace/轮询 | Bubblewrap TERMINATION_GRACE=500ms；Local waitUntilDead 中 10ms；workload waitFor 20ms；原值未改。无独立 wait 区间日志，不能虚构精确等待耗时 |
| 枚举 | 原 process.descendants()、map、reverse-PID sort 未改；其后同步注册所有原 handles，增加时间成本 |
| survivor | 原过滤、根 isAlive 与采样控制流位置（两次 wait 后、capture join 前）未改；但原采样前插入 snapshotAll，改变实际采样时刻。不能声称采样时刻无变动 |
| capture | 初始 join 250/250、显式 stdout/stderr close、条件 join 750/750、&/|| 仍在；try-with-resources 增加 marker，marker.close 在 input.close 前执行；额外编码/同步会扰动线程完成时刻。IOException 原吞并语义保留，新增计数；未验证所有记录器异常路径的无影响性 |
| primaryFailure | 原 selectResultFailure 公式未改；PROCESS_TIMEOUT 在清理前/返回前/最终 result 均保留 |
| cleanup.completed | processReaped && workloadContained && capturesComplete 未改；processReaped 仅由根 PID 不在原 survivors 推导，不是直接 waitpid 证明 |
| 入口接受条件 | timeout、completed、failure 空、survivors 空的 conjunction 保留；原测试 ProcessHandle.of(pid) 重查换成 recorder 的自有根 handle。严格接受观测机制不同，PID 复用边界未验证，不应将 combinedPass 称为原 JUnit 通过 |
| 其他场景 | Main 只有一个 launchResolved；没有 detect/探针、整个原测试、cancellation、正常退出或 neutral-boundary 场景；controller 不含 retry，attempt 与启动记录各一个 |
| 独立收尾 | 返回后约 200ms、独立 teardown 可对匹配身份做有界强制终止，但这次 actions 全 none；自有根 waitFor=true。其结果不参与原 cleanup |

## native exit=0 的准确范围

Main:109–110 的适配 conjunction=true；Main:194 要求 diagnosticFailure==null、recorder 存在且 failed()==false。Recorder.failed 只覆盖 errors、dropped events/identities、proc errors/truncations；**不检查 unresolvedRisk**，也不能单独把所有 capture 统计类别均称为 exit 门禁（本次实际统计为 0）。独立收尾未消除身份分类缺口仍可 exit 0。这不是正式 Gradle/JUnit 或资格验证。

## 结论与扰动

分类：`CLEANUP_DECISIONS_PRESERVED_TIMING_PERTURBED_ROOT_ASSERTION_ADAPTED`。
未发现原清理算法、终止先后或公式的修复；但严格场景等价未建立，特别是根接受观测变化与同步采样时延。观测代码分配对象、读取 proc、同步编码、异步 fsync journal、时钟测量和 capture marker 都可能改变调度。root 注册实测区间 4.564911ms，枚举记录区间 36.545927ms；后者包含原枚举成本，不能全归因于补丁。一次 instrumented 结果不能外推未加补丁候选。
