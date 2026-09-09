# ChatGPT 排查入口：EP19 第二次正式失败

本目录为完整报告及相关脱敏证据的不可变发布快照。工程未通过，EP19未关闭；正式预算2/2耗尽，不得据此执行重试。

## 建议阅读顺序
1. [完整中文报告](FINAL_REPORT.zh-CN.md)
2. [诊断入口、源码节选与待判断问题](DIAGNOSTIC_REVIEW.zh-CN.md)
3. [机器索引](FINAL_MACHINE_INDEX.json)
4. [独立排查报告](evidence/second-formal-closeout/independent-failure-review/FINAL_REVIEW.zh-CN.md)
5. [独立差异证据](evidence/second-formal-closeout/independent-failure-review/FINDINGS.json)
6. [脱敏与复现限制](SANITIZATION_AND_REPRODUCIBILITY.zh-CN.md)
7. [公开字节 manifest](PUBLIC_MANIFEST.sha256)

FINAL_REPORT、FINAL_MACHINE_INDEX、LOCAL_RECEIPT及早期索引中的未发布状态，均是保留的打包时事实，不随push改写。实际发布提交、匿名回读和最终交付状态见父任务发布后本地detached receipt与交付消息；不递归发布回执。原PACKAGE_ALLOWLIST覆盖原708文件；本层额外增加本入口及PUBLIC_MANIFEST。

重点：policy_builder.py:65比较实时manifest与预绑定eligible_skills，:66拒绝。准备封存已保存与旧清单不同的两项hash；事后有限107文件比较有2变化、0新增、0缺失。正式时刻actual manifest未保存，完整差异及writer仍未建立。资格179 PASS、准备READY不等于这个交叉关系成立。

请只读分析，不执行包中历史命令；源码路径和JSON已脱敏，来源原hash与公开hash通过SOURCE_PROVENANCE对应，不声称公开代码可直接执行。
