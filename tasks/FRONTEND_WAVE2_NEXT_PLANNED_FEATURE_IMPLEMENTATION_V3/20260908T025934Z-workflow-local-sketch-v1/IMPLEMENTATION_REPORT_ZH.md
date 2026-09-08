# V3 Workflow 本地节点编排草图 — 实现报告

状态：本轮工程证据通过，等待独立评审；未提交、冻结或发布产品。

已在既有 UX_WAVE_1_REVIEW 中追加 Render 采纳与两项勘误。正确的前端提议权限键为 `render.job.summary.query`；既有 Render 请求范围为 `principalId`、`tenantId`、`sessionId`、`projectId`，不含 Workspace。旧密封报告和证据提交保持不变；旧 Raw HTTP 仍为 216/219、三次超时，不改写为全部成功。

本功能依据既有 Workflow “排列七类节点”计划，从空白开始添加本地卡片，复用 Shell Selection、动作分发及 Inspector 完成选择、重命名、移动、定位、移除和确认丢弃。限制为当前页面内存，不保存、不执行、不加载真实 Workflow，不创建边或后端 Operation。卡片上限 12，标题上限 120；局部坐标范围 X 16–896、Y 16–560。共享 Inspector 的通用范围未修改，局部画板范围另有明确说明。

验证基线与最终树：

```text
BASELINE_IMPLEMENTATION_TREE=afc520c2fb8da37961cc6931e71743256b60a3e5
FINAL_IMPLEMENTATION_TREE=79541c256a4405e5e8cd3dd53e36e1611e9959d1
```

完整机器结果见 [MACHINE_INDEX.json](MACHINE_INDEX.json)，源码前后端点与完整补丁见 [SOURCE_INDEX.md](SOURCE_INDEX.md)。定向测试 297 个通过；完整测试 695 个通过，相对 680 基线新增 15、移除 0。浏览器记录 22 项通过。这些是本轮最终树的新执行，不是复用旧 Render 数值。

过程保留真实 RED、失败尝试、审批超时及批准后的接续记录。首次写入器报告不是最终验收；其焦点、组合键及确认框归属发现由后续修正与最终证据替代。

浏览器为 headless Chromium，桌面与窄屏视口仿真，使用 CDP 焦点仿真、原生指针/按键、DOM 定位/滚动/语言辅助以及 CDP 文本插入；未注入 Workflow 节点；既有 Shell 使用明确模拟的 dashboard 上下文与无效本地认证标记，不是实际认证或后端整合。未验证物理设备、触摸/虚拟键盘、OS IME、屏幕阅读器语音或其他浏览器。既有 lint 警告及可选 /vite.svg 缺失保留，未进行无关修正。

后端需求只澄清现有记录，不新增需求 ID；仅描述一个未来固定前后端版本/受控身份数据的只读接入场景，未执行整合。后端独立推进，不要求其 HEAD、索引或运行状态静止。构建预先指定外部输出；原前端 dist 和后端 static 不作为新运行产物。

证据发布与工程结论分离：本报告在发布前密封，最终提交与远端验证由外部交付收据记录。旧 Projects detached 收据限制未重试。下一步仅独立评审此功能，不启动第二功能。
