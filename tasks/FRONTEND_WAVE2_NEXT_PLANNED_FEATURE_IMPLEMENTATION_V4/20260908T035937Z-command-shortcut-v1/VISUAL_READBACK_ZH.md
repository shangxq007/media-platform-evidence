# V4 截图实读

读取实际最终构建截图，不由文件名推断行为。

- `01-desktop-editor-en.png`：1440×1000。Keyboard shortcut 编辑器、完整说明、当前 Mod+K、获得焦点的 select、Apply/Restore/Cancel 和关闭按钮均可见；背景保留所选 Canvas 项及单一 Inspector，未见编辑器横向裁切。背景页面仍可纵向滚动，这不是完整编辑器适配声明。
- `03-narrow-editor-zh.png`：390×844。复用的底部对话框，简中说明自动换行，select 和三个动作及关闭按钮全部位于视口；新增交互没有可见裁切。背景导航/工具栏换行，并仍可见继承的英文 provisional-context 提示；不宣称整个平台全部本地化。

像素只证明可见布局，键鼠行为由 21 条原生检查与输入命令记录证明。Headless Chromium、CDP focus emulation、DOM 定位/滚动/locale 辅助均披露；无物理手机、虚拟键盘、OS IME 或屏幕阅读器测试。
