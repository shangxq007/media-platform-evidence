# r6 Part A — AR008/AR010 只读 advisory preformal 审查

## 结论

**AR008 / AR010 全范围 CLOSED 不获支持；处置为 OPEN / PARTIAL。** r5 的明确 sequential cleanup、fdopen ownership、helper+fsync、attached receipt+marker merge、主进程已退出后的正常 owned-descendant 异常收尾均已有实际修正；但实际调用链仍有下面三个具体遗漏。保存的 161 PASS 可独立静态对账，不能替代遗漏路径的符合性证明。AR001..006 的既有规则与已存回归保持支持。

这是 advisory preformal，不是 final independent acceptance 或正式启动许可。全文读取 Owner authorization、REPAIR_R6_PACKET、r5 Part A、r6 writer final report 和 final matrix。仅源文件/保存日志/JSON/AST/字节及 hash 读取；未导入或执行被审代码，未运行测试、probes、preparation、baseline、formal，未扫描或杀进程，未读取共享 ledger/usage、私有清单正文或凭据。写入仅在本 part-a。E=implementation-r6/tooling/executor，Q=implementation-r6/tooling/qualification，W=writer-evidence-r6，均相对 J。

## 1. 精确 r5 residual 处置

| r5 issue | r6 disposition | 来源与范围 |
|---|---|---|
| A5-010-1 BoundaryObserver/ancestor cleanup | PARTIAL / OPEN | E/observe.py:158-173 保留 constructor primary 与自身 close；preservation.py:39-59 在获取 nxt 后立即加入 owned list，逐 fd 独立 close；directory_inventory:182-188 / Collector:110-114 同样尝试 close。但嵌套因果落盘仍丢失，且 capture_file 新的窄 except 可跳过 release，见 A6-008-2/A6-010-1。 |
| A5-008/010-2 durable stream composition | 精确缺陷 RESOLVED | E/durability.py:144-165，fdopen 在 ownership guard 内，closefd=False，body 捕获 BaseException；flush/file fsync/stream close/raw close/parent fsync 分别 _attempt。:22-42 保留 primary 类型（仅 primary 无 cleanup 时直接重抛）、复合行和 primary dimensions。:53-62,106-140 扩展到目录 sync、exclusive bytes、existing file。E/vite_closure.py:15-24 → parsers.py:22-29 → runner.py:340-380 不把带 dimensions 的 helper+evidence group 改判单一 product。Q/r6:68-138 的真实 fd/stream + fault seam 支持该组合；subprocess.run 返回非零是 mock，不是真实 node helper 执行。 |
| A5-010-3 exception after main exit | 普通实际分支 RESOLVED；完整异常 cleanup 仍 OPEN | E/native_observe.py:411-419 不再受 child.poll()==None 限制，先 cleanup descendants 再 :420-425 独立 restore ChildScope/close Watch。:263-275 的 prior exclusion 和 retained birth、:297-311 的信号前身份检查支持已声明 serialized owned scope；但 discovery/birth 失败仍短路已知 owned resources，见 A6-010-3。 |
| A5-008-4 attached receipt + marker | 精确缺陷 RESOLVED | E/external29_driver.py:248-266 不再 receipt early return 后漏 marker；:282-301 合并 causal/secondary、标记 uncertainty；:373-379 latch→merge→sanitized log→FAIL stop。:305-313 不输出异常 reason/path。Q/r6:190-221 同时携带 attached receipt 与 marker failure，保存 PASS。该 control 的 runner/adapter 为 seam 替身，真实 adapter:44-56 会附加失败 marker 属性，静态路径对得上。 |
| r5 aux receipt 补充 seam | 精确缺陷 RESOLVED（静态） | E/runner.py:324-336 在 aux receipt put 失败时携带原 native receipt/dimensions，并给正常 aux REJECT 附 receipt。未把本轮九项 controls 宣称为独立 aux compound GREEN。 |

r5 已解决的 strict_baseline failed handoff、formal 两资源独立 cleanup、native Watch constructor group、产品/环境/helper 分类、postseal failure supplement 未撤回。E/external29_driver.py:316-323,431-477；native_observe.py:44-48；r5 controls 在保存的最终 161 中全部 PASS。AR009 这里只保留旁证，不代替 part-b 最终专项处置。

## 2. 仍 OPEN 的具体实际路径

### A6-010-1 — capture_file 将 finally 改成窄 except 后的语句，取消/非预期异常会漏 fd

E/capture.py:155-156 已获取 fd；:147-188 的读取、分配、hook、hash 阶段只有 :189 `except (OSError, CaptureError)`；:196-201 的 close 已不在 finally 中。因此例如读取中 KeyboardInterrupt，或 chunks.append/join 分配 MemoryError，会直接越过 raw fd release。它不是任意未来 plugin 要求：E/bookkeeping_v3.py:18-20 的真实 bundle/manifest 获取使用此函数；取消和采集异常正是当前所有 owned resource 收尾范围。r5 的 finally 至少保证进入关闭；r6 引入了这一窄类型回退。

Q/test_r6_remaining.py:104-113 的 body fault 明确只抛 CaptureError，刚好进入窄 except；其 PASS 不能证明 BaseException/其他 Exception 释放。应保留原 retry 分类，同时对所有离开 acquired-fd 区域的路径独立 release 并保留 primary/cleanup；不要求盲目重试失败 close。本 finding 为静态可达性，未运行 fresh RED。

### A6-008-2 — group 在真实嵌套 capture→receipt 链中退化为摘要，leaf 原因/类型丢失

E/preservation.py:18-28 `_raise_owned` 即使只有 primary 且 cleanup=[] 也新建 BaseExceptionGroup；其 causal_errors 仅以 `str(primary)` 记录，不递归继承已有 group rows。一次 directory_inventory 内层 stat/read/close 异常会经 :182-188、parent_fd:52-59 再包装，外层 primary 只剩“... (N sub-exceptions)”的 group 摘要，而不是原始 OSError/CaptureError 的类型/原因。

更关键的真实交付路径：Collector.read:110-114 → Collector.capture:123-129 → Collector.error:71 仅保存 type/errno/str(e)，丢掉 group 子异常与 causal_errors；capture_files:139-142 只从该 errors JSON 建 RuntimeError；native_observe.snapshot:10-12 → run:337/368，再丰富的 native receipt 已无法恢复被丢弃的原始 read/stat 与 close 细节。该问题连“只有 primary、无 cleanup”也受 `_raise_owned` 无条件分组影响，不能声称所有 helper 保持原异常类型。

另一条对应的实际 boundary 入口：capture_file/capture_directory 的 group → E/boundary.py:144-145，`_reason`:24-25 只取 type+str；写入 :209 的 reasons 只有 group 摘要。compound evidence 写失败在 :220-223 也转成通用 BoundaryReject，异常 context 不等于结构化 causal proof。

Q/r6:15-20 主动遍历 exceptions，:40-66/104-113 直接检查内存 group 的 flattened 文本，未经过 Collector.error/capture_files/boundary 的实际落盘转换。故测试真实 PASS 与实际 structured diagnostics 丢叶子原因可以同时成立。这个遗漏仍属于 r5 A5-010-1 原始+secondary 完整保留要求，非新增 after-cutoff 规则。要求沿实际嵌套和最终 receipt 路径保留叶子原因、类型及角色，不仅 Python traceback 中可见。

### A6-010-3 — descendant discovery/identity 故障仍可跳过其他已拥有 PID；部分 uncertainty 被泛化

E/native_observe.py:263-274 `pending()` 先按 children 查询逐个 birth，直到全部完成才返回。单个 birth 的 PermissionError/OSError、或 :269 OWNED_PID_REUSED，会中断该轮，尽管 `scope.known` 可能已有其他可安全重新验证的身份。cleanup_owned_descendants:287-291 捕获后设置 pending=[]，不尝试 retained known 集合；在期限内反复 discovery 错误会让其他已知 owned 子进程从未获得独立清理尝试。:290-291 还把 pending 的 OWNED_PID_REUSED 放进 DISCOVERY_UNKNOWN（保留 reason，但不是独立 PID_REUSED kind）。

即使 pending 成功，:297 `scope.birth(pid)` 位于 :304-311 信号异常保护之外。一个 pid 的 birth permission/unknown 异常立即退出整个 cleanup，余下 pending 身份被跳过；run:419 仅收一个 generic cleanup error，descendant_cleanup 仍为 None，:416 未更新 pending，:445 的 remaining 可保持旧值/初始空列表。失败不被接受，但“实际 owned cleanup 完整尝试 / remaining 与未知明确区分”并未闭合。

Q/r6:177-188 虽命名 unknown_permission_and_timeout，实际只 mock os.kill PermissionError，Scope.pending/birth 永远成功；未覆盖 discovery permission、birth permission、PID reuse、多个 identities 中一项失败后的独立收尾。

此处不要求杀身份未知/已重用 PID，也不要求清理无关 children。应对每个已保留身份分别复核、独立尝试可安全执行的 cleanup，明确记录不能复核者及剩余不确定性；不能让一项不可验证阻断其他已验证 owned identities。既有 prior-child 排除和串行调用所有权假设保留。

## 3. 真实 descendant fixture 与声明边界

Q/r6:140-175 确实执行 native_observe.run/真实 Watch，child 脚本 Popen 一个 start_new_session=True descendant，写 PID，主进程在短暂等待后退出；第二 drain 经等待后抛异常。GREEN 断言 returned exception receipt 含 terminated PID、remaining=[]、cleanup QUIESCENT、os.kill(pid,0) 得 ProcessLookupError。finally 有防泄漏清理，但成功断言在其之前，因此不是 fixture finally 替生产 cleanup 过关。RED W/red-predecessor-004/NATIVE.log:69-74 保存主进程 native_exit=0、descendant 未清理的实际失败 receipt。GREEN 正常结果不逐字段打印成功 receipt，故成功 PID/birth 具体值只由该执行 control 的断言/源码约束支撑，不编造另一个原生明细回执。

scope.children 读取 /proc/self/task/*/children，排除 prior，并保存 birth（E/native:247-275）；新异常 helper不全机 pgrep/kill。需纠正 writer 全面“无全机扫描”的措辞：继承的正常流程仍有 tagged_processes :231-239 遍历 /proc，再于 :357 与 owned children 合并。这里只确认新异常收尾的 task-owned 范围，不据此增加全机无无关变化要求，也不将旧 tag 路径宣称为全程 birth-checked。

## 4. AR001..006 保留

- AR001 RETAINED_RESOLVED（既有批准范围）：E/driver:68-122 最后 capture callback/identity/drain/共同 cutoff/stop-drain 判定与 r5 相同；:410-421 保留 baseline→preflight→prestart→command/gate→FINAL/COVERAGE/SEAL。observe.py 唯一 r6 delta 是 constructor catch；正常注册、temp/drain、结束队列规则未变。不要求 cutoff 后继续观察。
- AR002 RETAINED_RESOLVED：driver:59-66,396-403 seed→bind；observe:85-100 双向非零 cookie 与 source/target配对，:254-277可见 temp metadata，bookkeeping_v2/v3 字节与r5相同。真实合法 visible temp rename及非法外移入/移出/mode controls仍在161 PASS。
- AR003 RETAINED_RESOLVED：boundary:104-137实际wall/monotonic、previous accepted lower/rollback；文件与r5字节相同。
- AR004 RETAINED_RESOLVED：bookkeeping_v3.py与r5字节相同；既有原始 framing、UTF8/keys/constants及 escaped CR区别的 controls在161 PASS。
- AR005 RETAINED_RESOLVED：boundary:96-97,149-150,217-229，previous usage 与 session/time 只在 evidence 成功后提交；合法usage变化后unchanged控制保留。
- AR006 RETAINED_RESOLVED：formal:382-415仍只由实际observer/capture/policy/binding构造输入，不暴露bundle/strict/coverage摘要注入；executor_adapter.py与r5字节相同，latch/consume/no resurrection保持；未扩张为任意Python调用不可注入。

bindings/execution/matrix/packaging/compile_inventory/lean_materialization 与r5字节相同；native29/timeouts、COMPILE/BOOTJAR/跨run隔离/assets/static→resources→JAR/Lean没有在本轮替换规则。AR007有限已绑定graph专项不在本分项重新签认。Owner已接受ledger捕获间overwrite-restore/truncate-regrow限制保留，仅限该ledger；不扩展到Memory，不重开为缺陷，不新增3600秒attempt上限。

## 5. 保存证据独立静态对账

详见 RECEIPT_CHECKS.json（程序统计/比较，不靠报告计数）：

- RED predecessor-004：9 unique，8 FAIL、1 ERROR，native=1/wrapper=0；raw log identity/status 与 RESULT/PROCESS一致。ERROR是r5没有新cleanup_owned_descendants函数的 AttributeError（log:12-18），不是已执行了unknown/permission检查；不可计成该行为的真实RED。
- GREEN focused-006：相同9，9 PASS，native=0/wrapper=0；74 source bindings before=after，当前74非private文件全部hash匹配。
- selected test body RED/GREEN/current 一致：52b8f8a633d5529c8770c03ffaa083b5cd704051db4f43c6a27207a933427591。RED绑定73项，当前4个支持文件已不同（build_dependency_evidence.py、run_source_bound_group.py、test_conformance_corrections.py、test_r4_remaining.py）。r5 executor及实际选择的r6测试体仍匹配；不把未执行支持文件或后来wrapper源码假称RED当时加载字节。
- integrated qualification-005：161 expected /161 native unique /161 PASS，missing/unexpected/duplicates及非PASS为0；RESULT额外有expected/time字段，以id/actual投影比较与原生日志一致。76 mandatory从qualification_contract.py AST重新提取，与receipt一致且全部执行。PROCESS log/result hash正确，QUALIFICATION五dependency hashes正确，matrix accounting相等。
- integrated source mapping 113 before/after相等；本分项核验80个非candidate-inputs/非private条目的当前字节全部一致，33个candidate-inputs仅作为绑定摘要，没有读正文、不提升为完整private依赖复核。
- parent wrapper Q/run_integrated_parent.py:24-46 在Popen前/communicate后取manifest、记录真实child.returncode/PID/argv/cwd；保存parent receipt为PID9、native=0/wrapper=0、21.353877741s，parent log/result hashes以及113项source maps都与integrated绑定相等。builder:6-7在内部source snapshot前import的限制现有parent prelaunch binding补足；内部self-written PROCESS仍不是独立OS launch证明。本reviewer没有重新launch，保存writer parent receipt也不等于本次最终独立接受。
- runtime final-003 SHA256=000519c86183cccb2c326d27f023435fa58745f7a7076eef873be83a74538283，qualification/dependency digest和source map匹配。W/runtime-loader-004/VALIDATION.json保存PASS；没有重跑loader或prepare，binding不豁免上述遗漏。

## 6. 固定状态与交付

绑定产品SHA a29864343ed4f630b052c20d86c23b240f13cfd0、tree fd37409d0274662abbe86f69e3d963c05b379696、patch bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690 与Owner一致；本分项不声称fresh Git重物化。产品3/3、formal1/2依委派保持，未消费第二次尝试；8000/29仅EXPECTED。writer“仅剩formal”的无保留结论不获本分项支持。

未改source、历史、共享状态；仅EARLY.md、EARLY_FINDINGS.md、本报告、RECEIPT_CHECKS.json和source/hash回执写入当前part-a。读取曾遇输出截断，按范围补读；JSON对账首次直接比较含额外时间字段的RESULT与投影产生false，已按id/actual纠正，非候选错误。所有结论是已保存证据+静态实际路径审查，三个OPEN均未冒充新执行反例。
