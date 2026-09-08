# Browser preparation — NOT EXECUTED

Everything prepared here is external to the product. No preparation helper, build, browser, server, or acceptance gate has been run. Automatic file-write Python syntax lint succeeded; TSX and runtime behavior remain unverified until the parent executes them. Independent review is REQUIRED.

## Fixed contracts

- `P=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/browser-prep`
- Snapshot must be materialized at `P/../final-validation-01/snapshot/frontend`, with parent-provisioned `node_modules` and `../final-validation-01/FINAL_TREE.txt` containing the exact 40-character implementation tree identifier.
- `prepare_fixture_host.py` writes only under P. It does not build. It emits the external host and a Vite config using the unchanged final registered `routeTree` and ordinary `src/main.tsx` as separate entries. It extracts EN/zh labels from the snapshot catalogs, failing closed if the expected catalog shape differs.
- Build output is **P/build**, NOT product dist/static. `publicDir:false`, no product Vite config invocation, no backend proxy, no writes to snapshot dependencies. `--configLoader runner` avoids Vite's dependency-local config bundling cache.
- `run_browser.py <unique-attempt>` reads P/build directly. **No V7_BUILD_ROOT environment variable is used.** It creates `P/browser-<unique-attempt>` with exclusive creation, copies browser helpers, and writes `TREE_BINDING.json` with exact key **FINAL_EXACT_IMPLEMENTATION_TREE** (required by `control.py`). It refuses changed source/host/build bindings.
- Inherited runtime prerequisites: `/usr/bin/bwrap`, `/home/user/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`, and Python with websockets at `/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_SLICE_1C_BROWSER_HARNESS_ENVIRONMENT_CORRECTION_AND_NATIVE_VALIDATION_CONTINUATION_V1/venv/bin/python3`. Their availability has not been tested in this preparation task. Do not install or change dependencies implicitly.
- Reserved ports 4198 and 9269 must be free. Server binds loopback only. Browser children run under read-only-root bwrap, with only the new attempt directory writable, a disposable HOME/profile, and cleared inherited environment. Chromium DNS blocks remote names; browser traffic assertions reject non-loopback traffic. This is not a separate network-namespace security certification.

## Parent execution instructions (later, not performed here)

After materializing/finalizing the snapshot and performing parent-owned gates, use a shell with pipeline error propagation and retain every log:

```bash
set -o pipefail
P=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_RENDER_ARTIFACT_METADATA_ACCESS_CORRECTION_V1/browser-prep
python3 -B "$P/prepare_fixture_host.py" 2>&1 | tee "$P/preparation-01.log"
node "$P/../final-validation-01/snapshot/frontend/node_modules/vite/bin/vite.js" build --config "$P/fixture-host/vite.config.mjs" --configLoader runner 2>&1 | tee "$P/build-01.log"
# Only after successful build exit:
python3 -B "$P/bind_build.py" 2>&1 | tee "$P/binding-01.log"
python3 -B "$P/run_browser.py" final-01 2>&1 | tee "$P/browser-launch-final-01.log"
```

Stop immediately if a command fails; `set -o pipefail` propagates pipeline status but does not itself abort an interactive sequence. Use separate commands and inspect each exit, or add `set -e` in an isolated execution script. Parent may apply its own stronger sandbox to preparation/build. Do not invoke the product vite.config.ts, whose outDir targets backend static resources.

Preparation refuses to overwrite `fixture-host`; binding refuses to overwrite `BUILD_BINDING.json`; runner refuses to reuse an attempt directory. Preserve failed attempts/logs/screenshots. If changes require rebuilding, archive the entire current host/build/binding and retain prior manifests before parent-authorized rematerialization. A browser-only rerun uses a new label, e.g. `final-02`, without changing the sealed build. Do not change or execute old V7 helpers in place.

## Coverage and interpretation

`PLAN.json` is the machine-readable matrix. Both EN and zh-CN run the full mixed/revocation/race core at 390x844; EN also runs 1440x1000. Same artifact IDs and ordinary values transition from inspectable to denied/unknown/stale/unavailable using actual native Refresh reads, not render-execution retry. Detail is closed before the native background refresh and reopened afterward; this does not claim clicking inert controls behind an open modal or in-modal refresh support.

Full attribute/text DOM snapshots cover hidden descendants, titles, aria/data attributes and links, not merely visible text. Each denied item excludes all six protected fields. The shared `task-courtyard` remains independently valid in task/attempt details and the allowed item's own task link; therefore mixed checks assert its absence in each restricted item subtree, while all-restricted checks assert absence throughout the artifact section. Other restricted identity values must be absent throughout the section even in mixed mode.

The fixture controls read outcome, pending resolution, and provider access/session replacement. It intentionally ignores cancellation when delivering late replies. These are simulated adapter boundaries, not backend/auth/permission proof. Native pointer/Escape inputs, locale DOM helper, locator annotations/scroll, focus emulation, viewport-vs-device limits, and remaining interaction-owner/component-gate responsibilities are recorded explicitly in ASSISTANCE.json.

Only RESULT.json with PASS **plus** successful smoke exit, clean teardown, native check results, traffic/diagnostics inspection, verified build/served census and independent review can support acceptance. This preparation package makes no such claim.
