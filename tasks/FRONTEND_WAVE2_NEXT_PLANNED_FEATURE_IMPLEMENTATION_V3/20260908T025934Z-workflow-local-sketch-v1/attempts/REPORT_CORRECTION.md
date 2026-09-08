# Public derivative: unrelated stash metadata omitted; original retained locally

# FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3 — bounded correction report

STATUS=THREE_SOURCE_REVIEW_FINDINGS_CORRECTED_TARGETED_GREEN
FINAL_EXACT_TREE_GATES=NOT_RUN
PRODUCT_PUBLICATION=NOT_PERFORMED
BACKEND_INTEGRATION=NOT_PERFORMED

## Scope and preserved state

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`
- Branch: `agent/frontend-wave2-product-ux-v1`
- HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`
- HEAD parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`
- Applicable instruction file: worktree-root `AGENTS.md`; no nested instruction file applies to the two product paths. The Owner-authorized correction supplies the bounded source/test write scope and required test scope; no conflict was found.
- The pre-existing dirty worktree, writer attempts `01` through `12`, and `REPORT_INITIAL_HANDOFF.md` were preserved. Current SHA-256 for `REPORT_INITIAL_HANDOFF.md`: `9b61f73e1b92eb4950c572ecb532481e97dcaa1911f79c66be039aa96c02e6b5`.
- Product writes in this correction were limited to `frontend/src/product/workflow-sketch/WorkflowSketch.tsx` and `frontend/src/product/workflow-sketch/WorkflowSketch.test.tsx`. No Git index/ref/commit, instruction, configuration, skill, memory, backend, accepted shared engine, persistence, or execution source was written.

## Corrected source identities

| SHA-256 | Path | Correction classification |
|---|---|---|
| `ff3bd8780f8c815938d19c71fc667d271c4dd9437ec5adfd63a5c188ea70b155` | `frontend/src/product/workflow-sketch/WorkflowSketch.tsx` | Corrected local component |
| `e0b062254c1b480f31d4a46b25155235e8a6c3c339213069f614c74be3473ced` | `frontend/src/product/workflow-sketch/WorkflowSketch.test.tsx` | Corrected behavioral tests |
| `7b1a778538215bab79945a0082e2d7852c2a36064f4ca5fa87a8b2ef4fce46df` | `frontend/src/product/workflow-sketch/model.ts` | Inspected/preserved local model |
| `14e188aebb9978985ec02b3d8c99926efeaacf3fffe2dcb611a5216061834488` | `frontend/src/product/workflow-sketch/model.test.ts` | Inspected/preserved model tests |
| `e56db59bbe54cf370878256f3018b8d2822d3324c2a3c627a566411de0c25dfa` | `frontend/src/interaction/InteractionDialog.tsx` | Inspected/preserved shared dialog |
| `86c1869dcaef397c67b268d6eedcebc89960947e12a6dd842adbe6e953170f29` | `frontend/src/interaction/SelectionContext.tsx` | Inspected/preserved shared selection API |
| `bff063f2346274c771b9dd834650e66338b5b8291a004dfe9e406b3f0ff5bc19` | `frontend/src/interaction/model.ts` | Inspected/preserved shared engine |

The prior handoff identities for the two corrected files were `2823a9759de30e752f4890e82002ad2b4fc468638f492dda0846e97d790cf58b` and `cb3c009385aecb730b7d58ca29c3b963457995efbb00ca9115e6e754685f8500`, respectively. No lifetime-derived string key was introduced.

## Finding dispositions

1. **Composing native activation — corrected.** `onNodeKeyDown` now identifies Enter/Space before the composition guard and calls `preventDefault()` for composing Enter/Space, including key code 229, while returning without selection. The behavioral test dispatches cancelable composing Enter and key-code-229 Space events and asserts `defaultPrevented === true` for both plus unchanged selection.
2. **Unconditional delayed focus — corrected.** The `pendingFocus` ref and layout-effect focus queue were removed. Add, remove, and confirmed discard receive `event.currentTarget`, compare it with `document.activeElement`, and transfer focus only for the control that actually owns focus. Transfers use the already-mounted board synchronously; confirmed discard first synchronously closes through the existing `InteractionDialog` lifecycle and then focuses the board. Programmatic/nonfocused add and remove tests prove that a separately focused stable board/card retains focus. The earlier NEW capacity-test expectation was deliberately changed from the last-created card to the stable board: the Owner explicitly permits an existing stable board destination, it remains enabled when palette controls become disabled, and it avoids making a newly created card an unnecessary focus-policy dependency.
3. **Confirmation surviving owner change — corrected.** Reset confirmation now lives inside the state record owned by exact `store` and `selection.lifetime` identities. An owner change synchronously presents a fresh sketch with confirmation false; all state updaters retain exact owner guards. The regression opens confirmation, replaces scope/owner, verifies the dialog retires, adds a new-scope card, invokes the detached old control, and verifies the new-scope card remains.

Unconfigured, current-page-only, persistence, backend, canonical semantic, and execution/invocation boundaries remain unchanged. Shared Selection/pagehide ownership and `InteractionDialog` implementations were not modified.

## RED/GREEN and requested regressions

All evidence is append-only under this writer directory and each JSON report has a distinct native-exit companion.

| Attempt | Exact test scope | Native exit | Machine-readable result |
|---|---|---:|---|
| `13-workflow-correction-red` | `src/product/workflow-sketch/WorkflowSketch.test.tsx` after behavioral test edits and before component correction | 1 | 10 total; 6 passed; 4 failed; 0 pending. Failures covered composing default cancellation, focused capacity destination, nonfocused focus retention, and owner-scoped confirmation. |
| `14-workflow-correction-green` | `src/product/workflow-sketch/WorkflowSketch.test.tsx` after component correction | 0 | 10 total; 10 passed; 0 failed; 0 pending. |
| `15-correction-regressions-green` | Workflow model/component + route tree + localization + InteractionShell | 0 | 82 total; 82 passed; 0 failed; 0 pending. Vitest suite counters: 10/10 passed. |

Commands:

```text
node_modules/.bin/vitest --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/writer/13-workflow-correction-red.json src/product/workflow-sketch/WorkflowSketch.test.tsx

node_modules/.bin/vitest --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/writer/14-workflow-correction-green.json src/product/workflow-sketch/WorkflowSketch.test.tsx

node_modules/.bin/vitest --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/writer/15-correction-regressions-green.json src/product/workflow-sketch/model.test.ts src/product/workflow-sketch/WorkflowSketch.test.tsx src/app/routeTree.test.tsx src/localization/localization.test.tsx src/interaction/InteractionShell.test.tsx
```

Attempt 15 per-file counts:

- `src/product/workflow-sketch/model.test.ts`: 4/4 passed.
- `src/product/workflow-sketch/WorkflowSketch.test.tsx`: 10/10 passed.
- `src/app/routeTree.test.tsx`: 10/10 passed.
- `src/localization/localization.test.tsx`: 13/13 passed.
- `src/interaction/InteractionShell.test.tsx`: 45/45 passed.

Evidence SHA-256 identities:

- `13-workflow-correction-red.json`: `3177c2425139c443b1bd1f68fc80fb4a783772bb5c2e88f9be63d48844a178a0`
- `14-workflow-correction-green.json`: `5ffdd247f0f3385902591935718ab1a8e8e23c7d7a4838b123d3642710bc8147`
- `15-correction-regressions-green.json`: `d9d79d25a5fc8a60c3c5919720e2e996845a53859b5345103ecb41252465e554`

Per Owner instruction, no full suite, typecheck, lint, architecture guard, build, browser run, final exact-tree gate, publication, or optional expansion was performed.
