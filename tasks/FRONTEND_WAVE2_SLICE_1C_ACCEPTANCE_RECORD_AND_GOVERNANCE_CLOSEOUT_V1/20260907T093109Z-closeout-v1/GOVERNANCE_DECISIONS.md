# H4 与 tracked-dist：事实、现行约束、待决包

## H4 精确身份与原由

当前待决 identifier：`WAVE2_FREEZE_GATE_01=AUXILIARY_H4_LEDGER_OWNER_DISPOSITION`，来源 `sources/slice1c-recovery.txt:88–91`（原绝对位置见 SOURCE_INDEX.json）。

不要把该门禁误解为后端架构 H4，也不要把历史越界写 incident 当成该 ledger failure。
历史 schema=`H4_FRONTEND_PRODUCT_SURFACE_DISPOSITION_LEDGER_V1`；task=`FRONTEND_PRODUCT_SURFACE_CANONICAL_CONTRACT_ALIGNMENT_AND_CLEAN_FORWARD_V1`；后续 correction=`H4_BOUNDED_CORRECTION_R1_R6`。原始账本位于 `docs/architecture/governance/h4-frontend-product-surface-disposition-ledger-v1.json`，记录旧前端 product surface 的 canonical contract 对齐、shadow 清理、不可用 projection 的 fail-closed 处置；并非 Slice1C 新功能验收表。

可演进记录是 `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv`，schema=`FRONTEND_CURRENT_GOVERNED_SCOPE_LEDGER_V1`，h4_base_sha=`9cd899a3ad6196e04cdfda21430ed61529abf49a`。其首三行固定两个 law：`HISTORICAL_CLOSURE_LEDGER_IS_IMMUTABLE_V1`、`CURRENT_GOVERNED_SCOPE_EVOLVES_APPEND_FORWARD_V1`。`frontend/scripts/validate-h4-disposition-ledger.mjs:9–25,41–57` 区分历史与 current scope；实际 current source 必须有 ACTIVE identity，测试、fixtures、声明文件等有各自排除，不是任意 path classification 的同义物。

最早恢复的 Wave2 gap 证据为 `sources/h4-baseline-gap.md`：历史执行 `npm run h4:ledger` 报 `missing actual current scope identity: frontend/src/integrations/localization/adapters/TolgeeRemoteCatalogAdapter.ts`。基线和当时 current ledger SHA256 均为 `e1fa98bda1ad3c77ab8b91d83a8fad59b1507310e38837ac3a88b10e0f1f7945`，adapter 均为 `f33b45294aa66b04a5a2cb67ee71b310208ea90e860e3f00469eb9ffc497d6de`。该文件已经存在于 supplied base；不是 Slice1A/1B/1C 新增的 source defect。架构 exact-path ledger 与 H4 current-scope ledger 是不同账本，前者 green 不能证明后者 green。

责任：原 gap 明确记录 `Hermes/Owner disposition`；frontend architecture 与 API gap 文档 owner=`frontend-platform`。H4 JSON 本身没有指定个人 owner，不自任新 owner。Hermes可恢复事实和准备方案；Owner决定该 freeze debt 如何处置，后续执行者须获确切写集授权。

### 具体决策包

建议选项 A：承认它是预存 current-scope 覆盖债务；保持历史 H4 关闭账本 immutable；继续承认已采纳的 Slice1C 技术结果；在未来产品 freeze 前安排单独、append-forward、逐路径的 current-scope reconciliation，保留 validator 的双账本 laws 与原覆盖标准。**本任务没有执行 reconciliation，没有 waive gate。**

替代选项 B：Owner 明确授予仅冻结层面的限时例外并指定补齐期限/验收条件；这属于新 waiver，当前没有它的依据，不推荐以无期限 defer 代替关闭。

已有 evidence：原 failure、baseline bytes、历史与当前账本、明确 freeze-gate 来源；本次只重核文档引用和特定已知漏项，未重跑 H4 gate，也未扩展 census。仍缺：Owner 对 A/B 的具体 disposition，以及未来 reconciliation 的完整差异与验证证据。现有一般 closeout 授权并不包含未知 waiver，也不包含源/guard 修正。

建议批准语句：“采用 H4 方案 A：保留历史关闭账本，认可当前缺口为预存路径治理债务；不影响已采纳 bounded technical acceptance；产品 freeze 前单独完成 current-scope append-forward reconciliation，不豁免 gate。”这是 disposition 批准，不是立即授权本任务更改 ledger 或 commit。

### 实际阻塞

- 技术 review：不阻塞，已采纳。
- Formal Slice1C acceptance：未恢复到一条要求 H4 必须先关闭的规则；不能凭 H4 推断总体验收不合格。总体验收账本/覆盖来源仍待明确，不宣布 overall closure。
- 独立 frontend UI 开发：非绝对阻塞；新任务需明确授权且不能借此改 H4。
- Product freeze/readiness：现有 WAVE2_FREEZE_GATE_01 未关闭。
- Commit/publication：本任务本身禁止；未来不能用技术 PASS 或本提案替代 freeze/commit/publication 独立授权。

## tracked-dist 实际 policy 与 destination

当前 frontend lane 真实 tracked paths 见 `ARTIFACT_PATHS.json`：frontend/dist 8，backend static 3，frontend/build 0。是该分支的只读观察，不是 backend candidate 的实时状态。未要求并行 backend ref/head/status 冻结。

现有要求：
- `sources/historical-output-policy.md:94–98` 记录 Vite 默认输出 backend static、当时 coupling viable、当时三个 dist 文件 DEFER。该“三个”是历史时间点，不能覆盖本次 8 个观察。
- `sources/architecture.md:442–444`：若 kept tracked，generated output 按产物验证，不能作为 source authority。
- `sources/vite-config.ts:25–29`：outDir=`../platform-app/src/main/resources/static`，emptyOutDir=true，assetsDir=assets。这意味着裸 build 的输出/清理目标是后端静态目录，不是 frontend/dist。
- `sources/package.json:8`：build=`vite build`，没有自带安全 override。
- 根 `.gitignore` 忽略 `**/build/`、node_modules，不存在取消这些 tracked dist/static 文件的有效规则；ignore 从不追溯 untrack 已跟踪文件。
- 后续 Wave2 plan (`sources/wave2-plan.md:73–79`) 要求未来 build 预先解析并记录 external/frontend-only outDir、保护 backend、禁止 bare npm run build；当前 Owner 又明确只读，故本次 build=0。
- 当前 `frontend/Dockerfile` 是 node 开发服务器，不构成生产 bundle packaging 决策。后端 static 是 platform-app 资源路径，但此次恢复没有找到授予前端任务跨 lane 打包/清理/发布权限的记录。产品打包和 publication 要 Owner 另行授权；不凭目录名自定个人 packaging owner。

不一致有三层：旧耦合说明与后来 frontend-only build discipline；历史 tracked dist 与新 external reviewed build 身份；未来 freeze 如何把 artifact/source 精确绑定。不是“删除产物即可 green”，更不是后端 candidate gate-output-isolation incident 已替前端解决问题。前端已有历史 static 越界 incident（历史记录 1 incident/10 paths）须保持其原处置时间线；此 task 没有新 incident，也不据其推断 H4 原因。

### 具体 policy 提案（尚未 enact）

推荐 A：本轮保留已有 tracked policy，不改 .gitignore/config、不删文件；平时前端独立验证只写明确 external outDir；未来获授权 freeze 时，固定 exact implementation，生成授权 frontend/dist，逐 path/size/hash 验证 staged artifact 与 exact-tree rebuild 等价，必要的 path-classification 更新单列；与 backend static 的拷贝、cleanup、packaging 只在独立授权的 integration/release task 执行。Owner 同时确认该 integration/release task 的 packaging 责任 lane，未确认前不得写 backend static。

替代 B：未来单独迁移为 untracked/generated artifact policy，包含 ignore、build destination、packaging contract、CI/docs 同步及验证；这是后续 implementation/governance task，不在本次 scope。不能把本方案文件当成迁移已生效。

还缺 Owner 选择 A/B 并确认未来 packaging boundary。建议选择 A，避免无关迁移。建议批准语句：“采用 tracked-dist 方案 A；保留 tracked generated artifacts，独立前端验证 external-only；未来获授权 freeze 逐字节绑定产物，backend static 仅由单独授权的 integration/release task 处理；本次不 enact 配置或产物变更。”

门禁源=`WAVE2_FREEZE_GATE_02=TRACKED_FRONTEND_DIST_ARTIFACT_POLICY_RECONCILIATION` (`sources/slice1c-recovery.txt:90–91`)。阻塞未来 artifact freeze readiness；不否定 accepted technical review，不把 dirty HEAD/static/dist 与 fixed reviewed build 混同。独立 frontend-local UI 的另行授权开发不需要 backend packaging 先发生。当前产品 commit/freeze/merge/push/publication 全未授权/未执行。
