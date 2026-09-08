# Sandbox 清理可靠性修正：当前阻断报告

TASK=EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1
LANE=BACKEND

## 1. 结论与决定

**结论 B：已形成有针对性回归支持的本地修正候选，但正式验证在产品门禁前被保全 baseline 拒绝。任务暂停，未完成交付闭环。**

这不是 sandbox 修正后的正式回归失败，也不是正式通过。第一次尝试已消费；不能重用 namespace，不能直接继续下游 gate，不能为了等待安静窗口原样重跑。第二次尝试仅有预算上限，不自动具备重试资格。尚须核对原 Owner 授权的具体第二次使用条件；本报告不新增执行授权。

## 2. 候选身份与范围

- 修正候选：`a29864343ed4f630b052c20d86c23b240f13cfd0`
- Tree：`fd37409d0274662abbe86f69e3d963c05b379696`
- 直接父提交／原候选：`689ab9456461a8d19a72d059f5157092efc43aff`
- canonical 比较基线：`86d6aef94fd5e58da552e97c11473cff6eca734e`
- 仅本地候选；未合并、未推送产品。最近失败后核验 checkout 干净，报告编写时重新读取的提交身份一致。

相对直接父提交仅五个路径：

```text
sandbox-isolation-module/src/main/java/com/example/platform/sandbox/LocalBoundedProcessLauncher.java
sandbox-isolation-module/src/main/java/com/example/platform/sandbox/BubblewrapSandboxProcessLauncher.java
sandbox-isolation-module/src/main/java/com/example/platform/sandbox/ContainerSandboxProcessLauncher.java
sandbox-isolation-module/src/test/java/com/example/platform/sandbox/CleanupFailurePropagationTest.java
sandbox-isolation-module/src/test/java/com/example/platform/sandbox/CleanupReliabilityTest.java
```

## 3. 修复了什么，以及证明的边界

1. **Local 清理与主失败保留**：等待自有 Process 根退出；终止、枚举或观察出错后仍尝试独立清理；保留操作错误，分别保留主执行失败与清理失败。
2. **Bubblewrap 聚合丢失错误**：不再仅凭空 survivor 集合重新计算成功并抹掉下层清理失败。
3. **Container 两次清理丢失错误**：保留前后两次操作错误，继续遵守 named-container/detached-helper 原有语义。
4. **已退出保留句柄的身份判断**：保留对象已确认退出时，不再要求退出后可能消失的 live Info；仍存活但身份未知、冲突句柄、权限或观察错误仍失败关闭。

上述结论有源码、确定性 RED 与行为测试支持，不等同于证明历史唯一根因。观测补丁与产品候选分开；未用适配后的诊断 Main 冒充原 JUnit。未修改原有 grace/timeout、原集成测试接受断言或 H7 的33条规则；本次正式 H7 gate 尚未执行，因此不宣称正式门禁已证明这一点。

## 4. 实际完成的验证

| 验证 | 实际结果 | 限制 |
|---|---|---|
| 最终合成 JUnit | 34通过，0失败、0错误、0跳过 | 受控替身调用真实实现，不是OS稳定性证明 |
| 聚焦及共享调用者回归 | 4通过，0失败、0错误、0跳过 | 包括两后端原集成方法及现有调用者测试 |
| 最终版本稳定性 | 五轮，每轮两个原集成方法通过；共10次JUnit执行 | 两后端 timeout/cancellation/正常场景随完整方法各执行五轮，不是概率可靠性证明 |
| 新增身份 Gradle 验证 | 27通过，0失败、0错误、0跳过 | 仅新增类，不是完整后端套件 |
| 新鲜原生身份/分类生产者 | 两项native exit 0，原生回执绑定源码、argv和输出 | 为新版绑定取得完整回执；不重复真实timeout诊断或稳定性 |
| 实际候选外部绑定 | 通过 | 历史错误回执保留 |
| 候选绑定合成资格 | 158控制通过，13项独立封包检查通过 | 不代表产品门禁通过 |
| 隔离副本/Lean准备 | 通过；准备复核与端点检查通过 | PREPARED_NOT_BASELINED |

完整后端**期望**身份为8000，保留原29个预期skip。这是原接受身份加27个已测新增身份的预期集合，不是实际全套测试结果。报告编写时重新解析了上述合成、聚焦、五轮稳定性和新增身份XML；见 `candidate-preparation/STATUS_REPORT_XML_ACCOUNTING.json`。

## 5. 第一次正式尝试为何停止

Run：`candidate-formal-001`。

- launcher native=1，baseline native=1。
- 拒绝原因：`BASELINE_OBSERVATION_REJECT`。
- baseline 子进程实测耗时：81.978729828秒；不是整个任务工时。
- Collector记录COMPLETE，捕获75627个文件，采集错误0、observer错误0。
- 观察到3条 `REJECT_INSTRUCTION_EVENT`：`.curator_ledger.jsonl` 的两条事件及 `.usage.json.lock` 的一条事件。**writer=NOT_ESTABLISHED**；不凭文件名推定由哪个服务或用户产生。
- `.usage.json` 的policy与collector记录摘要不同，inode、mtime、ctime不同。此差异来自本次真实捕获值，不是事后重新采样；程序在观察拒绝处先停止，未到绑定谓词或后续V2评估。
- LAUNCHER_ATTEMPT和BASELINE_ATTEMPT已存在；accepted baseline、seal、preflight、START均未建立或运行。

**本次门禁账：29 required / 0 PASS / 0 failed product gate / 29 NOT_RUN。**

历史正式 run `baseline-sequence-formal-001` 的 **29 required / 9 PASS / 1 FAIL / 19 NOT_RUN** 保留；其 RUNTIME_PREFLIGHT 清理断言失败未被覆盖。新旧两次失败位于不同层，不能合并或互相抵消。

## 6. 预算与未决事项

- 本任务专门真实诊断：1/8；native2，诊断错误保留，不计成功复现。旧任务已消费的一次带观测未复现另行保留。
- 产品行为修复迭代：3/3，预算已满，不能再修改产品行为。
- 最终稳定性：五轮已完成，不重复执行。
- 正式尝试：1/2，第一次namespace永久消费；第二次未启动。
- acc2额度耗尽、编译依赖缺失、中间RED、绑定拒绝等过程失败均保留，未用最终成功覆盖。

**唯一最小下一步：核对原授权中第二次正式尝试的具体使用条件，并就本次baseline保全拒绝形成有依据的处置决定。** 当前没有证明安静窗口可获得，也没有证明应豁免这些事件；不得删弱规则、忽略变化、暂停服务或修改运行时配置来暗中推进。

## 7. 保全、依赖与交付限制

定向依赖复核发现历史8份Hermes源码4同4变，支持固定输入/窗口内不动态选择的有条件纪律，不是全局无语义或完整运行时不变证明。原报告条件结论保留；父层将证据绑定进 `formal-tooling/dependency/DEPENDENCY_CHECK.json`，执行器身份和准备处置验证通过，之后才启动第一次尝试。

baseline拒绝说明本次不能宣称完整保全PASS；未证明所有外部写者不存在。控制进程已退出，但尚未交付完整task teardown结论。前端开发lane未被本任务修改，不以此代替宿主全范围无变化证明。

本报告是**当前阶段本地报告**，不是最终验收报告。新任务证据尚未发布，未取得新evidence commit、公开manifest或匿名固定提交逐文件核验结果；不提供旧任务URL冒充本次交付。

```text
STATUS=BLOCKED_BEFORE_GRAPH
INDEPENDENT_REVIEW=REQUIRED
EP19_CLOSED=NO_PENDING_INDEPENDENT_REVIEW
PRODUCT_PUBLICATION=NOT_PERFORMED
POST_PUBLICATION_SANITY=NOT_RUN
EVIDENCE_DELIVERY_STATUS=LOCAL_STATUS_REPORT_ONLY_NOT_PUBLISHED
```

## 8. 关键证据（相对此任务根）

- `PRODUCT_CORRECTION_001_REPORT.md`：writer阶段报告，里面“无新提交/无真实运行”的说法只适用该历史阶段，已被后续候选与回归补充，未改写原文。
- `CORRECTION_BUDGET_RECONCILIATION.json`：3次产品迭代对账。
- `runtime-regression/`：聚焦、稳定性、新增身份的原生结果及XML。
- `formal-tooling/REAL_BINDING_RESULT.md`：真实绑定及新鲜/复用资格。
- `candidate-preparation/dependency-current-001/DEPENDENCY_CURRENT_REPORT.zh-CN.md`：定向依赖报告。
- `candidate-preparation/FORMAL_ATTEMPT_001_FAILURE_RECONCILIATION.json`：本次失败对账。
- `formal-tooling/parent-logs/candidate-formal-once-001.native.log`：launcher原生日志。
- `formal-tooling/outputs/continuation-runs/candidate-formal-001/runtime/orchestration/baseline.native.log`：baseline原生日志。

私有捕获全图与Skill/Memory正文不包含在本报告内。编写本报告只进行了证据读取、Git只读身份查询及任务内报告写入；未重跑测试或formal，未直接写Skill/Memory正文。
