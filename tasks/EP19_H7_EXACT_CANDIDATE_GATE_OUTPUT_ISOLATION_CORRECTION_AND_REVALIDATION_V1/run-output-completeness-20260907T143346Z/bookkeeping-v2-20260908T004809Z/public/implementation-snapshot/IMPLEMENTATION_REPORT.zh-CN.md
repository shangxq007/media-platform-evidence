# Scoped Runtime Bookkeeping Contract V2 实施与资格报告

## 结论

Owner 授权的 V2 已在本 continuation 具体实现并完成受影响资格：`FRESH_QUALIFICATION_RESULTS=129 PASS / 0 FAIL / 0 ERROR`。固定候选未变，正式产品 gate 未运行，`FORMAL_START_CREATED=NO`，29项均为 `NOT_RUN`。这不是把历史 strict failure 改判成功，也不是产品发布或 EP19 关闭。

新 executor identity：`20ef0bc2939209032b82af3a28f5ca932d5e32fcca569bccd5ed1fb5d58a1b14`。

## 实施内容

`executor/bookkeeping_v2.py` 实现稳定 FD/path-bound byte capture、UTF-8 strict JSON、duplicate key/nonfinite/malformed 拒绝、eligible record/escaped pointer/schema 枚举，以及四字段单调比较。每个正式 run 在 baseline 阶段生成 `bookkeeping-policy-v2.private.json`，内含完整 parsed projection，明确标记 `PRIVATE_NOT_FOR_PUBLIC_PACKAGE`；公共 receipt 只输出摘要、hash、metadata difference 与 changed pointer，不输出 Skill/Memory body 或完整私有记录。

V2 只允许已存在 record 中已存在的 `view_count`、`use_count`、`last_viewed_at`、`last_used_at` 变化。record membership、field membership、所有其他值严格深相等；count 必须为排除 bool 的非负 integer 且不下降；timestamp 只允许 null 保持或 null→UTC-aware ISO string，既有字符串不得倒退/变 null。`patch_generation`、`last_reused_patch_generation`、state、pinned、sync、ownership 与未知字段均不豁免。

usage file 保持 exact path、regular type、filesystem boundary、owner/group/mode、single-link strict；inode/size/time 可观察变化。Skills root 保持 path/inode/type/owner/group/mode/link 与最终 direct-child entry set strict，只允许 size/mtime/ctime 差异。现存 `.usage.json.lock` 保持完整 metadata strict。临时空间仅为 root direct child `^\.usage_[a-z0-9_]{8}\.tmp$`；unexpected persistent temp、target attribute event、target moved-out、temp cross-boundary rename、symlink/hardlink/type/owner/group/mode/device 异常均拒绝。

`executor/observe.py` 将 exact target/temp event 保留在事件账中并延迟到最终语义评价；其它 Skill 与全部 Memory 仍严格。`executor/decision_evidence.py` 从同一 captured hash/metadata 与 V2 stable bytes 派生决定，分别输出 OLD_STRICT、V2 integrity、bookkeeping、writer attribution、observation limits；receipt 写/fsync 失败抛错，不允许启动。`coverage.py`、`runner.py` 将 policy/dependency/Owner/qualification/executor identity 纳入 scope、baseline、seal、preflight、prestart、gate boundary 与 final acceptance。旧 strict 只作为独立诊断，不再对完全合规的四字段变化形成意外 veto。

原有 A/B/C 继续保留：独立 backend/candidate-frontend/SHADOW checkout/output/receipt 绑定，COMPILE freshness/completeness，以及 frontend referenced-asset closure。没有 blanket Skills skip、扩展名排除或 hidden-file 排除。

## 四字段依赖结论

`BOOKKEEPING_FIELD_DEPENDENCY_CHECK=COMPLETE_WITH_TASK_LOCAL_BINDING_REQUIREMENTS`。安装 Hermes 的 curator lifecycle/review prompt 与 TUI skill ranking/filtering 确实读取四字段，所以不能声称其全局无语义。本任务固定29项 matrix、candidate、argv/cwd、inventory、parser 与 qualification applicability 不读取这些字段。正式窗口前由 run-local bindings、scope、qualification closure、private policy 和 seal 固定实际输入；窗口内不通过 curator/UI 动态选择 gate。源码摘要与行级说明见 `dependency/`。

当前真实 sidecar 的只读 schema/inventory probe：222 usage records 中205个匹配按安装 scanner 语义发现的 Skill name，17个 orphan/ineligible record 全字段 strict；inventory 有221个 selected names、2个 duplicate names；因此 eligible pointers 为820。锁 PRESENT、old strict PASS、V2 PASS；没有落盘 raw records/value 或 Skill body。此 probe 不是正式 baseline 或 seal。

## RED、GREEN 与复用

RED 在实现前实际运行，结果为 `Ran 1 test`、1 error、rc=1，原因是 `bookkeeping_v2` 尚不存在，见 `qualification/RED.*`。

最终 GREEN fresh suite 实跑129项，包含：parser/schema/monotonic、unknown nested exponent-overflow、nested-category inventory name 与 orphan strict、baseline persistent-temp 拒绝、replacement/root metadata、permission/path/symlink/hardlink、real inotify atomic temp、strict Skill/Memory、capture gap、evidence-write failure、stale executor/policy/Owner/qualification/seal、actual receipt values、29-node mocked-expensive launch reachability，以及 strict violation 在模拟 native rc0 时阻止 START。`qualification/attempt-001` 保留一次 capsule identity parser 的正常纠错：测试本身124项全过，但预期 evidence-write stderr 插入同一状态行，旧解析只得到123 identities，builder 因闭包不等拒绝；修正后未放宽总数或唯一性。

复用仅限明确未变组件。A/B/C 的 artifacts/bindings/compile/freshness/isolation/namespaces/packaging/vite helpers 逐文件相等；`execution.py` 的 `exact`、`frontend_sandbox`、`formal_sandbox` 逐函数 AST 相等；旧 parent full capsule 的 real Gradle/frontend/formal/Lean 日志、process/result receipt 与资格程序被过滤绑定。parent-runtime-completion-3 的 formal-boundary PASS 及10份 native receipt/log 也逐项封存；old/current `formal_sandbox` AST digest 同为 `fe1357c3465b6b8bcae13eb5dbc42ccabbb12e7977ff839e382e84f9c74302ad`。历史45 diagnostics、旧 strict 结果和已修改的 coverage/observer/decision/runner 没有被重标为当前资格。精确范围见 `qualification/REUSE_LEDGER.json`。

## 观察限制与边界

合规 bookkeeping variation 可与 `WRITER_ATTRIBUTION=NOT_ESTABLISHED` 共存。没有完整 writer/syscall ledger；短命 temp 可能在 observer 打开前消失，记录为 observation limit。最终结构/内容、所有严格输入、可分类事件、capture 与 evidence write 仍 fail closed。不会使用 `ORIGINAL_ALL_BYTES_AND_METADATA_IMMUTABLE`、`COMPLETE_BOOKKEEPING_TRANSACTION_ACCOUNTING` 或 `GLOBAL_WRITER_ATTRIBUTION_ESTABLISHED`。

未修改 candidate、原 Skills/Memory、共享配置、其他 profile 或历史目录；未执行 git commit/push/merge/rebase，未运行正式 product gate。并行 frontend ref/工作树未触碰。

## 当前结果字段

- `TASK=EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1`
- `CONTINUATION=SCOPED_RUNTIME_BOOKKEEPING_CONTRACT_V2_IMPLEMENTATION_AND_FORMAL_VALIDATION`
- `LANE=BACKEND_VALIDATION`
- `CANDIDATE_COMMIT_SHA=689ab9456461a8d19a72d059f5157092efc43aff`
- `CANDIDATE_TREE=6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`
- `OWNER_CONTRACT_VERSION=OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2`
- `V2_CONTRACT_IMPLEMENTED=YES`
- `STRICT_SCOPE_RETAINED=YES`
- `BOOKKEEPING_SCOPE=/home/user/.hermes/skills/.usage.json; four fields only`
- `OLD_STRICT_PRESERVATION_RESULT=QUALIFICATION_OBSERVED_OLD_STRICT_REJECT_FOR_APPROVED_VARIATION; FORMAL_NOT_RUN`
- `V2_INPUT_INTEGRITY_RESULT=QUALIFICATION_PASS; FORMAL_NOT_RUN`
- `V2_BOOKKEEPING_EVALUATION=QUALIFICATION_PASS; FORMAL_NOT_RUN`
- `WRITER_ATTRIBUTION=NOT_ESTABLISHED`
- `FRESH_QUALIFICATION_RESULTS=129 PASS, 0 FAIL, 0 ERROR`
- `FORMAL_LAUNCH_BINDING=IMPLEMENTED_AND_QUALIFIED; PARENT_COMMANDS_READY`
- `FORMAL_START_CREATED=NO`
- `REQUIRED_GATES=29; PASS=0; FAIL=0; NOT_RUN=29`
- `ACTUAL_TEST_IDENTITY_ACCOUNTING=129 unique, 0 duplicate`
- `A_B_C_CORRECTIONS=RETAINED`
- `PRODUCT_CHANGED_PATHS=[]`
- `FRONTEND_LANE_INTERFERENCE=NONE`
- `HISTORICAL_FAILURES_PRESERVED=YES`
- `PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE`
- `PRODUCT_PUBLICATION=NOT_PERFORMED`
- `POST_PUBLICATION_SANITY=NOT_RUN`
- `EP19_CLOSED=NO`
- `INDEPENDENT_REVIEW=PENDING`
- `EVIDENCE_COMMIT_SHA=NONE`
- `REMOTE_VERIFICATION=NOT_PERFORMED`
- `STOP=BOUNDED_IMPLEMENTATION_AND_QUALIFICATION_COMPLETE; PARENT_FORMAL_EXECUTION_PENDING`

完整 parent 执行命令见 `PARENT_COMMANDS.md`。它会在新 namespace 创建 prospective policy/baseline/seal，preflight 真正通过后才自动启动一次29-gate graph；失败不自动修产品或重跑。
