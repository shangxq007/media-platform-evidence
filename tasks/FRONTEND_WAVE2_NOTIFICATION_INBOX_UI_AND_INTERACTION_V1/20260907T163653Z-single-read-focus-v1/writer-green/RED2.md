# RED2 result

Production source was SHA-256 `9c8fe17ec79523d04a42b4c6c214b0942e0c25de345866d7b869ff0252ca5861` immediately before this run.

- Exit: 1
- Total tests: 77
- Passed: 68
- Failed: 9
- Pending: 0
- Todo: 0
- Suite accounting reported by Vitest JSON: 6 total, 4 passed, 2 failed, 0 pending
- Arithmetic: 68 passed + 9 failed + 0 pending + 0 todo = 77 total

All nine failures are meaningful focus-continuity RED assertions in the stage-1-added single-read group. Eight observe the focused single-read button remaining active after it becomes disabled instead of focus moving synchronously to the active filter. The narrowly modeled native-blur case observes BODY instead of the active filter. No failure is an import, collection, setup, configuration, or helper failure. The 64 original baseline tests continue to pass.

Raw machine-readable report: `red2-focused.json`.
