# Notification focus correction stage 2

## Outcome

Focused GREEN passed. `mark()` now receives the explicit initiating button from both single-read and read-all click handlers. When—and only when—that exact initiating control owns `document.activeElement`, focus moves synchronously to the current active filter before `busy` disables mutation controls. Programmatic activation while Refresh or another valid control owns focus does not steal focus.

The production diff does not add DOM queries, layout changes, row refs, focus timers, asynchronous reclaim, or global handlers. Existing mutation ownership, single/all mutual lock, abort/generation checks, stale completion behavior, query reconciliation, close/reopen/context/unmount retirement, and Unread row-removal recovery remain unchanged.

## Test correction rationale

Stage-1 new tests were revised from the over-specific same-row detail control to the already-implemented active All/Unread filter. The exact old/new identity mapping is in `TEST_REVISION.md`. The new failure/invalid/reject assertion was corrected to the actual catalog phrase `could not be confirmed as read`; no catalog changed.

The first GREEN attempt exposed a pre-existing modeled-blur helper assumption. Its failure artifacts are preserved. The helper now applies its disabled-button blur model only when that exact button still owns focus. Its original test title and original BODY assertion text remain intact, and the modeled-native limitation stays explicit.

## Verification

RED2 ran while production source still matched baseline SHA-256 `9c8fe17ec79523d04a42b4c6c214b0942e0c25de345866d7b869ff0252ca5861`:

- Exit 1; 77 total, 68 passed, 9 failed, 0 pending, 0 todo.
- All nine failures were new single-read focus assertions; no import, setup, collection, config, or helper failure.
- All 64 original baseline tests passed.

Final focused GREEN:

- Command: `npm test -- --configLoader=runner --no-cache src/product/notifications/NotificationInbox.test.tsx --reporter=json --outputFile=.../writer-green/green-focused-final.json`
- Exit 0; 77 total, 77 passed, 0 failed, 0 pending, 0 todo.
- Vitest suite accounting: 6 total, 6 passed, 0 failed, 0 pending.
- Arithmetic: 77 passed + 0 failed + 0 pending + 0 todo = 77 total.

No full suite, build, typecheck, lint, architecture gate, commit, Git write, backend action, catalog change, shared dialog change, or global handler change was performed. Hermes retains final gates.

## Exact final hashes

- `NotificationInbox.tsx`: `8af25d9b262e63410a3dea74832fee93957434339252b283a9c127d60ab7b1b5`
- `NotificationInbox.test.tsx`: `d95af75427d1fe3e2305e041e9f229244b52d6e06b9652f9ffe3c2094cb93d06`
- RED2 JSON: `2ffdabc10d42603e25f791276009c5d7244e0c695643e52bf11950a46ed740f5`
- Preserved failed first-GREEN JSON: `e6ce5dd1634c70602c9c19da6564445019ec955a80154419fb7f0123b5298224`
- Final GREEN JSON: `1200bd993e8e6c2632ea0c06a091d0c1e0d56227e5a12c902aa8fdd53cd2825a`

Changed product files are limited to the two authorized notification files. Evidence is limited to the authorized `writer-green` directory.
