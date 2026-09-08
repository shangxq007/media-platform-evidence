# EP19 H7 续行交付：具体契约差异待决定

## 结论 B
固定修正候选已完成已有结果的静态核验。本次拒绝不能整体归为外部实现误判：ledger 写事件符合现行 strict 拒绝规则；lock close-write 例外未获批准；usage 的 policy/collector 捕获确实不一致。**未实施新规则，未启动第二次正式尝试。** 已有产品修正成果与具体待决定提案一并交付，正式验收仍未完成。

候选 `a29864343ed4f630b052c20d86c23b240f13cfd0`，tree `fd37409d0274662abbe86f69e3d963c05b379696`；直接父提交 `689ab9456461a8d19a72d059f5157092efc43aff`。补丁摘要 `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`，已用 `git diff --no-ext-diff --no-color --abbrev=8 <parent> <candidate>` 重建逐字节核对。canonical comparison base 单独固定，不冒充直接父提交。产品仍只三份清理生产源码与两份对应测试，续行产品/依赖/生产测试变更为零。

## 产品修正与证据范围
修正清理操作错误被空 survivor 集合覆盖、共享调用者丢失清理失败，以及保留句柄已经确认退出后 start 信息消失导致的误判。主执行失败和清理失败分开保留；live 未知身份、权限/观察异常仍失败。这证明具体缺陷与修正，不证明历史失败的唯一根因。

| 已有执行 | 本轮核验 | 限制 |
|---|---|---|
| 产品合成 | 34，零失败/错误/跳过 | 原 RED 与中间迭代一并保留 |
| focused/共享调用者 | 4，零失败/错误/跳过 | 不是完整后端套件 |
| 稳定性 | 五轮各两个原方法，共10次 | 不合并为新增身份；本轮未重跑 |
| identity | 27，零失败/错误/跳过 | native-delta另一次27完全同集，新增唯一数为0 |
| 外部工具资格 | 158个去重控制、13 capsule | 已有结果静态回核，不是新鲜执行或正式门禁 |

七份 runtime INVOCATION 各54个源码摘要匹配候选；最终合成产品/测试源码50份匹配候选。完整历史 wrapper/init 摘要绑定在选定链仍缺失，不能将源码匹配说成完整运行工具链证明。原结果不被新执行替换。8000完整后端身份及29 skip仅为EXPECTED；完整套件未执行，实际全集计数未建立。

产品迭代3/3；专门诊断1/8（native2、原结果保留，不当成功复现）；正式尝试1/2。历史 baseline-sequence-formal-001 为29/9/1/19；candidate-formal-001为29/0/0/29。后者baseline/launcher均native1、没有accepted baseline/seal/START，preflight和29门未执行。0门禁FAIL不是正式PASS。

## FIRST 拒绝的直接处置
逐项“对象→观察→谓词→保护对象→证据程度→成立/不成立结论”见 [FIRST_REJECTION_ANALYSIS](existing/continuation-review-001/rejection/FIRST_REJECTION_ANALYSIS.json) 与[中文分析](existing/continuation-review-001/rejection/FIRST_REJECTION_REPORT.zh-CN.md)。包含三条事件、两目标、usage两捕获摘要/九字段、时间与调用顺序、原来源摘要和源码版本。

- ledger：mask2及mask8，准备/collector内容hash不同。现行V2无内容豁免；既有hash无法证明纯追加、合法schema或无语义变化。
- exact lock：mask8，与两端相同空文件/元数据共存；不能从端点一致抹掉中间事件，不证明writer或合法性。
- usage：policy/collector的hash、inode及部分时间元数据不同；程序早在observation拒绝处停止，后续capture_binding/evaluate未执行。不得把不一致强绑为PASS，也不把未执行比较写作已运行FAIL。
- 历史writer继续UNKNOWN。没有全机扫描、跨lane静止要求或审批链考古。

## 请求 Owner 决定的精确差异
**默认保留现行strict；以下均未获批准。**

1. [lock/capture提案](existing/continuation-review-001/rejection/NARROW_RULE_PROPOSAL.json)：仅 exact `.usage.json.lock` 的已存在、同身份、空内容、九字段全等的mask8/cookie0进入pending裁决；create/delete/replacement/modify/unknown仍拒绝。允许V2语义变化进入baseline接受是单独规则变化，不能冒充“采集修复”。稳定真实捕获须同源生成hash、metadata、解析投影及capture ID；保留两阶段则必须保存两份真实原件且按契约比较，绝不回填旧行。
2. [ledger提案](existing/continuation-review-001/ledger-proposal/LEDGER_CONTRACT_PROPOSAL.json)及[说明](existing/continuation-review-001/ledger-proposal/LEDGER_PROPOSAL_REPORT.zh-CN.md)：仅精确default ledger，原文件保持身份与原/上一捕获前缀；新增行仅patch/edit、evidence为空、完整非空before/after严格相同且独立strict inventory一致。严格八字段schema，拒绝未知字段/动作/空manifest/重复ID、替换、截断、链接、超范围或不完整捕获。正文、配置、Memory和其他路径不放行。
3. **观测能力必须显式决定**：inotify+端点hash不能证明捕获间无改写恢复。ledger提案只能主张连续覆盖捕获点的前缀完整性，不能主张完整syscall历史纯追加。若这不满足要求，应保留strict，不能为了运行采纳弱保证。ledger会影响审计/rollback选择，不能称全部记录无语义。

### 父复核适用性说明（优先于子报告的建议字段）
- 当前续行已授权常规范围内实施和针对性资格；子报告中“另行授权qualification/第二次”的旧措辞不增加routine审批。**只有实际新契约差异要批准**；已授权的第二次仍以全部前提为条件。
- ledger子提案的3600秒窗口等数字是未批准的设计选项，不是实测值，更不修改原formal或native超时。父建议**不采纳新的全图3600秒上限**；若选ledger方案，保持已适用正式/native时间设置，仅审议其解析/捕获资源限额。不得压缩时限省略验证。
- lock-only不能解决ledger；ledger NOOP子集也不保证下次真实更新符合。不能以改run ID、等安静窗口满足资格。
- 所列控制均PLANNED_ONLY。新predicate影响observer、collector/semantic binding、baseline veto、decision evidence、boundary/coverage/seal；须按依赖闭包新鲜验证并重绑。旧158/13不替代它。

## 第二次正式启动条件
第一次处置已有证据，但新增契约未批准/未实现/未资格，因此条件2、3、5等未满足，**SECOND_ATTEMPT_ELIGIBILITY=NO**。固定候选可以复用，不需要空提交。candidate-formal-001已消费永久保留；本轮没有新namespace、没有baseline重采样。待具体规则决定且实现/资格/身份/私有输出与缓存/前置加载/工具许可全部通过后，才可按既有授权使用剩余一次。

## 安全收尾与保全边界
11个明确宿主回执PID在记录采样点不存在。没有对不确定PID或资源发信号；629175缺selected-chain回执、namespace-local10缺宿主映射，保持未决。**完整后代/容器/挂载teardown未证明**，不把控制进程离开当全资源清理。没有reset/clean/stash、恢复metadata、暂停服务或改动前端lane。前端ref仅界定边界，未在其上执行门禁。没有宣称本轮全时段、全机零变化。

## 公开范围与本地保留
公开包包含五份候选源码、精确产品补丁、RED/GREEN XML/命令/退出记录、分run runtime XML与源码摘要、资格原生日志/修复差异、FIRST三目标缩减记录、提案、预算与机器索引。`SOURCE_LOCATORS.json`列复制来源/字节数/摘要；`PUBLIC_MANIFEST.sha256`覆盖最终公开载荷，manifest本身由detached回执绑定。

完整private before/policy/scope、ledger/usage正文、无关指令及Skills/Memory正文不公开；仅提供三目标hash/metadata/事件及来源定位。公开缩减不是完整捕获副本。历史wrapper/init缺口、未知writer和历史工具审批恢复缺口均保留。子代理曾因scope输出筛选过宽产生工具自动缓存，已披露；不公开该缓存，也未删除现场。

机器索引为封存时快照，提交自身SHA与匿名远端验证不可能预填；最终固定提交URL、manifest摘要、逐文件匿名HTTP回读结果由本地detached DELIVERY_RECEIPT提供，不递归发布回执。证据发布不是产品发布，也不是最终独立接受。

本轮未发出产品/Skill/Memory内容修改；Skill加载可能伴随框架账本更新，不据此声称全局账本未变。没有实施未批准保全规则。

INDEPENDENT_REVIEW=REQUIRED  
EP19_CLOSED=NO_PENDING_INDEPENDENT_REVIEW  
PRODUCT_PUBLICATION=NOT_PERFORMED  
POST_PUBLICATION_SANITY=NOT_RUN
