1. 已恢复静态与实际前端契约并记录写入前范围。
2. 已写 adapter/pilot.py 初稿与真实 HTTP 边界测试入口；首次 RED 为模块尚未实现，不算行为 RED→GREEN。
3. 实现后运行真实 loopback 测试，socket 创建被 sandbox 以 EPERM 明确拒绝。遵循 WRITER_BRIEF 停止，不升级、不旁路、不改用 mock 冒充 HTTP。未开始 frontend 适配；Outcome C，不能声明 B。
