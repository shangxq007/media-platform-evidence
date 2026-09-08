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
