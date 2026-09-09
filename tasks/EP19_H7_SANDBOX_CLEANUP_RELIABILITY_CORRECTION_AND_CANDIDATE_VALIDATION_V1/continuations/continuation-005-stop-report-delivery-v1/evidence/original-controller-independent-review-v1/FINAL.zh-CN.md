# 原 canonical controller CP-01..04 既有独立复核

## 裁决与边界

**REJECTED。CP-01、CP-02、CP-03、CP-04 均有实质修正，但均未完全关闭。** 本报告延续 `control-plane-independent-review/FINAL.zh-CN.md:19-70` 的四项 finding，不创建新 gate、框架或 review program。不批准安装、live 登记、formal 消费、slot、direct-FF、publication 或 closure。

确实支持的 controller 局部能力是：在原 controller source copy 中合并 acceptance；queue/ledger/slot 主事务共锁、journal、版本与同 payload 重放；a298 专属 SlotControl 分支；读取并哈希 JSON evidence；三原目标 expected-before 检查。**这些局部支持不等于 controller scoped PASS，更不等于集成 readiness。** coherence `final-006` 仍为 **REJECTED**（`coherence-independent-review/FINAL.zh-CN.md:5-7,50-55`）；`integration_ready=false`、`formal_ready=false`、`real_readiness=BLOCKED`。

下述简写均相对 `original-controller-correction-v1/`：
- C = `candidate/scripts/canonical_publication_control.py`
- P = `candidate/references/protocol-v1.json`
- T = `candidate/tests/test_canonical_publication_control.py`
- I = `parent-handoff/INSTALL_AFTER_COORDINATION_AND_REVIEW.py`
- IT = `tests/test_install_handoff.py`

## 独立静态核验及证据等级

已读取原 rejection、corrected FINAL/machine report、allowlist、实际 candidate/before source、protocol、patch、installer、installer manifest、保存的 native 日志、qualification、受影响输入说明及 coherence rejection。未 import/执行 candidate、installer 或 tests。

独立重新计算 `MANIFEST.sha256` 的 **76 条、76 个唯一文件：全部 match，缺失 0，失配 0**；全部位于 correction 包内，覆盖除 manifest 自身之外的全部文件。manifest 自身 SHA-256 为 `a0ab41c61a26aa72c08f575d246fb99199ac1797e38800bf8776ec93d59c150e`。这证明所审字节完整性，不证明生产者真实性或运行时充分性。

对 `ORIGINAL_TARGETS.patch` 做纯内存 unified-diff 重建：逐条上下文/删除行与 preserved before 比对，三个输出均逐字节等于 candidate；没有执行 git apply、写临时树或运行测试。patch 仅三 allowlist 原目标，三份 before/candidate 摘要与 install manifest 相符。

| 对象 | 独立计算 SHA-256 |
|---|---|
| controller | `a58cccd502c9f4ed704c6d4396fe03176c9f2115c7a14e2beb486eda3ceeca65` |
| protocol | `121d90bb0e0af61f18800d084ed719ddef46c414fd778a23ea45b6744c787065` |
| existing tests | `2f53760e97f91add87c45786e5ac974bb9fbc94f462ea54483328b39865177bd` |
| patch | `b0288047b1d09d8af8f78ee7aa73ec9bb39258241feb01010d500f123a5d1ebf` |
| installer | `0f5770e2c6928fb07626981c7f920c95226da97a9e8621cf8cc6f2f87ecee051` |
| install manifest 文件 | `903573f485e3db2da761b3b51da6aa306043d4b0c6427e8de9966e9afb2d2c17` |

保存的 native evidence：predecessor 29 tests/exit 0；RED 34 tests、1 failure/4 errors、exit 1；GREEN controller 38 tests/exit 0；installer 4 tests/exit 0。对应 `green/results/predecessor-regression.stderr.txt:1-34`、`red/results/reproduced-unittest.stderr.txt:36-83`、`green/results/candidate-unittest.stderr.txt:1-43`、`green/results/installer-unittest.stderr.txt:1-9` 及各自 exit-code 文件。静态 AST 的 before/candidate/installer test 定义数分别与 29/38/4 相符。保存 compile/JSON/git-apply-check/git-apply exit 为 0；保存 patch-program 尝试 exit 127，stderr 是 command not found。它们都是**既存生产者运行记录的读取**，不是本复核新执行或对来源的独立运行证明。

## CP-01 — PARTIALLY_CORRECTED / NOT_CLOSED

### 支持
C:173-210 的同一 state lock 与 journal/sequence 拒绝已被 QueueControl.load/get（567-585）、SlotControl.load/require_holder（673-726）、EP19 inspect 初始读取（1024-1026）复用。主事务在锁内读取、查 replay、查 expected-before（238-252），统一 journal → queue → ledger → slot → 验证 → clear（267-288）。acquire/freeze/release 主 mutation 也已进入该事务（691-717、759-783、791-805），正常 slot 操作外层 slot lock、内层 state lock，不再是原第二 writer。

### 剩余阻断：并非 ALL 原 reader 同域 fail closed
1. **原 `stable-state-readback` 仍绕过事务。** C:95-109 仅对任意路径连续两次读 bytes 并输出 PASS，CLI C:1614-1618 直接调用；不取 state lock、不检查 journal、不比较其他 authority sequence。在 `AFTER_WRITE_1` 留下 queue 新/ledger 旧的稳定 partial 状态（C:279-284）时，它仍可对 queue 或旧 ledger 输出 `STABLE_STATE_READBACK=PASS`。因此“所有原 reader 拒绝”的 FINAL:9 与 QUALIFICATION:48 过强。
2. **inspect 混合快照。** C:1025 调用 read 后锁已经释放（208-210），1031-1032 才逐个重算 queue/ledger 摘要；可返回旧 CURRENT_STATE/sequence 配新甚至 partial authority 摘要。installer I:179-181 正消费此 readback，却仅检查 COMMITTED。
3. **identity_readback 的授权窗口未覆盖输出。** C:979 经 load 验 holder 后 state lock 即释放；之后比较 caller observed SHA 并在 C:1005-1006 写 PASS。并发 release/transaction 可在两者之间发生；没有最后同域校验。不能把它作为同次持锁的完整 readback。
4. recovery C:304-322 只校验 journal 自报版本、before/after 摘要，再迭代其任意 AFTER；没有固定三 authority 集合、完整 journal/sequence/event 结构验证和恢复后 `_read_locked()` 验证便清 journal。此外 `_read_locked` C:188,198 允许 slot 缺失时 queue/ledger reader 继续。需要使恢复及缺失/不确定状态也符合既有完整性要求，而非只证明一个正常 journal 可 roll-forward。

T:504-521 只覆盖 QueueControl/SlotControl 两个 reader、一次 AFTER_WRITE_1；T:544-560 名为 concurrent original writers，但实际上两线程都调用同一个 acceptance.register_successor，不是 QueueControl writer 与 SlotControl/acceptance 的交叉竞争。不能凭 test 名称宣称 ALL-reader、跨原 writer 资格已完成。

## CP-02 — PARTIALLY_CORRECTED / NOT_CLOSED

### 支持
P:97-110 固定 a298 candidate/tree/parent/patch 和专属授权；C:908-920 确实读 authoritative successor、held slot、exact candidate/tree 与 fresh-main 一致性。C:921-930 将授权写入原事务，C:951-965 从特定 PUBLISHING 状态记录 canonical readback。普通 C:808-861 仍要求 frozen integration、ordered parents，签发 EXACT_NORMAL_PUBLICATION_ONLY，未改成普遍 direct-FF。

### 剩余阻断：真实 entry/state ordering 仍由绕行完成
工程接受 C:1207-1224 仅解决依赖、设置 review 状态，停留 READY_FOR_CANONICAL_QUEUE；queue → acquire 后是 SLOT_ACQUIRED（C:711-714），但 direct-FF 入口 C:911 要求 APPROVED_FOR_PUBLICATION。P:27-34 没有专属 slot→direct-FF-ready transition。实际“整链测试”T:600-606 通过通用 `QueueControl.transition` 顺次宣称 INTEGRATING、VALIDATING_INTEGRATION、FROZEN_FOR_REVIEW、INDEPENDENT_REVIEW、APPROVED_FOR_PUBLICATION，**没有调用 freeze_integration 或独立 publication review**。C:605-622 对这些 transition 仅查图边/候选不可变/部分依赖，不验证冻结对象、held slot 或 evidence。因此不是“没有方法”，而是 methods 之间缺少合法、受约束的 exception ordering；synthetic green 是靠无条件状态推进跨过去的。

同一个通用 transition 还允许 PUBLISHING→CANONICAL（P:35；C:614-621）而不调用 publication-result consumer，故“只能凭真实 canonical readback 进入 CANONICAL”（corrected FINAL:10）不成立。正常两父 authorize 校验仍受支持，不把上述状态绕过误写为普通 authorize 已放宽。

CLI C:1657-1664 虽先读 `--queue/--entry`，C:863-933 的 direct-FF 方法根本不使用传入 entry，而是按 policy successor 在另一个 `--state-root` 内查找。指定不同 entry/queue 不会构成对操作目标的精确绑定。该真实 publication entry 应拒绝目标不一致，而不是忽略调用方 entry。

此外 ancestry/race/remote 在 C:879-896 先于 slot/state 锁读入，只有固定字段比较；没有观测时间、原始命令回执、repository/ref、slot 获取实例或 publication transaction 绑定。canonical readback C:947-950 只匹配 candidate/tree/actor，未绑定本次 authorization 或观测发生在授权之后。同一旧 receipt 可以在同 actor/同 candidate 的另一次授权中被接受。控制器可以保持不执行 Git，但必须消费受信且绑定本次阶段的真实外部执行回执；不能将 caller JSON 本身当成真实 fresh/no-race/readback。该问题与 CP-03 相交，不新增 finding。

## CP-03 — PARTIALLY_CORRECTED / NOT_CLOSED

### 支持
C:123-144 确实读存在的 JSON 文件、比对 SHA-256；formal C:1134-1158 检查 exact gate 集合/顺序/native 字段，engineering C:1211-1218 绑定 formal/controller 摘要，closure C:1248-1256 绑定 sanity/canonical 摘要。缺文件、假摘要语法、NOT_RUN gate、错 executor 等部分负例有静态实现支持。formal failure C:1170-1196 保留 NEW_USED=1、failed 状态；C:1125 防止再开始。不能再沿用旧“完全不读 bytes”的描述。

### 剩余阻断：匹配 caller 提供文件与字段不等于 evidence provenance
- admission C:1036-1068 只验证 caller JSON identity 的 schema/candidate/可选 tree，其所谓 implementation_sha256 是 **executor identity JSON 文件**的摘要，不是所执行代码/完整受接受依赖闭包的验证。没有从固定的 accepted executor/config/policy authority 派生期望身份。`fixture_only=false`、route_ready 等亦为 caller 布尔值。T:451-465 用极小自建 executor/config/policy JSON、fixture_only=false 就通过，没有 native executor/provenance。controller 自身 hash 确有核验，但不足以令任意 executor identity 变成已接受来源。
- formal gate C:1148-1156 不要求 gate 的 attempt/run、config/policy、START/consumption receipt、raw stdout/stderr/command 身份；executor_actor 只需非空，未与 state FORMAL_ACTOR 对齐。seal C:1157-1158 仅 schema/result/candidate/tree，连 fixture 提供的 executor_sha256 都未核对。bundle gate_order 数组是声明顺序，不是执行次序证明。
- engineering/closure 的 reviewer_role 和 reviewer_actor 仍由 caller 文件/CLI 给出；C:1217-1219、1255-1257 的不同字符串不证明独立执行者/受接受 reviewer route。普通 publication review C:634-637 也仅做同类字符串匹配。
- sanity gate C:1235-1241 没有绑定执行器/实际 publication attempt/发生在 canonical readback 后；CP-02 所述 ancestry/race/readback 也不消费可追溯原始运行产物。

T:468-485 手工生成全部 formal gate/seal PASS，T:607-620 手工生成 ancestry/race/remote/canonical/sanity/closure PASS，最后 T:621-622 成功关闭。这些是**真实存在且正确哈希的 synthetic JSON bytes**，不是证明其内容由指定 native producer 执行得到的真实 evidence。原生日志的绿色只能支持 parser/transaction 在这些 fixture 上的行为；无法补足原 CP-03 的“no self-report PASS”。修正应消费既有受接受 producer/attempt/原始回执与精确 binding，不要求另建密码签名体系或新审查框架。

## CP-04 — PARTIALLY_CORRECTED / NOT_CLOSED

### 支持
install manifest:7-22 是 actual shared Skill 三个原位置，不再安装第二 controller。I:69-88 解析 review body 的 decision、target、patch、installer、manifest 身份，不接受环境 APPROVED；I:99-120 先检查所有 source/target 的 original-or-identical 字节；I:121-136 可从 journal 重放并做最终哈希 readback。C:240-252 的同 payload replay 在旧 expected-before 之前判定；I:170-181 不再以 successor count=0 阻断重放，且通过 original controller 登记。

### 剩余阻断：恢复性不等于安全激活或 CAS
1. **部分激活没有 reader interlock。** manifest 先列 controller，后 protocol/tests；I:121-132 逐个替换。中断在第一个目标后，新的 shared executable 已可由原用户启动，但 protocol 仍旧；journal 只在 task-local parent-handoff 内，C:28-29,559-565,1013-1016 不检查安装 journal/version pair。即便通常 EP19 初始化会因旧 protocol 缺 key 失败，普通 queue/slot 操作已可按新 controller 行为运行，不能称整包尚未激活。已运行的旧进程也不会因替换文件自动采用新 state lock。文档“先协调”不是覆盖切换/中断/恢复整个窗口的持久消费阻断。
2. **expected-before 不是并发 CAS。** I:123 读 digest、124 检查，到130调用 atomic_write/54 os.replace 之间没有共同 installer/maintenance lock。其他维护者可在 check 后写入 unknown bytes，再被 replace 覆盖；两个 installer 对同一 journal 也未串行化。最终 digest match 不证明期间没覆盖第三方内容。必须在既有安全协调范围内保证所有相关维护/运行者停止并保持排他，不能仅增加一次哈希或只锁本脚本。
3. **恢复 journal 未重新绑定 exact targets。** I:93-96 只检查 journal 顶层 manifest_sha256，I:121-130 直接使用 journal 自己给出的 target/before/after/base64/mode；没有把每行路径、数量、顺序、before/after 与已批准 manifest 逐项比对。自洽但错误的 journal 行不能作为 reviewed-target 权威。
4. **实际安装早于 admission/登记资格。** I:166-178 先 review、安装，再 controller 验 admission/expected queue/ledger；缺失/无效 admission 或 stale state 仍可留下已激活共享代码。当前 `PARENT_INSTALL_AND_REGISTRATION.md:3,10,14` 和 affected binding:3 要求这些条件先满足，脚本未把协调、coherence 接受与 admission 前置落实为安装前验证；I:170-171 还会在发现任何同名 state journal 时自动 recover，未核对是否为本次登记事务。不能将“已授权必要原 controller 维修”扩成“任何 partial state 均可自动恢复”。

IT:37-56 只对三个临时普通文件制造一次中断再重放，不启动原 reader、不覆盖部分激活/并发 unknown overwrite/恢复 journal 与 manifest 不一致。IT:16-23、25-35、58-65 亦不是 `main()` 的 install→recover→register→inspect 端到端中断测试。没有 successor-count-zero 是有用修正，但不构成完整 handoff 幂等与安全协调证明。

## 集成影响与有限处置

保持原四项有限修正要求：补全同域 reader/recovery 与精确 readback；约束 a298 专属真实 entry/state ordering，禁止通用 transition 绕过 acceptance；将 JSON 完整性进一步绑定既有真实 producer/attempt/受接受 source，而非 caller 自洽字段；使原三目标安装在整个切换/恢复窗口排他且 fail closed，恢复严格绑定 manifest，安装前落实现有资格条件。这些仍回到本次 CP-01..04，不新增 gate 或产品修复范围。

`AFFECTED_INPUT_REACCEPTANCE_AND_BINDING.json:22-56` 已诚实列出 coherence 的四项纠正/重接受/重绑定依赖；它不是这些依赖已完成的证据。原 second-writer b8c1d9 binding 不得复用，7 packages/107 members/15 instructions/105 exact reuse/2 accepted changes 的既有精确语义输入也不能被较小自洽 JSON 替代。当前 controller 被拒绝与 coherence final-006 被拒绝是两个同时有效的事实；不能把其中一个“有局部支持”翻译为另一个已具真实 admission/formal 路径。

固定产品候选 `a29864343ed4f630b052c20d86c23b240f13cfd0` 不变；历史 formal 2/2、新额度 total 1 / used 0、global next ordinal 3；产品新增修复 0。本复核没有消费或改变任何预算。`FINAL_AUTHORITY_READBACK.json:3-16` 中 shared/live hashes、successor 0、旧 old86d6 RELEASED_FAILED 是保存的 writer readback，本复核没有新读 live authority 来把它冒充当前独立测量。

## 本次实际操作

仅静态读取、SHA-256/JSON/AST/patch 字节核验，及在指定 `original-controller-independent-review-v1/` 中写本报告与 `VERDICT.json`。未执行 tests/probes/loader/installer/git apply/formal/product/admission；未访问网络或凭据；未写 live queue/ledger/slot、共享 Skill/Memory、源代码或历史报告；未新增 gate。既存测试结果已明确标为 saved native evidence；本次执行验证限于静态完整性计算。
