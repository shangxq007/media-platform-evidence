# Hermes 任务局部运行时与原路径保全边界

状态：**READ_ONLY_INVESTIGATION_COMPLETE；REPLACEMENT_CONTRACT=NOT_ENACTED；不授权启动或重跑。**

## 1. 结论

Hermes 支持独立进程的 `HERMES_HOME`、`hermes -p/--profile <name>`，以及内部基于 ContextVar 的 task-local home override。它们能将遵守该解析器的本任务 Hermes 状态读写路由到另一目录，**不能阻止仍指向原目录的并发进程更新 `/home/user/.hermes/skills` 和 `/home/user/.hermes/memories`**。因此在不改变共享配置、不协调/限制其他写者的条件下，不能保证原路径满足当前“原始基线全部字段相等且所观测写事件一律拒绝”的义务。副本一致不解除原路径义务；容器/私有 mount 视图的只读也不等于宿主原 inode 不变。

现行 observer 不需要也不得加豁免；在当前契约下继续 fail-closed 是正确结果。若保留当前绝对保全语义，只能等待实际稳定且具备所需观察证据的区间；本调查没有建立该区间，也没有验证其他写者静止。若业务需要允许并行使用统计，必须独立批准下面的前瞻契约，并另建执行/验证命名空间；不得把旧 REJECT 重新解释为 PASS。

已读取安装源码、官方在线文档和指定 executor；未运行 Hermes CLI、Collector、Watch、runner、产品命令或测试，未创建 profile，未改配置、权限、源文件或 instruction 正文。配置值和 credential 文件没有读取：不需要实际开关值即可判定隔离不是访问控制。此结论是实现/文档的静态边界调查，不是隔离运行 E2E 成功证明。

## 2. 原义务、字段和实际执行谓词

来源文件的绝对路径、摘要和行段见 `source-references.json`；在线原文的本地文本、URL、HTTP 状态和摘要见 `web-sources.json`。

- `executor/preservation.py:10-11` 的 `INSTRUCTIONS` 精确为上述两个 **ORIGINAL** 根。`FIELDS` 为 `st_dev, st_ino, st_mode, st_uid, st_gid, st_size, st_mtime_ns, st_ctime_ns, st_nlink`。文件有 `kind, metadata, sha256, git_blob`；递归目录另有排序 `children`。atime 不冻结，不恢复时间戳；这不等于豁免已观察到的 `IN_ATTRIB`。
- `Collector:49-98` 要求真实非 symlink 的常规文件/目录、完整非空 universe、所有祖先 FD 绑定、目标读取前后字段相等、目录成员前后相等。失败为 `INCOMPLETE/native_exit=1`；只发布摘要和元数据，不发布 instruction 正文。其顺序端点不是原子快照，也非历史连续证明。
- `coverage.derive:23-74` 保留全部旧 `protected` 成员，加入 Collector 枚举的全体 entries、当前 helper、本地 import 边、控制/权威输入、qualification 闭包、runtime frozen 支持输入。`enumeration_roots` 仍为原两个根；使用统计不是输入范围外的文件。
- `observe.Watch.classify:51-65` 在 instruction 根下返回 `REJECT_INSTRUCTION_EVENT`；受保护路径返回 `REJECT_PROTECTED_INPUT_EVENT`；相关祖先写事件为 `REJECT_PROTECTED_ANCESTOR_EVENT`。不存在 `.usage.json` 或 `IN_ATTRIB` 豁免。
- `MASK=0x2|0x4|0x8|0x40|0x80|0x100|0x200|0x400|0x800`：分别是 `IN_MODIFY, IN_ATTRIB, IN_CLOSE_WRITE, IN_MOVED_FROM, IN_MOVED_TO, IN_CREATE, IN_DELETE, IN_DELETE_SELF, IN_MOVE_SELF`。事件保存 `path,mask,cookie,category,observed_ns,writer=NOT_ESTABLISHED`。overflow、watch loss、unknown watch、动态子树 prewatch gap 拒绝。
- `observe.run:186-238`：先登记 watch、取 before、drain；已拒绝则 `PRESERVATION_REJECT_BEFORE_CHILD`。命令后等本任务后代、after、final drain；`REJECT := native_rc!=0 OR changed!=[] OR timeout OR watcher.rejected()`。监控窗口仅每条命令；inotify 不给 PID 因果证据，不覆盖所有 mmap/远程文件系统/属性。
- `runner.compare_baseline:321-331`：从原 `baseline.json.entries` 取 wanted；只存在已成功 reconciled 的 Shadow 精确例外，与 Skills/Memory 无关。`snapshot(wanted) != wanted => FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP`。非递归重采目录字段不能替代全程 entry-set 事件账，但之前的 recursive universe 和登记 watch 提供范围。
- `runner.run_all:334-374` 先验 owner/review/seal/candidate/preflight，再实时 preflight，再原基线比较；只有通过才写 `runtime/START.json`。最后再次 compare/seal/freshness。不能移动 expected hash 来掩盖 drift。
- 原 `qualification/CONTINUATION_PRESERVATION_CONTRACT.md:11-25,47` 明确 Skill 使用元数据无例外、sealed gate run 不调用 Skill 工具、`PRESERVATION_CONTRACT_RELAXATION=NOT_APPROVED`。`inputs/MONITOR_CONTRACT.txt:6,12,14-15` 也要求事件/字段变化拒绝并保留有限观察声明。

**原义务的形式化摘要**：`OLD_PASS = complete_capture ∧ retained_original_universe ∧ endpoints_equal_in_all_captured_fields ∧ no_reject_event ∧ no_observation_error ∧ bounded_children_quiescent ∧ native_success ∧ seals_and_authorizations_valid`。这只是实际实现覆盖范围内的 bounded PASS，不升格为所有时间、所有写方式的物理不可变性。

## 3. 支持机制与不能覆盖的边界

|机制|精确入口/数据路径|支持的效果|不能作为原路径保全证明的原因|
|---|---|---|---|
|进程局部 Hermes home|`HERMES_HOME=<已获授权的独立目录>`；`hermes_constants.get_hermes_home():82-89`|配置、skills、memories 等 resolver 路由；不需更改父进程/共享 config|只影响该进程及正确继承的子进程；原路径其他写者仍可写；本轮没有设置或启动|
|单次 profile 选择|`hermes -p <name>` / `--profile`；标准路径 `/home/user/.hermes/profiles/<name>/`|CLI 在 imports 之前选择 home；不必 `profile use` 改 sticky default|profile 必须存在；创建会写 profile/seed skills/别名，本轮禁止；仍非 OS 写权限隔离|
|Task-local override|`set_hermes_home_override(path)` 返回 Token，`reset_hermes_home_override(token)`；ContextVar `_HERMES_HOME_OVERRIDE`|不改 `os.environ`；`get_hermes_home` 优先级为 context override > env > OS 默认|内部 scoped routing 不是任意用户任务的全工具 sandbox；对象已有缓存、process-home 路径、插件/外部 CLI 仍须逐一验证|
|Skills 动态解析|`tools/skills_tool.py:60-69` 和 `skill_manager_tool.py:67-80`|正常模块绑定未被显式 patch 时按调用时 home 解析；`skill_usage._skills_dir()` 也动态解析|显式 patch 的模块常量优先；Web `_profile_scope` 仍在锁内改/恢复模块全局；不能宣称整个进程所有 handler 随 ContextVar 完全隔离|
|Web config scope|`hermes_cli/web_server_profiles.py:_config_profile_scope:231-242`|await-safe、只改 contextvar 的 config scope|文档字符串明确 config-only；`_profile_scope:197-228` 有另外全局技能目录切换。不得拿 config-only 当全 runtime 隔离证书|
|memory 开关|`memory.memory_enabled=false` 与 `memory.user_profile_enabled=false`；或 `memory.write_approval=true`|内建 store/工具关闭，或提交待审批|只管理经过该机制的写入；不阻止另一进程或 terminal 写文件；不控制所有外部 memory provider；本轮没有修改|
|curator 开关/暂停|`curator.enabled=false`；pause 是跨会话持久状态|控制 curator 维护流程|不是 usage 写入开关、不是原目录只读锁；禁止修改共享状态，未执行|
|delegate/worktree/terminal backend|子 agent conversation、terminal session，Git worktree 或 terminal 容器|上下文/工作目录或工具执行环境分离|delegation 官方禁止 memory tool 不等于 OS 不可写；skills_view 仍可能记账；terminal 容器不自动包住宿主 Hermes 状态写入|

CLI 细节：`hermes_cli/main.py:495-539` 对普通 home 仍可能读取该 root 的 `active_profile`；只有 env 已指向 `profiles/<name>` 且无显式 flag 时直接信任。不能只打印 env 就断言最终选择；将来若启动独立任意 home，须显式 pin 并读回最终 resolver/模块/store 实际路径，且禁止 fallback。不得使用或臆造新的禁写 env，也不得挪用 HOME/CODEX_HOME。官方确有 `terminal.home_mode: profile`，但它改工具 HOME，既不是本任务允许路径，也不能保全宿主原目录。

## 4. `.usage.json` 是具体风险，不是历史归因

`tools/skills_tool.py:_skill_view_with_bump:640-658` 在成功读取后 best-effort 调用 `bump_view` 和 `bump_use`；`tools/skill_usage.py:400-407,459-475` 对所有来源的 skill 记账。可能变化的 JSON 指针为 `/<escaped-skill-name>/view_count`, `/last_viewed_at`, `/use_count`, `/last_used_at`, `/patch_generation`, `/last_reused_patch_generation`。`bump_use` 会归一化 patch generation 并记录 patch 后复用；不能把文件视为纯时间戳缓存。记录不存在时 `_empty_record:329-332` 还创建完整状态键。

实际原路径映射：
- 主 sidecar `/home/user/.hermes/skills/.usage.json`。
- `_usage_file_lock:65-80` 使用 `/home/user/.hermes/skills/.usage.json.lock`，必要时创建；flock 仅串行化参与者，不禁止合法更新。
- `save_usage:359-367` + `utils._atomic_write:177-217` 在同目录 `mkstemp(prefix='.usage_', suffix='.tmp')`，写/flush/fsync 后 replace；所以可能发生 `.usage_<随机>.tmp` CREATE/MODIFY/CLOSE_WRITE、rename cookie 对应的 MOVED_FROM/MOVED_TO、目标 inode/ctime/mtime/size 改变及 **skills 目录自身 mtime/ctime/size 等变化**。失败清理可能 DELETE。真实分支还可能 copy fallback、symlink 解析；不能只靠文件名推断已发生的 syscall 序列。
- `on_skill_lifecycle(action='loaded')` 是提交后的 best-effort hook，可缺失 task/session identity、可抛错被抑制，`bump_view` 不 emit；它不是 complete writer audit ledger。
- 内建 memory 路径为 `/home/user/.hermes/memories/MEMORY.md` 和 `USER.md`（`memory_tool.get_memory_dir`、`memory_tool_store._file_path/_save_to_disk`），atomic 临时文件前缀 `.mem_`。这两个正文及全部 memory 附属输入应继续严格保护，不能随 usage 记账放宽。

**在线文档差异**：此次 HTTP 200 的 curator 页文本第 266 行说 bundled/hub skills 不记 telemetry；安装实现 `skill_usage:400-407,459` 明确 ANY/ALL，无该资格 guard，成功 skill_view handler 直接 bump。因此不能利用文档这句话免除 installed/bundled skill 风险；以安装代码解释本机可能行为，保留文档差异，不推定过去实际写者。官方 profiles 文档也明确不得让两个 agent 共用同一个 home。

本调查按要求调用过一次 `skill_view('hermes-agent')`。其源码显示这类“读工具”可能附带 usage 写入，因此**不能承诺本调查在运行时层面绝对无副作用**；没有本次 syscall writer receipt，不能断言该调用确已写入，更不能把既有拒绝后的 diff 归因于它或其他进程。后续不再调用 Skill 工具。

## 5. 前瞻替代契约（NOT_ENACTED）

以下是新契约设计，不是现行 observer 豁免，不适用于既有拒绝、不改变当前 baseline，也不是已部署机制。机器字段见 `proposed-contract.json`。

### 5.1 严格对象和支持输入

`STRICT_ORIGINAL` 包含两个原根下除**明确登记的使用统计事务对象**外的全部真实成员：所有 `SKILL.md`、任意扩展名正文、`references/ templates/ scripts/ assets/` 和未知新增路径；`.archive`、组织/同步/来源/选择策略及 `.usage.json` 中非获准字段也严格。整个 memories 树（不仅两个 .md）严格。全部 helper、observer、scope、原始保护 inventory、授权/qualification/seal/preflight、候选绑定及依赖输入仍按旧规则冻结。不得按扩展名或隐藏文件整体排除，也不得把 bookkeeping 内的政策字段放行。

### 5.2 唯一可申请的统计事务

默认精确允许候选仅 `/home/user/.hermes/skills/.usage.json` 的已存在 skill record 中 `view_count,use_count,last_viewed_at,last_used_at`；默认 **不得**增删 record，不得修改 `created_by,agent_created,created_at,state,pinned,archived_at,patch_count,last_patched_at,patch_generation,last_reused_patch_generation,sync` 或任意未知键。因此若当前 `bump_use` 必须改变 `last_reused_patch_generation`，事务仍拒绝，不能扩大解释为“仅记账”。如未来确要批准其他语义，须新的字段级 owner 决定/验证，不能此次预授权。

每个候选事务必须有完整、可信、前瞻的内核/执行边界证据：绑定 `run_id, transaction_id, boot_id, pid, process_start_time, executable_sha256, code/config digest, effective profile/home, skill_id, operation, syscall result`；记录真实 FD dev/ino、路径/父目录绑定、严格单调事件序号、before/after 字节摘要及授权字段 diff、writer 所有相关 open/write/fsync/rename/unlink/chmod/chown 的完整期间事件和成功/失败。单独自报 task_id、argv、文件名、inotify cookie 或 best-effort hook 不足以归因。

计数谓词：只允许 nonnegative integer，`after_count = before_count + 完整账中该 skill 已提交相应操作数`，不允许 bool/string normalization、decrement、lost update。时间字段必须等于被绑定事务生成并有可信时序界限的 timestamp；其余 JSON 结构/字段 deep-equal。双 bump 是两个可能分开的提交，必须都入账；不能把一次技能加载粗略当一次文件更新。缺失任一证据、未知 writer、未知操作、overflow/gap/异常 fallback、账与字节不一致，一律 REJECT。

### 5.3 entry-set 与目录元数据

不允许 `/skills/**/.usage*` glob 豁免。每个临时文件必须在创建前/创建时由可信事务记录注册精确绝对路径和 inode，只在原 skills 根，最终消失且只能原子替换精确 `.usage.json`。`.usage.json.lock` 如基线已存在，则最终身份/类型/权限等不变；如基线缺失，默认不得在窗口中新建，除非新授权显式列入唯一新增成员及全部 endpoint 字段。不得伪称 lock 一定最终不存在（实现通常保留 lock）。

所有严格目录的 children 集合最终精确等于基线，除已独立批准的精确持久 lock 成员；临时 entry 的中间增删必须与完整事务账一一对应，没有未解释子树或 transient。skills 根 `st_dev,st_ino,st_mode,st_uid,st_gid,st_nlink` 继续严格相等；可能受目录项事务影响的 `st_size,st_mtime_ns,st_ctime_ns` 只有在 **全部** parent entry/属性操作与已批准事务因果对应、无 chmod/chown/xattr 或未归因操作、最终成员检查通过时才可条件接受，不能按“rename 一般会改目录时间”宽免。其他目录的所有旧字段仍冻结。统计目标文件因 replace 可改变 dev/ino 等的范围须精确绑定同一 mount/预登记 temp inode、模式/owner 保持基线、nlink=1、最终哈希及全部 metadata 有因果账；不允许 symlink/hardlink/路径替换绕过。

若当前统计实现的 create mode 与基线权限不一致，则该事务不能通过这个提案；本调查不修实现或调权限。ACL/xattr 如新契约声称完整属性保护，必须补充真实采集及 syscall 覆盖；现有 fields/inotify 不能冒充这一证据。

### 5.4 新旧判定和声明边界

保持原始 `OLD_PASS/OLD_REJECT` 原样输出。另一个经 owner 批准的新版本 reducer 最多能得出 `ORIGINAL_STRICT_CONTENT_PRESERVED_WITH_ACCOUNTED_BOOKKEEPING`，而不是 `ORIGINAL_ALL_BYTES_AND_METADATA_IMMUTABLE`。`NEW_PASS := approved_before_start ∧ sealed_binding_valid ∧ strict_original_equal ∧ complete_event_coverage ∧ every_delta_has_exact_allowed_transaction ∧ zero_unknown_writer ∧ final_entry_set_valid ∧ directory_metadata_reconciled ∧ product_predicates_unchanged`。

`PRIVATE_INPUT_SNAPSHOT_MATCH` 只能说明副本/任务输入冻结；不能替代原路径条款。公共结果分别列 `original_old_contract_result`, `original_new_contract_result`, `private_snapshot_result`, `observation_limits`, `historical_writer=NOT_ESTABLISHED`。未完整观测或审批则新结果 `NOT_EVALUATED/REJECT`，不得降为 warning。

### 5.5 采用控制

保持当前 observer 字节不变、没有新豁免。本轮仅产出提案；没有 writer ledger/可信审计通道可供现在采用，故当前 gate 不具备该提案的接受条件。将来必须先有 owner 的版本化字段/路径/时间窗授权、独立审查、明确新 evaluator 与旧 observer 并列的权限及结果契约，再新 run/new baseline/new seal。用完整 positive/negative qualification（未知写者、只改政策键、temp 仿冒、目录 chmod、计数丢失、未登记 rename、watch gap/overflow、私有副本 PASS 但原始 drift）证明 fail-closed；最后重新 preflight。任何改 observer、scope、谓词的需求均是另一份待批准变更，不得借此次调查落地。不把未来语义 retroactive 到旧 evidence，不删除旧差异、不恢复 metadata、不终止其他进程。

## 6. 调查限制与副作用透明度

未读 credential 或发布 Skill/Memory 正文；没有历史 writer 归因。报告中 .usage/.mem 事件是安装实现的可能因果路径，不是该历史窗口已观测事实。未使用 profiles 的实际创建/启动测试，故不声明受支持机制已经在本任务验证。

工具 `web_extract` 的配置后端只支持 search，失败后改用 Python HTTPS 获取官方页面，均 HTTP 200。一次 `execute_code` 输出过长触发工具自身自动落盘 `/home/user/.hermes/cache/exec/stdout-9d03cffe0023.txt`；这是运行时工具的已报告外部副作用，不是有意输出位置，也没有尝试删除/修改。后续用有界输出规避。因这一工具自动落盘和 Skill 读取记账可能性，不能声称“所有实际运行时写入均在授权目录”，即使本调查主动编写的全部交付文件都在 `runtime-analysis/`。此限制本身也说明 task-local 输出约束与宿主 runtime 写隔离不能混同。
