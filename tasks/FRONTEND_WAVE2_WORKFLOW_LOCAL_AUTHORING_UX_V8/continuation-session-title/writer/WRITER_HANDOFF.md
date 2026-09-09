# Writer handoff — V8 session continuity and node-title correction

Bounded implementation and focused validation complete. No commits, staging, freeze or Git ref/index mutations. Final gates, browser checks, real IdP validation, acceptance and publication remain Hermes work.

## Delivered behavior

Installed oidc-client-ts 3.5.0 raises UserLoaded on silent renewal. The wrapper subscribes before hydration, establishes a trustworthy initial baseline, and reads the current SDK User on each load signal. Valid unchanged issuer/audience/principal/session sid, optional tenant claims and OAuth scope preserve the draft across rotating tokens/expiry. Notification revisions and lifecycle activity reject superseded reads. Event payload identity is never applied: observing current SDK state also handles an old notification interleaving with a pending genuine change. Definitive events and signout initiation retire synchronously, including redirect failure. A changed loaded identity retires after its SDK read, before callback-promise completion. Automatic silent renew stays enabled.

Workflow tenant/Workspace/Project, semantic access decision/factors and Selection ownership remain retirement boundaries. Equal access with newer observation time or explanation preserves editing. No canonical permission is granted. Cards use 120px border-box height within existing 136px default row spacing, with a two-line/40px title overflow boundary. Full 120-character titles remain in data, accessible names and editable inspector. No collision/autolayout, persistence or restore logic.

## Verification

Exact commands, working directories and native exits: commands.json. All reports/logs remain under this writer directory.

| Run | Native exit | Native test accounting |
| --- | --- | --- |
| red.json + red.log | 1 | 25 = 0 passed + 1 expected failed + 24 pattern-skipped |
| renewal-green-02.json + log | 0 | 25 = 1 passed + 24 pattern-skipped |
| interleave-red.json + log | 1 | 42 = 0 passed + 1 expected failed + 41 pattern-skipped |
| targeted-final.json + log | 0 | 178 = 178 passed + 0 failed + 0 skipped + 0 todo |

The first RED ran against unchanged production and failed because ordinary renewal removed the draft. The extra interleave RED proved the initial repair could hide a genuine pending identity change; final code fixes it. Final six files: routeTree, WorkflowSketch, Workflow model, AppShell, InteractionShell and Interaction model. Counts were cross-checked against native assertion statuses; all six file results passed with empty error messages and native failed-suite count zero. This reporter does not expose a separate runtime-error count, so none is invented.

Typecheck: typecheck-final-02.log, npm run typecheck, exit 0. Focused ESLint of all four changed TS/TSX files: lint-final-02.json + log, exit 0, zero errors/warnings. git diff --check: exit 0, no output. Intermediate focused-01/targeted-green and earlier typecheck/lint reports are retained and predate the final interleave repair. Historical 869/170/46 figures are not this run's results.

One incorrect-working-directory npx launch (renewal-green.log) exited 1 attempting package resolution, with EPERM network denial and no JSON report. No install or approval/sandbox bypass followed; reruns used the installed frontend runner with --no-install. A first handoff-generation command failed on an absent native JSON runtime-error field; the final accounting uses only reported fields and assertion statuses.

## Exact scope and preservation

Production: auth wrapper, Workflow host key and Workflow CSS. Tests: existing route and Workflow component tests. Docs: existing review, requirements TSV and API gap ledger. Eight changed paths:

- `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`
- `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`
- `frontend/governance/UX_WAVE_1_REVIEW.md`
- `frontend/src/app/routeTree.test.tsx`
- `frontend/src/auth/oidcClient.ts`
- `frontend/src/product/workflow-sketch/WorkflowSketch.test.tsx`
- `frontend/src/styles/foundation.css`
- `frontend/src/surfaces/FoundationPages.tsx`

continuation.patch is relative to inherited dirty implementation, not HEAD. before/, before.json and after.json contain exact baseline/final file hashes. historical-preservation-check.json verifies all supplied historical archive hashes unchanged. All inventoried paths outside these eight are unchanged, including unrelated Render tests, tracked dist/backend static, backend, build/dependency files and guards.

Unchanged HEAD `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`; full ref `refs/heads/agent/frontend-wave2-product-ux-v1`; real index SHA256 `675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`. Stash unchanged. Prior dirty/untracked work preserved. Actual-tree delivery is not a committed/frozen candidate. AGENTS.md freeze/integration rules are overridden by explicit WRITER_BRIEF Owner no-commit authorization (GOVERNANCE.md); instruction alignment deferred. No build, backend/EP19 test, browser adapter, Skill/Memory edit, Git remote operation, integration or publication.

## Test expectation mapping

expectation-mapping.json lists exact retained/replaced/added route test names. Original all-UserLoaded retirement is replaced by two-renewal preservation and actual principal/tenant/sid/scope/invalid-expiry/missing-session/ambiguous-tenant retirement. All five payloadless native-event retirement cases remain. Subscription cleanup now expects SDK hydration/current-user reads and preserves valid unchanged loaded state; symmetric removal and inactive retained callbacks remain checked. The old late-getter/always-retire-late-load test now checks stale hydration rejection and preservation of a new stored session on old notification delivery. Both signout outcomes retain synchronous retirement. Retirement helpers exercise actual retained title, arrange and delete closures against reused local IDs.

Independent additions cover delayed initial trustworthy hydration; init/load interleave; reads after logout/unmount; quick loaded updates and old events after new context; old-event/pending-new-context race; SDK read rejection/null; unknown/nonfinite expiry; Workspace/Project route replacement; semantic access factor/error change versus timestamp refresh; and maximum Chinese/continuous/mixed titles with full inspector/accessible-name/keyboard access. Existing owner/document/adapter StrictMode coverage remains. Fixtures construct the actual SDK User with standard optional sid profile; only manager transport/events are mocked. No sameSession flag or production test authorization.

## Limits and Hermes handoff

AUTH_CONTRACT.md and SDK_INSPECTION.txt provide precise installed-source references. sid is optional at the IdP and necessary only to prove this continuity capability. Missing/ambiguous session data or invalid/unknown expiry retires drafts. Real provider sid stability, tenant semantics and remote invalidation remain unverified. Ordinary Project context is provisional BLOCKED; server session-bound Project/access/query identity remains unestablished (UXW1-002 and FB-GAP-001/002 updated). No universal authentication/authorization PASS.

SDK callbacks have no operation generation. A stale SDK operation actually overwriting storage is indistinguishable from new authentication and fails closed when different/unknown. Payloadless old invalidations cannot identify an old owner. SDK getUser refreshes timers; this consumer does not redesign transport/token lifecycle. No token-string/timestamp identity or unsafe tombstone inference masks these limits.

CSS containment is implemented; component tests prove intact full data and accessibility. Desktop/narrow computed geometry, focus/clipping at browser zoom and visual type/position legibility remain Hermes browser checks; no happy-dom geometry or real-browser PASS is claimed. Final engineering gates/build, independent review, integration and publication remain outside this bounded writer step.
