# integrated-correction-v2 安全父交接

当前必须停止在 source-copy：不得安装、登记、admission、formal、slot、direct-FF、publication 或 closure。

## 父任务现在可安全执行的只读核验

```bash
cd /REVIEW_ONLY/EP19/continuation-005
sha256sum integrated-correction-v2/candidate/controller/scripts/canonical_publication_control.py integrated-correction-v2/candidate/controller/references/protocol-v1.json integrated-correction-v2/candidate/controller/tests/test_canonical_publication_control.py integrated-correction-v2/ORIGINAL_TARGETS.patch integrated-correction-v2/parent-handoff/INSTALL_AFTER_COORDINATION_AND_REVIEW.py integrated-correction-v2/parent-handoff/INSTALL_MANIFEST.json
python3 -m json.tool integrated-correction-v2/FINAL_MACHINE_REPORT.json >/dev/null
python3 -m json.tool integrated-correction-v2/integration/INTEGRATION_REQUIREMENTS.json >/dev/null
```

随后把 `integrated-correction-v2` 的精确 source/hash/patch 送回**既有**独立技术审查关口；实现者报告不是独立批准，不新增 review program。

## 实际安装阻断

只读搜索确认原 Skill 只有 publication slot/state locks，没有覆盖所有旧/新 controller consumers、三个共享目标及整个 check/replace/recovery 窗口的既有 maintenance/consumer-quiescence interlock。publication slot 不是维护权限；task-local lock 无法阻止旧进程；不得据此自造 maintenance authority。

因此本包的 installer 在 `assess_existing_maintenance_coordination()` 处固定 fail closed。父任务必须先由原 Skill 管理者指出并取得**既有**安全协调机制的精确命令/receipt/排他范围；若该机制不存在，需要管理者在另一个明确授权的维护动作中提供，而不是由本任务绕过权限。该机制确认前没有安全安装命令。

## 机制存在后的必要顺序（不是当前执行授权）

1. 既有独立 review machine verdict 必须批准 exact patch、installer、manifest 和三 target candidate hashes。
2. 在任何 shared write 前，先验证 corrected coherence exact 7/107/15 inputs、original-controller registration interface 及 task-private admission 输出规则；不能使用历史 `ep19_successor_acceptance.py`。
3. 原管理机制取得排他并确认所有 controller consumers quiesced；排他必须持续覆盖三个文件的 expected-before check、replace、readback、任何 recovery 与重新启用。
4. recovery journal 的 target count/order/path/before/after/payload 必须逐项等于 reviewed manifest；未知 bytes/CAS 竞争立即停止。
5. 安装完成且仍在排他窗口内才重新启用 original controller；然后由 original controller 产生 registration same-snapshot readback。
6. real coherence admission 捕获原始 bytes 并重算 private/public comparison；original controller 的 formal-start consumer 再绑定该 `ADMISSION.json` 精确 SHA-256 执行 0→1 consume。

当前这些步骤均未执行，formal 保持历史 `2/2`、新增 `0/1 used`、global ordinal `3`，产品新增 `0`。
