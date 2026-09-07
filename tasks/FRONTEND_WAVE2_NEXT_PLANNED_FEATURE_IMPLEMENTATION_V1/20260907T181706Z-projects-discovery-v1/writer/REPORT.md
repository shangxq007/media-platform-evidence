# FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1 — writer report

## Outcome

Implemented one complete, read-only Workspace recent-project discovery and inspection increment on the existing `/w/$workspaceId/projects` route. Ordinary loading is fail-closed and performs no HTTP request. An explicit localhost-only `projectsFixture=1` query parameter enables a visibly simulated, in-memory demonstration.

The increment supports initial loading and cancellation, retry and refresh, literal name/description search, opaque projected-status filtering, deterministic name sorting with an ID tie-break, filter reset, loaded-empty versus local-no-match states, bounded/limited snapshot disclosure, and a read-only detail dialog using the existing `InteractionDialog` Escape/trap/focus restoration behavior. It does not expose Open, Create, persistence, or a canonical permission/action.

## Governance and repository state

- Applicable instruction file: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/AGENTS.md` (repository root; no nested instruction file applies to the edited paths).
- Precedence conflict: the durable root freeze-before-verification rule was overridden by the newer explicit Owner instruction requiring no commits or index writes. No commit, index, remote, integration, server, browser, build, package, dependency, Skill, Memory, credential, or documentation operation was performed.
- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`
- Branch: `agent/frontend-wave2-product-ux-v1`
- HEAD remained `f5e19cf53fd010eea2935dd29557e82a879e042c`; its parent is `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- Candidate SHA: none, as explicitly required. Post-integration state: not applicable.
- Existing stash preserved: `stash@{0}: On agent/roadmap22-executable-task-graph-worker-fabric-decision-recovery: phase15-pre-cip2-drift-gate-repair-safety`.
- Existing dirty work was preserved. At start it included governance docs/TSVs, frontend architecture guards, route/shell/design-system/interaction/localization/Canvas/Review/Timeline/Foundation/style work, plus the untracked notification increment. This executor did not restore, stage, commit, hide, or mutate the non-allowlisted work.

## Writable paths used and purpose

All product/test writes are in the ten-path allowlist. The Projects directory contains exactly the five permitted new files.

- `frontend/src/product/projects/source.ts` — frontend-only typed injection contract; explicit principal/tenant/session/Workspace/request ownership; strict recent-snapshot and failure parsing; existing `ProjectSummary` reuse; EffectiveAccess-based query disposition; local filtering and deterministic sorting; fail-closed unavailable source with no transport.
- `frontend/src/product/projects/source.test.ts` — contract, scope/receipt, duplicate/malformed, opaque status, sort/search, unavailable-source, localhost fixture, and EffectiveAccess regression tests.
- `frontend/src/product/projects/fixture.ts` — localhost-only, in-memory, visibly simulated fixture with no auth/storage/transport behavior and optional failure/boundary demonstrations.
- `frontend/src/product/projects/ProjectBrowser.tsx` — read-only Projects UI, request lifetime isolation, source/provider injection boundary, local filters, refresh/cancel/retry, exact failure/empty states, and one `LOCAL_EPHEMERAL` dispatcher for all project inspection entries.
- `frontend/src/product/projects/ProjectBrowser.test.tsx` — UI, localization, dialog identity/focus, failure clearing, source/scope changes, cancellation/unmount, late-reply and no-authority tests.
- `frontend/src/surfaces/FoundationPages.tsx` — only the legacy `ProjectListPage` body and its now-unused `useMemo` import were changed by this increment; it mounts `ProjectBrowser` inside the existing shared shell. `WorkspaceHomePage` was left unchanged. Other pre-existing dirty changes in this file were preserved.
- `frontend/src/localization/catalogs.ts` — English and Simplified Chinese text for the Projects increment.
- `frontend/src/localization/source-manifest.json` — registered 52 `shell.projects.*` platform-owned keys.
- `frontend/src/styles/foundation.css` — responsive Projects controls/cards/origin/detail styling using existing tokens and primitives.
- `frontend/src/app/routeTree.test.tsx` — added a runtime assertion that the already-registered Projects route reaches the fail-closed browser without consuming Workspace Home. The Home-link assertion remains present.

No changes were made to shared shell, shared dialog, Selection, notification, Canvas, Review, Timeline, command registry, route registration source, platform client, APIs, backend, configuration, package files, or documentation by this executor.

## Source and authority boundary

`ProjectsSource` is an application-source injection proposal, not an endpoint implementation or accepted backend DTO. Its scope includes `principalId`, `tenantId`, `sessionId`, `workspaceId`, and per-request `requestId`; responses must echo exact ownership. Success receipts are strict, reject duplicate IDs, reject an optional Project tenant mismatch, enforce the recent-snapshot limit, and never expose malformed or foreign content.

Query availability consumes the existing `EffectiveAccessEntry` and `isAvailable` semantics. No status string from `ProjectSummary.status` is interpreted as an access or protocol decision; projected statuses remain opaque display/local-filter values. The fixture’s access entry is scoped to its simulated source, persistently labelled as simulated, and cannot open or authorize a real Project.

There is no reliable ordinary adapter yet because the existing `workspace.getHome` wrapper binds only a Workspace ID to `/me/dashboard`; it does not provide this consumer with an explicit authenticated principal, tenant, session generation, request-ownership receipt, and established EffectiveAccess projection. Reading local/session storage would not establish those guarantees. Accordingly, ordinary Projects loading is unavailable, makes no HTTP request, and never falls back to a mock after a real injected source fails. Workspace Home intentionally continues to use its existing, separate projection unchanged.

## Public fixture URL parameters

The fixture activates only on hostnames `localhost`, `127.0.0.1`, or `[::1]`, and only when exactly one `projectsFixture=1` parameter is present.

- Primary demonstration: `/w/<workspaceId>/projects?projectsFixture=1`
- Empty recent snapshot: add `projectsFixtureEmpty=1`
- Limited one-item snapshot: add `projectsFixtureLimited=1`
- Access projection demonstrations: `projectsFixtureAccess=denied` or `projectsFixtureAccess=unknown`
- Source failure demonstrations: `projectsFixtureFailure=unavailable|denied|unknown|unsupported|error`

Unknown optional values do not broaden availability. Duplicate `projectsFixture` parameters, non-local hosts, or a value other than `1` leave the ordinary source unavailable.

## Verification evidence

Every test command used the required `npm test -- --configLoader=runner --no-cache ... --reporter=default --reporter=json --outputFile=<external unique path>` shape. JSON arithmetic below is taken from the preserved machine-readable report (`total = passed + failed + pending`). Logs, commands, exits, and JSON are in this writer directory.

| Attempt | Scope | Total | Passed | Failed | Pending | Exit | Result |
|---|---|---:|---:|---:|---:|---:|---|
| `red-01` | new source + UI tests against compileable behavioral scaffolds | 44 | 9 | 35 | 0 | 1 | expected RED; no missing-import failure |
| `green-01` | source + UI | 44 | 31 | 13 | 0 | 1 | preserved implementation attempt |
| `green-02` | source + UI | 44 | 43 | 1 | 0 | 1 | one ambiguous test query |
| `green-03` | source + UI | 44 | 44 | 0 | 0 | 0 | green |
| `green-04` | source + UI + route | 53 | 53 | 0 | 0 | 0 | green |
| `final-focused` | source + expanded UI + route | 54 | 53 | 1 | 0 | 1 | preserved over-strong late-result test expectation |
| `final-focused-02` | source + expanded UI + route | 54 | 54 | 0 | 0 | 0 | final green |
| `localization-01` | localization contract | 13 | 13 | 0 | 0 | 0 | green |

The first two ad-hoc targeted TypeScript invocations were preserved (`typecheck-01`, exit 2: missing CLI path/vite context; `typecheck-02`, exit 1: TypeScript disallows CLI `paths`). The first external focused config attempt was also preserved (`typecheck-03`, exit 2: inherited type roots resolved from the evidence directory). `typecheck-04` and the post-final-test `typecheck-05` both exited 0 using `writer/tsconfig.projects.json`. Focused lint `lint-01` exited 0 with one unused type-only import warning; that import was removed, and `lint-02` plus post-final-test `lint-03` exited 0 with no output. `git diff --check` exited 0.

Final focused JSON: `writer/final-focused-02-results.json`. Localization JSON: `writer/localization-01-results.json`.

## Backend dependency fields for Hermes records

- Request / linked records: `UXW1-001`; `FB-GAP-001` (Workspace-to-Project scoped resolution); related composition gap `FB-GAP-009`.
- User flow: find and inspect a bounded recent-project snapshot; canonical Project opening remains separate and unavailable.
- Current gap: no accepted consumer adapter binds authenticated principal, tenant, session generation, explicit Workspace, request ownership, EffectiveAccess, and non-disclosing failure semantics. The existing dashboard wrapper is insufficient for this lifecycle contract.
- Desired capability: authenticated Workspace recent-project membership projection with safe existing-`ProjectSummary` display fields and an explicit bounded/limited recent-snapshot boundary.
- Proposed application contract status: frontend consumption proposal only / UNAGREED; no endpoint, backend DTO, operation key, or backend acceptance claimed.
- Required response ownership: exact principal, tenant, session, Workspace, and request identity; reject stale, malformed, duplicate, over-limit, or mismatched receipts.
- Required outcomes: `ok`, `unavailable`, `denied`, `unknown`, `unsupported`, and `error`, with no resource content on failure.
- Blocking level: blocks reliable ordinary recent-Project loading and verified Project opening; does not block the fail-closed read-only frontend or existing Workspace Home.
- Mock behavior: explicit localhost-only simulated fixture; ordinary unconfigured unavailable; no HTTP and no real-source-failure fallback.
- Selective integration acceptance: use a separately accepted authenticated adapter/build; verify exact scope and request echo, limited labeling, failure clearing, logout and all identity/source transitions, and absence of Project-open/canonical mutation authority.
- Current status: frontend increment implemented and locally verified; real integration not established.

## Limitations

- No real authenticated adapter, backend endpoint, server DTO, full inventory traversal, cursor, or server-side search exists in this increment.
- Inspection shows only the returned `ProjectSummary` view. It is not a canonical Project detail, existence proof, membership proof, or opening permission.
- Local filters/sort operate only on the loaded recent snapshot and are reset when the keyed source context changes.
- Open, Create, pin/favorite, persistence, and canonical commands remain unavailable and were not mocked.
- Hermes owns final full gates, documentation/ledger updates, candidate freezing, and any later integration.
