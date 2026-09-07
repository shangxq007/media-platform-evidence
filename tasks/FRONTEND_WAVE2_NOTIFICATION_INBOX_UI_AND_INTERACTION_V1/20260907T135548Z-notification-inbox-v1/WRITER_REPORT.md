# Notification inbox writer handoff

Status: bounded implementation handed off for independent review. This report records writer changes and targeted checks; it makes no product acceptance, server-contract acceptance, integration, deployment, or runtime-readiness claim. Hermes owns independent validation and documentation.

## Authority and preserved state

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
- Branch: `agent/frontend-wave2-product-ux-v1`.
- HEAD remains `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- No candidate commit/SHA was created or frozen. WRITER_TASK expressly overrides root AGENTS.md's freeze-before-verification procedure and prohibits all Git writes. Durable instruction alignment remains a separate governance task. No integration or worktree retirement applies.
- Only root AGENTS.md was found in the repository instruction scope; no nested frontend instructions. The supplied Owner task takes precedence over historical validation/build instructions in the two DESIGN.md references.
- Owner-declared accepted dirty tree: `5c19a1045c3382140c62a84cf74ba3d4ec47e354`. Read-only `git ls-tree -r` returned exit 128, `fatal: not a tree object`; this identifier could not be independently resolved as a local Git tree. Preservation therefore binds the actual initial file bytes, status, HEAD and stash in `writer-evidence/before.json`, not an invented reconstructed tree.
- Initial and final stash descriptions match. Existing Review, Canvas, command, Selection, pagehide, validator and other accepted product files outside the allowlist retain their initial hashes.
- Four documentation/ledger files changed concurrently after the writer baseline: `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`, `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv`, `docs/architecture/governance/frontend-product-path-classification-v1.tsv`, and `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`. These were not writer mutations. They were preserved and separately recorded in `scope-and-identities.json`; the task assigns documentation to Hermes. No non-allowlisted product source changed against the writer baseline.

## Actual writer paths

Exactly the 11 paths in ALLOWLIST.json were written, using in-place writes for existing files:

| Path | Classification / change |
|---|---|
| `frontend/src/components/app-shell/AppShell.tsx` | Existing shared presentation: import and mount one NotificationInbox beside existing shell actions |
| `frontend/src/components/app-shell/AppShell.test.tsx` | Existing test source: append shared-entry coverage for all 14 registered surfaces and real two-item Selection preservation across inbox interactions; preserve prior assertions |
| `frontend/src/localization/catalogs.ts` | Presentation copy: English and Chinese `shell.notifications.*` messages; existing namespace/schema contract retained |
| `frontend/src/localization/source-manifest.json` | Presentation catalog coverage: require the new source keys; no namespace/schema/version change |
| `frontend/src/styles/foundation.css` | Presentation styles: bounded desktop inbox, near-full-width narrow dialog, text wrapping, visible focus, narrow shell wrapping and touch targets |
| `frontend/src/product/notifications/types.ts` | New frontend consumption types and runtime receipt/target/date validation; no server authority |
| `frontend/src/product/notifications/unavailable.ts` | New default unavailable adapter; no HTTP/auth/storage |
| `frontend/src/product/notifications/fixture.ts` | New explicit, isolated, in-memory simulation and localhost opt-in |
| `frontend/src/product/notifications/NotificationInbox.tsx` | New provider/props seam, principal-owned request lifetime and accessible inbox UI |
| `frontend/src/product/notifications/NotificationInbox.test.tsx` | New behavioral component tests |
| `frontend/src/product/notifications/adapter.test.ts` | New receipt, navigation and simulation-boundary tests |

Writer-only patch: `writer-evidence/writer-only.patch`. Final SHA-256 identities: `writer-evidence/scope-and-identities.json`. These hashes were rechecked after the final targeted run and static checks. No documentation, API wrapper, router, InteractionDialog, Selection/store/dispatcher, dependency, configuration, backend or generated-output file was authored by the writer.

## Exact proposed frontend consumption contract

This is an internal consumption proposal, NOT an accepted server DTO or permission projection. No endpoint or HTTP prefix is chosen or guessed. The mismatched existing wrappers are not called or changed.

- `InboxSource = { context, adapter }`. Context is `{ principalId: string|null, tenantId: string|null, sessionId: string, access: 'allowed'|'denied'|'unknown', workspaceId?: string }`. Its session identity must change on authentication lifetime changes. Optional workspace scope is supplied only by an explicit adapter contract; the current route/project/Selection never supplies inbox scope. Source/context are immutable presentation inputs; a future connected integration must publish changes synchronously.
- `InboxAdapter` declares `origin: 'real'|'simulated'|'unavailable'`, `capabilities: {singleRead: boolean, readAll: 'inbox'|'unsupported'}`, `list(request, AbortSignal)` and optional `markRead` / `markAllRead`. All return `Promise<unknown>` so runtime validation precedes consumption. There is no built-in real adapter or auth subscription. Default availability remains unavailable even when the app has an apparent local user ID.
- List request: `{context, requestId, filter: 'all'|'unread'}`. Successful result: `{status:'ok', context, requestId, filter, items, unread, traversal}`. Item: `{id, content:{title,body,type,createdAt:string|null}, read:boolean, target?:unknown}`. All notification content is carried as opaque text and rendered through React text nodes. Opening detail is local and does not mark read or select media.
- Unread is either `{kind:'known',total:nonnegativeInteger}` for the entire adapter-owned inbox or `{kind:'unknown'}`. Loaded unread never establishes a total. Counts below loaded unread, and inconsistent complete snapshots, reject. Entry count is unknown until a current successful query confirms it; no badge means unknown, not zero.
- Traversal is `{kind:'complete'}` or `{kind:'limited',limit:positiveInteger}`. This version consumes bounded snapshots only; no cursor, page number, fabricated total or next-page behavior. Limited snapshots carry visible incompleteness disclosure, including when the loaded snapshot is empty.
- Mutation request: `{context,requestId,operation:{kind:'single',id}}` or `{context,requestId,operation:{kind:'all',scope:'inbox'}}`. Single success requires exact context, request and item identity plus `status:'ok'` and `read:true`. Inbox-wide success/partial requires the exact operation and `{status:'ok'|'partial',readIds:string[],failures:{id,reason:'denied'|'not-found'|'error'}[]}`. Duplicate/overlapping result IDs reject; success cannot contain failures; partial must contain failures.
- Failure envelope: `{status:'unavailable'|'denied'|'not-found'|'error',context,requestId,explanation?:string}`. Exact outer keys and ownership are validated. Ordinary `{error:'NOT_FOUND'}`, void/HTTP success, false read, wrong request/item/context, unknown/malformed counts, duplicate item IDs, and unread-filter results containing read items cannot confirm success. Safe explanations remain verbatim text; thrown transport internals are not displayed.
- Every successful or partial mutation starts a fresh list query. No optimistic item patch or count decrement; no automatic mutation retries. Failed reads preserve the last confirmed unread state. A reconciliation failure clears the displayed snapshot and leaves count unknown.
- A synchronous lock serializes single and inbox-wide mutations, including duplicate activation before React commits disabled state. Lists use generation ownership and AbortSignal. Refresh/filter changes synchronously invalidate older list work. Confirmed overlapping mutations request the current filter afresh. Close invalidates/aborts work; unmount or adapter/principal/tenant/session/access/scope changes retire the inbox session. The keyed session removes old content during render without remounting the media shell. Old completions cannot repopulate a changed/closed view.
- Supported related target shape: `{kind:'project-overview'|'review',tenantId,workspaceId,projectId,availability:'available'|'missing'|'denied'|'unknown'}`. Exact keys; route identifiers limited to ASCII letters/digits/underscore/hyphen. Matching tenant and any declared adapter workspace scope are required. Only existing `/w/{workspaceId}/projects/{projectId}/overview` and `/review` destinations are generated. Arbitrary URLs, extra URL fields, scripts/data URLs, ambiguous IDs, path traversal and unknown target kinds are rejected with explanation. Destination permission checks remain in their existing route. Simulated targets never open real resources or grant app permissions.
- Known notification types (`render.completed`, `review.requested`, `system.announcement`) have localized display labels; unknown types are neutral. Valid zoned ISO timestamps use the active UI locale; invalid dates, including calendar rollover dates, display a localized unavailable label.

## Interaction and simulation

The unchanged InteractionDialog owns entry focus, Escape, Tab wrapping, backdrop close and restoration. Detail/refresh completions do not take focus. When a focused unread row disappears from a newly confirmed snapshot, focus moves to the active filter only if the user has not moved elsewhere. One restrained status region reports loading/results/errors. Default, denied, unknown, empty and error states do not fabricate content. Horizontal Studio and existing navigation/Inspector ownership are retained. CSS accommodates long opaque text; narrow toolbar wrapping prevents the new entry from extending beyond the viewport.

Tests can inject `source` through `<NotificationInbox source={...}/>` or `<NotificationInboxProvider source={...}>` around ProductAppShell. `createNotificationFixture(options)` supports simulated context/access, empty/limited snapshots, failed list and selected failed read IDs. Its data and read state exist only in its closure. Every fixture call checks its exact simulated context. Simulation never inspects real auth, tokens, credentials or permissions.

For Hermes's separately authorized bundled Chromium smoke, activate `?notificationFixture=1` on hostname exactly `localhost`, `127.0.0.1` or `[::1]`. Duplicate activation parameters and non-loopback hosts do not activate it. The switch is read at NotificationInbox mount; reload to change URL fixture mode. Optional parameters:

- `notificationFixtureAccess=denied` or `unknown` for fail-closed source states; default simulated access is allowed.
- `notificationFixtureFailure=list` for a list failure.
- `notificationFixtureFailure=read` for controlled single/all read failures.

The shell entry shows SIMULATED/模拟数据, including an accessible description; the open panel persistently discloses that these are in-memory examples with no real account, notification or permission. Fixtures never fall back from a real error. No notification HTTP, external provider, permission prompt, push or service worker call is introduced. No localStorage content/read/auth persistence is used.

## Tests and raw evidence

Tests were authored before the new implementation. Raw attempts are retained, including collection failures and repairs; none are relabeled as passing:

| JSON report | Result |
|---|---|
| `RED-01.json` | Expected missing-module RED: 0 collected tests; 2 collection-error files before implementation existed |
| `GREEN-attempt-01.json` | 40 passed; component collection error revealed the fixed existing catalog namespace contract; corrected within shell namespace rather than expanding scope |
| `GREEN-attempt-02.json` | 64 total = 63 passed + 1 failed; exact newline assertion corrected to inspect unchanged raw textContent |
| `RED-02.json` | 69 total = 67 passed + 2 failed; added calendar-invalid-date behavior failed and was fixed; new shell test used incorrect store getter and was corrected to the existing getSnapshot API |
| `GREEN-attempt-03.json` | 122 total = 122 passed + 0 failures + 0 skipped/pending |
| `GREEN-final.json` | 122 total = 122 passed + 0 failures + 0 skipped/pending; 0 collection errors |

Final files: adapter 40, inbox component 33, AppShell 36, localization 13; 40 + 33 + 36 + 13 = 122. `test-summary.json` recomputes these counts from assertion records and checks report arithmetic. These are targeted results, not the full frontend suite. Existing tests were retained.

Coverage includes exact success/failure envelopes, partial/global/unknown counts, denied/unknown sources, confirmed single/read-all operations and partial failures, synchronous duplicate/overlap suppression, concurrent refresh ordering, active-filter reconciliation, logout/principal/tenant/session changes, closing and stale completions, safe target rejection, simulation separation, keyboard/backdrop/focus behavior, both UI locales, all shell surfaces and preservation of a real two-item media Selection. The calendar rollover test supplies an additional meaningful behavior RED before its repair.

Static checks: final `tsc --noEmit` exit 0; scoped ESLint exit 0 with empty diagnostic log; `git diff --check` exit 0. Initial typecheck diagnostics and their scoped corrections are retained in `typecheck-01.log`; `typecheck-02.log` and `typecheck-final.log` are clean. All ESLint logs are clean.

Exact test command records are in `writer-evidence/commands.json`. All Vitest invocations used `--configLoader runner --no-cache --reporter=json --outputFile=<external file>`, with stdout/stderr in adjacent external `.log` files. No build, browser run, full suite, architecture validator, supplemental Node check, old pagehide/backend test suite, Git write, remote operation or publication was run. Independent full-suite/browser validation remains Hermes's responsibility.

## Exact proposed ledger disposition for Hermes

The concurrent documentation edits already contain the following intended direction; the writer did not apply them. Treat this as a proposal to reconcile against Hermes's independent review, not acceptance evidence.

1. In `frontend-product-path-classification-v1.tsv`, retain the existing five modified-path classifications. Add or retain these exact six rows:

```tsv
frontend/src/product/notifications/types.ts	REUSE	FRONTEND_INBOX_CONSUMPTION_BOUNDARY_NOT_SERVER_AUTHORITY
frontend/src/product/notifications/unavailable.ts	REUSE	FAIL_CLOSED_UNCONFIGURED_NOTIFICATION_ADAPTER
frontend/src/product/notifications/fixture.ts	REUSE	EXPLICIT_SIMULATED_IN_MEMORY_NOTIFICATION_FIXTURE
frontend/src/product/notifications/NotificationInbox.tsx	REUSE	SHARED_PRINCIPAL_OWNED_INBOX_PRESENTATION
frontend/src/product/notifications/NotificationInbox.test.tsx	REUSE	NOTIFICATION_INTERACTION_AND_CONTEXT_ISOLATION_EVIDENCE
frontend/src/product/notifications/adapter.test.ts	REUSE	NOTIFICATION_BOUNDARY_RECEIPT_AND_NAVIGATION_EVIDENCE
```

2. In the current governed production-scope ledger, add or retain the four non-test notification module paths with `ACTIVE`, `POST_H4_ADDITION`, `NOTIFICATION_INBOX_BOUNDED_FRONTEND_CONSUMER`. Preserve the immutable historical H4 ledger and existing-path classifications. Tests belong in path classification, not a fabricated production-scope expansion.

3. For `UXW2-NTF-001`, keep `WAVE1_FRONTEND_FREEZE_BLOCKING=NO` and `FUTURE_PRODUCT_CAPABILITY_BLOCKING=YES`. Proposed `BLOCKING_LEVEL=BLOCKS_REAL_NOTIFICATION_INBOX_INTEGRATION`; proposed `STATUS=OPEN_REAL_INTEGRATION_NOT_ESTABLISHED_FRONTEND_SIMULATED_CONSUMER`. Desired capability: `Shared Shell frontend inbox consumer with unavailable default and explicit simulation; separately accepted real adapter required.` Desired application contract: the exact typed frontend proposal above, explicitly requiring independent backend acceptance and observable auth-context ownership. Mock behavior: `Explicit in-memory, labeled fixture only; no auth grant, HTTP, persistence or real-error fallback. Ordinary path unavailable with unknown count.` Acceptance criteria remain real client/server prefix/envelope/traversal/count/read-all/persistence/failure/cross-user/tenant/logout tests and FB-GAP-002 authorization; fixture evidence cannot satisfy these.

4. For `FB-GAP-010`, proposed mock boundary: `Frontend-only shared inbox consumer and explicit in-memory simulation implemented for independent review; ordinary path unavailable/unknown. No server persistence, delivery, authorization or cross-device synchronization established.` Proposed blocking disposition: `OPEN — BLOCKS_REAL_NOTIFICATION_INBOX_INTEGRATION; frontend simulation does not resolve the gap.` Append the proposed consumption shape and unsupported-target gap; do not assert a read-all endpoint exists. `FB-GAP-002` remains unchanged and open. Do not expand into UXW2-NTF-002..004 / FB-GAP-011..013.

## Remaining limits

There is no real inbox integration, accepted server contract, auth-change subscription, delivery, persistence, background count polling or cross-device synchronization. Closed entries show an unknown count; opening queries only an explicitly configured eligible source. Close/unmount aborts and discards frontend work but cannot promise cancellation of a future server operation; reopening/refreshing obtains a new snapshot. Traversal is bounded snapshots only. Unsupported target kinds remain an explicit integration gap. Only the existing typed project overview/review routes are linkable for a future real adapter, with destination authorization retained. Native browser/layout/screen-reader behavior and stabilized full-suite acceptance were not run by the writer. No product acceptance claim is made.
