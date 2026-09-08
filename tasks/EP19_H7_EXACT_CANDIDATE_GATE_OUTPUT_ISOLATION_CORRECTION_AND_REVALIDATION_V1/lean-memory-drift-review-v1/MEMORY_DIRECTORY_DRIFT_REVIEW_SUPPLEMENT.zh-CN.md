# Memory directory drift：只读补充审阅

**结论：已记录的严格 Memory 根目录 ctime 漂移成立；不是独立接受，不改变历史 FAIL。** 正式图按原始 RESULTS 逐项统计为 **0 PASS / 1 FAIL / 28 NOT_RUN**。CHANGE_IMPACT 在命令前 GATE_BOUNDARY 被拒，原因 `FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP`；native_exit=null、wrapper_exit=1、retry_authorized=false。

## 证据路径约定
- continuation（C）：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/lean-materialization-20260908T025242Z`
- run（R）：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/lean-materialization-20260908T025242Z/outputs/continuation-runs/lean-materialized-formal-001`
- 决定性 receipt（D）：`/home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/lean-materialization-20260908T025242Z/outputs/continuation-runs/lean-materialized-formal-001/runtime/decision-evidence/1788839340790111066-74ccb49729b44df0b2aa11476c994db3.json`
- D SHA-256：`273a32bec8c7900d11962c8f7232f7ba0b87c8917b55ff8cd7e67e02481434d8`。
- 下文 C/R 相对路径均相对于以上精确根；JSON 映射保存绝对路径、字段、端点数值和源码行号。仅解析既有记录、检查既有源码字节，不导入或执行 executor；没有运行测试、collector、gate，没有实现 helper，没有发布。业务证据不取自 live Skill/Memory 正文。运行指令要求加载的审阅流程 skill 不构成被调查对象的现场证据。

## A. 路径与对象：root 不等于 file
漂移对象是 `/home/user/.hermes/memories`，`kind=directory`，不是 MEMORY.md 内容改变。D 的 `differences[0].fields` 仅含 `metadata.st_ctime_ns`：

`1788838990891651268 → 1788839301436583201`（整数纳秒，差值 `310544931933 ns`；这个差值不是观测持续时间）。

D 的 `before` 与 `current` 根目录记录：dev=47、ino=449121、mode=16832、uid=1000、gid=100、size=84、mtime_ns=1788837463612015274、nlink=1 均相同；仅 ctime 不同。根目录无 sha256/git_blob/children 字段。D.before 的全部五个 Memory 记录与 R/baseline.json `entries` 一致。

## B. 捕获区间、metadata、成员及内容覆盖
D `capture.start_ns=1788839306701721649`、`capture.end_ns=1788839337807331010`；`result=COMPLETE`，capture_errors/evidence_errors 为空。D 整体 `started_ns=1788839304426477684` 至 `finished_ns=1788839338319372949`，不等同于逐路径 stat 时刻，也不含后续 receipt 写入完成证明。

之前三张 receipt 的 Memory root ctime 都为旧值：

| phase | receipt 文件名（R/runtime/decision-evidence/） | capture.start_ns → end_ns |
|---|---|---|
| PREFLIGHT | `1788839157587406297-db828d7ac80d4b1ab1b63995524eed4a.json` | 1788839123227367027 → 1788839154558116998 |
| LAUNCH_PREFLIGHT | `1788839238457677258-01b91fc2207c4eb6854de701183d0cee.json` | 1788839204058076529 → 1788839235367961400 |
| PRESTART | `1788839283286278928-5b590409dce44a8d9e659404dc954416.json` | 1788839248876749684 → 1788839280283311578 |

最近 PRESTART 为 PASS，但不能遮蔽随后 GATE_BOUNDARY 的 REJECT。仅可把最近旧值采样与新值采样置于上述各自顺序捕获区间；没有逐路径时间，不把区间端点当成变更发生边界。R/baseline.json 只有 `time=1788839083.0041234`（秒），无 capture start/end；C/executor/runner.py:103–114 表明它是 snapshot 后构造 baseline 时的 time.time()，不是 Memory 采样时刻。不能用 preparation-collector 的较早区间代替 formal baseline 区间。

覆盖分层：
- metadata：`st_dev, st_ino, st_mode, st_uid, st_gid, st_size, st_mtime_ns, st_ctime_ns, st_nlink`；atime 不冻结、不比较（preservation.py:10–12、95–98）。
- 文件：`MEMORY.md`、`USER.md`、`MEMORY.md.lock`、`USER.md.lock` 的 kind、全部记录 metadata、sha256、git_blob 均逐字段相等。文件内容仅按历史哈希端点比较，没有读取或输出正文；具体哈希见 JSON A。这不是连续内容不变证明。
- 成员：scope.json `protected` 包含以上四文件及根；`enumeration_roots` 包含 Memory 根，但本次 decision 用 `Collector(files=...)` 重新捕获原 wanted 键（decision_evidence.py:59–64、190、207–209），不会递归重枚举；preservation.py:62–67、80–89 仅在 recurse=True 时记录 children。五个已知键复查不等于新建/消失成员的完整目录清单证明。
- 本边界没有连续 command-gap monitor，没有原子快照。端点相等不能排除期间创建后删除、修改后恢复等未记录中间状态。

## C. Predicate、receipt 与代码的同源绑定
D 控制身份 raw_sha256 已与保存文件字节比对一致：
- R/baseline.json：`5d67c8e2b1a8db9c25d38cfb3523ad8f276e30276c8ca1bc18638a2c5cac26cb`
- R/scope.json：`19fedc9f82136421c0ae0212eaaba29261d0217917e4830c63d888213906e1dc`
- R/bookkeeping-policy-v2.private.json：`50ec4403a5cacb7326677c989f6d23682d44851da9b528ef3cf4aa7714d027fe`

从保存值重算而非重新执行 gate：capture_complete=true；capture_errors_empty=true；usage hash/metadata、Skills root metadata 与 bookkeeping_evaluation 三项绑定均 true；`current == wanted` 为 false；排除 policy.target 和 policy.skills_root 后 `strict_current == strict_before` 仍为 false。

D 顶层：`OLD_STRICT_PRESERVATION_RESULT=OLD_STRICT_REJECT`，`V2_INPUT_INTEGRITY_RESULT=REJECT`，`V2_BOOKKEEPING_EVALUATION=PASS`，`WRITER_ATTRIBUTION=NOT_ESTABLISHED`，`claim=REJECT`。嵌套 bookkeeping_evaluation 的 input integrity PASS 仅为 bookkeeping 子判断，不能覆盖顶层 Memory 拒绝。

精确执行链（C/executor/）：
1. decision_evidence.py:31–56、181–193：读取控制文件实际字节及 metadata 并绑定；207–218：捕获和 bookkeeping 绑定。
2. :213、219–222：scoped 仅 usage 文件与 Skills 根；其余 strict map 不等即抛本次原因。
3. :239–255：同一 before/current 生成 differences 与失败字段；278–291：写 receipt 后重新抛拒绝。receipt 文件本身不独立证明 fsync 成功。
4. runner.py:276–285 在命令启动前调用比较；真正 observe.run 位于 :334；:389–396 保存失败 receipt。D `call_boundary=GATE_COMMAND_NOT_YET_INVOKED_BY_THIS_CALL`，原 RESULTS traceback 与这些行吻合；`gate_process_status=NOT_ESTABLISHED` 不应升级成全系统无进程声明。

decision_evidence.py、preservation.py、runner.py、bookkeeping_v2.py 保存字节 SHA-256 均与 D `executor_identity.entries[绝对路径].sha256` 一致，完整摘要见 JSON C。

## D. V2 例外不能扩展到 Memory
C/OWNER_AUTHORIZATION.txt SHA-256 为 `338a9449a678ab0de5e4a7167823e3fff983f38bac76e5deac3c029a1c4c9528`，与私有 policy 的 owner_authorization_sha256 一致。
- :66–80，尤其 :74：entire Memory scope 保持严格；:273 要求 Memory changes reject。
- :112–150：仅 exact `/home/user/.hermes/skills/.usage.json` 既有合格记录的 view_count/use_count/last_viewed_at/last_used_at 有界可变，其他字段深比较。
- :168–174：仅 Skills 根可在定义边界内放宽 size/mtime/ctime；身份、权限、所有权与最终成员集仍严格，禁止自动扩展至其他目录。
- :205–235：approved bookkeeping 可以 attribution unknown 而 PASS，不代表 strict Memory 也可接受。bookkeeping_v2.py:30–31、359–366 保持其自身严格字段及根成员集；decision_evidence.py:219–222 保留 Memory 严格比较。

因此本次不是单纯被 old-strict 误拦的 V2 合法差异，也不能用“正文哈希没变”替代整个 Memory 严格规则。

## E. Attribution 的证据限制
已建立：根目录 ctime 端点变动、四个既有 Memory 文件记录端点相等、该 gate 调用尚未进入 native 命令即拒绝。
未建立：writer PID/UID/进程/会话/agent 身份、具体 syscall、目录变动原因、期间成员/内容完整历史。D `OBSERVATION_LIMITS` 为 `NO_COMPLETE_WRITER_OR_SYSCALL_LEDGER` 与 `SHORT_LIVED_TEMP_CONTENT_MAY_DISAPPEAR_BEFORE_OPEN`；更一般的边界见 D.coverage_bounds。Memory 与 Skills 根出现相同 ctime 数值只构成时间相关，不能推出同一 writer。ctime 是状态变更时间字段，不是出生时间、操作名称或责任归属证据。也不能从本任务没有显式 Memory write 调用推导外部无人写入。

## F. 处置及最小下一步
保留 R/runtime/STOP.json、RESULTS.json、历史 receipt、原 public、delivery/public、原 ZIP，不改写或重新封装。当前结论是保存证据的静态复核，**不是独立接受、不是 gate 重跑结果、不是发布或关闭**；原 candidate_acceptance=PENDING_PARENT、independent_review=PENDING 不升级。

最小下一步：父控/独立审阅者裁决此已记录严格漂移。若必须查 writer，另行授权只读、按精确 Memory 路径和已记录时间定位的既有事件/syscall/进程记录审阅；若不存在相关记录，保持 NOT_ESTABLISHED，不编造归因、不用新的现场扫描“补证”历史。任何新采样、containment、baseline 变更或重跑须另定授权；本任务不实施。Owner :306、316 明确禁止拒绝后刷新 baseline 掩盖差异或自动重跑。

### 父控追加：有证据支持的处置选项（仅准备审阅，不实施）
|选项|精确事项及理由|证据与未知|是否改变接受契约|
|---|---|---|---|
|既有事件记录的定向审阅|如保留相关记录，限定上述 Memory 根路径和 PRESTART/GATE_BOUNDARY 区间，查 metadata 操作及 writer；不存在则保持 NOT_ESTABLISHED|端点记录不含完整 syscall/PID ledger，不能从 ctime 唯一反推原因|不改变；若需新增事件采集需另定授权，且不能补证历史|
|前瞻性契约裁决|Owner 可决定是否继续严格拒绝 Memory 根目录 ctime-only 变化，或另行定义“目录身份、权限、成员与文件内容有完整证明时”的精确例外；当前材料缺少完整成员观测，不能直接批准该例外|现有契约明确 Memory 严格，当前代码正确拒绝；正文端点哈希相同不是目录完整性等价证明|若采用例外则改变接受契约，只能前瞻适用，不重分类本次 FAIL|
|准备/环境修正|目前没有足以指定修正对象的 writer 或操作证据，不推荐实施猜测性修正|相同 ctime 仅相关；未发现已证实的 preparation 缺陷|当前不实施、不改变|
|collector/decision-binding 修正|当前未发现拒绝值绑定错误；成员覆盖不足属于明确观测限制，如未来需要完整成员证明，应单独定义最小采集要求|同一 captured map 参与 predicate 和 receipt；没有完整重枚举与连续历史|当前不实施；未来扩充观测不自动授权放宽 predicate|

**公开可独立复核边界：**原 public 包不包含完整 baseline/capture 私有记录或私有 policy。补充给出其哈希、字段投影和代码位置，能够公开审阅逻辑及主张，但仅凭公开包不能独立证明全部五个 Memory 原始记录、全量 strict map 与私有 policy 的真实性/完整性；该部分仍需获授权审阅者在本地核对原件。
