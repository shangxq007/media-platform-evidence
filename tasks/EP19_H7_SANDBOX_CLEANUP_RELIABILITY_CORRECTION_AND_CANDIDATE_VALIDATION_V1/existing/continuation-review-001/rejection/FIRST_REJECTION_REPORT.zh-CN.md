# FIRST baseline 拒绝只读调查（非独立最终验收）

## 结论

**第一次实际拒绝是 `BASELINE_OBSERVATION_REJECT`，不是 capture_binding，也不是 V2 evaluate。** 原始 traceback 位于 runner.py:138；原始私有 receipt 的 evaluation=null，ordering 没有 CAPTURE_BINDING_PREDICATE/SUBSEQUENT_EVALUATION。collector COMPLETE/native_exit=0 与 baseline 进程 native_exit=1 是不同层级，不矛盾。

3 条 REJECT_INSTRUCTION_EVENT 分布于 2 个路径。原始两个 decision-evidence 文件是同一次失败的 private/sanitized 两种记录，不是第二次尝试。

**不能将这次失败整体定性为 Path A 实现缺陷。** ledger 不在 V2 明确批准范围，严格 reducer 拒绝它符合现有契约；若要容忍它，属于 **Path B 新契约**，需要明确 Owner 审批。lock 存在“端点严格不变但 close-write 仍被泛化为 instruction event”的集成疑点；现有 Owner 没有明确批准该事件豁免，不能把疑点当已证实 defect。usage 跨阶段不一致是额外 D 风险，不能通过放宽 ledger/lock 就消除。

## 精确对象→值→谓词→保护目标→强度→结论

下表中的版本统一为 OWNER_AUTHORIZATION_SCOPED_RUNTIME_BOOKKEEPING_V2。所有完整元数据、原始事件及来源 SHA256 见 FIRST_REJECTION_ANALYSIS.json 的 table/sources；未导出全量 private before map、Skill/Memory 正文或 usage 记录ID。

| 对象/事件 | 观测值 | 实际谓词/位置 | 保护目标 | 证据强度 | 支持 / 不支持 |
|---|---|---|---|---|---|
| `.curator_ledger.jsonl` modify | mask=2,cookie=0,observed_ns=154469523131084 | observe.py:70 REJECT_INSTRUCTION_EVENT；:170 → runner:138 | enumeration root 下非批准对象；不是按名字判断instruction正文 | 原始事件+实际源代码；writer UNKNOWN | 支持严格拒绝；不支持“只追加”“由curator写”“非语义” |
| `.curator_ledger.jsonl` close-write | mask=8,cookie=0,observed_ns=154469523309623 | 同上 | 同上 | 原始事件；endpoint见JSON | 支持打开为写的fd关闭事件；事件时间是drain时monotonic时间，不是写入syscall时间；不支持精确writer/因果顺序 |
| `.usage.json.lock` close-write | mask=8,cookie=0,observed_ns=154469524322534；policy/collector九字段完全一致；ino=495362,size=0,mode=33188 | observe.py:64-69只特判usage/temp，:70拒绝lock；bookkeeping_v2.py:369-374要求lock状态/元数据严格相等 | 既存lock身份/生命周期；非任意lock例外 | 事件+两端点；不具完整中间历史 | 支持close-write与空文件端点共存；不支持“写入字节”“合法持锁”“中途从未修改” |
| `.usage.json` policy→collector | hash不等；ino 22589169→22589275；mtime 1788903270814698621→1788903445702266536；ctime 1788903270815698630→1788903445704266554；size两者96588 | capture_binding:439 要求hash及全部metadata相等，但本次未到达 | 真实捕获输入与语义policy绑定 | 两捕获已证实；谓词结果只可标静态推论 | 支持潜在 BOOKKEEPING_BASELINE_CAPTURE_UNBOUND；不支持当作 FIRST/已执行异常；没有collector解析正文，不能证明仅四字段变动 |
| baseline exception | captured COMPLETE，errors=[]；observer_errors=[]；3 rejects；evaluation=null | runner:138 早于 :140/:142；baseline_evidence:20-30只生成summary | failclosed、一票否决及一次性预算 | 原始日志/receipt/实际代码一致 | 支持未调用preflight/gates；不支持手工强绑或重建旧baseline |

usage 原始 hash：
- policy：ac89a0a5e3cd046efffc6aa9acfca4a8804b30769105a4d236dbb20881351c91
- collector：0423d100cb536417edc9b2d8a50a806ec565fddb9b774dd695c2679b12c5d379

ledger 准备阶段 instruction_inventory hash 为 b470610f505e0c67f2a85ec32108b200958c997048f8f538d9ef893abebb0aba，collector 为 fa949f72d9a6621ee2c68b3db0bccd097998b16dc7cf63aca5de7984bca0bbbd。因此还有分时内容变化证据，不只是两个事件标签；没有历史字节差分，仍不能认定 append-only。

## A/B/C/D/E 分类边界

- **A 严格对象**：真实指令正文及references/templates/scripts/assets/config、全部Memory、产品、observer/executor、授权/policy/qualification/baseline/seal/matrix、未知对象仍严格。REJECT_INSTRUCTION_EVENT是scope类别，不是正文鉴定；ledger属于未获例外对象。
- **B 已批准 bookkeeping**：仅 `/home/user/.hermes/skills/.usage.json` 既存合格记录内 view_count/use_count/last_viewed_at/last_used_at；其他字段深相等；计数非bool非负不下降；时间沿现有UTC schema初始化/不倒退；usage替换相关metadata及Skills根指定metadata按V2处理。不能扩大到ledger。
- **C lock lifecycle**：当前policy明载PRESENT→保持全部metadata，不存在“所有lock自由创建/变化”许可。mask8不证明文件内容改变。仅对该操作拟定显式窄规则；这不自动消除ledger拒绝。
- **D 跨阶段一致性**：POLICY_CAPTURE_BEGIN/END在OBSERVER_REGISTER_BEGIN之前，collector随后；这是顺序采集，不是原子快照。两端数据不等为真实证据。不可把policy hash写回collector行，也不可用后来重采样宣称原比较通过。
- **E 真正实现错误**：已证实的是严格failclosed动作，不是产品bug。runner:145在baseline要求OLD_STRICT PASS，与Owner §9“跨路径应用V2、合法变化不应被旧strict意外否决”存在静态一致性疑点；capture coherence本身则必须保留。本次未到该分支、没有V2语义结果，不足以把它认定FIRST的实现根因。若作Path A修正，必须先说明不降低既有实质保护，并另获本阶段实施授权。

## 权威链与代码绑定

已读取当前 formal-tooling/OWNER_AUTHORIZATION.txt 全文；它是旧任务的V2权威，不是本候选的新one-shot授权。与旧任务 bookkeeping-v2-20260908T004809Z/OWNER_AUTHORIZATION.txt 字节完全一致，SHA256=338a9449a678ab0de5e4a7167823e3fff983f38bac76e5deac3c029a1c4c9528。

旧 owner-clarified-execution-20260907T1120Z/OWNER_DECISION.txt 保留严格event义务/缺失历史/writer unknown/独立review pending。当前 CONTINUATION_AUTHORITY.md 明确首个拒绝即停、002仅预留、现有V2范围不扩大。六个关键executor文件当前hash全部等于原始before map捕获hash；详细路径与全digest见JSON。此核验只证明所读代码与失败捕获一致，不宣称整个宿主或产品当前状态全局未变。

## 最窄新规则建议（未审批、未实现、未测试）

完整可审议条款在 NARROW_RULE_PROPOSAL.json。优先建议 **ledger保持strict**，不要为让001变绿发明“安全ledger schema”。新规则仅讨论既存空lock的exact mask8 pending→裁决，以及同一真实捕获字节的policy/collector绑定设计。这样不足以放行本次全部拒绝，必须明确承认。

1. exact lock路径、PRESENT→PRESENT、regular/dev/ino/uid/gid/mode/nlink及所有九字段保持相等、size=0/empty hash；仅 mask==8,cookie==0 可以进入pending。任何modify/attrib/create/delete/move/link/type/未知mask拒绝。即使端点相同也保留事件；Owner必须明确接受该限定观测弱化，不声称完整中间写历史。
2. usage保持现有四字段和temp正则 `^\.usage_[a-z0-9_]{8}\.tmp$`（exact Skills root direct child），不新增通配符。stable read一次产出真实bytes/hash/meta/投影；collector绑定同一capture ID。若分时读，必须保存各阶段真实语义输入并比较；不一致或缺失仍failclosed。
3. 只有Owner明确允许baseline建立期合法V2变化，才拟将runner:145的old-strict veto改为完整strict integrity+V2 semantic+coherent binding+无reject/unresolved+coverage完整。保留OLD_STRICT_REJECT作为事实，不“修复”原001。
4. start封存输入后完整注册watch并稳定捕获；mid持续事件流及每边界真实比较；end drain、所有pending裁决、严格target检查、root entry与temp生命周期完整。未知/不完整/读取失败/watch loss/overflow/证据写失败均拒绝。已有temp观测有限例外不得自动转移到lock或ledger。
5. ledger若未来确需变动，须另行Owner决定及真实writer/reader/schema/依赖审查，明确允许event、字段、类型范围、prefix append-only完整性及禁止历史重写/回退/rotate/replacement。本调查没有足够资料填写其语义schema，因此**没有可激活的ledger豁免**。writer可保持UNKNOWN并不替代内容/依赖证明。
6. 全部正反控制仅为后续计划：unchanged/合规四字段/替换/root变化/真实空lock-close通过；ledger追加、lock修改再恢复、非法字段/type/计数下降、strict bodies/Memory改变、temp越界、缺失capture/旧identity/证据写失败拒绝；真实FS control只在disposable fixtures且获权后运行。
7. 改动影响observer/reducer、bookkeeping、baseline/decision-evidence、scope/sequence/seal及preflight/prestart/每gate/boundary/final。新qualification及source applicability、Owner sha、policy sha、capture协议、matrix、executor identity必须完整重绑；不能整包借用旧qualification，独立review仍PENDING。

**第二次尝试仍BLOCKED**：必须Owner明确批准所有实际新规则、受影响实现/资格验证另获权完成、完整新binding/readiness、Owner明确第二次尝试许可后才可讨论执行。本次无实施、测试、probe、新baseline、产品写、服务暂停、credentials操作；仅新建本目录分析材料。

## 证据强度与执行限制

同一原始事件的observed_ns是在drain解析时取monotonic值，不是syscall发生时间；cookie=0没有rename关联；writer始终UNKNOWN/NOT_ESTABLISHED。没有宿主无写入证明。分析过程中一次scope输出筛选过宽导致工具自动stdout spill（目录路径列表，不是private before map），没有将其纳入交付、没有删除自动缓存。手工发出的证据写入均限制在本目录，工具基础设施自身缓存不应被虚报为零。

本报告为只读分析角色，不是最终独立接受；001历史失败保持不变，产品候选固定身份沿既有identity证据引用，不做新的产品运行或测试。
