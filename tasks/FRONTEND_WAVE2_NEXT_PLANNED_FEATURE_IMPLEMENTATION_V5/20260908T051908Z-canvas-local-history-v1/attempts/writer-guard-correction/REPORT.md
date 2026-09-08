# V5 bounded canvas restore correction

Completed in place in `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`. The only product file edited was `frontend/src/product/canvas/model.ts`, inside `restoreCanvasEdit` (local presentation implementation). No other source was edited.

Removed the temporary Map construction and replaced `byId.get(node.presentationId)` with `values.find(value => value.presentationId === node.presentationId)`. The existing readonly history values describe the two local nodes with distinct presentation IDs; a direct scan avoids allocating mapped pairs and a Map for this small collection. This is a legitimate small-data simplification, with no transport, bracket-access substitution, alias, extra lookup structure, or behavior expansion. No new duplicate-ID behavior or validation was added.

Restore still copies the current state and current matched node, assigning only `title`, `x`, and `y`. It preserves `presentationId`, `semanticReferenceId`, the current `references` and `edges`, and every camera field (`zoom`, `viewportX`, `viewportY`). Unmatched nodes remain the same objects. History input remains readonly. Other functions are unchanged. The exact bounded diff was checked against the pre-edit snapshot.

## Guard finding and inherited limitation

Read the actual `frontend/scripts/frontend-architecture-guard.mjs` lines 183–193; the excerpt is saved in [guard-lines-183-193.txt](guard-lines-183-193.txt). Line 189 matches any identifier followed by a dotted `get`, `post`, `put`, `patch`, or `delete` call, without resolving the receiver's type or whether the call performs transport. Thus the pure local Map lookup was a false positive under `UNSTABLE_ROUTE_DIRECT_COMPONENT_CALL_COUNT`. The inherited broad-regex false-positive limitation remains. The guard was not edited or executed; its before/after SHA-256 was checked unchanged ([guard.sha256](guard.sha256)).

The existing `../final-validation-02/gates/architecture.log` reports count 1, evidence `product/canvas/model.ts:151:byId.get(`, and `FRONTEND_ARCHITECTURE_GUARD=FAIL`. Its companion `architecture.json` records native `exit_code: 1`. That is a failure baseline, not a pass or waived gate. No post-correction architecture result is claimed. Final full gates are owned by Hermes.

## Focused verification

Exact command and working directory ([command.txt](command.txt)):

```text
cwd: /home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend
node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V5/writer-guard-correction/tests.json src/product/canvas/model.test.ts src/product/canvas/WorkspaceCanvas.test.tsx
```

Native Vitest exit: **0**, saved in [native-exit.txt](native-exit.txt). Combined stdout/stderr: [tests.log](tests.log). Machine-readable output: [tests.json](tests.json). Execution timestamps: [timing.txt](timing.txt).

| Existing test file | Total | Passed | Failed | Skipped/todo |
| --- | ---: | ---: | ---: | ---: |
| `src/product/canvas/model.test.ts` | 37 | 37 | 0 | 0 |
| `src/product/canvas/WorkspaceCanvas.test.tsx` | 113 | 113 | 0 | 0 |
| Total | 150 | 150 | 0 | 0 |

Arithmetic checked against JSON assertion results and summary: 37 + 113 = 150; 150 passed + 0 failed + 0 pending + 0 todo = 150 total. Both file results passed, with no reported file errors; JSON success is true. Vitest reports 19 nested suites, not 19 files. Existing coverage includes local title/position undo/redo, current reference identity, selection and camera preservation, history bounds, and lifecycle cancellation. No tests were added or edited.

## Scope and instruction precedence

Read root `AGENTS.md`, which governs the repository. Checked `frontend/AGENTS.md`, `frontend/src/AGENTS.md`, `frontend/src/product/AGENTS.md`, and `frontend/src/product/canvas/AGENTS.md`; none exist. The latest explicit Owner instruction authorizes only this in-place product correction and external evidence, with focused tests, and prohibits Git and broader gates. That instruction takes precedence over root governance requirements to record Git state and freeze a candidate commit before verification. Consequently branch/HEAD/status/stash, candidate SHA/parent, and integration state were not inspected or changed. Any governance alignment is deferred to a separate Owner task; no instruction file was changed here.

No build, guard execution, typecheck, full-suite/backend testing, Git, Skills, or Memory operations were performed. No integration, remote operations, or cleanup was performed.

Evidence in this directory: this report, [model.before.ts](model.before.ts), [model.diff](model.diff), [model.after.sha256](model.after.sha256), guard excerpt/hash, test command, native exit, log, JSON, and timestamps. Product edits and evidence writing stop with this report.
