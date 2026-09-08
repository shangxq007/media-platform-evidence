# V7 bounded writer correction handoff

The four verified interim controller observations are corrected in the existing authorized working tree. This is an unfrozen writer correction, requiring independent controller review. Controller owns exact-tree final gates, browser and package. Product freeze remains forbidden and would require separate Owner authorization. No final acceptance or backend integration is claimed.

## Corrections

1. `source.ts` explicitly excludes `TEST_ONLY_RENDER_ACCESS_KEY` from real `HOST_AGREED` bindings even when both binding and EffectiveAccess key match and provenance is `SERVER`. The existing source-boundary test now asserts unknown/unavailable presentation for that relabelling. The component no-query test exercises denied, unknown and relabelled-test-key initial boundaries under StrictMode with a spied adapter that would otherwise return valid data.
2. `RenderBrowser.tsx` always displays supplied progress value, unit, total, totalUnit and stage in detail after receipt validation, including finite invalid ranges or mismatched units. Missing totals remain explicitly unprovided. The existing invalid 140 frames / 100 frames fixture test now asserts all raw fields, invalid status, and absence of 100%/140% or a progress bar. Additional behavior verifies distinct shots/frames units and absent totals without percentages; existing Chinese workflow coverage asserts all four translated field labels and literal source values. Percentage validation is unchanged: invalid progress is never clamped or converted to a percentage. Malformed/nonfinite receipts still fail closed at the source boundary.
3. External `SCOPE_AND_SOURCE_MAP.md` now states that independent review is required while product freeze remains forbidden/separately authorized. The root AGENTS freeze-before-verification instruction is overridden by the newer Owner no-commit/no-freeze authorization. Permanent instruction alignment remains a separate governance task; no Skill or instruction file was changed.
4. Existing StrictMode registration/ready retirement, pending owner retirement, and pending access/source replacement/unmount tests were extended in place. They establish ready data plus an open dialog or actual pending reads, prove StrictMode replay with at least two requests and exactly one live signal, assert all old signals abort, and settle late successes/rejections without restoring old content/dialogs or changing the replacement/retired state. Pending explicit-owner retirement and each pending access/binding/adapter/unmount boundary exercise both late outcomes, including the formerly live request. The new ready replacement test covers access status, a newly matched host binding and an actual adapter replacement; it verifies immediate old data/dialog removal and successful replacement data where allowed. Existing identity/access/page lifecycle tests remain intact. These tests passed against the existing lifecycle implementation; no lifecycle production change was needed.

## Exact repository changes in this continuation

Only six paths changed relative to the preserved prior writer result, all already in `ALLOWLIST.json`:

- `frontend/src/product/render-browser/source.ts` — real binding correction.
- `frontend/src/product/render-browser/source.test.ts` — existing negative boundary test extended.
- `frontend/src/product/render-browser/RenderBrowser.tsx` — raw supplied progress fields.
- `frontend/src/product/render-browser/RenderBrowser.test.tsx` — focused behavior assertions and three new test titles.
- `frontend/src/localization/catalogs.ts` — four field labels in English and zh-CN.
- `frontend/src/localization/source-manifest.json` — those four existing-consumer translation keys.

The prior intentional 15-path result remains the full change set against accepted working tree `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee`. Scope validation reports no deletions/outside-allowlist changes and 990 unchanged baseline paths outside the allowlist. The prior `WRITER_HANDOFF.md`, allowlist, fixture host builder and browser scripts were preserved. No controller helper was written by this continuation.

An external preservation comparison detected `package_local.py` changed concurrently, from SHA-256 `f7899641c3540dde863a4f88735838e4aeeca41e309bc163d547b25ba6f3aa0c` to `da384784b1abe7976841cadb723adc1fbe96781d037d698b1eab0ccb884c60e1`. The first broad external equality assertion failed on that file; this writer neither edited nor restored it. `writer-runs/correction-05-preservation.json` records the observation separately from the passing repository scope check.

## Actual verification and evidence

Commands ran from the worktree `frontend` directory except the read-only scope/whitespace checks. Each named log records the exact command, raw output and command exit. No full suite, architecture/full gates, build or browser was run in this continuation.

| Check | Command | Actual result | New evidence |
|---|---|---|---|
| Regression RED | `./node_modules/.bin/vitest run src/product/render-browser --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7/writer-runs/correction-01-red.json` | exit 1; 40 tests: 37 passed, 3 failed, 0 pending/todo. Failures reproduce missing raw fields and relabelled test-key acceptance at source/component boundaries. | `writer-runs/correction-01-red.log`, `correction-01-red.json` |
| Targeted behavior | `./node_modules/.bin/vitest run src/product/render-browser src/components/app-shell/AppShell.test.tsx src/interaction src/localization/localization.test.tsx src/app/routeTree.test.tsx --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7/writer-runs/correction-02-targeted.json` | exit 0; reporter 20/20 suites, 173 total/passed, 0 failed/pending/todo, success=true. All 173 assertion statuses verified passed. | `writer-runs/correction-02-targeted.log`, `correction-02-targeted.json` |
| Typecheck | `npm run typecheck` | exit 0 | `writer-runs/correction-03-typecheck.log` |
| Lint | `npm run lint` | exit 0; 0 errors, 46 warnings, all in unchanged files. This npm script quotes the recursive glob, unlike the prior handoff's shell-expanded command; the prior 13-warning count is not reused. | `writer-runs/correction-04-lint.log` |
| Accepted-tree scope | `python3 /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7/scope_check.py` | exit 0; original 15 allowlisted paths only; HEAD/branch/real index unchanged | `writer-runs/correction-05-scope.log` |
| Whitespace | `git --no-optional-locks diff --check` | exit 0 | `writer-runs/correction-06-whitespace.log` |
| Test identity retention | Counter comparison of `targeted-final.json` with `correction-02-targeted.json`, keyed by suite path and full test title | All 170 predecessor identities retained; 3 new; 0 removed. Arithmetic verified from machine reports. | `writer-runs/correction-07-test-identities.json` |

`writer-runs/correction-00-start-state.json` records branch, HEAD/parent, worktree status, stash state, initial file hashes/modes, original test contents and external preservation hashes. `writer-runs/correction-05-preservation.json` records the exact six-path continuation delta and final hashes/modes.

## State and retained boundaries

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`.
- Branch: `refs/heads/agent/frontend-wave2-product-ux-v1`.
- HEAD: `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent: `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- HEAD, branch, real index and existing stash state unchanged. No candidate commit/freeze or integration exists.
- No staging, commit, freeze, reset, clean, stash, ref/remote operations, backend inspection/work, Skill changes, build/browser or recover.py invocation.
- Existing frontend-unagreed projection, real host-binding requirement, unavailable ordinary route, read-only Artifact metadata and no-write boundaries remain in force. This correction adds no transport, permission authority, runtime lifecycle abstraction, route or feature.
- Prior handoff remains preserved; this separate correction handoff supersedes only its affected behavior/verification claims for the controller's review.
