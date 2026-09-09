# EP19 continuation-005 阅读索引

1. [STOP 汇总报告](REPORT.zh-CN.md)；[当前机器状态](CURRENT_MACHINE_STATUS.json)。先区分授权、机制缺口、实现者资格与独立接受。
2. [原 controller-v1 独立 REJECTED](evidence/original-controller-independent-review-v1/FINAL.zh-CN.md) 及同目录 VERDICT.json：CP-01..04；[coherence final-006 独立 REJECTED](evidence/coherence-independent-review/FINAL.zh-CN.md)：COH-IR-01..04。更早第二控制器拒绝报告在 evidence/control-plane-independent-review。
3. [v2 writer 报告](evidence/integrated-correction-v2/FINAL.zh-CN.md) 及同目录 FINAL_MACHINE_REPORT.json。CORRECTED 仅是 writer 声明，v2 独立审查 NOT_RUN；有关额外授权的历史说法以汇总报告澄清为准。
4. [installer 拒绝源](evidence/integrated-correction-v2/parent-handoff/INSTALL_AFTER_COORDINATION_AND_REVIEW.py)：assess_existing_maintenance_coordination 与 main；[install manifest](evidence/integrated-correction-v2/parent-handoff/INSTALL_MANIFEST.json)；[历史父交接](evidence/integrated-correction-v2/parent-handoff/PARENT_SEQUENTIAL_COMMANDS.md)，只读不要执行。
5. [controller 原三目标 diff](evidence/integrated-correction-v2/ORIGINAL_TARGETS.patch)；[coherence v2 before→candidate diff](COHERENCE_V2_REVIEW.patch)。候选 controller/protocol/tests 位于 evidence/integrated-correction-v2/candidate/controller；coherence source/test 位于 candidate/coherence。旧 controller-v1 与 RED source snapshots 通过映射精确定位。
6. [v2 qualification](evidence/integrated-correction-v2/QUALIFICATION.json)；[日志与来源核验](QUALIFICATION_PROVENANCE.json) 列出六个 native log 链接路径、原始摘要及历史 source-binding 限制。未运行新测试。
7. [原始→公开路径/摘要映射](SOURCE_PUBLIC_MAPPING.json)、[遗漏清单](OMISSIONS.json)、[公开完整性清单](PUBLIC_MANIFEST.sha256)。所有改写源码仅供审阅，不是执行源。

待评估的问题：排他协调如何覆盖旧进程与三个目标完整恢复窗口？CP/COH 修正是否真正满足原既有裁决？source-bound 资格的历史观测边界是否足够？本包不回答为 PASS、不启动新 review；formal/产品发布/sanity/closure 均保持未完成。
