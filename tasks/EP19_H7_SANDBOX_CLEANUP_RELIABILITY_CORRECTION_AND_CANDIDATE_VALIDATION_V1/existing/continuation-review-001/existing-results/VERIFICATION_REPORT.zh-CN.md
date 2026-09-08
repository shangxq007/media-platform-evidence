# 既有结果静态核验（非最终独立验收）

LANE=BACKEND_VALIDATION；未重跑任何测试、probe、workload、baseline；未发送信号；仅新增本目录文件。

## 已核实
- HEAD `a29864343ed4f630b052c20d86c23b240f13cfd0`，tree `fd37409d0274662abbe86f69e3d963c05b379696`，直接父提交 `689ab9456461a8d19a72d059f5157092efc43aff`，checkout status 干净。
- 实际 `PRODUCT_PATCH.diff` SHA256 `bab6aee8346f7ef47ca94f1e3da629e7ae81df2f16202706ae4966864a485690`。与 `git diff --no-ext-diff --no-color --abbrev=8 <parent> <candidate>` **逐字节相等**；不是猜测 full-index 序列化。仅三份生产源码与两份测试源码。
- 冻结报告 SHA256 `26d6daa2446590a1032222bb9b4ee99081d2156ba22fb74ee4c35a124b70b49c`。
- 实际解析既有 XML：合成34；focused4；stability-001..005 各2（10次执行）；identity-001为27；native-delta另一次27。全部0失败/错误/跳过。native-delta身份集合与identity-001完全相同，不能增加唯一身份计数。
- 七份 runtime INVOCATION 每份54个源码摘要均匹配候选 Git blob 内容；最终合成快照50份产品/测试源码匹配候选，合成 source manifest 51/51、class manifest 84/84、依赖9/9实际字节匹配。保留原始 argv、native exit 与边界说明。
- 两份 native-delta 回执 native/wrapper exit 均0，Git源码身份、快照及日志摘要匹配；JUnit两份输出摘要匹配。impact输出是已绑定 stdout，outputs映射为空，未伪造额外输出。
- REAL_BINDING_RESULT 的27个artifacts逐项匹配；fresh authority4/4、sources68/68、evidence3/3匹配。资格身份实际去重158；capsule原生日志实际13条ok且native exit0。十个声明复用组件 current/prior 实际摘要相同；仅支持明确列出的未变组件复用，不扩大为所有变更路径。
- DELIVERY_MANIFEST 664/664；PRESERVED_BEFORE 2686/2686。followup BEFORE实际2095项，当前2086相同，9个差异路径恰好等于AFTER authorized_changes，未将摘要声明直接当作核验结果。

## 进程与资源边界
仅检查11个已选择自有回执的明确宿主PID，当前全部 `/proc/<pid>` 不存在（包括629198与629201）；这是采样时已离开的证据，不是全局无残留证明。629175只有上下文历史PID，选择链未找到自有回执，标为identity-unproven且不采样；资格回执PID10缺少宿主namespace映射，亦不采样。没有进程列表扫描、容器枚举、FD/环境内容读取或信号操作。

完整task teardown仍 **NOT_PROVEN**：根进程离开不能推出后代、容器、挂载等全部资源已清除；未以不确定身份探测或处置资源。

## 阻断与限制
1. 正式验证仍BLOCKED_BEFORE_GRAPH；既有报告的baseline拒绝没有被本轮静态核验消除。8000身份/29 skip是EXPECTED，不是完整实际测试通过结果。
2. runtime INVOCATION提供候选源码摘要及原命令，但本轮选定链未找到运行时wrapper/init脚本的完整历史摘要绑定；已记录当前脚本摘要，不能倒推历史字节或静默补跑。本结论是绑定缺口，而非已证明脚本被改动。
3. 158/13是外部绑定工具资格证据，不是产品门禁PASS；明确组件静态复用也不代表新的产品执行。
4. 未形成全资源teardown或最终独立验收结论。本报告只是既有证据版本核对；私有JSON含本地绝对路径/argv，不应直接公开。

文件：`verification.private.json`（详细计数、逐项比较、原命令）；`machine-inventory.json`（公开安全缩减进程清单）；`MANIFEST.sha256.json`（本次新增交付摘要）。既有文件均未修改。
