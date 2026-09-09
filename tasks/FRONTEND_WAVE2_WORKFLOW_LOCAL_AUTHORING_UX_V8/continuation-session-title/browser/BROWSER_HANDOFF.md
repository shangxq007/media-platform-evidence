# Browser continuation — BLOCKED / NOT EXECUTED

本阶段没有浏览器 PASS，也不是独立验收。没有运行七项普通 frontend gates，没有发布、使用真实凭据或修改产品。

## 阻断

1. 首次隔离 fixture 构建真实执行，native exit **1**。`build.log` 保留完整错误。为保证 snapshot/node_modules 只读，外部 Vite options 使用 `configLoader: 'runner'`；实际 `vite.config.ts` 的 `__dirname` 在此 loader 下触发 `ERR_AMBIGUOUS_MODULE_SYNTAX`。构建未生成 `build/`。这是外部 harness/config-loader 兼容问题，不是已证明的产品行为故障。
2. 下一次工具申请（环境检查、外部 build runner 的 `__dirname` 兼容修正和再次 fixture build）被工具审批超时拒绝，**0 internal calls**。没有修正落盘，没有再次构建。遵守拒绝，未换工具或改写申请以完成被拒绝操作。需要 Owner 明确允许通过正常审批重新触发此申请，才能继续这条构建路径。
3. Parent 另行通知七项普通 frontend gates 申请也因审批超时拒绝、0 internal calls。该独立 blocker 不能由本 fixture lane 替代；无 overall PASS。

## 已完成的准备

- 已读 writer/WRITER_HANDOFF.md、writer/AUTH_CONTRACT.md，审阅最终 oidcClient、真实 WorkflowProjectShell subscription、WorkflowSketch、Vite config，以及历史 Chromium harness。
- governance toolchain manifest read-only 校验：26 entries / 26 OK / 0 failed，PASS_HERMES_MANIFEST_VERIFY（工具原始输出在本会话）。
- 只写本目录。历史源来自 `../../browser-attempt-02`，历史目录未修改。
- 外部 `fixture-host/entry.tsx` 路径已转向 `../validation-01/snapshot`，保留真实 routeTree 和实际 subscribeOidcSessionRetirement 消费者。未 mock retirement callback。
- 外部 SDK fixture 使用最终 snapshot 的已安装真实 oidc-client-ts User；模拟 current-store、有效 expiry/scopes、pending getter、old notification payload、新 session、logout redirect rejection。仅显式 loopback `workflowFixture=1` opt-in；身份/Workspace/access 只在外部 fixture 边界模拟，不作为真实授权。
- `FINAL_INTERFACE.json` 的源接口 SHA256 已从最终 snapshot 重算，但整个 source/tree→fixture→build→served binding 尚未完成。目标树来自 Parent 指定 `0289714b2d4094db210b55681fa4f6a8135f7054`；本 lane 不声称独立核验了该 Git tree。

## 证据与计数

根目录：`/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_WORKFLOW_LOCAL_AUTHORING_UX_V8/continuation-session-title/browser-continuation`

- `build.log`：唯一实际构建日志，exit 1。
- `INVENTORY.json`：报告生成前文件完整清单。计数 **35,161 regular files**：fixture-host 35,152；browser 5；4 个根文件。随后新增此清单和本报告，最终预期 35,163 regular files，报告交付前另行只读校验。
- 递归复制 fixture-host 意外展开历史 node_modules symlink，复制大量已安装依赖；没有安装包，也没有新凭据。保留原样，避免把清理混入被阻断执行。清单可用于有界后续清理。
- 已复制的 `browser/workflow_smoke.py` 仍是历史脚本，**尚未适配本次 compact scenarios，禁止当作 continuation evidence 或直接执行**。没有运行旧 preparation interface。
- Chromium 启动 **0**；独立用户场景 **0**；scenario runs **0**；assertion executions **0**；distinct/repeated check names **0/0**。
- 新浏览器截图 **0**；无法提供代表截图或进行本次视觉检查。清单中的 **1 个 PNG 是依赖复制文件，不是截图证据**。
- served-build SHA256 readback、browser console/network、无 Workflow writes/persistence、浏览器 teardown 均 **NOT_RUN**。本 lane 没有启动 fixture server/Chromium，也未获得端口空闲发现结果，因此不声称执行过端口 teardown verification。

## 尚未执行的要求

两次正常 renewal 保持 UI-created 节点/title/position/selection/inspector 未完成输入与 DOM identity；sid/principal 更换退休后可重新编辑；pending old read 与 old UserLoaded/current new store 两种竞态（含 pending B + old A notification）；logout initiation/late read/redirect failure；120 字中文、连续 ASCII、混合标题在 1440×1000 和 390×844 的默认相邻卡 geometry、完整 inspector 和 keyboard focus；基本 add/inspect/arrange/delete；project/workspace/access context 更换；explicit repeats、机器 accounting、raw logs、完整 binding、served SHA256 和 console/network/storage/teardown。

## 必须保留的边界

这是 SDK-boundary 模拟，不是实际 IdP、真实 backend、物理设备、OS IME 或 screen-reader 测试。sid 可选，缺失不能证明 continuity，必须 fail closed。无 generation 标记的旧 SDK operation 若真正覆盖 current store，或 payloadless 旧 invalidation，无法可靠区分旧 generation。真实 provider sid 稳定性、租户语义、远程失效及服务端 session-bound Project/access 未验证。即使后续浏览器通过，也只构成工程证据，不构成 Owner independent acceptance。
