# EP19/H7 r1–r12 修正历史与第二次正式 STOP 完整交付报告

## 1. 最终结论
第二次正式调用 `proc_51f5901fa58d` 的parent保存事实为exit 1；实际FORMAL_ATTEMPT已记录2/2消费，且在policy与baseline之前不可返还地消费。FORMAL_FAILURE拒绝原因是 **PREBOUND_ELIGIBLE_MANIFEST_CHANGED**，定位policy_builder.py:66 / external29_driver.py:662。

**29 REQUIRED / 0 PASS / 0 产品gate FAIL / 29 NOT_RUN。没有baseline、preflight、START或成功FINAL/SEAL。不是产品门禁失败，也绝不是产品门禁通过。正式预算2/2、产品修复预算3/3用尽；禁止第三次尝试、刷新baseline、换namespace绕过预算或再改产品。EP19_CLOSED=false。**

独立最终失败审查已真实完成并合并，结论 **BLOCKED_NO_ENGINEERING_ACCEPTANCE**。此包尚未网络发布；没有证据提交/匿名回读，不冒称GitHub已完成。父任务可直接使用此诊断包检查与后续evidence-only追加发布。

## 2. 身份不得混为一谈
- 固定产品commit：`a29864343ed4f630b052c20d86c23b240f13cfd0`；tree：`fd37409d0274662abbe86f69e3d963c05b379696`。
- 产品patch SHA256：`bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`；直接父提交`689ab9456461a8d19a72d059f5157092efc43aff`；canonical比较基点`86d6aef94fd5e58da552e97c11473cff6eca734e`。
- 实际r12运行EXECUTOR_IDENTITY：`79344cddc6d782269572438e367c73a4ce11fa8f5597fcf2db50581b7e08b098`；identity文件原hash：`6ce755b2b6e32120a6eac5c3911da0152d75fe8beec83557170348d6c89f8193`。
- final-004 runtime binding原hash：`2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3`。旧writer index将此放入EXECUTOR_IDENTITY属于handoff表达，本报告明确区分，不能把binding hash当作运行identity。
- r12集成qualification原hash：`a5e305305bca2c30b036d5d480042efc5feb3644b9e2336a77a39a7cad00bb4e`；dependency原hash：`105046378b144d9ca0c6f9de4b0f0f6e3f7f31fdf3ffc0c7f66879911355d8e6`。
- 产品identity DELTA原hash为`4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e`，外部r11→r12 patch原hash为`5abeb7f1df5cdd484ee67e82eee639769397dfe577cb68aada6e45f322bb0ea8`；用途独立，不能将外部patch传入产品JSON消费者。

当前source_binding列举的121个本地输入已只读hash核对，0不一致；这不是全机无变化或正式保护窗口证明。当前产品未改；机器索引另列固定候选历史9条路径，不把历史static污染记录改写成当前新变化。

## 3. 失败诊断：保存事实、准备摘要和当前观察三层分离
拒绝谓词把policy重新捕获的包名→manifest有序列表（path/hash条目）与旧private eligible_skills深相等比较。私有map文件自身hash仍可正确，但其指向的共享文件字节已未必与旧manifest相同。不是usage计数单调性或ledger append语义拒绝。

独立审查从保存的最终PREPARATION_DISPOSITION发现两条新hash，与旧map/strict inventory矛盾；保存prepared_ns早于consume_ns。随后有限7包事后只读哈希观察为107对107条、2内容hash改变、0新增/0缺失，另外105条相同。两条为hermes-governance-toolchain的SKILL.md及references/remote-github-visibility-audit.md。公开FINDINGS只含定位与旧/新hash，不含正文/完整私有清单。

**正式回执没有保存当时actual manifest；不能把事后2条差异说成正式时刻完整差异集合。写入者、精确修改时间、修改动机均NOT_ESTABLISHED。** 包作者没有重扫共享树；引用独立审查原件并已核对其manifest。

loader、synthetic prepare sentinel、实际准备与其200项advisory各自有范围限制。最后instruction seal与旧eligibility seal分别正确，不意味着相互一致；有限分项PASS被提升为整体ready会遗漏跨清单关系。完整代码及调用序列/问题见[诊断入口](DIAGNOSTIC_REVIEW.zh-CN.md)。

## 4. r1–r12与资格历史
HISTORY_R1_R12包含12轮、127份实际RESULT定位；附历史报告/索引/逐项矩阵、RED/GREEN与失败/取代资格回执及原生日志。旧candidate-formal-001保持BASELINE_OBSERVATION_REJECT、29 NOT_RUN；此次实际第二次失败追加，不覆盖旧namespace。
r1..r12从连续观察、V2 temp、时钟/framing、依赖身份，到cause/latch/持久化/限额，再到r12实际prepare consumer，均保留逐轮证据及适用范围。r11真实准备AttributeError失败、r12 qualification-001失败、后续资格被取代原因留在历史文件，不用最终PASS抹去。

r12 qualification-005机械对账：179 expected、179 executed、179 unique、179 PASS；94 mandatory全部存在；FAIL/ERROR/SKIP/duplicate为0，missing/unexpected集合为空。该结论来自原始身份列表，**不是重跑结果、不是产品测试、不是完整正式baseline**。focused predecessor RED native1/wrapper0，GREEN native0/wrapper0；旧27产品测试身份、旧资格reuse仅历史适用性，不fresh。

CONFORMANCE_MATRIX逐条列AR、契约、历史反例/RED/GREEN/入口、最终r12处置及来源；两项005/006为保留回归，不捏造新RED。AR007的资格修正不等于真实eligibility跨seal一致性已经闭合；独立审查未重新签发全部AR工程通过。

## 5. 正式逐门与完整后端
FORMAL_GATE_RESULTS.json从实际FORMAL_FAILURE的29唯一gate生成，每项NOT_RUN，命令未执行、exit/output/time/freshness为null或NOT_RUN。GATE_EXECUTION_MATRIX原命令仍随源码交付，但不是实际运行日志。FULL_BACKEND_ACCOUNTING：EXPECTED=8000、EXPECTED_SKIPPED=29，EXECUTED/PASSED/FAILED/ERRORED/SKIPPED=0（本attempt未启动），DISCOVERED/MISSING/UNEXPECTED/DUPLICATE=null（没有发现/对账输出）。不能将预期填为实际通过。

## 6. 保全与批准限制
A/B/C没有修改：精确空regular锁例外、既有usage四字段V2规则、ledger NOOP_MANIFEST_APPEND_SUBSET。原64MiB prefix、128记录、1MiB行、8MiB新增、4096 manifest项、128 eligible包、每边界最多3次/5秒、4096 pending及原生gate timeout保持。没有新增3600秒attempt cap。
已接受的ledger捕获间overwrite-restore/truncate-regrow不可见限制继续披露，不再变成新门禁，也不推广到其他protected对象。正式只留下consume/failure持久化事实，不能从这两文件推出成功连续覆盖、同源capture接受、FINAL/COVERAGE/SEAL或工程保全通过。

## 7. EP19关闭条件逐项对账
本报告及CLOSURE_CRITERIA_ACCOUNTING只是交付对账，不是第二权威账本。已找到旧关闭回执但原可追加账本精确位置/记录键/权威来源未建立；没有猜路径或修改冻结回执。旧86d6候选确有历史产品发布，当前a298候选未发布；不混淆两者。工程、独立接受、原账本、产品发布、sanity和证据发布分别对账如下。

|既有条件|当前处置|
|---|---|
|固定产品/预算不漂移|FIXED_INPUTS_BOUND_NO_NEW_PRODUCT_CHANGE|
|外部契约符合性|QUALIFICATION_REVIEW_SUPPORTED_NOT_ENGINEERING_PASS|
|资格/依赖/运行绑定|PREPARATION_BOUND_BUT_FORMAL_ELIGIBILITY_REJECTED|
|正式完整29门及保全|NOT_SATISFIED_29_NOT_RUN_BUDGET_EXHAUSTED|
|完整后端身份|NOT_SATISFIED_NOT_RUN|
|H7/EP19既有语义及打包|NOT_SATISFIED_NOT_RUN|
|独立接受|INDEPENDENT_FAILURE_REVIEW_COMPLETED_BLOCKED_NO_ENGINEERING_ACCEPTANCE|
|原验收记录追加|BLOCKED_ORIGINAL_AUTHORITY_APPEND_TARGET_NOT_ESTABLISHED|
|修正候选规范产品发布|NOT_PERFORMED_CURRENT_CANDIDATE_NOT_AUTHORIZED|
|发布后sanity闭合|NOT_RUN_CURRENT_CANDIDATE|
|证据交付|LOCAL_CANDIDATE_ONLY_PARENT_PUBLICATION_PENDING|

具体剩余动作：保留独立失败结论及三层证据，父任务检查本包并正常追加证据发布/匿名固定提交逐字节回读；查明原权威账本精确目标后仅追加允许的失败对账；任何工程恢复须另获明确授权，议题收敛为eligibility与instruction基线的一致性/授权形成时序及启动前消费者，不自动执行修复或新验证。当前候选产品merge/push/deploy及发布后sanity不在本轮授权内。

## 8. 交付与披露
SOURCE_ALLOWLIST和PACKAGE_ALLOWLIST为精确名单；SOURCE_PROVENANCE区分原始与脱敏字节；MANIFEST与LOCAL_RECEIPT为非循环完整性材料。公共必要r12源码、tests、拒绝谓词/调用者、资格结果、准备边界、独立诊断已纳入。大型fixtures/Lean/clone/collector、旧完整源码树及private正文未打包，详见OMITTED_EVIDENCE和SANITIZATION_AND_REPRODUCIBILITY。衍生源含路径常量替换，因此不可声称可直接执行或原hash不变；预算也禁止运行历史命令。

没有凭据访问/网络/push；当前EVIDENCE_COMMIT_SHA与URLs/Public manifest为null，REMOTE_VERIFICATION=NOT_ATTEMPTED。证据发布成功也不会提升工程结论。完整必需字段的实际值如下（结构字段详见机器JSON）。

## 9. 必需输出字段
|字段|实际值|
|---|---|
|`AFFECTED_QUALIFICATION_RESULTS`|{"focused_green": "1_PASS", "focused_red": "1_EXPECTED_FAIL", "integrated": "179_PASS"}|
|`APPROVED_CONTRACT_CHANGED`|false|
|`BASELINE_RESULT`|NOT_RUN_STOP_BEFORE_BASELINE|
|`CANDIDATE_COMMIT_SHA`|a29864343ed4f630b052c20d86c23b240f13cfd0|
|`CANDIDATE_TREE`|fd37409d0274662abbe86f69e3d963c05b379696|
|`CAPTURE_COHERENCE_AND_LIMITS`|UNCHANGED_CONTRACT_QUALIFICATION_ONLY_NO_FORMAL_ACCEPTANCE|
|`CONTINUATION`|CONFORMANCE_CORRECTION_SECOND_FORMAL_EXECUTION_AND_CLOSEOUT|
|`CONTINUOUS_PROTECTION_COVERAGE`|NO_COMPLETE_FORMAL_WINDOW_NO_BASELINE_OR_START; qualification scope only|
|`DECISION`|SECOND_FORMAL_STOP_LOCAL_EVIDENCE_CANDIDATE_ONLY|
|`DEPENDENCY_AND_ELIGIBLE_BINDING`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`EP19_CLOSED`|false|
|`EP19_CLOSURE_CRITERIA_ACCOUNTING`|CLOSURE_CRITERIA_ACCOUNTING.json|
|`EVIDENCE_COMMIT_SHA`|null|
|`EVIDENCE_DURABILITY_AND_FAILURE_LATCH`|FORMAL_ATTEMPT_AND_FAILURE_PRESENT; no successful FINAL/COVERAGE/SEAL|
|`EXECUTOR_IDENTITY`|79344cddc6d782269572438e367c73a4ce11fa8f5597fcf2db50581b7e08b098|
|`FAILED_GATES`|0|
|`FINAL_PRESERVATION_RESULT`|NOT_RUN_NO_SUCCESSFUL_FINAL_OR_SEAL|
|`FORMAL_ATTEMPTS_USED`|2/2|
|`FULL_BACKEND_TEST_IDENTITY_ACCOUNTING`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`INDEPENDENT_REVIEW_RESULT`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`LANE`|BACKEND_VALIDATION|
|`MACHINE_INDEX_URL`|null|
|`NOT_RUN_GATES`|29|
|`PASSED_GATES`|0|
|`POST_PUBLICATION_SANITY`|NOT_RUN_CURRENT_CANDIDATE|
|`PREFLIGHT_RESULT`|NOT_RUN|
|`PRODUCT_CHANGED_PATHS`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`PRODUCT_PATCH_SHA256`|bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690|
|`PRODUCT_PUBLICATION`|NOT_PERFORMED_CURRENT_a298_CANDIDATE; old_86d6_PUBLICATION_HISTORY_RETAINED|
|`PUBLIC_MANIFEST_SHA256`|null|
|`QUALIFICATION_IDENTITY_ACCOUNTING`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`REMAINING_BLOCKERS`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
|`REMOTE_VERIFICATION`|NOT_ATTEMPTED_LOCAL_ONLY|
|`REQUIRED_GATES`|29|
|`REVIEW_INDEX_URL`|null|
|`SECOND_FORMAL_RUN_ID`|candidate-formal-002|
|`START_CREATED`|false|
|`STOP_REASON`|PREBOUND_ELIGIBLE_MANIFEST_CHANGED; SECOND_FORMAL_BUDGET_EXHAUSTED|
|`TASK`|EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1|
|`EXECUTOR_IDENTITY_FILE_ORIGINAL_SHA256`|6ce755b2b6e32120a6eac5c3911da0152d75fe8beec83557170348d6c89f8193|
|`RUNTIME_BINDING_ORIGINAL_SHA256`|2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3|
|`PRODUCT_FIX_BUDGET_USED`|3/3|
|`FORMAL_PROCESS`|proc_51f5901fa58d|
|`FORMAL_NATIVE_EXIT`|1|
|`FAILURE_CLASSIFICATION`|PREBOUND_POLICY_ELIGIBILITY_REJECTION_NOT_PRODUCT_GATE_FAIL|
|`PUBLIC_MANIFEST_SHA256_NOTE`|No public manifest yet. Local MANIFEST.sha256 hash is recorded in LOCAL_RECEIPT.json outside its own coverage.|
|`AR001..AR010_DISPOSITION`|见 FINAL_MACHINE_INDEX.json 的同名结构字段；无省略字段。|
