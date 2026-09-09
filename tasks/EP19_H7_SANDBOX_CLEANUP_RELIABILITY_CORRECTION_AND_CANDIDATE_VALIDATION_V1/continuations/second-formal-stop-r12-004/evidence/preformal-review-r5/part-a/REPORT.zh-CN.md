# r5 Part A — 只读 preformal 符合性报告

## 结论

**AR008 / AR010 的全部失败路径闭合不获支持（OPEN / PARTIAL）；精确 r4 外层 sequential cleanup、native Watch 构造聚合、单独 parser 分类、普通 gate marker / final receipt seam 已有真实修正。AR001..006 既有批准范围的回归保持得到支持。保存的 152 PASS 真实可对账，但不能覆盖下面仍存在的具体复合故障/资源路径。**

本报告是 advisory preformal，不是 final independent acceptance，也不是正式启动许可。仅静态阅读、AST/JSON/log 解析、源码字节比较和 SHA-256；未导入被审实现，未运行测试、探针、preparation、baseline、formal，未读共享 ledger/usage、私有清单或凭据。仅本 part-a 报告/hash 文件写入。Owner 全文、REPAIR_R5_PACKET、WRITER_PACKET、两份 r4 完整报告、r5 writer report/matrix 已读。E=implementation-r5/tooling/executor；Q=implementation-r5/tooling/qualification；W=writer-evidence-r5，均相对 J。

## 1. 精确 r4 residual 的处置

- **A010-R4-FORMAL-FINALLY：特定缺陷 CLOSED_SUPPORTED。** E/external29_driver.py:284-291 对 continuous、observer 分别 try/except BaseException；:398-438 收集 body、失败证据、资源清理错误并聚合，:439-445 最后才发布正常 RESULTS。第一个 close 抛错不再跳过第二个，清理失败不返回成功。Q/test_r5_remaining.py:84-191 调真实 formal 控制流，但模块/consume/policy/observer/strict_baseline 是 fixture 替身；两独立 controls 对第二次 close 和 primary+两 cleanup 检查，不是正式执行或真实 fd close 的全路径证明。
- **r4 strict_baseline failed handoff：RETAINED。** E/driver:170-211 在 watch acquisition 后的整个 pre-return 区间负责本地关闭，原始与 close 错误聚合；只有成功 tuple 返回才交给 formal。r5 未撤回该修复。旧 r4 control 在最终152中 PASS。
- **native Watch constructor：特定缺陷 CLOSED_SUPPORTED。** E/native_observe.py:44-48 聚合 add/constructor 与 fd-close 两异常。Q:193-210 实际获取 Watch，注入 add 错误和先真实 close 再抛错。该控制不是 BoundaryObserver 构造器测试。
- **B4-008-1：单独 parser I/O/env/helper 分支 CLOSED_SUPPORTED；复合故障仍 OPEN。** E/parsers.py:19-29 和 vite_closure.py:12-31 将 I/O、node launch、helper nonzero 与产品断言区分；runner:348-369,442-474 传播维度，不再仅凭整个 parser stage 判成 product。Q:272-331 分別检验这些 seam。产品断言 control 在 RED 已 PASS，应称保留回归，不称新修正。
- **B4-008-2：普通单独 seam 修复，不能整体 CLOSED。** native:372-403 附带 child pid、已观测 exit、termination、timeout、events/errors/gaps、cleanup 到异常 receipt；runner:463-474 接收；:530-538 final receipt 写失败携带 prior r；driver:262-281 在普通 FAIL result 后 marker 失败保留 gate 主原因。Q:212-244 实际 native 子进程退出0，加退出 stream 后注入的 OSError及真实关闭后注入的 cleanup 错误，证明这个分支，不证明观察中异常/全部复合链。Q:333-423 的 marker 与 receipt 是两个分开的 fixture controls。
- **B4-009-1：本分项对特定 postseal 补封修复提供旁证。** E/artifacts.py:86-143 在原 sealed 已存在且验证成功时独占建立 failure-supplement，绑定原 seal digest/run/gate/candidate/tree/details；runner:510-529 保留原原因并另记 supplement 写失败。Q:425-494 真正先 seal 再使 after_copy 检查失败；原 seal 验证及 supplement 绑定均有保存 PASS。详细 AR009 最终处置由 part-b 汇总，不把本观察扩展到所有存储故障闭合。

## 2. 当前范围内仍存在的实质遗漏

以下均为**真实源码可达分支的静态 findings**，不是本 reviewer 运行的反例；不得写成已有 fresh RED。全部属于 Owner 既有失败核算/owned cleanup要求，不要求新契约、任意未来 plugin、after-cutoff 观察或全机无关进程证明。

### A5-010-1 — BoundaryObserver 与祖先 fd 清理仍是旧式替换/短路

E/observe.py:148-160：构造过程中 directory_inventory/_add 失败后 `self.close(); raise`。若 close 同时失败，原始 constructor 错误成为隐式 Python context，而不是稳定的聚合/receipt causal chain。formal:363 的赋值不会完成，outer observer 仍为 None，:415 不会取得此资源；formal failure :402-406/causal_rows :248-259 不遍历 __context__，故结构化原始原因缺失。Q/r5 constructor control只覆盖 native Watch，不覆盖这个实际 formal 首个 observer。

E/preservation.py:25-41 的 parent_fd 同时拥有全部祖先 fds，finally 的 `for fd in reversed(fds): os.close(fd)` 无独立保护；一个 close 抛错跳过余下所有 fd。此非未来调用者：native Watch.add :56-61 及真实 directory_inventory :159-160 直接使用它。父级 Watch.close 不能关闭 parent_fd 的其他局部 fd。类似 capture.py:177-180,202-203 及 preservation.py:91,158 的单 fd finally会替换原始失败，虽不涉及第二资源跳过。**“所有 owned cleanup 独立尝试/原始与 secondary完整保留”不能据 outer helper 通过而宣告完成。** 不要求盲目重试失败 close；要求其他已拥有资源不被跳过、错误因果保留。

### A5-008/010-2 — 实际 durable stream 仍会短路清理并覆盖复合 helper/native 原因

E/durability.py:97-108：fdopen 在保护 try 前；若 fdopen 失败，原始 fd 没有收尾。finally 内 stream.close、os.close(fd)、fsync_directory(parent) 仍顺序执行；stream.close失败跳过 raw fd关闭及parent sync；raw close失败跳过parent sync。flush/fsync/body 的原始异常也可被后续 cleanup替换。exclusive_bytes :63-73、sync_existing_file :81-88 / fsync_directory :10-13 同样不聚合原始与 close错误。

更直接的 AR008 因果丢失：E/vite_closure.py:15-24 在 stream body 中已经产生 `ViteClosureFailure`（node launch环境错误或helper非零），随后真实 exclusive_stream 的 fsync/close又抛 OSError，外层只生成 LOG_PERSISTENCE_FAILURE，丢掉原环境/helper维度；ParserFailure、runner._causal_rows不会遍历它的隐式 context，因此正式 gate结果只保留后一个维度。Q:307-321 的 fsync control在 `yield` 之前抛错，既没有 child/helper主失败，也没走真实 fsync cleanup。独立 GREEN 并未覆盖此复合情况。

同一个真实 stream 在 native:295-325：观察 body先抛错时stage不会到 EVIDENCE_LOG_FINALIZATION；退出context又fsync失败，native:380仍按 PROCESS_OBSERVATION/PROCESS_LAUNCH归类，可能漏 evidence维度且原观察错误被替换。不能把“正常流结束后额外注入fsync失败”的 Q:219-223提升为该路径证明。

### A5-010-3 — 异常退出没有收尾已拥有的 descendants

E/native_observe.py:310-322正常流用 tag+ChildScope.pending 识别并收尾 owned descendants。新 finally :357-365 仅在主child尚活着时 killpg/wait 主child；:366-368 的 ChildScope.close (:276-277)仅恢复 subreaper标志。若主child已退出，后续 descendant drain/pending/resolve阶段抛错，异常收尾不再枚举/等待/终止既有 owned descendants；即使主child尚活着，已setsid的 adopted descendant也不由主group kill保证清除。不是对无关进程的要求：ChildScope自身 :242-246 明文承诺覆盖已脱tag/setsid/chdir的 adopted descendants，并已有 prior/birth归属隔离。

在异常循环开始前 pending 初值为[] (:285)，exception receipt :388可保存这个未重新核验的空列表。保留字段不等于实际quiescence成立。Q:233的child仅`pass`，没有descendant异常控制。需保留已批准owned-process模型，不能把残留子进程当完成收尾；本reviewer未扫描或杀任何进程。

### A5-008-4 — final receipt失败再叠 marker失败时，secondary仍掉出结果

E/runner.py:531-538的错误已带 runner_gate_receipt；driver:342先调用真实 adapter._latch_exception，marker失败被 adapter:50-56附加到异常.failure_marker_errors。随后 merge_graph_exception :263-275选择 attached receipt，并仅当 `not isinstance(attached,dict)`时合并 causal_rows，因而新 marker错误未进入返回结果。causal_rows本身 :249-252 在receipt有causal_errors时也早返，未到:258。adapter内存与异常属性短暂持有信息，但 driver吞异常返回 results 后，FORMAL summary不序列化 adapter.failure_marker_errors；marker恰未能落盘，故该secondary可最终无交付记录。

这不造成继续接受：adapter.failed已置True，driver停止下一gate/成功FINAL。但违反本轮特意要求的“receipt失败+marker失败”完整原因保留。Q:371-423使用只置failed的Adapter，不注入marker写失败；Q:333-369则是普通returned FAIL，无attached receipt。两项分别PASS不能证明组合通过。

补充同类可达 seam：runner.aux :324-327 在已得到辅助native receipt后，receipt put失败未附带该已观测r；普通aux拒绝也仅抛AUXILIARY_PROCESS_REJECT。主runner :406或:423此时仍在INITIAL_ACQUISITION，不接收这些正常返回aux的独立protection/timeout/exit维度。已有成功写出的aux receipt可单独阅读，但复合receipt写失败时不得声称gate因果链完备。

## 3. AR001..006 回归与契约边界

- AR001：driver:68-122仍从capture/evaluate到final callback、最后identity check再drain、共同cutoff、stop/drain后durable决策；formal:377-388覆盖baseline、preflight、prestart、command/gate、FINAL/COVERAGE/SEAL。native Watch注册/事件/drain/identity/stop段相对r4不变（仅constructor分组及run异常receipt改动）。Q/r3:100-131真实最后identity期间写Memory并查最终事件拒绝，最终152 PASS。前述failure cleanup不足不能反向宣称正常连续观察回退。
- AR002：observer_seed :59-66、formal:363-370真实seed再bind；observe.py相对r4完全不变，精确temp元数据、路径、非零cookie双向生命周期及边界状态保持。Q/r3:133-150真实合法temp可见后rename且PASS；外移入/移出/非法mode负控在最终152 PASS。
- AR003：boundary.py:104-137实际wall/monotonic capture窗口、前次accepted lower、rollback拒绝保持；Q/conformance:129-144仍验证回退与future timestamp。无datetime.max/新attempt总时限。
- AR004：bookkeeping_v3.py字节不变；raw framing与UTF8、duplicate keys、常量检查保持。Q/conformance:146-166区分真实CRLF/raw CR与escaped CR；最终PASS。
- AR005：boundary.py:96-97,149-150,217-229保持previous accepted usage，并仅在evidence成功后commit session/usage/time。合法usage变化后unchanged后续边界路径保留，最终integrated fixture/positive controls PASS。
- AR006：实际formal仅内部Watch/capture/policy/binding，不开放bundle/strict/coverage摘要入口；通用Engine fixture API不当成正式CLI注入。coverage.py及qualification mandatory/accounting guard保持（新增13 mandatory）；消费marker仍先于baseline。latch在任何后续成功边界前生效。未证明任意Python调用不可注入，也未声称正式执行已发生。

observe.py、boundary.py、capture.py、bookkeeping_v3.py、preservation.py、coverage.py与r4字节相同；bindings/execution/matrix/packaging/compile_inventory/lean_materialization也相同。既有native29命令/timeout、COMPILE、BOOTJAR、Git→resources→JAR、Lean等未因本轮更换；没有重开已接受ledger捕获间overwrite-restore/truncate-regrow限制，也不把该限制扩大到Memory。AR007有限graph/parser准备等详细结论不在本分项重新签认；未读取private来源。

## 4. 保存的真实 RED / GREEN / final qualification

独立解析native log身份/status，与RESULT.controls、PROCESS control_ids/statuses和hash对账（机器计算见下）。

- W/red-predecessor-003：13 unique，10 FAIL、2 ERROR、1 PASS，native=1/wrapper=0。完整raw log显示行为/返回字段断言失败；constructor ERROR是真实r4 close替换add错误，supplement ERROR是返回缺字段，不是模块导入失败。cleanup聚合control在RED仍先停于observer.closed断言，不能声称RED已逐条执行后面的三个message断言。
- W/green-focused-005：相同13，全部PASS，native=0/wrapper=0。72 before/after bindings相同且全部当前字节一致。真实node helper负控、真实native子进程及真实seal存在；其余mock seam范围已逐项说明，不是完整产品执行。
- W/qualification-003：152 expected /152 unique native /152 PASS，0缺失/意外/重复/非PASS；67 mandatory从qualification_contract AST重新提取，与receipt一致、全部实际执行。native与RESULT顺序identity/status完全一致。PROCESS raw/result hashes正确；QUALIFICATION五项dependency hashes正确；matrix accounting相等。111绑定条目before/after相等；本分项仅验证其中78个非candidate-inputs文件当前字节，全部一致；33个candidate-inputs条目未读正文，不提升为全private/candidate依赖复核。
- focused wrapper Q/run_source_bound_group.py:58-78在fresh Popen前后hash实际executor+test root，Q/test_r5_remaining.py:19-25 TARGET导入和:78/286/301 explicit file loader确实指向r4或r5。RED的72 entries中70当前相符；两个未执行的其他qualification文件test_conformance_corrections.py/test_r4_remaining.py后来变更，不能声明RED整个test-root仍与当前完全一致。实际运行test_r5_remaining.py digest仍相同；r4全部executor、dependency均相同。RED/测试本体归属支持，未回填历史。两份其他文件后来差异不影响这个仅导入test_r5_remaining的focused replay；不编造它们当时的源快照。
- integrated builder :6-7在source_before之前已经import durability/qualification_contract，:32-39在test discovery/execution前后hash。PROCESS native_exit由unittest结果在进程内生成，不是独立父进程退出观测；不夸大为OS加载全字节证明或防采样间瞬态替换。
- runtime final-002 digest 004aa36b9c2d7c1b92071d3b7ff02656af1cba34c4e8d67b47d3f38adafbd432；source mapping与QUALIFICATION相等，qualification/dependency digest匹配。W/RUNTIME_BINDING_VALIDATION.r5.final-002.json是writer已存loader PASS，本reviewer未执行loader或prepare。binding不是formal结果，更不是这里残余遗漏的豁免。

## 5. 固定状态、范围与交付

绑定产品SHA a29864343ed4f630b052c20d86c23b240f13cfd0、tree fd37409d0274662abbe86f69e3d963c05b379696、patch bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690，与Owner给定身份相等；本分项未执行fresh Git/产品重物化验证。产品3/3、formal1/2保持委派约束；未消费尝试、未创建正式namespace。8000/29仅EXPECTED。这里不认可writer“仅剩formal”的无保留表述，具体剩余项为§2的实际owned资源/复合因果链，须由parent处置后再评估全闭合。

初始/最终source hash包含本轮实际源码/测试/Java/Gradle/JS文件，比较完全相同。EARLY.md、EARLY_FINDINGS.md先持久化；本最终报告及hash只在preformal-review-r5/part-a。读取批次曾因输出截断重新定向读所需完整文件；一个静态AST选错ImportFrom的分析异常已修正，未执行被审代码，未影响最终机械对账。

## 附：独立静态 receipt 对账

```json
{
  "red-predecessor-003": {
    "native_count": 13,
    "unique": 13,
    "statuses": {
      "FAIL": 10,
      "PASS": 1,
      "ERROR": 2
    },
    "native_result_exact": true,
    "process_ids_exact": true,
    "process_statuses_exact": true,
    "log_hash_ok": true,
    "result_hash_ok": true,
    "source_before_after_equal": true,
    "source_bound_count": 72,
    "current_nonprivate_checked": 72,
    "current_source_mismatches": [
      "J/implementation-r5/tooling/qualification/test_conformance_corrections.py",
      "J/implementation-r5/tooling/qualification/test_r4_remaining.py"
    ],
    "native_exit": 1,
    "wrapper_exit": 0,
    "dependency_hash_ok": true
  },
  "green-focused-005": {
    "native_count": 13,
    "unique": 13,
    "statuses": {
      "PASS": 13
    },
    "native_result_exact": true,
    "process_ids_exact": true,
    "process_statuses_exact": true,
    "log_hash_ok": true,
    "result_hash_ok": true,
    "source_before_after_equal": true,
    "source_bound_count": 72,
    "current_nonprivate_checked": 72,
    "current_source_mismatches": [],
    "native_exit": 0,
    "wrapper_exit": 0,
    "dependency_hash_ok": true
  },
  "qualification-003": {
    "native_count": 152,
    "unique": 152,
    "statuses": {
      "PASS": 152
    },
    "native_result_exact": true,
    "process_ids_exact": true,
    "process_statuses_exact": true,
    "log_hash_ok": true,
    "result_hash_ok": true,
    "source_before_after_equal": true,
    "source_bound_count": 111,
    "current_nonprivate_checked": 78,
    "current_source_mismatches": [],
    "native_exit": 0,
    "wrapper_exit": 0,
    "missing": [],
    "unexpected": [],
    "expected": 152,
    "mandatory": 67,
    "mandatory_missing": []
  },
  "qualification_links": {
    "dependencies_match": true,
    "source_maps_match": true,
    "matrix_accounting_equal": true
  },
  "binding": {
    "sha256": "004aa36b9c2d7c1b92071d3b7ff02656af1cba34c4e8d67b47d3f38adafbd432",
    "qualification_digest_match": true,
    "dependency_digest_match": true,
    "source_binding_matches_qualification": true,
    "run_id": "candidate-formal-002",
    "candidate": "a29864343ed4f630b052c20d86c23b240f13cfd0",
    "tree": "fd37409d0274662abbe86f69e3d963c05b379696",
    "product_patch_sha256": "bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690",
    "mandatory_ast_count": 67,
    "mandatory_ast_equals_receipt": true
  },
  "review_source_before_after": {
    "count": 81,
    "unchanged": true
  }
}
```
