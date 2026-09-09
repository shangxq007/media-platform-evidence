# r12 实际准备四步只读复核（Parent disposition 前）

## 结论
**FOUR_PREPARATION_OUTPUTS_SUPPORTED_SEAL_PENDING；独立 advisory，非最终接受。**
现存实际 prepare、identity、endpoints、revalidate 产物符合已读取的现行消费者要求；本轮200项静态检查全部通过，未发现实际拒绝、必需准备产物缺失或所核对当前字节不一致。未执行任何被审程序、测试、probe、loader、collector、PID扫描或准备/正式命令。

J为本continuation，R为implementation-r12/tooling/outputs/continuation-runs/candidate-formal-002。完整绝对来源与SHA256见SOURCE_HASHES.json，逐项判定见MACHINE_CHECK.json。

## 实际证据
- prepare.json为PREPARED_NOT_BASELINED，固定candidate/tree/base、qualification、Owner摘要一致，formal_gate_execution=false。namespaces有backend/frontend/shadow-fixture三份独立clone记录，保存tree/parent、hardlinks=0、alternates=0；三份原生clone日志含--no-hardlinks及checkout完成，当前.git/HEAD均为固定完整SHA，无alternates文件。本轮没有新Git命令，树/parent/完整inode独立性仍以生产者保存检查为依据，不伪称重新完成全仓Git验证。
- bindings的29个唯一order/gate与当前权威matrix一致；source-recovery的158个引用源文件hash一致。parser MANIFEST列出8包216文件，run-local拷贝逐项hash一致。
- Lean materialization列出4617文件；当前run-local逐文件SHA256、大小、mode、regular/nlink与manifest一致。完整preparation-collector保存5077项entries、4627个hash、errors=[]；其hashed文件集合与4617 Lean+1 init+9去重runtime工具精确相等。任务内4618个文件当前hash与capture一致；9个外部工具只核对保存capture/compatibility/revalidation之间摘要一致，不重新读取或探测外部工具。源/目标目录与三方inode独立性由已保存materialization/revalidation支撑，未重跑collector。
- 三个真实Lean准备probe：version、prefix、import-compile-proof，native_exit均0，process receipt与嵌入记录逐字段一致，原生日志hash一致，Lean版本4.19.0、绝对run-local prefix、system_fallback=false。编译日志为空是成功允许结果，不是缺失；PreparationProbe.olean存在、非空且hash一致。**三个准备probe不是29-gate产品FORMAL门禁**。
- identity完整文件hash为6ce755b2b6e32120a6eac5c3911da0152d75fe8beec83557170348d6c89f8193；依据runner.executor_identity_basis源码独立重建当前helpers/orchestration及全部绑定字段，再用sort_keys=True、separators=(',',':') canonical JSON计算，运行身份为79344cddc6d782269572438e367c73a4ce11fa8f5597fcf2db50581b7e08b098。它不是binding文件hash。当前tooling源宇宙与source_binding精确相等，产品identity delta与外部patch分别封存、用途不混淆。
- endpoints保存PASS、正确run_id、bwrap/podman/socket与Coq image/ID、0<started_ns<finished_ns。它支持当时本地image inspect成功，不声明现在重探测过socket/容器。
- PREPARATION_REVALIDATION为PASS，三方inode交集均0、COMPLETE且hashed=expected_files=4627、已核对probe数3、baseline_created=false/formal_gate_execution=false；三个helper摘要与当前源一致。源码只重读/核对既有probe，不重启probe；输出是汇总，不另保存一次完整collector。
- Parent给出的prepare proc_86af25d7b9ff与revalidate proc_4ee05022e93c退出0、identity/endpoints退出0与成功产物相容。已检查R/readiness没有独立外层四命令process/stdout封装回执；现行消费者也不要求此种额外文件。不将Parent提供进程事实冒充本reviewer读到的原始外层log；实际可读原生日志为clone和Lean probe。

## 当前hash
- `RUNTIME_BINDING.candidate-formal-002.r12.final-004.json`：`2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3`
- `EXECUTOR_IDENTITY.json`：`6ce755b2b6e32120a6eac5c3911da0152d75fe8beec83557170348d6c89f8193`
- `namespaces.json`：`0b542963316f92d2ee1ee4e8d11455046a750c2b532cd83bba2e57d9c78d8615`
- `bindings.json`：`e72ca3f9fb67524fe535b5299300f982f5c56663c14950b877425913a4114283`
- `source-recovery.json`：`de16a811204f92c51f63f42b485941948c9d805178ae02f8eb2db27719713f2f`
- `lean-materialization.json`：`e0a6d2426a25fe9fbaffd3bdd79d20deaa5fde5578e9a2ed13dd19996071a6cc`
- `preparation-collector.json`：`5d226fd518c420589e2d9a1ed424547c8280510089f7d675010cd0a4cab59cb7`
- `PREPARATION_COMPATIBILITY.json`：`eb9588a46d4481d9c2635f87d941e89444cb7b6b19e14b17a385c478df437664`
- `prepare.json`：`0ecdf3c36ef6f318318a22a9b9002c3ed651f68aa45d7ad1f49516727415ea78`
- `PREPARED_ENDPOINTS.json`：`be2fbddccea28d25c65cd819d2ce4396165a0b1a5e713dc3ba58e4fb9b39e179`
- `PREPARATION_REVALIDATION.json`：`ce2ddf7a5f1664b74292461f0c0606107d50c809b512d6fe927c326784b93630`

## 尚未闭合的既有seal要求（不得用formal试错）
1. Parent实施审查文件已为PASS、独立最终接受PENDING；两份r12报告和binding引用hash一致。本advisory不替代Parent最终合并处置或未来工程独立接受。
2. 当前PREPARATION_DISPOSITION.json不存在，Parent实际指令预加载及最终disposition仍待完成。Parent输入必须真实包含result=READY；instructions_preloaded/no_governance_during_window/no_unrelated_activity_during_window三个true；pending_required_instructions=[]；new_required_instruction_action=STOP；external_process_nonwriting=NOT_ESTABLISHED；非空且真实已加载、仍存在的preloaded_instruction_paths。不能借用子代理已加载事实。
3. 现行driver生成disposition后，回读schema=ep19-preloaded-preparation-disposition-v1、run_id、上述完整语义；basis必须是7个准备文件+runtime identity+qualification+executor/tools/candidate-inputs-v3/qualification文件+binding.closure的当前摘要；instruction_inputs非空且当前吻合；instruction_inventory对应实际捕获。必须满足0<endpoints.finished_ns<prepared_ns<=当前时间。CLI exit0不等于sequence.verify全部条件成立。本轮未读取共享instruction/bookkeeping树，未代签inventory。
4. 保持最终source/binding/qualification/matrix/候选、私有eligibility既有合并结论及工具许可/owned资源有效；完成seal后不得再加载新指令或变更输入，确需新指令即STOP。本轮未重读private map/inventory正文或证明其语义，保留既有loader及Parent审查范围。
5. 不新增全机无writer证明，不扫描/停止无关进程；保留NOT_ESTABLISHED。不重跑已成功准备步骤，不删除namespace/残片或换ID。正式consume在policy/baseline之前；不能用缺START返还预算。只有全部既有条件闭合，Parent才可独立提交唯一剩余正式调用。

## 历史、预算与限制
本轮观察FORMAL_ATTEMPT/BASELINE_ATTEMPT/LAUNCHER_ATTEMPT、baseline、seal、runtime START/RESULTS均不存在，runtime未获得产品门禁结果。正式未调用与预算1/2沿用Owner/Parent明确事实；marker不存在只是本地佐证，不是普遍预算返还算法。8000身份/29 skipped仍仅EXPECTED。r11实际prepare exit1/AttributeError及其失败报告完全保留，不能被r12成功追认。工程通过、最终独立接受、EP19关闭均未宣称。

审查中一次clone日志判断误假定Git缩写为9字符，实际日志为a2986434；按完整HEAD及实际原生缩写修正reviewer谓词，三项通过，没有改动候选日志或隐去候选失败。此前宽输出截断后采用定向源码/结构化读取；未将截断当证据缺失。

只写本actual-preparation-review目录：本报告、MACHINE_CHECK.json、SOURCE_HASHES.json、MANIFEST.sha256；未改实现/历史/共享Skill或Memory。遵守限域，不另写共享技能。
