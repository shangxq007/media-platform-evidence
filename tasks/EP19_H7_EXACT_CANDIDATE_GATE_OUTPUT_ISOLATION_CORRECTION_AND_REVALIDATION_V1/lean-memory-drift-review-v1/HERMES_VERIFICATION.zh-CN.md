# Hermes 本地交付复验

## 决定
本地 preparation correction、一次 fresh formal continuation 以及中文报告/机器字段/public ZIP 已产出。工程接受状态为 BLOCKED，不是产品通过；EP19 未关闭，独立接受审查仍 PENDING。未发布 Git。

## Hermes 实际验证
- 报告层测试：6/6 PASS，真实 unittest 运行耗时 10.393 秒。
- public MANIFEST：58 个 payload 文件全部 SHA-256 一致；manifest 成员与目录实际 payload 精确一致，无遗漏或额外成员。
- ZIP：60 个成员（58 payload、manifest、detached fields）；CRC 检验无错误，压缩包内全部 manifest payload 哈希一致。
- 本 continuation 路径下 seal 绑定的 4738 个文件重新哈希：0 mismatch。这不是对所有全局 Skill/Memory metadata 的无漂移声明。
- historical/helper 字节对照报告 PASS；三个 exact candidate clone 验证报告 PASS。
- 追加凭据扫描未发现 sk-/Bearer 凭据或敏感字段长值赋值；PRIVATE KEY 宽匹配仅命中报告源码中的扫描正则，不是私钥。实际 decision projection 仅含 metadata/delta/hash，不含 Skill/Memory 正文。此项为本地范围审查，不等于独立接受。

## 正式结果（未重跑）
29 gates：0 PASS / 1 FAIL / 28 NOT_RUN。
CHANGE_IMPACT 在 GATE_BOUNDARY 因 FROZEN_BASELINE_DRIFT_ACROSS_COMMAND_GAP 拒绝；native_exit=null（NOT_INVOKED），wrapper_exit=1，retry_authorized=false。
Memory 根目录 metadata.st_ctime_ns：1788838990891651268 → 1788839301436583201。Writer NOT_ESTABLISHED。
OLD_STRICT_PRESERVATION_RESULT=OLD_STRICT_REJECT；V2_INPUT_INTEGRITY_RESULT=REJECT；V2_BOOKKEEPING_EVALUATION=PASS（限定 bookkeeping 范围，不覆盖 strict reject）。

## 交付摘要
PUBLIC_EVIDENCE.zip SHA-256：7c49ed5822d9aa03bfc6e44c704ae199648616fd819cf3188109d08d65c58263
public/MANIFEST.sha256 SHA-256：ca96d3d6c4c5663338c4113229d455910e635ee3b0170984ab55bea0fa36adaa
FINAL_FIELDS_WITH_MANIFEST.json SHA-256：76a3140beb05a342ef40f1928fd047dea5195c4b0b58ed56fc840ac55d7e5c61

本复验记录位于已校验 public 包之外，不改写其 manifest 或 ZIP。机器字段和完整中文主报告见同目录 public/FINAL_REPORT.zh-CN.md 与 FINAL_FIELDS_WITH_MANIFEST.json。

## 恢复与边界
先前报告 executor 因 agent_close 被终止（exit -15）；恢复 executor 完成后，Hermes 首次实际报告运行发现 watches 整数被 len() 处理的报告层错误。bounded Codex 修正 scalar/collection schema 并生成交付，Hermes 再次运行测试并校验交付。该修正未改冻结候选、未刷新 baseline、未重跑 formal graph。
本轮未主动写入 Skill 或 Memory；技能读取可触发运行时 usage bookkeeping，不作为全局零写入声明。未测量的历史分阶段用时不补造。
