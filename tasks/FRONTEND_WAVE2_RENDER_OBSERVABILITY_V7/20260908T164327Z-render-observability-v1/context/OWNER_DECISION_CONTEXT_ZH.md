# 大模型上下文（精简版）

```yaml
context:
  schema: llm-context-compact-v1
  knowledge_as_of: '2026-09-06'
  language: zh-CN
  purpose: >-
    为后续大模型提供媒体生产平台的现行决策、候选方案、权威边界、实施状态与外部核验边界。
    本文是决策上下文，不是代码、部署或测试结果证明。
  reading_rules:
    - 决策状态、实现状态、持久化状态、证据状态必须独立解读。
    - 对话中已采纳或保留，不等于已实现、已入库、已集成或已验证。
    - 提议、待决、目标与计划不得描述为当前能力。
    - 已被替代的记录不得作为现行规则；应采用其替代项。
    - 仅有对话或声明级证据的事项，操作前必须复验仓库、运行环境或官方资料。
    - 外部核验只确认所列技术的角色、项目身份、许可或宽泛维护状态；不证明内部集成完成。
    - 涉及安全、权限、权利、计费、资源和发布的未知条件一律保守处理并默认拒绝。
  status_semantics:
    ADOPTED_IN_CONVERSATION: 对话中已采纳；不等于已实现或已持久化
    RETAINED: 保留为现行方向；仍以实现与证据字段判断落地程度
    PROPOSED: 提议；不得作为当前事实或已批准承诺
    PENDING: 待决；不得据此选型或实施
    SUPERSEDED: 已被替代；仅保留历史语境，不作为现行规则
  global_invariants:
    - Canonical 对象每类只有一个写入权威；外部系统、前端、队列、Agent、Plugin、Provider 与 Worker 均不得越权。
    - Canonical Timeline、Operation、Revision、Artifact、Workflow 与业务权限由平台类型化语义定义，第三方工具只在适配边界内工作。
    - 概率性 AI 输出先形成 Observation、Proposal 或不可变 Artifact，再经预览、授权与类型化 Operation 提交。
    - 执行计划、缓存、优化、重写和后端替换不得改变 canonical 结果；未知等价性时关闭优化。
    - 身份认证、授权、Capability、Entitlement、Quota、Trust 与资源策略分权并取交集，前端展示不能授予权限。
    - 版本、实现、配置、运行镜像与输入必须固定到足以重放和审计；历史产物与当前上游新鲜度分开判断。
    - 不可信代码、任务包、社区算力和远程工具必须最小权限、隔离、验证，并禁止隐式执行。
```

## 决策全集

以下 YAML 列表覆盖全部决策。字段：`id` 唯一标识；`topic` 主题；`rule` 规则；`why` 理由；`decision` 决策状态；`implementation` 实现状态；`persistence` 持久化状态；`evidence` 证据状态；`confidence` 信心；其余字段为关系。

```yaml
- id: ARCH-CACHE-001
  semantic_digest: 69c702e5af86b58c
  topic: 缓存与 Artifact 复用
  rule: 缓存分进程内、本机和集群层，命中只是一种执行优化，不得改变 canonical 结果；复用必须同时匹配输入、semantic digest 与 implementation digest。旧 Artifact 可对固定输入仍有效而相对当前上游过期，不能用单一二元有效性表达。
  why: 把缓存和产物有效性锚定到完整摘要，可在保持语义确定性的前提下安全复用。
  decision: ADOPTED_IN_CONVERSATION
  implementation: UNKNOWN
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-DATA-001
  semantic_digest: f80c8c1890eccb07
  topic: PostgreSQL authority 与扩容
  rule: PostgreSQL 保持 canonical relational store；扩展只用于观测、查询、索引、检索和分析，不定义领域语义。容量治理依次采用纵向扩容与 SQL/index/VACUUM 优化、partition/read replica、分离非 canonical workload，只有证明单
    primary 边界后才按 project/tenant 分片，并保持单项目 Revision Graph 位于同一 authoritative shard。
  why: 延后分片并限制扩展职责，可降低迁移和一致性成本，保持 canonical 事务边界。
  decision: PROPOSED
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: ARCH-DSL-001
  semantic_digest: 7ce5d6ac31624bb7
  topic: DSL 与 IR 分层
  rule: 首版采用 JSON/YAML Schema 与类型化 Canonical IR，固定 Authoring DSL → Canonical IR → Operation/Execution IR 或 RenderPlan → Provider Output 的分层；Canonical IR 是版本、Diff、Hash
    与语义权威。自定义文本 DSL 延后到 Canonical Core、Capability 和 Typed Operation IR 稳定且需求验证之后。
  why: 先稳定语义和类型系统，可避免过早维护通用语言及其解析器、迁移和安全负担。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: ARCH-EFFECT-001
  semantic_digest: eeb933e103c288c9
  topic: Effect、Transition 与 Automation 语义
  rule: Effect 与 Automation 使用有序 Effect Stack、稳定 EffectInstance、版本化强类型参数及 AutomationCurve/Keyframe；首版插值限定为 HOLD 和 LINEAR。Effect/Transition 固定 resolved semantic version，Crop/Transform
    属于 composition primitive，Mask geometry 与生成能力分权，并在 Timeline/RenderPlan 之间建立局部语义 delegation seam。
  why: 强类型、版本固定和明确委托边界可保证效果可复现，避免任意 JSON、脚本和后端私有语义成为权威。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: medium
- id: ARCH-EXECUTION-001
  semantic_digest: 0406ea9226626e1c
  topic: Timeline 到执行后端的编译边界
  rule: Canonical Timeline 描述作品，Core 将其编译为后端中立的 RenderGraph/Execution Plan 与 ExecutionTaskEnvelope，再由 Backend Compiler 生成具体命令；Worker 不解释 Timeline，也不自行选择业务语义。
  why: 分离作品权威、计算计划和后端命令，可替换执行后端并防止 Worker 演化为第二套领域内核。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-EXTERNAL-001
  semantic_digest: 5936cb5c19f1f467
  topic: 外部平台与基础设施边界
  rule: PVE、Dokploy、RustFS、n8n 等拓扑只是环境实施；NiFi 仅为可选、可替换的 remote-managed Integration/Dataflow Provider；Odoo 仅为外部 Back-office/ERP/Business Operations 系统。它们都不得成为 Timeline、Revision、Operation、RenderPlan、Workflow、Entitlement、Artifact
    或其他平台领域状态的权威。
  why: 将基础设施、数据流和 ERP 限定在适配边界，可替换技术实现并保护平台 canonical authority。
  decision: RETAINED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-FLAG-001
  semantic_digest: 9c14c96e8d531e1c
  topic: OpenFeature 渐进发布
  rule: 保留 OpenFeature 作为特性求值方向，但在消除双路径求值、实现确定性百分比分桶、补齐管理 API 授权与上下文并建立实验闭环前，不宣称生产级渐进发布已完成。
  why: 明确保留方向与验收缺口，可防止将已有 SDK 或数据库接入误判为完整发布能力。
  decision: RETAINED
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: REGISTERED_OR_FROZEN_IN_SOURCE
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: high
- id: ARCH-GOVERNANCE-001
  semantic_digest: 21529d35e22f8718
  topic: Shared Kernel 与架构复核治理
  rule: Shared Kernel 必须最小化并受准入与暂停扩张规则约束；关闭 routine substage 和默认逐 milestone 独立评审，只在既定 Architecture Epoch 或 authority、scope、frozen contract 发生重大变化时复核。已拒绝的第三方重开阶段、重排路线或提前替换实现建议不得被视为现行决策。
  why: 稀疏而有触发条件的复核与受控 Shared Kernel 可减少反复重开结论和跨域耦合。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-MATERIAL-001
  semantic_digest: 70e175c4eca032c8
  topic: PBR 材质标准
  rule: 通用 PBR surface 使用 pinned OpenPBR semantics，不自建平台专有通用 PBR；MaterialX 只负责图、interchange 和 compiler mechanics，并将规范版本、图版本、renderer 版本分离。
  why: 采用开放且固定版本的材质语义可减少专有模型成本，同时保持编译器和渲染器可替换。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-OPTIMIZATION-001
  semantic_digest: 6823aa5218dd2fb5
  topic: 约束、重写与成本优化
  rule: 先由类型化领域约束确定合法计划空间，成本优化只能在其中选择。任何 Provider 替换、融合、重排或 rewrite 都必须满足显式 interoperability contract、已定义 law、前置条件和证据；未知时 fail closed，重要决策与计划选择必须可追溯。
  why: 把合法性证明置于优化之前，可防止性能或成本策略改变 canonical 语义。
  decision: ADOPTED_IN_CONVERSATION
  implementation: UNKNOWN
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: ARCH-PLUGIN-001
  semantic_digest: 598fdc302c9a1331
  topic: 首版插件架构
  rule: 首版让内置 Source、Trim、Encode、Output 节点通过统一 Plugin SPI 运行，不建设市场或加载第三方代码；PF4J 仅作为可信 Java 插件的打包与生命周期 Adapter，不是插件语义最高权威。
  why: 以内置插件验证 SPI 并限制 PF4J 职责，可先证明扩展边界而不提前承担不可信代码生态风险。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: ARCH-SCENE-001
  semantic_digest: 65aa52667c9dad96
  topic: Blender 与 Omniverse 边界
  rule: Shot Manifest 管镜头意图，Blender/.blend 是编译执行状态而非 canonical revision；Omniverse 只可作为 bounded POC 或可选 Scene/RTX surface，不得拥有 canonical media state。
  why: 将 DCC 与实时场景平台限制为执行或表面层，可避免工具文件和外部平台接管媒体权威。
  decision: PROPOSED
  implementation: UNKNOWN
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: medium
- id: ARCH-STORAGE-001
  semantic_digest: 3877916034a334f5
  topic: 统一存储语义顺序
  rule: Unified Storage Semantics 应在 Timeline Media Semantics 完成后立即建设，并先于 Artifact/Provenance 扩展、Execution Provider 与商业交付。
  why: 先固定存储身份和生命周期边界，可避免后续 Provider 与交付功能固化临时 URI 或覆盖语义。
  decision: PROPOSED
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: ARCH-SUBTITLE-DELIVERY-001
  semantic_digest: ad6b99ae634dec7b
  topic: 字幕交付轨道
  rule: 普通和多语言字幕默认作为独立 subtitle tracks；只有复杂动态字幕烧录到唯一主视频流，不得因字幕默认创建多个视频流。
  why: 独立字幕轨兼顾切换、可访问性和体积，烧录仅用于格式无法表达的动态视觉。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: PROPOSAL_IN_CONVERSATION
  evidence: SOURCE_ONLY
  confidence: high
- id: CPG-001
  semantic_digest: 71ad654570ef6115
  topic: One Core / Many Products
  rule: 平台采用 One Core / Many Products：AI / Hybrid Media Production Platform 以单一 canonical media core 和单一 semantic Operation model 支撑 Guided、Studio、Developer 及各应用表面；Core
    Platform、Product/UX、Studio/Application Showcase 可并行演进，但不得复制 Timeline、Asset、History 或权限权威。
  why: 共享语义核心可让不同复杂度和产品定位复用身份、版本、操作与治理，同时避免形成多套不可互操作的领域模型。
  decision: RETAINED
  implementation: PRODUCT_VISION_ADOPTED_SHARED_CORE_IMPLEMENTATION_NOT_REVERIFIED
  persistence: CONSOLIDATED_FROM_REPEATED_PRODUCT_ARCHITECTURE_DECISIONS
  evidence: CONVERSATION_DECISIONS_NO_CURRENT_END_TO_END_VERIFICATION
  confidence: high
- id: CPG-002
  semantic_digest: 30987fcd48cf359e
  topic: 单语义 Workspace 与多产品表面
  rule: 采用单一语义 Workspace：CREATE、PLAN、CANVAS、FLOW、EDIT、PRODUCE 以及不同产品复杂度都是共享对象的上下文投影；Canvas 几何和连线仅属 presentation，语义关系进入 typed authority；各前端共享 design system、semantic
    components、统一对象身份和 capability/permission projection。
  why: 多表面可优化不同创作任务而不分裂领域真相；竞品只提供交互语法和信息架构参考，不成为平台本体。
  decision: ADOPTED_IN_CONVERSATION
  implementation: UX_ARCHITECTURE_DECIDED_IMPLEMENTATION_NOT_REVERIFIED
  persistence: CONSOLIDATED_PRODUCT_UX_DIRECTION
  evidence: CONVERSATION_DECISIONS_NO_USABILITY_OR_INTEGRATION_VERIFICATION
  confidence: high
  depends_on:
  - CPG-001
  refines:
  - CPG-001
- id: CPG-003
  semantic_digest: 645ee9dddcfb78a4
  topic: 近期产品切入与范围收敛
  rule: 近期优先交付个人 AI 媒体生产系统中的 LibTV 类 Agent/API 后端与单视频垂直切片，以真实内容闭环验证价值；完整多租户、计费、市场、协作、无限画布及全套商业基础设施延期。
  why: 当前主要风险是过度建设；先验证单人真实生产闭环，再扩大产品和商业范围。
  decision: PROPOSED
  implementation: SCOPE_RECOMMENDATION_PRODUCT_DOMAIN_EARLY
  persistence: RETAINED_ROADMAP_RECOMMENDATION
  evidence: USER_INTENT_AND_CONVERSATION_ANALYSIS_NO_DELIVERY_VALIDATION
  confidence: medium_high
  depends_on:
  - CPG-001
  refines:
  - CPG-001
- id: CPG-004
  semantic_digest: 67d6e9cceb0ea5cf
  topic: Application 组合层与 Creative Products
  rule: ApplicationDefinition 是版本化产品组合层，组合 Workflow、Recipe、Template、Capability、Agent、Integration 与 typed/versioned creative products；模板通过 TargetRole 绑定素材和参数，不扩张固定
    productId 字段。外部 Workflow/Skill 是应用蓝图而非 Runtime 权威，只有经跨应用复用验证的契约才可晋升平台原语。
  why: 把参数绑定、产品组合、创作产物和运行时权威分开，可支持多素材应用并快速形成产品，而不持续膨胀 API 或核心领域。
  decision: ADOPTED_IN_CONVERSATION
  implementation: COMPOSITION_MODEL_DECIDED_RUNTIME_AND_PROMOTION_PROCESS_NOT_REVERIFIED
  persistence: CONSOLIDATED_APPLICATION_ARCHITECTURE
  evidence: CONVERSATION_DECISIONS_NO_APPLICATION_RUNTIME_VERIFICATION
  confidence: high
  depends_on:
  - CPG-001
  refines:
  - CPG-001
- id: CPG-005
  semantic_digest: 6dcea5c0144a71a4
  topic: Application rollout 与 AI/Hybrid Film
  rule: Application rollout 顺序为 A1 Shorts、A2 Localization、A3 Podcast/Interview、A4 Ecommerce、A5 HandDrawn、A6 PaperCollage、A7 StopMotion、A8 AI/Hybrid Film；A8 定位为 Film
    Production Studio，并将 Creative Development、Media Composition、Production Execution 分域，以 typed products 和 immutable Shot Artifacts 衔接 canonical Timeline。
  why: 稳定的应用序列与责任域边界既支持递进式产品验证，也避免故事开发、镜头制作和最终剪辑争夺权威。
  decision: ADOPTED_IN_CONVERSATION
  implementation: ROLLOUT_AND_DOMAIN_BOUNDARIES_ADOPTED_DELIVERY_NOT_REVERIFIED
  persistence: FORMAL_PRODUCT_ROLLOUT_DIRECTION
  evidence: CONVERSATION_DECISIONS_NO_APPLICATION_DELIVERY_VERIFICATION
  confidence: high
  depends_on:
  - CPG-001
  - CPG-004
  refines:
  - CPG-004
- id: CPG-006
  semantic_digest: 45c5ee637b2c5c84
  topic: 插件 artifact 与产品发行边界
  rule: 第一方插件采用独立 monorepo module，默认一个叶插件一个主 JAR，同一 artifact 支持 bundled 与 external loading，Full 产品仅是 core 加预装插件；Epoch 3 只保证 SPI/authority 边界 plugin-ready，不提前实现 marketplace、hot
    reload、完整 PluginClassLoader 或完整 Plugin Runtime。
  why: 统一 artifact 可避免内置与外置实现分叉；先验证真实 Provider 插件，再扩大插件平台范围。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PACKAGING_AND_EPOCH_SCOPE_ADOPTED_FULL_RUNTIME_NOT_IMPLEMENTED_BY_CLAIM
  persistence: CONSOLIDATED_PLUGIN_PRODUCT_SCOPE
  evidence: CONVERSATION_DECISIONS_FIRST_PROVIDER_ACCEPTANCE_NOT_REVERIFIED
  confidence: high
  depends_on:
  - CPG-015
- id: CPG-007
  semantic_digest: eb7af123d84478f5
  topic: 版本兼容与接口生命周期
  rule: 兼容范围必须用显式 VersionRange 表达，并以 ProducerReleaseVersion 与 CompatibilityAdvisory 标注 known-bad producer；接口版本独立于平台发行版本，使用 DRAFT/PREVIEW/STABLE/DEPRECATED/RETIRED
    元数据和 breaking-change 机器门禁。绿地版本治理收敛为唯一 canonical 表达，除非发现真实外部消费者或持久化生产数据，否则不保留 alias、fallback、legacy parser 或双读双写。
  why: 显式版本和生命周期证据比从产品版本猜测兼容性更可靠；绿地系统避免无事实依据的迁移复杂度。
  decision: ADOPTED_IN_CONVERSATION
  implementation: GOVERNANCE_ADOPTED_MACHINE_GATES_AND_CONSUMER_AUDIT_NOT_REVERIFIED
  persistence: CONSOLIDATED_VERSION_GOVERNANCE
  evidence: EXPLICIT_CONVERSATION_DECISIONS_NO_CURRENT_REPOSITORY_VERIFICATION
  confidence: high
  depends_on:
  - CPG-020
- id: CPG-008
  semantic_digest: fdc338cd90e6c11c
  topic: GraphQL 写入与 Federation 边界
  rule: GraphQL mutation 仅 lower 为 bounded application commands/OperationPlan，禁止逐字段 CRUD mutation；Federation 延期，只有在独立部署、独立所有权和网络隔离的服务真实出现后重评。
  why: 写入必须经过领域操作与授权边界；不存在真实服务边界时引入 Federation 只会增加分布式复杂度。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: DESIGN_PROPOSAL_ONLY
  confidence: high
  depends_on:
  - CPG-001
  - CPG-011
- id: CPG-009
  semantic_digest: afd5642f5e5134ff
  topic: 商业、订阅、计量与授权权威分离
  rule: 支付、商业合同、账单、平台订阅、Usage Metering、Entitlement、Quota 与 Authorization 分离权威：Odoo Subscription 管商业合同与账单事实，Platform Subscription 管平台订阅状态；初期贡献算力采用 credits/accounting，不引入
    token/crypto。
  why: 商业事实、能力资格、用量和操作许可具有不同生命周期；分权可避免支付或订阅状态直接越权成为授权结论。
  decision: RETAINED
  implementation: AUTHORITY_BOUNDARIES_DECIDED_INTEGRATION_NOT_REVERIFIED
  persistence: CONSOLIDATED_COMMERCIAL_GOVERNANCE
  evidence: CONVERSATION_DECISIONS_NO_END_TO_END_BILLING_OR_AUTHORIZATION_VERIFICATION
  confidence: high
  depends_on:
  - CPG-011
- id: CPG-010
  semantic_digest: 9772590491c1f1ac
  topic: Canonical state 与 UX 投影
  rule: PostgreSQL canonical state 是当前事实，lifecycle events 是历史，队列仅负责运输与唤醒；Execution View 与前端状态机都是投影，不得反向成为领域真相。
  why: 消息可重复、延迟或乱序，投影也可过期，因此都不能承担最终状态权威。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PARTIAL_DESIGN
  persistence: CONVERSATION_ONLY
  evidence: NO_RUNTIME_VERIFICATION
  confidence: high
- id: CPG-011
  semantic_digest: d2067176619a7c76
  topic: Effective Access 与统一授权权威
  rule: 后端是唯一授权权威。Effective Access 是 Authentication、RBAC/ABAC、Capability 与 runtime availability、Entitlement、resource-aware Policy、Quota、Trust/Sandbox、用户权限及 Workspace
    policy 的交集；Feature Flag 不得授予权限，Agent、Skill、MCP 或远程模型的 delegation 不得造成信任或权限升级。前端仅消费 principal-filtered EffectiveAction 投影，并在 prepared execution 时重新授权。
  why: 身份、基础权限、上下文策略、商业资格、配额和信任条件必须分权并取交集，才能防止 UI、Flag 或委托链绕过服务端授权。
  decision: RETAINED
  implementation: MODEL_ADOPTED_EXISTING_RBAC_FOUNDATION_ENFORCEMENT_NOT_REVERIFIED
  persistence: CONSOLIDATED_SECURITY_AND_UX_AUTHORITY_POLICY
  evidence: CONVERSATION_DECISIONS_WITH_PRIOR_GAP_CLAIMS_NO_CURRENT_ENFORCEMENT_TEST
  confidence: high
  depends_on:
  - CPG-010
- id: CPG-012
  semantic_digest: dd2383cebf5a4ebb
  topic: Rights authority 与授权门禁
  rule: Rights/Usage Policy 采用跨媒体 typed foundation，RightsEvidence 与 EffectiveUsagePolicy 分离；权利检查在 OperationPlan、RenderPlan 与 Publication 的 authorize 阶段执行，不得散落于 UI
    或 Provider Adapter。
  why: 原始证据不等于可执行政策，集中门禁才能对不同媒体、用途和发布目标给出可审计的授权结论。
  decision: ADOPTED_IN_CONVERSATION
  implementation: RIGHTS_MODEL_AND_GATES_ADOPTED_IMPLEMENTATION_NOT_REVERIFIED
  persistence: CONSOLIDATED_RIGHTS_GOVERNANCE
  evidence: EXPLICIT_CONVERSATION_DECISIONS_NO_END_TO_END_RIGHTS_VERIFICATION
  confidence: high
  depends_on:
  - CPG-011
  refines:
  - CPG-011
- id: CPG-013
  semantic_digest: 070f3b3dc35626fd
  topic: 字体许可、供应链与 Registry
  rule: Font Registry 管理内容 digest、许可、商用/嵌入/再分发权限、作用范围与 fallback chain；字体字节在 sandbox 中完成结构验证、sanitization 与执行 conformance 前不得进入 shaping/render，且结构安全与渲染一致性证据分层记录。
  why: 字体同时涉及版权、供应链输入安全和确定性渲染，不能仅按可加载文件处理。
  decision: ADOPTED_IN_CONVERSATION
  implementation: FORMAL_ROADMAP_ADOPTED_NOT_IMPLEMENTED
  persistence: MERGED_INTO_ADOPTED_TEXT_AND_RIGHTS_ROADMAP
  evidence: ROUTE_AND_SECURITY_DECISIONS_NO_IMPLEMENTATION_EVIDENCE
  confidence: high
  depends_on:
  - CPG-012
  - CPG-014
  refines:
  - CPG-012
- id: CPG-014
  semantic_digest: f54d6c1295e956c9
  topic: 共享文本引擎与 raster 权威
  rule: 优先 POC WASM-capable shared Text Engine：前端采用 CanvasKit/Skia、后端采用 Skia，GPU API 仅作为 raster/composition backend，DOM 不作为 canonical raster authority。
  why: 共享布局与 shaping 语义可降低预览和最终渲染漂移，同时保留不同 GPU 后端的替换空间。
  decision: ADOPTED_IN_CONVERSATION
  implementation: POC_PRIORITIZED_NOT_REVERIFIED
  persistence: CONVERSATION_PRODUCT_UX_DECISION
  evidence: NO_CROSS_RUNTIME_CONFORMANCE_VERIFICATION
  confidence: high
  depends_on:
  - CPG-019
- id: CPG-015
  semantic_digest: fa15e9454732c16f
  topic: 插件信任、隔离与可复现性
  rule: 插件权限默认拒绝，并按来源、信任级别、生效位置、数据敏感性和性能选择 SPI/Spring、PF4J、独立 Worker、容器、Wasm、MCP 或前端沙箱；PF4J 仅是 trusted JVM load/lifecycle/discovery 隔离候选，不可信 Marketplace 代码默认 out-of-process。Render
    Plan 必须锁定插件版本、实现摘要、配置和运行镜像，安装、启用、禁用、删除及历史版本并存分离治理。Plugin Registry V1 只含 descriptor、validation、registry、health 与 deterministic matching，Runtime V2 前另行冻结信任边界。
  why: 插件加载机制不等于安全边界；最小权限、隔离与版本锁定共同保证权限不继承升级、历史输出可复现且 Registry 不越权执行。
  decision: RETAINED
  implementation: DESIGN_AND_V1_SCOPE_RETAINED_RUNTIME_ISOLATION_NOT_IMPLEMENTED_OR_REVERIFIED
  persistence: CONSOLIDATED_PLUGIN_SECURITY_POLICY
  evidence: DESIGN_AND_SCOPE_STATEMENTS_NO_RUNTIME_SECURITY_VERIFICATION
  confidence: medium_high
  depends_on:
  - CPG-011
  - CPG-019
- id: CPG-016
  semantic_digest: 7434ea9786d0cb42
  topic: 不可信任务包导入
  rule: ZIP、文件组、manifest 与 prompt 一律视为不可信 Application/Ingest 输入；必须验证路径穿越、symlink、文件数、解压尺寸、压缩比、类型和 schema，并禁止执行包内任意脚本、shell、FFmpeg 或 Python。
  why: 任务包同时具有归档炸弹、路径逃逸、内容欺骗和任意代码执行风险，必须在进入应用层前 fail closed。
  decision: ADOPTED_IN_CONVERSATION
  implementation: SECURITY_REQUIREMENTS_ADOPTED_IMPLEMENTATION_NOT_REVERIFIED
  persistence: CONVERSATION_SECURITY_DECISION
  evidence: NO_INGEST_SECURITY_TEST_EVIDENCE
  confidence: high
  depends_on:
  - CPG-011
- id: CPG-017
  semantic_digest: efb5b57cc904a53d
  topic: Contract-first Frontend 与 UX-level IR
  rule: 前端建立 InteractionIntent/ProductAction 作为 UX-level IR：语义动作 lower 到唯一后端 Operation，纯 presentation/local ephemeral 动作留在前端。前端可基于 application-facing contracts 和
    mock 先行迭代，但 canonical semantics、authorization、semantic diff/merge 与真实 availability 由后端决定；i18n 仅属 presentation foundation，canonical enums、IDs、operation keys 与
    locale 无关，并区分 UI locale、内容语言和 Agent 对话语言。
  why: 允许 UX 并行开发而不伪造后端权威；稳定的 typed action 与 reason code 也避免本地化文本进入协议语义。
  decision: PROPOSED
  implementation: CORE_FRONTEND_CONTRACT_DIRECTION_ADOPTED_I18N_FOUNDATION_PROPOSED
  persistence: CONSOLIDATED_FRONTEND_ARCHITECTURE
  evidence: CONVERSATION_DECISIONS_NO_CONTRACT_OR_LOCALIZATION_INTEGRATION_VERIFICATION
  confidence: high
  depends_on:
  - CPG-002
  - CPG-011
  refines:
  - CPG-002
- id: CPG-018
  semantic_digest: 7d99ac5951701039
  topic: Typed Patch 与 Semantic Extension 治理
  rule: Patch Engine 保持有限、确定、强类型、可验证且原子；规划、全局优化和后端选择在外层完成并产出 Typed Patch。普通插件只能实现既有 Capability；引入新 canonical semantics 必须通过更高等级治理，并提供确定性序列化、验证、等价、diff、merge、迁移和 conformance
    契约。
  why: 将不可控规划与语义扩展挡在安全执行内核之外，才能维持版本、合并和重放的一致性。
  decision: RETAINED
  implementation: PATCH_DIRECTION_ACCEPTED_EXTENSION_CONTRACT_NOT_IMPLEMENTATION_VERIFIED
  persistence: CONSOLIDATED_SEMANTIC_GOVERNANCE_BOUNDARY
  evidence: DESIGN_ACCEPTANCE_EXPLICITLY_NOT_FULLY_VERIFIED
  confidence: high
  depends_on:
  - CPG-019
  - CPG-020
- id: CPG-019
  semantic_digest: c179bb0de9bfd9d7
  topic: 验证层级、参考实现与形式化一致性
  rule: 证据采用分层模型：声明 < 类型/静态检查 < 单元与属性测试 < 集成/端到端与 conformance < 随机/差分验证 < 模型检查 < 形式证明。Graph Algorithms V1 作为结构验证基线；Java 可承载生产接口与参考实现，高风险优化实现必须与参考/形式模型做差分和一致性验证。形式化验证聚焦共享语义与运行时
    invariant，semantic rewrite 受机器可检查 law 约束，未证明时 fail closed，并按 authority 风险逐级提高证明要求。
  why: 证据强度必须与权威和风险匹配；参考实现、可执行 conformance 与形式模型组合可防止高性能实现静默改变语义。
  decision: RETAINED
  implementation: GRAPH_V1_CLAIMED_ACCEPTED_EVIDENCE_LADDER_ADOPTED_FULL_FORMAL_STACK_NOT_REVERIFIED
  persistence: CONSOLIDATED_VERIFICATION_GOVERNANCE
  evidence: DECISION_EVIDENCE_PRESENT_RUNTIME_AND_FORMAL_PROOFS_NOT_EXECUTED_IN_THIS_TASK
  confidence: high
  depends_on:
  - CPG-020
- id: CPG-020
  semantic_digest: f8e1dc0be5bc2d37
  topic: 决策状态、证据与 Roadmap 版本治理
  rule: 'Roadmap #1–#28 的编号与版本身份保持稳定，不新增 #29；新增能力进入 post-#19 cross-cutting foundations、Application、Product/UX 或 Studio track。决策、实现、持久化和证据状态必须分别记录：Roadmap #21 保持关闭且标记
    canonical integration，#22 Decision Recovery 仅为已授权、尚未开始，不得把授权、历史工时或执行声明升级为实现完成或验证证据。'
  why: 稳定编号和分离状态可阻止路线反复重编号，也避免把讨论采纳、执行宣称和可复验证据混为一谈。
  decision: RETAINED
  implementation: ROADMAP_21_CLAIMED_CLOSED_ROADMAP_22_AUTHORIZED_NOT_STARTED
  persistence: CANONICAL_ROADMAP_GOVERNANCE_DIRECTION
  evidence: STATUS_ASSERTIONS_PRESERVED_NO_CURRENT_IMPLEMENTATION_REVERIFICATION
  confidence: high
- id: CPG-021
  semantic_digest: 2eb90db07f383547
  topic: 路线图顺序与 bounded integration 窗口
  rule: 媒体路线在 Patch Engine 最终验证后先完成 Media Semantics/Invariant Charter，再实施基础转场/特效、Diff/Patch/API 和后端编译，之后进入 Three-way Merge；OpenCue 不必等待全仓治理完成，但仅在 EP06 关闭后优先推进 EP25，再启动
    bounded integration POC，其他治理 lane 并行。
  why: 先稳定媒体语义可避免 Merge 二次重构；以明确 gate 开放 bounded POC 可平衡治理完备度与集成学习。
  decision: PROPOSED
  implementation: ROADMAP_SEQUENCE_AND_POC_WINDOW_PROPOSED
  persistence: CONSOLIDATED_ROADMAP_PROPOSAL
  evidence: SEQUENCE_AND_ESTIMATE_CLAIMS_NOT_IMPLEMENTATION_VERIFIED
  confidence: high
  depends_on:
  - CPG-018
  - CPG-019
  - CPG-020
- id: CPG-022
  semantic_digest: 15591532a4631fe1
  topic: 架构与依赖健康自动守卫
  rule: 依赖方向固定为 API → Application/Orchestrator → Kernel Ports/SPI → Adapters，以构造器注入、Spring Modulith 与 ArchUnit 阻断循环和越层依赖；治理接受后建立依赖健康基线，组合自动更新、版本审计、漏洞扫描、SBOM、Dependency
    Review 与 Gradle Dependency Verification。
  why: 结构和供应链约束应转化为持续、可执行的机器门禁，而不是依靠约定或隐藏循环。
  decision: PROPOSED
  implementation: ARCHITECTURE_GUARDS_PLANNED_DEPENDENCY_HEALTH_PROPOSED
  persistence: CONSOLIDATED_ENGINEERING_GOVERNANCE_WORK_PACKAGE
  evidence: GUARDS_AND_TOOLCHAIN_NOT_RUN_IN_THIS_TASK
  confidence: medium
  depends_on:
  - CPG-019
  - CPG-020
- id: CPG-023
  semantic_digest: 5e1a552408d47f7e
  topic: Agent 与生成式后端的非权威定位
  rule: Embabel 仅候选用于核心媒体运行时的只读、受控目标规划，AgentScope 用于外部多 Agent 工程与实验；ComfyUI 可作为可替换生成式媒体执行后端。三者均不得替代图算法、Hermes 治理、Workflow、Timeline 或模型语义权威。
  why: 规划框架、多 Agent 工具和节点式生成后端各有适用范围，但都必须被既有权威、授权与验证边界包围。
  decision: PENDING
  implementation: SPIKES_AND_BACKEND_EVALUATION_PROPOSED_NOT_RUN
  persistence: CONSOLIDATED_PENDING_TECHNOLOGY_POSITIONING
  evidence: COMPARATIVE_ASSESSMENT_ONLY
  confidence: medium_high
  depends_on:
  - CPG-011
  - CPG-018
- id: CPG-024
  semantic_digest: e0c4d1b3c5061904
  topic: Golden Story 验证边界
  rule: Golden Story 可作为端到端创作验证场景，但具体故事内容不是平台架构规范，也不能单独证明通用产品能力。
  why: 代表性故事适合验证跨层闭环，但将样例内容固化为架构会过拟合单一叙事。
  decision: RETAINED
  implementation: VALIDATION_SCENARIO_RETAINED_NO_CURRENT_RUN
  persistence: GOVERNANCE_BOUNDARY_RETAINED
  evidence: NO_END_TO_END_GOLDEN_STORY_RESULT_IN_THIS_TASK
  confidence: high
  depends_on:
  - CPG-005
  - CPG-019
- id: CPG-025
  semantic_digest: 87ab5dd65c46776a
  topic: 非可信贡献算力与 GPU 资源治理
  rule: 普通用户贡献算力一律视为非可信执行，必须受隐私、隔离、结果验证和任务适配约束；本地单张 8GB NVIDIA GPU 同时只运行一个重型 GPU 服务，任务结束主动卸载模型并释放显存；激励近期仅使用 credits/accounting，不采用 token/crypto。
  why: 贡献节点扩大信任与数据暴露面，本地显存又是硬资源约束，因此需先用保守调度、安全门禁和简单记账建立可验证边界。
  decision: PROPOSED
  implementation: SECURITY_AND_RESOURCE_POLICIES_PROPOSED_NOT_VERIFIED
  persistence: CONSOLIDATED_COMPUTE_GOVERNANCE_PROPOSAL
  evidence: NO_SANDBOX_RESULT_VALIDATION_OR_GPU_RUNTIME_TEST
  confidence: high
  depends_on:
  - CPG-009
  - CPG-011
  - CPG-019
- id: CPG-026
  semantic_digest: e6bc6001240a055c
  topic: 生产能力选择、成本与验收合同
  rule: 产品化生产链采用 capability support envelope、多目标 implementation selection、成本 estimate-reserve-reconcile、typed stage products、production replay 与 deliverable acceptance；不采纳
    Agent 直接充当 orchestrator 或业务权威的模型。
  why: 显式能力边界、成本闭环、阶段产物和交付验收可将生成式生产从一次性调用提升为可计划、可回放、可核验的产品流程。
  decision: ADOPTED_IN_CONVERSATION
  implementation: LEARNINGS_ADOPTED_PRODUCTION_CONTRACTS_NOT_REVERIFIED
  persistence: CONSOLIDATED_PRODUCT_PRODUCTION_DIRECTION
  evidence: CONVERSATION_DECISION_NO_END_TO_END_PRODUCTION_REPLAY_OR_ACCEPTANCE_TEST
  confidence: high
  depends_on:
  - CPG-004
  - CPG-009
  - CPG-019
  refines:
  - CPG-004
- id: DATA-CAN-001
  semantic_digest: 31bab49eb0a180ba
  topic: Canonical Artifact、OpenDAL 与 NiFi 分层
  rule: Artifact/Storage 保持 canonical media data-plane authority；OpenDAL 是 StoragePort 下的访问机制，类型不应成为业务 authority；NiFi 位于其上作为可靠数据流/集成执行层；JuiceFS/Alluxio 仅是缓存或分布式数据层候选，不拥有
    Artifact identity。
  why: 将身份、命名、提交和保留语义与存储 SDK、缓存和数据流产品解耦。
  decision: ADOPTED_IN_CONVERSATION
  implementation: OPENDAL_INTRODUCTION_CLAIMED_NOT_VERIFIED; NIFI_AND_CACHE_CANDIDATES_NOT_IMPLEMENTED
  persistence: EXPLICITLY_ADOPTED_CONVERSATION_BASELINE
  evidence: SOURCE_AND_ADOPTION_RECEIPT_NO_CODE_VERIFICATION
  confidence: high
- id: DATA-CAN-002
  semantic_digest: 3f6c50bcbdff8b65
  topic: OpenDAL 首选适配器提案
  rule: 提议将 OpenDAL 作为首选 Storage Data-Plane Adapter，且其类型不得传播出 Adapter；Artifact 命名空间、提交、复制、保留和交付语义由平台定义。
  why: 在不泄漏第三方 SDK 的前提下统一多后端存储访问。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SELECTION_PROPOSAL_NO_POC
  confidence: high
  refines:
  - DATA-CAN-001
- id: DOM-AI-001
  semantic_digest: c7593e121d5a1b24
  topic: AI/CV 权威与生成提交
  rule: AI/CV 只能 Observe、Analyze、Propose/Plan 和 Generate；模型输出先规范化为平台定义的 ObservationSet 或 OperationPlanProposal，不能直接修改 Timeline。生成媒体必须先物化为带 provenance、digest-pinned
    的 immutable Artifact，再由独立 typed Operation 预览、授权并纳入 canonical state；ASR observation 不等于 canonical Caption。
  why: 把概率性推理和生成与确定性 canonical commitment 分开，可容纳非确定 Provider 而不放弃审计和提交完整性。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-ARTIFACT-001
  semantic_digest: 21a0c0604ed9d9c8
  topic: Artifact 身份、生命周期与保留
  rule: Artifact 的逻辑身份、内容摘要、物理 Replica 和交付地址分离；正式 Blob 不可变，并经 staging、校验和提交后变为 AVAILABLE。严格区分 immutable Artifact、durable Observation 与 rebuildable Cache；Retention
    是策略而非 identity，历史 Revision 直接 pin 的 Artifact 必须防 GC。
  why: 内容寻址身份、物理位置和保留策略分离，可支持复制、迁移、重建和历史可复现性。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: DOM-AUTHORITY-001
  semantic_digest: 229448f924a2c8df
  topic: Canonical 写入权威
  rule: 每类 canonical 对象只能有一个写入所有者；其他服务、Provider 与集成只能经该 authority 的受控接口提出或执行变更。
  why: 单一写入权威可避免多服务直接写同一状态造成竞态、漂移和责任边界不清。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-COMPOSITION-001
  semantic_digest: 32c81fe2f3bf161f
  topic: Canonical 几何与像素权威
  rule: Timeline 使用连续、非 pixel-indexed、fixed-point 的 canonical composition geometry，并显式定义视觉层序与输出参与；统一 RenderPlan/RenderGraph、shader、color 和 sampling contract，Preview
    仅为 conformant projection，Backend Final Render 才是 authoritative pixel output。
  why: 将几何和渲染语义固定在 canonical 层，同时把像素执行留给后端，可支持跨端一致性而不绑定具体图形 API。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-CORE-001
  semantic_digest: 55ff1dfe61663d60
  topic: 媒体领域权威与统一内核
  rule: Product、TimelineRevision、Artifact、StorageReference 等 canonical 对象保持职责分离；Timeline 只拥有持久时序组合，Workflow 拥有过程。所有产品面共享同一媒体语义内核，套餐差异仅由能力、权限、策略、配额和产品表面表达。
  why: 稳定的领域边界与共享内核可避免物理存储、工作流或商业分层侵入媒体语义。
  decision: RETAINED
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-EVENT-001
  semantic_digest: e6f798e84eb91d48
  topic: Typed Event 边界
  rule: Typed Event 只表示 canonical state transition notification 或 integration fact，不是唯一事实来源；Canonical state 与 Revision DAG 保持 authority。
  why: 事件作为通知而非事实唯一存储，可避免在尚无必要时引入完整 event sourcing 的一致性和回放复杂度。
  decision: RETAINED
  implementation: PARTIAL_OR_CLAIMED_NOT_VERIFIED
  persistence: REGISTERED_OR_FROZEN_IN_SOURCE
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-FONT-001
  semantic_digest: d8a2fedc1cb33a6f
  topic: Canonical 字体与文本确定性
  rule: 最终视觉内容必须 pin 精确 FontAsset、face、fallback、shaping 和 resolved GlyphRun；系统字体只用于发现。文本的 language、script、direction 独立并按 range 建模，保持逻辑 Unicode 顺序；fallback 在 shaping-safe
    cluster 上执行。Variable font identity 包含内容摘要、FaceIndex 和精确 design-space axes，AUTO 值提交前解析；subset/atlas 仅为受许可约束的派生物。跨端一致性分 semantic、layout、pixel 三层，最终渲染可使用 pinned
    reference raster path。
  why: 固定字体内容、解析结果与 shaping 边界，可避免宿主环境和 fallback 差异破坏历史排版与像素结果。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-INTEGRITY-001
  semantic_digest: 3242dac175301730
  topic: 完整性 containment 与修复
  rule: 完整性事件按 severity、propagation risk、blast radius 和 containment 分维度处置，只阻断可能传播或产生已知非法 canonical state 的操作。修复对当前 authoritative head 做 forward correction；必要时从 repaired
    base 语义重放后续 Operation intent，无法确定则人工恢复，绝不静默改写旧 Revision 或强制移动 active ref。
  why: 风险比例化阻断与前向修复可同时限制故障传播、维持无关能力，并保护不可变历史和审计链。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-OPERATION-001
  semantic_digest: 7128345c2ed804b5
  topic: Canonical Operation 提交事务
  rule: 所有 canonical media mutation 必须沿 REQUEST → RESOLVE/PREPARE → exact OperationPlan+digest → VALIDATE → PREVIEW → AUTHORIZE → ATOMIC APPLY → NEW REVISION 的单一提交路径；绑定
    baseRevisionId/baseContentHash，stale base fail closed。参数区分 target、semantic parameters、resolution inputs 与 execution requirements，禁止 Map<String,Object> 或直接字段修改成为权威。
  why: 统一且精确的事务边界可关闭旁路写入，保证并发安全、授权、审计和原子提交。
  decision: RETAINED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-OPERATION-002
  semantic_digest: 924e3cb26af4eaa2
  topic: Operation、Capability 与 Recipe 公共语义
  rule: 业务功能、Workflow、Template、Agent 和 Plugin 只依赖 canonical typed Operations；Operation 定义类型、effect、依赖和作用域，Recipe 是高阶组合而不能重定义 Operation。Capability discovery 按 principal
    过滤，并将能力存在、entitlement、permission、quota 分离；授权感知 target/scope。
  why: 稳定的公开操作面与分离的能力政策可形成复杂度防火墙，避免编排层自建媒体语义或直接改字段。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: medium
- id: DOM-PUBLICATION-001
  semantic_digest: 3beafd9a297e6fe9
  topic: 外部发布与指标观测
  rule: 发布建模为 OutputArtifact → PublicationAttempt → ExternalPublication；性能数据按 observedAt 保存为 ObservationSet，不覆盖历史计数。YouTube、TikTok 等原始指标保留来源语义，跨平台归一指标必须是显式版本化派生。
  why: 区分产物、尝试、外部对象和时序观测，可保留失败历史与来源差异，避免伪造可比指标。
  decision: PROPOSED
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: DOM-RELATIONSHIP-001
  semantic_digest: 7b5e160315c6d73d
  topic: 语义关系与派生传播
  rule: 建立 typed semantic Relationship 与 selection/scope resolution，但不采用万能 RDF 或泛化图作为权威。结构性变更通过 Relationship+OperationPlan 协调传播；多语种等语义派生使用 authoritative source semantic
    units、N:M alignment、增量失效和局部再生成，人工修改的下游进入 DIVERGED 且禁止自动覆盖。
  why: 关系机制只承载跨域协调，各领域继续拥有具体语义，可避免一对一镜像和自动覆盖用户修改。
  decision: PROPOSED
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: DOM-RELEASE-001
  semantic_digest: d408bc74bc6a1845
  topic: 版本解析、灰度与 pinning
  rule: Version、Build Identity、Release Channel 与 Rollout Assignment 必须分开；灰度只在兼容候选中选择。OperationPlan 或 WorkflowRun 一旦 resolve，必须 pin 精确 implementation、plugin、model、recipe/workflow
    revision 和必要 runtime；上游更新只产生 outdated/upgrade proposal，不自动重写已 pin 下游。
  why: 解析后固定全部实现身份，可让同一提交可追踪、可重放，并避免运行中追随 latest 或上游变更。
  decision: ADOPTED_IN_CONVERSATION
  implementation: UNKNOWN
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-REVISION-001
  semantic_digest: ec4a740953b6f988
  topic: Creative Revision Graph
  rule: 项目级 Creative Revision Graph 共享不可变 Revision DAG；通用层仅提供 DAG、ancestor、merge-base、head 等 mechanics，各领域拥有 ChangeSet、Diff、冲突和 semantic merge。Timeline Git 保留图机制但升级
    source binding、serialization/hash、equality/diff/merge/validation；.blend 和二进制只作为 Artifact，用户界面默认呈现创作替代方案而非原始 DAG。
  why: 复用成熟图机制并保留领域合并语义，可扩展版本能力而不让后端、Blender 或通用图抽象接管 canonical model。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: DOM-SCHEMA-001
  semantic_digest: 7c2a08137948d3ed
  topic: Canonical Schema 与版本体系
  rule: 历史 immutable revision 保留原始 canonical bytes、格式版本和 hash；旧格式由 versioned reader/projector 读取，语义迁移必须显式产生新 Revision。软件发行使用 EPOCH.RELEASE.PATCH，canonical、capability、operation
    和 API contract 使用 major.minor，immutable state 使用 RevisionId，三类版本严格分离。
  why: 不可变历史与分层版本标识可保持哈希、审计和兼容性，避免升级时原地改写历史或混用版本语义。
  decision: RETAINED
  implementation: DESIGN_OR_PLANNED_NOT_VERIFIED
  persistence: REGISTERED_OR_FROZEN_IN_SOURCE
  evidence: SOURCE_ONLY
  confidence: high
- id: DOM-SUBTITLE-001
  semantic_digest: 9aaef22caf635061
  topic: 字幕 canonical authority 与母版
  rule: SubtitleTrack/TimedTextTrack 是独立 canonical authority，Caption content、presentation、delivery 和 Timeline composition 分离；Timeline pin 精确不可变版本并可引用多轨。Canonical
    TimedText 目标为 ASS 语义超集，ASS/WebVTT/TTML 仅为兼容目标，导出需 capability negotiation 且不得静默有损；字幕证据层与语义/设计母版分离，交付格式只从母版生成。
  why: 独立、版本化的字幕权威可支持多语言、复杂样式和多格式交付，同时避免 Timeline 或某个交换格式吞并字幕语义。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: medium
- id: DOM-TEMPLATE-001
  semantic_digest: 1b2845f5896506fd
  topic: Template 语义与边界
  rule: Template 是版本化、可复用、可参数化、可验证和可编译的语义组合；参数必须 typed，可组合 Timeline、Caption、Effect、Workflow 等 authorities。应用模板只能生成 OperationPlan/Typed Patch，不直接写 Timeline，也不保存后端命令、存储操作或
    Provider 选择为权威数据。
  why: 把模板限定为 canonical intent 的参数化蓝图，可扩展到多媒体组合，同时不绕过能力、权限和执行分层。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: high
- id: DOM-TIME-001
  semantic_digest: b688c8630c1ffd50
  topic: 精确时间与编辑操作
  rule: Canonical Timeline 使用精确有理数或 ticks/timeScale 表示，并显式区分 timeline、source、frame、sample 与 VFR/PTS 时间域；placement 保持 absolute/exact，Ripple、Insert、Lift、Extract、Slip、Slide、Roll
    等属于 operation layer。任何时长变化必须由显式 Patch 表达，普通参数效果不隐式改变作品时长。
  why: 精确时间和显式时长变更可避免浮点漂移、后端隐式决策，并使 Preview、Diff 与 Merge 可重复。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: medium
- id: DOM-TIMELINE-001
  semantic_digest: ef97ac5905da63ba
  topic: Canonical Timeline 语义模型
  rule: Timeline 是类型化、有属性、有序、时间化的多关系模型，分别验证容纳、依赖、引用、同步和 Revision 关系；它拥有 composition placement、视觉合成顺序、输出参与状态与 provider-neutral composition space，但不吞并 Effect、Transition、Automation
    或 TimedText 的局部语义。
  why: 把作品结构与各局部领域语义分权，可保持 Timeline 可验证且避免万能 Node/Edge 或单一 DAG 模型。
  decision: RETAINED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY_NO_IMPLEMENTATION_VERIFICATION
  confidence: high
- id: EXEC-CAN-001
  semantic_digest: 8e56444acd3a3729
  topic: 受约束、确定性的执行 DAG
  rule: Render DAG 只能由平台编译器生成，节点类型有限、无环、有界并可确定性拓扑排序；用户、模板和插件不得提交任意执行图。
  why: 限制组合空间并保持可验证、可重放的执行语义。
  decision: ADOPTED_IN_CONVERSATION
  implementation: ARCHITECTURE_TASK_PROPOSED
  persistence: CONVERSATION_ONLY
  evidence: RULES_NOT_ENFORCED_OR_VERIFIED
  confidence: high
- id: EXEC-CAN-002
  semantic_digest: 9ae321614eae2bf3
  topic: 逻辑计划、物理计划与版本固定
  rule: Logical RenderPlan 保持确定、后端中立；Physical Execution Plan 固定 capability、Recipe、Provider implementation、定价和输入资产版本，并可在硬约束后按资源、成本、质量和延迟选择实现；改选实现产生新 plan revision
    与 attempt。
  why: 隔离 canonical intent 与运行时选择，使选择可审计且不发生静默 fallback。
  decision: PROPOSED
  implementation: FUTURE_DESIGN
  persistence: CONSOLIDATED_FROM_CONVERSATION
  evidence: MIXED_ADOPTED_FOUNDATION_AND_PROPOSED_REVISION_MODEL
  confidence: high
- id: EXEC-CAN-003
  semantic_digest: 47bb2c795901dd21
  topic: Artifact DAG 延后
  rule: Artifact DAG 保持 deferred，默认不进入 ProviderBinding、RenderExecution、Patch、Merge 或回滚主路径。
  why: 避免将尚未验证的 Artifact 图模型变成近期执行内核前提。
  decision: RETAINED
  implementation: DEFERRED_DISABLED_BY_DEFAULT
  persistence: REFERENCED_AS_FROZEN_BOUNDARY
  evidence: DESIGN_CLAIM_ONLY
  confidence: high
- id: EXEC-CAN-004
  semantic_digest: 78021592cd1a74a0
  topic: 不可变执行尝试与 fenced observation
  rule: ExecutionJob 是稳定逻辑身份，ExecutionAttempt/RenderJob 表示不可变尝试；重试创建新尝试并 fence 旧 generation，可重绑定 Environment，但不复活 FAILED 记录或承诺进程现场迁移；同步、callback、poll、stream 统一为按
    attempt/generation fencing 的 observation。
  why: 保证重试、远程回调和环境切换下的状态单调性与审计性。
  decision: ADOPTED_IN_CONVERSATION
  implementation: TARGET_PARTIALLY_DESCRIBED_NOT_VERIFIED; CURRENT_DRIFT_POSSIBLE
  persistence: FROZEN_CONVERSATION_BASELINE
  evidence: EXPLICIT_ADOPTION_PLUS_UNVERIFIED_CURRENT_BEHAVIOR
  confidence: high
- id: EXEC-CAN-005
  semantic_digest: c2dba5c75e4c8e35
  topic: Core、Provider 与 Worker authority 边界
  rule: Core 拥有 canonical semantics、durable state、planning、orchestration 和 lifecycle；Provider 是有界能力实现，只校验输入、执行、报告并返回标准 candidate；Worker 消费 typed immutable contract
    与 ArtifactRef，不能直接修改 RenderJob、Product、Artifact 或 canonical persistence。
  why: 集中状态所有权并让 FFmpeg、OpenCV、Blender、Houdini 等实现可替换。
  decision: RETAINED
  implementation: BOUNDARY_HARDENING_REQUIRED; NOT_CODE_VERIFIED
  persistence: FROZEN_DESIGN_DIRECTION
  evidence: DESIGN_AND_EXPLICIT_ADOPTION_CLAIMS
  confidence: high
- id: EXEC-CAN-006
  semantic_digest: 5557a9e9a8002426
  topic: Typed capability 与插件贡献模型
  rule: 上层依赖稳定、可发现、可版本化的 typed Capability，而非插件名；Plugin 只是可安装实现包，Provider、ExecutionBackend、IntegrationAdapter 是不同 contribution，第一方实现同样插件化；Registry/插件不得直接执行或修改 canonical
    state，platform-plugins 仅作逻辑 namespace，叶模块才是构建部署单元。
  why: 在保留多语言实现自由的同时维持单一语义 authority 和可组合部署边界。
  decision: PROPOSED
  implementation: DESIGN_ONLY_OR_PLANNED; CONTROL_PLANE_P1_ONLY
  persistence: FROZEN_CONVERSATION_BASELINE
  evidence: MIXED_EXPLICIT_ADOPTION_AND_PROPOSED_PLUGIN_PLANE
  confidence: high
- id: EXEC-CAN-007
  semantic_digest: 64de8c23b4aba048
  topic: Provider、ExecutionBackend、Worker 与 Placement 分工
  rule: Provider 定义能力实现，ExecutionBackend 定义执行 mechanics 与 placement delegation，WorkerRuntime 是实际执行端点，Placement Authority 决定放置；平台拥有 task attempt、generation 和 completion，后端内部
    retry 不等于平台 Attempt；planner 可将最终渲染分区到多个 pinned providers。
  why: 消除 backend/provider/worker 混用并明确跨实现执行的状态所有权。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_ONLY_NOT_IMPLEMENTED
  persistence: FROZEN_CONVERSATION_BASELINE
  evidence: EXPLICIT_FREEZE_AND_ADOPTION_BLOCKS
  confidence: high
- id: EXEC-CAN-008
  semantic_digest: 317375875a4b62ed
  topic: 单一 Placement Authority 与 scope
  rule: 一个 workload 同时只能有一个 active Placement Authority：平台先选择 ExecutionBackend，再由其按 PLATFORM_MANAGED、BACKEND_DELEGATED 或 REMOTE_PROVIDER_MANAGED scope 完成内部 placement；委托后端可隐藏内部
    load 与 placement。
  why: 防止平台调度器与外部后端对同一工作负载发生双重放置。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_ONLY_NOT_STARTED
  persistence: AUTHORITATIVE_HANDOFF_ADDENDUM
  evidence: EXPLICIT_LAW_BLOCK_AND_FORMAL_ADOPTION
  confidence: high
  depends_on:
  - EXEC-CAN-007
- id: EXEC-CAN-009
  semantic_digest: 15457e87b96a5eb3
  topic: Worker 形态与服务拆分
  rule: Worker 类型由生命周期、管理方式、信任、资源和位置等正交维度组合；物理 Worker 按资源能力与隔离需求形成逻辑池，多能力 Worker 正常；服务拆分依据 runtime dependency、资源、安全、故障域和 scaling profile，而不是 capability 枚举。
  why: 避免按产品功能或单 capability 形成僵硬微服务拓扑。
  decision: PROPOSED
  implementation: PARTIALLY_IMPLEMENTED_UNVERIFIED; SERVICE_SPLIT_NOT_IMPLEMENTED
  persistence: AUTHORITATIVE_HANDOFF
  evidence: MIXED_ADOPTED_MODEL_RETAINED_LIFECYCLE_AND_PROPOSED_SPLIT_RULE
  confidence: high
- id: EXEC-CAN-010
  semantic_digest: c16615a35199fcbd
  topic: Native Worker 拉取、租约与准入
  rule: 通用 Native Worker Fabric 使用 worker-initiated pull、central matching、原子 lease、reservation backing，并在本地 admission 时 fail closed。
  why: 在并发领取和资源竞争下保持唯一派发与资源承诺。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_STARTED
  persistence: AUTHORITATIVE_HANDOFF_ADDENDUM
  evidence: EXPLICIT_FORMAL_ADOPTION
  confidence: high
  depends_on:
  - EXEC-CAN-012
- id: EXEC-CAN-011
  semantic_digest: bf4bbd9532d6e48f
  topic: PhysicalHost、资源真值与预留
  rule: PhysicalHost 表示可承载多个隔离 ProviderRuntime 的资源容量；资源模型严格区分 CAPACITY、RESERVED、OBSERVED，Resource Ledger/Reservation 是调度承诺 authority，采用 reservation first、telemetry
    second；设备按身份计量，GPU 初期优先独占预留。
  why: 避免从瞬时 CPU load 推断设备容量，并让调度承诺可核算、可拒绝。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PARTIALLY_IMPLEMENTED_WITH_KNOWN_HOST_BINDING_IDENTITY_FRESHNESS_GAPS
  persistence: EPOCH_3_ENTRY_REQUIREMENT_AND_AUTHORITATIVE_HANDOFF
  evidence: EXPLICIT_ADOPTION_AND_GAP_ANALYSIS
  confidence: high
- id: EXEC-CAN-012
  semantic_digest: 14c6d1d1bf9e5d97
  topic: 弹性执行、drain 与调度范围
  rule: 执行架构采用局部加固而非重写；先冻结统一 ExecutionProvider 与 Artifact Staging 合同，以 Local/Container 为参考实现，再评估 Kubernetes、OpenCue 和单一云 Batch；统一 Fabric 先覆盖 Worker lifecycle、join/leave、lease/heartbeat
    与 bounded dispatch，完整动态 scaling/placement policy 后置；非渲染 scheduler 暂不冻结，scale-in 必须先 drain。
  why: 先稳定执行合同与生命周期，再选择调度产品和扩展全局策略。
  decision: ADOPTED_IN_CONVERSATION
  implementation: PLANNED_NOT_VERIFIED
  persistence: FROZEN_CONVERSATION_BASELINE
  evidence: EXPLICIT_ADOPTION_AND_SCOPE_DIRECTIVES
  confidence: high
- id: EXEC-CAN-013
  semantic_digest: 3d076237319818e0
  topic: OpenCue V1：通用/优先执行调度定位
  rule: OpenCue 曾被定位为 render-farm ExecutionProvider/Environment，并承担 farm scheduling/resource placement；该定位不得扩展为媒体 backend、workflow runtime、canonical authority 或万能
    scheduler。
  why: 记录 OpenCue V1 的边界及其后续收缩前的历史语义。
  decision: SUPERSEDED
  implementation: NOT_IN_CURRENT_RELEASE_SCOPE
  persistence: HISTORICAL_CONVERSATION_DECISION
  evidence: EXPLICIT_PRIOR_ADOPTION_SUPERSEDED_BY_LATER_HANDOFF
  confidence: high
- id: EXEC-CAN-014
  semantic_digest: 79c515652faae655
  topic: OpenCue V2：可选专业离线 farm backend
  rule: OpenCue 仅作为可选、专业、可替换的离线 farm ExecutionBackend，适用于 frame/DCC/大批量/license-aware/studio farm；它在该后端内决定 WHERE/WHEN，但不是通用 Worker Fabric 或 canonical execution authority。
  why: 把专业 farm placement 与平台 WHAT 语义、通用 Worker Fabric 和 Provider 内 HOW 分离。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_ONLY_UNKNOWN
  persistence: AUTHORITATIVE_HANDOFF_ADDENDUM
  evidence: EXPLICIT_CURRENT_POSITION_CORROBORATED_BY_LATER_ADOPTED_RECORDS
  confidence: high
  supersedes:
  - EXEC-CAN-013
- id: EXEC-CAN-015
  semantic_digest: c269fe2e9c19ab98
  topic: OpenCue adapter-first 集成与 Worker 能力探测
  rule: OpenCue 早期通过 adapter/sidecar 集成且不 fork；并提议用 render-toolchain manifest 与启动前 capability probe 控制 worker 能力注册，由 RenderPlan 的 ExecutionRequirement 匹配 eligible
    worker。
  why: 保持 OpenCue 可替换，并防止声明能力与真实工具链、codec、license 或运行环境漂移。
  decision: PROPOSED
  implementation: OPENCUE_MEDIA_WORKER_ENABLEMENT_V1_NOT_STARTED
  persistence: CONVERSATION_PROPOSAL_WITH_RETAINED_NO_FORK_DIRECTIVE
  evidence: EXPLICIT_NO_FORK_DIRECTIVE_PLUS_UNVERIFIED_CAPABILITY_PROPOSAL
  confidence: high
  depends_on:
  - EXEC-CAN-014
- id: EXEC-CAN-017
  semantic_digest: 68f2913935ffbd03
  topic: 合法性优先的 Provider 组合与 materialization
  rule: Provider 组合先按 compatibility graph 和硬约束求可行空间，未知语义 fail closed，再按成本、延迟、质量与 locality 优化；跨 Provider 默认使用显式、不可变、有类型的 Artifact materialization，同 Provider 可在约束检查后
    coalesce，但不得改变 PhysicalPlan 或语义身份。
  why: 确保优化不能创造合法性，并使跨执行 island 的数据边界可审计。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_ONLY_NOT_STARTED
  persistence: FROZEN_CONVERSATION_BASELINE
  evidence: MULTIPLE_EXPLICIT_ADOPTION_BLOCKS
  confidence: high
  depends_on:
  - EXEC-CAN-002
  - EXEC-CAN-007
- id: EXEC-CAN-018
  semantic_digest: dcfe2d3d0ec97d81
  topic: 图算法与 Solver SPI
  rule: JGraphT 用作图结构和基础算法内核；整体执行优化另设 Solver SPI，JGraphT 不单独承担完整商业调度优化。
  why: 分开图表示/基础算法与复杂约束求解器。
  decision: ADOPTED_IN_CONVERSATION
  implementation: JGRAPHT_ADOPTION_CLAIM_NOT_LIBRARY_VERIFIED; SOLVER_SPI_DESIGN_ONLY
  persistence: CONVERSATION_ONLY_WITH_PRIOR_ACCEPTANCE_CLAIM
  evidence: NO_LIBRARY_OR_TEST_VERIFICATION
  confidence: high
- id: EXEC-CAN-019
  semantic_digest: 77bf5d0741ee48e1
  topic: BMF bounded Provider-native graph POC
  rule: BMF 仅作为 bounded Provider-native graph POC；第一代 runtime 镜像提议优先 Debian + Nix，纯 NixOS/Nix OCI 后置；真实证据出现前不重写既有基础。
  why: 以隔离 POC 验证 Provider 内 HOW，同时控制运行时和架构迁移风险。
  decision: PROPOSED
  implementation: POC_AND_RUNTIME_IMAGE_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: ADOPTED_POC_BOUNDARY_PLUS_PROPOSED_IMAGE_SELECTION
  confidence: high
- id: EXEC-CAN-020
  semantic_digest: adb04007c2296c21
  topic: Caption content、presentation 与 delivery authority
  rule: Caption Content 是 canonical；Rendering 属于 Provider concern；Content、Presentation、Delivery 相互独立，标准可切换字幕不等于全保真动态字幕。
  why: 避免交付格式能力反向定义字幕内容或动态呈现语义。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_FROZEN_FUTURE_TIMELINE_V2_EFFECT_IR
  persistence: EXPLICITLY_ADOPTED
  evidence: EXPLICIT_ADOPTION_RECEIPT
  confidence: high
- id: EXEC-CAN-021
  semantic_digest: b6ec8b5652bbafa8
  topic: Audio authority、时间映射与效果分层
  rule: Media 拥有 source audio truth/analysis，Timeline 拥有 authored mix、time mapping、gain 与 intent，versioned effects 拥有 DSP semantics，Provider 执行，Delivery Profile 拥有响度与
    true-peak 约束；playback rate、pitch、formant 分离，composition primitives、effects 和 delivery processing 不合并为万能 AudioEffect。
  why: 保持音频创作语义、DSP 实现与交付规范各自可版本化。
  decision: ADOPTED_IN_CONVERSATION
  implementation: DESIGN_ONLY_NOT_IMPLEMENTED
  persistence: EXPLICITLY_FROZEN_IN_CONVERSATION
  evidence: EXPLICIT_ADOPTION_BLOCKS
  confidence: high
- id: EXEC-CAN-022
  semantic_digest: 53fa79d87fd6e1f2
  topic: TransitionInstance 转场模型
  rule: 提议将转场建模为连接两个时间实体的独立稳定 TransitionInstance；首版普通转场在切点校验显式 source handles，并在编译阶段生成重叠执行区间。
  why: 避免把转场退化为 Clip 字符串属性或未经校验的时间线重叠。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: CONVERSATION_ONLY
  evidence: DOMAIN_PROPOSAL_ONLY
  confidence: high
- id: EXEC-CAN-023
  semantic_digest: 508b90e2d978367b
  topic: 外部标准与行业系统采用政策
  rule: 外部标准和行业系统不自动成为平台 canonical authority；OTIO、OpenAssetIO、OpenUSD、AYON、OpenCue、Mesos、SheepIt、Flamenco、Exo 等按交换投影、原生标准资产、能力 Provider、互操作桥、执行环境或机制参考接入。
  why: 借用生态互操作能力而不让外部模型替代平台 canonical media semantics。
  decision: PROPOSED
  implementation: POLICY_AND_ADAPTERS_MOSTLY_NOT_IMPLEMENTED
  persistence: CONVERSATION_POLICY_PROPOSAL_AND_RETAINED_POSITIONING
  evidence: MIXED_RETAINED_PRINCIPLES_AND_UNADOPTED_POLICY_TABLE
  confidence: high
- id: EXEC-CAN-024
  semantic_digest: f8d78db14309042a
  topic: 不可信社区 Worker 安全模型
  rule: 社区 Worker 应按非可信执行处理，实施最小权限、输入隔离、结果验证和可撤销身份。
  why: 降低第三方算力读取敏感输入、伪造结果或长期滥用凭据的风险。
  decision: PROPOSED
  implementation: UNKNOWN_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
- id: EXEC-CAN-025
  semantic_digest: c4ac898e16d37993
  topic: Composite Resource 与跨场景一致性 Profile
  rule: 人物、场景等 Composite Resource 由稳定身份、版本化 facets 与显式依赖组成；跨场景一致性 Profile 只打包精确版本引用，不拥有 Entity、Scene、Timeline 或 Provider-specific semantics。
  why: 支持跨场景复用与一致性，同时避免不可控 God Object。
  decision: ADOPTED_IN_CONVERSATION
  implementation: ARCHITECTURE_ADOPTED_NOT_CODE_VERIFIED
  persistence: EXPLICITLY_ADOPTED_IN_CONVERSATION
  evidence: EXPLICIT_ADOPTION_AND_PRINCIPLE_LIST
  confidence: high
- id: EXEC-CAN-026
  semantic_digest: 399f115db71bd26f
  topic: Tolgee LocalizationProvider 选型
  rule: 选择 Tolgee 作为初始外部 TMS并优先使用 Tolgee Cloud；通过平台 LocalizationProvider/adapter 隔离，以便未来自托管或更换供应商。
  why: 快速获得 TMS 能力且不把供应商 API 变成领域 authority。
  decision: ADOPTED_IN_CONVERSATION
  implementation: ADOPTED_SELECTION_SCHEDULED_AFTER_WAVE_1_NOT_VERIFIED
  persistence: EXPLICITLY_ADOPTED_IN_CONVERSATION
  evidence: EXPLICIT_SERVICE_DEPLOYMENT_MODE_AND_STATUS
  confidence: high
- id: OPS-CAN-001
  semantic_digest: eac036f2677dad32
  topic: Recipe、Template 与 OperationPlan 分层
  rule: Recipe 是版本化、有类型、有限且声明式的 Operation 组合资产；Template 仅对 Recipe 做参数/default policy 绑定并生成 provider-neutral 的创作者意图，解析绑定后 lowering 为单请求 OperationPlan，不直接选择 Provider
    或执行存储操作；高级执行细节仅渐进披露。
  why: 将可复用创作资产、实例化意图和执行计划分开，避免模板或 Recipe 成为执行 authority，并避免产品界面泄漏 Provider 参数。
  decision: PROPOSED
  implementation: DESIGN_ONLY_MIXED_ADOPTION; TEMPLATE_GENERALIZATION_NOT_IMPLEMENTED
  persistence: CONSOLIDATED_FROM_CONVERSATION
  evidence: MIXED_EXPLICIT_ADOPTION_AND_UNADOPTED_TEMPLATE_PROPOSAL
  confidence: high
- id: OPS-CAN-002
  semantic_digest: 5d10595c856a1164
  topic: Recipe 代数与安全改写
  rule: Recipe sequence 仅在 typed composition 有定义时满足结合律并具有 typed identity；交换、并行和 interchange 必须证明语义独立及效果条件，未知条件 fail closed。
  why: 阻止未经证明的组合改写改变媒体语义或副作用顺序。
  decision: ADOPTED_IN_CONVERSATION
  implementation: NOT_STARTED
  persistence: CONVERSATION_BASELINE
  evidence: FORMAL_PRINCIPLE_BLOCK
  confidence: high
- id: OPS-CAN-003
  semantic_digest: 2f7e52497797ce67
  topic: 组合优化工具候选
  rule: OR-Tools 可作为组合优化候选；Calcite 主要作为 planner/rewrite 架构参考。
  why: 保留求解器与规划器参考方向，而不把候选工具误记为已选型。
  decision: PROPOSED
  implementation: UNKNOWN_NOT_VERIFIED
  persistence: CONVERSATION_ONLY
  evidence: SOURCE_ONLY
  confidence: high
  depends_on:
  - EXEC-CAN-018
- id: OPS-CAN-004
  semantic_digest: 6446c3172cb490ad
  topic: PVE 宿主、guest 与 pve-2 存储布局
  rule: PVE 宿主只承担 hypervisor；初始每台一 guest：pve-1 为 Infra Dokploy VM，pve-2 为 Intel Media Worker LXC；pve-2 淘汰 linear LVM 数据布局并迁移到 ZFS mirror。
  why: 隔离宿主职责并提高 pve-2 工作节点存储冗余。
  decision: ADOPTED_IN_CONVERSATION
  implementation: TARGET_CONFIGURATION_NOT_VERIFIED
  persistence: CONVERSATION_DECISION
  evidence: ADOPTION_CLAIMS_NO_LIVE_INFRA_VERIFICATION
  confidence: high
- id: OPS-CAN-005
  semantic_digest: 908e686ea785e314
  topic: Serverless 一致性与媒体数据路径
  rule: 采用 Serverless Function Conformance foundation，但当前不部署常驻自托管 FaaS；Lambda/Cloudflare Workers 等只承载符合时限和数据面约束的任务，大媒体通过对象存储直传和签名 URL；字幕等领域不感知具体云厂商。
  why: 统一函数执行约束，同时避免大媒体穿过短时函数或污染领域模型。
  decision: PROPOSED
  implementation: FOUNDATION_PLANNED_NOT_VERIFIED; MULTILINGUAL_EXECUTION_NOT_IMPLEMENTED
  persistence: CONVERSATION_BASELINE
  evidence: ADOPTED_FOUNDATION_AND_DATA_RULE_PLUS_PROPOSED_MULTILINGUAL_LAYERING
  confidence: medium
- id: OPS-CAN-006
  semantic_digest: 6a39397e582369de
  topic: 执行用量与成本账本
  rule: 每次外部或可计量执行应发出统一 UsageRecord；执行服务记录 usage 证据，成本账本结合价格快照计算成本。
  why: 分离不可变用量证据与随时间变化的价格计算。
  decision: PROPOSED
  implementation: MINIMUM_METERING_FOUNDATION_NOT_IMPLEMENTED
  persistence: REPEATED_FUTURE_QUEUE_PROPOSAL
  evidence: ARCHITECTURE_PROPOSAL_NOT_IMPLEMENTED
  confidence: high
- id: OPS-CAN-007
  semantic_digest: 4e1e042e0fa589a1
  topic: Feature flag 求值接口
  rule: 所有业务 feature 求值提议统一经 OpenFeature Evaluation API；默认 PlatformFeatureProvider 复用 PostgreSQL 控制面，Unleash/flagd 仅作可选 Provider。
  why: 将业务调用与具体 feature flag 产品隔离。
  decision: PROPOSED
  implementation: NOT_IMPLEMENTED
  persistence: ARCHITECTURE_RECOVERY_PROPOSAL
  evidence: NO_CODE_VERIFICATION
  confidence: high
- id: OPS-CAN-008
  semantic_digest: 1663a0a2bd141db9
  topic: 契约、语料与形式化验证工具链
  rule: 接口按类型使用 OpenAPI/Spectral/oasdiff、Protobuf/gRPC/Buf、AsyncAPI CLI 或 GraphQL SDL/Inspector 做契约验证；媒体语料分层并按 hash 管理大文件，CI 分 smoke/standard/extended/conformance；Lean/Rocq
    仅用于语义模型、证明和 CI gate，不进入普通线上请求路径。
  why: 通过接口兼容门禁、分层媒体样本和离线形式化证明共同验证执行边界，而不增加线上依赖。
  decision: RETAINED
  implementation: TOOLCHAIN_TEST_CORPUS_AND_FORMAL_GATES_NOT_REPOSITORY_VERIFIED
  persistence: CONVERSATION_BASELINE
  evidence: ADOPTED_TOOLCHAIN_AND_FORMAL_BOUNDARY_PLUS_RETAINED_CORPUS
  confidence: high
- id: WF-AIVFX-CONS-001
  semantic_digest: ce3ac5e97b305417
  topic: 状态驱动执行与事务边界
  rule: 状态流转遵循 Command → canonical 状态转换 → Domain Event → Orchestrator → 下一 Command；进度信号不直接改变生命周期。claim、状态持久化和完成提交使用短事务，外部执行在数据库事务外，FAILED 以可独立提交事务记录。
  why: 把意图、事实、进度和外部副作用分开，降低重复执行、长事务和失败状态回滚风险。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-002
  semantic_digest: 4e010e9ef961affc
  topic: 工作流运行时分工
  rule: 采用一套 canonical Workflow 语义模型和多运行时策略：Temporal 是主要 durable runtime；LiteFlow 仅是 bounded short-chain 候选；OpenCue 只做渲染资源调度；执行环境选择与 workflow runtime 正交，canonical
    状态仍由平台内核拥有。
  why: 避免多个引擎争夺流程与状态权威，并按持久性、时长和调度职责选运行时。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-003
  semantic_digest: 17fa4def4fb4b875
  topic: 工作流类型与组合粒度
  rule: 用户创作工作流与系统内部能力组合分别建模，并区分 Capability Composition、定义级 Graph/Fragment Composition 和拥有独立 durable execution 的 Workflow Composition；Workflow 管编排，Patch 管作品变更，Execution
    DAG 管计算，Subworkflow 是持久组合边界。
  why: 业务过程、作品原子变更、计算执行和子流程的暂停、审批、缓存及失败恢复语义不同。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-004
  semantic_digest: f9c135fa77ca0c7f
  topic: Child Workflow 约束
  rule: Child Workflow 只引用已发布且固定版本的 Definition；默认禁止递归环，首版父到子传播取消，Usage/Cost 只聚合不重复造事实，边界使用稳定类型引用。
  why: 保证子流程可重放、可审计，并避免取消与计量语义重复。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-005
  semantic_digest: 8e20b85c89c1a6c7
  topic: WorkflowDefinition 与 Stage
  rule: WorkflowDefinition 是 typed directed process graph，typed nodes、control-flow edges、data bindings 与 execution policies 分离；任意图环不作为 canonical 控制流。WorkflowStage
    仅是可选组织/治理层，可承载 typed I/O、验收、审批、预算和观测，Node Graph 仍是唯一执行权威。
  why: 把执行语义与展示、分组和治理元数据分开，避免 Stage 或任意环绕过 OperationPlan。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-006
  semantic_digest: b2b6a93b587bcd08
  topic: Workflow、Plugin、Planner 与 Provider 权威
  rule: 按业务类型而非框架划分工作流；Workflow 拥有 lifecycle/process authority，PluginRuntime 决定 WHAT capability executes，Planner 决定 WHERE，Provider 决定 HOW。各层可调用领域内核，但不得自行写 canonical
    领域状态。
  why: 为定义、流程推进、能力选择、执行绑定和领域事务保留单一决策所有者。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.99'
- id: WF-AIVFX-CONS-007
  semantic_digest: 005e5c4355483919
  topic: Embabel/Temporal 早期评估（历史）
  rule: 早期方案曾建议把 Embabel 隔离为可替换规划适配器、Temporal 负责持久执行、领域服务掌握状态；该方案已被更严格的 Foundation Gate 后应用层 POC 边界替代。
  why: 保留被替代的历史判断，不能把早期技术评估重新视为当前采纳项。
  decision: SUPERSEDED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-008
  semantic_digest: 9cc5120095036342
  topic: Embabel 最终定位
  rule: 当前不引入 Embabel 核心依赖；仅保留为 Foundation Gate 后的 Application Agent/Planner POC，优先 Workflow Adoption Analyzer，且不得替代 Temporal 或 PluginRuntime。
  why: 先验证规划价值并保持可替换性，避免形成新的流程或能力执行权威。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-009
  semantic_digest: 51f6e910184c9fbc
  topic: 状态机实现策略
  rule: 采用显式 transition policy、aggregate invariants 等状态机建模思想，但当前不引入 Spring Statemachine；Temporal 保持 durable process authority。
  why: 获得状态约束而不叠加第二个持久流程引擎。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-010
  semantic_digest: 49e3d5e325d3ceb4
  topic: Temporal replay 与动态策略
  rule: 启动 Temporal Workflow 前冻结 ResolvedFeatureSnapshot/AuthorizedExecutionRequest；不得在 replay 代码中动态求值 Feature Flag 或授权，重新授权只发生在 Activity/Application 边界。
  why: 动态策略会破坏 replay 确定性，也会让历史执行受当前权限或开关静默影响。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-011
  semantic_digest: e3c0c26bf9694006
  topic: 产品切片与执行面开放顺序
  rule: 横向增加 Creative、Workflow、Economics、Provenance、UX、3D 能力而不复制 canonical core；先完成基础 gate 与 FIRST_REAL_MEDIA_CUT（现有 FFmpeg 路径的 3–5 clips 最小闭环），再补 Access/Policy、Progressive
    Delivery、Usage/Cost/Observability 与最小计量，之后才开放 Plugin Runtime V2 和 Workflow Execution V1。
  why: 先用真实媒体闭环验证核心，再为高风险执行面建立授权、计量、审计和观测基础。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '1.0'
- id: WF-AIVFX-CONS-012
  semantic_digest: cd3a773608ad40cb
  topic: 精确时间、TemporalMapping 与同步
  rule: 平台内部时间采用整数 Tick，Blender 边界用整数帧、音频边界用整数 sample，避免浮点秒；可变速属于有界、后端中立的 TemporalMapping，时间特效只修改显式 mapping 或对象 range，不隐式 rebase 全局 Timeline。Timeline、Caption、音视频通过
    stable temporal anchors 和 coordinated revisions 同步，并按既定 gate 验证 RenderExtent、handles 与 tails。
  why: 统一精确时钟并显式表达速度和同步，避免跨帧率漂移、隐藏时长变化和领域对象相互可变绑定。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.91'
- id: WF-AIVFX-CONS-013
  semantic_digest: ecc3fa163e6cf590
  topic: Infinite Canvas、Recipe 与 Workflow
  rule: Infinite Canvas 是 Workspace/Product Surface，Visual Workflow 是持久过程组合，Recipe 是可编译为 OperationPlan 的语义组合；presentation edge 不等于 semantic relationship。
  why: 防止界面连线直接升级为流程或领域语义。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '1.0'
- id: WF-AIVFX-CONS-014
  semantic_digest: 36ad6ef60303d77c
  topic: 外部自动化、Camel 与长等待
  rule: n8n、GitHub 等外部自动化可导入 canonical WorkflowDefinition，或作为固定精确版本的 ExternalWorkflowNode 调用；Apache Camel 仅作可替换的连接、协议与 mediation runtime，其 Route/Kamelet/Exchange
    不成为 Workflow、Capability 或领域权威。长等待、回调和重试由 durable workflow/integration 持有，不交给短生命周期边缘函数。
  why: 复用外部连接生态，同时保持版本、状态和长期执行的内部权威。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: medium_high
- id: WF-AIVFX-CONS-015
  semantic_digest: 90a1ccab17087915
  topic: NiFi 参考、Event Plane 与外围基础设施
  rule: 吸收 NiFi 的持久队列/背压、runtime envelope、provenance、API/插件隔离、准入和 retry/yield 分离思想，但 NiFi 不是 canonical runtime。Event Plane 是非权威平台层，EventMesh 仅为可替换 transport/gateway/mesh；canonical
    transaction 先写 Transactional Outbox 再投影为 CloudEvents，媒体字节不走事件面且消费者保持幂等。NiFi、Camel、Redis、NATS、Kafka 等只在出现 concrete consumer 后部署。
  why: 采用成熟模式而不把技术参考误当已部署或领域权威，并避免无需求的重型基础设施。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-016
  semantic_digest: 7db33b3f95631dae
  topic: TMS 与远程 i18n 边界
  rule: 外部 TMS 负责翻译工作流、译文、术语和审核，平台拥有 translation keys、含义、参数 contract 与 fallback；前端可拉取经版本化和 schema 校验的远程 presentation-only locale bundle，并强制 bundled fallback。远程文案不得控制权限、feature、operation、route
    或 workflow。
  why: 支持外部本地化协作而不把业务与安全控制交给远程目录。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-017
  semantic_digest: 6d884e55b6cf8513
  topic: Workflow 模型需求与凭据
  rule: Workflow 节点只声明 Model/Capability Requirements，由兼容性检查与 Provider resolution 生成执行绑定；Secret 不进入 Workflow Definition，仅保存 CredentialBindingId。
  why: 保持定义可移植、可审计，并避免凭据泄露或绑定具体模型供应商。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-018
  semantic_digest: d02094c512d53668
  topic: AI Capability 与框架中立 Plugin SPI
  rule: 新模型通过稳定 Capability Contract、Adapter、Manifest 和显式 feature negotiation 接入；平台插件标准是自有、框架中立的 Plugin SPI，Embabel、AgentScope、MCP 和 UI 只通过 Adapter 消费能力，公共合同外仅允许受控扩展。
  why: 允许模型和 Agent 框架替换，同时不假装供应商能力完全同构或让某框架成为 ABI。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-019
  semantic_digest: 64bed9c6df030997
  topic: MCP、Skill、Agent 与 GraphQL 接入边界
  rule: MCP 是接入协议，Skill 是领域能力包装，Agent 是规划组合层；三者必须调用现有应用服务，不能成为业务权威或绕过 Patch/Revision。MCP 发布从内部 typed SDK 和只读资源开始，再增加分析、Artifact 生成、Patch Preview，最后才开放需授权的 Apply/Workflow/Render。GraphQL
    仅作交互式 Query/Projection API、Subscription 与受控 Command Transport，不是 canonical schema、媒体 DSL、内部服务总线或媒体字节数据面。
  why: 以逐级权限开放控制智能与交互入口风险，并避免接入协议或查询技术成为业务权威。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.97'
- id: WF-AIVFX-CONS-020
  semantic_digest: f25e7c4d706e73de
  topic: Agent、Skill、MCP 与 Capability 统一模型
  rule: Agent、Skill、MCP、Plugin、Template 只能发现、组合和调用平台能力，不是 canonical domain authority；系统、用户、组织、Marketplace 和外部连接的 Agent/Prompt/Skill/MCP/Model 共用同一 Contract family、版本与
    trust/permission 模型。Skill 可声明 MCP tool requirement，MCP 工具经 Adapter 映射为 effective capability view。
  why: 消除内置能力特权和协议泄漏，让所有能力服从一致的版本、信任与授权规则。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.99'
- id: WF-AIVFX-CONS-021
  semantic_digest: 41b1db0be75e8483
  topic: Prompt 与 Skill 资产化
  rule: Prompt 与 Skill 应成为带版本、digest、schema、requirements 和 provenance 的可引用一等资产；Skill 只能生成 OperationPlan proposal，不能直接修改 canonical state。
  why: 使智能组合可重现、可审计，并保留变更门禁。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-022
  semantic_digest: 5fff943e639066d2
  topic: 首个 AI/CV 媒体切片
  rule: 首个 AI 辅助编辑链路为安全导入 → 人脸/主体检测与跟踪 → Auto Reframe proposal → 预览授权 → 新 revision → 9:16 MP4，并配套 MEDIA_TASK_PACKAGE_INGEST、MEDIA_ANALYSIS_OBSERVATION 与 FIRST_AI_ASSISTED_EDIT
    基础。
  why: 用可审核 proposal 而非自动改写 Timeline 验证 AI 分析到真实输出的闭环。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '1.0'
- id: WF-AIVFX-CONS-023
  semantic_digest: f5a8ab42cc77596e
  topic: Agent 权限上限
  rule: Agent、MCP、Shell、Workflow、GraphQL 等入口不能绕过 acting principal 授权，Agent 不得拥有高于 acting principal 的 canonical mutation authority。
  why: 防止入口或自动化身份形成权限提升通道。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-024
  semantic_digest: d2825d1e2bef1c5e
  topic: Agent 产品入口
  rule: Product Shell 内 Agent 是继承当前选择上下文的即时 Copilot；独立 Agent Workspace 面向跨项目、长任务、runs、plans、automation 与 approvals；两者共享同一 Agent、Operation、Capability 和 Authorization
    模型。
  why: 区分即时协助与长期自治体验，同时避免两套智能能力和权限体系。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-025
  semantic_digest: 16c65e12856e4785
  topic: Planner Explain/Analyze
  rule: Planner 应提供 Explain/Analyze，说明执行选择、约束、权衡、物化和成本。
  why: 让自动规划结果可审计、可比较并可由人批准。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-026
  semantic_digest: 2464fe2e6bd28acb
  topic: 并行 Agent 工程隔离
  rule: 并行 Agent 工程任务使用隔离 worktree、显式任务 DAG、独立验证和受控合并。
  why: 减少并行修改相互污染，并让每个工作流结果可验证和可回滚。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-027
  semantic_digest: 1847aed45f140fa2
  topic: 音频增益与响度语义
  rule: Gain 是非破坏 canonical composition primitive；source loudness 是带算法版本的 derived analysis；clip/track/bus/master/delivery gain、peak/loudness normalization、compression
    与 true-peak 各自分权。
  why: 避免把分析值、创作增益、动态处理和交付规范混成单一音量参数。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.99'
- id: WF-AIVFX-CONS-028
  semantic_digest: ab9fe208a5821f6b
  topic: Blender、Previs 与动作捕捉边界
  rule: Blender 是可替换的 Scene/Animation/Simulation/Motion/Render Provider，而非 Timeline 或镜头语义权威；Scene/Shot/Camera、动作捕捉语义、版本和采纳由平台管理，.blend 仅作 Artifact。一个 Blender Shot
    默认对应一个主摄像机输出，Blender 的反向变化只能作为提案由 Timeline 接受或拒绝。
  why: 利用 Blender 的三维执行能力，同时避免多个事实源、二进制合并和 Provider 静默反写。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-029
  semantic_digest: 8569e2df5ef9edc3
  topic: 异构媒体资产模型
  rule: 统一媒体 identity、lifecycle 和引用，但保留各媒体的 intrinsic clock、geometry 与 metadata；来源与媒体类型、Asset 与 Clip、不可变 AssetVersion 与二进制 Artifact 分离，派生进入 Provenance DAG，并通过 typed
    bindings 接入 Timeline，不用通用 payload 抹平语义。
  why: 在支持上传、生成、派生和复合资产的同时保留不同媒体的真实语义。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.99'
- id: WF-AIVFX-CONS-030
  semantic_digest: 8c36b65155a57929
  topic: 版本、Provenance 与外部工具研究
  rule: 内部 Structured Version Semantics 与 PROVENANCE_LINEAGE_V1 自己拥有变更和媒体生命周期语义。Foundation Gate 后将 Revision Backend（JGit vs jj-lib）与 Structured Version Semantics（TerminusDB/Dolt/Panproto）分轨研究；OpenLineage
    只作互操作投影，Marquez 可选 POC、DataHub 留作后期企业 catalog、OTel 只做运行时关联、C2PA 只做对外可验证投影。
  why: 把待验证的版本后端、结构化语义与外部血缘投影分开，不把技术参考误作平台权威或已采纳实现。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.95'
- id: WF-AIVFX-CONS-031
  semantic_digest: 74bf0558c862708f
  topic: 字幕渲染后端政策
  rule: Canonical Subtitle Model 由平台拥有；默认生产路径是 FFmpeg/libass，高级路径是平台 WebCaptionRenderer。Remotion 不作默认字幕或 canonical media renderer，只保留为受许可门禁、成本计量且可替换的可选后端。
  why: 保留开放、可自托管和成本可预测的默认路径，同时允许受控高级表现。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-032
  semantic_digest: 771a17cdcb3c3e38
  topic: MLT 与 OpenFX 分工
  rule: OpenFX 作为专业效果插件兼容标准，不是 Canonical Effect、Timeline、Workflow 或 Data Plane 权威；MLT 仅是可选 NLE/传统效果/OpenFX 兼容 Provider，不作主 Timeline 或主媒体 Runtime，初期可作为 OpenFX Host，独立
    Host 延后。
  why: 获取开放专业效果生态而不新增 canonical 权威或过早制造独立执行面。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-033
  semantic_digest: 7d4fd4260e621eb0
  topic: ASWF 与图像/VFX 组件角色
  rule: OpenUSD、MaterialX、OCIO、OpenVDB/NanoVDB、OpenAssetIO/ArResolver、Hydra/Storm、OpenImageIO/OpenEXR 等只承担交换、解析、呈现或执行职责，不自动成为平台领域权威：OpenFX 不是 shader IR，OpenVDB 是稀疏体
    backend、NanoVDB 是派生 GPU representation，Hydra 是 scene delegation、Storm 是参考 preview，Open RV/Gaffer 是 review/参考表面，Partio 在有真实 consumer 前推迟。
  why: 明确每项技术的角色和引入条件，避免把生态参考误写成已采纳的 canonical 架构。
  decision: RETAINED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.98'
- id: WF-AIVFX-CONS-034
  semantic_digest: 32dd86df352e0234
  topic: ASWF 能力引入顺序
  rule: 先完成 Media Canonical Model V2 与 Timeline V2，再建设 Color Foundation、RenderGraph/GPU、Provider Fabric、Distributed Render，最后按实际需求引入 Advanced VFX/3D；OpenAssetIO 仅作为横向
    asset interoperability port。
  why: 先稳定媒体语义和执行合同，再增加高复杂度三维与分布式能力。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.94'
- id: WF-AIVFX-CONS-035
  semantic_digest: a00bbe0d9a997f1d
  topic: 增量渲染范围
  rule: 媒体变更先计算 dependency closure 与 temporal halo，只重算最小必要渲染范围。
  why: 在保证依赖和时间邻域正确性的前提下降低重渲染成本。
  decision: ADOPTED_IN_CONVERSATION
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-036
  semantic_digest: a892a4e130c2a76f
  topic: 专业与生成式媒体运行时候选
  rule: OpenFX 插件候选集中由 Natron 承载，Blender、Sverchok、Gaffer 通过 OpenEXR 图像序列与 Natron 协作而不直接加载 OFX；生成式多媒体候选采用 ComfyUI 为生成中枢、Ollama 为语言/RAG 中枢，复杂音频与 3D 使用隔离 Python 环境，Blender
    负责最终 3D 资产处理。上述均为待验证运行架构，不视为已实施或已采纳。
  why: 隔离专业插件、生成模型和原生依赖，同时明确这些技术组合仍只是提案。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: high
- id: WF-AIVFX-CONS-037
  semantic_digest: e614c744ca75be1e
  topic: PVE 与 OpenCue Worker 部署
  rule: 基础设施候选采用 PVE_CLEAN_SLATE_INFRASTRUCTURE_TOPOLOGY_V2：pve-1 主责基础设施与临时 CI，pve-2 主责媒体运行时与临时 Worker；OpenCue 中 FFmpeg、OpenImageIO、OpenColorIO、MediaInfo 等安装在 RQD
    render workers 而非 Cuebot，OpenCV 按能力提供，Blender/GStreamer 等后置。
  why: 把控制服务与媒体执行工具分开，并按真实能力需求逐步扩展 Worker 镜像。
  decision: PROPOSED
  implementation: CONSOLIDATED_WITHOUT_IMPLEMENTATION_UPGRADE
  persistence: CONSOLIDATED_REGISTER_ONLY_NO_GOVERNANCE_UPGRADE
  evidence: SOURCE_REGISTER_EVIDENCE_ONLY_NOT_INDEPENDENTLY_REVERIFIED
  confidence: '0.99'
```

## 外部核验摘要

```yaml
external_verification:
  verified_on: '2026-09-06'
  scope_policy: 仅核验技术角色、项目身份、许可或宽泛维护状态；精确版本、价格、配额及内部集成状态除非明确列出，否则仍未核验。
  findings:
  - technology: OpenCue
    status: VERIFIED
    verified_scope: 确认其为影视/动画渲染管理系统；官方仓库活跃并声明 Apache-2.0。
    boundary: 支持限定的农场/渲染管理角色；不支持其成为 canonical Workflow 或媒体权威。
  - technology: BMF (Babit Multimedia Framework)
    status: VERIFIED
    verified_scope: 确认其为跨平台、多语言多媒体框架，支持 GPU 与异构执行；仓库声明 Apache-2.0 且近期活跃。
    boundary: 可作为受限 Provider-native graph POC；部署兼容性仍需实测。
  - technology: Temporal
    status: VERIFIED
    verified_scope: 确认其为可跨故障恢复工作流的开源 durable-execution 平台。
    boundary: 适合持久编排机制，不拥有平台业务语义。
  - technology: Apache NiFi
    status: VERIFIED
    verified_scope: 确认其用于系统间信息流管理，具备队列、背压与数据流处理能力。
    boundary: 适合作为集成/数据流 Provider，不是 canonical Workflow 权威。
  - technology: Apache Camel
    status: VERIFIED
    verified_scope: 确认其为协议、格式、连接器与企业集成模式的集成框架/库。
    boundary: 仅支持受限的集成管道角色。
  - technology: OpenTimelineIO
    status: VERIFIED
    verified_scope: 确认其为剪辑信息 API 与交换格式，且不是媒体容器；项目被描述为成熟并持续开发。
    boundary: 适合作为交换边界，不是平台完整 canonical Timeline 权威。
  - technology: OpenUSD
    status: VERIFIED
    verified_scope: 确认其为协作构建、组合与交换动画 3D 场景的可扩展平台。
    boundary: 支持场景交换/组合；平台权威边界仍由内部决策定义。
  - technology: MaterialX
    status: VERIFIED
    verified_scope: 确认其为跨应用和渲染器的材质与外观开发开放交换标准，仓库声明 Apache-2.0。
    boundary: 支持外观开发交换，不是完整材质领域权威。
  - technology: Natron
    status: PARTIALLY_VERIFIED
    verified_scope: 仅部分确认：官方发布页存在较新预发布活动；未固定稳定版或生产就绪结论。
    boundary: 保留为可选 OpenFX/合成集成候选，不保证作为主后端。
  - technology: PF4J
    status: VERIFIED_WITH_ARCHITECTURAL_INFERENCE
    verified_scope: 确认其为带插件生命周期与独立类加载器的轻量 Java 插件框架；类加载隔离不等于操作系统安全边界。
    boundary: 仅用于可信、受控 JVM 扩展；不可信代码仍需进程或容器隔离。
  - technology: Embabel
    status: VERIFIED
    verified_scope: 确认当前官方项目为 JVM Agent 框架，结合大模型交互、代码和领域模型。
    boundary: 保留为候选 Agent 规划层，不是平台权威。
  - technology: OpenAssetIO
    status: VERIFIED
    verified_scope: 确认其为媒体生产工具与资产管理系统之间的互操作标准。
    boundary: 支持资产管理互操作边界，不拥有 Artifact identity。
  left_unverified:
    - 历史仓库提交标识、测试数量、里程碑完成声明和所有实现状态。
    - 云价格、免费层、配额、区域可用性和账户特有限制。
    - 未在核验摘要中明确给出的精确当前版本。
    - 本地工作站与虚拟化环境库存声明。
    - Odoo、OpenMeter、Hyperswitch 的当前产品与许可细节。
    - 媒体、字体、翻译或模型权利的法律结论。
```

## 使用约束

- 回答“当前是否可用/已完成”前，必须同时检查该决策的 `implementation`、`persistence` 与 `evidence`，不能只看 `decision`。
- 生成方案时优先遵循 `ADOPTED_IN_CONVERSATION` 与 `RETAINED`；`PROPOSED`/`PENDING` 必须显式标为候选；`SUPERSEDED` 不得复活。
- 若关系字段与文字冲突，以更具体、更新且非 `SUPERSEDED` 的决策为准；仍不明确时停止推断并请求核验。
- 外部核验结论只支持技术角色边界，不应被扩张为性能、生产就绪、兼容性、成本或集成完成证明。
