# V5 Canvas 本地撤销/重做实现报告

## 状态、决定与用户结果
工程验证通过，等待独立评审；只发布证据，不提交/冻结/合并/推送/发布产品。
用户可撤销及重做当前 Canvas 的本地标题、位置修改。一次完成的多选拖动只记一条历史，最多50条；撤销后新编辑清除redo。选择、镜头、取消和无效动作不写历史。原先有编辑而没有恢复能力；现有 IA 314–329 明确允许 unapplied presentation drafts 的 local undo，Canvas 基础范围见 foundation 文档282–295。不是重复整个Canvas，也未声称全局优先级。完整预选范围见 SELECTION_AND_SCOPE.md。

## 实现和安全边界
沿用AppShell、Selection、Inspector、既有命令发现和dispatcher，工具栏及命令面板共用历史。仅记录本地标题/坐标，恢复到当前身份与引用上，保留选择/primary/camera；Inspector投影同步，旧提案被拒绝。owner/context/document/adapter retirement和unmount清空历史并拒绝保留回调。同步本地行为不伪造网络状态；空历史拒绝动作但保留稳定可聚焦控件。文本输入原生undo未被接管；安全文本及EN/zh-CN文案。Workflow消费者仅对新无目标动作做类型收窄，无新增Workflow能力。
本地操作不授予canonical权限，不增加后端接口、保存或执行。两个既有需求记录复用 UXW1-002，说明未来可选布局保存与会话历史独立，无新增ID、无约定endpoint/DTO；真实集成未执行。

## V4采纳与治理
已追加既有 UX_WAVE_1_REVIEW.md，包含六个Owner采用字段及全部限制。V4全量704、定向279、浏览器21、七门禁及八产物均为历史，不当作V5执行。V4封存/旧交付不变；H4历史、tracked-dist策略、正式Slice1C与release独立，无全历史债务清零。没有修改Skill/Memory正文，没有旧detached receipt重试。

## 最终验证与失败保留
最终树：`f62687609a556dff204fc6939416c11abd45f945`。定向299通过；完整724唯一身份通过，原V4报告基线704，新增20、移除0、重复0、失败0、跳过0。七项门禁原生退出均0，命令/log/JSON见final-validation/gates。
第一轮type-policy失败后修正测试字面量和Workflow共享消费者收窄；第二轮架构正则误报纯内存Map.get，改为小数组匹配，未修改/放宽守卫。第三轮才是最终通过结果。失败树/patch/log/退出和writer RED/GREEN均保留在attempts，不冒充最终验证。
外部构建8文件，必需引用缺失0，既有可选/vite.svg缺失独立披露；完整SHA256及可重构JS分块。完整accepted-to-final二进制安全patch在外部索引重放得到同树，未写真实索引。浏览器最终32项通过、6截图，覆盖核心标题/位置恢复、分组拖动、工具栏/面板、指针/键盘、空历史、中英/桌面窄屏。browser-01定位器错误保留；同树同构建仅修正外部locator后通过。模拟项目上下文、DOM辅助及设备限制见ASSISTANCE/截图报告，不声称真实后端或物理设备资格。

## 变更和保留
15个既有路径：12个前端实现/测试/样式/本地化，3个文档，无新产品路径。完整前后端点、patch和分类见SOURCE_INDEX/SOURCE_BEHAVIOR_MATRIX。HEAD `f5e19cf53fd010eea2935dd29557e82a879e042c` 不是实现树。保留真实索引与分支/HEAD、原scoped路径成员和执行位、981个allowlist外文件、232个历史/dist文件；不要求并行后端或全系统静止。恢复时曾错误用全仓库成员比较scoped baseline，已按原materialize.py分母校正，无产品更改。

## 下一步与交付
独立评审确切树和本证据包。工程通过不是独立验收，不宣布EP19或全平台集成完成。固定提交、manifest哈希及匿名Git/Raw回读收据只留本地，避免递归发布。全部机器字段见MACHINE_INDEX.json。
