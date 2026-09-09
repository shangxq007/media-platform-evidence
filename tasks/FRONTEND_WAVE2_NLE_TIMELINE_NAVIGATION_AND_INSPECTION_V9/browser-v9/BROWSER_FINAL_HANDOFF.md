# V9 Native Browser Handoff — BLOCKED / INCOMPLETE

**This is not browser acceptance. Do not count it as a passed gate.**

## Stable input and scope
- Input tree: `a90af5baccf94a437b67e69fb1897328572a0209`; source `../validation-02/snapshot/frontend`; ordinary final bytes `../validation-02/build`.
- Read writer/VERIFICATION_INTERFACE.md, writer/CORRECTION_02_HANDOFF.md, correction-02/VERIFICATION_INTERFACE_ADDENDUM.md, snapshot AGENTS.md and relevant final route, NleWorkspace, navigation, gateway, Selection, InteractionDialog, SDK wrapper and localization source.
- Only browser-v9 contains writes. No product edits, canonical writes, backend, credentials, publication, Skill/Memory actions.
- Existing V8 Chromium helper mechanics were copied as a template only; no prior result counts or screenshots reused.

## Implemented and executed
- Explicit loopback opt-in fixture entry wraps the actual existing NLE router with TimelineNavigationProvider. Actual NlePage, ProjectFrame, default timeline query gateway, Axios versionless transport, shared Selection and InteractionDialog remain in source.
- Isolated GET receiver supplies strictly separate HEAD/history/detail/compare simulation. Navigation projection is an in-memory provider, not HEAD authority. Actual gateway retains its historical Project==Timeline mapping, not independently proven identity.
- SDK alias injects UserManager transport/events and config only; installed SDK User and actual oidcClient wrapper remain. Simulation is NOT real authorization. Ordinary final build is independently served without these aliases or implicit fixture fallback.
- External Vite production build succeeded, configLoader `bundle`, React/TanStack deduplication; exact argv/start/end/exit in BUILD_COMMAND.json, output in build.log. Initial EROFS failure is retained in failures/build-01. Repair mounted task-owned vite-temp over dependency cache only inside bwrap; source stays read-only.
- Native headless Chromium launched via CDP under read-only-root bwrap. Two loopback receivers served fixture and ordinary final builds; every file's served SHA256 matched its disk SHA256 (probe-01/SERVED_MANIFEST.json).
- Browser actually navigated `/w/workspace-1/projects/project-1/edit?nleFixture=1`, loaded the product shell/NleWorkspace, and made real local GET requests for current revision and revision history; receiver returned 200 for both.

## Failure and blocking tool refusal
1. `probe-01/tests.log`: timed out waiting for `[data-navigation-object]`. This is a precondition failure, **not yet a product defect**. The needed follow-up DOM/state inspection did not run successfully.
2. First teardown recorded a transient port-release race; a subsequent live read verified all scoped ports refused connections. The helper was adjusted to delay final release checking; this does not change product source.
3. `probe-02` failed before spawn because bind-based preflight did not set SO_REUSEADDR, despite the ports refusing connections (TIME_WAIT is a likely explanation, not proved).
4. The next external harness repair/re-run request was explicitly blocked by the tool: **“BLOCKED: execute_code script timed out without user response. The user has NOT consented to running this code. Do NOT retry, do NOT rephrase the script, and do NOT attempt the same outcome via a different tool. Silence is not consent.”** No bypass or further browser execution was attempted. Parent/Owner must resolve permission before continuing.

## Verified accounting (Python-derived persisted JSON)
See COUNTS.json and preassigned SCENARIOS.json:
- 15 preassigned unique scenarios.
- **0 completed unique scenarios; 0 completed scenario runs.**
- **0 native assertions; 0 distinct assertions; 0 repetitions.**
- 1 actual native probe run; 1 precondition failure.
- **Screenshot list: empty (0)**. No screenshot-only claims, no screenshot review possible.
- Browser Network events: 10 requests. Fetch interception events: 10; 0 blocked by interceptor; 0 observed POST events. These only describe the incomplete mount probe, **not** a navigation zero-operation guarantee.
- Actual/blocked attempts are separately preserved in BROWSER_HTTP_REQUESTS.json, ALL_INTERCEPTED_ATTEMPTS.json and receiver HTTP JSONL. Ordinary served-byte manifest fetches are not ordinary browser execution.

## Outstanding — all remain unverified
- Ordinary entry native-browser behavior; desktop/narrow native mouse/keyboard/focus, bilingual labels, geometry, long names.
- Full discovery/filter/exact-time locate/locate-selected/selection/inspect/close/continue chain.
- Loading/empty/error/retry, revision/source/access/identity retirement, late responses.
- IR01-1 retained real toolbar callbacks; IR01-2 modal nonrevival and focus fallback.
- No-new-Operation/media assertions across actual navigation scenarios.
- Representative screenshots and actual parent visual review; final independent acceptance review.

## Evidence files
- `fixture-host/{entry.tsx,sdk.ts,oidc-config.ts,fixture.html}`, `build.mjs`, `build_run.py`, `server.py`, `run.py`, `probe.py`, copied `browser_helpers.py`, `chromium_helpers.py`, `control.py`.
- `ARTIFACT_MANIFEST.json`: source/fixture/fixture-build/ordinary-build byte hashes.
- `probe-01/{COMMANDS.json,CHROME_VERSION.json,SERVED_MANIFEST.json,NATIVE_COMMANDS.json,BROWSER_HTTP_REQUESTS.json,ALL_INTERCEPTED_ATTEMPTS.json,BROWSER_DIAGNOSTICS.json,fixture-http.jsonl,ordinary-http.jsonl,tests.log,TEARDOWN.json}`.
- Failures preserved separately from successful fixture build: failures/build-01, probe-01 and probe-02. These are not green scenario runs.

## Teardown
- probe-01/COMMANDS.json records all spawned child exits; its immediate TEARDOWN.json captured the transient release race honestly.
- Final independent port check at `2026-09-09T02:23:20.436542+00:00`: ports **4200, 4201, 9279 each connect_ex=111 (connection refused)**; command exit 0.
- No servers/browser were spawned after the refused rerun request.

Native events design uses CDP Input dispatch; DOM geometry/scroll/focus helpers and programmatic retained-callback/store probes must be disclosed when implemented. Current work does not substitute jsdom for browser verification and does not claim real data integration.
