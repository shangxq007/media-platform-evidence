# 第二次正式失败独立诊断与处置（最终）

## 结论
**BLOCKED_NO_ENGINEERING_ACCEPTANCE；独立 advisory / 符合性失败审查，不是工程 PASS。**
固定候选 a29864343ed4f630b052c20d86c23b240f13cfd0 / tree fd37409d0274662abbe86f69e3d963c05b379696。第二次尝试已消费，预算 2/2；29 REQUIRED、0 PASS、0 产品 gate FAIL、29 NOT_RUN。不得第三次尝试、刷新 baseline、修改执行器或产品；EP19 不可据此关闭。8000 身份/29 skipped 仍仅预期，实际完整后端未运行。

## 精确失败谓词及阶段
`policy_builder.py:63–66` 构造 `actual = {name: row["manifest"] for name, row in policy["eligible_map"].items()}`，并用 Python 原生结构比较 `actual != declared.get("eligible_skills")`；不相等即抛 `PREBOUND_ELIGIBLE_MANIFEST_CHANGED`。比较的是包名到有序 manifest 列表的映射，条目为绝对 path / SHA-256；不是私有清单文件自身摘要比较，也不是 usage 单调性或 ledger append 语义失败。
`bookkeeping_v3.py:259–265` 调用 bind_eligible_packages，对 applicability 给定有限包集合重新捕获。capture.py 的 capture_manifest 递归该包内 regular 文件、按 path 排序，拒绝 symlink/special/空包/缺 SKILL.md，并有原有限额。本审查不调用这些模块。
`external29_driver.py:650` 先 consume，656 注册 observer，659–661 验证私有输入路径/摘要，662 调用 build；663 的 bind_policy、664 的 policy 持久化、670 strict_baseline、671 preflight、673 START、675 graph 均在本次异常之后，未到达。build 内 create_policy 已执行过捕获，不能说“没有任何 bookkeeping 读取”；但它返回的 actual manifest 没有被失败回执保存。

## 三层证据：不得合并为历史全知
1. 历史正式事实：FORMAL_ATTEMPT 记录 CONSUMED_BEFORE_POLICY_AND_BASELINE，FORMAL_FAILURE 原 traceback 定位 driver:662 / builder:66，并逐门记 NOT_RUN。该回执仅证明当时结构不等，**没有保存正式时刻 actual manifest 或逐项差异**。Parent提供 proc_51f5901fa58d exit1；本审查直接依据可见失败回执及源码返回1路径，不伪称独立读取了外层进程回执。
2. 保存的历史准备证据：PREPARATION_DISPOSITION.prepared_ns 与两个 instruction_inventory 摘要已存在；它们与旧 map/inventory 对应摘要不同，且等于本次当前观测。SKILL.md 还在 instruction_inputs 中记录同一新摘要。因此不能把差异仅归为正式之后的新漂移；至少保存的最终准备封存已记录不一致的两套权威输入。prepared_ns 早于 consume_ns，详见 FINDINGS.json。保存回执不是独立见证其写入时刻，时间字段按历史保存事实引用。
3. CURRENT_OBSERVATION：仅对 applicability 指定7包做窄文件枚举及 SHA-256，107个既有条目与107个当前文件对照：**2个内容摘要改变，0新增、0缺失；其余105条相同**。没有 symlink 观察异常。旧 strict inventory 的107个摘要均与旧 map 一致。此为本次普通只读哈希观测，不是正式稳定捕获/collector，不证明读取窗口中绝无变化，也不证明正式当时精确差异恰好只有2条。

### 两条有证据支持的差异（仅定位与摘要，不导出正文或私有完整清单）

- `USER_HOME/.hermes/skills/software-development/hermes-governance-toolchain/SKILL.md`
  - 旧 map 与 strict inventory：`049045c71ac90f97b5a8efa5159c32dcbca9405fe933b211798256a319829841`
  - 保存 disposition inventory 与当前观测：`f8d786ea262558a2f6415bbb87a4887d24f83cd9571b474f78c32a5721559aa9`

- `USER_HOME/.hermes/skills/software-development/hermes-governance-toolchain/references/remote-github-visibility-audit.md`
  - 旧 map 与 strict inventory：`253495020e1b042781e36ec83b717334618d34cb088939677ddf1ba02441cd26`
  - 保存 disposition inventory 与当前观测：`65657b1118309f2534dca847ea9b492deccc67703db6bb6b61cef348251faa9a`

## final-004 绑定与准备漏检原因
final-004 SHA-256 为 `2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3`，与 FORMAL_ATTEMPT 一致。applicability 仍引用 writer-evidence-r2 的 INPUT_CURRENT_APPLICABILITY；private-r12 map/inventory 文件自身摘要仍匹配绑定，applicability 中的两项 provenance 摘要也匹配。因此不是“绑定文件被换了”的证据，而是**冻结清单自身保持不变，不等于清单所指共享包正文仍等于旧字节**。
四个关键实现源（builder/bookkeeping_v3/capture/driver）当前摘要均匹配 final-004 source_binding。

- 资格 QUALIFICATION 保存179 tests/179 unique，failure/error/duplicate/skipped为0，但 formal_baseline=false、formal_preparation=false、product_gate_execution=false。真实合成控制通过没有证明真实共享 eligible bytes 等于旧 map。
- validate_runtime_binding_r12.py 验证 binding、资格、依赖、运行源及产品 identity；没有调用 policy_builder.build 或对真实包做此 exact manifest 比较。loader PASS 无法蕴含该谓词为假。
- part-a 限定前创建 product-identity consumer；positive CLI 在 sentinel FileExistsError 结束，不是完整准备成功。part-b 明确不读取 private map/inventory 正文，只依据 consumer 源与 loader，且将私有 eligibility 合并处置留给 Parent。
- actual-preparation-review 明确未读共享 instruction/bookkeeping 树，也未重新核验 private eligibility，范围是准备产物、Lean/namespace/source seals；当时 disposition 尚待完成。其“200项检查通过”不能覆盖未检查的跨清单关系。
- 最终 disposition 在 driver:832–833 捕获当前 instruction_inputs/instruction_inventory；sequence:55–57 比较的是该封存与当前指令树，不是和旧 eligible map 做交叉相等。formal 又把 sequence.verify 排在 policy build 后面。两个独立保持正确的 seal 可以互相矛盾：旧 map 的冻结完整性与新 instruction inventory 的当前完整性不是同一不变量。

**支持的漏检解释**：分项审查明确限域，Parent 合并/启动条件未以证据闭合真实 eligible manifest 对旧预绑定值的交叉一致性；最终准备产物事实上已经携带可静态识别的两条矛盾。不能将分项有限 PASS 提升成完整 formal readiness。此结论不等于认定审查者隐瞒，也不能据此认定是谁改写了共享文件。

## 独立处置与边界
保留第二次失败，不重命名为资格、不回收预算、不覆盖旧 map/inventory/binding/失败回执。失败属于正式 setup 的预绑定输入一致性拒绝，不是产品门禁 FAIL；fail-closed 行为保留，不建议去掉等式或重写旧 map 强迫通过。
本审查不重新宣称全部 AR001..010 工程通过，不推翻已获接受的 ledger 捕获间限制，不新增全机无 writer 门禁。写入者、确切修改时刻、修改原因与正式时刻完整差异集均 NOT_ESTABLISHED。未读取或导出共享 ledger/usage/指令正文，只对有限包文件在内存中哈希。
现有授权可完成失败证据交付和权威关闭条件的失败对账；工程接受/EP19关闭仍阻断。任何后续恢复应另获明确授权，最小议题为旧 eligibility 基线与准备指令基线的一致性契约、授权形成时间及其启动前消费者；不自动执行修复或新验证。本次没有 loader、collector、test、probe、prepare、formal、PID 扫描、服务操作或产品仓库写入。

## 交付与完整性
只在本任务指定 independent-failure-review 目录追加早期/最终中文报告、摘要索引和非循环 manifest。未执行 Skill/Memory 修改；不对其它进程或全机文件变化作无证据的“零变更”担保。所有选定原件 SHA-256 与观察时间见 FINDINGS.json；报告与该索引哈希由 MANIFEST.sha256 外部绑定。早期报告保持原样。
