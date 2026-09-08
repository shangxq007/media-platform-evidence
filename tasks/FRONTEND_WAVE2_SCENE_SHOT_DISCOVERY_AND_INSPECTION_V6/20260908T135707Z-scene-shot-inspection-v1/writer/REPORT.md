# V6 primary writer report — bounded Scene / Shot discovery and inspection

## Outcome and authority boundary

The bounded V6 frontend task is implemented. The registered Project Production route now consumes a read-only Scene/Shot browser. Its ordinary path is deliberately `UNAVAILABLE`: it sends no Production request and creates no principal, tenant, session, permission, Project relationship, or fixture. Tests and an external browser host can opt in only by explicitly injecting a complete identity/scope, EffectiveAccess projection, and source adapter.

This is a frontend-only **UNAGREED consumption interface**, not an accepted backend endpoint, DTO, permission key, or Production authority. No canonical or persistent write exists. No backend lane/process/runtime/evidence was touched. No dependency/build configuration, Skill/Memory, Git index/ref/history, remote, publication, or product build output was mutated.

## Governance and retained repository state

- Applicable instruction: repository-root `AGENTS.md`; no nested instruction file exists under the changed paths.
- Task override: the Owner's explicit no-freeze/no-product-Git-mutation rule supersedes the repository candidate-freeze requirement for this run. No other conflict was found.
- Branch at start and report: `agent/frontend-wave2-product-ux-v1`.
- HEAD retained: `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- Accepted dirty tree named by task: `f62687609a556dff204fc6939416c11abd45f945`.
- One pre-existing stash was observed and left untouched: `stash@{0}` on the Roadmap 22 branch.
- The intentional dirty baseline was preserved. There is no candidate commit/SHA because commits, staging, freezing, and index/ref writes were prohibited.

## Exact V6 changed paths

New bounded product paths:

1. `frontend/src/product/production/ProductionBrowser.tsx`
2. `frontend/src/product/production/ProductionBrowser.test.tsx`
3. `frontend/src/product/production/types.ts`
4. `frontend/src/product/production/model.ts`
5. `frontend/src/product/production/model.test.ts`
6. `frontend/src/product/production/source.tsx`
7. `frontend/src/product/production/simulatedSource.ts`
8. `frontend/src/product/production/production.css`

Existing allowlisted integration/governance paths:

9. `frontend/src/surfaces/FoundationPages.tsx`
10. `frontend/src/app/routeTree.test.tsx`
11. `frontend/src/localization/catalogs.ts`
12. `frontend/governance/UX_WAVE_1_REVIEW.md`
13. `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`
14. `docs/architecture/governance/frontend-product-information-architecture-v1.md`
15. `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv`
16. `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`

`frontend/src/localization/catalog.ts` was inspected and allowlisted but not changed. No unlisted product path was changed by V6.

## Source-to-contract mapping

| Requirement | Implementation / evidence |
|---|---|
| Exact supplied owner context | `ProductionScope` carries principal, tenant, session, Workspace, and Project; receipts echo scope plus request ID. Missing principal/tenant remains unknown/fail-closed. |
| Existing access authority | Real sources require the exact frontend-proposed query key with a `SERVER` EffectiveAccess projection. Fixture sources require the separate fixture key and `DEVELOPMENT_FAIL_CLOSED`. `surface.production.view` or visibility alone never grants the read. |
| Source ownership and retirement | Adapter identity plus every scope/access field key the session. Generation, AbortController, live/unmount, cancellation, source replacement, access replacement, and context changes reject late results and clear old data. |
| Strict data and relations | Zod strict schemas reject unknown fields. IDs are globally unambiguous across Scene/Shot; every Shot has exactly one explicit existing Scene relation; duplicate/orphan relations, cross-Project entities/references, duplicate references, excess bounds, and mismatched receipts fail closed. |
| Bounded/version-aware disclosure | Required projection version plus `complete` or `bounded` metadata; explicit stale failure; no total/cursor inferred. Empty snapshot, no matches, no related Shots, missing field, and supplied-empty field are distinct. |
| Read-only workflow | Local Scene ID/name/description search, opaque supplied status filter, stable name+ID sort, reset, Scene browsing, explicit related Shot list, and shared-dialog supplied-field inspection. No create/delete/rename/reorder/status/assignment/task/workflow/render/preference operation exists. |
| Safe references | Only existing shared reference kinds with the same Project ID pass validation. Detail shows a local safe-reference inspection or explicit unsupported explanation. It creates no link and consumes no external/storage/download URL. Destination permission remains independent. |
| Selection and focus | The existing Selection owner is registered with an empty adapter because Scene/Shot are not legitimate `NODE`/`CLIP`/`LANE` kinds; prior-surface selection retires without semantic mislabelling. Shared `InteractionDialog` provides native launcher-focus return and focus containment. Async completion never moves focus. |
| Localization and responsive behavior | Complete EN/zh-CN controls/states in the existing catalog; two-column desktop/tablet layout collapses below 760px; long supplied IDs wrap. Supplied opaque values are not translated or interpreted. |
| Registered consumer | `ProductionPage` retains the existing typed Production route/ProjectFrame and passes only its exact route Workspace/Project expectation. Without an injected source it renders unavailable and does not query. |

## Fixture injection API for the final external browser host

There is no query-string or automatic localhost fixture hook. The browser host must import and inject explicitly:

```tsx
import { ProductionBrowser } from './src/product/production/ProductionBrowser'
import { createSimulatedProductionSource } from './src/product/production/simulatedSource'
import { ProductionSourceProvider } from './src/product/production/source'
import { SelectionProvider } from './src/interaction/SelectionContext'

const scope = {
  principalId: 'browser-controlled-principal',
  tenantId: 'browser-controlled-tenant',
  sessionId: 'browser-controlled-session',
  workspaceId: 'browser-workspace',
  projectId: 'browser-project',
}
const source = createSimulatedProductionSource({ scope })

<SelectionProvider scope={{ workspaceId: scope.workspaceId, projectId: scope.projectId, surfaceId: 'production' }}>
  <ProductionSourceProvider source={source}>
    <ProductionBrowser expectedScope={scope} />
  </ProductionSourceProvider>
</SelectionProvider>
```

The direct `source={source}` prop is an equivalent explicit injection seam. Useful deterministic fixture options are `empty: true`, `limit: 3`, `failure: 'error'`, `failure: 'stale'`, and `accessStatus: 'POLICY_DENIED'`. The scope argument has no identity defaults and rejects incomplete identity/scope at runtime.

## Actual writer verification

All runs used the installed locked dependency tree. Test runs used Vitest's `runner` config loader, `--no-cache`, and JSON reporters under this external writer directory.

### RED

Initial import-boundary RED: native exit 1; two failed suites before modules existed, preserved in `writer/red/`.

Meaningful behavioral RED command:

```text
./node_modules/.bin/vitest run src/product/production/model.test.ts src/product/production/ProductionBrowser.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/red-behavioral/vitest.json
```

Result: native exit 1; 54 total = 24 passed + 30 failed + 0 skipped/todo. Assertions executed against inert pre-implementation scaffolds. JSON, log, exact command, native exit, and checked arithmetic are retained in `writer/red-behavioral/`.

### GREEN / affected

Final affected command:

```text
./node_modules/.bin/vitest run src/product/production src/components/app-shell/AppShell.test.tsx src/interaction src/localization/localization.test.tsx src/app/routeTree.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/affected-final-04/vitest.json
```

Result: native exit 0; 20/20 suites; 188 total = 188 passed + 0 failed + 0 skipped/todo. JSON, log, exact command, native exit, and checked arithmetic are retained in `writer/affected-final-04/`.

Additional checks:

- `npm run typecheck`: native exit 0; final log/exit under `writer/typecheck/`.
- `./node_modules/.bin/eslint src/product/production src/surfaces/FoundationPages.tsx src/app/routeTree.test.tsx src/localization/catalogs.ts`: native exit 0; no diagnostics; evidence under `writer/lint-affected/`.
- Allowlisted `git diff --check`: exit 0, no output.

Intermediate failed and passing attempts remain preserved; no result was overwritten or invented.

## Governance appendices completed

- Appended the exact Owner-adopted V5 review tokens and accepted limits; historical V5 724 full / 299 targeted / +20 −0 / seven gates / 32 browser checks are explicitly not fresh V6 evidence.
- Appended the Owner priority order to the existing IA planning record: Scene/Shot > Render observability > Workflow UX > bounded NLE editing > Agent-assisted creative; only Scene/Shot is authorized.
- Reused FB-GAP-007 in both the existing TSV and gap ledger, with FB-GAP-001/002/004/008 retained for Project/access/resource/reference boundaries.
- Recorded one future pinned frontend/backend controlled Project read with authorized/denied/error/stale cases and zero writes. It is a proposal, not integration or backend authorization.
- Added only current append-forward production paths to the current governed-scope ledger. Historical H4 classification was untouched.

## Outstanding and controller-owned work

- Real authentication, Project membership, EffectiveAccess, a backend adapter/endpoint/DTO, and real referenced-resource destination checks remain unestablished.
- Tasks, assignments, milestones, workload, ordering, writes, media duration/progress, ownership, canonical Scene/Shot semantics, and arbitrary URL access remain out of scope.
- Hermes owns final exact-tree/index preservation, full 724-baseline identity accounting, seven gates, external build, real browser fixture-host run, screenshots, keyboard/narrow recovery scenarios, package/replay/manifest, and independent acceptance review.
- Physical device, IME, screen-reader, real backend, and publication acceptance are not claimed.

## Append-forward controller-review corrections

Correction authority: `CONTROLLER_REVIEW_REQUEST.md`. The original report was preserved before correction as `writer/REPORT_INITIAL.md`; both its source and preserved copy had SHA-256 `08d27407100f04abeeb76d41fe730cbbab0d6f5c3cdcd9ef1bf138134273b1cf` at preservation. This section supersedes only the four source-contract claims identified below. It does not replace or upgrade the original task, real integration, browser, build, publication, or acceptance status.

### Exact corrections applied

1. **Existing InteractionStore owner lifetime now fences Production data.** `ProductionBrowser` observes both `useInteractionStore()` and `useSelection()`. The empty Scene/Shot-safe surface adapter moved outside the source-keyed request session, so source replacement does not falsely retire the shared owner. `pagehide`, explicit owner retirement, or the same-store lifetime replacement synchronously removes the ready/loading subtree, aborts its controller, and rejects late replies. The retired store shows only `Production context retired`; it cannot requery. A fresh Selection store created by the existing `pageshow` mechanism remounts and rebinds the source. This is unit-tested lifecycle behavior, not physical bfcache qualification.
2. **No fictional real-server key remains.** The former fixed `production.scene-shot.query` requirement is removed. A real source now supplies `readAccessBinding: { kind: 'HOST_AGREED', accessKey }`, and readiness requires that exact non-malformed key to equal the supplied EffectiveAccess entry key with `SERVER` provenance. A mismatch, development provenance, or the generic `surface.production.view` visibility key remains unknown/fail-closed. `frontend.unagreed.production.scene-shot.read` is only an unavailable local label. `test-only.frontend-unagreed.production.scene-shot.read` is only simulated/test vocabulary and can never satisfy a real-origin source.
3. **All required request identities validate before adapter invocation.** Principal, tenant, session, Workspace, and Project must each be nonempty and contain no whitespace or control characters. Validation neither trims nor rewrites identifiers. Invalid source or expected route scope resolves to unknown before `readProject` is called. The strict receipt schema uses the same identity predicate.
4. **Reset is stable and always present.** The controls retain one Reset button for complete, bounded, matching, and no-match loaded results. It advertises `aria-disabled` when already at defaults but stays in the DOM; when query/status/order differs, activating it restores all defaults while preserving focus on that same button. The original no-match Reset behavior remains covered.

### Corrected source and fixture contract

The simulated external host API in the original report is unchanged: `createSimulatedProductionSource({ scope })` creates its explicitly test-only binding, and `ProductionSourceProvider` injects it. There is still no URL, localhost, storage, or automatic fixture path.

A future real host—not the V6 fixture—must construct the binding from its actually agreed server projection and matching access entry:

```ts
const source: ProductionSource = {
  scope: actualAuthenticatedScope,
  access: actualServerEffectiveAccess,
  readAccessBinding: {
    kind: 'HOST_AGREED',
    accessKey: actualServerEffectiveAccess.key,
  },
  adapter: agreedReadOnlyProductionAdapter,
}
```

V6 provides no value for `actualServerEffectiveAccess.key`, no endpoint, and no permission interpretation. Host agreement, Project membership, destination access, and backend contract acceptance remain external and unestablished.

### Added correction tests

- Arbitrary matching host-agreed `SERVER` binding succeeds; mismatched binding, development provenance, and generic surface visibility fail closed.
- Each malformed required field—principal, tenant, session, Workspace, Project—produces unknown and sends zero adapter reads.
- A ready snapshot clears on `pagehide`; a pending owner-retired result cannot reappear; only the existing fresh `pageshow` store rebinds.
- Existing non-vacuous source/adapter replacement and unmount late-reply tests remain green.
- Reset is exercised with a populated matching status filter, returns all defaults/results, and retains focus; the no-match Reset scenario remains green.

### Correction RED / GREEN evidence

Correction RED command:

```text
./node_modules/.bin/vitest run src/product/production/model.test.ts src/product/production/ProductionBrowser.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/corrections/red/vitest.json
```

Result: native exit 1; 70 total = 58 passed + 12 failed + 0 skipped/todo. The 12 behavioral failures directly covered missing stable Reset, owner-retirement clearing/late-result fencing, host-supplied binding, and malformed required contexts. JSON, log, command, exit, and arithmetic receipt are preserved under `writer/corrections/red/`.

Final correction-focused GREEN used the same two test files and runner flags with output under `writer/corrections/green-final-02/`: native exit 0; 5/5 suites; 70 total = 70 passed + 0 failed + 0 skipped/todo.

Final broader affected command:

```text
./node_modules/.bin/vitest run src/product/production src/components/app-shell/AppShell.test.tsx src/interaction src/localization/localization.test.tsx src/app/routeTree.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/corrections/affected-final-03/vitest.json
```

Result: native exit 0; 20/20 suites; 202 total = 202 passed + 0 failed + 0 skipped/todo.

Current source checks:

- `npm run typecheck`: native exit 0; final evidence in `writer/corrections/typecheck/typecheck-final-03.log` and `native-exit-final-03.txt`.
- `./node_modules/.bin/eslint src/product/production src/surfaces/FoundationPages.tsx src/app/routeTree.test.tsx src/localization/catalogs.ts`: native exit 0 with no diagnostics; final evidence in `writer/corrections/lint/lint-final-02.log` and `native-exit-final-02.txt`.
- An intermediate lint exit 1 for the initial control-range regex is preserved; the equivalent character-code implementation removed that style violation without weakening identity validation.
- Allowlisted whitespace/diff check: exit 0, no output.

Correction product changes remained within the original allowlist: Production browser/model/types/simulated source/tests/CSS, existing localization catalog, backend request TSV, and backend gap ledger. No Git index/ref/history mutation, backend work, dependency/build configuration, Skill/Memory change, build, browser run, remote operation, or publication occurred. The controller retains final gate/build/browser/package authority.

## Append-forward final bounded review follow-up

Follow-up authority: `FINAL_BOUNDED_REVIEW_FOLLOWUP.md`. This appendix adds two final checks/corrections only. `writer/REPORT_INITIAL.md` remains byte-identical at SHA-256 `08d27407100f04abeeb76d41fe730cbbab0d6f5c3cdcd9ef1bf138134273b1cf`; all original and first-correction evidence remains preserved.

### A. StrictMode host reproduction and bounded correction

The main entry renders the router beneath React `StrictMode`; AppShell provides the existing `SelectionProvider` below that boundary. A non-vacuous component regression reproduced the actual lifecycle shape with StrictMode around Localization, SelectionProvider, and ProductionBrowser using a valid real-origin test source.

Pre-correction result: native exit 1. The selected test failed because the initial host remained permanently on `Production context retired` and never rendered `Connected Scene`. The JSON reporter contains 29 discovered tests: 1 selected failed and 28 were skipped by the exact name filter. Raw command, log, JSON, native exit, and count receipt are under `writer/final-followup/strictmode-red/`.

Correction: ProductionBrowser now reconciles its captured lifetime from `store.getSnapshot()` only when its existing surface-adapter layout effect is set up/replayed. StrictMode cleanup/setup can therefore accept the re-registered same-store lifetime. Explicit owner or document retirement does not rerun that effect, so it still synchronously renders the retired state and aborts/rejects pending results. Existing direct-owner, `pagehide`/fresh-`pageshow`, adapter/source replacement, and unmount tests remain unchanged and green. No shared Selection file or lifecycle authority changed; this is not physical bfcache qualification.

### B. Distinct invalid snapshot disposition

Pre-correction result: native exit 1. The selected malformed-relation test failed because the current generic `Production snapshot error` heading did not satisfy the required `Invalid production snapshot` disposition. The JSON reporter contains 30 discovered tests: 1 selected failed and 29 were skipped by the exact name filter. Raw evidence is under `writer/final-followup/invalid-red/`.

Correction: adapter invocation and frontend receipt parsing now have separate guarded stages:

- a thrown/rejected source request remains the existing retryable `error` state;
- a valid source `error` receipt remains that same retryable `error` state;
- strict schema, ownership, bound, relation, or reference validation failure becomes local-only `invalid`;
- explicit source `stale` remains unchanged and separate.

`invalid` is not added to the backend receipt/status contract. It is a frontend validation disposition with localized EN/zh-CN title/body, no returned content or raw exception disclosure, and the existing safe Retry control requests a fresh snapshot. A new rejected-source test proves transport detail remains hidden, the Error heading remains distinct, and Retry stays available. The newly introduced malformed-relation assertion now proves Invalid, Retry, and old-content removal.

### Final follow-up results

Focused GREEN:

```text
./node_modules/.bin/vitest run src/product/production/model.test.ts src/product/production/ProductionBrowser.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/final-followup/green-01/vitest.json
```

Native exit 0; 5/5 suites; 72 total = 72 passed + 0 failed + 0 skipped/todo.

Affected GREEN:

```text
./node_modules/.bin/vitest run src/product/production src/components/app-shell/AppShell.test.tsx src/interaction src/localization/localization.test.tsx src/app/routeTree.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SCENE_SHOT_DISCOVERY_AND_INSPECTION_V6/writer/final-followup/affected-final/vitest.json
```

Native exit 0; 20/20 suites; 204 total = 204 passed + 0 failed + 0 skipped/todo.

Current source checks:

- `npm run typecheck`: native exit 0; raw log/exit/command under `writer/final-followup/typecheck/`.
- `./node_modules/.bin/eslint src/product/production src/surfaces/FoundationPages.tsx src/app/routeTree.test.tsx src/localization/catalogs.ts`: native exit 0 with no diagnostics; raw evidence under `writer/final-followup/lint/`.
- Allowlisted whitespace/diff check: exit 0, no output.

Follow-up product edits are limited to original-allowlist `ProductionBrowser.tsx`, `ProductionBrowser.test.tsx`, and `localization/catalogs.ts`. No Git index/ref/history mutation, backend/shared-Selection/Skill/Memory work, dependency/build configuration, build, browser run, remote operation, or publication occurred. The controller retains final exact-tree gates and native browser/package authority after writer exit.
