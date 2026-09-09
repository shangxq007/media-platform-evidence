# V10 native Chromium engineering handoff

**Scoped core matrix PASS twice; supplemental boundary probes PASS. This is engineering validation, not independent final acceptance.** Parent visual inspection and acceptance decision remain outstanding.

## Input and execution boundary

- Authoritative source tree: `ea4798924207d4004c92910815a42753e4ab9724`, `../validation-01/snapshot`; ordinary build: `../validation-01/build`. Parent seven gates were supplied as context and were not rerun here.
- Read writer/WRITER_HANDOFF.md, WRITER_BRIEF.md, SOURCE_DELTA.json, final Publication source/types/testing/model, route tree, InteractionDialog and source Vite config. Read V9 final03 fixture/build/runner/helpers and final green handoff; only mechanics were reused, not results or source defaults.
- Only new `browser-v10/` was written. No product, baseline V9, Skill/Memory, credentials, backend or remote publication edits. Read-only-root bwrap for build and native processes; task-owned Vite temporary directory mounted over installed dependency cache only in the build namespace. Snapshot AGENTS candidate-freeze instruction conflicts with current explicit no-commit/no-product-edit authority; current authority controls, no commit/index changes performed.
- `fixture/entry.tsx` mounts actual RouterProvider/routeTree, ProjectFrame/AppShell and PublicationSourceProvider. Stable source/owner/adapter until explicit fixture boundary changes. Existing installed React/ReactDOM/TanStack deduped externally. SDK alias substitutes transport/events only, retaining installed SDK User and product oidcClient subscription/retirement behavior. This is simulated access, **not server authorization**.
- Every product import, source config, `@` alias from that config, installed SDK import and ordinary build path binds to V10 validation-01. The inherited inert plugin label `explicit-v9-sdk-boundary` and legacy build receipt filename do not select V9 source; exact content is manifested.
- Fixture route: `http://127.0.0.1:4200/w/w/projects/p/publication?publicationFixture=1`. Loopback and explicit opt-in enforced in entry/SDK/server; no ordinary fallback. Ordinary route separately navigated at port4201 with no fixture query/provider.

## Results (machine-derived)

| Run | Scenarios PASS/FAIL | Assertions PASS/FAIL | Native tests exit |
|---|---:|---:|---:|
| matrix-04 | 10 / 0 | 37 / 0 | 0 |
| matrix-05 | 10 / 0 | 37 / 0 | 0 |
| supplemental-01 | 4 / 0 | 12 / 0 | 0 |
| restricted-02 | 2 / 0 | 6 / 0 | 0 |
| overflow-01 | 1 / 0 | 2 / 0 | 0 |

Core final matrices: **20 scenario executions / 10 unique IDs; 74 assertion executions / 37 distinct assertion names**. `FIRST_MATRIX_VERIFIED.json` was written after parsing complete matrix-04 PASS, before matrix-05 launched. Same core test runner used in both.

Including supplemental successful runs: **27 scenario executions / 17 assigned IDs; 94 assertions / 53 distinct names / 41 repetitions**. Assigned IDs are not all distinct user journeys: supplemental network-accounting IDs repeat the core network audit. Supplemental scenarios ran once, not twice; do not describe this as two repeats of every supplemental assertion. `COUNTS.json` separately preserves all incomplete/failed runs and their totals. `SCREENSHOTS.json` includes **74** screenshots across successful and failed attempts; do not treat failure screenshots as green evidence.

## What was actually exercised

- Ordinary final build reaches **Workspace context unavailable** after actual local bootstrap GET receives503; no loaded Publication rows or `__V10`. Ordinary source-not-connected component is behind unavailable Project bootstrap and was **not separately reached**. This is unavailable ordinary-route evidence, not loaded ordinary integration.
- Actual shell publication route, source read request scope, EN/zh-CN desktop1440 and narrow390 list/calendar width bounds; loaded March bilingual calendar captures, narrow dialog.
- Native CDP mouse clicks, Input.insertText search, Enter default-action check, initial dialog focus, Tab/Shift+Tab containment, Escape/launcher focus return. All publication buttons explicitly `type=button`; Enter produced no submit event. This input is not inside a submit form, so it does not establish unrelated form implicit-submit behavior.
- Native month navigation across December/January and leap February29, actual Today, UTC/New_York cross-midnight and DST-before/after source instants, unscheduled/invalid-offsetless separation, seven-row March10 agenda and native five-more overflow. Zone change did not reread source and preserved exact source timestamps.
- Shared account/status/search state in list/calendar; same-platform distinct stable account IDs; unknown raw status; equal-time plan-ID order remains stable ascending and descending.
- Independent try1/try2/external1 identities; permitted safe failure summary; restricted title/summary/copy/artifact/media/failure/URL sentinels absent from entire document outerHTML (including attributes), permitted identities retained, denied artifact reference omitted. List grant withdrawal removes rows/details. External URL never became a link.
- Refresh removal, read error/retry, partial empty, complete empty, selection/query/zone/scroll preservation, safe focus fallback when selection disappears, refresh/same-ID nonrevival.
- Same-context trusted SDK renewal retains open browsing. Actual subscribed UserUnloaded retires source binding, removes detail and prevents old-binding reread. Fresh owner binding can read without reopening detail. Scope replacement/late receipts and aborted reads exercised.
- Actual retained React button props and input/select callbacks invoked programmatically after scope retirement: old date/view/filter/sort/zone/open/refresh handlers inert. Old detail dismiss cannot close a fresh same-ID occurrence. These are retained real callbacks, not fabricated duplicate implementations.

## Preserved failures and diagnosis

No confirmed product defect was established. No product correction was made.

1. `matrix-01`: inherited helper incorrectly waited for `.ff-app-shell` on ordinary unavailable bootstrap, although passive DOM correctly showed Workspace context unavailable. Corrected only helper readiness to `.ff-root`; ordinary assertion retained. Native exit1, zero assertions, evidence preserved.
2. `matrix-02`: runner JavaScript selector quoting SyntaxError during calendar assertion; corrected Python-to-JS quote encoding. Original runner saved as `runner-pre-quote-fix.py`; native exit1 and earlier14 passing assertions preserved.
3. `matrix-03`: returning a retained React props array by value exceeded CDP object reference depth. Corrected probe to retain in page and return scalar true; no product assertion weakened. Saved `runner-pre-reference-fix.py`; native exit1, earlier33 passing assertions preserved.
4. `restricted-01`: **one actual failed assertion**, caused by incorrect oracle expecting denied artifact ID `output` to remain. Full DOM showed its safe omission; model.ts45–48 explicitly filters both artifacts and plan references by separate artifact grant. Sentinel omission passed. Original `runner/restricted.py` and failure remain unchanged; `RESTRICTED_ORACLE_DIAGNOSIS.md` explains corrected new runner, which asserts permitted plan/attempt/external IDs and explicitly denied artifact omission. This is not a security leak or demonstrated product defect.

No actual tool refusal occurred. Browser diagnostics retain expected ordinary503/API errors and missing vite.svg404; matrix-02 retains the harness SyntaxError. These were not silently discarded.

## Network accounting and isolation

`NETWORK_TOTALS.json` keeps Network events, Fetch interception events and actual receiver requests separate. For each final core run: **49 browser events,21 interceptions,45 actual receiver requests** (receiver includes health/served-manifest fetches). Every recorded run has zero browser/intercepted/receiver mutation attempts and zero interceptor-blocked attempts. Do not sum these independent streams as unique requests.

Chromium proxy/DNS restricted non-loopback traffic; Fetch allows only127.0.0.1 ports4200/4201. Servers never forward APIs; API GETs return503 and mutation verbs would log403. No backend/real canonical/social requests or real publishing account connection. Core source reads are in-memory fixture adapter calls, not HTTP Publication API evidence. `BOUNDARY_LOGS.json` stores request/abort/SDK event evidence for applicable runs. `ACTUAL_RECEIVER_REQUESTS.json` and JSONL preserve actual receiver observations, including ordinary bootstrap failures.

## Hash binding, commands, cleanup

`INPUT_BINDING.json` captured inputs before preparation. `FINAL_HASH_BINDING.json` + each run's `SERVED_MANIFEST.json` bind fixture/source/runner/build configuration/output and served bytes. Summary recomputed every served disk SHA256 against wire SHA256, and confirmed **8,008 snapshot files +11 ordinary build files unchanged**. Dependency symlinks excluded from that census; dependencies were not installed or changed.

Build command: `python3 browser-v10/build_run.py` (invoked by absolute path from `/home/user`), exit0. Exact underlying bwrap/node argv, UTC start/end and native exit in `BUILD_FINAL03_COMMAND.json`; output `build.log`.

Native command pattern (absolute taskroot path used):
```
python3 browser-v10/runner/run.py matrix-04 runner/tests.py
python3 browser-v10/runner/run.py matrix-05 runner/tests.py
python3 browser-v10/runner/run.py supplemental-01 runner/supplemental.py
python3 browser-v10/runner/run.py restricted-02 runner/restricted-corrected.py
python3 browser-v10/runner/run.py overflow-01 runner/overflow.py
python3 browser-v10/summarize.py
```
All above exit0; run.py prints `NATIVE_EXIT 0`. Earlier exit1 commands retained in per-run COMMANDS/tests.log and manifest index. `NATIVE_COMMANDS_INDEX.json` records exact process argv/PID/start/end/exit; `NATIVE_COMMANDS.json` per run records actual timestamped CDP input/evaluation commands. Chromium **149.0.7827.55**; executable `/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`.

Every scoped child was terminated/waited via its owned process group. Final independent `FINAL_TEARDOWN.json` verifies recorded PIDs absent and ports4200/4201/9279 refusing connections. Summary output `BINDING_NETWORK_TEARDOWN_VERIFIED`.

## Screenshots for parent actual visual inspection

Absolute paths and SHA256 in SCREENSHOTS.json. Recommended relative paths:
- `overflow-01/loaded-march-en-1440.png`, `loaded-march-en-390.png`, `loaded-march-zh-CN-1440.png`, `loaded-march-zh-CN-390.png`, `DST-agenda-narrow.png`.
- `matrix-05/english-detail.png`, `attempt-details.png`, `filters.png`, `ordinary-desktop.png`, `ordinary-narrow.png`, `session-retired.png`, `late-nonrevival.png`.
- `supplemental-01/narrow-detail.png`, `complete-empty.png`, `old-dismiss-new-occurrence.png`, `old-controls-retired.png`.
- `restricted-02/restricted-metadata-details.png`, `list-denied.png`.

Captured DOM/geometry is machine-checked, not a claim that the child visually reviewed every screenshot. Parent requested responsibility for representative visual inspection remains open.

## Limits

No real IdP/server access contract, account/channel integration, canonical mutation, scheduler, media access, screen reader, IME, touch or physical device/keyboard evidence. CDP native events execute Chromium default actions; DOM scrollIntoView/select change helpers and retained-props/fixture-source probes are disclosed programmatic aids. Restricted supplemental probe obtains the external fixture source through React props, changes its test-only adapter/access, then uses host owner replacement; it does not modify product implementation or real credentials.

Coverage is representative, not exhaustive over all timezone/DST transitions, malformed receipts or lifecycle permutations. In particular no dedicated physical-device ergonomics or separate Project/tenant-route change matrix is claimed; native scope-session/owner and SDK-session boundaries were exercised. SDK same-context and logout events are simulated transport events, not a real identity provider. Current date is native run clock; 2024 source calendar navigation is explicit, not a product Date override. Ordinary loaded source integration remains unavailable. Parent final review is not replaced by these results.
