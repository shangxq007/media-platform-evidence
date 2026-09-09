# V9 Chromium continuation — EXECUTED, NOT ACCEPTED

**Final outcome: 15/15 assigned scenarios executed; 14 pass, V9-02 fails with a reproducible product behavior defect. Browser acceptance must remain RED. No product changes made.**

## Final evidence and accounting

Authoritative repeated final runs: `continuation-run-04` and `continuation-run-05`, both executing `continuation_tests_04.py`, both native test exit **1**.

Computed by the executed `python3 summarize_continuation.py`, not inferred from prose:
- 15 assigned unique scenarios; 15 executed unique scenarios in each final run.
- Each final run: 14 passed scenarios, 1 failed scenario; 85 native-browser assertions, 84 pass and 1 fail.
- Both final runs: 30 scenario executions, 28 pass and 2 fail; 170 assertion executions, 168 pass and 2 fail; 85 distinct assertion names and 85 repeated assertion executions.
- All five continuation runs, including historical harness failures: 75 scenario executions, 310 assertion executions, 89 distinct names. These historical runs are NOT silently reclassified as successful final runs.
- 30 final-run screenshots, enumerated with absolute paths and hashes in `CONTINUATION_SCREENSHOTS.json`.
- `CONTINUATION_COUNTS.json`, `CONTINUATION_SCENARIO_RESULTS.json`, `CONTINUATION_ASSERTIONS.json` contain computed counts, exact assertion names, expressions, results and repetitions. Each run also contains its original `SCENARIO_RESULTS.json` and `NATIVE_CHECKS.json`.

`BROWSER_FINAL_HANDOFF.md`, original `COUNTS.json`, prior failures and zero-completed counts are unchanged historical evidence. Continuation does not retroactively change the BLOCKED report.

## Acceptance blocker: native Locate selected clip submits the time form

Reproduced in both final runs; exact native sequence and state are in `NATIVE_COMMANDS.json` and `LOCATE_SELECTED_DIAGNOSTIC.json`:
1. Filter loaded clips for `Continuation`.
2. Enter `1001/30000`, click **Locate time**. Both authored ranges include that boundary; the two-match result and first clip selection are correct.
3. Natively click `clip:clip-2`. A dedicated assertion verifies the second clip is selected before continuing.
4. Natively click **Locate selected clip**. The final selected object is incorrectly `clip:clip-1`, not the explicitly selected `clip:clip-2`.
5. A passive DOM submit listener records `{submitter: "Locate selected clip", type: "submit"}`. The button has no `type` attribute and the browser resolves it to `submit`.

Source explanation, without editing it:
- `validation-02/snapshot/frontend/src/product/timeline/TimelineNavigation.tsx:191-195`: the selected-clip button is inside the locate form and omits `type="button"`.
- `src/components/design-system/index.tsx:16-17`: shared Button forwards props without supplying a non-submit default.
- `TimelineNavigation.tsx:152-156` restores the explicitly requested clip during its click callback, but the subsequent native form submission invokes `locate(input)` and selects the first boundary match again.

This is a browser-native default-action defect, not a missing fixture object or a mocked click result. No submit cancellation, button-type patch, product fix, expected-result relaxation, or disconnected-element click was used to pass it. Parent/Owner must separately authorize any product correction and rerun.

Primary failure evidence:
- `continuation-run-05/LOCATE_SELECTED_DIAGNOSTIC.json`
- `continuation-run-05/V9-02-failure.png`
- `continuation-run-05/V9-02-failure-DOM.json`
- `continuation-run-05/NATIVE_CHECKS.json`

## Actual ordinary build, separate from injected build

Chromium actually navigated `http://127.0.0.1:4201/w/workspace-1/projects/project-1/edit`, loaded the unchanged ordinary final JS/CSS, attempted the real workspace bootstrap GET, and settled on **Workspace context unavailable** after the local no-backend receiver returned 503. Desktop and narrow screenshots and DOM are saved. This is not merely a served-byte check.

V9-01 passes only its **ordinary unconfigured boundary** scope: no `__V9`, no navigation objects, and no fabricated Loaded timeline projection. It does NOT establish ordinary loaded NLE behavior, authenticated workspace availability, a configured geometry source, or backend/IdP integration. Ordinary loaded navigation remains unavailable without genuine workspace/source integration; no fixture fallback was injected into that ordinary build.

## Fixture diagnosis and external repair

Read `probe-03/DOM.json` before authoring assertions. It showed **Timeline inspection restricted or access unknown**, despite a valid HEAD revision. `navigation.ts:75` requires the exact adapter origin literal `isolated-verification`; old `fixture-host/entry.tsx` supplied `isolated-v9-native-verification-<id>`. That fixture origin violated the product contract and explained the missing objects.

Only the new external `fixture-continuation-01/entry.tsx` changes this literal to the required value. Old fixture and old build remain unchanged. A new production build lives in `build-continuation-01/`. Its first build failed because the copied fixture namespace lacked the old host's node_modules symlink. This was repaired externally using the existing installed dependency target; failure log and command receipt remain `build-continuation-01.log` and `BUILD_CONTINUATION_01_COMMAND.json`. Successful build receipt is `BUILD_CONTINUATION_02_COMMAND.json`, exit 0, with `build-continuation-02.log`.

`probe-continuation-01/DOM.json` then showed **Loaded timeline projection**, four actual navigation objects and the expected controls. Its native exit was 0. No new tool denial occurred during this continuation. The earlier denial and subsequent parent-approved retrigger remain historical and were not bypassed.

## Actual source path and simulation boundaries

Stable input tree: `a90af5baccf94a437b67e69fb1897328572a0209`.

External entry imports the actual snapshot `src/app/routeTree`, wraps it in `TimelineNavigationProvider`, and renders the real NLE route, ProjectFrame/NleWorkspace, TimelineNavigation, shared SelectionActionBar/SelectionInspector and InteractionDialog. The existing default timeline query gateway and Axios transport reach the explicit loopback GET receiver for HEAD/history/explicit revision detail. The fixture never replaces those UI components with duplicate markup.

Simulation seams remain explicit:
- In-memory navigation geometry/projection with bounded exact rational authored ranges; not HEAD authority and not real media.
- Workspace/effective-access adapter responses and SDK UserManager transport/events are synthetic. Installed SDK User semantics and the actual oidcClient wrapper remain in the built source path.
- Real gateway's historical Project==Timeline mapping remains, not proof of independent backend timeline identity.
- Ordinary build has none of the fixture aliases or source provider.

`CONTINUATION_HASH_BINDING.json` verifies every baseline source file, ordinary-build file, old fixture and old fixture-build file against the pre-continuation manifest; all are unchanged. It manifests the new host/build and harness, and binds final-run disk hashes to served-byte hashes using the exact `SERVED_MANIFEST.json` files. Build configuration/receipts provide the source-to-built entry path; no claim of reproducible bit-identical ordinary and injected bundles is made.

## Scenario coverage

| Scenario | Final status | Executed behavior |
|---|---|---|
| V9-01 | PASS, boundary only | Actual ordinary final desktop/narrow browser load, real unavailable workspace boundary, no injected/guessed projection |
| V9-02 | FAIL | Bounded discovery/filter, exact rational locate, inclusive shared boundary; native selected-clip preservation fails as above |
| V9-03 | PASS | Native Down, I, Tab, held Shift+Tab, Escape, returned focus, next-clip continuation and selection clear; exact range and supplied asset metadata |
| V9-04 | PASS | Exact Chinese discovery/time/locate/inspect labels, metadata dialog, desktop and narrow layout |
| V9-05 | PASS | English desktop/narrow geometry, full long-name title preservation, document/list horizontal bounds |
| V9-06 | PASS | Real provider loading, bounded empty, thrown error, native retry, ready recovery; unknown time basis disables locate instead of guessing time |
| V9-07 | PASS | Native explicit history/detail gateway selection retires old projection; delayed old-revision response rejected |
| V9-08 | PASS | Adapter/source replacement aborts old read; deliberately completed late response cannot revive objects |
| V9-09 | PASS | Access denial withdraws modal/data; regained access does not revive selection; late denied response rejected |
| V9-10 | PASS | Actual SDK subscribed UserLoaded path with changed identity retires pending projection; late completion cannot restore it |
| IR01-1 | PASS | All six retained real toolbar callbacks individually produce zero dispatches, zero state and focus changes after old selection, revision and source changes; same store and retired lifetime verified |
| IR01-2A | PASS | Metadata clear focus fallback; new selection, batched clear/reselect, batched hide/show and primary changes never revive prior modal |
| IR01-2B | PASS | Native narrow mobile track dialog, native clear track, main focus fallback, new clip no revival, explicit relaunch and native Escape focus return |
| IR01-2C | PASS | Each real metadata/mobile modal separately retired across revision and source replacement; selecting a new clip cannot revive prior modal |
| V9-11 | PASS | All navigation scenario Network and Fetch-attempt ledgers checked for new canonical-operation/media/mutation attempts, including blocked attempts |

Retained callbacks and boundary invalidations are deliberately programmatic probes of actual React props and the actual Selection store obtained via context dependencies. Per-callback dispatch observation is installed only for those assertions and then restored. They are not presented as native user clicks. Revision replacement under an open modal invokes its actual retained history callback as a background boundary event; no click-through of a modal is claimed. Native interactions use Chromium CDP Input events. DOM scroll/geometry helpers position controls; locale changes use the real select change handler. Text uses CDP Input.insertText; there is no physical typing or IME claim.

## Network accounting — actual, intercepted and blocked remain separate

Each final run records **204 Network request events** and **90 Fetch interception events**. They are different browser event streams, not a forced one-to-one count. Cached/browser requests and interception events must not be deduplicated together.

- `BROWSER_HTTP_REQUESTS.json`: all observed browser Network requests, with method/type/time.
- `ALL_INTERCEPTED_ATTEMPTS.json`: every Fetch-stage attempt and whether continued to the local receiver or blocked.
- `fixture-http.jsonl`, `ordinary-http.jsonl`, `ACTUAL_LOCAL_RECEIVER_REQUESTS.json`: actual receiver requests, including health/served-manifest requests, HTTP status and no-forwarding marker.
- `NAVIGATION_NETWORK_ASSERTION.json`: scenario-scoped navigation observations/interceptions and forbidden subsets. Ordinary bootstrap remains separately visible rather than counted as navigation.
- `CONTINUATION_NETWORK_ACCOUNTING.json`: counts and explicit mutation/403/interceptor-blocked lists for all continuation runs.

Both final runs observed **zero non-GET/HEAD requests, zero POST attempts, zero interceptor-blocked attempts and zero receiver mutation attempts**. These are observed results, not an interceptor-based assertion that attempted writes cannot exist. The server retains explicit POST/PUT/PATCH/DELETE 403 logging; blocked mutation attempts would be listed, not hidden. No backend forwarding, real media playback/download or canonical write was performed.

## Screenshots and visual inspection

Final screenshot index: `CONTINUATION_SCREENSHOTS.json` (absolute paths and SHA256).

Representative paths relative to this directory, for parent actual inspection:
- `continuation-run-05/ordinary-final-desktop.png`
- `continuation-run-05/ordinary-final-narrow.png`
- `continuation-run-05/V9-02-failure.png`
- `continuation-run-05/english-metadata-keyboard.png`
- `continuation-run-05/chinese-desktop-metadata.png`
- `continuation-run-05/chinese-narrow.png`
- `continuation-run-05/english-longnames-1440.png`
- `continuation-run-05/english-longnames-390.png`
- `continuation-run-05/mobile-track-dialog.png`
- `continuation-run-05/loading.png`, `empty.png`, `error.png`

Child visually inspected final-run failure, ordinary desktop and English narrow screenshots, plus run-03 metadata/Chinese narrow/mobile dialog screenshots. Visible facts: long list labels truncate with full DOM titles retained; dialogs wrap long supplied names; the narrow list and actions remain within width; the desktop shared inspector wraps the extreme long clip name into a very tall column. That is not a claim of ideal layout or comprehensive visual QA. The failure screenshot visibly selects Opening after Locate selected clip. Parent's own screenshot inspection remains required.

## Commands, native exits and teardown

Executed in this directory:
```
python3 build_continuation_01.py                         # exit 1, dependency resolution failure preserved
python3 build_continuation_02.py                         # exit 0
python3 run_continuation_01.py probe-continuation-01 probe.py  # NATIVE_EXIT 0
python3 run_continuation_01.py continuation-run-01 continuation_tests_01.py # NATIVE_EXIT 1
python3 run_continuation_01.py continuation-run-02 continuation_tests_02.py # NATIVE_EXIT 1
python3 run_continuation_01.py continuation-run-03 continuation_tests_03.py # NATIVE_EXIT 1
python3 run_continuation_01.py continuation-run-04 continuation_tests_04.py # NATIVE_EXIT 1
python3 run_continuation_01.py continuation-run-05 continuation_tests_04.py # NATIVE_EXIT 1
python3 summarize_continuation.py                        # exit 0, HASH_BINDING_AND_TEARDOWN_PASS
```

Exact bwrap, installed Python/Chromium, server and test argv, timestamps, child PIDs, native exits and scoped termination flags: per-run `COMMANDS.json`, consolidated `CONTINUATION_NATIVE_COMMAND_EXITS.json`. Chromium version is preserved per run. Helper uses read-only-root bwrap with only browser-v9 writable, new isolated HOME/profile and loopback servers; no source writes.

Historical continuation harness failures remain: initial ordinary loader timing/shell assumption, incorrect expected labels, CDP returning cyclic React-backed DOM references, and inspector-already-open setup. Subsequent scripts corrected only those harness assumptions, strengthened callback coverage and preserved all previous result files. No acceptance assertion was removed to conceal the selected-clip defect.

`CONTINUATION_FINAL_TEARDOWN.json`: every scoped continuation child PID is absent; ports **4200, 4201 and 9279 each connect_ex=111**. Per-run teardown reports no remaining ports and exited children. No unrelated processes were targeted.

## Remaining limits

- Product defect above prevents full browser acceptance; no product repair authorized to this child.
- Ordinary loaded route/source remains integration-blocked; ordinary unavailable boundary is what was actually executed.
- No physical devices/keyboard, IME, screen-reader, real authentication/IdP/backend or real authorization claims.
- No full-media or canonical operation execution claims; no product edits, ordinary gate reruns, credentials, publication or Skill/Memory writes.
- Parent visual review and independent acceptance decision remain outstanding.
