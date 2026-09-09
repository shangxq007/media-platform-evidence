# integration-review-002 / part-b

状态：COMPLETE；仅咨询性静态审查，非独立验收。路径相对于 integration-001。

## AR006 — RESOLVED

针对实际 formal 外层入口，旧 bundle 重放/缺省 coverage、strict、binding 的直接 caller 反例已被强制调用链隔离。

源证据：`tooling/executor/external29_driver.py:24-37,74-79,90-118,188-218,326-340`；`tooling/executor/binding_contract.py:28-61`；`tooling/executor/boundary.py:107-125`；`tooling/executor/bookkeeping_v3.py:202-232`

正式 CLI 不接受 bundle、coverage_complete 或 strict_input_integrity 参数；boundary 包装从实际 observer 获取事件/错误，固定证据目录，不传 bundle，Engine 因而调用 capture_bundle 的真实同源读取。baseline 的 strict=True 先经过实际 capture/watch rejection；后续调度前执行 strict_check。formal 必须先 modules→binding_contract.load，对精确 schema、固定候选/tree/patch、matrix、输入全集及当前 source_binding 逐项核对，再给 adapter 传 binding 和 expected 字段。不能因内层 fixture API 仍可注入就称这些参数在实际入口可由调用者制造 PASS。

限制：RESOLVED 仅指原 AR006 的实际外层 caller 输入绕过，不等于五条件已全面正确：strict 连续覆盖完整性属 AR001 范围，本 part 不裁决；资格/依赖语义来源仍见 AR007，证据持久性见 AR008/009。没有执行 CLI、capturer 或 formal。

## AR007 — OPEN

外层增加真实 qualification receipt/hash 检查与 runtime/source 绑定，但控制身份闭合及依赖/eligible 来源绑定仍不完整。

源证据：`tooling/qualification/build_runtime_binding.py:27-42`；`tooling/executor/binding_contract.py:34-60`；`tooling/executor/coverage.py:113-141`；`tooling/executor/boundary.py:70-87`；`tooling/executor/external29_driver.py:196-208`；`tooling/qualification/policy_builder.py:25-56`；`K/writer-evidence/DEPENDENCY_BINDING.json:6-7,30-41`

不能复用“只有 schema+PASS 即可正式启动”的旧反例：coverage.qualification_inputs 现在要求非空 dependencies、五类回执路径、hash 和 native/result 结果。但是它不对 result.controls 实際身份集合、unique、skipped 或必需 affected controls 对账，只比较总 tests 和若干汇总字段；无 control rows 的摘要仍不能被这些谓词识别。dependency 文件仅校验 role/禁用词列表和 truthy dynamic-reader；缺失 consumers/readers 默认空，未校验 sources 依赖闭包。formal 接收 applicability/private-map 路径，policy_builder 与它们当前提供的声明比 manifest 后仅记当前 hash，未把这些 hash 与已绑定 dependency.sources 中的预绑定清单hash闭合。由此仍未落实原 AR007 所要求的强制 provenance。实际现成 qualification-005 的87个唯一控制、0失败/错误/跳过、native_exit=0及直接依赖hash经本次静态核对一致；不指控这些现成回执伪造。

限制：现有87回执是实在的一致证据，不是本审查新执行或穷尽契约覆盖。没有读取共享usage/ledger、私有manifest正文或实际执行依赖来冒充完成运行时闭包；只是指出必经校验的来源缺口。

## AR008 — OPEN

外层停止后续门有改善，但证据异常仍不锁死 adapter，且接受状态先于持久证据推进。

源证据：`tooling/executor/boundary.py:185-196`；`tooling/executor/executor_adapter.py:85-103`；`tooling/executor/external29_driver.py:174-185,215-235`

Engine 在 write_evidence 前更新 session 和 previous_usage；异常绕过 RunAdapter 的 result!=PASS 分支。实际 driver 在图内捕获异常并置 stopped，禁止后续门，但返回后仍用同一个 adapter 调 FINAL/COVERAGE/SEAL。若某一次证据写入短暂失败、随后恢复，FINAL 可继续针对已经推进的 session 判定；图内异常不进入 formal 外层 setup 异常的 adapter.fail。总结果仍 FAIL，不会因此变成整体 PASS，也未发现正式 baseline 重建路径。

限制：确定性源码推理，未注入 IO 故障；不声称已运行恢复攻击。

## AR009 — OPEN

正式 consume 顺序及 marker 所在目录 fsync 已修正；私有证据与失败 marker 的目录持久性仍有缺口。

源证据：`tooling/executor/external29_driver.py:39-64,196-210`；`tooling/executor/boundary.py:46-64`；`tooling/executor/executor_adapter.py:22-34,93-103`；`tooling/qualification/policy_builder.py:59-71`

formal 先 durable(FORMAL_ATTEMPT) 再 observer/policy/baseline，不再把旧独立 policy_builder 的调用次序缺口直接套到正式入口。durable 对文件及其直接父目录 fsync；但 boundary 私有 capture 文件落在 private 子目录，只 fsync 外层 decisions 目录，未 fsync private；adapter failure marker 只 fsync 文件。新建嵌套目录的父目录发布也未由通用 durable 递归落实。故完整崩溃持久性不能视为解决。

限制：已 consume 的正式 marker 阻止同 namespace 重启，不把私有证据缺口夸大成已证明正式入口必可重试；未执行崩溃测试。

## AR010 — OPEN

真实 acquisition 的循环内期限、事件容量和共享重试预算仍未落实。

源证据：`tooling/executor/capture.py:53-118,147-168`；`tooling/executor/observe.py:68-73,140-182`；`tooling/executor/external29_driver.py:74-79`；`tooling/executor/bookkeeping_v3.py:36-45,202-222`

capture_file 只在尝试前和完整 read 结束后检查时间，read 循环没有时钟检查；无 max_bytes 的 usage/manifest 读取可在持续增长期间超过五秒仍不返回。observer drain 直到 EAGAIN 才结束，追加事件时不检查 4096 上限或时间，reducer 才事后拒绝；外层直接调用该 drain。每个 capture_file 重新分配最多三次尝试，非跨整个边界共享重试轮次。 capture_bundle 确实以同一 deadline 传 remaining 并在末尾检查，故并非完全没有总时限；缺口是读取/目录/事件获取期间不能及时中断，且三次尝试仍逐文件重置。

限制：没有运行持续写入/事件洪泛探针；普通多文件读取数量不能等同于重试次数；不要求 Owner 已明确拒绝的3600秒 cap。

## 完成范围及验证

- 仅咨询性静态审查，不是独立最终接受或新批准前置条件。
- 没有运行测试、探针、捕获、准备或formal，没有读取共享bookkeeping，没有修改产品/实现/封存integration。
- 正式预算仍为上下文给定1/2；本审查没有消费或核查正式运行状态。
- 仅AR006—AR010；AR001—AR005不在本part裁决。
- 现有87回执不构成穷尽覆盖，历史writer仍NOT_ESTABLISHED。
- Owner已接受ledger捕获间隐藏overwrite-restore/truncate-regrow观察限制；不是缺陷，不新增3600秒cap。
- 失败审查日志未使用；未从失败会话推定任何既有完成结论。

源hash：`SOURCE_HASHES_BEFORE.json` / `SOURCE_HASHES_AFTER.json`，82 个 scoped 源/配置文件，前后变化 0；详见 `SOURCE_HASH_COMPARISON.json`。此范围为 tooling 下 .py/.sh/.json，并非重新验证 parent 已验的1357项全集。

现有资格回执核对：`RECEIPT_CHECK.json`；87 controls / 87 unique，0 failure/error/skip，native_exit=0，直接dependencies及已声明source binding的hash一致；未执行测试。

判定汇总：{"RESOLVED": 1, "OPEN": 4}。JSON 机器索引：`REVIEW.json`。本报告所有 integration 源定位相对 integration-001；`K/` 前缀定位相对 continuation-002-approved-bookkeeping。
