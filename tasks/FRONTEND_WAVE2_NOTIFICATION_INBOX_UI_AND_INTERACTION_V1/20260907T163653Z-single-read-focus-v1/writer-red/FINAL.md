Stage 1 TEST-ONLY is complete.

- Changed only [NotificationInbox.test.tsx](/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/notifications/NotificationInbox.test.tsx:454), written in place.
- `NotificationInbox.tsx` remains byte-identical to baseline SHA-256 `9c8fe17e...2ca5861`.
- All 64 existing tests and titles were preserved and passed.
- Added 13 single-read focus tests: 4 passed, 9 expected RED.
  - 8 genuine RED assertions: focus remains on the disabled read button instead of the enabled same-row detail control.
  - 1 explicitly labeled Happy DOM/native-blur model: focus falls to `BODY`.
- Existing read-all focus coverage: 10/10 passed.
- Existing ownership/overlap coverage: 3/3 passed.

Focused JSON result:

- Suites: 6 total, 4 passed, 2 failed
- Tests: 77 total, 68 passed, 9 failed
- Pending/todo: 0
- Exit: `1`, solely from expected assertion REDs

The initial invocation also exited `1` before collection due to read-only `.vite-temp`; that setup failure is preserved. The bounded retry used built-in `--configLoader=runner`, without changing configuration.

Evidence: [writer-red report](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/writer-red/REPORT.md), [JSON results](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/writer-red/focused-vitest-runner.json), and [structured summary](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/writer-red/RED_SUMMARY.json).

No production correction, Git write, full suite, build, typecheck, or unrelated modification was performed.