# r12 Part B：资格、v7依赖与parent实际准备交接静态预审

## 结论
**SUPPORTED_EXACT_FINITE_PREPARATION_CONSUMER_SCOPE；parent 实际准备仍待执行与逐步回读。** 未在本次审查范围发现需要重开实现修复的具体可达阻断；不是对完整准备必定成功的保证，更不是最终独立接受、formal启动回执或EP19关闭。未调用loader/test/probe/prepare/formal、未导入被审代码、未读取共享bookkeeping或凭据、未读取绑定private map/inventory正文。私有eligibility语义本轮仅审consumer源码及已有loader证据，不能称本reviewer独立重验过私有数据。

读取完整Owner授权、writer/r12 packet、r11 readiness与失败诊断、两份r11报告、r12 final-002 report/index/handoff、final-004 binding及直接源文。r11真实parent proc_f7a8bc56f5cf prepare exit1/AttributeError仍是历史失败，reason摘要97863e69ab6779d2ba89485b262716ae8d167eca604f7e3536880eff0c10a790不被新GREEN改写；旧loader PASS不升级成旧prepare PASS。

路径：J为本continuation；T=J/implementation-r12/tooling，E=T/executor，W=J/writer-evidence-r12，R=T/outputs/continuation-runs/candidate-formal-002。

## 1. 独立身份及来源核对
从测试class/method AST独立重建179 unique，与expected、RESULT、PROCESS完全一致；源码固定mandatory字面集94，全部在实际集合。native日志解析179 unique且逐项ok；RESULT全部PASS；missing/unexpected/duplicate/fail/error/skip均未出现。native/wrapper=0/0。不是只看tests总数。qualification-005的121文件before/after及当前tooling宇宙完全相等，QUALIFICATION.dependencies保存的5项hash逐一吻合；覆盖真实raw/process/result引用。

source snapshot实际副本核验：RED82/侧、GREEN82/侧、integrated121/侧、loader123/侧，全部snapshot bytes hash=source_sha256=snapshot_sha256，两侧稳定。审查前后E/qualification选定源码hash无变化。端点快照不证明运行中绝无瞬时修改；PID是writer子进程命名空间观测，不是独立系统证明。

final loader NATIVE JSON=VALIDATION JSON，两个hash与PROCESS一致；validator源文确实调用coverage.qualification_inputs、dependency.validate、verify_required_runtime_files和execution.verify_object_source→identity_delta.validate；它没有运行prepare。

## 2. 精确binding与两类delta
唯一文件 **W/RUNTIME_BINDING.candidate-formal-002.r12.final-004.json**。
SHA256 **2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3**（独立字节计算）。
qualification=a5e305305bca2c30b036d5d480042efc5feb3644b9e2336a77a39a7cad00bb4e；dependency=105046378b144d9ca0c6f9de4b0f0f6e3f7f31fdf3ffc0c7f66879911355d8e6。

runtime schema=ep19-external29-runtime-binding-v2：严格完整key集合；reviewed_delta旧字段不接受；product_identity_delta与external_implementation_delta各强制path/sha256，exact_path而非宽松path别名。固定candidate/tree/parent/base/patch、唯一run ID、29唯一matrix、inputs完整宇宙、source_binding全121文件、各输入hash及v7强制检查均保留。当前binding两类delta分别与v7 sources对应项完全相等。

product_identity_delta指向任务candidate-preparation/native-delta-001/DELTA.json，hash4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e。它是ep19-cleanup-identity-delta-v1；source/JUnit/native receipts所指artifact hashes本轮核验匹配。execution只把这个字段交给身份consumer。consumer保留tree/diff/source blob、原生argv/cwd/time/exit、JUnit身份/状态及classifier校验；历史27身份并非fresh产品门禁。
external patch只作执行器差异：IMPLEMENTATION.r11-to-r12.final-004.patch，hash5abeb7f1df5cdd484ee67e82eee639769397dfe577cb68aada6e45f322bb0ea8，不进入产品JSON解析。OLD_TREE补回仅供adjacent inventories；legacy bc.authority缺项在当前integration-qualified-v2提前return之后，不把legacy路径宣布已获资格。

## 3. 实际私有CLI范围与v7有限图
test_r12_actual_prepare实际子进程prepare，经parser→modules→binding→runner.prepare→verify_object_source→identity_delta.validate。fixture只改嵌套祖先定位与qualification前置为显式sealed private source check；未mock掉上述目标validators。正控CLI本身exit1/FileExistsError，在预先存在sentinel处停止；测试方法GREEN是0，不是prepare成功退出0。负控错patch/错schema/错candidate/错hash/缺字段/错config seal拒绝。**namespace creation、clone、parser复制、Lean与container准备未由这个控制执行**。这正是有限前创建consumer证明，不是整个prepare端到端证明。

静态独立重建v7 lexical local-import graph为39 nodes/126 edges，与保存图完全相等，source_nodes hash相等；新增6条语义边可在实际源文找到，包括prepare→verify_object_source及产品JSON与外部patch的分离。ledger仍只为OBSERVATION_INTEGRITY_ONLY，授权/指令选择/候选/gate/rollback来源均false，未知reader继续拒绝。

边界：reachable_local_graph只搜索executor/qualification，不包含tools/revalidate_preparation.py（真实driver通过tools sys.path导入）；该文件实际已在全source_binding封存，且本轮读取实际入口/产品consumer。不能把39节点图称全Python/stdlib/第三方/prepare后所有活动的完整运行证明；此有限图限制未构成当前证据缺失或绕过，不新增全机依赖门禁。

## 4. Retained AR001..010与限制
AR001连续窗口/strict祖先，AR002 V2 temp metadata及cookie生命周期，AR003墙钟/单调窗口，AR004原始JSONL framing，AR005合法usage后不变边界，AR006无摘要注入，AR008失败锁存及原原因ownership，AR009目录链耐久，AR010受控有界捕获保持r11精确处置；AR007只扩展上述真实prepare consumer。核心driver/bookkeeping_v2/v3/boundary/capture/durability/adapter/native_observe/sequence/coverage/Lean/namespaces均与r11字节相同，旧控制均进入fresh179。不能把有限stderr故障控制升级成OS断管/全域耐久证明；decision/baseline legacy emitter保留静态支持层级。

native29/H733、原生门禁超时、64MiB prefix/128 records/1MiB line/8MiB append/4096 manifest/128 packages/每边界3次5秒/4096 pending不改；无3600秒整attempt cap。Owner接受ledger捕获间overwrite-restore/truncate-regrow观察限制，不重开也不扩展到其他protected对象。

## 5. Parent顺序实际准备与回读接受条件
精确解释器：USER_HOME/.hermes/hermes-agent/venv/bin/python3；coverage比较sys.executable完整字符串，不替换成系统python或resolve后路径。driver=E/external29_driver.py。
按W/PARENT_HANDOFF_COMMANDS.r12.final-002.md，逐条单独执行，公共参数严格为：
`--run-id candidate-formal-002 --binding "$J/writer-evidence-r12/RUNTIME_BINDING.candidate-formal-002.r12.final-004.json" --binding-sha256 2bfe0792c93fb55859f95c672d9c75dde6083dae536d8092c8999dfb8e393dd3`。
命令形状：`"$PY" -B "$D" prepare|identity|endpoints|revalidate|disposition [上述公共参数]`；竖线只是本报告枚举，不是shell命令。disposition额外`--input /absolute/parent-owned/PARENT_DISPOSITION_INPUT.json`，必须用parent真实文件替换占位符。不得整块无条件投递。

1. prepare：首轮确认R不存在、精确binding hash、解释器可执行。0退出后回读prepare.json result=PREPARED_NOT_BASELINED、固定candidate/tree、formal_gate_execution=false；namespaces三份独立clone无hardlink/alternates，bindings29；source-recovery；parser闭包；lean-materialization/preparation-collector/PREPARATION_COMPATIBILITY。compatibility PASS/not_baseline、strict collector COMPLETE且hashed=expected、run-local Lean无symlink、三个原生probe exit0及日志hash/输出/system_fallback=false。真实prepare有clone/复制/Lean --version、--print-prefix、PreparationProbe.lean bwrap运行等owned副作用，不能称无命令准备。
2. identity：回读implementation-r12/evidence/EXECUTOR_IDENTITY.json的identity_basis和canonical JSON摘要，stdout PASS。identity是运行时basis摘要，**不是直接把binding hash抄进去**；旧r11 parent review不能自动沿用。
3. endpoints：PREPARED_ENDPOINTS result/checks PASS、run_id、真实started/finished、固定bwrap/podman/socket及本地image inspect匹配。非pull或服务操作。
4. revalidate：T/tools/revalidate_preparation.py生成PREPARATION_REVALIDATION，schema ep19-lean-preparation-final-helper-binding-v1；PASS，strict collector COMPLETE，三方inode交集0，已有三个probe receipt hash/exit重新核对，baseline_created=false、formal_gate_execution=false；它不重跑probe。
5. disposition：输出R/PREPARATION_DISPOSITION.json，schema ep19-preloaded-preparation-disposition-v1、正确run_id；basis含7准备文件、runtime identity、资格及输入封存，当前字节吻合；非空实际instruction_inputs，instruction_inventory有效；0<endpoint.finished_ns<prepared_ns<=当前时间。CLI退出0不足以代替sequence.verify所有字段的回读。

Parent输入最小完整语义：result="READY"；instructions_preloaded/no_governance_during_window/no_unrelated_activity_during_window均JSON true；pending_required_instructions=[]；new_required_instruction_action="STOP"；external_process_nonwriting="NOT_ESTABLISHED"；preloaded_instruction_paths为parent实际已经加载且仍存在的非空绝对文件路径数组。不得用writer/reviewer已加载代替parent事实，不为全机无写入作证明。disposition生成真实共享instruction inventory，不在本reviewer权限内执行。

Parent implementation review consumer要求implementation_review="PASS"，independent_final_acceptance为"PENDING"或"REQUIRED"；由parent合并分项后真实生成，不是本advisory自签。建议附证据hash是来源说明，非新增consumer key门禁。相关parent记录放T外，避免破坏全文件source_binding。

## 6. 残余条件、namespace与预算
本次只读exists观察R不存在；没有调用任何准备/formal。剩余条件是parent合并本报告与part-a、私有eligibility的合并处置、当前工具许可和owned资源、真实预加载与parent记录、上述五步的实际产物接受。没有用旧r11 readiness“只剩运行”的说法掩盖前创建缺陷：该缺陷在r12仅获得精确修正与有限新资格支持。

每条失败/缺失/残片/不一致立即停，保留现场；不删除namespace、不改ID、不盲目重试。prepare尚未formal consume不代表允许重试；成功receipt常用O_EXCL。formal在policy/baseline之前consume ordinal2/total2，可能留下空/partial marker；无START、无成功baseline、无failure marker均不返还预算。不得用formal试探disposition字段，也不得第三次尝试。

只有所有既有条件由parent闭合后，才按同一handoff的独立formal命令（额外真实--review、r2 --applicability、private-r12 --private-map/--private-inventory）使用剩余一次；本报告不调用它，不请求同范围重复授权。产品预算3/3、formal1/2保持；29门仍0 PASS/0 FAIL/29 NOT_RUN；8000/29仅EXPECTED。最终真实formal对账、最终独立接受及权威closeout仍待完成；EP19_CLOSED=NO，无产品发布。

## 文件与工具问题
仅写part-b：EARLY.zh-CN.md、CHECKS.early.json、STATIC_CHECKS.json、SOURCE_HASHES.before/after.json、本报告和MANIFEST.sha256。曾误读qualification/revalidate_preparation.py得到FileNotFoundError，已按实际driver定位tools/revalidate_preparation.py读取；不是实现缺文件。工具大输出曾截断，关键源文采用后续限定读取/结构解析。受限定写域约束未写共享Skill。
