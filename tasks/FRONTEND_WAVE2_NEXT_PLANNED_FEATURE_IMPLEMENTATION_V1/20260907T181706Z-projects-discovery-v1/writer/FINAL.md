Implemented the bounded read-only Workspace Projects increment.

- Added scoped source contract, strict receipt validation, localhost fixture, discovery/filter/sort UI, cancellation/retry/refresh, and read-only detail dialog.
- Ordinary Projects loading remains unavailable because no authenticated principal/tenant/session-bound adapter exists; no HTTP or mock fallback occurs.
- Fixture: `/w/<workspaceId>/projects?projectsFixture=1` on localhost only.
- Preserved existing dirty work and made no commits, index writes, remote operations, builds, or browser/server runs.
- Final focused tests: 54/54 passed.
- Localization tests: 13/13 passed.
- Targeted TypeScript and lint checks passed.
- All failed attempts and machine-readable results were preserved.

Full handoff: [REPORT.md](/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1/writer/REPORT.md)