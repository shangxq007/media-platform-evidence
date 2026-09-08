# EP19 H7 timeout 清理单次隔离诊断报告

## 决定

**NOT_REPRODUCED_IN_ONE_INSTRUMENTED_ATTEMPT；历史唯一根因仍 INCONCLUSIVE。**

本次已真实执行一次带观测补丁的独立副本，Java native exit=0。原超时主失败为 PROCESS_TIMEOUT；cleanup.completed=true、survivors=[]、captureStreamsClosed=true。不得据此认定产品缺陷已修复、历史失败是误报或固定候选可正式验收。

实验 ID：ep19-h7-timeout-diagnostic-001。额度已消费 1 次，无自动重试。正式门禁重跑 0，新正式尝试 0。独立评审 REQUIRED，EP19 未关闭。

## 身份、路径与恢复来源

- 固定 candidate：689ab9456461a8d19a72d059f5157092efc43aff；base：86d6aef94fd5e58da552e97c11473cff6eca734e；tree：6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6。
- 历史根目录：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/baseline-sequence-20260908T070258Z`。
- 历史 backend 源码根目录：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/baseline-sequence-20260908T070258Z/outputs/continuation-runs/baseline-sequence-formal-001/sources/backend`。
- 独立实验副本：`/home/user/Documents/workspace/audit-runs/EP19_H7_TIMEOUT_CLEANUP_ISOLATED_DIAGNOSTIC_EXPERIMENT_V1/candidate`。
- 本次证据根目录：`/home/user/Documents/workspace/audit-runs/EP19_H7_TIMEOUT_CLEANUP_ISOLATED_DIAGNOSTIC_EXPERIMENT_V1/evidence`。
- 实验完整内容身份 SHA-256：`727188350f96bce9843426fd98f21661dc997de0f0b74052314b7f16944d38d5`。这是完整 path/mode/文件 SHA256 清单的摘要，不是新的 Git commit/tree。
- 观测 patch SHA-256：`41897cf4ca6463168be38ccaa800b9bb6fd8827b2170dc02cb9acf7eab77aa8d`。

独立 clone 使用 --no-hardlinks，未复用或修改历史 checkout。最初 7634 项 Git 文件对象逐一匹配；实验只修改两个 launcher 文件，另增三个 diagnostic Java 文件和一份 README。不是“全部源码改动 0”。产品正式候选、canonical 与前端开发工作区本任务改动均为 0。实验末尾历史 checkout 7634 文件字节未变，实验固定输入未变，反向 patch --check 退出 0。

旧包 manifest SHA256 为 ef0b0920fc8448dde7060bbd04d5583f629d7f79906a5dccfeaf10384fcb8424，归档 SHA256 为 9e6c0541a41094bc04da2be13de6450ccb4ad228a17623b9d41e87f1a0a7aa6f，均新鲜复核一致。176 项 manifest 文件、177 个归档普通文件成员逐字节匹配。baseline/seal/START 等七份私有记录只读摘要绑定，START→launch、launch→seal/preflight 关联匹配。没有运行原 collector，也不将读取记录当作新正式验证。

`PRIOR_INLINE_DIAGNOSIS.zh-CN.md` 是本次首次将上一对话交付正文转录落盘；不是伪造的旧文件。时间、正文摘要、转录局限与重新核对范围见 `PRIOR_DIAGNOSIS_PROVENANCE.json`。原正文中的历史语气和路径缩写原样保留，真实完整源码路径见 `original-source-identities.json`。未取得可作逐字节比较的历史聊天数据库导出，因此转录来源是可见对话，不升级为数据库归档证明。

已完整读取 `/home/user/Documents/03-大模型上下文-精简版.md`；仅作决策上下文，不作实现/测试证明。

## 历史事实：没有改变

历史 SOURCE_RUN_ID=baseline-sequence-formal-001，29 门中 9 PASS / 1 FAIL / 19 NOT_RUN。失败门 RUNTIME_PREFLIGHT native=1、wrapper=1，3 项测试执行，2 通过、1 失败。

原 `sandbox-isolation-module/src/test/java/com/example/platform/sandbox/BubblewrapSandboxProcessLauncherIntegrationTest.java:125–129` 执行 timeout 场景，第128行超时断言通过，第129行进入清理断言；第210行 completed 断言失败。原 XML 第5–8行记录 survivors=[489968]、enginePid=489967、engineClientReaped=true、workloadProcessesContained=false、captureStreamsClosed=true、descendantsObserved=3。历史 PID 只作为证据字段，未读取当前同号 PID 或发信号。

## 实验准备和实际调用链

Codex 是观测源码 writer，Hermes 作控制、编译、差异核对和真实执行。使用 codex-router 显式 gpt-6-astra，路由最小回应 ROUTE_OK；未读取凭据正文。首次 PTY writer 因 PATH 未找到 codex-router 未启动 executor，保留日志；随后用安装绝对路径启动成功。这不是绕过工具拒绝。

使用 /usr/bin/javac 25 编译本模块全部 main Java 与三个新入口/辅助类，退出0，产生76个新 class 文件。外部依赖仅复制 spring-modulith-api 2.0.4，摘要绑定；没有共享历史可变 class/JAR 输出，不运行 Gradle。首次将 javac 解析为包装器真实路径造成 getopt 退出255；纠正调用路径后编译通过。两次均是编译准备，不是实验次数。

`TimeoutCleanupDiagnosticMain.java:91–102` 构造与原 timeout 相同 requirement 并唯一一次调用 launchResolved：

`TimeoutCleanupDiagnosticMain → BubblewrapSandboxProcessLauncher.launchResolved → launch → BubblewrapProcess.start → LocalBoundedProcessLauncher.terminateTreeWithHandles → closeAndJoinCaptures → cleanupObservation → SandboxExecutionResult`。

- workload：/usr/bin/timeout 30 /usr/bin/sleep 30；timeout=250ms；cancellation=never；环境 Map.of()；capture=1024。
- 不调用 detector、不执行其 /usr/bin/env probe；显式以 detector 原十项 capability 集合构造 diagnostic-declarative-not-probed 元数据，不冒充新鲜能力证明。
- 不执行原整套测试方法、cancellation、正常退出或 neutral-boundary 场景。
- 保留 TERM→父 TERM→第一等待→存活后代 KILL→存活父 KILL→第二等待→原 survivor 采样的顺序、500ms grace 与10ms轮询；本次原 KILL 分支实际未调用。
- 原 completed 计算、primaryFailure 选择、survivor 过滤/位置、capture join/close 表达式未改变。
- 入口的原接受条件 conjunction 保留。根进程判定使用保留的自有 ProcessHandle，替代测试的数字 PID 重查，以遵守不得观察 PID 复用对象的限制；不声称两者在 PID 复用下行为完全相同。

`EXPERIMENT_PLAN.json` 固定精确命令、干净显式环境、127项源码/class/依赖/controller输入摘要和45秒外层上限。`run_once.py` 在 Java 启动前独占创建并 fsync owner-attempt-consumed，Java 再独占创建 diagnostic-started。不存在自动 retry 路径。

## 本次观察：时间线与证据定位

原始时间线 `runtime/timeline.jsonl` 共70行，含68个事件和2行状态。4个身份均 journal 落盘；event/identity 丢弃、proc解析错误、截断、capture错误和记录器错误计数均为0。完整字段见 `runtime/result.json`，不是以下摘要的替代品。

| 原始位置 | 观察 |
|---|---|
| timeline:3、10–12 | 注册 bwrap 529945 → bwrap 529946 → timeout 529948 → sleep 529949 父子链；初始均 S，保存 startTicks、startInstant、raw stat/状态子集 |
| timeline:5–6 | timeout 被识别，清理前 primaryFailure=PROCESS_TIMEOUT |
| timeline:9 | 原 process.descendants 枚举捕获3个后代 |
| timeline:15–16 | sleep 529949 的 ProcessHandle.destroy 返回 true，未抛异常 |
| timeline:18、20 | sleep 与 timeout 的信号邻近采样被记录为 identity_mismatch；不足以证明数字 PID 已复用 |
| timeline:21–22 | timeout 529948 的 ProcessHandle.destroy 返回 false，未抛异常 |
| timeline:30–32 | namespace bwrap 529946 在采样中为 R，destroy 返回 true |
| timeline:34–38 | 529946 proc入口消失；根 bwrap 的保留句柄已判不活，随后仍按原算法调用 Process.destroy，返回 void |
| timeline:43–44 | 原 survivor 扫描产生 actualSurvivors=[] |
| timeline:48–56 | 两次初始 join 与两次显式 close完成，capturesComplete=true |
| timeline:57–59 | PROCESS_TIMEOUT 保留，最终 cleanup.completed=true，无cleanup failure，workload exit=143 |
| timeline:61、65 | 返回后即时及约200ms补充观察：保留的4个句柄均 isAlive=false；身份已退休的对象不再读取数字 proc路径 |
| timeline:66–69 | 独立收尾；0个附加信号，实际自有根 Process.waitFor 返回true，但 unresolvedRisk=true 原样保留 |

实测控制器启动到结束 770.615475ms；launcher observation elapsed=352.972288ms；已记录 cleanup.full 区间58.806965ms；独立收尾区间2.128583ms。它们是不同测量范围，不能混作单一清理时间。root注册区间4.564911ms，原后代枚举区间36.545927ms；这些观察值不支持“观测零扰动”。

## 推断、替代解释与缺失项

A. **实际运行的后代幸存者**：本次原扫描没有 survivor；不能验证历史489968当时是否仍执行workload。

B. **退出/回收竞争或僵尸**：信号邻近身份变得不可验证、后续句柄不存活，与退出竞争相容；没有已确认的Z状态，本次不证明僵尸解释。观察不到对象也不证明由本方回收后代。

C. **信号失败/权限问题**：一个 destroy=false 是已记录事实，但缺少errno/系统调用证据，且调用前身份已失去可核验性、随后句柄不存活。不能仅凭false归因于权限；true也不能直接当作终止完成。

D. **树变化/重父化/顺序**：原父子链被捕获。身份退休后没有新的可靠PPID时间线；未改变终止顺序做对照，无法确定顺序的因果作用。

E. **capture前快照过早**：本次扫描在capture前已经为空，不存在“非空旧survivor后续消失”的本次复现；历史解释仍未排除。

F. **未复现与证据不足**：本次明确未复现历史清理失败。日志保留计数完整不等于状态证据完整；记录器 `TimeoutDiagnosticRecorder.java:176–200` 将startInstant消失或跨读取不一致归为unknown/identity_mismatch并退休。当前输出未保留每个失败比较的左右值，因此不能细分为PID复用、进程退出还是其他身份信息变化。不得据此修订原结果，更不得自动重跑补证。

## 收尾与风险

`runtime/teardown.json` 保留了4个对象的准确PID/startTicks/startInstant和未重采样理由。所有保留句柄最后均为false；根Process.waitFor=true仅证明自有根等待完成，不证明本方waitpid了后代。因为unknown/identity_mismatch尚未解决，unresolvedRisk仍为true。没有可确认仍运行且需本次追加发信号的对象；没有再用数字PID查找或批量终止。若独立评审要求进一步检查，必须绑定这些启动身份，不能仅凭PID或名称操作。

## 最小下一步，不实施产品 correction

先独立只读评审本包，重点确认观测对时序影响、身份退休分支和未复现结论。最小缺失项是身份核验失败时各阶段startInstant/startTicks比较值及准确“进程消失/不可取得/不一致”分类；若要新增这些观测并重新运行，须另行授权新的有界实验，当前额度已耗尽。

本次证据不足以指定产品行为修复。若将来证据支持修改LocalBoundedProcessLauncher共享清理，其影响不止Bubblewrap：本地launcher、ContainerSandboxProcessLauncher、ContainerEngineProcess、BubblewrapProcess均调用该树清理。应新增覆盖退出/回收竞争、真实信号失败、重父化和capture时序的聚焦验证，并检查所有共享调用者。旧资格只能在新变化影响分析下复用未受影响部分；改动sandbox-isolation-module产品内容必然形成新产品身份，必须新候选及单独正式验证授权，不能声称原689ab945已包含修复。

## 权限、发布与交付边界

本地写入、编译和一次实验均有实际成功工具结果；没有修改审批策略。此前几轮停在状态说明是控制面执行失误，不归因于新的工具拒绝。

Owner已授权去掉原地址空格，匿名GitHub API确认 `https://github.com/shangxq007/media-platform-evidence` 存在且HTTP200。新明确的“重新提交”授权限定本地准备；此前远端认证的no-retry未取得独立恢复放行，因此未重新提交凭据操作、未push。这里不伪造“又被拒绝”，也不拿旧commit代替本次发布。远端Markdown/Raw/机器索引URL均尚未产生，仓库存在不是交付验证。

本包只追加本任务外部材料，不改变旧包原字节。机器字段见MACHINE_INDEX.json，最终manifest/归档摘要和完整最终字段见证据目录外的detached交付回执，避免自引用哈希循环。LOCAL_VERIFIED只表示本地包字节核验，不表示产品验收、唯一根因成立或后代回收证明完整。

未执行Skill/Memory写入。曾有只读工具stdout超限自动缓存，已在前次进度披露，非本任务证据交付。无前端分支验证/冻结/暂停要求；没有对并行开发正常变化设立全局保全要求。STOP：不得自动产品修复、第二次实验或正式门禁重跑。
