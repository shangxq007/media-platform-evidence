# V5 Canvas local title/position undo/redo — writer report

Implementation completed in the existing dirty worktree. This is writer implementation and focused-test evidence, not a freeze or independent acceptance decision. Hermes owns the seven final gates, build and browser verification.

## Scope and preservation

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
- Branch: `agent/frontend-wave2-product-ux-v1`.
- Unchanged HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`; unchanged parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- Owner-supplied accepted dirty-content baseline: `66b3b9abd9b79161c8f4c902acfd2acb336a387a`. It is not HEAD and was not independently reaccepted here.
- Root AGENTS and the selection/scope record were read before editing. Ancestor paths and the frontend tree yielded no additional AGENTS files. Root AGENTS governs all changed paths. Copies of the read instructions are included in this evidence directory.
- Explicit Owner authorization supersedes root freeze-before-verification and candidate-commit requirements: no candidate SHA was created, no Git mutation commands were run, and no integration or cleanup was performed. Any durable alignment of that instruction belongs to a separate Owner governance task, outside this writer scope. The selection record's backend-documentation disposition was read as decision context; the latest Owner prohibition on external documentation edits governs this implementation.
- `initial-state.json` and `final-state.json` record branch, HEAD/parent, worktree, dirty status, stash and index diff. These Git observations compare equal. The pre-existing stash and all dirty paths remain. The initial allowed files are copied under `before/`; `incremental.patch` describes only this task's additions to that dirty content. All four pre-existing test files remain exact byte prefixes of their final versions: no existing tests renamed, skipped, removed or weakened.
- All source writes were in place using file append or Python `Path.write_text`, with no rename/replacement operations. No new source files, backend/build/config/guard edits, dependency installs, servers, remote operations, Skill/Memory writes, or external documentation edits occurred. Only writer evidence was created outside the source allowlist.

## Exact changed paths

- `frontend/src/product/canvas/model.ts` — Canvas local history and existing interaction integration.
- `frontend/src/product/canvas/model.test.ts` — focused behavior tests.
- `frontend/src/product/canvas/WorkspaceCanvas.tsx` — Canvas local history and existing interaction integration.
- `frontend/src/product/canvas/WorkspaceCanvas.test.tsx` — focused behavior tests.
- `frontend/src/interaction/model.ts` — Canvas local history and existing interaction integration.
- `frontend/src/interaction/model.test.ts` — focused behavior tests.
- `frontend/src/interaction/InteractionShell.tsx` — Canvas local history and existing interaction integration.
- `frontend/src/interaction/InteractionShell.test.tsx` — focused behavior tests.
- `frontend/src/localization/catalogs.ts` — localization contract.
- `frontend/src/localization/source-manifest.json` — localization contract.
- `frontend/src/styles/foundation.css` — presentation styles.

`final-state.json` contains before/after SHA-256 values and scope classifications for all 11 changed files. `source-manifest.json` gained only the five required Canvas message keys; catalogs provide matching EN/zh-CN definitions and interpolation parameters.

## Behavior and architecture

History is owned solely by `CanvasSession`, held in its local ref. Each entry contains before/after arrays of local `presentationId`, `title`, `x` and `y`. No semantic reference IDs, entity identity, references, edges, camera, Selection state, proposals or canonical revisions are retained. Restore joins by local presentation key and overlays only title/X/Y onto the current projection, preserving current references, edges and camera.

The combined undo/redo timeline retains at most 50 edit entries. Each successful title input change is one edit, including intermediate typing values; there is no blur/word coalescing. Each Inspector coordinate input or keyboard move records one changed projection. A committed drag, including a multi-node group, records one atomic entry. Previews, canceled gestures, return-to-origin/no-op drags, equal/truncated/clamped unchanged values, invalid placements, selection, pan/zoom/fit/reveal and other camera changes record none. A new actual edit clears redo; no-ops and camera/Selection changes preserve it. The toolbar visibly explains the 50-edit session scope, unsaved behavior, rename granularity, group-drag granularity and current undo/redo counts including zero.

Undo/redo use the existing `WORKSPACE_PRESENTATION` union, dispatcher and active adapter. The adapter exposes live support from session history, so dispatch rejects unavailable actions even before a stale rendered command is replaced. History commands need no selected target; they can restore earlier local edits while retaining the current selection membership and primary, or while selection is empty. Other surfaces reject history intents. Existing canonical dispatch rejection remains first, and AppShell canonical palette actions remain disabled.

After adapter restore, existing synchronous store reconciliation refreshes Inspector/Selection projections and advances the store revision when its selected projection or supported capabilities change. Tests assert immediate selected coordinates in the same dispatch turn and rejection of pre-undo/pre-redo proposals. No new Selection authority, registry, global store or global keyboard layer was added.

Undo/redo first discard a live preview and release capture; a retained pointer completion cannot commit that canceled drag. Both history restoration and new local edits recheck ownership/projection after capture release, covering synchronous retirement or intervening edits. History clears on ownership/adapter/document retirement, effect cleanup/unmount, workspace/project navigation and provider-store replacement. Retired adapters reject retained edit/restoration work; retired dispatchers reject history. A resumed page gets empty history under a new lifetime; the existing Canvas presentation may remain after pagehide/pageshow, but its previous history cannot be revived. A fresh edit under the new owner is undoable.

## Action IDs and selectors

| Entry | Identifier / selector |
| --- | --- |
| Dispatcher undo | `{ category: 'WORKSPACE_PRESENTATION', type: 'undo-local' }` |
| Dispatcher redo | `{ category: 'WORKSPACE_PRESENTATION', type: 'redo-local' }` |
| Contextual palette | `canvas.undo-local`, `canvas.redo-local`, discovered through existing `useSelectionCommands` only while available |
| Undo toolbar | `[data-canvas-history="undo"]`; EN `Undo local edit`; zh-CN `撤销本地编辑` |
| Redo toolbar | `[data-canvas-history="redo"]`; EN `Redo local edit`; zh-CN `重做本地编辑` |
| History group | role `group`, EN `Local edit history`, zh-CN `本地编辑历史` |
| History counts | `#canvas-history-status`, role `status`; referenced with `aria-describedby` |
| Existing projections | `[data-canvas-node]`, Inspector `Local title` / `Local X` / `Local Y` |

Buttons reuse shared Button and Canvas toolbar primitives/styles. They remain native buttons in the Tab order with `aria-disabled` when exhausted, while dispatch guards activation. Last undo/redo activation preserves focused button identity. Native text editing undo is untouched; no global undo/redo shortcuts were introduced. Existing flexible toolbar wrapping is reused for narrow layouts.

## Native TDD chronology and results

Each attempt has its own unchanged raw `.json`, `.log`, `.exit`, and `.command.json`. `test-attempts.json` gives exact argument vectors and reconciled counts. All executions used the existing native executable from `frontend/`:

`node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=<writer>/<attempt>.json <focused test paths>`

| Attempt | Exit | Total | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 01-title-position-red | 1 | 98 | 97 | 1 | 0 | 0 |
| 02-title-position-green | 0 | 150 | 150 | 0 | 0 | 0 |
| 03-palette-red | 1 | 46 | 45 | 1 | 0 | 0 |
| 04-palette-green | 0 | 46 | 46 | 0 | 0 | 0 |
| 05-retirement-red | 1 | 101 | 98 | 3 | 0 | 0 |
| 06-retirement-green | 0 | 147 | 147 | 0 | 0 | 0 |
| 07-history-boundaries | 0 | 158 | 158 | 0 | 0 | 0 |
| 08-release-ownership-red | 1 | 105 | 104 | 1 | 0 | 0 |
| 09-release-ownership-green | 0 | 151 | 151 | 0 | 0 | 0 |
| 10-lifecycle-consumers | 0 | 171 | 171 | 0 | 0 | 0 |
| 11-projection-consumers | 0 | 130 | 130 | 0 | 0 | 0 |
| 12-focused-final | 0 | 271 | 271 | 0 | 0 | 0 |

1. **01 → 02:** Added one end-to-end title/position history behavior test before production edits. Native red was the missing Undo button (97 existing tests passed). Implemented bounded history projection helpers, session recording/restoration, dispatcher intents, toolbar, localization and unavailable styling; native green passed 150 tests across Canvas component/model and interaction model.
2. **03 → 04:** Added the shared AppShell palette/Inspector/Agent/canonical-boundary behavior test. Native red was missing contextual Undo discovery. Added discovery through `useSelectionCommands`; native green passed 46. Two new test selectors later in that scenario were corrected to the existing labels `Apply local presentation` and `Close Agent conversation`; no assertion was removed or weakened. Review also corrected history interpolation parameter metadata and replaced an ES2022 `.at` call with an ES2020-compatible slice.
3. **05 → 06:** Added retirement behavior for owner, document and adapter. Native red showed retained history counts in all three cases. Added synchronous history/lifetime clearing and retained-adapter guards; native green passed 147 tests.
4. **07:** Expanded behavior coverage for the 50-entry session bound, redo/no-op branching, atomic group gestures, preview cancellation, Selection/camera exclusion, projection-only records and live dispatcher availability/canonical/other-surface rejection. All 158 passed without a production change.
5. **08 → 09:** Added the synchronous capture-release retirement test. Native red showed the rename dispatcher incorrectly reported success after ownership retired. Moved local recording/publication behind a post-release ownership/projection check and returned edit rejection through the existing adapter. Split the two history action variants into separate discriminated union members. Native green passed 151.
6. **10:** Added retained contextual-command availability, context/unmount/pagehide/pageshow, retirement during undo capture release, Chinese/safe title and native-control contract tests; 171 passed including localization.
7. **11:** Added same-turn shared projection/proposal invalidation and unselected history restoration with preserved camera and redo; 130 passed.
8. **12:** Final focused run of Canvas model/component, interaction model/shell, localization and existing AppShell tests: **271 total = 271 passed + 0 failed + 0 errors + 0 skipped**, exit 0. `final-test-counts.json` contains per-file assertion counts checked against the raw report.

## Limits and handoff

- Session-only title/position edits; no saved history, canonical undo, backend calls, new persistence or cross-surface history.
- Per-input rename history is intentional and visible in both languages. History older than the latest 50 edits is unavailable.
- Happy-dom component tests simulate pointer capture and the click resulting from native key activation. They verify focus identity, Tab eligibility, nonprevented Enter/Space, guarded exhaustion, safe text and bilingual copy; they do not establish real browser pointer routing, actual native keyboard default behavior, responsive layout or accessibility acceptance. Hermes must verify those in the browser.
- No full suite, typecheck, lint, architecture/governance gates, build, browser/server or seven-gate acceptance was run by this writer. Existing AppShell canonical behavior was covered by its focused tests and the new shared-consumer test.
- No source edits follow this report. No freeze, commit, acceptance seal or independent acceptance claim is made.
