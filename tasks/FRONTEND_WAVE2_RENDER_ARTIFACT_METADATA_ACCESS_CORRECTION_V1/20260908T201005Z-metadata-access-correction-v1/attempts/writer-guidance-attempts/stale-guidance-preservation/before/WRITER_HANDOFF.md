# Writer handoff: bounded Artifact metadata access correction

Task: FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1. Implementation and focused RED/GREEN verification are ready for Hermes review. V7 overall acceptance, full engineering gates, browser evidence, real backend contract and integration remain pending/unestablished. No commit or freeze occurred.

## Evidence placement

Actual writer evidence: `/tmp/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1`. Requested E: `/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1`. The developer filesystem restriction permits writes only in the task worktree and `/tmp`, and escalation is unavailable. No write to E was attempted. Hermes must copy this package into E, preserving raw attempts and relative paths; this file is prepared for `E/WRITER_HANDOFF.md`. Final engineering/browser evidence will be supplied by Hermes at E.

## Scope and precedence

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
- Branch: `agent/frontend-wave2-product-ux-v1`; HEAD unchanged: `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- Actual index SHA-256 unchanged: `675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`. Before/after branch, HEAD, parent, status, stash and worktree inventory match exactly in `before-state.json` and `after-state.json`.
- Root `AGENTS.md` governs the repository; the supplied AGENTS instructions match it. No ancestor or nested AGENTS.md was found. The current Owner WRITER_BRIEF.md explicitly authorizes the dirty implementation tree and overrides candidate freezing. Verification therefore used unfrozen working files; no final candidate SHA exists. Durable instruction alignment is deferred to separate governance work, without editing AGENTS.md.
- Read source/component/tests/fixture/CSS/localization/manifest, existing FB-GAP-005 records and complete existing review report. Decision context `/home/user/Documents/03-大模型上下文-精简版.md` was read for relevant permission and render principles only, especially backend authorization authority and fenced execution attempts; no decision/Skill/Memory edits.
- No staging, commit, reset, clean, stash mutation, merge, fetch, push, ref/history operation, remote write, dependency change, backend/EP19 activity, guard change, build, dist/backend-static change, new product path, or other feature work. No integration or cleanup is authorized here.

## Exact writer changes

Paths below are relative to the task worktree and compared with the authorized dirty starting tree, not HEAD.

| Path | Classification | Change |
| --- | --- | --- |
| `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md` | Existing FB-GAP-005 governance | Clarify collection/item access, allowed fields, response trimming, refresh/clear and future pinned integration cases. |
| `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` | Existing FB-GAP-005 governance | Update the existing row only; no new request ID or contract. |
| `frontend/governance/UX_WAVE_1_REVIEW.md` | Append-only review | Preserve the complete original prefix and append real interim writer findings/results and pending acceptance. |
| `frontend/src/product/render-browser/RenderBrowser.test.tsx` | Behavioral tests | One preserved real RED regression plus item, collection, mixed-state, transition, invalid receipt and lifecycle coverage; all original test bodies preserved. |
| `frontend/src/product/render-browser/RenderBrowser.tsx` | Production UI | A small item branch permits metadata only for inspectable; all four restricted states return a state-only list item. |
| `frontend/src/product/render-browser/source.test.ts` | Schema tests | Add explicit five-state preservation/relationship checks and missing/invalid metadataAccess rejection; no schema changes. |

No files added or deleted. `source.ts`, fixture, CSS, catalogs, source manifest, lifecycle/EffectiveAccess/host binding and all other repository files in the captured non-ignored inventory are unchanged. `preservation.json`, before/after file hashes, before/after copies and six per-file patches manifest the correction. Baseline test diffs remove no lines except the expanded type import; no baseline assertion or identity is weakened/deleted/skipped.

## Real RED/GREEN commands and results

All commands below ran from the worktree `frontend/` with existing installed binaries. Every attempt retains its unedited `raw.log`, `tests.json` and exact argv/cwd/exit in `command.json`. The wrapper itself exits normally after recording the Vitest child exit; the table reports the actual Vitest exit.

| Attempt | Exit | Files | Total | Passed | Failed | Skipped/pending/todo | Runtime error suites |
| --- | --- | --- | --- | --- | --- | --- | --- |
| red-01 | 1 | 2 | 42 | 41 | 1 | 0 | 0 |
| green-01 | 0 | 2 | 91 | 91 | 0 | 0 | 0 |
| green-02 (final focused) | 0 | 2 | 95 | 95 | 0 | 0 | 0 |

red-01:

```sh
./node_modules/.bin/vitest run src/product/render-browser/RenderBrowser.test.tsx src/product/render-browser/source.test.ts --configLoader runner --no-cache --reporter=default --reporter=json --outputFile=/tmp/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/red-01/tests.json
```

green-01:

```sh
./node_modules/.bin/vitest run src/product/render-browser/RenderBrowser.test.tsx src/product/render-browser/source.test.ts --configLoader runner --no-cache --reporter=default --reporter=json --outputFile=/tmp/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/green-01/tests.json
```

green-02:

```sh
./node_modules/.bin/vitest run src/product/render-browser/RenderBrowser.test.tsx src/product/render-browser/source.test.ts --configLoader runner --no-cache --reporter=default --reporter=json --outputFile=/tmp/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/green-02/tests.json
```

RED ran before any production edit, with exactly one new behavioral test. Its six soft assertions failed because the actual serialized Artifact subtree contained ordinary protected ID/name/type/availability/version/taskId values. The raw output and JSON include the received DOM. `red-source/` preserves that test and the old component. The original denied regression and all its assertions remain in the final source. No private-path/secret-string sanitization trick or fabricated failure was used.

Production SHA-256 before/at RED: `68dc8548f7c0d4342965dbfb3f2f226145856ff07937d9e200963063efe46aaa`. Final: `769a3bbbb6a02f07c02546e7cb413f8025c985dfb74c7b34d64790a7e0bf0d4a`.

GREEN-01 passed but emitted an act warning in the newly added adapter replacement test. GREEN-02 adds an explicit wait for the replacement response and four collection-level cases; all 95 tests pass with no stderr warning. `test-summary.json` verifies JSON count arithmetic and unique full identities: all 42 RED-run identities retained, 53 additional; relative to the pre-correction focused suite, 41 retained + 54 added, 0 removed. No full-suite count is inferred. Historical full baseline 789 and V6-to-V7 retained748/removed49/added41 remain historical.

Additional read-only check: `git diff --check` from the worktree root, exit 0; exact output in `diff-check.json`. No full engineering gate, browser run, build or backend test was executed by this writer.

## Behavior matrix

| Input / event | Implemented behavior and evidence |
| --- | --- |
| Available collection, inspectable item | After existing outer access/context/request/schema/relationship checks, render supplied name/id/type/availability/version/taskId and existing read-only disclosure. Positive field checks pass. No content/download/preview/external action. |
| Available collection, denied item | Generic accessible localized Metadata denied text in list item; no protected metadata in serialized subtree. Original real RED now passes. |
| Available collection, unknown item | Generic localized Metadata access unknown only; full-subtree exclusion assertions pass. |
| Available collection, unavailable item | Generic localized Metadata unavailable only; no cache fill. |
| Available collection, stale item | Generic localized Metadata stale only; no cache fill. |
| Mixed collection | One inspectable item remains readable alongside all four generic restricted placeholders; protected attributes/text absent. |
| Collection-level denied/unknown/unavailable/stale | Existing collection state and safe explanation preserved; no item list. Existing missing/empty/bounded behavior retained. |
| Same item ID inspectable to any restricted state | Refresh synchronously detaches old Artifact DOM; successful restricted receipt and reopened details contain only state. Only a new valid inspectable receipt restores metadata. |
| Denial followed by late old allow | Aborted old success is ignored after current item denial; explicit new valid allow restores. |
| Refresh error, rejected promise, cancellation, stale failure | Prior snapshot and dialog clear; retry remains available; cancelled late success cannot refill. Snapshot freshness labeling remains the existing separate collection behavior. |
| principal/account, tenant, session, Project changes | principalId is the proposed account/principal identity; no separate accountId exists. Tests exercise ready details and pending refresh for each scope field: old DOM removed, signals aborted, late replies ignored. |
| Outer access, binding, adapter, owner replacement/retirement | Same ready/pending checks; retained original StrictMode, initial denied/unknown, unmount and pagehide/pageshow tests also pass. |
| Missing/invalid metadataAccess or invalid task link | Schema rejects missing/null/empty/unrecognized/wrong-case/boolean states and preserves all five valid states without converting to inspectable; relationship checks still reject each state when task link is invalid. UI rejects bad access/relationship/request/scope receipts before rendering. |
| Independent task/source details | Authorized task ID remains in the related task section, never in a restricted Artifact subtree. Source identity is separately authorized Render metadata. No task suppression to satisfy an overbroad same-text assertion. |

## Limitations and Hermes next steps

- This is a defensive frontend display correction. The unagreed schema still accepts metadata fields on restricted items, so transport/runtime may contain them. Restricted backends MUST trim responses; DOM omission is not a confidentiality boundary. A trimmed server contract and frontend adapter representation remain to be separately agreed.
- Tests use injected read sources and happy-dom, not real server permission enforcement or browser/screen-reader acceptance. Existing badge translations are reused without redefining metadata access as download-only.
- Copy this writer package to E with raw failures preserved. Run the separately assigned final engineering gates and browser checks against the exact final working implementation, preserving all prior V7 evidence and baseline identities. V7 overall acceptance is pending; this writer does not claim final completion, integration or publication.
- No canonical main integration or task branch/worktree retirement was performed or requested.
