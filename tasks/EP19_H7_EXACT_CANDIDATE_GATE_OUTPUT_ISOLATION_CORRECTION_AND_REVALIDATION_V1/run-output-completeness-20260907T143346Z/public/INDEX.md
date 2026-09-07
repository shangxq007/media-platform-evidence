# 审查索引

**结果 B：A/B/C 修正及资格完成；正式门禁因具体保全实现差异和工具限制未启动。**

- [中文最终报告](FINAL_REPORT.md)
- [完整机器状态及逐门禁账本](MACHINE_INDEX.json)
- [唯一 readiness 决定](READINESS.json)
- [最终父资格核验](evidence/PARENT_FINAL_QUALIFICATION_READBACK.json)
- [代码身份及配置 hash](evidence/CORRECTED_EXECUTOR_IDENTITY.json)
- [修正 diff](evidence/EXECUTOR-REVISION-001.diff)
- [实际 namespace](prepared-run/namespaces.json) / [29-key bindings](prepared-run/bindings.json)
- [保全映射](evidence/PRESERVATION_MAPPING_WORKING.md) / [具体工具限制](evidence/TOOL_RESTRICTIONS.json)
- [历史端点 readback correction](evidence/HISTORICAL_FINAL_READBACK_CORRECTION.json)
- [数字账本澄清](evidence/NUMERIC_ACCOUNTING_CORRECTION.json)
- [本机完整证据位置](LOCAL_EVIDENCE_POINTERS.json)

`executor/` 是当前 helper 源码；`pre-correction/owned/` 是修正前 helper；`qualification/` 包含 raw native 日志、正负控制代码及有关小型 fixture。工作映射和 worker 历史报告不覆盖本次 FINAL_REPORT/READINESS 的阻塞结论。

MANIFEST.sha256 覆盖 payload 内全部文件但不包括自身。其真实 digest 及全部最终字段在包目录的 `FINAL_DISPOSITION.json`，最终读回在 `VERIFICATION.json`，二者在 payload 外，避免循环 self-hashing。远端发布及远端验证均未执行。
