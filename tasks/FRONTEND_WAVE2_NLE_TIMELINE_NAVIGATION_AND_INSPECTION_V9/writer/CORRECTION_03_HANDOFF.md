# CORRECTION 03 HANDOFF

Minimal correction complete; no commits or freeze. Parent must rematerialize validation-03, execute final7 gates and rerun the final native browser matrix. Browser acceptance is still pending; no browser GREEN is claimed here.

## Exact correction

Only these product paths changed relative to correction-02; both retain REUSE classification:

- frontend/src/product/timeline/TimelineNavigation.tsx — one-line addition of `type="button"` to Locate selected clip.
- frontend/src/product/timeline/TimelineNavigation.test.tsx — two added regressions; all 25 prior tests remain unchanged.

The time form contains exactly two buttons. Locate time retains `type="submit"` and the existing onSubmit handler. Locate selected clip no longer triggers that handler after restoring the explicit clip target. Nearby refresh, toolbar, metadata and object buttons are outside this form. No global Button default, time utility, inclusive authored interval, DTO, endpoint, UI label or other product path changed.

## RED and GREEN receipts

Primary native-browser RED remains unchanged at `browser-v9/continuation-run-05/LOCATE_SELECTED_DIAGNOSTIC.json`, bound by `correction-03/BROWSER_RED_REFERENCE.json`. It records Locate selected clip as the submitter, resolved DOM type submit, missing type attribute and final clip:clip-1 after explicitly selecting clip:clip-2. Browser handoff also preserves the repeated run-04 failure.

Before runtime modification, `correction-03/red-01.log`, `red-01.json` and `red-01.tests.json` reproduce the behavior in installed happy-dom: 27 total = 25 passed + 2 failed, zero pending/todo. The first added test uses connected HTMLElement.click(), real React handlers and DOM default submission, with a passive submit listener. It proves Locate time submits, the shared rational endpoint has two inclusive matches, the second clip is explicitly selected, then Locate selected clip wrongly changes selection back to the first. The second failure is the missing explicit button type. This is actual behavioral RED without a custom submission shim or fireEvent-only activation. `red-source/` and `RED_SOURCE_MANIFEST.json` preserve the executed test and unchanged pre-fix runtime bytes.

After the one-line fix, `green-focused.log`, `green-focused.json`, `green-focused.tests.json`: 7 files, 178 total = 178 passed + 0 failed/pending/todo. The added test now retains the second clip and exact 1001/30000 position and observes no extra submit. The second test verifies only Locate time is a submit button and exercises the unchanged form submission endpoint with requestSubmit. Timeline, NleWorkspace, editor-state, SemanticDiff, types, shared interaction and model regressions passed.

Other native command receipts/logs in correction-03: typecheck exit 0; two-file ESLint JSON in lint.log, zero errors/warnings; architecture guard PASS with governed 23/23 and no missing/unexpected/unclassified paths; git diff --check exit 0. GATE_SUMMARY.json records exact argv, read-only bwrap containment, exits and durations. TEST_ACCOUNTING.json derives counts from native Vitest reports. ACCOUNTING_NOTE.md discloses an initial report-parser field mismatch, corrected without changing tests or rerunning gates.

DOM-emulator limits: @testing-library/user-event is not installed; no dependencies were installed. HTMLElement.click() successfully reproduces the relevant default action. happy-dom does not synthesize implicit submission from Enter keydown; requestSubmit covers the form endpoint only. Native keyboard/Enter and final browser GREEN remain the parent's verification responsibility. No browser was launched by this correction.

## Source binding and preservation

Final SHA256:

- TimelineNavigation.tsx: `71ac8645edd1785393444c335fcdf2bea8eee77b87a0b2fdc7e5ed4d623538d1`
- TimelineNavigation.test.tsx: `6bac71597bc5cfaed185621d3ec2ed54cb9cdbcfffe1ff75fc800934960c1e28`

SOURCE_DELTA.json and CORRECTION_03.patch bind the exact two-path delta; before-source/, red-source/ and source/ retain the bytes. FINAL_SOURCE_MANIFEST.json binds all 7,981 source paths. PRESERVATION.json verifies 7,979 source paths outside this correction and all 18,325 inventoried prior evidence files unchanged, including prior handoffs, tests, browser failures and snapshots. Actively appended *_NATIVE.log files were excluded from immutability hashing and never overwritten here.

BEFORE_STATE.json and FINAL_STATE.json match: branch agent/frontend-wave2-product-ux-v1; HEAD f5e19cf53fd010eea2935dd29557e82a879e042c; parent 01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a; unchanged status, stash and worktree list. Index SHA256 remains 675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e. No candidate commit, integration, backend, static/dist, credentials, dependency, docs/index, Skill/Memory or remote change. Applicable instructions and explicit no-freeze precedence are recorded in SCOPE.md.

All earlier projection, access, real-backend/IdP, ordinary unconfigured and navigation-only limitations remain. Product editing stops at this handoff.
