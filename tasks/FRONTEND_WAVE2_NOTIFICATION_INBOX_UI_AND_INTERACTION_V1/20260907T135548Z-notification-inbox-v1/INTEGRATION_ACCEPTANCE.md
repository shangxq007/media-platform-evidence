# 真实通知集成验收清单 — 全部仍待建立

- [ ] 冻结真实adapter与HTTP prefix、durable inbox路径，禁止把legacy /me/notifications当作已建立集成。
- [ ] 验证list envelope、分页参数/遍历/完整性以及unknown/known全局count语义；不凭loaded page虚构total。
- [ ] principal-owned授权投影与session/principal/tenant变化可观察信号；logout和unknown/denied不泄露旧缓存。
- [ ] Workspace范围显式声明，tenant/resource权限由服务端及目的地强制检查，关联资源缺失/删除/拒绝结果清楚。
- [ ] single-read确切ID/上下文/operation回执和真实持久化readback；失败保持未读，无自动mutation重试。
- [ ] inbox-wide read-all实际可用HTTP端点与范围，跨未加载页面、部分失败、重复/并发语义；service method本身不够。
- [ ] HTTP200错误map必须被识别为失败；error/denied/not-found/partial不转换成读成功。
- [ ] 跨principal/tenant/logout、list out-of-order、All/Unread、refresh/read重叠集成测试；不得复用本fixture结果当真实证明。
- [ ] 真实客户端/服务端契约、TCP交互、数据库持久化与跨会话readback另行授权和执行。

本轮没有发通知、provider测试/重试、event publication、email/SMS/webhook/Novu、浏览器权限或push订阅。UXW2-NTF-002..004/FB-GAP-011..013不实现。
