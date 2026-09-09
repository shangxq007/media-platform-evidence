# V11 写入前范围与契约恢复

当前工作树沿用 Owner 指定 branch agent/frontend-wave2-product-ux-v1，HEAD f5e19cf53fd010eea2935dd29557e82a879e042c；实际接受基线为未提交树 afc966ad4872e6dd65997281c75fe49e7aaed376。RECOVERY.json 逐文件核对见 baseline-check.json；保留所有先前改动及 stash。

适用仓库根 AGENTS.md；frontend 无嵌套 AGENTS。父路径及任务根未发现额外指令。Owner 明确禁止提交/冻结/index 写入，优先于 AGENTS 候选 SHA 冻结一般规则；用基线、逐文件哈希及任务补丁交接，父任务负责最终树和七门。治理规则对齐作为后续独立事项，本次不改 AGENTS。

已读 WRITER_BRIEF、INITIAL_BOUNDARIES、RECOVERY（机器校验），research 下 IMPLEMENTATION_CONTRACT、OFFICIAL_CONTRACT_REVIEW、endpoint-allowlist、v10-field-mapping、deployment-pin，实际 Publication types/model/workspace/tests、EffectiveAccess、ProjectContext、OIDC retirement、Selection lifetime 与 application query gateway。公共 Postiz v2.23.0 / 1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9 仅 GET integrations 与 posts(startDate/endDate)，原始 Authorization，无分页。组织级读取须单独明确授权，服务器按 integration.id 过滤不缩小上游凭证权限。

实现范围：taskroot/adapter 标准库可运行本地服务与真实合成 HTTP 测试、显式隔离 host；frontend publication 最小分支消费独立 owner-local receipt；必要本地化及既有 scope/path/gap/planning 账本。全局 EffectiveAccess/项目认证不改、不冒充 SERVER 或 test-only 权限。普通入口无配置继续 unavailable。固定实例/版本/IP、一个稳定 Project/account、独立本地 caller auth、内存凭证、限制时间/字节/并发/读量/重试，重定向与其它路由一律拒绝；生命周期取消与代次防旧响应。

保留原始状态；QUEUE 日期仅 scheduledAt；PUBLISHED/ERROR 时间 unknown，DRAFT unscheduled；递归排除并 partial，非递归重复 ID 拒绝。无分页只 bounded/partial；releaseId 仅供应外部引用、缺失 attempt 关系；releaseURL 不输出。不存在的 artifacts/attempts/externalPublications 不造数据，无 copyVersion。

验证：有意义 RED→GREEN，完整真实本地 synthetic HTTP 边界，受影响 frontend tests/typecheck/lint/architecture controls；构建与收据全放 writer/adapter。不访问真实实例/账户/凭证、不发送、不启动容器、不改 backend/shared dist/EP19，不提交、不操作 index/remote。完成离线后仅 Outcome B，交接中文并列实际读取最小外部条件。
