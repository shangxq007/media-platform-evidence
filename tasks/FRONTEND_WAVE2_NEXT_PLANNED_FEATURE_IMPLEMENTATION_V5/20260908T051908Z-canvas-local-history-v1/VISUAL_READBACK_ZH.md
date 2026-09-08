# 截图与限制

最终6张截图及32项原生检查见 final-validation/browser。窄屏英文截图可见 Undo/Redo、历史数量及未保存说明，按钮换行并可聚焦。页面需纵向滚动，画布不能完整显示于第一屏；不是完整移动创作编辑器验收。保留既有局部英文标题。

Headless Chromium、1440×1000及390×844视口、CDP指针/按键、focus emulation；DOM查询/定位标注/scrollIntoView及语言切换辅助，独立loopback模拟项目宿主与无真实认证的临时标记，详见 ASSISTANCE.json。没有历史/适配器状态注入。没有真实后端、物理设备、触摸、OS IME或屏幕阅读器验证。

browser-01同名按钮定位匹配2项而中止，原记录保留；仅外部定位器限定dialog后，同树同构建browser-02通过。容量和owner生命周期由组件测试证明，不冒充新增浏览器资格。
