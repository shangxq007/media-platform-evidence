# V9 implementation risk review 01（只读风险评审，非验收）

## 身份、范围及证据

- 审阅根目录：本任务 `validation-01/snapshot`；以下产品源码引用均相对此根目录。
- 指定 source tree：`ed691988cec52b967e1724964bd1854f3b88d7b4`，与 `validation-01/FINAL_TREE.txt:1`、`SOURCE_DELTA.json:3` 一致。独立用 Python 对 SOURCE_DELTA 的 **17 个路径**计算 SHA256 和 Git blob SHA1，全部匹配记录；这不是重新验证整个 tree 的所有对象或生成新冻结点。
- 已读 `writer/WRITER_HANDOFF.md`、`BASELINE_CONTRACT_REVIEW.md`、`writer/VERIFICATION_INTERFACE.md`，重点追踪 navigation、NleWorkspace、FoundationPages、共享 Selection/Inspector/Dialog 和相应测试。
- 已读 snapshot 根 AGENTS；frontend 下检索未发现嵌套 AGENTS。根第22行 freeze 要求与本次禁止 freeze 的授权冲突，遵从 Owner，不执行 freeze；治理指令对齐另行处理。
- 未运行产品测试、构建或浏览器，未读取凭据或 live worktree，未修改产品、Skill、Memory、Git。唯一写入为本报告。已有测试仅作为静态覆盖证据，不声称本轮复现通过。
- 不将父方正在修复的 map 变量架构误报、精确新增路径治理清单重复登记为缺陷。

## 可行动缺陷

### IR01-1 — P1：新增导航接入的共享 toolbar 仍可让旧回调修改新 owner 的选择

**源码链：**

- `frontend/src/product/timeline/TimelineNavigation.tsx:29–33` 以 target/source 等变化重挂 NavigationSession，但保留外层 InteractionStore；`:58–67` 注册/清理 adapter；`:188` 渲染共享 `SelectionActionBar`。
- `frontend/src/interaction/SelectionContext.tsx:45–51` 的 adapter 卸载会注销，随后新 session 在同一 store 注册。
- `frontend/src/interaction/model.ts:69–74,128–133` 注销使 lifetime 退休，但新 adapter 注册将同一个 store 的 `retired` 设回 false；`:149–160` 的兼容 dispatch 使用**调用时**当前 lifetime/revision，不验证发起控件的旧 lifetime。
- `frontend/src/interaction/InteractionShell.tsx:17–25` 共享工具栏的 Hide/Show、Clear、Edit properties、Ask 回调直接调用捕获的 store，无控件归属校验。相对地，同文件 `:139–144` 的 command palette 和导航自身 `TimelineNavigation.tsx:112–126,189,196` 有明确新鲜度检查。

**确定的触发序列（静态推导，非攻击假设）：** 在 revision A 选片段，保留 toolbar 的实际 `Clear selection` onClick；切到 revision B（或替换 navigation adapter），新 session 加载后选 B 的片段；调用旧 onClick。它仍指向已重新注册 adapter 的同一 store，`dispatch(select [])` 成功清掉 B 的选择。旧 Show/Hide/Ask 也会作用于新上下文。普通真实 Project/Session shell remount 换 store 的路径不等同于这个同 store 的 revision/source remount，不能用前者测试代替后者。

**影响与归类：** 本地选择/Inspector/Agent 状态可被已退休控件改变，违反本次 retained-controls 隔离目标；不涉及 canonical 写入或权限绕过。共享 toolbar 是继承实现，但这是 V9 新导航实际组合路径中的未封闭边界，不是声称该文件本次新引入了所有问题。

**建议修复：** 共享 toolbar 的操作捕获并比较 store、lifetime 和适当的 selection revision/primary，或为导航接入提供等效受保护回调；不要通过禁止新 adapter 注册或删除原按钮掩盖问题。

**补充验证：** 采用现有真实 callback 提取方式，保留 toolbar Clear/Show/Ask 回调，分别跨 revision 与 adapter 替换执行，断言新选择/面板不变。`TimelineNavigation.test.tsx:251–267` 只提取导航自己的 Inspect/Close；`:212–247` 多处仅对断开的 DOM fireEvent，不能覆盖上述实际共享回调。

### IR01-2 — P2：检查框 open 状态未随选中对象/导航 lifetime 失效，存在无显式检查动作的重开

**源码链及可直接执行的 UI 路径：**

1. 外层实际 shell 始终挂共享 Inspector：`frontend/src/components/app-shell/AppShell.tsx:149–154`。`frontend/src/interaction/InteractionShell.tsx:54–64` 的 NLE 分支保留裸 `mobileOpen`，无 selection/lifetime 归属；只有 workflow 分支 `:66–82` 具备按 store/lifetime/id 清理的逻辑。
2. 在窄屏选一个 track，点 **Open selection properties**，再点该对话框中的 **Clear track selection**（`:51`）。该动作清选择但不清 mobileOpen；`:58` 使对话框消失。随后选择任一 clip，`:58–63` 又渲染仍为 true 的 mobileOpen，对话框自动重开并抢焦点，无新的检查请求。
3. 同样，保持该 mobile Inspector 打开时通过宿主切 revision/source，NavigationSession 重挂而外层 SelectionInspector 不重挂；新对象选中时旧 mobileOpen 可复活。现有 route session 测试是整个 shell 换 key，并未覆盖此路径。
4. V9 自己的 metadata dialog 也有相同状态模型问题：`TimelineNavigation.tsx:45,108–119,124–126,196` 的 detailOpen 是未绑定对象的 occurrence。选择被清除只令 detail 条件为假，effect 仅做焦点回退，不清 detailOpen；后续选择使 metadata dialog 再出现。`TimelineNavigation.test.tsx:199–210` 验证清空时关闭，但未在清空后新选对象检查是否保持关闭。

**影响与归类：** 错误沿用旧检查意图、意外 modal 重开/焦点迁移；不是泄露旧元数据（内容仍从当前 selected 解析）。同一 store 下更新 primary 时是否允许已打开 inspector 跟随可以另定，但“清空后隐藏，再新选自动重开”和退休后复活应明确消除。共享 mobileOpen 是基线已指出的遗留风险，本次新 metadata dialog 则仍未补齐相应失效处理。

**建议修复：** 检查框 open 归属绑定当前 store/lifetime/target/selected id；选择为空、owner/target 变化时同步废弃 occurrence。将关闭/隐藏检查框与显式下一次打开区分，保留仍连接 launcher 的焦点恢复。不要另建 Selection store。

**补充验证：** 加入 mobile track→打开 properties→Clear track→选 clip 不重开的真实组合测试；metadata inspect→clear→选另一对象、revision/source 更换→重新选择均不复活旧 modal。再由父方在窄屏浏览器确认实际焦点。

## 已核对但不列为新缺陷的边界

- **数据来源诚实：** 默认 NleWorkspace 不提供 geometry source；导航只在显式 source、查询 target、Workspace/Project/tenant 和 test-only access 条件匹配时读 isolated adapter。`NleWorkspace.tsx:165–176,438–447`；`TimelineNavigation.tsx:10–13,29–41,81–101,169–174`。真实 tracks gateway 缺失、Project==Timeline 现有映射、fixture 不绑定真实 OIDC 主体，均由 handoff `:7–13,89` 和接口说明 `:9–10,54–58` 明示，不作为新增安全漏洞。
- **精确时间：** `navigation.ts:27–47,98–103` 用 BigInt 有理数比较/差值、拒负数及反向范围；inclusive 两端与 `timeline-module/src/main/java/com/example/platform/timeline/semantics/clip/MediaClip.java:149–164` 一致。零长度点和共享端点多个匹配是明确 authored 契约，不应改成 render half-open。`TimelineNavigation.tsx:128–143,179–185,203` 禁止未知 basis 的定位/派生时长，重叠 locate-selected 保留显式片段。测试 `TimelineNavigation.test.tsx:75–108,155–162` 静态覆盖这些主要路径。未发现需要修正的浮点/FPS推断。
- **收据与迟到异步：** `navigation.ts:80–95` 校验 request/scope/target、全局 clip 唯一、track关系和可选 bounds；`TimelineNavigation.tsx:32,64–72,81–106` 通过 session key、abort、generation、owner 和 snapshot 抑制旧读取。没有据此把本地 fixture 校验说成服务器授权。
- **外层生命周期：** `FoundationPages.tsx:93–115` 扩展既有 OIDC retirement 与语义 access key boundary 至 NLE，忽略 observedAt 的相等续期保持导航。`routeTree.test.tsx:605–644` 有真实 SDK mock 通知的续期/session/access 检查。其注入 scope 必须由宿主响应更新的限制已记录；不是要求本次新造真实后端身份适配器。
- **权限与 Operation：** 导航仅提供 reveal、LOCAL_EPHEMERAL selection/inspect；不导入或调用 Operation/media gateway。既有边界读仍在 `NleWorkspace.tsx:253–271`；preview→冻结确认→apply→权威 readback 在 `:306–418,460–479`。共享 dispatcher 在 `interaction/model.ts:145–169` 仍拒绝 canonical semantic。`NleWorkspace.test.tsx:391–424` 覆盖 injected 导航不额外调用 Operation/media。没有发现导航绕过这些权限链的新路径。
- **单 Selection owner：** source snapshot inventory 是同一 store 的唯一 adapter；精确位置为导航局部状态，没有塞入 SIMULATED_STEP 的全局 time。上述 IR01-1 是旧 callback 归属漏检，不是 competing store。
- **焦点/滚动：** 原生 button、键盘组合/IME 保护、共享 InteractionDialog 焦点 trap/launcher 恢复以及局部 scroll 保存都有实现（`TimelineNavigation.tsx:73–79,145–159`；`InteractionDialog.tsx:6–33`）。CSS 窄屏和长名处理见 `timeline-navigation.css:1–22`。这里只读源码，不用 jsdom scrollTop 断言替代浏览器的几何、原生 Enter/Space、窄屏/屏幕阅读器验收；IR01-2 的复活会破坏原本正确的焦点流程。

## 交接结论

本轮登记 IR01-1、IR01-2 两项本地交互生命周期缺陷，建议有界修复并补充对应组合测试。普通 source unavailable、isolated verification source、真实后端身份/访问未建立及无播放/缩放等是已声明范围限制，不误报为缺陷。不作 PASS/ACCEPTED 或最终独立验收结论；最终独立 review 仍 REQUIRED。
