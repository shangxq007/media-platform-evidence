# 四字段有界依赖审计

结论：`BOOKKEEPING_FIELD_DEPENDENCY_CHECK=COMPLETE_WITH_TASK_LOCAL_BINDING_REQUIREMENTS`。

`view_count`、`use_count`、`last_viewed_at`、`last_used_at` 并非全局无语义字段。安装版 Hermes 的 curator 用活动计数/时间判断 stale、archive、reactivate 并把统计写入审查提示；TUI 技能补全按活动排序，并可隐藏从未使用的 bundled Skill。因此 V2 不把整个 `.usage.json` 当作缓存，也不豁免 `state`、`pinned`、generation、sync、ownership 或未知字段。

本任务的实际执行路径不同：权威 `GATE_EXECUTION_MATRIX.json` 固定29个 gate 的 argv、cwd、仓库、候选身份、输入 inventory 与 parser；`executor/bindings.py` 只验证并重写这些已固定路径；qualification applicability 由 schema、源码/日志/回执摘要和显式 area 决定。候选 tracked 文本与 gate 命令不引用这四个 Skill sidecar 字段。验证窗口前可用任务本地 `bindings.json`、保护范围、qualification closure 与 seal 固定实际选择，不修改 Hermes profile/config，也不在窗口内调用 curator/UI 动态选择 gate。

Eligible 不是“`.usage.json` 中所有 key”。实现按安装版 `iter_skill_index_files` 的 excluded/support/org 遍历语义扫描当前 Skills root，并从每个 `SKILL.md` frontmatter `name`（缺失时目录名）建立 first-wins path/hash/metadata inventory。仅 usage record ID 与该 name inventory 的交集可有四字段变化；orphan/ineligible record 的四字段也作为严格值。duplicate names、nested category 路径及完整 inventory manifest 均在私有 policy 固定。当前只读探针为222 records，其中205 eligible、17 orphan strict；inventory 221 selected names、2 duplicate names。

安装 writer 的核验结果：

- `tools/skill_usage.py:329-339`：count 初始为非负整数0，两个时间初始为 null；首次更新为 `_now_iso()` 的 UTC aware ISO 字符串。
- `tools/skill_usage.py:359-364` 与 `utils.py:177-217`：同目录 `mkstemp(prefix='.usage_', suffix='.tmp')`、flush/fsync、replace；当前解释器随机段为8个 `[a-z0-9_]`，故只登记 direct-child `^\.usage_[a-z0-9_]{8}\.tmp$`。
- `tools/skill_usage.py:65-80,375-387`：持久锁名精确为 `.usage.json.lock`，Linux `flock` 后不删除。本次静态/元数据检查发现锁已存在，baseline 必须保留其身份与元数据，不制造共享锁。
- `bump_use` 也可能更新 generation 字段；这些仍严格，若变化则 V2 拒绝。
- Python JSON 对 `1e999` 可产生非有限 float；verifier 在 parse 后递归检查整个对象树，包含未知嵌套 strict 值，并拒绝 exponent overflow。
- reserved temp 在 policy/baseline 前若已持久存在会直接拒绝，不能把它收入 baseline entry set 后伪装为合法终态。

观察限制：本审计是安装源码与本任务路径的定向静态检查，不证明未来未知 reader 不存在，不建立完整 writer/syscall 账，也不把任何变化归因给 Hermes。原始 `.usage.json` 仅用于私有 schema/inventory 聚合检查；本交付不含记录正文、字段值或 Memory 内容。最终 eligible IDs、escaped pointers 与 baseline projection 由每个新 run 的 `bookkeeping-policy-v2.private.json` 在稳定读取后生成，并明确标记 `PRIVATE_NOT_FOR_PUBLIC_PACKAGE`。

本报告不是 baseline、seal、formal start、产品 gate 或发布成功证明。
