# V7 bounded writer scope and source map

## Authority, worktree, and instruction precedence

- Owner task: `FRONTEND_WAVE2_RENDER_OBSERVABILITY_V7`, frontend lane, bounded implementation in `/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1` on `agent/frontend-wave2-product-ux-v1`.
- Recovered source: accepted working tree `31f1b0b668e5538ca2960afe3c4b6ec5b74d74ee` over repository HEAD `f5e19cf53fd010eea2935dd29557e82a879e042c`; `recover.py` reconfirmed 1,004 scoped paths with exact membership, bytes, modes, and unchanged real index.
- Applicable repository instruction: root `AGENTS.md`; no nested `AGENTS.md` exists below the target paths.
- Conflict and precedence: root governance normally requires freezing an exact candidate SHA before verification. The current Owner brief expressly requires `NO COMMIT/FREEZE` and forbids staging, committing, touching refs, or the real index. The newer task authorization therefore overrides the freeze instruction for this writer pass. No candidate commit will be created; independent controller review remains required. Product freeze remains forbidden under this authorization and would require separate Owner authorization; controller review does not imply permission to freeze.
- Prohibitions retained: no build, backend inspection or work, remote operation/publication, staging, stash, reset/clean, commit, merge, ref mutation, or final acceptance claim. Historical H4/guards and sealed V6 evidence remain untouched.

## Exact selected plan item

Implement only the already-prioritized `Render observability` item from `docs/architecture/governance/frontend-product-information-architecture-v1.md`, following the adopted order `SceneShot > Render observability > Workflow UX > NLE > Agent`. Extend the existing `/operations/renders` Render browser; stop before Workflow UX.

## Actual sources inspected and disposition

| Source | Disposition for V7 |
|---|---|
| `frontend/src/product/render-browser/{RenderBrowser.tsx,source.ts,fixture.ts}` and focused tests | Existing V2/V3 real implementation base; extend in place, do not create another Render center, route, registry, or permission system. |
| `frontend/src/contracts/app/render-job.ts`, `frontend/src/api/render-jobs.ts`, existing render routes/components | Real existing five-field summary and legacy transport/routes inspected first. They do not cover the requested coherent task/attempt/progress/failure/artifact observability envelope. Reuse their established identity vocabulary where compatible; do not call their polling/HTTP wrappers or claim their DTO as the richer accepted contract. |
| `frontend/src/product/production/{types.ts,model.ts,source.tsx,simulatedSource.ts,ProductionBrowser.tsx}` and tests | Production Scene/Shot V6 implementation pattern; reuse strict host-agreed EffectiveAccess binding, explicit simulated injection, exact identity/scope receipts, owner lifetime, StrictMode re-registration, abort/generation retirement, opaque status, bounded completeness, and safe text rendering patterns. |
| `frontend/src/foundation/effectiveAccess.tsx` | Existing authoritative frontend projection consumer; reuse. UI visibility never grants Render or Artifact read authority. |
| `frontend/src/interaction/{SelectionContext.tsx,model.ts}` | Existing sole selection owner lifecycle; reuse for owner/document retirement and fresh `pageshow` rebind. No new owner or registry. |
| `frontend/src/interaction/InteractionDialog.tsx`, design system, horizontal AppShell and route tree | Reuse the current dialog focus contract, controls, shell hierarchy, and existing `/operations/renders` route. |
| `frontend/src/product/notifications/types.ts` | Existing independent destination-access pattern inspected. V7 exposes no Artifact navigation because no existing typed Artifact application route plus independent target-access receipt is established. |
| `frontend/src/localization/{catalogs.ts,source-manifest.json}` | Extend both bundled English and zh-CN presentation catalogs; source values remain literal and locale-independent. |
| `frontend/src/styles/foundation.css` and `frontend/src/product/production/production.css` | Existing responsive/narrow-scroll styling inspected. Prefer one focused new `render-browser.css`; foundation CSS remains unchanged unless a verified shared need emerges. |
| `frontend/governance/UX_WAVE_1_REVIEW.md` | Append only the Owner-adopted V6 read-only review with the fixed evidence identities in the brief; do not rewrite sealed V6 history. |
| `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv` and API gap ledger | Update existing `FB-GAP-005` only; do not add duplicate IDs or invent agreed endpoint/permission/schema. |
| current governed-scope ledger and product path classification | Register only the new focused Render stylesheet; existing paths retain their current entries. |
| build config (`frontend/package.json`, `vite.config.ts`, `vitest.config.ts`) | Inspected only. Build is prohibited; no build/config change planned. |
| `/home/user/Documents/03-大模型上下文-精简版.md` | Read fully. Canonical state, authorization, Artifact identity, execution attempts, projections, and frontend status remain independently authoritative; proposals are not current backend capability. |

## Contract and behavior plan

1. Replace the fixed real permission literal with an explicit host-agreed SERVER EffectiveAccess binding; preserve a distinct test-only unagreed fixture binding. Ordinary production route stays unconfigured/unavailable and performs no request. Remove the URL-triggered fixture path.
2. Define the smallest strict `FRONTEND UNAGREED` read projection required by the UI: principal/tenant/session/Project/request ownership; bounded or complete snapshot/version/freshness; Render identity/name/literal status/source/time/progress/task/version; optional explicit attempts, safe failures, and Artifact metadata-state records. No endpoint or server DTO is asserted.
3. Validate required identities without trimming, receipts, Project ownership, duplicate Render/attempt/Artifact IDs, explicit attempt parent/retry and task links, ISO source times, finite progress values, bounds, and completeness. Preserve unknown source status literally. Unsafe failure/explanation content fails closed rather than displaying credentials, private paths, or raw traces.
4. Derive a percentage only for finite nonnegative values with a positive total, matching supplied units, and value not exceeding total. Never clamp invalid progress, synthesize progress/ETA/order, or use timers.
5. Keep list search over supplied ID/name, source-supported status filters, stable name/ID sort, Reset always focusable in active results, current-snapshot disclosure, and stable Refresh/Cancel/Retry. Preserve filters and reasonable list scroll/focus across refresh/detail return; late/cancelled/retired results cannot restore data.
6. Detail is read-only and distinguishes missing/partial values; task and attempt statuses remain separate; attempts are only supplied records; Artifacts distinguish missing, empty, bounded, denied, unavailable, unknown, stale, and inspectable metadata. No Artifact open/download/arbitrary URL/storage path is accepted.
7. Model unavailable, denied, unknown, unsupported, error, invalid, stale, cancelled, empty, no-match, detail-not-found, invalid-relationship, missing, and partial outcomes without retaining old sensitive content.
8. Exercise behavior-focused tests for progress validity, failures, Artifact states, access/unconfigured behavior, identity/access/Project/source and Selection-owner retirement, StrictMode, cancellation/retry/late results, invalid refs/detail removal, list controls/focus, and EN/zh-CN.

## Precise expected repository changes before product editing

The exact allowlist is machine-readable in `ALLOWLIST.json`. Planned production/test paths are the five existing files under `frontend/src/product/render-browser/`, one new focused `render-browser.css`, `frontend/src/localization/{catalogs.ts,source-manifest.json}`, and the existing route integration test. Planned governance paths are the existing acceptance record, existing backend request TSV, existing gap/IA documents, and both current ledgers. No other repository path is authorized for this writer pass.

## Bounded writer correction continuation

The prior writer exited successfully; its intentional 15-path result is preserved. This continuation verifies the four interim observations against current bytes. Planned corrections are confined to `source.ts`, `source.test.ts`, `RenderBrowser.tsx`, `RenderBrowser.test.tsx`, and the two localization files already in `ALLOWLIST.json`. External evidence changes are this freeze wording correction, new named correction logs/state, and separate `WRITER_CORRECTION_HANDOFF.md`; the prior handoff and controller helpers/fixture host/browser files are preserved. Root `AGENTS.md` applies with no nested target instructions; the full Owner context document was read. No ancestor instruction files were found. The newer Owner no-commit/no-freeze restriction overrides root freeze-before-verification; permanent instruction alignment remains a separate governance task. Run only targeted behavior tests, typecheck, lint, and read-only scope/whitespace checks; controller owns exact-tree final gates/browser/package. No recover.py rerun or index/ref mutation.
