# r8 Part A：实际 REJECT+marker 与 preflight→formal 失败传递只读预审

## 结论

**B7-008-1 精确修正获支持；B7-008-3 部分修正，但 preflight 回执自身写失败的实际传递仍 OPEN。因此不支持本分项 AR008 无保留 CLOSED。**

本报告为 advisory preformal，不是 independent final acceptance、正式启动许可或产品门禁结果。B7-008-2 交由对应分项评审，不替其签结论。AR001..007/009/010 保留此前已解决处置；没有重开已接受 ledger 捕获间观察限制，没有新增契约、3600 秒 attempt 限额或产品门禁。

路径相对 J；E=implementation-r8/tooling/executor，Q=implementation-r8/tooling/qualification，W=writer-evidence-r8。

## 已读范围和执行限制

读取 Owner authorization 全文、REPAIR_R8_PACKET.md、r7 part-b 完整报告、r8 final report/matrix/reconciliation/runtime binding；静态阅读实际 adapter/driver/boundary/causal 与测试源码、保存 native/result/process/source snapshots。仅本 part-a 写入报告和 SHA-256。没有导入被审模块、执行测试/探针/preparation/baseline/formal，没有产品修改，没有私有/共享 ledger、usage、credential 原文读取，也未沿 runtime binding 私有目标打开材料。

82 个 scoped executor/qualification/tools 非 pycache 文件在审查前后 SHA-256 完全一致；前后 manifest 和独立静态核对结果均已保存。历史失败文件未修改。固定候选与预算按 Owner/保存绑定保留，未重新运行 Git 或 loader：产品修复 3/3、正式尝试 1/2；本次未消费正式预算。正式 baseline/preflight/gates NOT_RUN，8000/29 仍仅 EXPECTED。

## B7-008-1：支持精确关闭

r7 part-b:13-17 的具体问题是正常返回 REJECT 后，adapter 先 fail，再附原 decision；marker 错误抢先逸出，driver 又因 failed=True 跳过 relatch。

r8 实际路径：

1. E/executor_adapter.py:113-124 调真实 Engine.check；其返回非 PASS 时先构造 BoundaryReject、附 boundary_decision_receipt 和 causal_errors。
2. :125-142 才执行 fail。marker 失败经 _attach_marker_failure(:56-68) 和 raise_composed，保留原 rejection 为 primary；combined 同时附原 result 与 marker rows。:146-157 继续在持久化前不可逆 failed=True。
3. E/external29_driver.py:373-374 →真实 boundary 包装(:114-123)→上述 adapter；:387-390 即使已 latch 也 merge。:253-280 从附着 receipt 复制原 decision/reasons，并合入 causal_errors 和 secondary_failures；:281-283 明示 persistence uncertainty。失败后 :393 停止，正式 :430-440 不会进入成功 FINAL/COVERAGE/SEAL，:441-487 把 gate result 带入 runtime/RESULTS.json 的既有序列化路径。
4. E/boundary.py:225-245 非 PASS 不提交 next_session/previous_usage；本次未改变该已接受顺序。

保存真实反例 Q/test_r8_transport.py:56-101：Observer 返回 coverage error，真实 driver.boundary、RunAdapter.boundary、Engine.check 均未被 mock；只将外围 strict_check 置空，且对实际 failure marker fd 的 os.write 注入故障。Runner.run_gate 若触发即失败。:88-99 通过 durable 写出并读取 driver 最终 gate failure，明确断言 REJECT、原 R8_FORCED_ACTUAL_BOUNDARY_REJECT、marker 原因、uncertainty；:95 断言仅一次 boundary；:100-101 断言后续 final 被 NamespaceConsumed 拒绝。

W/red-predecessor-002/NATIVE.log 的该 control 在 Q:96 精确 KeyError('decision')，不是 setup 错误；W/green-final-001 同体 PASS。故其支持“原 boundary decision + marker secondary 到最终 gate result”这条精确闭合，而不是仅 helper flatten 通过。

证据限度：Q:29-33 的 TemporaryDirectory 在 cleanup 时删除。现在保存的是测试源码、原生日志、process/result 与 source copies，并非永久保留的 DRIVER_FINAL_FAILURE.fixture.json。GREEN 证明真实调用及 saved-read 断言曾成功，不能冒称本 reviewer 读取了一份仍存在的最终 fixture 文档，更不能称运行过正式 RESULTS。

## B7-008-3：仅写成功分支修复，实际写失败分支仍 OPEN

### 精确已修复部分

E/external29_driver.py:327-334 保存 original 并计算 causal.receipt_rows；当 :335 的 preflight.json 写成功时，:337-340 抛 EngineeringPreflightBlocked，携带 preflight_receipt 和 causal_errors。formal :425 的必经调用失败进入 :448-458，使用 :350-362 的同一个 formal_failure_document；其包含全部 causal rows 和 preflight disposition。因此 r7 的无条件 str→裸 RuntimeError 退化在这个分支已修正。

Q/test_r8_transport.py:158-222 实际调用 engineering_preflight 和 latching_strict_check(:163-169)。只在 strict_capture producer 注入一个有 native primary 与 evidence secondary 的 structured exception；真实 adapter latch、preflight 持久化与读取被执行，formal helper 的内存结果同时保留两叶，未生成 START，后续 final 被拒绝。这是 bounded fixture 验证，不是 shared preparation/formal。

### 残余 B8-008-3-PREFLIGHT_RECEIPT_WRITE_TRANSPORT

**OPEN，静态可达，不冒称 fresh RED。**

实际先发生一次 structured capture/cleanup 或 boundary 拒绝，:327 将异常保存在局部 original；:329-334 已形成带完整原因的 result。随后 :335 `runner.put(run/'preflight.json',result)` 是无保护的可失败调用，位于创建/附着 EngineeringPreflightBlocked(:337-340)之前。

真实 runner.put 在 E/runner.py:27 → E/coverage.py:11-13 → durability.exclusive_bytes。这个既有真实证据写点发生 OSError/write/fsync/close 失败时，:337-340 永远不执行；逸出的只是 preflight 回执写异常（或该写内部的组合），original/result 不附在它上面。由于原 except 块已经结束，不能依赖 Python 自动 exception context 关联这个保存在局部变量中的旧异常。

formal :448-452 接收到的是新写异常，formal_failure_document :358-361 只能读取该异常的 causal rows/附着 preflight_receipt。E/causal.py:87-149 读取显式 rows、group children 和 receipt 属性，不读取调用栈局部 original；因此最终 FORMAL_FAILURE 缺原 capture/cleanup/marker 叶子及 preflight disposition。即使原 BOOKKEEPING_FAILURE 已经成功保存，formal 也没有读取并绑定它的补救路径；:454-456 检查 failure_path 已存在时不会再写原 marker。

这是已批准 AR008/009 的“原失败与证据写次级失败均须保留”在有限实际序列化点的剩余问题，不是对未来插件的假想要求。adapter 先前 latch 仍有效，正式执行停止，**不是成功绕过**；缺陷是最终失败事实被新证据错误替换。

Q:190-196 名为 evidence-write-secondary 的叶子是 strict_capture producer 通过 causal.raise_composed 主动构造，并不是 :335 preflight.json 写点的故障；Q:182 的 put 使用正常 durable。因此当前 GREEN 未覆盖此 compound branch。限定修正应在这个可失败持久化之前附原 preflight receipt，捕获该写失败并关联为 secondary，再让同一 formal serializer 保留完整事实；不要修改产品或已批准契约。

### RED 与最终落盘证明的限制

该控制的 authoritative RED 在 Q:210 因旧版没有 formal_failure_document helper 而 FAIL，尚未执行两叶断言。这是实现接口缺失的 RED，不是同一最终失败文档“原叶子缺失”的直接 RED。GREEN Q:211 仅调用 helper 返回内存 final；Q:212 真正读取的是 preflight.json，未将 final 通过正式失败文档写点保存再回读。静态 formal wiring 能支持写成功分支，但不能升级成已经保存完整最终 FORMAL_FAILURE 的真实反例覆盖。建议 parent 在既有授权修正中补精确同体前后结果，而本 reviewer 不执行测试或准备。

## 保存证据的独立静态核对

详见 STATIC_CHECKS.json。按实际字段解析 native→RESULT.controls→PROCESS（不是照抄 writer 总数）：

| 保存运行 | 原生结果 | native/wrapper | 每侧 source copies |
|---|---|---|---|
| red-predecessor-002 | 1 FAIL + 2 ERROR，3 unique | 1/0 | 78 |
| green-final-001 | 3 PASS，3 unique | 0/0 | 78 |
| qualification-003/integrated | 170 PASS，170 unique | 0/0 | parent 117 |
| runtime-loader-002 | 保存 VALIDATION PASS | 0/0 | 119 |

native/result/process 对应 hash、status projection 全相符；上述副本逐文件 hash=snapshot_sha256=source_sha256，before/after source hashes 一致。集成 RESULT 的 expected 170 / mandatory 85 与保存身份对账零差异保持，未由本分项重新推导全 AR007 import/mandatory authority 图。loader 的 119 副本含 117 tooling 与 validator/binding；r8 final report:5 的“118 当前实现文件”不应作为计数依据，:16 的 117 bound tooling 才与 binding/VALIDATION 实际相符（报告计数瑕疵，不列新工程门禁）。

同体测试 SHA-256：`e447308b4ed7498102e1731e8235b3001666bbc342275b62d9915e0b95a321a9`。

runtime binding SHA-256：`5728eafccf0f13665c963cdaf9c3773a7fe76450f5251c2047b33514881d4b20`。exact run_id=candidate-formal-002，117 source entries；全部本审查 82 scoped 当前源码与 binding 匹配；qualification/dependency 文件 hash 与 binding 相符，VALIDATION hash 与 PROCESS 相符。未运行 loader、未读取其私有输入。namespace PID 与 writer-owned subprocess receipt 不是 reviewer 独立 OS attestation；历史 NOT_ESTABLISHED_NO_BACKFILL 不回填。

## 最终处置与剩余动作

- B7-008-1：SUPPORTED_CLOSED_EXACT_SCOPE。
- B7-008-3：PARTIALLY_FIXED_OPEN_PREFLIGHT_RECEIPT_WRITE_TRANSPORT。
- B7-008-2：本分项不签结论，合并对应评审。
- AR001..007/009/010：RETAINED_PRIOR_DISPOSITION，未重开；不把其已有 PASS 抹掉，也不把 170 PASS 当作未覆盖分支闭合。
- parent 合并评审时应保留上述 OPEN，在已授权外部修正内解决 preflight 回执写失败和真实 final saved-read 证据，不据本分项启动正式执行。

初次批量读取输出曾截断，已通过限定文件/行补读；静态校验首次字段投影不匹配（controls vs control_statuses、log_sha256 命名差异），后按真实 schema 更正，最终校验结果已保存。没有执行被审代码或修改实现。
