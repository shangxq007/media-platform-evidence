# EP19 H7 Observer 恢复与 exact-candidate 续行报告

## 结论：B — 修正与受影响资格完成，最后启动保护检查拒绝

Observer 已按 Owner 明确同意的精确操作恢复；父环境受影响资格通过。初始 preflight 与 launch 内重新执行的 preflight 均为 ENGINEERING_READY，但 runner 在写入 START.json 之前的最后一次 compare_baseline 抛出：

```text
FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP
executor/runner.py:361 -> compare_baseline:331
父 runner 进程 exit=1
正式 START.json 不存在
正式 gate 目录数=0
29 required / 0 PASS / 0 FAIL / 29 NOT_RUN
```

没有正式 gate native command 开始，故不是结果 C，也不能把父进程 exit 1 算作某项产品 gate FAIL。未重试、未创建第二个正式运行、未刷新期望 hash、未恢复受保护 metadata。

## 1. 身份与审批

- TASK：`EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1`
- CONTINUATION：`OBSERVER_MAPPING_RESTORATION_AND_EXACT_CANDIDATE_GATE_CONTINUATION`
- LANE：`BACKEND_VALIDATION`
- Candidate base：`86d6aef94fd5e58da552e97c11473cff6eca734e`
- Candidate commit：`689ab9456461a8d19a72d059f5157092efc43aff`
- Candidate tree：`6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`
- 新 namespace：`owner-observer-restored-689ab945-v1`（已准备、启动命令被调用，正式执行未开始）
- 新 executor identity：`db414fda33a6ffa134b1291880ef1b1907fbe12e6b2a01d482830b4042296c4d`
- 原 evidence commit：`9decd69997bf0d40a596522cfb339563de2b913d`
- 原 public manifest SHA-256：`14d5a527f8ced6abeb9183dd0b59e0cb6c0900f06dacb250de26dec3e1d6f563`

原 execute_code 路径接受并执行了本次明确同意的 observer_scope_correction。先归档当前 helper，再以经核验的 published pre-correction 原件字节替换；没有更换工具规避限制，没有修改审批记录或旧 TOOL_RESTRICTIONS.json。

| Observer | SHA-256 |
|---|---|
| 归档 preimage | `0cb21b755471c5e554aa971f9f633e298bce55b722ed48a4773e79955677a3e8` |
| 核验原件及 live replacement | `2e060dd77ed4b24132d581e36cc3fa84c8b67d928cd9ec7689dcdc8823e991e2` |

差异仅为 resolve_shared() 恢复；没有手工重构或新 allowlist。391 个其他 reviewed 文件、5 个 original controls 不变。原 executor identity、旧 seals 与全部历史包保留。新 identity 的完整定义与构成见 [NEW_EXECUTOR_IDENTITY.json](evidence/NEW_EXECUTOR_IDENTITY.json)。

## 2. 资格：fresh 与 reused 分账

父环境实际新执行：

| 集合 | 方法数 | failures | errors | skips |
|---|---:|---:|---:|---:|
| Observer affected controls | 25 | 0 | 0 | 0 |
| Binder 正反控 | 10 | 0 | 0 | 0 |

新 qualification receipt 的 fresh test 字段仅为 25，另 10 项 binder 控制独立留证。Observer 控制含 12 个显式注入 classifier/resolver 场景、12 个真实 inotify observe.run 场景、1 个显式注入 late-event 的真实 finalizer 场景。覆盖 exact frontend ref 可达对象、不可达对象、zlib 损坏、对象 hash mismatch、symlink、临时路径、未绑定目录、缺失 ref、canonical/PRIMARY 同字节 metadata 写入，以及 native 0 不能接受 unresolved 的路径。所有 Git DB 都是 disposable fixtures；真实正控预先存在 fanout 目录，不能据此声称新子树 prewatch gap 已消失。writer 始终未知。

保留旧 observer 正控的 2 个预期 RED 失败，以及 writer 的中间运行。它们不计入父面 fresh 35 个控制，也不计为产品门禁。

复用资格经过完整 41,986 项 prior dependency 字节验证；仅旧 live observer path 映射到精确 preimage。40 个 focused 方法和 114 个 broader 方法复用；6 个触及已变更 shared-object 判定的 broader 方法由新控制替代。原 147 focused rows、131 broader rows 与 40/120 方法计数保持历史意义。

Gradle instrumentation、frontend isolation、Lean、Coq runtime probes 为逐项绑定的旧 native 证据复用，本次 fresh runtime probe 数为 0。没有复制旧 aggregate PASS 作为新 executor 的 fresh PASS。当前新 receipt 的 42,389 项 dependencies 在停止后再次验证，无漂移；加上 receipt 本身，closure 为 42,390 项。当前 Coq image ID 另行只读核对一致，不视为新 runtime probe。

## 3. 隔离、readiness 与实际阻断

backend、candidate-frontend、SHADOW 为独立 exact-candidate clones，各自 Git common-dir/object store，无 alternates/hardlinks。build/cache/temp/evidence 使用新 namespace；frontend 输出外置。原矩阵的历史源定位信息保留，实际 clone 身份与运行位置见 [namespaces.json](run/namespaces.json)。未检查或冻结 parallel frontend development checkout 的 HEAD/index/worktree，未使用其测试结果。

原严格 canonical/PRIMARY、有限 SHADOW、metadata/event、Skill instruction/runtime usage/directory 区分及 frozen runtime policy 规则均保留。没有将 INDEPENDENT_REVIEW=PENDING 设为新阻断，也没有设为 ACCEPT 解锁。

baseline 与两次 preflight 已真实执行并通过。最终启动检查仍以原 baseline 为准，发现差异即拒绝。拒绝后对 117,888 个 baseline endpoints 进行只读回读，发现 2 项：

1. `/home/user/.hermes/skills/.usage.json`：内容、inode 及 metadata 不同。
   - baseline SHA-256：`47312b50c4a456e994505a6666bdc7084c4b42f238f33a74ad3a4f8be4e4c27b`
   - 后续回读 SHA-256：`68ae3e062b7a3003bbf6a7fbfbf49e99a90fd7f734490b1b30d2e44396a2c1cb`
2. `/home/user/.hermes/skills`：目录 mtime/ctime 不同。

原 throw 没有保存其瞬间的逐项 diff；以上是后续回读，不能反推早先拒绝瞬间仅有这两项，也不能确定 writer、精确事件时点或原因。没有通过 `.usage.json` 豁免、timestamp restore、metadata restore 或新 baseline 绕过。已加载必要 skills 的动作发生在 baseline 前；封存期间本控制面未再主动加载/编辑 skills。没有主动 Skill/Memory instruction-body 编辑；runtime usage 实际漂移如上，不归因给任何未证明的 writer。

启动 native traceback、两次 preflight 摘要、完整后续差异、scope 摘要与全量本地原始证据定位均在本包。一个停止后的只读诊断曾因缺少 Python import search path 失败，记录也保留；补充 search path 后回读成功，没有修改 helper，executor bytecode residue 为 0。

## 4. Gate / test / artifact 实际账本

- 29 formal gates 全部 NOT_RUN；没有删除 gate 或替换断言。
- Backend baseline：7,973 expected identities，含 29 expected skips；本次 discovered/executed/PASS/FAIL/error/observed skip 均为 0。7,973 项未观察到，29 expected skips 未执行观察。
- Candidate frontend baseline：149 identities，expected skips 0；来自此 candidate 自身的既有基线。本次 discovered/executed/PASS/FAIL/error/observed skip 均为 0，未观察到 149 项。
- A/B/C 修正及其适用资格保留，但本正式 namespace 的 artifact production、COMPILE inventory、frontend closure、processed resources、JAR 及 Git→resources→preserved JAR mapping 均 NOT_RUN。不能把 synthetic/reused 资格说成实际打包结果。
- GITOPS_PRODUCTION 等标签没有导致部署；产品 commit/freeze/merge/push/publication/deployment/sanity 均未执行。

[ACTUAL_ACCOUNTING.json](run/ACTUAL_ACCOUNTING.json) 列出完整 29-gate 分母、每个 NOT_RUN 及测试账本。

## 5. 历史保护与已知边界

旧 owner-execution-689ab945-v1 仍为 5 PASS / 1 FAIL / 23 NOT_RUN；ARCHITECTURE native -15、assertion completion NOT_ESTABLISHED、engineering FAIL_PRESERVATION。177 observations（174 rejected、3 authorized frontend）及其他历史因果限制不变；54 rejected paths 不等于 closing-difference paths。捕获端点的 canonical index equality 不能抹除 replacement/metadata events，历史 staged semantic equality 未建立，Skill instruction-body modification 与 writer attribution 亦未建立。

停止后复核旧 4,686 个 run files 与 7,641 个失败现场 endpoints，无差异；原 published continuation 的 180 payload files 及 manifest 也通过回读。此处仅证明已捕获端点/当前字节一致，不补造历史连续证明。

PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE。本次没有正式命令区间观察；本地 inotify 的 writer PID、mmap、网络文件系统及命令间短暂恢复写入限制仍在。

实测耗时分项：writer 进程工具报告 uptime 888 秒；父面 qualification binder 24.359714 秒；baseline 127.880489 秒；preflight 114.026068 秒；启动尝试进程工具报告 uptime 354 秒。这些包含不同边界与重叠准备工作，不相加冒充总工时或 native gate 时间。

## 6. 交付与停止点

本目录为新增 evidence-only continuation；原报告、封存包、历史与 frontend evidence 不覆盖。大 baseline/scope/seal、cache manifests 与全部原始现场留在本地，通过 [SOURCE_LOCATORS.json](SOURCE_LOCATORS.json) 提供完整路径、大小和 SHA-256；公开相关原始日志、拒绝证据、源程序、资格及机器账本。没有导出私有 Skill/Memory bodies 或凭据。

全要求字段见 [FINAL_DISPOSITION.json](FINAL_DISPOSITION.json)。此 payload 在发布前封存，commit/manifest/readback 等发布后才确定的字段由 detached publication receipt 与最终本地 disposition 补齐，不能回写已覆盖的 payload 制造 hash 循环。

INDEPENDENT_REVIEW=REQUIRED；EP19_CLOSED=NO；PRODUCT_PUBLICATION=NOT_PERFORMED；POST_PUBLICATION_SANITY=NOT_RUN；STOP=YES。下一步是独立审查本次启动拒绝及受保护 runtime usage/目录漂移的后续处置；本次不请求宽泛工程重授权、不提出豁免、不自动重跑，也不放行 Roadmap #23 / Second Wave。
