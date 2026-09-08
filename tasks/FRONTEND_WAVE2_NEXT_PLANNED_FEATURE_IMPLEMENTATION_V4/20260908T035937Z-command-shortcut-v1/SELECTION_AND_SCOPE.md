# V4 selection and bounded acceptance

SELECTED_FEATURE=Session-local command-palette shortcut remapping
PLAN_SOURCE_AND_ITEM=docs/architecture/governance/frontend-product-information-architecture-v1.md:314-325 / Commands and keyboard architecture / Shortcuts are remappable, discoverable, and never the only way to act
CURRENT_IMPLEMENTATION_GAP=commandRegistry.ts provides ShortcutOverrides/getShortcut/conflict detection, but AppShell.tsx:71-78 hardcodes Ctrl/Meta+K and line106 always shows Command-K; no user editor exists.
USER_VISIBLE_OUTCOME=Change the existing Commands shortcut, try it against the actual palette, cancel or restore registry default, without saving or affecting selection.
BACKEND_DEPENDENCY_DISPOSITION=NONE_FOR_LOCAL_REMAP; persisted user preferences remain unavailable and outside scope; no new requirement ID or API contract.

## Scope

- Reuse commandRegistry and the existing navigation.command-palette.open descriptor. One compact shell entry and shared InteractionDialog; no settings route or generic shortcut catalogue.
- Supported literal chords: Mod+K (registry default), Mod+Alt+K, Mod+Alt+P. Mod means exactly one of Ctrl/Meta. A bounded input/select may expose only these; invalid externally supplied values must fail closed rather than activate unsafe bindings. Registry collisions invalidate a candidate. This is a supported subset, not universal browser/OS collision detection.
- The active hint and listener derive from one resolved binding. Respect caller-provided palette shortcut override within supported subset; editor changes only this command. Unsupported/conflicting caller override gets truthful unavailable/error plus reset route, never silently intercept a different shortcut.
- Local authoring only: current mounted shell/context; reset on workspace/project/surface/Selection-owner retirement and unmount. No localStorage, URL, server preference or account setting. No mocked network lifecycle.
- Input/contenteditable/select, composition/isComposing/keyCode229, defaultPrevented, repeat, extra or both primary modifiers must not be intercepted. An existing modal owns focus: no palette/editor stacking by shortcuts or behind-modal activation. Commands remains available by native button.
- Selection and local surface drafts survive editor/palette opening, cancel/reset and actions. Existing selection commands still dispatch through shared owner; canonical palette commands remain disabled even with AVAILABLE access.
- English and Simplified Chinese; useful desktop and 390px narrow dialog, native focus entry/trap/Escape/backdrop/restore.

OUT_OF_SCOPE=Other shortcut remapping; keyboard-recording framework; global/persistent preferences; new permission/action/selection registry; canonical mutation; real backend integration; accepted feature redesign; dependency/guard changes; product Git mutations; backend EP19.

## Expected changed paths

- frontend/src/foundation/commandRegistry.ts
- frontend/src/foundation/commandRegistry.test.ts
- frontend/src/components/app-shell/AppShell.tsx
- frontend/src/components/app-shell/AppShell.test.tsx
- frontend/src/localization/catalogs.ts
- frontend/src/localization/source-manifest.json
- frontend/src/styles/foundation.css only if needed for this dialog/launcher
- frontend/governance/UX_WAVE_1_REVIEW.md (V3 adoption plus V4 progress)
- frontend/governance/BACKEND_ENABLEMENT_REQUESTS.tsv (append clarification to existing UXW1-002, no new ID)
- docs/architecture/governance/frontend-backend-application-api-gap-ledger-v1.md (local shortcut disposition; no contract/integration)

No new runtime paths expected. Existing H4/current-scope/path classification records remain unchanged unless a genuinely new governed path is authorized and classified; no unrelated ledger debt resolution.

## Acceptance criteria

1. Actual supported remapping: new chord opens palette, old chord no longer does, hint agrees; cancel leaves active binding; reset uses registry default.
2. Unsupported/conflicting overrides cannot activate and have clear repair/reset behavior. Literal local errors render safely.
3. Keyboard precedence: editing/composition/repeat/handled events/extra modifiers/modal ownership do not open or steal default behavior. Active exact match alone is consumed.
4. Native button fallback and dialog focus continuity; selection/drafts preserved; no stacked modal; context change retires editor and local binding; remount defaults restored.
5. Existing contextual palette actions still operate on current shared selection; canonical actions disabled regardless of simulated available access.
6. Behavioral RED/GREEN records, final targeted tests and seven required gates, full identity reconciliation versus exact V3 695 baseline. No intentional existing test identity removals planned.
7. Exact final implementation tree, new external build, emitted hashes and required refs, focused real Chromium desktop/narrow EN/ZH checks with actual pointer/keyboard. Browser project projection explicitly simulated; no real auth/backend.
8. Complete additive evidence package, exact patch replay, source endpoints, sealed manifest and anonymous fixed-commit readback. Product publication remains unauthorized.

## Source baseline and authority

Hermes verified all 996 predecessor-scoped paths, modes and membership against accepted V3 tree 79541c256a4405e5e8cd3dd53e36e1611e9959d1 using its external object chain. HEAD f5e19cf53fd010eea2935dd29557e82a879e042c is not the accepted working-content tree. V3 original test report and public seal verified. Review adoption is appended to the existing UX_WAVE_1_REVIEW.md; historical results not new V4 execution.

Owner V4 allows routine bounded iteration after development failures. No frozen candidate exists. Explicit tool denials/no-retry restrictions remain binding. No Skill/Memory edits. No backend lane stationary assertion. Root AGENTS freeze-before-validation rule yields to latest Owner unfrozen implementation/evidence-only authorization; instruction changes deferred.
