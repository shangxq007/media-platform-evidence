# 原始结果与有界时间线

所有行号对应 `sources/runtime/timeline.jsonl`；时间为 Java System.nanoTime 原值（ns），不可换算为跨运行绝对时间。控制器消费时间为 2026-09-08T16:06:26.929924Z，完成时间为 2026-09-08T16:06:27.700543Z。进程 startInstant 是另一来源，不能直接与 monotonic 相减。

| 阶段 | 原行 | 单调时钟记录覆盖区间 ns | 对象身份 | 直接观察/推断与缺项 |
|---|---|---|---|---|
|启动/注册|1,2,3,4|134568984785362 → 134569032793303|root 529945；Java parent 529917|原始记录；实际 ProcessBuilder.start 无独立 begin/end，rootStarted 是成功 start 后 hook。缺少 syscall 时间。|
|timeout|5,6|134569300636263 → 134569303629512|root / 本次 workload|直接记录 deadline 与 PROCESS_TIMEOUT；不是 workload 30s 自身到期。|
|原后代枚举/注册|8,9,10,11,12|134569306395976 → 134569348534490|529946→529948→529949|直接观测 PPID/start identity；名称来自 raw stat，不是当前名称匹配。|
|TERM|15,16,21,22,31,32,37,38|134569350090207 → 134569352722996|529949,529948,529946,529945|destroy 依次 true,false,true,void；exception=null。返回值不是终止完成；errno 缺失。|
|信号邻近身份变化|18,20,24,30,34,36,40|134569350226194 → 134569352787933|四个注册对象|sleep/timeout mismatch；namespace bwrap missing；root unknown。比较操作数缺失。|
|异步 capture 隐式关闭|26,27,28,29|134569351403211 → 134569351598715|stdout/stderr capture threads|与 TERM 交错，发生于原 survivor 扫描前；不可画成全部 capture 都在扫描后。|
|KILL/等待|无独立行|未单独记录|root 与原 descendants|无 KILL 调用事件；静态调用链和零丢弃日志支持本次未进强杀分支；没有 wait 独立起止记录，不能补造。|
|原 survivor|43,44|134569354642042 → 134569356377386|root 与原三后代|actualSurvivors=[] 直接记录；不是后续补充采样的替代。|
|capture join/显式关闭|48,49,50,51,52,53,54,55,56|134569362333032 → 134569362458695|threads 45/47；stdout/stderr|两个初始 join complete=true、显式 close、capturesComplete=true；条件 750ms join 未执行。|
|返回 primary/cleanup|57,58,59|134569303781618 → 134569371150665|root 529945|PROCESS_TIMEOUT、completed=true；returnedNano 来自 result 字段，mark 时间晚于真正返回。|
|独立补充观察|60,61,63,64,65|134569371259314 → 134569564448049|四个保留句柄|isAlive=false；数字 proc 路径退休后不重采样；不证明本方回收后代。|
|独立收尾|66,67,68,69|134569564580484 → 134569566709067|四个注册对象；自有 root Process|actions 全 none；own Process.waitFor=true；unresolvedRisk=true；没有追加信号。|

原始时间线为 70 行：68 条计时事件及 2 条无时间 status。文件序不是所有线程事件的全序；看各事件自身开始/结束时间。所有事件机器对应及原字段见 TIMELINE.json。

原返回 survivors=[]、后来句柄不活、proc 入口消失、自有根 wait 完成、后代由本方回收是不同命题。本次只直接记录前四种相应证据，后代本方回收未建立。没有已确认 Z 状态；没有 errno 证据；不对历史 489968 命名或做当前检查。
