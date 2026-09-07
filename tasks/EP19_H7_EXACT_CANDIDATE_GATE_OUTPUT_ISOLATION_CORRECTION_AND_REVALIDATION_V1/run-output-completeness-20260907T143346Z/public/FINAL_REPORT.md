# 后端验证续行最终报告（中文）

## 结论：B — 三项修正及资格完成，正式门禁未启动

TASK=EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1  
CONTINUATION=RUN_OUTPUT_ISOLATION_AND_ARTIFACT_COMPLETENESS_CORRECTION  
LANE=BACKEND_VALIDATION

候选：`689ab9456461a8d19a72d059f5157092efc43aff`  
Tree：`6c97c0c879aa4cd8d1c58ca338482dd8ce25eff6`  
Base：`86d6aef94fd5e58da552e97c11473cff6eca734e`  
修正版 executor identity：`sha256:e12d7d27f52e2ad19265b0ddc603303b934612569fb8eb19c296803649640f58`

这是工程执行结果，不是独立接受。原产品候选没有修改、提交、冻结、合并或发布。独立 frontend 开发分支没有被本任务测试、修改或冻结。

## 1. 已完成的三项修正

| 缺陷 | 修正及证据 | 验证边界 |
|---|---|---|
| A：不同 run 共用 backend build，旧 receipt 引用可变产物 | `executor/namespaces.py:11–69` 创建独立 backend/frontend/SHADOW clones，Git/common dir 分离、无 alternates/硬链接对象共享；`bindings.py:29` 重绑定完整 29-key 图；`artifacts.py:28–50,72` 复制并校验 gate 独占证据，绑定相对路径、大小、hash、run/candidate/producer。 | A/B fixture 使用六个真实 exact-candidate checkouts。B 的写入及清理不改变 A 的 copy；删除 A 的 live producer 后父控制面再次验证 copy 通过。该 fixture 的 11-byte 文件是控制字节，不冒充产品编译结果。 |
| B：COMPILE 仅以成功日志及任意 class 存在接受 | `compile.init.gradle` 外部捕获 Gradle 图、参与 source sets、JavaCompile 声明输出、执行前后 sources/outcomes；`compile_inventory.py:9` 检查所有要求任务、合法 NO-SOURCE、空初始化与完整声明输出清单；`runner.py` 将验证接入接受路径和产物封存。保留原 `--rerun-tasks --no-build-cache`。 | 父执行真实小型 Gradle fixture，覆盖生成源、嵌套类、NO-SOURCE、缺失输出、stale/preexisting 输出及 sealed class 丢失。不是实际产品 COMPILE 门禁。完整性以实际 Gradle 任务/声明输出和原生编译为基础，不以源文件数推算 class 数；不声称拥有能独立预测每个语义类型的编译器 oracle。 |
| C：只验 index，不验引用资产闭包 | `parsers.py:12` 的 FRONTEND_BUILD 路径调用 `vite_closure.mjs`；启用 Vite manifest，以 Acorn、parse5、PostCSS、postcss-value-parser 检查 HTML/JS/CSS/manifest 的本地传递依赖和完整 emitted-file manifest。规范化 base/query/fragment，拒绝路径越界；外部/data 与导航路由单独处理，不访问外部 URL。 | 真实 tiny Vite build、入口 JS/CSS 缺失、传递依赖缺失、preload/manifest、合法外部 URL 等控制通过。父控制面另复现 file URL 被误接受，随后保留原 fixture 重验得到 native 1、`VITE_UNSUPPORTED_SCHEME file`。不声称 Vite 曾实际丢失产品资产。无法可靠解析的动态形式显式拒绝，不静默遗漏。 |

每个正式 run 的 source/build/cache/tmp/evidence 绑定机制已实现；本次仅准备了 review-only run，未进行 baseline 或 launch。其实际路径见 `prepared-run/namespaces.json`，命令与依赖见 `prepared-run/bindings.json`。没有声明共享可写 dependency cache；dependency cache 不作为 accepted output 或 receipt 证据。证据复制是独立普通文件，不是符号链接或硬链接；这是 namespace/完整性保证，不是声称同一 Unix 用户不能恶意改文件。

## 2. 实际资格账本

父控制面最终执行：

- Focused：**40 个方法，147 条方法/子用例记录；0 failures、0 errors、0 skips**。
- Broader：**120 个方法，131 条方法/子用例记录；0 failures、0 errors、0 skips**。
- 真实 Gradle instrumentation、frontend 只读/private-PID/XDG 边界、Lean、Coq runtime 探针：**PASS**。
- 全部五个 native 阶段 exit **0**；阶段期间 helper/program source drift **false**。
- 完整资格闭包 **41,986 个依赖文件**；父 readback 校验 **41,987 个文件（含 receipt 自身）**通过。全部原始依赖留在本机，公开 payload 仅包含有关摘要、日志、控制源码和小型 fixture 证据。
- Native 阶段耗时：focused 111.459 秒；controls 202.090 秒；frontend 0.694 秒；Lean 26.178 秒；Coq 16.367 秒。总 wall time 与未拆分的其他工作/等待见 `evidence/TIMING.json`，不把并行或未测量时间虚构为纯工作时间。

`qualification/focused/`、`qualification/broader/`、`qualification/native/` 和 `evidence/PARENT_FINAL_QUALIFICATION_READBACK.json` 是当前父执行证据。早期 Codex 沙箱的 Gradle socket 拒绝只适用于那些失败尝试，不能描述当前父环境。早期失败、修正前代码、URL RED、synthetic launch fixture 的失败及父 readback 调用错误均保留，未改写成首次即通过。

Broader 控制中运行过 synthetic 29-key 图，**不算正式产品门禁**。旧版本的绿色资格不作为本次新版本的 fresh execution。

## 3. Packaging authority

继续保持：候选 Git static → exact checkout resources → Gradle processed resources → BOOTJAR entries。`executor/packaging.py:9–77` 检查路径、blob/hash、缺失、重复、冲突和不受支持的转换；接受前对独立保存的 JAR copy 重验。相关正负 fixture 通过，证据在 `qualification/packaging-fixture/`。

**实际候选 processResources/BOOTJAR mapping=NOT_RUN。** 单独构建的 frontend 结果没有集成到 backend static 或 JAR。实际集成仍需另行授权任务。

## 4. Preservation applicability 与唯一 readiness 决定

详细原要求→路径角色→观察→拒绝/条件处理→所需证据映射见 `evidence/PRESERVATION_MAPPING_WORKING.md`；本节和 `READINESS.json` 为最终 disposition。

- canonical 与 PRIMARY 不混称；canonical index 内容/既有元数据及 PRIMARY metadata 继续严格。端点内容相等不抵消 metadata/replacement 事件。
- SHADOW 例外仅属于新 run 的 disposable SHADOW、声明的三条 jOOQ 文件和既有 index 条件 reducer；不能扩展到 canonical 或 PRIMARY。
- Skill 正文、`.usage.json` 与目录 metadata 分开处理；没有 usage 豁免、expected-hash 刷新或 metadata 恢复。
- helpers、工具依赖、bindings、matrix、contract 通过独立 hash identity 与资格闭包绑定；未将 runtime cache growth 解释为修改 executable policy 的许可。
- 独立 frontend 分支维持原 exact-ref 条件例外，不要求其 HEAD/index/worktree 静止。
- run-owned outputs 与 gate-owned copies 由 A/B/C 控制验证；这不解释或豁免旧 preservation failure。

**仍有一个具体 implementation-to-mapping 差异：**

既有 `owner-clarified-execution-20260907T1120Z/ENGINEERING_MAPPING.md:3,14` 要求，对 exact frontend ref 可达的新 loose objects，在完成 reachability、zlib、object hash 等检查后作条件处理。修正版 `executor/observe.py:106–110` 却替换为无条件拒绝。该改动不属于三项 artifact 缺陷，也不能以 independent review PENDING 解释。

父控制面拟撤回这一范围外改动，仅恢复新 task-owned helper 到原有 bytes；**工具审批超时明确禁止该操作重试、改写重试或换工具实现同一结果**。实际 readback 确认没有创建该 revision-preimage，没有改变 helper。完整原始拒绝文本及两个 helper hashes 在 `evidence/TOOL_RESTRICTIONS.json`。

因此正式 readiness **BLOCKED_NOT_STARTED**，而非自动签发 ENGINEERING_READY。通用资格通过不能抵消已查明的契约实现差异。所需解决仅是该具体工具限制的合法解除/取代及后续限定纠正；**不请求扩大工程范围、重新授权 routine work、豁免保全或将独立审查提前标为 ACCEPT**。没有绕过工具限制。

## 5. 正式门禁、测试与历史

当前：**29 required / 0 started / 0 passed / 0 failed / 29 NOT_RUN**。后端 7,973 identities（29 expected skips）仅作为既有期望基线；实际发现、启动、通过、失败、跳过均为 0。候选 frontend 产品测试同样 NOT_RUN，未借用独立开发 lane 的结果。

历史保留：**29 required / 5 passed / 1 failed / 23 not run**；ARCHITECTURE native **-15**，断言完成未建立，engineering validation **FAIL_PRESERVATION**。177 observations = 174 rejected + 3 authorized frontend；54 rejected paths 不等于 closing-difference paths。canonical index 捕获端点内容相等，但存在 replacement/metadata 事件；历史 staged semantic equality、Skill 正文修改及 writer attribution 均未建立；usage 文件和目录 metadata 变化保持历史结论。停止后的 reload 不用于追溯归因。

原 manifest `78ddad64194ad9fe9e10359716e55bf76231f27992ead3f06198cb3e42990425` 再次匹配；88 payload 全部匹配。旧 run 4,686 文件没有新增、修改或缺失；失败 checkout 7,641 个端点对比无变化，包括两个原有缺失资源仍缺失。父 readback 曾误读 missing-row schema，已在独立 correction JSON 纠正，未改历史。88 个修正前代码/配置原件及 preimages 全部匹配。

230 个 Skill 正文文件的 hash/mtime 与本轮 after-launch snapshot 相同；该 snapshot 不是 first-launch 之前的证明。没有 Skill/Memory 正文写入或私有正文导出；Skill 工具加载可能更新 usage metadata，不被宣称为零变化。`PACK_HISTORICAL_BYTE_IMMUTABILITY=NOT_RECOVERABLE`。

## 6. 交付及停止

本地完整审查包已形成；公开 payload 是 traceable subset，大型原始现场及完整 qualification closure 保留在本机 continuation 根。`MACHINE_INDEX.json` 给出全部状态与逐门禁账本；最终 manifest hash 和完整字段副本位于 payload 外的 `../FINAL_DISPOSITION.json`，避免循环 self-hashing。

Evidence-only publication 的原审批限制未合法解除；没有获取发布凭据、重试 push 或换工具绕过。Evidence commit/固定远端 URL 未建立，remote verification=NOT_RUN。不得用本地校验替代远端校验。

INDEPENDENT_REVIEW=REQUIRED  
EP19_CLOSED=NO  
PRODUCT_PUBLICATION=NOT_PERFORMED  
POST_PUBLICATION_SANITY=NOT_RUN  
STOP=YES
