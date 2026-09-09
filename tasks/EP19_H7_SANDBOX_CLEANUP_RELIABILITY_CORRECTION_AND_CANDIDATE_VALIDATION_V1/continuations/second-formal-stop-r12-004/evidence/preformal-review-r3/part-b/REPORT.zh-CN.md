# r3 part-b 实际源码与存量证据审查

## 结论

**AR007 OPEN；AR008 OPEN（原接受边界 latch 缺口 RESOLVED，失败归类仍 OPEN）；AR009 OPEN（原 gate/XML/native-log/sealed-copy 调用点 RESOLVED，清理前镜像与失败辅助日志路径遗漏）；AR006 RESOLVED，原 finding 未回归。**

这是 advisory preformal，只读审查，不是正式执行后的独立最终接受。不能以本报告或 writer 134 PASS 声明全部符合、正式可启动。未运行被审代码、测试、probe、preparation、baseline 或 formal；未创建正式 namespace，未消费正式预算；固定产品、正式 1/2 状态保持。所有主动文件输出仅在本 part-b。

已完整读取 Owner 原文、REPAIR_R3_PACKET、r2 part-b、writer r3 final、最终 conformance matrix、当前 binding/qualification；以下均依据 `implementation-r3/tooling` 当前源码与真实保存的日志/receipt，而非 writer totals。源码路径下文简称 `E=implementation-r3/tooling/executor`、`Q=implementation-r3/tooling/qualification`；证据简称 `W=writer-evidence-r3`，相对任务 continuation 根 J。

## 存量证据独立对账

- 当前 tooling 排除 __pycache__/outputs 的 **108 个文件**与最终 runtime binding 和 qualification-004 的 source_binding 精确相等；全部 9 个 dependency source-node hash、7 个 declared helper hash 相符。
- `W/RUNTIME_BINDING.candidate-formal-002.r3.final.json` SHA-256 `b4c7ffba65c6b3b070d767f45ad30c9d372adc24363f93bceb282e7ba597e51b`；其 qualification digest 相符。owner/dependency/qualification/adapter/applicability/private-map/private-inventory hash 均相符。
- `W/qualification-004/QUALIFICATION.native.log` 独立逐行解析：**134 expected、134 expected unique、134 native identities、134 native unique、134 ok**；native 身份/状态与 RESULT.controls 精确一致，expected 集合相等。AST 提取的 **49 mandatory affected controls** 全部存在。原生 exit=0，5 项 dependency hash 均一致（closure 6 包括资格文件自身）。raw SHA-256 `1821f6c780b576c59e13ff9dac72c35f9aa4caf3d75cc97dd50eb26078473de1`。
- 当前保存的 argv 精确为 `USER_HOME/.hermes/hermes-agent/venv/bin/python3 -B <当前Q/build_integration_qualification.py> --output <W/qualification-004> --fixture-root <J/fixtures-r3/qualification-004>`；PROCESS/RESULT/log 同一输出目录，fixture 目录存在。定位 PROCESS.json:2-21。
- 90 个声明 candidate sources 的工作文件和固定 candidate Git blob 均逐文件 hash 相等；当前 HEAD/tree/parent 为固定身份，tracked status 空。必要任务私有 provenance 只读核验：instruction-origin hash、逐包 origin 行、eligible set 对私有 map 均相符；未输出正文，也未读取共享 ledger/usage 正文或凭据。
- `W/red-predecessor-004/NATIVE.log:1-8,29-58` 保存真实 7 FAIL+1 ERROR，PROCESS exit=1；`W/green-focused-002/NATIVE.log:1-13` 为 8 ok、PROCESS exit=0，两者原生日志 digest 各自匹配。**这两组 PROCESS/RESULT 没有 tested-source manifest/hash 字段，精确历史运行字节归属 NOT_ESTABLISHED**；不因 traceback 指向当前路径就把修改前后字节当作已经绑定。qualification-004 则有与当前字节精确相符的 source_binding。
- 机器对账见 `STATIC_VERIFICATION.json`。未声称 writer loader PASS 是本 verifier 重新执行 loader；本次没有导入被审实现。

## B3-007-1 — OPEN：有限实际 helper/readers 图仍有已存在的必经遗漏

已修复 r2 的具体 `vite_resolution.mjs` 缺项：E/runner.py:378-380 → E/vite_resolution.mjs:2-4 → 从 candidate frontend package root 解析 Vite；E/dependency_contract.py:134-173 读取/校验当前 source/helper bytes，:183-187 强制该 helper 与 prepared Vite runtime boundary。当前 rewritten helper 路径已替换历史路径。这些进展不再沿用旧 finding。

**但当前真实 FRONTEND_BUILD 接受路径还有明确的本地辅助进程：**

`E/runner.py:396` → `freshness.require_fresh_outputs` 的 parser callback → `E/parsers.py:41-45` → `E/vite_closure.py:5-9` → **`E/vite_closure.mjs`**。

这个 JS helper :7-9 还从实际传入的 `D/tools` 解析 `acorn`、`postcss`、`postcss-value-parser`、`parse5`。这是现存接受器和实际读者，不是 arbitrary/future plugin。然而 E/dependency_contract.py:134-149 的 9 节点/8 条边没有此链；:164-167 的 required_helpers 精确集合排除了 vite_closure.py/mjs；:185-187 只允许一个 vite runtime boundary。当前 W/DEPENDENCY_BINDING.r3.final-002.json 的 FRONTEND_BUILD command_helper_edges 也只有 vite_resolution.mjs。

源码哈希集合包含这些文件，证明 pin 了版本，**不等于实际读者边已来源化或已给出明确 runtime 委托**。缺失现有 helper 不会被上述 mandatory graph validator 识别为 missing；仍可接受这份 `unresolved_actual_dependencies=[]` 的图。Q/build_dependency_evidence.py:28-33 沿用历史 candidate 列表；:48-55 仅重写历史 helper basename 并加 vite_resolution；:73-95 再复制 command edges、固定声明 unresolved 空。E/dependency_contract.py:174-182 只将该列表和另一个自报列表比较，不从实际 parser/辅助进程链独立对账。

资格 `Q/test_r3_remaining.py:152-157` 只确认旧 r2 schema 被拒，当前 E/dependency_contract.py:130-131 的 stale-schema 分支足以满足测试；不能证明同为 v4、遗漏本次已有 parser/helper 的图会拒绝。存量 qualification log:130 的 ok 不闭合此缺口。

处置范围：应把现存 parser→vite_closure→task-local parser packages 的有限来源与委托边纳入，而非要求任意未来插件或第三方全体源码安全；保持原有 runtime preparation 排除边界。

## B3-007-2 — RESOLVED：资格完整 argv 与逐身份强制路径

E/coverage.py:122-174 对 fresh qualification 执行 source/dependency hash、PROCESS/log、结果、mandatory controls、原生日志身份核验。:145-155 要求精确完整 argv（Python、-B、程序、flag 顺序及值），并对账输出目录和 fixture；:156-167 逐原生 identity/status 核验，不只 tests/PASS。E/qualification_contract.py:57-95 拒绝 expected/actual duplicate、missing/unexpected、failed/errored/skipped、invalid status，且 mandatory 集合为固定 AST 集合。

该路径真实必经：E/external29_driver.py:34-39 → E/binding_contract.py:58-65 验证 dependency 与 binding；driver engineering_preflight :205-220 调 coverage.qualification_inputs，异常阻止 ENGINEERING_READY。实际 qualification-004 argv 与路径自洽。Q/test_r3_remaining.py:159-197 的 extra-flag 负控调用当前 loader，保存 log:129 为 ok。此子项不再 OPEN。

## B3-008-1 — 原 latch 缺口 RESOLVED；B3-008-2 — 归类 OPEN

**已修复关键 seam：**E/runner.py:411-412、442-444 把 gate 内异常转为 FAIL 后，E/external29_driver.py:240-250 立即走 FAIL 分支，调用 adapter.fail，完全不进入 COMMAND_AFTER/COMMAND/GATE；:251-254 对直接异常也 latch。E/executor_adapter.py:108-119 先设置内存 failed，再写 marker；marker 写失败也不能解除失败；:43-50 保留 latch。driver :291-299 在 stopped 时拒绝成功 FINAL/COVERAGE/SEAL。

E/boundary.py:217-229 仍先持久 private/public evidence 后才推进 session/previous_usage/clocks，adapter :95-105 捕获 capture/evaluate/write/binding 异常。原接受推进缺口 **RESOLVED**。保存 qualification log:131 为真实 actual-run_gate 控制成功；Q/test_r3_remaining.py:199-224 调 actual driver/runner，但在 check_execution_seal 注入 OSError、把 strict/boundary 换成 spy，因此证明的是返回 FAIL seam，**没有实际启动 fixture native command**，不覆盖以下复合归类。

**剩余归类错误：**E/external29_driver.py:242 仅凭 native_exit 非零将整个失败判成 `NATIVE_PRODUCT_FAILURE`。E/native_observe.py:292-297 在 watcher 拒绝或 timeout 时由外部 observer 主动 SIGTERM/SIGKILL native child；:331-332 同时保留 nonzero rc、timeout、events/gaps/observation_errors、wrapper_exit。E/runner.py:388 把这些 observation 字段并入 r；freshness.py:21 因 process/preservation 拒绝抛异常，runner :411-412 吞回 FAIL，却不传失败原因类别。结果由保护失败导致的终止会被 :242 标成产品失败；非零 native_exit 同时发生的 seal/evidence 异常同样被覆盖。

这不是 FAIL 可变 PASS 或继续接受问题，latch 已修；问题是 Owner:298-299 与 R3 packet:10 要求的产品/保全/环境区分未保留在新增 authoritative failure_class。应优先传播明确的 integrity/environment rejection，并保留 native exit 独立事实。实际非零 native + preservation/integrity 复合路径存量专门资格 **NOT_ESTABLISHED**。

## B3-009-1 — 原指定发布点 RESOLVED；B3-009-2 — 仍有必需失败证据绕过

已成立的实际调用：

| 路径 | 源码证据 |
|---|---|
| gate namespace 发布 | E/runner.py:330 → durability.exclusive_directory :34-40，同步 gate 与发布它的 gates 父目录 |
| XML 嵌套归档 | runner.py:300-305 → exclusive_bytes，ensure_directory :16-30 逐层同步新增目录及父目录 |
| 主 native 与 aux observe log | native_observe.py:288-313 → exclusive_stream :77-93，flush/file fsync/parent fsync |
| 不可变 sealed artifact copies | artifacts.py:29-37 → exclusive_directory/exclusive_bytes；:73-80 verify/recheck 后才 PASS |
| probe args/init | runner.py:79-82、365-366 → exclusive_bytes |
| consume/private/public/failure | driver.py:41-55；adapter.py:23-25,66-85,108-119；boundary.py:217-229；统一文件+父目录 helper |

exclusive_bytes :59-74 使用 O_EXCL/O_NOFOLLOW、处理 partial write，文件 fsync 后父目录 fsync。consume :47-55 保留既有 marker 阻止复用及目录链同步；失败 marker 写不出不使当前 adapter 继续。BOOTJAR 独占 copy、来源 recheck、Git→resources→sealed JAR 校验保留于 runner.py:415-441、artifacts.py:7-18,29-50。

**但必经 cleanup preservation 仍没有 durability：**E/runner.py:346-350 在清除上一次产物前调用 E/freshness.py:7-17；:13-14 普通 mkdir/open/write 清理前镜像，:15 读 hash 后 :16 立即 unlink 原产物。没有镜像 file fsync、cleanup-preimages 目录 fsync 或父链同步；:17 durable cleanup.json 仅同步其直接 gate 父目录，不递归同步镜像。后续若 native 失败，runner :415-416 根本不调用 artifacts.finalize；失败证据长期留在未同步镜像中。即使成功时 sealed copy 最终同步，也不能追溯保证“删除原件之前已持久保存清理镜像”的顺序。这属于已有清理保全契约（bindings.py:60）的现存调用，不是产品改动或新增 gate。

**同一遗漏还有真实辅助失败日志：**E/parsers.py:45 → E/vite_closure.py:7 用普通 open('xb') 保存 `.native.log`；:8 在 parser 失败立即抛异常。对应 JS :93 普通 writeFileSync 保存结果。成功时 artifacts.files(gate)→finalize 的 durable 独立 copy 可补成功证据，因此不误报“所有成功 Vite copy 都不 durable”；但失败时 runner 跳过 seal，原生辅助失败日志没有 file fsync。r3 writer 所谓所有 native logs 已统一仅覆盖 observe.run，不覆盖这个实际 subprocess.run。

Q/test_r3_remaining.py:226-250 检查 gate 父目录和直接 artifacts.seal，实际 fsync_directory 被 spy 包装后仍调用真实函数；其 log:132 ok 可证明指定修复点，不证明 cleanup failure/parser failure 全路径。此处为静态 durability 保证缺口；未运行掉电实验，也不声称每次崩溃必丢。

## AR006 与 native29 回归

**AR006 RESOLVED（原 finding 保持）**：E/external29_driver.py:425-431 formal CLI 无 bundle/coverage/strict 摘要注入入口；:267-284 绑定实际私有输入并从实际 policy/observer 建立 adapter；:99-114 boundary 强制真实 observer 数据及 evidence_dir；E/boundary.py:114 默认实际 capture_bundle。内层 fixture 参数仍非正式 CLI 入口。没有把 AR007 依赖语义缺口重命名成 AR006。

native29 对 r2 无命令/矩阵语义 drift：execution.py、bindings.py、matrix.py、GATE_EXECUTION_MATRIX.json、parsers.py、compile_inventory.py、packaging.py、freshness.py、vite_closure.py/mjs、lean_materialization.py 字节一致。runner diff 仅 init、XML、gate directory、probe args 的 durable publication 替换；native 主命令、timeout、H733、freshness/completeness、frontend closure、Git→resources→JAR、独占 BOOTJAR 副本、checkout/output 隔离未弱化。矩阵 SHA-256 `57c727549bc818bbcdc8c79c2babee3096f9ca2d058df0713033b6e49a42466e`。bindings.py:49 的每 gate 3600 为既有原生 gate timeout；无新增全 attempt 3600 上限。8000/29 仍为 EXPECTED，不是此次产品执行结果。

## 边界与交付

- 固定 candidate `a29864343ed4f630b052c20d86c23b240f13cfd0`、tree `fd37409d0274662abbe86f69e3d963c05b379696`、parent `689ab9456461a8d19a72d059f5157092efc43aff` 已 read-only Git 对账；patch 仅核对 binding 固定值，本 part 未重新计算产品 patch。产品未修改。
- Owner 已接受的 ledger 捕获间 overwrite-restore/truncate-regrow 限制保持原边界，未重新列为 defect，未扩展到其它 protected 对象。
- 本 part 不复跑任何产品/资格/正式测试、不发布、不修改 shared skills/memory。历史 focused RED/GREEN 逐行真实结果可确认；其确切 tested-source 字节缺少自足绑定，保持限定，不影响当前 qualification source 对账。
- 文件：本报告、FINDINGS.json、STATIC_VERIFICATION.json、REVIEWED_SOURCE_DELTA.patch、source-hashes.before.json、source-hashes.after.json、HASH_VERIFICATION.json。源码前后完整性结论见 HASH_VERIFICATION.json；源码最初读取后建立 before，后续未执行被审实现。以上不宣称全历史目录已重新验收。
