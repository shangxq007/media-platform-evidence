# EP19 integrated-correction-v2 最终报告

## 结果

已在新的任务私有 `integrated-correction-v2/` 内完成原 unique controller source-copy 与直接依赖 coherence consumers 的联合修正和 affected qualification。实现结论是 **SOURCE CORRECTION COMPLETE / RETURN TO EXISTING INDEPENDENT REVIEW**；这不是独立批准，也不是 installed integration PASS。

真实状态保持：`formal_ready=false`、`integration_ready=false`、`real_readiness=BLOCKED`。共享三目标仍逐字节等于 expected-before，不等于本候选；没有 live successor/admission/formal/readiness 新事实。本轮没有共享/live 写入、安装、real prepare/admission/formal、产品测试/门、slot、publication、网络、凭据或 router 操作。

固定候选仍为 `a29864343ed4f630b052c20d86c23b240f13cfd0`，tree `fd37409d0274662abbe86f69e3d963c05b379696`，parent `689ab9456461a8d19a72d059f5157092efc43aff`，产品 patch `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`。预算保持历史 formal `2/2`、新增 `1 total / 0 used`、global ordinal `3`；产品历史 `3/3`、新增 `0`。

## CP-01..04 disposition

- **CP-01 — source CORRECTED；未安装。** `stable_state_readback` 对三 authority 路径进入同一 state lock；Queue/ledger/slot 缺失、journal 存在、sequence/schema/transaction identities 不一致均拒绝。recovery 只接受精确三 authority、精确 journal 字段和唯一 ledger transaction，并在清 journal 前重验恢复后整体。`inspect` 与 identity readback 在同次锁定快照内形成摘要/结果。见 controller `:95-129,238-277,368-401,1101-1145,1158-1180`。测试实际覆盖 partial journal、畸形 recovery set、跨原 QueueControl/acceptance writer 并发；GREEN 43/43。
- **CP-02 — source CORRECTED；无真实 publication receipt。** 对 EP19 successor，generic `QueueControl.transition` 禁止进入 slot/integration/review/publishing/canonical 受控边；新 `SlotControl.prepare_ep19_direct_ff` 只允许 engineering 已接受、dependencies resolved、精确 a298 slot holder 的 `SLOT_ACQUIRED→APPROVED_FOR_PUBLICATION`。authorize 严格核对 caller entry，publication result 是唯一 `PUBLISHING→CANONICAL` consumer；CLI 已直接暴露 dedicated prepare/authorize/result。普通候选 normal two-parent 方法与测试保持。见 `:681-692,944-1058,1060-1099` 及 protocol 的 `direct_ff_state_order`。
- **CP-03 — source CORRECTED_FAIL_CLOSED；等待真实受接受 producer/reviewer receipts。** 新 validator 实读 source/stdout/stderr/producer receipt bytes，重算 SHA-256，并绑定 candidate/tree、producer source、attempt、actor、native exit、timing、formal gate/seal、engineering/closure reviewer、ancestry/race/remote/canonical/sanity。admission 的 implementation identity 改为已验证 executor source bytes，不再是 identity JSON 自身摘要；self-declared identity 负例已通过。见 `:137-200,1190-1220,1303-1334,1373-1384,1410-1430`。私有 fixture receipt 仅证明 consumer 行为；尚无真实 producer bytes，因此不宣称 readiness。
- **CP-04 — source CORRECTED_FAIL_CLOSED；实际维护机制缺失。** install recovery 的 target count/order/path/before/after/base64/mode 必须逐项重绑定 reviewed manifest；unknown/stale bytes 拒绝。只读检查原 Skill 未发现可覆盖所有旧/新 consumers、三个目标、完整 check/replace/readback/recovery/re-enable 窗口的既有 maintenance/consumer-quiescence interlock。publication slot 不是维护权限，task-local lock 也不能阻止旧进程。因此 installer `main()` 在任何 target write 前固定返回 `BLOCKED_MISSING_EXISTING_COORDINATION_MECHANISM`，不伪造维护权威、不允许 partial activation。见 installer `:37-52,96-155,196-199`。

## COH-IR-01..04 disposition

- **COH-IR-01 — source CORRECTED；original controller 尚未安装/复核。** runtime binding 只接受名为 `canonical_publication_control.py`、包含原 StateTransaction 与 integrated EP19AcceptanceControl 的源；`ep19_successor_acceptance.py` 与历史 `b8c1d9…bd4a` 明确禁止。新的 integration requirements 固定 controller candidate SHA `e3931e…f8a0`，registration readback 与 formal consume 分成原 controller 真实回执接口。
- **COH-IR-02 — source CORRECTED_FAIL_CLOSED；无真实回执。** nonfixture control evidence 必须引用原 controller same-locked-snapshot readback bytes；implementation review 必须是 machine APPROVED 且逐项核对 reviewed source bytes。admission 持久化 raw capture、完整 private comparison 与 public projection，validation 从 raw capture 重算并要求三者相等；formal consume 必须绑定 exact `ADMISSION.json` SHA-256。见 `eligibility_coherence.py:233-333`、`eligibility_admission.py:26-72,78-123`、`external29_driver.py:660-678`。
- **COH-IR-03 — source CORRECTED；real builder 未运行。** real contract builder 只接受既有 candidate-002 map/inventory/instructions 与 semantic decision 的精确 path/hash，并固定 7 packages、107 members、15 instructions；runtime builder 和 policy consumer 再把 caller map/inventory 与 contract 逐字节投影闭合，缩小/替换拒绝。见 `eligibility_coherence.py:35-40,114-190`、`build_eligibility_contract.py:33-54`、`build_runtime_binding.py:60-66`、`policy_builder.py:66-80`。
- **COH-IR-04 — source CORRECTED；real admission 未运行。** nonfixture admission output 经 resolve 后必须严格位于 exact run 私有目录之下；outside-run 负例已通过。见 `eligibility_admission.py:78-83`。

## RED/GREEN 与身份保留

保存的 source-bound RED：controller 42 tests，7 failures/1 error；coherence 14 tests，3 failures；installer 6 tests，2 errors，均 exit 1。保存的 GREEN：controller 43/43、coherence+external29 31/31、installer 6/6，合计 80/80，exit 0。native logs 及 SHA-256 见 `QUALIFICATION.json`。

测试 identity accounting：controller 38→43、coherence 11→15、external29 16→16、installer 4→6；旧 test identities 删除/改名均为 0。新增控制只覆盖前序明确缺陷。Python AST 与 JSON parsing 均 PASS；`git apply --check` 和实际私有 reconstruction 对 preserved original 三目标 PASS，重建摘要逐字节等于候选。系统无 `patch` 程序的 `command not found` 已诚实记录，未换绕过工具；随后使用既有 `git apply` 仅作用于 `/tmp` 私有副本，不触碰产品或 shared source。

## 精确 source/patch

- controller `candidate/controller/scripts/canonical_publication_control.py` — `e3931e0c414e84ae1340b4b39ab747b744eb6f96947babd99d936a2bf268f8a0`
- protocol `candidate/controller/references/protocol-v1.json` — `4f1cc6a2c5cde04279920cdcb429fdb69f97ca08c34dd6da628fc2fe024d4e25`
- controller tests `candidate/controller/tests/test_canonical_publication_control.py` — `32fbc8741daecfc64135d556192fbee147a0b8e10f30844e1f2e0622999f3057`
- original-target patch `ORIGINAL_TARGETS.patch` — `a947dd4268630314b8d8e337360eaec0c3dd4aea0bdedbccfe3b3226c146026b`
- installer `parent-handoff/INSTALL_AFTER_COORDINATION_AND_REVIEW.py` — `1aeadcd978407bdb3f95d78961e78c93a6115a064885ce43d0ff4a986bdd43da`
- exact install manifest `parent-handoff/INSTALL_MANIFEST.json` — `bbe9f0cd7f0ba33242e8e4232154ce8f391191f2b7093d7067a0a7222e81359a`
- coherence source identities及 exact finite inputs 见 `FINAL_MACHINE_REPORT.json` 与 `integration/INTEGRATION_REQUIREMENTS.json`。

共享 installed readback 仍为 controller `6c30fa…5362`、protocol `84948f…a65`、tests `498f2b…6cfb`，与 manifest expected-before 相等，证明本轮没有安装。

## 父交接与停止边界

父任务先执行 `parent-handoff/PARENT_SEQUENTIAL_COMMANDS.md` 的只读核验，再将 exact source/hash/patch 送回**既有**独立技术审查。不得由本实现者自批。

目前没有安全安装命令：原管理者必须先指出/提供既有 consumer-quiescence maintenance mechanism 的精确 command/receipt 与覆盖范围；若不存在，只能由原管理者在新的明确维护授权中建立，不能由本任务自造。该条件与既有 independent review 均满足前，禁止 install、registration、admission、formal、slot、direct-FF、publication、sanity 或 closure。失败历史与所有 sealed predecessor 文件均保持原样。
