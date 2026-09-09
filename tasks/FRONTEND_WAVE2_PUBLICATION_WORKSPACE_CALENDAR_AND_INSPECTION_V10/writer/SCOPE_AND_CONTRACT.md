# V10 writer scope and actual contracts — before implementation

2026-09-09. Authority: WRITER_BRIEF.md and current Owner instruction. Only root AGENTS.md applies; no nested instructions found. Root candidate SHA freeze conflicts with explicit no-commit/no-freeze authority: apply Owner rule, preserve HEAD/index/stash; instruction alignment is a separate governance task, no instruction edit here. Existing historical Vue AppShell design says implementation paused: this is stale design intent, superseded by current Owner authority and actual React foundation. Do not adopt its fallback or permissive guards.

Recovery.json fully checked: every recorded file hash matches. before.json records branch, HEAD/parent, index digest, status, stash and instructions; before.patch preserves tracked earlier diff. Actual baseline tree 37d003fc4f55faf166cd836a6ea93d77eb8b6a1e, no commits or Git index/object/ref writes intended. External evidence only in this writer directory. Actual tool denial means stop, never retry/bypass.

## Read contracts and findings
Read checkpoint-a implementation, existing IA (including AppShell/Selection/Operation/EffectiveAccess designs and priority appendices), actual React AppShell, routeTree, ProjectFrame/projectContext/platformClient, EffectiveAccessEntry/getEffectiveAccess, SelectionProvider/store/dispatcher/SurfaceAdapter, InteractionDialog, references, TimelineNavigation V9 lifecycle, Operation gateway, existing backend requests/gap ledgers and current/classification ledgers. Repository search found no DOM-PUBLICATION-001, PublicationAttempt, ExternalPublication, Postiz or publication query implementation in contracts/frontend/current architecture. No publication surface exists. Actual platform access catalog returns unknownAccess; Workspace→Project relationship remains BLOCKED. Operation gateway is Timeline authority and is not reused for publication. ArtifactRef is logical identity but there is no supported stable publication-to-artifact destination/access predicate; expose permitted logical refs as inert text only.

Recover DOM-PUBLICATION-001 as PROPOSAL, not discovered implemented backend authority: OutputArtifact → PublicationAttempt → ExternalPublication. Plans/intents, attempts and external outcomes are separate explicit IDs/relationships, preserve many attempts/account outcomes and literal unknown statuses. ObservationSet with observedAt and raw platform metrics semantics remains historical proposed analytics only, no metrics code.

## Proposed consumption and lifecycle
FRONTEND_CONSUMPTION_PROPOSAL; REAL_BACKEND_CONTRACT_NOT_ESTABLISHED. Provider-neutral isolated explicit host supplies PublicationSource (scope principal/tenant/session/Workspace/Project/source, owner object, adapter, independent EffectiveAccess catalog), PublicationSourceProvider/PublicationWorkspace source prop. No real or default fixture adapter, network, credentials, URLs, persistence or writes. Native SDK retirement subscription reuses V8/V9 behavior on the new page without rewriting auth. Same valid renewal remains stable; semantic source/access/context/owner changes remount local consumer and abort/reject prior receipts and retained callbacks; Selection remains sole owner. Source allowed flags are ignored: explicit host access entries must match test-only keys and existing EffectiveAccess AVAILABLE with satisfied/not-applicable factors. This proves frontend simulation only. Listing does not grant copy/artifact metadata: independent keyed content and artifact grants redact all such values before UI or Selection. Backend must independently trim responses; client omission is not confidentiality authority.

Read request echoes exact scope, request ID and fixed Project snapshot query (limit 200). Response validates scope/query, bounded/partial/complete boundary, IDs, explicit account/plan/attempt/external relationships. No joins by title/time/order. Local filters/search/sort operate on supplied permitted current-Project content; completeness always visible. Unknown status remains raw. Errors/restricted/invalid remove current snapshot and accessless details. Same-context refresh preserves query/month/day/timezone/view/scroll and restores still-valid selection; detail closes for revalidation and never revives. Close returns focus, disappearance uses region fallback.

Explicit timeField scheduledAt/publishedAt/unscheduled/unknown chooses calendar bucket; only strict offset/Z instants accepted. Omitted/null/malformed/offsetless values remain indeterminate, separate from explicitly unscheduled. Display timezone chosen from Intl-supported zones, presentation only. Gregorian month/day calculation and zoned Intl formatting avoid parsing date-only strings as UTC or assuming 24-hour local days; displayed interval is start local date inclusive to next-month local date exclusive. Sort uses selected explicit timestamp with deterministic ID ties and missing/invalid values last. No NLE media-time reuse, publish inference, scheduler, week/drag/reschedule or analytics.

## Priority and documentation
Append to existing IA: newly prioritized Publication workspace after bounded V9 acceptance, full NLE editing/Agent later; Postiz single-channel technical pilot/real publishing separate; heatmap/cross-platform analytics deferred. Append V9 acceptance to existing UX review only, including retained long-title inspector limitation and no full NLE/media/backend/EP19/Slice1C/product closure. Add FB-GAP-014 in existing requests/gap ledger (next actual convention; no relevant publication ID exists). Future one Project/OutputArtifact/account/content version → backend intent → single scheduler → attempts/external outcomes requires scoped access, paging/completeness, timezones, safe metadata, statuses, idempotency, errors/credential expiry and pinned Postiz adapter dependency. H4 Proposal A current ledger append only, no historical ledger changes/debt-zero claim. Architecture guard is initially unchanged; only exact expected inventory extensions if a concrete gate requires it, preserving negative controls.

## Exact proposed paths
- `frontend/src/product/publication/types.ts`
- `frontend/src/product/publication/model.ts`
- `frontend/src/product/publication/model.test.ts`
- `frontend/src/product/publication/PublicationWorkspace.tsx`
- `frontend/src/product/publication/PublicationWorkspace.test.tsx`
- `frontend/src/product/publication/publication.css`
- `frontend/src/foundation/surfaceRegistry.ts`
- `frontend/src/foundation/surfaceRegistry.test.ts`
- `frontend/src/app/routeTree.tsx`
- `frontend/src/app/routeTree.test.tsx`
- `frontend/src/surfaces/FoundationPages.tsx`
- `frontend/src/components/app-shell/AppShell.tsx`
- `frontend/src/localization/catalogs.ts`
- `frontend/src/localization/source-manifest.json`
- `docs/architecture/governance/frontend-product-information-architecture-v1.md`
- `frontend/governance/UX_WAVE_1_REVIEW.md`
- `frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv`
- `docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md`
- `docs/architecture/governance/frontend-current-governed-scope-ledger-v1.tsv`
- `docs/architecture/governance/frontend-product-path-classification-v1.tsv`

## Tests and handoff
Write meaningful behavior tests first, record native RED command/time/exit/log/JSON; implement then GREEN. Cover states, strict time/calendar DST/leap/year, account identity/filter/ties, multiple explicit relationships/raw statuses, secret omission, focus, refresh and true retained callbacks/late receipts/owner changes. Existing assertions remain except additive registry inventory extension for new surface. Run targeted Vitest, typecheck, lint, architecture and negative controls with native outputs outside product. No build/dist or browser adapter by writer; Hermes owns final seven gates/918 identities/46 warning identities/build/browser/delivery. Chinese WRITER_HANDOFF includes exact paths, evidence, injection signature and native browser labels, limitations and backend ID. No independent review or acceptance claim.

Pre-code clarification: add frontend/src/interaction/model.ts to exact scope to admit PUBLICATION as a presentation selection kind, avoiding false NODE/CLIP semantics. Add bilingual agent.kindPUBLICATION/kindLowerPUBLICATION labels; canonical actions remain rejected. Existing inspector receives read-only supplied selection, dedicated InteractionDialog holds permitted publication metadata.

Before implementation, test helper exact path addition: frontend/src/product/publication/testing.ts. Shared test receipts avoid registering a test suite through another test import; this helper is never a runtime fallback. RED-01/02 are setup failures; RED-03 demonstrates missing modules, behavioral RED will be separately recorded with a minimal unavailable shell.
