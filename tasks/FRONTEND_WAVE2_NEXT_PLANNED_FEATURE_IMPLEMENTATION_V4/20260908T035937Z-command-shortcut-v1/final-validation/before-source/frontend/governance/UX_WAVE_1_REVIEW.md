# Frontend product interaction and UX wave 1

HUMAN_REVIEW_REQUIRED=YES
HUMAN_REVIEW_STATUS=DEFERRED

This is uncommitted, UNFROZEN implementation work. No freeze, integration, remote operation, publication or visual approval occurred. Hermes will collect screenshots separately; none are claimed here.

## Scope and instruction precedence

Task: FRONTEND_PRODUCT_INTERACTION_AND_UX_WAVE_1. Sole implementation writer, no delegation. Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-product-interaction-ux-wave-1`. Branch: `agent/frontend-product-interaction-ux-wave-1`. Starting and retained HEAD: `2b0c306467c98ca8b67da4ad5f7b228e52f7107a`; parent: `681aadaec61f7e0fe222bb554075ab05471ad3c3`. Initial working tree was clean. One pre-existing stash was present and left untouched.

Root `AGENTS.md` applies to all changes. No nested frontend instruction files were found. The explicit Owner task overrides the root requirement to freeze before verification: verification runs against uncommitted files, without a candidate SHA. Instruction alignment is deferred to a separate governance task; AGENTS.md and skills are untouched. Only frontend files are changed. No backend/Gradle tests, installations, Git mutations, or canonical-root operations were performed.

Inspected before implementation: product canvas model and component; Review history/compare and request tests; NLE gateway operation preview/apply/readback state machine and regression tests; app shell, route scope and design-system primitives; foundation tests; architecture guard and its negative controls.

## Changes and exact human review flows

Use the installed frontend dev server (`cd frontend && npm run dev -- --host 127.0.0.1`). URLs below use its default port 3000; use the printed port if occupied. Replace `WORKSPACE_ID` and `PROJECT_ID` with authorized server-projected IDs (URL-encode each). No demo route or production mock import was added.

1. `http://127.0.0.1:3000/w/WORKSPACE_ID/projects/PROJECT_ID/canvas`: Tab to the canvas; arrows pan, unmodified `=`/`-` zoom, buttons stop at 50% and 200%, Reset viewport returns to 100% at origin. Tab to a node: focus alone does not select; Enter/Space or click selects. Arrow keys on a node select and move that node by 24 local units. Edit Local title/X/Y in the inline local inspector; placement is bounded to −2000…2000 local units. Visual guides follow local positions without changing reference identity or relationships. Clear selection, Escape on the canvas/node, and clicking canvas background clear selection and return focus to the canvas. Show selected node brings an arrangement back into view. Modified shortcuts and text controls retain their native behavior. Navigate to another project or workspace and verify title, placement, zoom and selection reset. Titles and layout are explicitly not saved.
2. `http://127.0.0.1:3000/w/WORKSPACE_ID/projects/PROJECT_ID/review`: Semantic Changes starts with history loading; failure has an alert and Retry history; empty history has No revisions available and Refresh history; a single distinct revision explains why comparison is disabled. Select two different projected revisions. Compare stays disabled for missing/equal selections and while its request is pending. Starting comparison clears the previous result. Change either selector during an outstanding request; only the newly requested pair may render. Failure has an alert and Retry comparison. Server success with no entities shows a distinct loaded-empty state. Navigate across project/workspace scopes while history or comparison is pending; old responses must not appear. Arrow keys/Home/End navigate the linked tabs and tabpanels. Other sections continue to state that their projection is unavailable; merge remains disabled.
3. `http://127.0.0.1:3000/w/WORKSPACE_ID/projects/PROJECT_ID/edit`: The presentation stage labels playback as simulation, not decoded media. Scrub local steps 0–20, use Previous/Next or Left/Right, and Home/End for bounds. Play advances one local step per second, pauses at the limit, and scrubbing pauses simulation. On a focused lane, Enter/Space selects; Up/Down focuses and selects the adjacent lane; Escape clears. Space on a lane retains native button activation; Space on the timeline background toggles simulation. Inspector shows lane selection and local step. The advanced Add Media Clip preview/confirm/apply/readback state machine is retained; only its presentation-step reducer branch is bounded. Do not submit real operations merely to review the local controls.

At widths near 390, 768, 1024 and 1440 pixels, review wrapping toolbars, focus indicators, lane controls, long revision IDs, and the local inspector. Canvas and NLE no longer force a 900px shell minimum; shell side panels stack on narrow screens and the inline canvas inspector stacks when the center area is narrow. Native accessibility and layout need Hermes/human browser review; DOM interaction tests are not screenshot evidence.

## State behavior, fakes and gaps

History and comparison use the existing TimelineQueryGateway; no client diff, inferred HEAD, canonical merge or new endpoint exists. Request generations reject superseded responses; project/workspace keys isolate sessions. Existing ScriptedTimelineQueryGateway and ScriptedOperationGateway are used only in tests, including deferred and rejected responses. Production routes retain real gateways and existing explicit unavailable boundaries.

Canvas reference IDs, semantic identity and visual-guide definitions remain separate from local display state. NLE V1/A1 are explicitly presentation lanes; the 0–20 range is neither media duration nor authoritative timeline geometry. No clip drag/trim/editing or decoded playback was invented. The empty diff prompt now works for both explicit Review pairs and NLE comparisons.

Proposals only are recorded in `BACKEND_ENABLEMENT_REQUESTS.tsv`, with explicit blocking levels, current MOCK behavior, contract needs and acceptance criteria. Existing unresolved context, source-pin, playback, extended review and layout-persistence gaps remain visible.

## Unresolved UX questions

- Should local canvas arrangements persist, and should selection persist separately from layout? Current behavior intentionally resets on leaving scope.
- Should the generic shell inspector eventually host these selection details instead of a surface-local panel? Current generic host remains an unavailable projection placeholder.
- What server time basis, duration and safe media access should drive actual playback? Current local steps cannot answer that.
- Should unavailable Review tabs remain visible for discoverability or be hidden until projected capabilities arrive?
- What browser dimensions, touch behavior and screen-reader combinations does the Owner want as ongoing acceptance coverage? Human responsive/focus review is still deferred.

## Control-plane verification and current handoff

Hermes reran frontend-only validation after the writer exited. The current inventory is 16 frontend paths and 0 non-frontend paths. The writer-generated build was preserved outside the worktree; the three historical tracked dist files were restored byte-for-byte from HEAD. The final production build used `npm run build -- --outDir .ux-wave1-final-build`, then its output was preserved externally. Generated bundle names are not part of the current source delta.

Current results: 167/167 frontend tests pass across 23 files; lint exits 0 with 46 warnings; typecheck and production build pass. Dependency installation, installed tree, and manifest/lock consistency pass. The unchanged architecture guard still fails: exactly four new paths lack entries in the out-of-scope docs ledger (the two governance files and two Canvas test files); stale and duplicate ledger counts are zero. Guard tests are 69/70 passing, with only the repository positive control failing on this path-accounting condition. No guard was weakened. Alignment needs separate authorization for `docs/architecture/governance/frontend-product-path-classification-v1.tsv`.

Actual Firefox browser validation on the final production build passed 12 explicit checks and produced 11 screenshots, including loading/error/empty states and narrow-screen Canvas. All HTTP data was deliberately synthetic, served by an isolated read-only UX fixture server. No backend integration, decoded media playback, or human approval is claimed. One expected handled API 503 console event occurred during the deliberately failing scenario; no fatal runtime event was recorded.

Stable final evidence and screenshot gallery:
`/home/user/Documents/workspace/audit-runs/FRONTEND_PRODUCT_INTERACTION_AND_UX_WAVE_1/FINAL_REPORT.txt`
`/home/user/Documents/workspace/audit-runs/FRONTEND_PRODUCT_INTERACTION_AND_UX_WAVE_1/UX_REVIEW.html`

The mobile first viewport is dominated by stacked navigation, placeholders and the scope warning. The Canvas stage is below the fold; a separate scrolled screenshot shows it. Desktop NLE likewise devotes substantial space to empty side panels and revision metadata. These hierarchy questions remain open for human review, alongside the existing questions below. Local Canvas changes are lost when the surface unmounts, not only when the project identity changes.

HUMAN_REVIEW_REQUIRED=YES; HUMAN_REVIEW_STATUS=DEFERRED. No candidate commit, freeze, merge, remote update, or backend test was performed. The base is the pre-existing cached origin/main at `2b0c306467c98ca8b67da4ad5f7b228e52f7107a`; live canonical synchronization remains a pre-freeze prerequisite. Runtime writer route was Codex/ChatGPT subscription, account acc3, gpt-6-astra, high reasoning effort. An auxiliary analyst route failed with credit exhaustion and supplies no independent acceptance evidence. Hermes changed only this handoff documentation and generated-output placement after writer exit, not implementation source. Hermes also updated the frontend validation skill reference to document the Vite output-directory trap; the writer did not modify skills.

## Writer-stage verification (historical, superseded above)

Final command results and exact changed paths follow. Full command logs and machine-readable test reports are retained in `/tmp/ux-wave-1-*` for this session; no screenshot evidence is present.

The unchanged architecture guard reconciles every frontend file, including generated dist files, against `docs/architecture/governance/frontend-product-path-classification-v1.tsv`. That ledger is outside the authorized change scope. Required new tests/governance files and changed build artifact names need Owner-governed ledger alignment before this path gate can pass. This implementation does not weaken the guard, modify its baselines, or bypass the negative controls.


All commands below ran from `frontend/`, except `git diff --check` at the worktree root. The final Vitest JSON report and Node TAP report were parsed to check count arithmetic.

| Actual command | Exit/result | Evidence |
| --- | --- | --- |
| `npm run test -- --reporter=default --reporter=json --outputFile=/tmp/ux-wave-1-tests-final.json` | 0; 23 files, 167 tests: 167 passed, 0 failed, 0 skipped/todo | `/tmp/ux-wave-1-tests-final.log`, `/tmp/ux-wave-1-tests-final.json` |
| `npm run lint` | 0; 0 errors, 46 warnings, none in edited files | `/tmp/ux-wave-1-lint-final.log` |
| `npm run typecheck` | 0 | `/tmp/ux-wave-1-typecheck-final.log` |
| `npm run build -- --outDir dist` | 0; output confined to frontend/dist; main JS chunk size warning (601.17 kB minified) | `/tmp/ux-wave-1-build.log` |
| `npm run architecture:guard` | 1; all authority/bounded counts zero; 11 unclassified paths, 2 stale paths | `/tmp/ux-wave-1-architecture.log`, `/tmp/ux-wave-1-path-ledger.json` |
| `npm run architecture:guard:test` | 1; 70 tests: 69 passed, 1 failed, 0 cancelled/skipped/todo | `/tmp/ux-wave-1-architecture-tests.log` (TAP) |
| `git diff --check` | 0 | Final worktree whitespace check |

The one guard-test failure is `governed frontend passes with all authority counts at zero`: the repository positive control fails because of the unchanged external path ledger. Every other guard test, including negative controls, passed. There are no unexpected/missing governed runtime modules, API runtime modules, duplicate ledger paths, or authority-rule violations. The 11 new paths are the seven generated assets, two canvas tests and two governance documents listed below. The two stale ledger entries are the previous generated assets replaced by the required build. No guard or guard test was changed.

The first full Vitest run found two route-test assumptions affected by the new named canvas region and live project label. Assertions now target the named region and breadcrumb and additionally prove local title/selection reset after navigation; the complete rerun passed. An earlier targeted run passed 78 tests across five files. An initial npm invocation from the repository root failed before running tests and was corrected to the frontend working directory; it is not counted as a gate result.

The build replaced tracked dist outputs and emitted seven new assets; these remain local build artifacts for review, not published content. HEAD, branch and the pre-existing stash are unchanged. No final candidate SHA exists because this work is expressly UNFROZEN. Session evidence with source/artifact hashes and gate results is `/tmp/ux-wave-1-verification.json`.

## Exact changed files

Statuses are relative to the supplied base: M = modified, D = removed by the scoped build, A = new untracked file. Nothing outside frontend appears in this inventory.

| Status | Exact path | Scope classification |
| --- | --- | --- |
| D | `frontend/dist/assets/index-BMcgZaKx.css` | Generated frontend build output |
| D | `frontend/dist/assets/index-B_O_iL1c.js` | Generated frontend build output |
| M | `frontend/dist/index.html` | Generated frontend build output |
| M | `frontend/src/app/routeTree.test.tsx` | Interaction / regression test |
| M | `frontend/src/components/design-system/index.tsx` | Presentation implementation / accessibility |
| M | `frontend/src/product/canvas/WorkspaceCanvas.tsx` | Presentation implementation / accessibility |
| M | `frontend/src/product/canvas/model.ts` | Presentation implementation / accessibility |
| M | `frontend/src/product/review/ReviewWorkspace.test.tsx` | Interaction / regression test |
| M | `frontend/src/product/review/ReviewWorkspace.tsx` | Presentation implementation / accessibility |
| M | `frontend/src/product/timeline/NleWorkspace.test.tsx` | Interaction / regression test |
| M | `frontend/src/product/timeline/NleWorkspace.tsx` | Presentation implementation / accessibility |
| M | `frontend/src/product/timeline/SemanticDiff.tsx` | Presentation implementation / accessibility |
| M | `frontend/src/product/timeline/editor-state.test.ts` | Interaction / regression test |
| M | `frontend/src/product/timeline/editor-state.ts` | Presentation implementation / accessibility |
| M | `frontend/src/styles/foundation.css` | Presentation implementation / accessibility |
| A | `frontend/dist/assets/FoundationPages-J8Y6WSC5.js` | Generated frontend build output |
| A | `frontend/dist/assets/NleWorkspace-D8bkm_YR.js` | Generated frontend build output |
| A | `frontend/dist/assets/ReviewWorkspace-Db1vaNTi.js` | Generated frontend build output |
| A | `frontend/dist/assets/SemanticDiff-D33tyCVc.js` | Generated frontend build output |
| A | `frontend/dist/assets/WorkspaceCanvas-CYhDLQ93.js` | Generated frontend build output |
| A | `frontend/dist/assets/index-DmzUeVFh.js` | Generated frontend build output |
| A | `frontend/dist/assets/index-DvHXc8NM.css` | Generated frontend build output |
| A | `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` | Review governance / capability proposal |
| A | `frontend/governance/UX_WAVE_1_REVIEW.md` | Review governance / capability proposal |
| A | `frontend/src/product/canvas/WorkspaceCanvas.test.tsx` | Interaction / regression test |
| A | `frontend/src/product/canvas/model.test.ts` | Interaction / regression test |


## Owner continuation status — read-only recent Projects (2026-09-08)

This appendix preserves all historical review conclusions above. It records the current Owner direction; it is not a new acceptance ledger or Slice number.

- Notification focus correction `c1d45edff185a99f3a961a9b29598ea2b34d0f18` is Owner-accepted within its recorded Chromium scope; evidence `16848a46bf15e1cfff38ce869b86454f18a6e3b6`, public manifest `baa499b7eacdf6d1fe6df4d30b4617eeb14333f2fd780c716fc47d3084bf2a1e`. Its regression coverage is retained, not reopened.
- Current task: `FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1`. Selected existing `frontend-foundation-checkpoint-a-implementation-v1.md` → Compact surface design records → Workspace → PRIMARY_ACTIONS: “search Projects, inspect recent work”, bounded to the established Projects list route and read-only discovery/inspection. This is not the whole roadmap or canonical Project opening.
- Frontend behavior: local literal search, opaque status filter, deterministic name sort, reset, one shared read-only detail dialog, refresh/cancel/retry, bounded/limited snapshot and distinct unavailable/unknown/denied/unsupported/error/empty outcomes. Local presentation is not a server Revision or persisted result.
- Ordinary Projects loading remains unavailable until a correctly scoped authenticated adapter is supplied; the old dashboard wrapper cannot establish this consumer's identity/permission/receipt guarantees. The existing Home consumer is unchanged. Explicit localhost fixture data demonstrates the new flow without real authentication or transport.
- Dependency disposition: clarify existing `UXW1-001` / `FB-GAP-001` (related `FB-GAP-009`), add no requirement ID, endpoint or Operation contract. Future integration is a separately authorized single read-only recent-snapshot path.
- Status: unfrozen local feature increment; independent review required. Exact final identities, executed gates and additive delivery receipt belong to the external task report at `/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1/FINAL_REPORT.md`.
- Boundaries: no product freeze/commit/index change/merge/push/deployment, no real integration, no backend EP19 work; historical H4 and formal Slice1C status/publication gates unchanged.


## Owner adopted bounded technical review — recent Projects / V2 continuation

INDEPENDENT_TECHNICAL_REVIEW=PASS_BOUNDED
REVIEWED_IMPLEMENTATION_TREE=0b76ac9352ad40fc155c7203ed69f6362b0db89f
PROJECTS_UNCONFIGURED_BEHAVIOR=ACCEPTABLE_WITHIN_FRONTEND_ONLY_SCOPE
ADDITIONAL_PRODUCT_CORRECTION_REQUIRED=NO
REAL_BACKEND_INTEGRATION=NOT_ESTABLISHED
DETACHED_RECEIPT_PUBLICATION=BLOCKED_AS_REPORTED
PRODUCT_PUBLICATION=NOT_AUTHORIZED_BY_THIS_REVIEW

Owner adoption under FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V2. ChatGPT's review checked 141 public text payloads against the manifest, patch replay against 15 supplied final endpoints, 630 unique passing full-suite identities (54 additions/no removals versus 576), 232 unique passing targeted identities, 36 recorded Chromium checks bound to the final tree, 17 chunks reconstructing six JS artifacts, all eight build artifacts, and desktop-list/narrow-Chinese-detail screenshots. These are independently reviewed recorded results, not newly executed tests, full public-package verification by ChatGPT, or real-backend acceptance. Broader H4/Slice1C/release statuses are unchanged; this is an append to the existing status record, not another acceptance ledger.


### Current V2 increment status

`FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V2` selects the foundation plan's Compact surface design records → Operations → search/filter/sort and open backed projections, limited to existing `/operations/renders` and explicit single-Project safe RenderJobSummary inspection. Scope/acceptance and exact final verification live in the task-owned external `IMPLEMENTATION_REPORT_ZH.md`; independent review is required. No new Slice or release acceptance. Storage, accepted recent Projects and other accepted creator features remain unchanged. The original V1 detached receipt remains BLOCKED_AS_REPORTED, separate from this implementation.


## Owner adopted Render review — V3 continuation

INDEPENDENT_TECHNICAL_REVIEW=PASS_BOUNDED_WITH_REPORT_ERRATA
REVIEWED_IMPLEMENTATION_TREE=afc520c2fb8da37961cc6931e71743256b60a3e5
PRODUCT_CORRECTION_REQUIRED=NO
REPORT_ERRATA_REQUIRED=2
REAL_BACKEND_INTEGRATION=NOT_ESTABLISHED
PRODUCT_PUBLICATION=NOT_AUTHORIZED_BY_THIS_REVIEW

Owner adopts independently reviewed recorded results: 141 public text hashes, patch replay against 15 final endpoints, 680 unique passing full identities (50 additions/0 removals versus 630), 282 targeted identities, 33 browser checks, 6 JS reconstructed from 16 chunks, 8 build artifacts, desktop and narrow Chinese detail screenshots. This is not fresh execution, complete 219-file verification by ChatGPT, live integration or release approval.

Append-only errata: [/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/PRIOR_RENDER_REPORT_ERRATA.md](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/PRIOR_RENDER_REPORT_ERRATA.md). Correct proposed real-source key: `render.job.summary.query`; actual Render request scope: principalId, tenantId, sessionId, projectId, not Workspace. Prior anonymous Git verification remains complete as reported; raw HTTP remains 216/219 with three timeouts. Older Projects detached receipt stays blocked and is not retried. Historical reports and broader H4/Slice1C dispositions unchanged.

V3 independently authorizes one planned local Workflow node-arrangement increment, not canonical definition editing/validation/execution. Final technical result belongs in the task-owned V3 report; no product freeze or publication authority follows.
