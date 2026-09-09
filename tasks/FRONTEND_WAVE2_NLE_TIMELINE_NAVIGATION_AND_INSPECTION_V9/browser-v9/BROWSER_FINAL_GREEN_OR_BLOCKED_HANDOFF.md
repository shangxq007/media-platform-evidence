# FINAL V9 — native Chromium scoped GREEN

Both final full matrices passed on **validation-03/snapshot**, implementation tree **37d003fc4f55faf166cd836a6ea93d77eb8b6a1e**. Previous V9-02 RED now passes without weakening its assertions. This is GREEN for the assigned isolated/browser-boundary matrix, **not backend-integrated ordinary loaded NLE acceptance**. Parent must visually inspect screenshots and independently verify evidence before its acceptance decision.

All paths below are relative to `/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NLE_TIMELINE_NAVIGATION_AND_INSPECTION_V9/browser-v9` unless absolute.

## Executed results

| Final native run | Scenarios | Assertions | Screenshots | Native exit |
|---|---:|---:|---:|---:|
| final03-run-01 | 15 PASS / 0 FAIL | 89 PASS / 0 FAIL | 16 | 0 |
| final03-run-02 | 15 PASS / 0 FAIL | 89 PASS / 0 FAIL | 16 | 0 |

Persisted computation: `FINAL03_COUNTS.json`, `FINAL03_SCENARIO_RESULTS.json`, `FINAL03_ASSERTIONS.json`. Total **30 scenario executions**, **15 distinct scenarios**, **178 assertion executions**, **89 distinct assertion names**, **89 repeated assertion executions**, **32 screenshots**, zero failures. Counts apply only to these two new final runs; prior RED and harness artifacts are not reclassified.

`runner-final03/final_tests.py` preserves all original `continuation_tests_04.py` check expressions and names. `FINAL03_ASSERTION_PRESERVATION.json` compares their ASTs: 54 original static check call sites retained, four additional sites (58 total). Loops expand these into 85 original + four added assertions per run. No failure retries occurred. The first complete run was independently parsed for 15 PASS scenarios and all 89 passing checks before the second was started.

### Corrected native default action and independent Enter boundary

Each run's `LOCATE_SELECTED_DIAGNOSTIC.json` records:
- Native second-clip click selected `clip:clip-2` before native Locate selected clip activation.
- After activation: selected **clip:clip-2**, position **1001/30000**, passive submit log **[]**.
- Locate selected clip resolves to explicit DOM `type="button"`; Locate time remains explicit `type="submit"`.

Then, additively and after the original success assertion/screenshot, the test focuses the actual time input, inserts `1001/30000`, and sends CDP **Input.dispatchKeyEvent Enter keyDown/keyUp** with native Enter text semantics. No requestSubmit, dispatchEvent submit, handler invocation, submit cancellation, or button patch implements this check. `NATIVE_ENTER_DIAGNOSTIC.json` records exactly one native form submission with submitter **Locate time**, type submit, exact position **1001/30000**, selected **clip:clip-1** and two inclusive boundary matches. Focus remains in the actual input. This demonstrates the corrected non-submit action and the unaffected implicit-submit path separately.

## Source, fixture, build, aliases and served-byte binding

New namespaces only:
- Fixture: `fixture-final03/` (four host files and symlink to existing installed dependencies).
- Injected production output: `build-final03/`.
- Build configuration/receipt: `build-final03.mjs`, `build_final03.py`, `build-final03.log`, `BUILD_FINAL03_COMMAND.json` (exit 0).
- Isolated runner/helpers/server/tests: `runner-final03/`.
- Runs: `final03-run-01/`, `final03-run-02/`, each with independent HOME/profile.

All fixture source imports, SDK installed User import, build Vite import, source config path, and ordinary runner build path refer to **validation-03**, never validation-02. The actual snapshot `frontend/vite.config.ts` supplies `@` -> its own `./src` alias; external config overrides fixture root/output and adds only explicit SDK/oidc-config seams. The external entry imports actual `src/app/routeTree`, localization, platform client, effective access, TimelineNavigationProvider and styles. It renders the actual NLE route, ProjectFrame/NleWorkspace, TimelineNavigation, shared selection bar/inspector and dialogs, not duplicate UI markup. Adapter origin remains the required **isolated-verification**.

Existing dependency target: `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/node_modules`. No install occurred. React, React DOM and existing TanStack packages retain explicit dedupe configuration. Build executes in read-only-root bwrap; the installed Vite temporary target is bind-mounted to new external `vite-temp-final03/`. Product and ordinary outputs are not writable.

`FINAL03_HASH_BINDING.json` binds the exact source snapshot, ordinary output, fixture files, new injected output, new runner, build configuration/receipt and each run's `SERVED_MANIFEST.json`. Every served ordinary and fixture file was fetched and its SHA256 matched disk; the summary rechecked those disk hashes. This establishes exact inputs/configuration and disk-to-wire binding, not a claim that injected and ordinary bundles are bit-identical or reproducibly identical.

`FINAL03_BEFORE_MANIFEST.json` and `FINAL03_PRESERVATION.json` verify unchanged **8,001 snapshot files**, **11 ordinary-build files**, and **1,889 pre-existing browser files** inventoried before preparation (excluding dependency symlinks). All earlier handoffs, old fixtures/builds, continuation-run-04/05 RED and the established test script remain unchanged. No product edits or ordinary gate reruns were performed.

## Ordinary native build and scenario scope

V9-01 separately navigated actual unchanged **validation-03/build** at `http://127.0.0.1:4201/w/workspace-1/projects/project-1/edit` in Chromium. The real workspace bootstrap GET reached the explicit local no-backend receiver, got 503, and the route settled on **Workspace context unavailable**. Desktop and narrow screenshots/DOM were captured. It had no `__V9`, navigation objects or fabricated Loaded timeline projection. This is native unconfigured-boundary validation, not merely a byte fetch and not proof of ordinary loaded navigation.

Both final runs pass all assigned IDs:
- V9-02: bounded discovery/filter, exact rational/shared inclusive boundary, explicitly selected clip preservation, plus actual Enter implicit submit.
- V9-03: native arrows/I/Tab/held Shift+Tab/Escape, dialog focus trap/return, continued selection and exact supplied range/asset metadata.
- V9-04/05: exact Chinese labels and dialogs, Chinese narrow, English desktop/narrow, long-name title preservation and width bounds.
- V9-06: loading/bounded-empty/error/retry/ready and disabled unknown-time locate.
- V9-07/08/09/10: revision, replaced source, denied access, actual subscribed SDK UserLoaded identity boundaries and deliberately late-response rejection.
- IR01-1: six actual retained toolbar callbacks individually inert across selection/revision/source changes; same store, retired lifetime and zero dispatch/state/focus effect assertions retained.
- IR01-2A/2B/2C: metadata/mobile clear focus fallback, batched and new-selection nonrevival, explicit mobile relaunch/Escape, each modal retired under revision and source replacement.
- V9-11: navigation canonical-operation/media/mutation attempt ledgers, including intercepted/blocked attempts.

## Network accounting: do not merge event streams

| Metric | run-01 | run-02 | Combined |
|---|---:|---:|---:|
| Browser Network events, all GET | 204 | 204 | 408 |
| Fetch-stage interceptions | 162 | 114 | 276 |
| Actual local receiver requests, including health/manifest fetches | 185 | 137 | 322 |
| Navigation-scoped Network events | 193 | 193 | 386 |
| Navigation-scoped interceptions | 151 | 103 | 254 |

Each run has **zero** interceptor-blocked attempts, intercepted mutations, browser mutations, receiver mutation attempts, receiver 403 blocks and forbidden navigation operation/media attempts. Event-stream/interception/receiver totals differ; they are independently observed and never forced into a one-to-one count. Ordinary workspace bootstrap is kept distinct from navigation scope. Network interception permits only the two loopback origins; Chromium also has non-loopback proxy/DNS isolation. Server does not forward to backend; attempted mutation handlers would explicitly log 403 rather than disappear.

Native ledgers and schema paths, for independent parsing:
- `<run>/SCENARIO_RESULTS.json`: array `{id,status,start_assertion,end_assertion,network_start,network_end,interception_start,interception_end}`.
- `<run>/NATIVE_CHECKS.json`: array `{IMPLEMENTATION_TREE,VALIDATION_TIMESTAMP,name,expression,passed,value}`; every tree is the final tree above.
- `<run>/NATIVE_COMMANDS.json`: CDP array `{tree,timestamp,method,params,result}`; inspect actual Input dispatches and evaluate readbacks.
- `<run>/BROWSER_HTTP_REQUESTS.json`: array `{url,method,type,timestamp}`.
- `<run>/ALL_INTERCEPTED_ATTEMPTS.json`: array `{url,method,allowed_to_local_receiver,requestId}`.
- `<run>/fixture-http.jsonl`, `<run>/ordinary-http.jsonl`: actual receiver records; combined `<run>/ACTUAL_LOCAL_RECEIVER_REQUESTS.json` adds receiver identity.
- `<run>/NAVIGATION_NETWORK_ASSERTION.json`: `navigation_network`, `navigation_interceptions`, `forbidden_navigation_network`, `forbidden_navigation_interceptions` arrays.
- `<run>/SERVED_MANIFEST.json`: `{build,path,bytes,disk_sha256,served_sha256}` array.
- Consolidated: `FINAL03_NETWORK_ACCOUNTING.json`, `FINAL03_NETWORK_TOTALS.json`, `FINAL03_NATIVE_COMMAND_EXITS.json`.

## Screenshots — parent visual review REQUIRED

`FINAL03_SCREENSHOTS.json` enumerates all 32 absolute paths, sizes and SHA256. Recommended actual inspection from **final03-run-02/**:
- `english-exact-locate.png` — Continuation/clip-2 remains selected at exact 1001/30000.
- `native-enter-implicit-submit.png` — focused time input, first clip selected by normal implicit submit.
- `english-metadata-keyboard.png` — native keyboard inspector/dialog.
- `chinese-desktop-metadata.png`, `chinese-narrow.png`.
- `english-longnames-1440.png`, `english-longnames-390.png`.
- `ordinary-final-desktop.png`, `ordinary-final-narrow.png`.
- `revision-retirement.png`, `late-source.png`, `metadata-nonrevival.png`.
- `mobile-track-dialog.png`; also loading/empty/error screenshots.

Child directly viewed the final run-02 locate-selected and native-Enter screenshots. Visible selected rows agree with the diagnostics: Continuation after Locate selected clip; Opening after Enter. Exact time and two-match status are visible. Extreme long names still wrap into a very tall narrow desktop inspector column; this is not a claim of ideal design or comprehensive visual QA. Other images are captured and manifested for parent's own actual inspection; child does not claim to have visually reviewed them all.

## Commands and teardown

Executed commands in browser-v9:
```
python3 prepare_final03.py
python3 build_final03.py
python3 runner-final03/run.py final03-run-01 runner-final03/final_tests.py
# Parsed first run results and asserted complete PASS before starting repeat.
python3 runner-final03/run.py final03-run-02 runner-final03/final_tests.py
python3 summarize_final03.py
```
All exited 0. Both test runner outputs: `NATIVE_EXIT 0`. Summary: `FINAL_BINDING_PRESERVATION_TEARDOWN_PASS`. Chromium: **Chrome/149.0.7827.55**, exact executable and bwrap argv/PIDs/timestamps/exits in native command receipts and per-run `CHROME_VERSION.json`. No tool denial, build failure or matrix failure occurred in this final phase.

Each run's `TEARDOWN.json` reports exited children and no remaining ports. `FINAL03_TEARDOWN.json` independently verifies all scoped spawned PIDs absent and ports **4200, 4201, 9279** refusing connections. Only scoped process groups were terminated.

## Disclosures and remaining work

The host's bounded geometry, workspace/effective-access responses and SDK transport/events remain synthetic; installed SDK User semantics and actual oidcClient wrapper remain in the source path. Real gateway HEAD/history/explicit detail GETs reach only the local fixture receiver, retaining historical Project==Timeline mapping. No real IdP, backend, authorization, media or physical-device behavior is established.

Retained actual React props/store callbacks, state invalidations and late completions are deliberate programmatic probes, not native user clicks. Open-modal revision replacement uses the actual retained history callback as a background boundary, not click-through. DOM scroll/geometry positions controls; locale helper triggers real select change handling. Text uses CDP Input.insertText and keyboard uses Chromium CDP Input events; no physical keyboard, IME or screen-reader claim.

No credentials, publication, source changes, ordinary gates, Skill or Memory writes. All child writes stay under external browser-v9. No remaining product blocker in the assigned matrix; ordinary loaded integration remains unavailable without genuine workspace/source setup. **Parent visual inspection, independent artifact verification and final acceptance decision remain outstanding.**
