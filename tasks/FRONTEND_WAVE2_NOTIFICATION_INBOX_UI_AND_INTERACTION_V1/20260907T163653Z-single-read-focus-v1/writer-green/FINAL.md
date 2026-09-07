Implemented the bounded notification focus correction.

- RED2: 77 total, 68 passed, 9 meaningful focus failures; exit 1.
- Final GREEN: 77/77 passed; exit 0.
- Focus now synchronously transfers to the active filter only when the initiating single/read-all button owns focus.
- Programmatic activation from another focused control does not steal focus.
- Preserved first-GREEN modeled-helper failure and corrected its conditional blur modeling.
- No full suite/build, commits, Git writes, or out-of-scope changes.

Final SHA-256:

- `NotificationInbox.tsx`: `8af25d9b262e63410a3dea74832fee93957434339252b283a9c127d60ab7b1b5`
- `NotificationInbox.test.tsx`: `d95af75427d1fe3e2305e041e9f229244b52d6e06b9652f9ffe3c2094cb93d06`

Evidence: [REPORT.md](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NOTIFICATION_INBOX_UI_AND_INTERACTION_V1/single-read-focus-continuity-v1/writer-green/REPORT.md)