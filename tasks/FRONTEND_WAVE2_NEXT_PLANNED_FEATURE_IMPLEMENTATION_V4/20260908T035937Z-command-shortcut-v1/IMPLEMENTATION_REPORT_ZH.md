# V4 命令面板快捷键会话内改绑 — 实现报告

工程验证完成，等待独立评审；产品未提交、冻结、合并或发布。

## 已有计划与交互

依据现有 IA 的 Commands and keyboard architecture（314–325 行）完成一个局部未完成项：既有 override 不再仅改变显示，实际命令面板监听也使用同一有效绑定。只改 navigation.command-palette.open，支持 Mod+K、Mod+Alt+K、Mod+Alt+P；Mod 是 Ctrl/Meta 二选一。通过现有 Shell 的 Keyboard shortcut 入口和 InteractionDialog 改绑、取消或恢复默认；保持原 Commands 按钮与共享 Selection 命令分发。无第二注册表、权限系统、Inspector 或 canonical Apply 通道。

绑定只存在于当前 Shell/context 内，不保存；上下文/owner 退役和卸载清除。非法/冲突 override 保守禁用快捷键并提供修复入口，不静默抢占默认键。编辑控件、组合输入、已处理/重复事件、多余修饰键及其他模态窗口优先。支持集合不等于所有浏览器、OS 或辅助技术下的无冲突认证。英文和简体中文文案、桌面及窄屏交互均有证据。截图人工读取显示新增编辑器在 1440×1000 和 390×844 中控件与文字可见；窄屏沿用底部对话框，背景仍有继承的英文 provisional-context 提示，不宣称全产品本地化完成。

## 身份与证据

BASELINE_IMPLEMENTATION_TREE=79541c256a4405e5e8cd3dd53e36e1611e9959d1

FINAL_IMPLEMENTATION_TREE=66b3b9abd9b79161c8f4c902acfd2acb336a387a

V3 PASS_BOUNDED 已追加到原 UX_WAVE_1_REVIEW.md，原 V3 695/297 测试和 22 个浏览器结果保留历史身份。本轮新执行：定向 279 个通过；完整 704 个通过；相对 V3 新增 9、移除 0。七个工程门禁原生退出码均 0；46 条继承 lint 诊断身份无新增或移除（不是零警告）。最终树的浏览器检查 21 项通过。构建 8 文件；必需引用缺失 0，继承的可选图标缺失 1。详见机器索引、原始报告和验收映射，不从声明推导结果。

完整补丁在外部索引重放得到精确最终树；源码前后端点与相关上下文齐备。真实产品 HEAD/索引保留，范围外前端路径与受保护历史/生成文件无差异；不要求后端 EP19 lane 静止。没有新增 runtime 路径、改守卫或重写历史 H4；正式 Slice1C 台账整合与产品发行仍分开。

## 原始失败与边界

开发 RED/GREEN 与有意义的失败原样保留在 attempts，最终通过不抹去失败。浏览器使用 headless Chromium、CDP focus emulation、原生 pointer/key 和披露的 DOM 定位/滚动/locale 等辅助；宿主 dashboard 与惰性本地认证标记为模拟，未执行真实认证或后端整合。不得扩张为物理设备、触屏键盘、OS IME、屏幕阅读器或其他浏览器验收。

本功能没有网络生命周期，不制造 loading/retry/success。UXW1-002 和现有 API gap 文档说明局部改绑不依赖 Project-layout 持久化；账号/全局快捷键保存未实现，无新需求 ID 或 API 共识。本任务不重试任何旧 detached 收据。

## 交付状态

此报告在证据发布前密封；公开 commit、固定 URL、全量匿名 Git/Raw 差异和 manifest 自身摘要由本地追加发布收据记录，不回写本报告、不无限发布收据。产品发布未授权，下一步仅独立评审。
