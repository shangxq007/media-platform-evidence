# V9 WRITER HANDOFF

Status: bounded authorized writer implementation complete; product interfaces stable and tested. Parent independently owns final seven gates, external build/browser and acceptance. No real backend geometry/authentication integration is claimed. Stop editing after this handoff unless Parent authorizes bounded follow-up.

## Result and source boundary

Ordinary existing NLE Project entry no longer supplies synthetic V1/A1 tracks, clip fixtures, simulated playback or fake progress. It presents queried Project/Timeline/Revision and a distinct unavailable track/clip state. Existing TimelineQueryGateway has only HEAD/history/detail/compare; no geometry read is guessed. Its current HEAD projection maps backend productId to both Project and Timeline, which remains a documented identity limitation. Historical revision targets omit HEAD's digest.

Explicit `NleWorkspace.navigationSource` / `TimelineNavigationProvider` supplies only an isolated verification source. Loaded multi-track discovery/filtering, exact-time and selected-clip location, LOCAL_EPHEMERAL selection, full supplied metadata inspection, keyboard/focus handling and viewport continuity are implemented. Success requires validated echoed request/scope/target, relationship/uniqueness/time bounds and explicit test-only simulated EffectiveAccess binding. No real adapter, endpoint, server DTO or permission was created. Loading, complete empty Timeline, empty track, bounded empty, filtered no-match, unavailable, error/retry, stale and restricted are distinct. Missing queried target is unavailable, not an inferred access denial.

Metadata is optional supplied identity/name/type/version/logical source references and exact source/timeline ranges. No media open/download/preview link, playback, decoder, source-pin generation, persistence, new undo or canonical editing exists. Existing Operation preview → frozen confirmation → apply → authoritative readback and operation IDs remain intact; new navigation never calls Operation or media access. Existing asset/capability boundary reads on NleWorkspace mount are separate and preserved.

NLE reuses the existing OIDC lifecycle subscription and semantic `timeline.operation.apply` access observation solely for owner retirement, without changing global auth or granting access. Equal stable renewal/access timestamps preserve navigation; true Project/Timeline/Revision/identity/access/source/store changes retire details/selection and abort/isolate reads. Retained selection, inspector and dialog-occurrence callbacks are guarded. Injected hosts must reactively replace their scope/access/adapter; test fixtures are never current server identity authority. Shared synthetic proposal tests keep their original assertions in a test-local fixture host, no longer ordinary NLE UI.

## Exact time semantics

Existing ExactMediaTime syntax is reused (integer or rational, positive denominator, max64 input characters), with nonnegative navigation and BigInt comparison/difference. No floating-point conversion, guessed FPS or total duration. `MediaClip.java` nested TimeRange lines149–166 uses inclusive `contains`; V9 follows that authored rule, including zero-length points and multiple clips at shared endpoints. RenderExtent/RenderSampleWindow half-open execution windows are a different contract and are not inferred as authored geometry. First loaded match is selected; locate-selected preserves the explicit overlapping clip. Unknown units disable location and derived duration. Bounds are optional and never inferred; same-target refresh clears positions made invalid by new bounds/basis. No zoom is added; internal list scroll is preserved through inspection and equal refresh.

## Scope, instructions and preservation

Read source/IA/contracts before product edits; saved SCOPE_AND_CONTRACT.md before behavioral RED. Root AGENTS.md is the only applicable repository instruction. Owner's no-freeze/no-commit/no-index authorization overrides generic candidate freeze; instruction alignment remains a separate governance action. No integration is authorized.

Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
Branch: `refs/heads/agent/frontend-wave2-product-ux-v1`.
HEAD unchanged: `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
Index SHA256 unchanged: `675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`.
No candidate commit/tree freeze or index/ref/object write. Stash unchanged. PRESERVATION.json verifies 992 unmodified recovery paths and no unexpected recovery drift; all other writer-inventoried source/governance files outside the 13 intended modifications retain their initial hashes. Four new files are explicitly classified. Native gates run under bwrap with product filesystem read-only, --configLoader runner and --no-cache, outputs only here. No dependencies/config/static/dist/backend/EP19/Skill/Memory/remote/browser changes.

## Exact V9 changed paths

13 modified, 4 added; prior dirty work is preserved outside the intended deltas. These are V9 paths relative to the recovered V8 implementation, not the entire dirty product status.

| Path | V9 change |
|---|---|
| `frontend/src/app/routeTree.test.tsx` | Modified |
| `frontend/src/interaction/InteractionShell.test.tsx` | Modified |
| `frontend/src/localization/catalogs.ts` | Modified |
| `frontend/src/localization/source-manifest.json` | Modified |
| `frontend/src/product/timeline/NleWorkspace.test.tsx` | Modified |
| `frontend/src/product/timeline/NleWorkspace.tsx` | Modified |
| `frontend/src/surfaces/FoundationPages.tsx` | Modified |
| `frontend/governance/UX_WAVE_1_REVIEW.md` | Modified |
| `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` | Modified |
| `docs/architecture/governance/frontend-product-information-architecture-v1.md` | Modified |
| `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv` | Modified |
| `docs/architecture/governance/frontend-product-path-classification-v1.tsv` | Modified |
| `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md` | Modified |
| `frontend/src/product/timeline/navigation.ts` | Added |
| `frontend/src/product/timeline/TimelineNavigation.tsx` | Added |
| `frontend/src/product/timeline/timeline-navigation.css` | Added |
| `frontend/src/product/timeline/TimelineNavigation.test.tsx` | Added |

Existing review appends Owner's bounded V8 adoption and V9 status. IA priority status advances only the authorized navigation/inspection portion of NLE; later editing/Agent work remains unauthorized. Existing current-scope/path ledgers classify the four additions. Existing UXW1-004 and FB-GAP-001/002/003 document local completion versus geometry/time/identity/access/version gaps and a future fixed-version single Project/Timeline/Revision read integration. Original backend request identity/blocking columns are preserved; TSV arity verified. No second ledger, H4 clearing or tracked-dist policy change.

## Native verification and accounting

Final writer commands ran from `frontend` through `writer/run.py` read-only containment; full arguments, cwd/containment, native logs and exits are in the matching JSON receipts.

| Final evidence | Outcome |
|---|---|
| focused-handoff.log / focused-handoff.tests.json / focused-handoff.json | 9 files, 209 total =209 passed +0 failed +0 pending +0 todo; exit0 |
| typecheck-handoff.log / typecheck-handoff.json (`node node_modules/typescript/bin/tsc --noEmit`) | exit0 |
| lint-handoff.log / lint-handoff.report.json / lint-handoff.json (all src TS/TSX) | exit0; 0 errors, 46 existing warnings |
| diff-check.log / diff-check.json (`git diff --check`) | exit0 |

Focused Vitest arguments: `node node_modules/vitest/vitest.mjs run src/product/timeline src/interaction/InteractionShell.test.tsx src/app/routeTree.test.tsx src/api/app/timeline-query.gateway.test.ts src/localization --configLoader runner --no-cache --reporter default --reporter json --outputFile <this writer directory>/focused-handoff.tests.json`.

TEST_COUNTS.json independently checks arithmetic. coverage-mapping.json maps risks to actual native test identities and includes all209 test records with no duplicate file/name identities. It is behavioral coverage mapping, not an instrumented coverage percentage. Final warnings include two existing unsupported-route notFound diagnostics; no act warnings remain.

Six old simulation test identities are retired with explicit expectation-mapping.json: keyboard/bounds/inspector/viewport/collapsed-controls expectations are retained in exact navigation replacements, and fake ticking playback is replaced by no-playback assertions. The four replacement/new NleWorkspace test identities,14 new navigation tests and1 NLE lifecycle route test yield a net+13 identities within the selected suites. This is not a fresh full-suite count or proof of19 independent product scenarios. Original meaningful Operation/readback/reducer/query tests remain. No full-suite/build/browser run by writer; historical full890 is not a V9 run.

### Preserved failures and corrections

- red-entry-01: 2 genuine behavioral failures before implementation (Play/synthetic lanes still present; missing unavailable-projection explanation),17 nonselected tests skipped. Native log/JSON retained.
- red-range-01: 1 genuine authored-boundary failure before correcting half-open matching to actual authored inclusive semantics;13 nonselected tests skipped. Native log/JSON retained.
- navigation-01:13 passed, with initial test act diagnostics later corrected; subsequent focused runs retained.
- focused-01:191 passed/2 failed due new duplicate visible revision IDs; narrowed old queries to canonical code identity rather than weakening expected authority.
- typecheck-02: failed on test-only mock return/parameter typing; corrected without changing production contracts. Other typecheck attempts remain separately logged.
- focused-03:195 passed/1 failed because a new React Query access-change test asserted before its scheduled notification; awaiting the real notification preserves the retirement expectation. focused-04 and subsequent final/handoff runs pass.
- lint-01 passed with47 warnings including one unused Badge import left after removing simulation; removed it, final46 warnings. No lint rule disabled.
- Two read-only baseline Git diagnostics initially lacked external evidence object alternates; corrected using RECOVERY.json alternates. See AUXILIARY_FAILURES.md. No Git mutation.

## Interfaces, browser handoff and remaining limits

See VERIFICATION_INTERFACE.md for the exact provider/props, test-local source recipe, strict request/response shape, scope/access binding, CSS selectors and bilingual accessible UI labels. Product interface files and final content hashes are in FINAL_SOURCE_MANIFEST.json. `v9-complete.patch` includes all17 intended deltas; `v9-tracked.diff` is the existing-path delta from the recovered implementation. STATUS_FINAL.txt preserves the complete dirty status, separate from V9 scope.

Parent should independently exercise ordinary unconfigured route and injected verification host at desktop/narrow widths, long names, native Enter/Space/I/Escape/focus, inspector/list-scroll continuity, revision/source/access/identity retirement and late receipts. Writer did not run browser adaptation, build, final seven gates, physical-device or screen-reader checks. Narrow geometry is implemented but browser acceptance is pending.

Real backend geometry, independent Timeline identity, server Project relationships/five-factor access/session binding, media access, playback and durable editing remain unestablished. Future limited integration criteria are appended to the existing backend ledger, with no new endpoints or permission names and zero writes from navigation. Beyond NLE, existing OIDC limitations remain: missing sid/unknown validity can retire, untagged old invalidations and old SDK storage overwrites are not universally isolated, and real IdP/backend lifecycle behavior is unverified. No overall platform acceptance is inferred.
