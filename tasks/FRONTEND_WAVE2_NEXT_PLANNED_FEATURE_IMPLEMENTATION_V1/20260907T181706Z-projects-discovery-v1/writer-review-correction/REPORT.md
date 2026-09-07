# FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1 — writer review correction

## Outcome

Completed the bounded correction for the existing Workspace recent-Project discovery feature. The focused Projects tests are green at 53/53. No commit, index, remote, backend, build, typecheck, full-suite, browser, Skill, Memory, or unrelated source operation was performed.

The correction keeps one stable workflow button mounted while it changes between Cancel, Retry, and Refresh. Focus therefore remains owned through loading, cancellation, failure, retry, and success without an asynchronous focus effect; if the user moves focus elsewhere, completion does not reclaim it.

Real-origin loading now requires the exact frontend-proposed `project.recent.query` key and a `SERVER` EffectiveAccess projection. Simulated loading requires the explicitly labelled `fixture.project.recent.query` plus `DEVELOPMENT_FAIL_CLOSED`. Changing only the fixture adapter origin cannot create real query authority. Presentation labeling uses the same provenance check, so an untrusted origin is presented as unavailable rather than connected. The fixture remains a simulation and never grants authorization.

For an initial trusted server denial/unknown result, the UI renders the source-owned explanation verbatim alongside localized generic copy. A simulated denial/unknown renders the fixture's clearly simulated explanation. Untrusted or unavailable projections do not contribute opaque explanation text.

## Authority, instructions, and repository state

- Worktree: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1`
- Branch: `agent/frontend-wave2-product-ux-v1`
- HEAD remained `f5e19cf53fd010eea2935dd29557e82a879e042c`; parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`.
- Applicable repository instruction: root `AGENTS.md`; no nested instruction applies to the allowed paths.
- Precedence: the current Owner instruction authorizes ordinary feature-local correction/tests and explicitly prohibits frozen candidates and product commit/index writes, overriding the durable freeze-before-verification rule for this task.
- Existing stash remained untouched: `stash@{0}: On agent/roadmap22-executable-task-graph-worker-fabric-decision-recovery: phase15-pre-cip2-drift-gate-repair-safety`.
- The dirty worktree and every unrelated/historical artifact were preserved. `frontend/governance/UX_WAVE_1_REVIEW.md` appeared as unrelated dirty state after the initial status capture; it was not read or modified by this executor. No attempt was made to restore, stage, hide, or reconcile concurrent/unrelated changes.
- Candidate SHA and post-integration state: not applicable; both were outside authorization.

## Review observation verification

1. **Observed — workflow focus removal.** Current source conditionally mounted Refresh only for ready, Cancel only for loading, and Retry only for cancellation/query failure. Activating one removed the focused node with no stable handoff. The pre-fix focus test observed `document.activeElement === BODY` after Cancel. Corrected with one persistently mounted feature-local workflow button and no timer/global Escape/focus effect.
2. **Observed — origin flag could relabel simulation as real authority.** `sourceDisposition` previously called `accessDisposition` for every non-unavailable origin and accepted AVAILABLE regardless of projection key/source. Tests proved a real adapter accepted fixture/development/missing-server projections before the fix. Corrected with exact origin-specific projection provenance and matching presentation labeling.
3. **Observed — initial source reason was lost.** State initialized directly to denied/unknown while `explanation` initialized to null, so trusted server explanation text was absent. Corrected by deriving initial opaque explanation only from a provenance-matched projection. The same exact server string is asserted in English and Simplified Chinese.
4. **Partly disproved and partly observed — lifecycle test validity.** Counterevidence: the existing parameterized principal/tenant/session/workspace transition test already created an actual pending refresh, captured its request, loaded the new empty context, and then resolved a structurally valid old owned receipt; the unmount case also used its captured valid request. Remaining defect: the same-identity adapter-replacement case resolved `requestId: "late"`, which could pass through parser rejection rather than lifecycle ownership, and explicit `principalId: null` logout coverage was absent. The helper was corrected to resolve the actual captured request/scope, preserving the existing test/title and invariant. A concrete logout case now establishes a valid old pending receipt, transitions to a new principal-null context that performs no query, and resolves the old receipt after the new state is visible.

## Changed paths and scope

Only four of the five authorized Projects files changed during this correction:

- `frontend/src/product/projects/ProjectBrowser.tsx` — stable workflow control, provenance-backed source label, and verbatim trusted source explanation.
- `frontend/src/product/projects/ProjectBrowser.test.tsx` — focus lifecycle/no-theft, real source test helper, opaque en/zh-CN denial explanation, valid same-identity receipt, and principal-null logout coverage.
- `frontend/src/product/projects/source.ts` — exact real/simulated projection provenance, presentation-origin projection, and trusted explanation helper.
- `frontend/src/product/projects/source.test.ts` — real/simulated key/source and presentation-label regressions.

`fixture.ts`, localization catalogs/source manifest, and `foundation.css` did not change. No other product, test, configuration, documentation, shared Dialog, command registry, notifications, backend, or build path was changed by this executor.

## Before/after SHA-256

| Path | Before | After |
|---|---|---|
| `frontend/src/product/projects/ProjectBrowser.tsx` | `cf4aa628ff7921462ed3ee20c790fe088a5535621c66c4727a1b67beac180f85` | `d931257e0a02f7ec2ddebaca64924694a088949e6574c36be023ea9dfc071bad` |
| `frontend/src/product/projects/ProjectBrowser.test.tsx` | `eb3b462f8b8a287ace1fe3cf72c8f359fce7c864004f9dc93fe10e3c06497a71` | `4f2252163393362d291dda0c875a0e9485961addbfc7026eace8030084d448b4` |
| `frontend/src/product/projects/source.ts` | `1e5867bf508b3c10f427643ce02ff635c009ba50947d4a4d494670fc88f83390` | `44e2ded7175552dc052edb130c8af915d8ae62c8732279185e3a136c305cc46e` |
| `frontend/src/product/projects/source.test.ts` | `91c88bd281ddb6eac270a16208d4237548f7c499f784396000173d3009736d1c` | `126fc3e8c08c6c1bec033b2dc25f0b69b8c9e3d39b45a63dd6485acb69487999` |
| `frontend/src/product/projects/fixture.ts` | `6d8ad39bf55610bd717eecb2842ce90851ba2139f73f5d4bcecd4c661ccb33db` | unchanged |
| `frontend/src/localization/catalogs.ts` | `a137d11db68552eab6441eacc07561cdb763daca039e79de38acfe1a92f3a7a3` | unchanged |
| `frontend/src/localization/source-manifest.json` | `1446e2ffa18e0e97852fbc64d15a424c167334b2e681f80162efde39d1af79f8` | unchanged |
| `frontend/src/styles/foundation.css` | `881a8d1544ed820e6feb89dabd9644ef4f30d0ae226ef6f5226c833c8ca90393` | unchanged |

## Focused test evidence

All commands were run from `frontend/` with `--configLoader=runner --no-cache`, default plus JSON reporters, and unique external report paths. JSON accounting satisfies `total = passed + failed + pending` for every attempt.

| Attempt | Tests | Passed | Failed | Pending | Exit | Purpose |
|---|---:|---:|---:|---:|---:|---|
| `red-focus-trust-lifecycle-01` | 53 | 48 | 5 | 0 | 1 | Pre-production-fix RED for focus, trust provenance, and en/zh-CN server explanation. |
| `red-focus-trust-lifecycle-02` | 53 | 47 | 6 | 0 | 1 | Adds explicit simulated explanation RED before production correction. |
| `green-projects-focused-01` | 53 | 53 | 0 | 0 | 0 | Corrected focus, lifecycle, provenance, and explanation behavior. |
| `green-projects-focused-02` | 53 | 53 | 0 | 0 | 0 | Final GREEN including provenance-backed presentation labeling. |

Exact final command:

```text
npm test -- --configLoader=runner --no-cache src/product/projects/source.test.ts src/product/projects/ProjectBrowser.test.tsx --reporter=default --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V1/writer-review-correction/green-projects-focused-02-results.json
```

Final machine-readable accounting: 5/5 reported suites passed; 53 total tests = 53 passed + 0 failed + 0 pending; `success: true`. Commands, logs, exits, and JSON reports for every attempt are preserved in this directory.

## Pending validation

Stopped after focused GREEN as directed. Hermes still owns the required final native policy typecheck and any broader final validation/integration decision. No typecheck, build, full suite, lint, localization campaign, browser/native reproduction, app-unused check, Node-cache check, or optional diagnostic campaign was run in this correction.
