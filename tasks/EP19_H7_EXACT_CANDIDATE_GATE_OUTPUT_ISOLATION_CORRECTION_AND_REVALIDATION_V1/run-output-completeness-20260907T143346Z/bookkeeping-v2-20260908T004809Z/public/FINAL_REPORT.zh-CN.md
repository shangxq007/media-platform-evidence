# V2 实施、父资格与正式启动前停止报告

## 决定

**V2 已实施，父侧 fresh 129 项控制 PASS；正式验证未启动。当前结果为 STOP_INCOMPLETE_STRICT_INPUT_CAPTURE，不是产品 PASS，也不是另一次 proposal-only。**

Owner 的 prospective V2 决定已采用。完整 writer/syscall ledger 不再是限定 bookkeeping 例外的前提；独立审查维持 PENDING，不阻断已授权工程执行。但原有严格工具输入捕获要求仍然生效。

新 continuation：`bookkeeping-v2-20260908T004809Z`。唯一准备的真实 run：`outputs/continuation-runs/bookkeeping-v2-formal-001`。

候选 commit：`689ab9456461a8d19a72d059f5157092efc43aff`；tree：`6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`；base：`86d6aef94fd5e58da552e97c11473cff6eca734e`。新 executor identity：`20ef0bc2939209032b82af3a28f5ca932d5e32fcca569bccd5ed1fb5d58a1b14`。Owner contract：`OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2`。

## 已完成的实现与资格

- 已恢复原 executor identity `198ae4c300605046853a9a39d4e9307af2e4bd96b02e45a0bb53dd077282b6ef`、observer `2e060dd77ed4b24132d581e36cc3fa84c8b67d928cd9ec7689dcdc8823e991e2` 和候选对象，保留 helper preimages；未改历史目录。
- 四字段一般会影响 curator 的活动/生命周期维护和部分 UI/学习图选材，因此没有宣称全局无语义。实际固定 29-gate matrix、产品命令与该验证执行链不通过这四字段选择输入；动态 Skill selection 不进入 gate 窗口。指令正文、支持文件、其他 usage 值与整个 Memory 仍严格。
- 使用稳定 FD 读取、重复键/非有限数拒绝、类型敏感深比较、计数与时间单调性、eligible-record 枚举与安装 inventory 绑定。实际 baseline-policy 枚举和严格值保留在本地 `bookkeeping-policy-v2.private.json`，不公开其中的私有值。四字段候选许可不是整个文件免责。
- 使用精确 usage 目标、root、已存在 lock 与 direct-child `.usage_[a-z0-9_]{8}.tmp` 命名空间。usage 替换及限定 root 元数据变化有记录；其余输入、未知事件、重定向、持续临时项和捕获缺口仍拒绝。
- scope、baseline/seal、preflight、prestart、逐 gate observer/reducer、命令边界、final acceptance、receipt 和 identity 已接入 V2。OLD_STRICT 结果单列，不能作为仅含许可 variation 的隐性 veto。
- 保留 RED 和 ordinary correction attempts。父侧中间实测揭示并修复：指数溢出、Skill 名称/目录映射、已有 persistent temp 被 baseline 接纳、资格复用证据不足。资格 capsule 还曾因只解析到 123/124 identities 拒绝；该尝试未删除。
- 实施者最终 suite 为 129 项；父侧另行实跑相同完整 suite，原生 exit 0，`Ran 129 tests in 5.903s; OK`。父侧验证 114 项 qualification 输入摘要及 formal-boundary applicability；这些证据不是本次真实 gate graph 成功证明。
- A/B/C 未撤销：run-specific 三套独立 checkout/output/receipt；COMPILE 新鲜度和完整性；frontend 引用资产闭包。复用内容、适用性和真实原生日志/回执的绑定详见 qualification/reuse 文档。

## 实际失败与责任边界

`python -B executor/runner.py prepare ...` 成功，backend、candidate-frontend、SHADOW 均在本 run 的独立 checkout。未执行并行前端开发 ref 的 gates，也未要求该 ref 静止。

父准备根据此次 `PARENT_COMMANDS.md` 选择了以下 **raw Lean distribution**：

`/home/user/Documents/workspace/audit-runs/EP19_H7_PRODUCTION_INPUT_BOUNDARY_CORRECTION_AND_PACK_MONITOR_QUALIFICATION_V1/formal-tools/lean-4.19.0-linux`

复制为 run-local cache，4617 个文件的解析后内容摘要一致，Lean binary pin 与 Podman socket/pinned Coq image 检查通过。但是 `copytree(..., symlinks=True)` 保留了该源中的库链接。它并不等同于旧 parent preparation 所用的 fully materialized 源：

`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/owner-clarified-execution-20260907T1120Z/prepared-tools/lean-4.19.0-linux`

这是**本次准备指令/源选择缺陷**，不是 Owner 未授权，也不是未知历史写者造成的漂移。文件内容摘要一致不足以证明严格 collector 接受文件类型；此前的 fixture 与复用资格没有证明本次实际 materialization 的端到端 readiness。

真正调用 baseline 时，`runner.py:100 → observe.snapshot → preservation.capture_files` 返回 `INCOMPLETE_CAPTURE`。以下 12 个 run-local `lib/` 项触发 `SYMLINK_SCOPE_REJECTED`：

- `libLLVM.so`
- `libLLVM-15.0.1.so`
- `libc++.so.1`
- `libc++abi.so.1`
- `libc++abi.so`
- `libatomic.so.1`
- `libatomic.so`
- `libz.so`
- `libz.so.1`
- `libunwind.so`
- `libunwind.so.1`
- `libclang-cpp.so`

所有完整绝对路径、当前 lstat 和 link target 保存在 `STOP_CONDITION.json`。这 12 项属于严格工具依赖，不属于四字段 bookkeeping 例外。没有通过放宽 symlink 规则、替换已拒绝 run 的输入、刷新 baseline 或另起 formal run 绕过拒绝。现有材料提示正确的 materialized 来源，但未在失败现场施加修复或重试。

## 实际状态

- 完成真实 run preparation；baseline capture 原生 exit **1**。
- `baseline.json`、`seal.json`、正式 preflight 和 `runtime/START.json` 均未创建。
- REQUIRED **29**；PASS **0**；FAIL **0**；NOT_RUN **29**。另记 readiness/capture failure **1**；它不冒充产品 gate FAIL。
- 正式 graph attempts **0**；正式测试 discovery/execution **0**。7973 / 29 skips / 149 保留为期望，不记作实际结果。
- 拒绝后的只读 bookkeeping endpoint 检查：OLD_STRICT **PASS**、V2 bookkeeping **PASS**；它只覆盖该 endpoint。全范围 OLD_STRICT 保全 **NOT_ESTABLISHED_INCOMPLETE_CAPTURE**，V2 input integrity **INCOMPLETE_CAPTURE**，不可由局部 PASS 升格。
- WRITER_ATTRIBUTION **NOT_ESTABLISHED**。不声称完整事务追踪、全局 writer 归因或全部原始字节/元数据不可变。

## 历史、隐私与发布边界

开头和结束均核对两份历史清单：4686 个旧运行文件、4615 个旧 continuation 文件，当前字节差异各 **0**。这是清单所列文件的端点读回，不是连续不可变证明。旧 5 PASS / 1 FAIL / 23 NOT_RUN、ARCHITECTURE/FAIL_PRESERVATION、command-gap 拒绝与后续 29 NOT_RUN 均未回改。`PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE`。

未编辑产品源代码、Skill/Memory 正文、共享 Hermes config 或其他 profile。Skill loading 的运行时 bookkeeping 与工具缓存不被冒称为“没有任何运行时写入”。未进行产品 commit/freeze/merge/push、部署或发布；未干预并行前端 lane。独立审查 **PENDING**，EP19 **未关闭**。

公开交付不含私有 usage 全文/strict projection、Skill/Memory 正文或凭据。`implementation-snapshot/` 是实施者在真实 baseline 尝试前形成的阶段证据，其中的 parent-command/readiness 描述已由本报告纠正；不能作为最终 readiness。最终机器字段见本交付根 `FINAL_FIELDS.json`，真实停止记录与原生输出见 `parent-evidence/`。远端 publication 状态以发布后 detached receipt 为准，证据发布不构成工程接受。
