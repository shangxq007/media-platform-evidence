# r12 part-a：实际 preparation consumer 与 source-bound CLI 静态审查

## 结论与权限

**SCOPED_CLOSURE_SUPPORTED / ADVISORY_PREFORMAL_ONLY。** 未发现阻止本次“缺失 API + 产品/外部 delta 语义错配 + 前创建 CLI consumer 资格”限定修正闭合的实质缺陷。此结论不是完整 preparation 成功、29-gate 工程通过、全部 AR 独立接受或正式启动许可。最终 owner/parent 合并其他分项审查与真实准备回执后才能决定后续动作。

本次只读取已有文件、解析数据、比较源码和计算 SHA-256；没有测试、导入被审模块、loader、probe、prepare、baseline、formal、产品工作负载、Git 命令或实现修改。没有读取共享 ledger/usage/credentials 正文。仅在 J/preformal-review-r12/part-a 写报告及静态摘要。依据 OWNER_AUTHORIZATION.verbatim.txt:46–61,173–183,234–248,261–279,302–312；本子任务限制比 Owner 总授权更窄。

路径简称：J 为本 continuation；E=J/implementation-r12/tooling/executor；Q=J/implementation-r12/tooling/qualification；W=J/writer-evidence-r12；P=J 的父目录/candidate-preparation/native-delta-001。

## 1. API 与产品语义：闭合

- r11 首个故障依据 preparation-failure-r11/FINAL_STATIC_REPORT.zh-CN.md:13–16,28–30,36–52：Parent 原错误是摘要事实，非可见原 traceback。静态计算 `module 'binding_contract' has no attribute 'path'` 的 UTF-8/no-newline SHA-256 为 `97863e69ab6779d2ba89485b262716ae8d167eca604f7e3536880eff0c10a790`，与保存 RED 的 causal reason 一致。不能把本轮 RED 的 unittest traceback 说成原 Parent traceback。
- E/identity_delta.py:59–62,105–110 改为既有 `bc.exact_path`；E/binding_contract.py:24–27 保留绝对路径且 resolve 相等要求。没有新增 permissive path alias。
- 对比 r11/r12 的 identity_delta.py，实质只有两个 path API 修正及 derivation 字段描述修正。原 exact schema、candidate/tree/parent/base、tree universe、Git object source、source blob、测试源码方法、JUnit 身份集合、native argv/cwd/exit/source/output 绑定与 impact policy 校验仍保留（E/identity_delta.py:87–96,105–158）。不是删掉 validator 或把 patch 文本造为产品 JSON。
- E/binding_contract.py:37–45,67–73 明确强制两字段 `product_identity_delta` 和 `external_implementation_delta`，分别 exact path/hash；E/execution.py:12–24 只把产品字段交给真实 identity validator，并传真实 git 函数。E/runner.py:32–40 的 executor identity basis 同时收纳两个摘要。
- 最终绑定实测 SHA-256=`2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3`，文件是 W/RUNTIME_BINDING.candidate-formal-002.r12.final-004.json；121 项 source_binding 均与当前文件字节一致。
- 外部目录完整静态枚举（排除 outputs/__pycache__）为 r11 121 / r12 122 文件，13 个 changed/added，精确等于 W/IMPLEMENTATION_DELTA_RECORD.r12.final-004.json:4–82；每个 before/after 摘要相等，无遗漏差异。外部 patch 摘要 `5abeb7f1df5cdd484ee67e82eee639769397dfe577cb68aada6e45f322bb0ea8`。这不等同于本次独立执行产品 Git 状态检查；产品固定身份另有已保存 loader 证据。

## 2. 产品证据来源：历史真实产物，不是 fresh 产品 PASS

最终产品字段固定 P/DELTA.json，实测摘要 `4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e`。独立静态核对其六个 source、两个 XML、两个 producer receipt、两个 raw log 的引用摘要均一致。

P/junit.RECEIPT.json:2–39 绑定固定 candidate/tree/parent/base、原 Gradle argv/cwd、native/wrapper=0、PID/起止时间、source Git blob 与输出 XML；P/junit.START.json:2–17 与其 PID/argv/start 一致；P/junit.stdout.log:3–13 保存 compile/test 与 BUILD SUCCESSFUL。impact 对应 START/RECEIPT 亦有独立 PID/argv/start 和日志绑定，不是将外部 patch 转写为伪造 JSON。

静态 XML 解析得到 CleanupReliabilityTest 2、CleanupFailurePropagationTest 25，共27个唯一 identity，与 DELTA.delta_identities 集合精确相等，无 testcase failure/error/skipped。未执行产品测试或生产者。本证据支持保存的 candidate-bound 历史27个身份来源；不补造它未保存的环境/执行源历史证明，不将其归属于 r12 执行器，也不把27、8000/29预期换算为本次正式实际通过。摘要一致和相互绑定不等于独立见证原生产进程；本审查对“真实”的支持来自既有 START/native/receipt/XML 链的一致性，而非重新见证历史。

## 3. CLI RED/GREEN：闭合到前创建 sentinel，非完整准备

真实链源码是 E/external29_driver.py:813–816,837–858 → modules/runpath → E/runner.py:71–75 → E/execution.py:12–20 → E/identity_delta.py:105–158。先 qualification 与 object/identity 验证，再检查已有 run，随后才创建 namespace。

Q/test_r12_actual_prepare.py:48–80,108–161,166–239 使用真实 subprocess argv（明确 qualified Python、`-B ...external29_driver.py prepare --run-id ... --binding ... --binding-sha256 ...`）。保存 fixture 的 source_binding 与实际字节相符。独立比较 RED/r11 与 GREEN/r12 私有 executor：只有 binding_contract.py 的私有 ancestry/证据目录映射、dependency_contract.py 的 ancestry、coverage.py 的显式私有 qualification 分支不同；external29_driver.py、runner.py、execution.py、identity_delta.py 字节未替换。没有 mock 掉本次关键 validators。

coverage 前置资格确实被 sealed private source check 替代（Q/test_r12_actual_prepare.py:69–88），因此不能称整个实际 integrated qualification 与 CLI 已在同一次未经替代的端到端准备中成功。最终保存 loader 另行走真实 qualification + verify_object_source（W/validate_runtime_binding_r12.py:17–41）；其 final-003 原生日志绑定 final-004，native/wrapper 均0，日志与前后源码快照摘要核对无差异。两类证据是互补，不是完整 prepare 证明。

| 保存证据 | 实际观测 | 精确含义 |
|---|---|---|
| W/red-r11-preparation-consumer-final-004/NATIVE.log:1–17 | 1 unittest FAIL，native1/wrapper0；首个 positive CLI 为 AttributeError、上述 reason hash | 同体测试复现旧 seam 故障；其余六案未执行 |
| W/green-r12-preparation-consumer-final-005/NATIVE.log:1–6 | 1 unittest PASS，native0/wrapper0 | 一个测试身份包含7次 CLI 调用，不是7个 unittest identity |
| GREEN positive-genuine-product-identity.process.json | CLI exit1 / FileExistsError，sentinel 未变 | 产品校验完成后拒绝预存在 run；不是 CLI exit0 或 PREPARED |
| external-patch-in-product-identity | exit1 / JSONDecodeError | 文本 patch 不能冒充产品 JSON |
| wrong-product-schema / wrong-product-identity | exit1 / RuntimeError，对应 DELTA_SCHEMA / DELTA_CANDIDATE 摘要 | schema/候选身份不匹配拒绝 |
| wrong-product-hash / missing-product-identity / wrong-config-seal | exit1 / RuntimeError，匹配各自 seal/schema reason | 前置绑定拒绝 |

以上七份 GREEN process 的 stdout/stderr hash 已按实际保存字节核对；RED 只有一份 case receipt，未把缺失六案宣称 RED。RED/GREEN test body 摘要均为 `ca1cf4d637247a985bb7779f5ad771e9603670feb195c438eaaf559f3fe7badd`，wrapper 源码摘要 `92757b304ecf36e7287fa0a757a7f25f24a80e5ef7a3c9f4de1a67553f1f1a8a`；各前后 source snapshot 文件摘要、source/snapshot 对应关系、log/result 摘要均一致。Q/run_source_bound_group.py:64–82,105–141 说明 wrapper_exit0 是源稳定，不是 child RED 成功。

“负控前无副作用”精确限定为目标 runner 在 namespace/create/tool calls 之前拒绝；fixture 建设、config/receipt 写入、环境配置本来存在，不应宣传为全进程零写。测试只断言 sentinel unchanged；源码顺序支持目标准备创建未到达，未对全机文件系统做零变更观测。

## 4. 邻接接口与剩余条件

- E/binding_contract.py:10 补 OLD_TREE；inventories 不是当前 prepare 所调用的路径，未重生成预期身份。
- E/coverage.py:188 当前 integration schema 返回；legacy binding_qualification.extension 在189行后。已报告的 legacy bc.authority 缺项不冒称闭合，也不是此绑定 mandatory schema 的可达阻断。
- E/external29_driver.py:817–834 的 identity/endpoints/revalidate/disposition 分支与 parser 参数静态对应；prepare 第75–94行之后的 namespace/clone/parser/Lean、这些后续接口的真实结果不在本次动态证据范围。W/ADJACENT_PREPARATION_INTERFACE_REVIEW.r12.final-002.json:2–21 与该限制一致。
- r11 loader 不足以证明 real prepare 的 readiness 判断已在 W/FINAL_REPORT.r12.final-002.zh-CN.md:5–7 追加更正，未覆盖原历史。
- 必须保留 parent 顺序准备回读、失败不重试、唯一 final-004 binding、剩余一次正式 consume，以及后续独立接受条件（W/PARENT_HANDOFF_COMMANDS.r12.final-002.md:3–6,18–29）。本审查没有操作任何现场，也不刷新预算：1/2 与产品3/3为既有报告状态，不是本次执行观测。29门和8000/29仍不得填实际PASS。
- 本分项不独立重审所有 AR001..010/179身份完整资格矩阵，不能以这个 scoped closure 代替其余分项、正式工程或 EP19 closeout。

## 5. 静态完整性与交付

初始/结束同一137文件摘要集合无变化：SOURCE_HASHES.before.json / SOURCE_HASHES.after.json。STATIC_CHECKS.json 保存上述真实静态计算结果。初审 EARLY_REPORT.zh-CN.md 保留。额外发现的历史引用/私有 case/snapshot 按绑定摘要静态核对，未把它们谎称全部纳入最初137项的审查前快照。

一次审查脚本按其他 receipt 模式假定 raw_log 字段而 KeyError；读取实际 schema 后改用 native_log_sha256 完成核对。没有执行被审程序、改动证据或隐藏该错误。最终限定结论：本 seam 无未解除 blocker；完整 parent preparation、formal、独立最终接受及 EP19 收尾仍待实际完成。
