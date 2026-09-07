# EP19 H7 启动拒绝证据与运行时保全边界续行报告

## 结论：B — 诊断修正通过资格；原路径保全仍需具体 Owner 契约决定

本次已完成授权范围内的诊断实现、父环境资格、支持隔离调查、运行时映射、组件复用账、独立 namespace 准备和条件 readiness。**没有创建正式 baseline/START，没有调用正式 run，没有执行产品门禁。** 当前条件评估为 `BLOCKED_OWNER_CONTRACT_DECISION_REQUIRED`，不是 `ENGINEERING_READY`。

新 namespace 的 prepare 指向已通过的**诊断资格**，该 schema 不是完整 formal-launch capsule。没有把历史 aggregate 改写成新版 PASS，也没有为解锁执行填入独立 ACCEPT。未来契约决定还须落实相应实现/资格及完整 runtime binding/preflight；仅批准本提案本身不代表可立即运行。

## 1. 身份、范围与来源等级

- Candidate BASE：`86d6aef94fd5e58da552e97c11473cff6eca734e`
- Candidate COMMIT：`689ab9456461a8d19a72d059f5157092efc43aff`
- Candidate TREE：`6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`
- 新 EXECUTOR_IDENTITY：`198ae4c300605046853a9a39d4e9307af2e4bd96b02e45a0bb53dd077282b6ef`，定义与全部输入见 `evidence/EXECUTOR_IDENTITY.json`。
- 旧 reviewed identity：`db414fda33a6ffa134b1291880ef1b1907fbe12e6b2a01d482830b4042296c4d`；原 observer SHA256：`2e060dd77ed4b24132d581e36cc3fa84c8b67d928cd9ec7689dcdc8823e991e2`。
- 只修改新的 task-owned executor 副本。相对原 preimage：`runner.py` 修改调用阶段、决策取证与源码 seal 完整性检查；新增 `decision_evidence.py`；`execution.py` 仅一行 O 绑定为原绝对 TASK_ROOT，其余字节精确不变。其余 **35** 个 helper 字节不变，工作 tools **343** 个文件与旧版本一致。
- 新资格脚本、账本和报告都在本续行目录。累计 diff、原 preimages、follow-up 源码 diff/清单、每次执行 source snapshot 均保存。公共包提供必要源文件/差异及本地 locator，不包含私有 Skill/Memory 正文。
- `03-大模型上下文-精简版.md` 已读取并记录摘要；它明确是项目决策上下文，不是代码、部署或测试证明。本任务不把 ADOPTED/RETAINED 当成实现或接受证据，不启动 notification、集成或 backend enablement。

## 2. 决策证据修正

实际调用路径为 `runner.preflight → compare_baseline`、`run_all → LAUNCH_PREFLIGHT → PRESTART`、`run_gate → GATE_BOUNDARY`、`run_all → FINAL_ACCEPTANCE`。所有比较使用同一份已读取的 baseline 和一次 Collector 返回的 current；这些值直接决定判定并进入回执，**不会另读文件后冒充原决定证据**。

回执包含 schema/run/candidate/base/tree、helper 捕获身份、scope 原字节摘要、baseline 原字节摘要、phase/gate、采集起止时间、before/current 元数据与摘要、路径/字段差异、missing/added/unreadable/unstable 及捕获/证据错误。START 使用 FD-relative 状态观测；不完整或非 regular 状态拒绝。进程历史默认 `NOT_ESTABLISHED`，另列本调用尚未启动 gate 的边界事实。

保存路径为新 run 的 `runtime/decision-evidence/`；校验与 protected、enumeration、frozen、repository/metadata 根及基线成员没有双向重叠。原/有效 scope 合并用于目标校验，不能通过 scope_override 删掉旧义务。拒绝 symlink/祖先替换；exclusive 新文件、写入/fsync 失败都不允许执行。部分写文件保留，错误进入异常/stderr；底层不可写时不能虚构“错误已可靠写入同一磁盘”。即使一个完整文件标记比较 PASS，也必须 writer 成功返回才能接受。

这些是顺序端点、有限 inotify 窗口，不是原子多文件快照或连续命令间观察；不证明全部 mmap、远程写或 writer PID。SHA/只读模式提供可校验的程序级 append-only 行为，不宣称文件 owner 无法篡改。后读诊断与原决定回执保持分离。

`qualification/EXAMPLES.json` 索引 **32** 份 disposable fixture 证据（包括 1 份故意部分写的原字节），全部不是 candidate product execution。旧 `owner-observer-restored-689ab945-v1` 的原始拒绝比较集合仍 **NOT_RECOVERABLE**；新能力不反补旧证据。

## 3. 实测资格、普通缺陷与复用

父环境：**45 methods / 45 PASS / 0 failure / 0 error / 0 skip**，native exit **0**，本次测试子进程实测 **12.904656 s**。真实文件/权限/observer 控制与明确的 injected 错误、mocked owner/preflight/昂贵 gate 适配在 controls ledger 中分开列出；fixture run_all/START 不算正式 START。

父环境另运行 4 项 CLI 绑定检查：当前资格验收 exit 0，旧初稿身份、旧 follow-up 身份、重复输出目录分别 exit 1，全部符合预期。这是 4 次 CLI 检查，不合并声称额外 unittest 方法。父面的同一 START 观测错误 probe 在旧快照中 exit 1（暴露漏拒绝），新 helper 中 exit 0（正确拒绝）；保留同一 probe hash、RED/GREEN logs 和 receipts，不重复计入 45 方法。

普通修正历史：初稿有 START 状态错误仍可能比较 PASS 的缺口，已在 seal 前按当前授权修复。followup-attempt-001 的两个失败是资格断言把 cleanup 描述当路径、把 tools 原目录定位错误；原 logs/source snapshot 保留，修正断言后父面验证通过。没有改产品来使测试通过。包汇编遇到故意 partial JSON 时的读取错误也单列记录，随后按原字节保留并明确分类。

复用只限已验证的组件行为：旧 focused **36** 方法、broader **81** 方法和 restored observer **25** 控制；旧 focused 4 项集成、broader 33 项旧 launch/assembler、本已 superseded 的 6 项、旧 binder 10 项不作新版 launch 证明。旧依赖 **42,389** 个字节记录已核验；新绑定另有摘要。旧 full runtime capsule 不直接复用：`execution.py` 整文件身份已变，即使函数 AST 全部相同，也没有重标旧 runtime receipts 为当前原生运行。详见 `evidence/QUALIFICATION_LEDGER.json`。

A/B/C 的算法和 enforcement helpers 保留，旧真实 Gradle/frontend/Lean/Coq 属历史组件证据，不是本次新产品 PASS。COMPILE 新鲜度、artifact 独立保存和打包映射当前均是**代码/资格保留，actual product result=NOT_RUN**。

## 4. 原运行时边界与具体未实施提案

当前配置的非敏感只读选择器为 HERMES_HOME=`/home/user/.hermes`、terminal backend=`local`、home_mode=`auto`，内建 memory/user profile enabled。没有更改 shared configuration。此环境选择器也不证明其他进程或 agent 内 ContextVar 的实际配置。

`preservation.INSTRUCTIONS` 硬绑定原 Skills/Memory 根；Collector 保护 kind、hash/blob 及 dev/ino/mode/uid/gid/size/mtime/ctime/nlink，递归 inventory 有 children。`coverage.derive` 保留原 protected 并加入全部指令成员；`Watch.classify` 对根下事件 `REJECT_INSTRUCTION_EVENT`；`compare_baseline` 对原 wanted 的已捕获字段不等拒绝；最后 seal/endpoint/observer 仍 fail-closed。现有 shared-object/SHADOW/确切 frontend ref 规则未变。

官方文档和已安装实现支持 HERMES_HOME、单次 profile 选择、内部 ContextVar 路由，但它们不能禁止仍指向 ORIGINAL 路径的并发写者。私有副本、bwrap 只读视图、另一 shell/cache/run ID、提前加载 Skills 都不能替代原路径义务。**本次未实施隔离，不声明完成 E2E 隔离验证，也不声称已排除所有可能的未来技术。** 实施位置、调用链、字段和资料差异详见 runtime-analysis 报告；6 个官方页面、18 项本地源码引用有来源摘要，父面已回读源 hash。

待 Owner 决定的精确措辞见 `evidence/BOUNDARY_DECISION.md` 和 `runtime-analysis/proposed-contract.json`，状态 **NOT_APPROVED / NOT_ENACTED**。核心是保留 OLD_PASS/OLD_REJECT，另行申请字段级、有可信完整事务证据的 bookkeeping 条件 reducer：

- 严格保护所有 instruction/support inputs、全部 memories、其他 Skills 成员/未知路径/未知字段；不是整个 Skills 目录豁免。
- 唯一候选为 `.usage.json` 已存在 record 的 view_count/use_count/last_viewed_at/last_used_at；其他字段与 record 集合不变。patch_generation/reuse_generation 变化仍拒绝。
- 计数须等于完整已提交操作账，时间须与受绑定事务一致；未知 writer、gap、overflow、incomplete、未登记 rename/temp/lock、权限或政策字段变化均拒绝。
- directory entry-set 与 metadata 必须逐事务因果对账，temp 必须精确登记且消失，lock 严格按基线处理；不能仅因“框架通常 rename”放行目录时间变化。
- 新结果最多声明 `ORIGINAL_STRICT_CONTENT_PRESERVED_WITH_ACCOUNTED_BOOKKEEPING`，不得声明 ORIGINAL 全字节/元数据不变。私人副本的 PASS 另列，不能替代原路径结论。

此提案目前缺少相应可信事务采集机制，未自动实现 reducer/allowlist。具体 adoption 控制、公开/私有声明、未知归因处置见完整提案。审批、实现、资格与独立接受是不同状态。

## 5. Readiness 与正式实际记账

新 namespace `owner-prestart-boundary-689ab945-v1` 已 prepare；新 backend/candidate-frontend/SHADOW 三个仓库均 exact candidate，各 **7,634** tracked 文件，Git metadata 独立、无 alternates/共享对象 inode。仅候选镜像，不访问独立前端开发 tree；ref 保持精确 `refs/heads/agent/frontend-wave2-product-ux-v1`，本任务没有其 source/gate/ref 操作。

readiness 在原契约隔离条件处阻塞。未建立新正式 baseline，未发完整 formal-launch capsule，未运行 runner 的 full technical preflight 或 formal run；没有伪装这些后续步骤通过。

**29 REQUIRED / 0 PASS / 0 FAIL / 29 NOT_RUN**。后端期望 7973（expected skips 29）、candidate frontend 期望149仅是既有 reference。实际 discovery/execution/pass/skip/fail/error 均 0；missing/unexpected/duplicate 对账未执行，不能用零充当已经对账无差异。完整逐 gate 与 identity 状态见 `GATE_ACCOUNTING.json`。

## 6. 历史、不干扰与限制

旧 5 PASS/1 FAIL/23 NOT_RUN、ARCHITECTURE exit -15、FAIL_PRESERVATION 保留；上一修正包 Outcome B/29 NOT_RUN 保留；最近启动拒绝仍为 `FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP`、exit1、无 START/29 NOT_RUN。没有刷新原 expected hash、恢复 timestamps/metadata、重建缺失文件或重标失败。

当前只读核验：旧 **4,686** 运行文件、**7,641** 失败现场端点、上一续行 **4,615** 控制/证据文件没有差异；这不是历史全程保全。`PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE`；旧 post-rejection 两端点差异的 writer 与当时完整拒绝集合仍未建立。

本轮没有调用 Skill/Memory 写工具或修改 instruction bodies/shared config；必需 skill_view 可能有 usage 记账副作用，工具 cache/log 也不全在 task root。没有本次完整 syscall attribution，不宣称所有 framework runtime 写入都被隔离，更不将历史差异归因到某个 agent。没有停其他进程、改全局权限或干扰 frontend lane。

## 7. Evidence-only 交付

本目录仅为 prepared public evidence。每个文件由 detached `MANIFEST.sha256` 覆盖（manifest 自身另在封包/发布回执中哈希），ZIP 与远端固定 commit 的验证由后续独立 publication receipt 给出。`FINAL_FIELDS.json` 的 publication 字段明确为封包时状态，不虚构尚不存在的 commit/hash。

完整发布后字段及 remote verification 将写入本地 `publication/FINAL_REPORT.md` / `publication/FINAL_FIELDS.json`，不回写此包。Product publication、post-publication sanity 均不执行。`EP19_CLOSED=NO`；`INDEPENDENT_REVIEW=PENDING/REQUIRED`；Roadmap #23 / Second Wave 不放行；`STOP=YES`。
