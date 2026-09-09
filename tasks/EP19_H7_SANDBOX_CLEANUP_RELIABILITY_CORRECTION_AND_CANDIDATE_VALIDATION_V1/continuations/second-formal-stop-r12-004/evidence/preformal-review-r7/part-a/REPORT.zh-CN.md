# r7 Part A — AR010 精确 residual 只读 preformal 审查

## 结论

**A6-010-1 RESOLVED；A6-010-3 RESOLVED（r6 指定 discovery/birth permission/unknown 失败范围）；A6-008-2 在本分项审查的 preservation→boundary→adapter→driver 路径 RESOLVED。本分项没有保留上述精确 r6 finding 为 OPEN。**

AR001..006/009 为 RETAINED_RESOLVED，保留原批准范围，不新增 cutoff 后观察义务，不重开 Owner 已接受的 ledger 捕获间 overwrite-restore / truncate-regrow 限制。AR007 与 AR008 全部 serialization/runner supplement/最终绑定的专项结论由 Part B 汇总；本报告不替代该专项，不把本分项通过扩张成整个外部实现无保留接受。

这是 advisory preformal，**不是 final independent acceptance，不是 formal 启动回执**。未执行测试、导入候选模块、probe、preparation、baseline、formal；未读取共享 ledger/usage、私有清单正文或凭据，未扫描/发信号给任何进程。全文读取 OWNER_AUTHORIZATION.verbatim.txt、REPAIR_R7_PACKET.md、r6 Part A 报告、writer r7 最终报告/矩阵/对账。仅本 part-a 两份报告为输出。

以下 E=implementation-r7/tooling/executor；Q=implementation-r7/tooling/qualification；W=writer-evidence-r7，均相对 J。

## 1. A6-010-1 — 已获得 fd 的无条件释放：RESOLVED

- 实际入口 E/bookkeeping_v3.py:219-256 仍用 capture_file 获取 usage/lock/ledger，manifest 亦调用该函数（E/capture.py:269-271）。不是只修测试 helper。
- E/capture.py:141-152 在 try 内取得 fd；:153-184 的 fstat、hook、分块读取、join、hash 和候选组装均在同一个拥有资源区域。:185 捕获 BaseException；:194-198 **真正 finally** 无论成功、CaptureError、KeyboardInterrupt、MemoryError 均独立尝试 os.close。
- :199-202 在 close 失败时组合主/次异常；无 close 失败时非 retryable 原异常重抛。取消不转换为成功或重试。OSError/CaptureError 的原 retry/terminal 分类 :187-193 保持。
- E/capture.py:32-36 → E/causal.py:87-108：单 primary 原类型重抛；复合用 BaseExceptionGroup，保留 primary/cleanup leaf 的 error_type、reason、stage、association。不要求对不确定 close 盲目重复关闭，不能声称 OS close 自身失败仍保证释放。
- 真实保存反例：W/red-predecessor-001/NATIVE.log:26-42、53-69 分别显示两个 control acquired=[4]、closed=[]。W/green-final-001/NATIVE.log:5、7 保存相同控制 PASS。
- Q/test_r7_remaining.py:71-119 在真实 os.open 返回之后用 opened hook 分别抛 KeyboardInterrupt/MemoryError；close_then_fail :84-87 先真实 close 再抛次生 OSError；:102-107 在 fixture finally 之前断言 open/close 集合相同、两个原因保留、fstat 已失效。因此此 GREEN 证明真实释放，不是只记录 close mock 被调用。测试没有模拟机器真实耗尽内存，也没有证明任意异步双重中断均可恢复；不作该扩大声称。

## 2. A6-010-3 — known identities 的错误隔离与剩余状态：RESOLVED

- E/native_observe.py:251、264-275 保存 prior 排除与 known PID/birth。异常 helper 不是按名称匹配或全机 kill。
- :287-294 discover() 将 PermissionError/OSError/RuntimeError 枚举故障记录后返回；关键不是返回 [] 本身，而 :295-297 **始终将 pending 与 scope.known 并集逐项处理**。故一次 pending 内 birth 失败不能丢掉此前已保留的其他身份。
- :298-314 每个 PID 独立读取 retained birth、独立捕获 birth permission/unknown；无法核验或重用者只记 uncertainty/unresolved 并 continue，绝不进入 :321-329 signal。另一 known PID 仍得到核验和清理尝试。
- :331-344 在期限内迭代，最后重新 discover+inspect(send_signal=False)，不是沿用失败前 pending。remaining 与 errors 分开；有 errors 即使 remaining 空也不会 QUIESCENT。PID_REUSED 在 inspect 分支保留专门 kind。
- 实际 run 的异常 finally :433-441 不受主进程是否仍存活限制，调用 helper 并更新 terminated/pending；:467-468 将 remaining 和完整 descendant_cleanup 放入 native receipt；ChildScope 和 Watch :442-447 分别关闭。
- Q/test_r7_remaining.py:121-168 为真实 ChildScope、一个 prior child、两个新 owned children；先通过 :131-136 建立 known，然后只对一个 birth 注入 PermissionError。:152-157 在 fixture finally 前要求另一 PID 已被生产 helper signal、prior child 未被 signal、uncertain PID 保留 remaining、result NOT_QUIESCENT。
- W/red-predecessor-001/NATIVE.log:45-50 原生失败 receipt 为 controlled PID 未进入 terminated 且 remaining 错误为空；W/green-final-001/NATIVE.log:6 保存同体 PASS。GREEN 日志没有另存成功 receipt 的完整 PID/birth 值，因此本报告不虚构成功 native receipt 细节。该新 control 不独立断言 os.kill(uncertain_pid) 未发生、受控 child 已被 reap；这些分别由生产 :298-314 的跳转与原有 cleanup regressions 补充，不将本 control 扩称所有 OS 故障组合已运行。
- 精确范围说明：这解决 r6 指定的 discovery/birth PermissionError/OSError/RuntimeError 短路问题；不是宣称任意 BaseException 或 waitpid 的任意非常规故障都已做全矩阵资格。继承的正常路径 :379-387 仍有 tagged_processes；不把本次安全身份 helper 的结论套到所有历史 tag 路径，不新增清理无关进程要求。

## 3. A6-008-2 — 本分项涉及的嵌套因果保存：RESOLVED

E/preservation.py:19-22 使用统一 composer，不再对单 primary 无条件新建 group；parent_fd :46-53 独立逐 fd 关闭。Collector.error :65-68 保存 causal.record；capture_files :136-143 将捕获记录的 leaf 装到抛出异常，而不是只用 group 摘要。E/causal.py:25-39 递归读 group/继承已有 causal rows，:87-108 保存组合关系。

E/boundary.py:149-155 保存 capture/evaluation rows，:217-238 将它们与 persistence leaves 放进结果及 attached exception；E/executor_adapter.py:45-63 收 receipt/marker leaves，:116-121 传递 boundary receipt；E/external29_driver.py:249-293 合并 attached/current/marker，不以 attached receipt early-return 丢 marker。:364-370 保持失败停止。KeyboardInterrupt 不能在这些 Exception-only 中间捕获层被转换为成功；实际 formal 外层 :425-465 以 BaseException 接住、失败落盘和资源关闭后保持取消。

Q/r7:170-215 经真实 preservation.capture_files→真实 Engine/RunAdapter→execute_actual_graph，并读回 BOOKKEEPING_FAILURE.json 中 decision.causal_errors 与最终 results。其 capture_bundle、strict check、Runner 是限定 seam；不是产品 gate 执行，也不是字面依次执行 capture.capture_file 再 preservation.read（两个独立获取实现）。:200-203 的全局 os.fstat 故障会在 ancestor 获取阶段触发，故本 control 的 GREEN 主要证实 parent_fd/Collector.error 的真实嵌套与保存，不冒称 target read 所有阶段被注入。

W/red-predecessor-001/NATIVE.log:18-23 的保存 marker 明确无原始 leaf；GREEN :3-4 的同控制 PASS 支持源码修复。本分项不重新签署 runner supplement 全矩阵；由 Part B 处理其广义 AR008 声明。

## 4. 保留规则及未扩大范围

| 规则 | 处置与当前源码 |
|---|---|
| AR001 | RETAINED_RESOLVED。driver:69-123 最终 callback、共同 cutoff、stop/drain；:401-412 baseline/preflight/prestart/graph/FINAL/COVERAGE/SEAL；observe r6→r7 仅 import/composed constructor exception delta，正常 watch/temp/drain 不变。 |
| AR002 | RETAINED_RESOLVED。observe:85-101 双向非零 cookie；:248-275 可见 temp type/nlink/dev/uid/gid/mode 与 pending 上限。bookkeeping_v2 delta 只加 causal serialization，不改语义；v3 字节未改。 |
| AR003 | RETAINED_RESOLVED。boundary:108-142 实际 wall/monotonic、previous accepted lower、回退拒绝。 |
| AR004 | RETAINED_RESOLVED。v3:106-123 原始 BOM/CR/partial/empty framing；整个 v3 与 r6 字节一致，UTF-8/keys/constants规则未改。 |
| AR005 | RETAINED_RESOLVED。boundary:226-244 证据成功后才推进 session/previous_usage/两时钟。 |
| AR006 | RETAINED_RESOLVED。formal:373-406 真实 runtime/policy/observer/binding 路径；未新增 summary 注入口。adapter:79-106 consume/no resurrection，:124-135 先 failed latch 后持久化。 |
| AR009 | RETAINED_RESOLVED（本分项源码旁证）。durability:20-25 独立 BaseException attempt；:40-59 嵌套目录发布同步；:119-140 fdopen closefd=False、body/flush/fsync/stream-close/raw-close/parent-fsync 独立组合。artifacts 与 r6 字节相等。完整专项仍由 Part B 汇总。 |
| AR010 既有获取限额 | RETAINED_RESOLVED。capture:39-73 controlled syscall guard、:159-168 分块容量检查；v3:219-256 同边界 deadline/三次总重试，各文件 attempts=1；observe:272-275/native:94-139 实际 event drain 内拒绝。未新增 3600 秒 attempt 限额。 |

bindings/execution/matrix/packaging/compile_inventory/lean_materialization/isolation 与 r6 字节相同；保留 native29 命令/原生超时、COMPILE freshness/completeness、跨 run 输出隔离、不可变 BOOTJAR、frontend/assets/static→resources→JAR、Lean、wrapper/init 的先前批准范围。不是 fresh 产品重验证。

Owner:110-113 接受的 ledger 捕获间 overwrite-restore/truncate-regrow 限制继续成立，只适用于该 ledger，不扩到其他 protected 对象；boundary:221-223 仍明确该限制。

## 5. 保存证据静态对账与限制

程序从保存原生日志解析身份/状态，与 RESULT 投影逐项比较；没有运行这些 controls。
- 主组 RED：5 unique / 5 FAIL；GREEN：5 unique / 5 PASS；日志、RESULT、PROCESS 摘要一致，native=1→0，wrapper字段均0（不把 wrapper=0 当 RED 成功）。
- RED snapshot executor 59 个文件与 implementation-r6/executor 字节完全相同；同组被选 test body RED/GREEN/integrated/current SHA256 全相同：eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a。
- focused RED 75、GREEN 76 项非private源码 before/after snapshot 均逐字节 hash 符合。GREEN focused 到最终当前有 binding_contract.py、qualification_contract.py、run_integrated_parent.py 三项后续变化，不把 focused 结果假装最终全部源码执行。capture/native/preservation 等本分项实现与 focused GREEN 对应源码仍相同。
- qualification-003 原生日志独立解析为 167 unique /167 PASS，expected 集合相同，82 个 receipt mandatory 全在实际集合；没有 missing/unexpected/duplicate/非PASS。其81项 executor/qualification/tools before/after snapshot 均与最终当前字节一致。没有读取 candidate-inputs/private 正文，不将此计数冒称116个完整依赖身份均独立复核。
- 内部 PROCESS 与父 PARENT_PROCESS 的 log/result hash 均复算通过。writer-owned 父回执 PID 是 namespace-local，不是本 reviewer 的独立 OS launch attestation。historic r6 RED exact producer 保持 NOT_ESTABLISHED，不回填。
- 产品固定 SHA/tree/patch 仅采用 Owner 与 writer 已绑定身份，不冒称 fresh Git重物化。产品预算3/3、正式1/2，本分项未消费；8000/29仅EXPECTED，正式工程结论仍未运行。

## 6. 只读证明与输出

审查前后对 executor/qualification/tools 共81个非 __pycache__ 文件计算 SHA256，集合及每项 hash 全等，变动0。before 完整清单已早期写入 EARLY_REPORT.zh-CN.md；after 完整清单和程序对账附下。只创建 EARLY_REPORT.zh-CN.md 与 REPORT.zh-CN.md，不修改候选、历史、共享状态或 Skill。

工具读取曾遇输出截断及 read_file 去重导致一次 KeyError；后续按范围/结构化摘要补读，不构成候选缺陷。未执行 fresh RED/GREEN 或进行修复。

## 附：独立静态对账
```json
{
  "red-predecessor-001_before": {
    "count": 75,
    "mismatch": []
  },
  "red-predecessor-001_after": {
    "count": 75,
    "mismatch": []
  },
  "red-predecessor-001": {
    "native_status_counts": {
      "FAIL": 5
    },
    "unique": 5,
    "log_result_equal": true,
    "source_stable": true,
    "current_different": [
      "executor/binding_contract.py",
      "executor/bookkeeping_v2.py",
      "executor/boundary.py",
      "executor/capture.py",
      "executor/decision_evidence.py",
      "executor/dependency_contract.py",
      "executor/durability.py",
      "executor/executor_adapter.py",
      "executor/external29_driver.py",
      "executor/native_observe.py",
      "executor/observe.py",
      "executor/parsers.py",
      "executor/preservation.py",
      "executor/qualification_contract.py",
      "executor/runner.py",
      "executor/vite_closure.py",
      "qualification/build_dependency_evidence.py",
      "qualification/run_integrated_parent.py",
      "qualification/run_source_bound_group.py"
    ],
    "log_hash_ok": true,
    "result_hash_ok": true,
    "native_exit": 1,
    "wrapper_exit": 0
  },
  "green-final-001_before": {
    "count": 76,
    "mismatch": []
  },
  "green-final-001_after": {
    "count": 76,
    "mismatch": []
  },
  "green-final-001": {
    "native_status_counts": {
      "PASS": 5
    },
    "unique": 5,
    "log_result_equal": true,
    "source_stable": true,
    "current_different": [
      "executor/binding_contract.py",
      "executor/qualification_contract.py",
      "qualification/run_integrated_parent.py"
    ],
    "log_hash_ok": true,
    "result_hash_ok": true,
    "native_exit": 0,
    "wrapper_exit": 0
  },
  "qualification-003_before": {
    "count": 81,
    "mismatch": []
  },
  "qualification-003_after": {
    "count": 81,
    "mismatch": []
  },
  "qualification-003": {
    "native_status_counts": {
      "PASS": 167
    },
    "unique": 167,
    "log_result_equal": true,
    "source_stable": true,
    "current_different": [],
    "expected_equal": true,
    "mandatory_in_actual": true,
    "mandatory_count": 82
  },
  "selected_test_hashes": {
    "red-predecessor-001": "eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a",
    "green-final-001": "eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a",
    "qualification-003": "eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a"
  },
  "selected_test_current": "eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a",
  "red_executor_vs_r6": {
    "files": 59,
    "mismatches": []
  },
  "retained_byte_equal": {
    "bookkeeping_v3.py": true,
    "bindings.py": true,
    "execution.py": true,
    "matrix.py": true,
    "packaging.py": true,
    "compile_inventory.py": true,
    "lean_materialization.py": true,
    "isolation.py": true,
    "artifacts.py": true
  },
  "integrated_receipt_hashes": {
    "parent_log": true,
    "parent_result": true,
    "inner_log": true,
    "inner_result": true,
    "native_exit": 0,
    "wrapper_exit": 0
  },
  "read_only_hash_check": {
    "before_count": 81,
    "after_count": 81,
    "equal": true,
    "changed": []
  }
}
```

## 附：after SHA256
```json
{
  "executor/ExposureProbe.java": "327ef74f80c6993808526b22bb379fbfdd6fb063f7a6307b52ce33639074d35d",
  "executor/VERSION.json": "53b14685fab83f2c0e5464af9ae47517101850075560c380e5b02fe66fc3a770",
  "executor/account.py": "0ec7573b3291218da34c0be289ecb46aef0f5c6e1932d80afc0a17db10da8259",
  "executor/artifacts.py": "7ccb717436a918612ba2b49fe342d0a3ef5e2723bf29082ca03ca53db493778b",
  "executor/baseline_evidence.py": "2902e7b176fba343e4f59b11cb86355629a858a07a518be8dfe19027c0e17f23",
  "executor/binding_contract.py": "4220e5f4512dc0a7cf8635a28aa0c61152248df9740d4b9e74fb1fc0855eeeff",
  "executor/binding_qualification.py": "582d67a8fe4eac0e037372c02fe7e7ec97ce10e4b448590d4c20ff2fa22b7a22",
  "executor/bindings.py": "c32950cd6f410129d6bdfe88f066b707b98b24587564bb6240b410f4cbe63c69",
  "executor/bookkeeping_v2.py": "64c72c4203a198e4123a5812863327d5ea8270995314387069498d445b7b764e",
  "executor/bookkeeping_v3.py": "3675ee06e82c7da45713fb703c2c1aed0edfab6dfb1b216e559f27faf74acebe",
  "executor/boundary.py": "5369c80b094d91a881b4d3dfb3f6d71888a9f99325673a51815fe78e4d899f93",
  "executor/capture.py": "06ebd6ddfe2a9b08ea042fbe83c02087b18ac60428727cd48e4e8a6016bcb8df",
  "executor/classpath.init.gradle": "ba4814f13edfa67393d62309a547e8cb434e66514cdc993aef81af50dd191f57",
  "executor/collect_frontend.mjs": "692c12e38d864d6110192cf9e9a61f5e91000e1de1ef71f857d4a73d174e3c11",
  "executor/compile.init.gradle": "c3efe1970c854a6087268f7368594a45ab956e2ea0c0a35a981a5e7aba1e564a",
  "executor/compile_inventory.py": "1b1fe1ab47e64226171d47f069bec9232b8d604c63f0a70e3882c9f2f6cdf91a",
  "executor/coverage.py": "36c8f947a2eda290ec78e0ce3be067ef35c754dc37a2d951f4bcfdb9b2438ddf",
  "executor/decision_evidence.py": "06f350be602a6e079b4afe929b513345d85377359fe695391b53e0183a3f3c9f",
  "executor/dependency_contract.py": "d67d5e967fb6c44a40cdac3ee9f2cb8876d63256eeea1c687bb59754e3a224ba",
  "executor/durability.py": "308805ff2685196c5660d349e9791050ba11e7abede806ee45313b8c476b103d",
  "executor/engineering.py": "e895d246660dc6ddceb21c86dd703d41275f33a268f4eb536f9e9b0adc48c990",
  "executor/execution.py": "84bbb927b15072796eb5ca835cf137921055a895c2fd2d265b2a623e1081fccf",
  "executor/executor_adapter.py": "8aff905714e06b527a8533c5568f8f9659c2d1e3780a73e26f49f1f818f7935c",
  "executor/external29_driver.py": "ed9afb6289ac6d17201d9819b9e089b73ff3ff951a1ea8b56230abd44ccd0ba4",
  "executor/freshness.py": "8f2ed88aa7a781c27efaa53ec80c314d32129cd39e6f937107297d50bd4669b6",
  "executor/frozen_shadow_monitor.py": "bb63de244007818956aa151ecceae98bf8c4fa50c45f2f7ee09bc74d63d21d0b",
  "executor/identity_delta.py": "e724dc6a6aa5ab9b3e498a5668276375e8aa13e2fccba0c5c73dd0975219a440",
  "executor/isolation.py": "4c0277d71479bb65cfd453a68799c53f7ed22e6b31cb72fce256859a7b9a4dc5",
  "executor/lean_materialization.py": "b082fff3453e1cf0cdd4d17f300c2aa54f8fc02339822766db73b8277e9fc297",
  "executor/lean_preparation.py": "c3862c3206c02f6c2f51a4c410b1957b8e9e760894949b8deb56efdaae0098e4",
  "executor/matrix.py": "76c0c5aec3cf9a4b850f792814fcf3053e34396e1a71c4d4e79f7fe73a6815ab",
  "executor/namespaces.py": "5610d6e27fad0343f26d2133eaaddb6bd59674f0d31ccc3657ffcd6c4da8d9f3",
  "executor/native_observe.py": "6b8f308f3ef0d4a735344a07801c2550a6acc591f24b72f359123a20c8d49d70",
  "executor/observe.py": "b36502c0fd2e140a882cde740683fd8af5043808d5ed7f4bf2cce7b9038c97de",
  "executor/packaging.init.gradle": "fd3c8ce83acd27274b616ee32de17352ba2b533bc9dbce875fb93f3a6921a6e4",
  "executor/packaging.py": "e7eb80c587d11e4c33ac8d1eb5485aa975e8fcc5a7beb1dde6d654dfd47ec299",
  "executor/parser_tools.py": "ae883f34dd75034fb4dbbde1aa7bc547f1bd0281308ef3dada0130a90e72c515",
  "executor/parsers.py": "92dd841bc5d57ca33b51dfa9be088812130641c91cc00e3f144fae56ad10aac3",
  "executor/preflight.py": "536211ae18cda30a9cc2290689f4923eac7502005b629ea1dfe77a284fd5b914",
  "executor/prepare.py": "f199697ad274077537840b6a7b08402fd06ecfa193b89e47323fad9ff8ed9e0d",
  "executor/prepare_finalize.py": "dc68828ad5b42f6ec9d5b02403952d68207ce6f272138de4aa8f8cc62f7ef90d",
  "executor/preservation.py": "e4de7957968afb10ba26bf59253ea897b32cdb457150108d06ffae63386b420f",
  "executor/qualification_contract.py": "68f78563f27a190661318e61d1d4b852768caf7e77fe5593d1ef142679ad79f5",
  "executor/qualify_frontend.py": "013af0fd6a54ac97c8b3c7fab44d6fbeb1e14f1a4cffdb8e49df0c27987111d4",
  "executor/runner.py": "89531e4ee485cf8daf41442af87ff4a6b62bec72cf7da6428ebb0909c4640135",
  "executor/sequence.py": "ab85a2a6e26b02d9f11166660dbe0d0757864f70c0de35171aaab60b4449df5e",
  "executor/shadow_binding.py": "eaf4933c7785dc421149681a09f62e4809a5c985da8d5d9cf81a878c493cf71e",
  "executor/test_account.py": "e0367c95ef5d37ef997a5a33be7e58e4fe2828d6b9af35c4597a822e4a5adf97",
  "executor/test_bookkeeping_v2.py": "d71ec5eede3d93dfa8d071bfc5fe9df3f86c429e382c1ac626406c56d4026dba",
  "executor/test_continuation.py": "630401bb64ba2251b1a273b3dc8d64607ea4f61cfc252376aeba87631ed5c4ef",
  "executor/test_contract.py": "3fc1b622f5a1f6c18b38bd1f3d908bc956cfd9cace746fbfed5b0c27b94efa4a",
  "executor/test_isolation.py": "43065b9e8bd2893535909d58f7e1008e67137e55642ccd8d2f43c130ad61857d",
  "executor/test_lean_binding.py": "947c2951de922d964311bbf81da5eb6dd2ca745f206303a00a86b395aef70f40",
  "executor/test_lean_materialization.py": "8ca17c5ff613528c4843c47d4330a39908af743fb842c26c98c32a3dc10f4d0c",
  "executor/test_owner_preparation.py": "8bd6d3343101564bde44ebd06fece088d6b494d87ee5ebf79717ec004b2d93f6",
  "executor/test_v2_integration.py": "dacc18f0d099a55b2dc6fb9555aabfc19703cd1b42cfb897af4e5281b830cd36",
  "executor/vite_closure.mjs": "c384d54525bfa558a0d488d2c76562f926e8ec7c1e61a4434cecf1d153d379b8",
  "executor/vite_closure.py": "365b0f070200a9e87f7c6bd2dcc6afdc9da5b695561237fe6cf761cfde7f0e3a",
  "executor/vite_resolution.mjs": "989ad04b5eef1f96e608adbbba25559ea05ad2b88fe1dc56015f7f5a8095a74c",
  "executor/causal.py": "1b89baafa1e11fa4251e4cfb7432b8fe6b42584f4bbd1052a07dba75acb60e4f",
  "qualification/build_dependency_evidence.py": "ec4c6fa54467904c634ac340d54ad86ec60a8d497d7129d8a6efb6f289045ff3",
  "qualification/build_integration_qualification.py": "c003fd7e46e44eb4dc1f254913b222e1a5120d803f47496508b9fd5c7d7961a1",
  "qualification/build_runtime_binding.py": "d687fa392234107a3479ab9d1964b6c4853d61025683203a99d2433af492b319",
  "qualification/candidate_binding.py": "620fc5ecf5608561468a97cc2963007cc153067442d9c9c4b185496a47464847",
  "qualification/policy_builder.py": "d1c52c68625b26eff6084cdaaade7476fcc37fa3bb8f2ec42b9ccd0e7f4cad8f",
  "qualification/run_group.py": "ead2a0000b4acfb26881a7ceb74d289d548f378f17012ecb81f3ebc8384ef3d4",
  "qualification/run_integrated_parent.py": "19481df993a20996243931ff91bc2fab30e6724f4cde0a0d96a70f3769aa499d",
  "qualification/run_source_bound_group.py": "7f7f9cebae2f3938189b5043fa3a8c9938cc22094d4ec3cecc566046f04033e8",
  "qualification/test_approved_contract.py": "6b96436eb4da521b9dd564cb18c194bbd8ad865900dac74a1db374624d2fa54e",
  "qualification/test_conformance_corrections.py": "1ccb7c99c37a828778050129171370d60f64c756082fae43f955ee3f207d695d",
  "qualification/test_external29_integration.py": "07f43f94c0b03f2f04931bda226ac7171df8cc0c7cc3faff65a91801e300e1f6",
  "qualification/test_r3_remaining.py": "5871417ad3e438f0c0c6d8c0ca352f6d900db5e16d3116c92d5f2d463d474938",
  "qualification/test_r4_remaining.py": "e4fa16c011a1e0bd8d8d68616c0dd15fa3682df83e210d342b52b6e52b8b02d5",
  "qualification/test_r5_remaining.py": "b76bb2b0abce5cb788cbd3c2e92f47e35556f14274fead6f8268938170d00e16",
  "qualification/test_r6_remaining.py": "52b8f8a633d5529c8770c03ffaa083b5cd704051db4f43c6a27207a933427591",
  "qualification/test_r7_remaining.py": "eabddeb989727178a57b503be4acf4ce443fa6b96922f14727bc1ef204fcdd3a",
  "qualification/test_r7_runner_supplement.py": "9944dd46ee94ed6fe7094732b4aa220539117057b1d74b5fc9d054cb474ce858",
  "tools/hermes_execute_once.py": "fcc52a8b1fb3d17e391faa69dd13fd7ddf86d7b2f0e1b1714809b953c5c4f0bd",
  "tools/prepare_boundary.py": "c9cee33034e783c17aa0dc4a7f23dc3112a832285cda90aa01c65a11539c7cd1",
  "tools/revalidate_preparation.py": "abed96f338352ab7b891c57f7ae1a153294ac3c06edc55aecae9b197ce9ee881",
  "tools/run_logged.py": "09698cab32edd64e6a03fbf80b8a7d67eee26101d5c795bcad9cf7d693e0ec0d"
}
```
