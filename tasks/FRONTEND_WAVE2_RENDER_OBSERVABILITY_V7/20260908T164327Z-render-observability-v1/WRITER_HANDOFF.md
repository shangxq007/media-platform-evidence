# FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7 writer handoff

## Result and review status

The bounded frontend implementation is complete in the authorized dirty worktree and stops before Workflow UX. It extends the existing `/operations/renders` Render browser, source boundary, route test, localization and governance records. It creates no parallel center, route, permission registry, transport, backend contract or canonical authority.

This is an unfrozen writer result. Independent review is **REQUIRED**. It is not a final accepted implementation, backend integration, release, publication, or product acceptance.

Repository state remains:

- worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`
- branch: `refs/heads/agent/frontend-wave2-product-ux-v1`
- HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`
- HEAD parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`
- recovered accepted working tree: `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`
- real index: unchanged from the recovery receipt
- commit/freeze/stage/stash/ref/merge/push/publish: not performed
- build/browser/full-final gates: not run; owned by the controller/Hermes

The root `AGENTS.md` freeze-before-verification rule conflicts with the newer Owner `NO COMMIT/FREEZE` task authorization. The Owner override was applied and is recorded in `SCOPE_AND_SOURCE_MAP.md`; no candidate SHA was created.

## Exact changed paths from the accepted working tree

1. `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`
2. `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv`
3. `docs/architecture/governance/frontend-product-information-architecture-v1.md`
4. `docs/architecture/governance/frontend-product-path-classification-v1.tsv`
5. `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`
6. `frontend/governance/UX_WAVE_1_REVIEW.md`
7. `frontend/src/app/routeTree.test.tsx`
8. `frontend/src/localization/catalogs.ts`
9. `frontend/src/localization/source-manifest.json`
10. `frontend/src/product/render-browser/RenderBrowser.test.tsx`
11. `frontend/src/product/render-browser/RenderBrowser.tsx`
12. `frontend/src/product/render-browser/fixture.ts`
13. `frontend/src/product/render-browser/render-browser.css` (new)
14. `frontend/src/product/render-browser/source.test.ts`
15. `frontend/src/product/render-browser/source.ts`

`writer-runs/16-scope-post-correction.log` proves exactly these 15 paths differ from the accepted working tree: no deletion, no outside-allowlist change, all allowlisted paths changed, 990 baseline paths outside the allowlist unchanged, HEAD/branch/index unchanged. The new stylesheet is registered once in both current governed ledgers. Historical H4/guard records were not changed.

## Implemented behavior

- Discover/search supplied Render ID or name; filter only by source-supported literal statuses; stable case-insensitive name then ID sort; always reachable Reset.
- One stable Refresh/Cancel/Retry control. Filters and bounded list scroll intent persist across refresh/retry. Cancel, replacement and failure clear returned content. Shared dialog close/Escape returns focus to the launcher.
- Read-only summary shows only supplied ID/name/status/source times/progress. It does not infer a Project, total, pagination, order, source time, progress or ETA.
- Detail shows Render/source identity, Project, literal status, Render/source version, created/updated/started/ended source times, separately labelled last successful frontend fetch time, supplied progress/stage, related task/status/version, task failure, attempts and Artifacts.
- Percentage is derived only when value/total are finite, value is nonnegative and no greater than a positive total, and supplied units match. Invalid values are shown as invalid; they are never clamped. Missing total is shown as partial. No timer, animation or polling exists.
- Unknown status remains literal and neutral; it is never classified as success/failure and never enables an action.
- Task and attempt statuses remain separate. Attempt history is never generated; only supplied ordinals and explicit parent/retry links appear. Missing, empty, bounded and complete histories remain distinct.
- Failure display is limited to validated user-safe summary/code/time. Credential-like content, private filesystem paths, raw traceback/stack patterns, unsafe controls and excessive lengths fail the entire receipt closed. All presentation uses React text nodes; no HTML interpretation exists.
- Artifact display includes only supplied ID/name/type/literal availability/version/explicit task link and metadata-access state. Missing, empty, bounded, complete, denied, unavailable, unknown, stale and inspectable-metadata states are distinct. No arbitrary URL, storage path, signed URL, download or open control exists. Task visibility and inspectable metadata do not grant Artifact read.
- Loading, cancelled, unavailable, denied, unknown, unsupported, transport error, invalid receipt, invalid relationship, stale, empty snapshot, no match and detail-not-found are distinct. No failed request retains old returned content or falls back to fixture data.
- Principal, tenant, session, Project, complete EffectiveAccess projection, binding, adapter/source and Selection owner lifetime participate in ownership. Replacement, cancel, unmount and explicit owner/document retirement abort and fence old generations. StrictMode re-registration works; a fresh `pageshow` owner rebinds while explicit retirement clears ready and pending data.
- English and zh-CN cover the complete workflow; source values stay literal.
- No render submit/execution cancel/task retry/rerender/Artifact delete/publish/Workflow/Timeline/canonical write, provider/worker call, notification, billing or quota action exists.

## Frontend-only contract and real-integration limits

The inspected real application contract `frontend/src/contracts/app/render-job.ts` is the existing five-field `RenderJobSummary`; it does not contain the coherent relationships required here. V7 therefore declares the minimum richer envelope explicitly as **FRONTEND UNAGREED** in `product/render-browser/source.ts`. It does not claim an agreed endpoint, permission key or server DTO.

The proposal echoes `principalId`, `tenantId`, `sessionId`, `projectId` and `requestId`; success supplies a bounded/complete Project snapshot, projection version/freshness/source update time/source-supported statuses, and strict Render/source/task/attempt/failure/Artifact records. Validation covers receipt ownership, malformed identity, Project ownership, duplicate Render/attempt/Artifact IDs and ordinals, finite numeric values, ISO source times and ordering, result bounds, parent/retry links, and task links.

A real source is query-ready only when the host explicitly supplies an arbitrary separately agreed read binding whose key exactly matches a `SERVER` EffectiveAccess entry. Generic `surface.operations.view`, the frontend proposal label, mismatched keys or development provenance fail closed. The UI does not hardcode a proposed real permission. Ordinary unconfigured route behavior is unavailable and sends no request.

Artifact open remains unavailable. A future open requires an existing typed application route/type plus an independently verified current target-access receipt. A future bounded integration may pin one frontend tree/build and one separately agreed backend Project-read adapter, exercise controlled authorized/denied identities and current/bounded/stale/error projections, and prove zero writes. It is not a full-platform prerequisite and does not authorize backend work.

## Verification on final writer files

| Check | Exact command | Result | Raw evidence |
|---|---|---|---|
| Targeted machine report | `./node_modules/.bin/vitest run src/product/render-browser src/components/app-shell/AppShell.test.tsx src/interaction src/localization/localization.test.tsx src/app/routeTree.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=.../writer-runs/targeted-final.json` | exit 0; 20/20 suites passed; 170 total, 170 passed, 0 failed, 0 pending, 0 todo; `success=true` | `writer-runs/11-targeted-post-correction.log`, `writer-runs/targeted-final.json` |
| Typecheck | `npm run typecheck` | exit 0 | `writer-runs/12-typecheck-post-correction.log` |
| Lint | `./node_modules/.bin/eslint src/**/*.{ts,tsx}` | exit 0; 0 errors, 13 warnings in unchanged accepted-tree files only | `writer-runs/13-lint-post-correction.log` |
| Architecture | `node scripts/frontend-architecture-guard.mjs` | exit 0; PASS; 200 governed source files, unclassified/stale/duplicate paths 0, all authority/bypass counts 0 | `writer-runs/14-architecture-post-correction.log` |
| Architecture controls | `node scripts/frontend-architecture-guard.test.mjs` | exit 0; 120 passed, 0 failed/cancelled/skipped/todo | `writer-runs/15-architecture-controls-post-correction.log` |
| Accepted-tree scope | `python3 .../scope_check.py` | exit 0; exactly 15 allowlisted changes, no deletions/outside changes, 990 baseline paths outside allowlist unchanged, real index unchanged | `writer-runs/16-scope-post-correction.log` |
| Structure/whitespace | `python3 .../writer_validate.py` | exit 0; JSON valid, 12-column request TSV with no duplicate IDs, both ledgers valid/no duplicates/new CSS once, `git diff --check` PASS | `writer-runs/17-structure-post-correction.log` |

The implementation preserved TDD history:

- `writer-runs/01-tdd-red.log`: intentional recovered-implementation RED, exit 1, 35 failed / 2 passed.
- `writer-runs/02-typecheck-iteration.log`: pre-implementation type errors, exit 2.
- `writer-runs/03-focused-iteration.log`: intermediate behavior run, exit 1, 4 failed / 46 passed, followed by corrections.

`writer-runs/00-recover-source.log` records recovery verification: accepted tree `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`, 1,004 scoped paths, exact membership/bytes/modes, unchanged real index.

No full-suite final report was generated and the V6 baseline's 797 unique identities were not recharacterized. Hermes/controller owns exact-tree materialization, full final tests, build and browser validation.

## Prepared isolated browser fixture (not run or built)

`fixture-host/entry.tsx` wraps the actual route tree with `RenderBrowserProvider` and the explicit simulated source. It refuses to run unless the isolated host is localhost/127.0.0.1 with `v7Fixture=1`; this switch is absent from ordinary application code. `FIXTURE_HOST_INPUTS.md` records its identity and scenarios.

Available controller outcomes through `window.__V7Fixture`: normal, pending/late, empty, unavailable, denied, unknown, unsupported, error, stale failure, invalid, invalid relationship, stale success, Artifact denied and detail removal. Calls are recorded for browser assertions. These are simulated data and adversarial adapter behavior only—not a real contract, permission, integration or browser result.

The fixture host has a local `node_modules` symlink to the worktree dependency directory for later external build resolution. The writer did not invoke Vite/build, start a server, or run a browser.

## Governance documentation

- Existing `FB-GAP-005` was updated in both request and gap ledgers; no new or duplicate requirement ID was added.
- The API gap ledger distinguishes the existing real five-field summary from the unagreed richer frontend proposal and records the future single bounded frontend/backend integration.
- The IA preserves priority `Scene/Shot > Render observability > Workflow UX > NLE > Agent`, records V6 as the prior item and V7 Render as the only current item.
- The existing acceptance record appends the Owner-adopted bounded V6 read-only review with evidence commit `7362b5e9e2e6df680b03a9666d5b8db264d9e413` and manifest SHA-256 `08ff3f82a0b607e28e98b24acf1db0eb1d868bd304fef784a63a9b34157e0e33`.
- That appendix labels the review as static and the validation as simulated, not a real contract, permission or integration. It preserves narrow-scroll, physical-device, IME, screen-reader and historical-governance limits and does not rewrite sealed V6.
