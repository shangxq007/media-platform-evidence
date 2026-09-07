# UX contract — PROPOSED_SLICE_1C_DECISION, not current runtime acceptance

D01 authority
PROPOSED_SLICE_1C_DECISION: Router resolves navigation; application surface supplies explicit scope; Selection alone owns refs/primary/lifetime/revision.

D02 scope identity
PROPOSED_SLICE_1C_DECISION: Use exact workspaceId?, projectId?, surfaceId; ref adds kind and localId. Optional means absent, not invented default ID. No pathname namespace.

D03 same scope
PROPOSED_SLICE_1C_DECISION: Preserve only surviving active owner and valid adapter. Equal scope does not force a new lifetime. Reconcile projections; equal snapshot stays identical.

D04 cross surface
PROPOSED_SLICE_1C_DECISION: Canvas/nle/review/workflow and every different SurfaceId have distinct scope. Clear membership, new lifetime; no shared cross-surface requirement found.

D05 project change
PROPOSED_SLICE_1C_DECISION: Different project invalidates old refs/primary; rotate lifetime. Never carry IDs even if localId matches.

D06 workspace change
PROPOSED_SLICE_1C_DECISION: Different workspace invalidates refs/primary; fresh lifetime, no workspace reuse.

D07 owner retirement
PROPOSED_SLICE_1C_DECISION: Destroying provider or unregistering its active adapter ends the presentation lifetime, even at equal scope. New mount starts empty. Incidental child rendering is not retirement.

D08 history and bfcache
PROPOSED_SLICE_1C_DECISION: Back/Forward resolves target normally; no snapshot restoration. Same active document/scope may naturally survive. Document pagehide retires ownership; bfcache pageshow must re-enter empty with fresh lifetime before interaction. Do not equate bfcache replay with permitted same-document preservation.

D09 query and hash
PROPOSED_SLICE_1C_DECISION: No Selection params currently parsed. Same-scope query/hash or #main-content may preserve surviving owner. If navigation destroys owner use retirement rule, not restoration.

D10 modal and subroute
PROPOSED_SLICE_1C_DECISION: Inspector/Agent dialogs are local state, not registered subroutes. Their open/close changes focus/UI only; future same-scope nested view follows survival rule.

D11 invalid target
PROPOSED_SLICE_1C_DECISION: Malformed/missing required route IDs or unsupported surface yields unavailable target with no active prior Selection. Known unavailable workspace/error clears/retires affected owner. Unknown project existence is not asserted deleted.

D12 async resolution
PROPOSED_SLICE_1C_DECISION: Choose unavailable target during committed unresolved transition. Render loading/error shell without selectable adapter. Establish exact navigation scope from matched params and explicit SurfaceId, not raw pathname. Only current target responses can activate its presentation.

D13 atomic transition
PROPOSED_SLICE_1C_DECISION: At navigation commit stop old interaction, cancel gesture, retire old owner if needed, expose target context and scope together, register target adapter then reconcile before consumers interact. Abort before commit leaves old owner; never publish mixed route/scope authoritative snapshot.

D14 gesture
PROPOSED_SLICE_1C_DECISION: No drag/marquee/pan crosses retiring or scope-changing navigation. Cancel before old DOM retirement, discard preview, release capture; navigation cancellation does not commit geometry. Same-scope surviving navigation may retain Selection but cancels gesture if geometry/context invalidates.

D15 Agent
PROPOSED_SLICE_1C_DECISION: Lifetime change invalidates proposal; equal surviving lifetime/revision may keep it. Projection/revision changes still stale. Retired UI proposal discarded; retained captured object must fail existing applyProposal.

D16 focus
PROPOSED_SLICE_1C_DECISION: Focus may move/reset without fabricated membership. Scope transition determines Selection; focus restoration cannot select an old ID. Preserve existing explicit native activation semantics.

D17 keyboard
PROPOSED_SLICE_1C_DECISION: No new router Delete/Arrow handlers or role=application. Existing shell Ctrl/Meta K is not Selection ownership; retain editable and IME exclusions. History shortcuts navigate, never restore refs.

D18 persistence
PROPOSED_SLICE_1C_DECISION: No URL/history/storage/bookmark/IndexedDB/server/per-project cache or Selection undo history. Natural live store survival is not restoration.

D19 URL boundary
PROPOSED_SLICE_1C_DECISION: URL may identify workspace/project/surface navigation. No selectedRefs, primary, lifetime, revision, preview or proposal revision parameters.

D20 multi instance
PROPOSED_SLICE_1C_DECISION: One local product Selection authority per active application instance/scope; no BroadcastChannel or storage synchronization. Legacy route-local controls are not merged into this authority.

D21 dependencies and canonical
PROPOSED_SLICE_1C_DECISION: Reuse TanStack router; no new router, generic navigation framework, server call, OperationPlan, authorization or canonical revision for Selection lifetime. Existing domain reads remain separately owned.

D22 revision
PROPOSED_SLICE_1C_DECISION: Within surviving provider, scope replacement seeds previous revision+1. Adapter cleanup increments once; equal reconcile is no-op. Fresh destroyed-provider mount may start at zero because new lifetime disambiguates. No global route revision clock.

D23 render independence
PROPOSED_SLICE_1C_DECISION: Semantics follow explicit ownership/scope/adapter invalidation, not React component name or pathname. No provider hoist or keep-alive cache solely to resurrect Selection; bounded links may retain same owner naturally.

D24 FB-GAP-001 and presentation readiness
PROPOSED_SLICE_1C_DECISION: Current ProjectContext never yields RESOLVED; do not add backend verification to Slice1C. Settled BLOCKED may expose explicitly provisional presentation-only fixtures using exact matched route context, never proof of project existence/authorization. LOADING/ERROR/unmatched targets remain selection-unavailable; proven invalid target cannot expose old refs. Domain controls retain existing fail-closed policies.