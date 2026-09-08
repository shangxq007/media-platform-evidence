# Owner V2 决定与旧义务映射

本轮权威是 `../OWNER_AUTHORIZATION.txt`，对应当前 Owner 直接消息的单份任务正文（消息中重复的同份正文不产生两个运行授权）。版本名：`SCOPED_RUNTIME_BOOKKEEPING_CONTRACT_V2`。只授权一个通过实际 readiness 后的新正式 gate graph。新实现独立审查可以保持 PENDING；执行授权不等于实现接受，更不等于产品发布。

## 明确采用

- 对 `/home/user/.hermes/skills/.usage.json` 现有、与真实 Skill inventory 绑定的 eligible records，仅 `view_count/use_count/last_viewed_at/last_used_at` 进入版本化语义比较。
- Counts 必须是非布尔非负整数、不递减；时间戳遵守安装 writer 初始化/schema/可比较时序。record/field membership 和全部其他值严格。
- 原路径/file type/ancestor binding/device/uid/gid/mode/nlink 继续保护；usage 原子替换的 inode/size/time 变化可记录而接受。
- Skills 根身份、type/owner/permissions/binding 严格；最终 persistent entry set 严格，单个 lock 只按 baseline/显式事前 registration。根 size/mtime/ctime 可在已声明 bookkeeping 边界内变化，不要求逐项 writer 因果账。
- 安装 writer 精确 direct-child temp namespace 可有短暂操作；不能泛化其他 temp/目录/路径，最终不得残留；已观察的 symlink/hardlink/permission/cross-boundary/strict-target violations 拒绝。
- 该有限 scope 内 `WRITER_ATTRIBUTION=NOT_ESTABLISHED` 可与 V2 成功共存；完整 writer/syscall ledger 不是 prerequisite。

## 不改变

产品候选、canonical protections、已有 Shadow/并行 frontend exceptions、实际 instruction/support/config、整个 Memory、helper/qualification/owner/policy/baseline/seal/matrix、unknown files/fields 均保持严格。A 独立 run/output/artifact；B COMPILE 完整与新鲜；C referenced asset closure；实际 capture-bound decision evidence 和 write-failure fail-closed 不变。

## 接受路径

Scope → baseline → seal → preflight → prestart → per-gate → command gap → final acceptance 全部必须使用同一封印 policy。Usage 仍在 dependency accounting，whole raw digest 为观察值，不作为批准变化的隐性 veto。旧 strict 与 V2 独立输出：OLD_STRICT_PRESERVATION_RESULT / V2_INPUT_INTEGRITY_RESULT / V2_BOOKKEEPING_EVALUATION / WRITER_ATTRIBUTION / OBSERVATION_LIMITS。新声明只能是 STRICT_INPUTS_PRESERVED_WITH_SCOPED_BOOKKEEPING_VARIATION；不声称原全部字节元数据不可变或完整事务归因。

## 历史边界

旧 5/1/23、ARCHITECTURE/FAIL_PRESERVATION、prestart drift、后续 29 NOT_RUN、缺失旧 decision evidence、unknown writers、PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE 原样保留。历史 stronger `proposed-contract.json` 不是本轮契约，不追溯应用 V2。

## 操作边界

只在新 `bookkeeping-v2-20260908T004809Z` 主动写实施、fixture、运行和证据；历史目录不改。前端开发 `refs/heads/agent/frontend-wave2-product-ux-v1` 无操作，不冻结其 HEAD/index，不跑其 gates。候选前端仅固定候选的独立 clone。

当前恢复：固定候选在 TASK_ROOT/sources/backend 三身份匹配；canonical media-platform 当前对象库不含该 SHA，因此使用实际 authority clone 而非补写 canonical。旧 executor identity 按既有 compact sorted identity_basis 重算一致，38 helper preimages 已匹配。旧 evidence commit 的公共 MANIFEST.sha256 实际字节摘要一致；早先检索错误地仅检索 .json 未命中，已保留为一次恢复查找错误而非身份失败。

较早 `bookkeeping-v2-20260908T001447Z` 已存在，只读取和保留，不假定它完成过当前实施。本轮使用新命名空间，避免覆盖。
