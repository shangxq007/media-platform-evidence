# Acceptance / governance / release dependency matrix

本表为原验收/交接结构的集成就绪增量，不是新权威账本。Accepted technical items 不因 release 未授权而回退 PENDING。

| Item | Evidence source | Current disposition | Actual dependency |
|---|---|---|---|
| Canvas correction technical review | Owner 当前任务 §4；c73104c5dc6be81eb41f173aa5f20f4d5d564e73 | ACCEPTED_BOUNDED | 不重开；固定实现身份 |
| Pagehide observation-boundary diagnosis | 2a2d014890d3a0ff693f4ad876a39a0df4d236df；Owner §3 | ACCEPTED_RECORDED_CHROMIUM_PATH | D1 excluded，D3 probes not established；不泛化 |
| Validator completeness correction | 7a0e93e9a4c6db56d002c741981cf3bd829424c1；Owner adopted review | ACCEPTED_CLOSED | 无新增 browser/product correction |
| Recorded lifecycle evidence | 既有 12/12 execution + accepted offline reassessment | ACCEPTED_WITHIN_RECORDED_SCOPE | Mock-backed Chromium；不是本次 fresh，不改旧49/50 |
| Formal Slice1C acceptance | 未找回总验收账本；本次 authority 是 bounded technical adoption | NOT_DECLARED_OVERALL; LEDGER_INTEGRATION_PENDING | 不擅自推定 overall closure；不发明 H4-before-technical-PASS 依赖 |
| H4 disposition | BASELINE_LEDGER_GAP；WAVE2_FREEZE_GATE_01 | PREEXISTING_SCOPE_LEDGER_DEBT; OWNER_PROPOSAL_A_READY | Owner disposition + 后续逐路径 reconciliation；无 waiver |
| Tracked-dist disposition | Vite outDir、tracked path list、WAVE2_FREEZE_GATE_02 | OWNER_PROPOSAL_A_READY_NOT_ENACTED | 未来 artifact/source binding、packaging boundary 与单独授权 |
| Product commit/freeze readiness | 当前任务 §1；前述 freeze gates | NOT_AUTHORIZED; FREEZE_GATES_OPEN | 不使用 dirty HEAD 代替 reviewed tree；独立授权 |
| Product publication readiness | Owner §3/§12 | NOT_AUTHORIZED_NOT_PERFORMED | freeze/acceptance/integration/release 授权，不改变 EP19/#23/Second Wave gates |
| Next independent frontend task | Wave2 plan §Subsequent priorities；NEXT_FRONTEND_TASK.md | PREPARED_CONDITIONAL | 明确下一 bounded implementation 授权及计划顺序 disposition；可先于 product publication |

## 本任务完成与待决分开

Documentation closeout 的交付标准是 accepted entry + precise packets + matrix + one plan-backed next brief + bounded evidence delivery，不要求 Owner 在此 turn 已选择 H4/dist，也不要求 product implementation 成功。Path recovery gap 明确交付，不用新 ledger 掩盖。

Owner 只需处理真实剩余项：GOVERNANCE_DECISIONS.md 的 H4 方案 A/B 和 tracked-dist 方案 A/B；以及是否在 formal Slice1C ledger 集成前单独授权 NEXT_FRONTEND_TASK.md 的本地 UI continuation。已采纳 validator review 和 exact branch ref 不再索取确认。
