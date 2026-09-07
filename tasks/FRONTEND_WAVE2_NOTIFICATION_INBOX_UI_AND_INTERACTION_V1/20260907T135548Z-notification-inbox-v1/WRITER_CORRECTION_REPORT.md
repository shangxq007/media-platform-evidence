# Writer bounded correction report

Applied only REVIEW_CORRECTION.md under the original WRITER_TASK.md and exact ALLOWLIST.json. This is a writer implementation/targeted verification report, not independent acceptance or real inbox integration evidence.

## Scope, instructions and preservation

Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`; owned branch: `agent/frontend-wave2-product-ux-v1`. Inspected HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`. The accepted dirty implementation tree recorded by the original task is `5c19a1045c3382140c62a84cf74ba3d4ec47e354`, not this branch HEAD. Existing stash entry `stash@{0}` (phase15-pre-cip2-drift-gate-repair-safety) was preserved. No commit/freeze/stage/history change or integration occurred; no final candidate SHA was created.

Repository-root AGENTS.md applies to all changed files. Ancestor inspection found no further instructions and the worktree instruction census found no nested AGENTS.md. The latest Owner task expressly overrides the root freeze-before-verification procedure and historical design validation instructions. Durable governance alignment remains a separate task. Read the correction, navigation note, original task, allowlists, compact Owner context, required IA/design records, accepted notification inventory and source identities, and current UXW2-NTF-001/FB-GAP-010/FB-GAP-002 records. No skill was needed.

Read-only Git state inspection at entry found the existing dirty implementation, the six notification module files untracked, and all four authorized Hermes documentation edits. They were preserved. No Git writes, remote operations, docs writes, build, browser, full suite, architecture validator, supplemental Node check or backend test was performed. No denial occurred. All source edits used in-place file writes.

`correction-evidence/before-sha256.json` and `after-sha256.json` census the existing frontend source/scripts/governance and architecture governance files; `scope-result.json` identifies exactly six writer changes, zero other changes during this correction, and 955 unchanged censused files. Each of the four DOCUMENTATION_ALLOWLIST.json files has identical before/after SHA-256. Their preexisting edits belong to Hermes, not the writer. Baseline copies of allowlisted paths and the exact follow-up-only `correction.patch` are retained externally. Existing AppShell, Selection, routing, Review, Canvas, InteractionDialog, styles and source manifest were untouched by this correction.

Exact changed paths (all existing allowlist entries):

- `frontend/src/localization/catalogs.ts`
- `frontend/src/product/notifications/adapter.test.ts`
- `frontend/src/product/notifications/NotificationInbox.test.tsx`
- `frontend/src/product/notifications/types.ts`
- `frontend/src/product/notifications/fixture.ts`
- `frontend/src/product/notifications/NotificationInbox.tsx`

Classification is unchanged: four production consumption/presentation/localization paths and two notification behavioral test paths. No new path or server contract is introduced. Existing ledger proposals in WRITER_REPORT.md remain proposals; its former simulated-status-only navigation description is superseded by this correction.

## Applied behavior

1. Related navigation now exposes a native anchor with an actual typed existing route. The fixture's first notification explicitly declares `project-overview` for `simulated-workspace` / `simulated-project`. Simulated navigation permits only that exact route and appends `?notificationFixture=1`; other simulated route kinds/IDs reject. Real injected sources retain existing typed overview/review mapping. Unavailable origin rejects. Strict target parsing, exact tenant and optional adapter workspace checks, missing/deleted/denied/unknown explanations remain. Both English and Chinese explain that the link opens a simulated overview without granting real account/resource permission. Every supported anchor retains the destination-access explanation. Unknown targets never become inferred URLs.
2. Each mutation owns a unique AbortController identity. Close immediately retires that owner and clears busy, allowing reopened interactions while an old promise remains unresolved. Success processing and finally release require the exact current owner; old completion cannot refresh, announce success or unlock a newer pending read. Lists still validate exact context/request/filter and use their existing generation ownership. No optimistic read/count update or automatic mutation retry was added.
3. Before disabling controls for mutation, capture the focused notification row. A body-focus fallback can then reconcile its confirmed disappearance in Unread to the active filter. Focus or pointer activity elsewhere cancels the saved intent permanently, including moving away and later blurring back to body. Close/context teardown/filter change retire the intent. Existing refresh/detail/no-focus-theft tests remain.
4. Type labels now use own-property lookup, so `__proto__`, `constructor`, and `toString` all render the neutral unknown-type label.
5. Added behavioral coverage for valid-success refresh inversion; exact valid old list receipts across principal/tenant/logout changes and reopening; synchronous single/read-all overlap in both orders; loaded unknown versus confirmed known zero; inbox-wide read-all affecting unloaded items in a one-item snapshot; and post-mutation reconciliation failures including a foreign-context error envelope. Existing rejection, partial failure, confirmed receipt and Selection-preservation tests remain.

## Native receiver coordination for Hermes

Fixture activation is unchanged: exactly one `notificationFixture=1` parameter on localhost, 127.0.0.1 or [::1]. The link is exactly:

`/w/simulated-workspace/projects/simulated-project/overview?notificationFixture=1`

Supply the existing deterministic local receiver's dashboard projection for the existing `/api/v1/me/dashboard` request with matching simulated IDs, for example:

```json
{
  "tenantId": "simulated-tenant",
  "workspace": { "id": "simulated-workspace", "name": "SIMULATED workspace" },
  "recentProjects": [
    { "id": "simulated-project", "tenantId": "simulated-tenant", "name": "SIMULATED project" }
  ]
}
```

This is a receiver fixture input for the existing destination, not a new notification transport or a writer change to the receiver. `platformClient.workspace.getHome` retains its exact workspace check; `ProjectContextProvider` retains BLOCKED status and FB-GAP-001; `ProjectFrame` retains exact route matching and unavailable/error handling; effective access remains unknown. The overview can display explicitly simulated route/project identity without authorizing canonical resources or operations. Receiver error or mismatch must remain unavailable; do not grant permissions to make the scenario pass. Follow the actual anchor in Chromium and verify URL, simulated identity/disclosure and existing blocked controls. No global routing/source receiver change is needed or was made by this writer.

Native focus proof remains Hermes-owned: focus a row's Mark as read button in Unread, start a delayed read, observe disabled-button focus behavior, finish it and verify focus reaches Unread only when the user has not moved. Repeat after moving to Refresh, and after moving away then blurring. Unit tests explicitly model native blur because happy-dom refuses blur on a disabled button: they assert disabled, briefly remove the DOM flag solely to deliver blur, then restore it before resolving the mutation. This is modeled input, not Chromium evidence; no native verification claim is made.

## Retained targeted attempts

All raw JSON reports and stdout/stderr logs are in `correction-evidence/`; original writer attempts remain untouched. `test-summary.json` derives counts from assertion records and verifies total/pass/failure arithmetic. Every attempt has zero skipped, pending, todo and collection errors.

| Report | Total | Passed | Failed | Disposition |
|---|---:|---:|---:|---|
| RED-01.json | 98 | 84 | 14 | Product regressions plus two disabled-blur model assertions and two mismatched error-copy assertions; retained honestly |
| RED-02.json | 98 | 87 | 11 | Corrected model/copy before production edits; meaningful navigation, prototype-label, reopen ownership and modeled focus RED |
| GREEN-01.json | 147 | 146 | 1 | Product corrections applied; newly reached pending-status assertion used “Marking” instead of the existing exact copy |
| GREEN-02.json | 147 | 147 | 0 | Targeted suite green; concurrent typecheck identified a test spy union-signature annotation mismatch |
| GREEN-final.json | 147 | 147 | 0 | Reverified after typed spy correction; no product edits followed |

Final file counts: inbox 54 + adapter 44 + AppShell 36 + localization 13 = 147 passed. The existing AppShell and localization tests were run, not edited. Final typecheck and scoped ESLint both exited 0 with empty diagnostic logs. Initial typecheck exit 2 and its exact diagnostic remain in `typecheck-01.log`; its fix supplies both required mock procedure parameters and asserts the request signal is not aborted.

The raw commands and exit codes follow, and also exist machine-readably in `correction-evidence/commands.json`. Each test command uses configLoader runner, no cache, JSON reporter and external output. No full-suite or native acceptance claim is made.

1. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `1`.

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/RED-01.json src/product/notifications/adapter.test.ts src/product/notifications/NotificationInbox.test.tsx > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/RED-01.log 2>&1
```

2. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `1`.

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/RED-02.json src/product/notifications/adapter.test.ts src/product/notifications/NotificationInbox.test.tsx > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/RED-02.log 2>&1
```

3. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `1`.

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-01.json src/product/notifications/adapter.test.ts src/product/notifications/NotificationInbox.test.tsx src/components/app-shell/AppShell.test.tsx src/localization/localization.test.tsx > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-01.log 2>&1
```

4. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `0`.

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-02.json src/product/notifications/adapter.test.ts src/product/notifications/NotificationInbox.test.tsx src/components/app-shell/AppShell.test.tsx src/localization/localization.test.tsx > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-02.log 2>&1
```

5. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `2`.

```sh
./node_modules/.bin/tsc --noEmit > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/typecheck-01.log 2>&1
```

6. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `0`.

```sh
./node_modules/.bin/eslint src/product/notifications/types.ts src/product/notifications/fixture.ts src/product/notifications/NotificationInbox.tsx src/product/notifications/NotificationInbox.test.tsx src/product/notifications/adapter.test.ts src/localization/catalogs.ts > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/lint-01.log 2>&1
```

7. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `0`.

```sh
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-final.json src/product/notifications/adapter.test.ts src/product/notifications/NotificationInbox.test.tsx src/components/app-shell/AppShell.test.tsx src/localization/localization.test.tsx > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/GREEN-final.log 2>&1
```

8. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `0`.

```sh
./node_modules/.bin/tsc --noEmit > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/typecheck-final.log 2>&1
```

9. Working directory: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend`; exit `0`.

```sh
./node_modules/.bin/eslint src/product/notifications/types.ts src/product/notifications/fixture.ts src/product/notifications/NotificationInbox.tsx src/product/notifications/NotificationInbox.test.tsx src/product/notifications/adapter.test.ts src/localization/catalogs.ts > /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/correction-evidence/lint-final.log 2>&1
```

Real notification integration, server persistence/count/read-all contract, observable real auth-context subscription, destination resource authorization and cross-device delivery remain open under FB-GAP-010/002. The bounded correction does not resolve or reclassify those gaps. Independent full-suite/native review remains with Hermes under the original task.
