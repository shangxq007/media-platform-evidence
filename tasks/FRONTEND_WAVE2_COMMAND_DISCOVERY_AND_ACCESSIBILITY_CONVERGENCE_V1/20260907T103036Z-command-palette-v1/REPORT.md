# 命令发现与无障碍收敛：实现与验证交付

创作者现在可在既有命令面板中使用键盘进入和浏览当前可用结果、看清目标及不可用原因，并通过原生按钮执行既有统一 dispatcher。搜索变化、已移除/禁用结果及过期 Selection/lifetime/revision 不再留下可执行旧候选。中文面板中本地产生的不可用说明已本地化；服务器提供的原始原因保留原义，不虚构翻译后的授权决定。

结论：IMPLEMENTED_AND_VALIDATED，提交 independent review；不是 independent acceptance、整体 Slice1C closure 或产品发布许可。

## 身份与变更
- TASK=FRONTEND_WAVE2_COMMAND_DISCOVERY_AND_ACCESSIBILITY_CONVERGENCE_V1
- LANE=FRONTEND
- FRONTEND_BRANCH=refs/heads/agent/frontend-wave2-product-ux-v1
- PRODUCT_HEAD_UNCHANGED=f5e19cf53fd010eea2935dd29557e82a879e042c
- BASELINE_IMPLEMENTATION_IDENTITY=00128d35b97775b97124ad1921053a0da282690d
- FINAL_IMPLEMENTATION_IDENTITY=43038f740997d0ebb3a8c67f293da7edab563fdb
- FINAL_SOURCE_MANIFEST_SHA256=0cfb3f708ed71c4cfddc044e8a4ec0b007f94a04f9d07bd723865730cb555461
- FINAL_BUILD_MANIFEST_SHA256=19b046a2a9a6f6bbbc90dec6ec3d4920c7fac397a7f69104134122df6ef765ce
- PRODUCT_CHANGED_PATHS=8：生产/展示代码 5、既有测试文件 2、本地化源清单 1；完整路径与前后 hash 见 SOURCE_DELTA.json，任务增量见 TASK_DELTA.patch，原始/最终字节见 before/、source/。
- DOCUMENTATION_CHANGED_PATHS=仅本任务外部证据包；产品仓库文档改动 0。Owner 决定见 OWNER_DECISIONS.md、AUTHORITY_AND_HANDOFF.md。
- 原 HEAD/index 不等于 implementation identity；本次使用外部 index/object store 写内容树，未 stage 真实产品 index，未创建 commit/freeze/ref。保留既有 dirty bytes，完整 baseline patch 另存本地 baseline.patch，公共包仅交本任务增量。

## 实际实现的键盘/焦点合同
- 沿 InteractionDialog 的 data-dialog-entry 进入搜索；Tab/Shift+Tab、Escape、关闭和原 launcher focus restoration 复用既有机制。
- 搜索 Down→首个可执行结果，Up→末个；结果 Up/Down 跳过 native disabled 项并在首尾钳制；Home/End 仅在结果按钮拥有焦点时工作。
- 输入框 Home/End、Space、修饰键和普通编辑仍属于输入；输入 Enter 明确不执行。结果 Enter/Space 仅由原生 click 激活，keydown 不 dispatch。
- 焦点用稳定 command ID 管理，聚焦滚入可视区；query/focus/projection 都是 palette-local，不改变对象 Selection。
- current committed projection 按 ID 重解析，拒绝已断开/替换的节点及缺失/不可用命令；Selection 命令在调用 dispatcher 前比较当前 store lifetime/revision。未新增 Selection、permission、registry、dispatcher 或持久目标 authority。
- composition/isComposing/keyCode229 不被重解释为激活或对话框 Escape；覆盖 compositionend 后 Space keyup。此项为模拟事件回归，不是物理 OS IME 实测。
- 搜索有 purpose/help；一个 role=status 报结果/可用数量或无匹配；不可用具体原因位于 aria-describedby 指向的可读元素，native disabled 维持不可执行。

## 最终验证
| 验证 | 实际结果 |
|---|---|
| 定向 InteractionShell/AppShell/localization | 79/79 PASS（45 + 21 + 13） |
| 最终完整前端 suite | 28 文件，399/399 PASS，0 skip，0 重复测试身份；此最终 tree 上运行 1 次 |
| typecheck | exit 0 |
| 全前端 lint | exit 0，0 errors、46 warnings；warning 路径与本任务改动交集 0 |
| architecture guard | PASS |
| architecture controls | 120/120 PASS |
| 外部 Vite 构建 | PASS；既有 >500kB chunk advisory 保留 |
| 最终 Chromium smoke | 28/28 PASS，Chrome/149.0.7827.55 |
| 文档/身份/任务 diff | git diff --check exit 0；HEAD/index 与捕获基线一致；8 个实际路径全部在 allowlist |

TEST_ACCOUNTING.json 列出 399 个精确测试身份；FULL_UNIT.json 和 gates/ 保留原始结果。已有 localhost:3000 connection-refused/TanStack fixture warning 未被计为后端集成成功。没有运行后端测试。

## 浏览器证据与限制
最终 browser/ 包含实际 CDP keyDown/keyUp、pointer、DOM focus/ARIA/geometry reads、截图和逐断言结果。覆盖输入入焦、方向/边界、无匹配、全不可用、disabled pointer、Enter/Space/可用 pointer、clear 后重新投影、新目标、close return、双语、长标签、结果滚动及 desktop 1440×1000 / narrow 390×844。Canvas→既有 `/edit` 路径的 CDP 文档导航检查已标为 synthetic route assistance，不冒充同文档 SPA 路由机制的全部证明；更细的 retained-context rejection 由组件/store 回归建立。

SYNTHETIC_ASSISTANCE=既有本地只读 HTTP fixture、CDP 文本插入、DOM locale helper、focus emulation、synthetic route navigation；没有直接修改 Selection 或伪造 canonical 成功。
PHYSICAL_DEVICE_SCREEN_READER_IME_LIMITS=未测试物理移动设备、屏幕阅读器输出、OS IME 或物理键盘；窄视口和 DOM 关系不替代这些证明。Review 沿共享组件与完整单元回归覆盖，未扩展新 Review 浏览器矩阵。

过程中保留了真实 RED 与环境失败：首次 Vite 临时配置写入只读 cache 的启动失败不是 assertion RED；随后 runner/no-cache 得到 9 个预期失败，修复后 GREEN；composition 松键新增失败亦已修复。浏览器 helper 导入/绑定文件、selector、TIME_WAIT/preflight 的问题属于任务 harness 接线错误，保留原记录。中间实现 163a57a6ed991c60492043d8c98c9314994bcc44 的 383/383 unit 与 23/23 自动 smoke 不是最终证明；截图审阅发现中文英文混杂后，新增真实 AppShell 双语 RED，再完成最终 399/399 + 28/28。没有重新打开任何已接受 pagehide/validator finding。

## 构建与边界
BUILD_OUTPUT_PLAN.json 保存实际解析结果。裸 build 原 outDir 为 platform-app/src/main/resources/static、emptyOutDir=true；本任务显式 override 到新 E/build，预解析确认后才执行。Vite bundle loader 的临时配置通过仅本任务命名空间挂载到外部 vite-temp，真实 node_modules/配置/lockfile 未改。产品树、snapshot 的源文件和 dist/static 在验证/构建命名空间中只读。

8 个 tracked frontend dist 与 3 个 tracked backend static 文件前后 SHA-256 全部一致；见 PRESERVATION.json。任务拥有的 fixture/Chromium 已关闭，最终 4196/9267 listener 为 0。此为有界观察，不声明全机或其他 worktree 持续冻结。

## 治理与下一步
H4_DISPOSITION=PROPOSAL_A_ADOPTED
H4_RECONCILIATION=NOT_PERFORMED_IN_THIS_TASK
TRACKED_DIST_POLICY_DISPOSITION=PROPOSAL_A_ADOPTED
TRACKED_DIST_IMPLEMENTATION_MIGRATION=NOT_PERFORMED
LOCAL_UI_CONTINUATION_BEFORE_FORMAL_LEDGER_INTEGRATION=AUTHORIZED
PRODUCT_FREEZE_PUBLICATION_GATES=RETAINED
BACKEND_CHANGES=0
NEW_BACKEND_REQUIREMENTS=0（UXW1-006、UXW1-007、FB-GAP-002 保留，不重复 ledger）
TRACKED_DIST_CHANGES=0
BACKEND_STATIC_CHANGES=0
PRIOR_PAGEHIDE_VALIDATOR_REOPENED=NO
PRODUCT_COMMIT_FREEZE_MERGE_PUSH=NOT_PERFORMED
PRODUCT_PUBLICATION=NOT_PERFORMED
INDEPENDENT_REVIEW=REQUIRED
STOP=YES

本任务无须再次请求 Owner 的 Proposal A、分支或开发顺序确认。下一步是独立评审本包，不是再开设计恢复或 validator/browser 任务。正式 ledger 集成、H4 current-scope reconciliation、未来 packaging/artifact freeze 和任何发布仍属于原有后续边界。证据 commit、manifest hash 与远端 readback 在独立 detached receipt 及最终交付消息提供，避免自哈希循环。
