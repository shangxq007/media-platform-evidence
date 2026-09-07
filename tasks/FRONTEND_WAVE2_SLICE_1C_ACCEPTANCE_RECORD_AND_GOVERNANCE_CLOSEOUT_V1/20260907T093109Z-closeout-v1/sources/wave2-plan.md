# Wave2 Selection and Canvas decision recovery — proposed, not frozen

Task: FRONTEND_WAVE2_SELECTION_AND_CANVAS_INTERACTION_DECISION_RECOVERY_V1
Mode: FRONTEND_DECISION_RECOVERY
Base commit: f5e19cf53fd010eea2935dd29557e82a879e042c
Base tree: 9dc2ed7a2b7088a60264349543f78b31cb9b124a
Branch: agent/frontend-wave2-product-ux-v1
Worktree: /home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1

The clean worktree is prepared; this document and its evidence remain outside the repository. No Wave2 source, tests, configuration or ledger was modified. Fourteen questions A–N have one source-cited disposition each in WAVE2_DECISION_REGISTER.tsv. They are Hermes proposals pending ChatGPT independent review, not ChatGPT-frozen decisions. No backend blocker is inferred from absent integrations.

## Observed baseline

- SelectionProvider is shell-level but keyed by workspace/project/surface; a surface transition creates a fresh interaction store. Adapter unregister clears membership and transient time/revision-pair context. Surface navigation currently uses ordinary anchors, so hard reload can destroy all runtime state.
- The store deduplicates IDs in caller order, resolves against the active adapter, chooses explicit primary or first, and invalidates synthetic proposals by lifetime/revision. Inspector, toolbar, command palette and Agent already share the store.
- SelectedObject carries NODE/CLIP/LANE plus a string ID. Canvas presentationId, semanticReferenceId and referenced entityId are distinct in the Canvas model; its adapter currently projects only an optional reference string. They cannot be inferred to be interchangeable.
- Canvas has local bounds, pan/zoom/fit/reveal, keyboard selection/movement and visual-only edges. Keyboard movement currently replaces selection with the focused node. Pointer gesture/group-move/marquee controllers are not present in the inspected Canvas component.
- NLE synthetic clips provide Ctrl/Meta toggle selection; this is frontend fixture behavior, not canonical clip geometry. Existing Timeline query/operation gateways and their preview/apply machinery must not be overwritten by a speculative generic gateway.
- Generic shell/Agent canonical Apply is rejected. CapabilityGateway returns UNKNOWN; AssetGateway is unavailable. Existing timeline-specific operations are not evidence of a general Agent OperationPlan/authorization backend.

## Bounded contract

Selection is one frontend context, not a new domain object or server policy. Proposed snapshot: scope, lifetime/generation, monotonic revision, ordered unique presentation refs, primary ref, and existing context projections. Hover, focused DOM target and gesture preview stay with the active surface. A selected presentation ref identifies its workspace/project/surface/kind/local object; optional application logical refs remain a separate typed projection and are not accepted as canonical operation authority merely because they are selected.

Membership ordering is deterministic: replace uses gesture order; toggle preserves survivors and appends additions; removal of primary chooses first survivor. Marquee uses registered presentation order with stable ID tie-break. Primary must belong to membership, and empty membership has null primary. No globally sorted semantic IDs are invented. Stale or wrong-scope targets fail closed. If an adapter projection removes targets, the active selection must be reconciled/pruned before any action and proposals invalidated.

All entry points express intent against the same snapshot. Inspector edits primary by default and visibly states multi-selection scope; bulk effects require an explicitly supported group action. Toolbar and command shell dispatch stable IDs, not translated strings. Agent captures selection/lifetime/revision for a proposal, shows affected targets, and rejects stale application. User intent/conversation language remains independent of UI locale.

## Prioritized implementation slices — none executed

### Slice 1A: selection invariants and Canvas multi-selection

Priority: first. Maps to A–F, K–N. Contract refinements stay within existing interaction/model.ts, SelectionContext.tsx, InteractionShell.tsx, Canvas model/component, localization catalogs/source manifest and their tests. No generic graph editor, new backend gateway, routing rewrite or persistent storage.

Deliverable after authorization: explicit scoped presentation identity handling, consistent replace/toggle/clear/primary behavior, Canvas Ctrl/Meta selection and equivalent keyboard/multi-select controls, shared consumer summaries and localized unavailable-action states. Preserve single-selection compatibility and current clear-on-surface-leave lifecycle.

Acceptance to execute in that later task: deduplication/order/primary invariants; wrong scope and stale targets rejected; focus does not select; Canvas membership is shared by Inspector/toolbar/commands/Agent; changing selection invalidates a proposal; canonical Apply never enabled; en/zh-CN labels and interpolation; keyboard text-edit/IME exclusions; native pointer and keyboard inputs. Re-run affected frontend tests plus complete frontend/guard/type/lint checks on the final exact tree under the existing policy. No fixed future test count is claimed here.

### Slice 1B: bounded Canvas direct manipulation

Depends on accepted 1A. Maps to G–I, K–L. Pointer capture and gesture preview are surface-local. Selected-node drag moves the selected group; unselected-node drag first selects it. Convert screen coordinates through current camera transform into local coordinates. Commit one common bounded delta for the group, preserving relative spacing; do not independently clamp nodes and distort layout. Escape/pointercancel/lost capture restore original preview; context changes cancel the gesture. Local completion is not a canonical transaction receipt.

Marquee is explicit desktop Select mode on empty Canvas; Pan mode owns camera dragging. A completed marquee must not bubble into the existing background clear handler. Define positive-area bounds intersection, zero-area click fallback, additive Ctrl/Meta selection, and deterministic registration ordering. Visual edges are excluded from selectable semantic entities. Do not add edge creation or graph evaluation.

Acceptance later: transformed-coordinate hit tests; overlap, empty area, drag cancel and lost capture; group boundary behavior; membership/primary determinism; one final invalidation; no server request from local manipulation; keyboard/Inspector alternative produces equivalent local result. Native pointer tests are required. Physical touch remains a separately measured gate, not inferred from a viewport.

### Slice 1C: route/selection lifetime refinement

A later, separately reviewed frontend slice; not a prerequisite for 1A/1B. Maps to J, D–F. Keep first-slice clear-on-leave behavior rather than claiming persistence now. Proposed enhancement is same-project in-memory per-surface bookmarks under a client-side shell owner, with adapter re-resolution on return. Prune missing targets, restore only compatible presentation refs, and generate a fresh active lifetime. Project/workspace change, logout/unresolved scope, or hard reload clears. No storage persistence and no cross-surface alias inference.

This requires explicitly reviewing shell mounting and anchor navigation before changing them. A bookmark is not an active adapter or authority to apply a cached Agent proposal. If implementing this requires broader route restructuring, return for a bounded scope decision instead of expanding 1A.

### Subsequent priorities, not included in this implementation scope

After independently accepted Selection/Canvas slices: command discovery/accessibility convergence, then a focused Review UX slice using existing query gateways. Scene/Shot planning, Workflow UX, Render observability and broader NLE/Agent workflows require their own decision recovery and application contract boundary. No commitment to deliver all twelve product areas at once.

## Application-operation and mock boundary

Local selection/hover/dialog/camera are ephemeral. Node move/title/reveal are workspace presentation only. Revision comparison consumes existing read-only query contracts. Future canonical media edits belong to Timeline operations, process edits to Workflow, and explicit semantic relationship intents to an independently accepted application contract. Never derive them from visual position, overlap or an edge.

The future Agent chain remains conversation -> Proposal -> OperationPlan -> Preview -> Authorize -> Apply. Selection is input context, never authorization. Until a real compatible backend chain exists, generic canonical Apply stays disabled. Do not synthesize plan digests, permission grants or APPLIED receipts for production UI.

Use current application-facing typed gateways rather than a broad interface renaming exercise. Preferred Project/Query/Capability/Operation/Agent/Workflow/Render vocabulary may guide narrow future ports, not require creating seven empty abstractions. Mocks expose product logical identities, named application states and typed unavailable/failure results. They may model synthetic local selection and read-only fixtures; they must not expose FFmpeg, scheduler, provider, storage or database internals. Mock outcome markers remain synthetic and cannot satisfy real backend acceptance.

## Keyboard, touch and responsive boundaries

Tab focuses without selecting; Enter/Space selects; Ctrl/Meta+Space toggles when the focused control owns that shortcut. Existing focused-node arrows remain local nudge behavior: preserve the group when focused node is already selected, otherwise select it before nudging. Inputs, textareas, contenteditable and IME composition bypass Canvas shortcuts. Escape cancels a gesture first, otherwise clears selection; it must not be an unconditional locale-switch helper action.

Use native buttons with membership-aware aria-pressed, localized help and a polite count/primary announcement. Do not add role=application to Canvas or pretend a generic graph/listbox interaction model has been accepted. Provide visible focus and keyboard equivalents for every required pointer action.

Touch first uses tap selection, an explicit multi-select toggle mode, Done/Clear and Inspector/nudge/reveal controls. Hover and long press are not required. Marquee/precision drag can remain desktop-only initially. Mobile stays review/navigation/light control, with persistent Agent title/close/composer and independent conversation scrolling. Touch target sizing and physical keyboard/OS virtual-keyboard behavior require actual validation in the later implementation task.

## I18n and build discipline

Every new user-visible label, status, help, accessible name and unavailable reason uses the neutral localization API and platform-owned en/zh-CN keys/parameter contracts. No product Tolgee imports. Do not translate stable IDs, operation discriminators or user intent. Add ledger rows only if actual new frontend paths require classification; no unrelated row changes.

FWR-I18N-01 through 04 remain future refinements: live Cloud/manifest bridge, compile-time key typing, remote-config observability, and keeping synchronous catalog digest mechanics out of security trust authority. None reopens the frozen foundation or blocks this presentation-only slice.

No build was run here. Future builds require resolved and recorded external/frontend-only Vite outDir before execution, read-only protection of backend paths, and immediate scope tripwires. Bare npm run build remains forbidden. No backend tests compensate for a frontend scope issue. Unauthorized mutation means stop and owner disposition, never restore-and-continue.

## Review gate and result

Decision denominator: 14 (A–N), 14 proposals, 0 omitted, 0 silently split. Proposals are implementation-shaped but not independently frozen. Architecture escalation: NONE beyond the requested independent decision review; no backend/frozen-foundation mutation is required for the recommended slice. Blocking gate: ChatGPT independent acceptance of the bounded decision contract. READY_FOR_WAVE2_BOUNDED_IMPLEMENTATION=NO until that review. Engineering branch exists and remains clean/unfrozen. No Wave2 candidate ref, commit or publication was created.

STOP. NEXT=CHATGPT_INDEPENDENT_FRONTEND_WAVE2_DECISION_RECOVERY_REVIEW
