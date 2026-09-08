# FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V4 — writer report

Implemented the selected session-local command-palette shortcut remapping. Final focused Vitest: **61 total = 61 passed + 0 failed + 0 skipped; 0 pending/todo and 0 reported runtime errors; native exit 0**. Product implementation is handed to Hermes for the seven authoritative final-tree gates, full test identity reconciliation and native browser verification. This is not a publication or full acceptance claim.

**Authority and preservation.** Reviewed `SELECTION_AND_SCOPE.md`, metadata from `BASELINE_INSPECTION.json`, `/home/user/Documents/03-大模型上下文-精简版.md`, repository `AGENTS.md`, the selected plan at `docs/architecture/governance/frontend-product-information-architecture-v1.md:314-325`, and existing registry, dialog, Selection, shell and localization conventions before editing. The root AGENTS applies to all seven writable paths; no nested frontend AGENTS exists. Its freeze-before-verification rule conflicts with the latest Owner V4 unfrozen authorization: V4 takes precedence, and instruction alignment remains deferred to the control plane. No instruction, Skill, Memory, configuration, dependency, backend, build output or requirement document was edited. No delegation or Git mutation was performed.

Working branch remains `refs/heads/agent/frontend-wave2-product-ux-v1`; HEAD remains `f5e19cf53fd010eea2935dd29557e82a879e042c`, parent `01cf2a509d687b8bf8b39eff69688b2a3f5f2f4a`. HEAD is not the accepted V3 working-content tree. Owner baseline metadata identifies accepted V3 tree `79541c256a4405e5e8cd3dd53e36e1611e9959d1`; writer preserved the existing dirty files and stored the seven pre-edit versions under `before/`. The index SHA-256 remains `675115408e86deb10531d0a973cd0372d48458cf17ddb0bb9e6c52858c2fa18e`, matching baseline metadata. Read-only branch, HEAD/parent, status, stash and worktree observations are in `START.json` and `FINAL_WRITER_EVIDENCE.json`. No frozen candidate or integration state is claimed.

**Changed product paths (in-place writes only).** `writer-product.patch` is the incremental patch against the preserved V3 input files, not against HEAD. Before/after SHA-256 values and classifications are in `FINAL_WRITER_EVIDENCE.json`.

| Path | Change |
| --- | --- |
| `frontend/src/foundation/commandRegistry.ts` | Supported palette chord choices and conservative resolution using the existing registry, getShortcut and conflict detector. |
| `frontend/src/foundation/commandRegistry.test.ts` | One behavioral resolution test covering unsupported external values, collisions and retained other overrides. |
| `frontend/src/components/app-shell/AppShell.tsx` | One compact launcher/editor, effective hint/listener, scoped local state, keyboard and modal precedence. |
| `frontend/src/components/app-shell/AppShell.test.tsx` | Eight behavioral cases covering remap, focus, selection, errors, locales, precedence and retirement. |
| `frontend/src/localization/catalogs.ts` | Fourteen new shell shortcut keys in English and Simplified Chinese. |
| `frontend/src/localization/source-manifest.json` | Only the fourteen added `shell.shortcut.*` required keys; all prior keys/order and metadata retained. |
| `frontend/src/styles/foundation.css` | Scoped select and wrapping action-row styles using existing tokens and shared responsive dialog rules. |

**Interaction selectors and chords.**

| Interaction | English selector | Simplified Chinese selector |
| --- | --- | --- |
| Launcher / editor | `getByRole("button", { name: "Keyboard shortcut", exact: true })`; dialog with the same name | Button/dialog `键盘快捷键` |
| Choice | `getByRole("combobox", { name: "Command palette shortcut", exact: true })` | Combobox `命令面板快捷键` |
| Apply | Button `Apply shortcut` | Button `应用快捷键` |
| Reset immediately and close | Button `Restore default` | Button `恢复默认` |
| Cancel | Button `Cancel` | Button `取消` |
| Close icon | Button `Close keyboard shortcut` | Button `关闭键盘快捷键` |
| Native palette fallback | `getByRole("button", { name: /Commands/ })` | Button matching `/命令/` outside the editor |

Choice values are exactly `Mod+K`, `Mod+Alt+K`, `Mod+Alt+P`. For Chromium on Linux use `Control+k`, `Control+Alt+k`, `Control+Alt+p`; the equivalent Meta combinations are supported. Mod requires exactly one Ctrl or Meta. Press from a noneditable target. Apply closes the editor, changes the Commands hint immediately, enables only the selected exact chord and stops consuming the previous chord. Cancel, Escape, close icon and backdrop discard the draft. Restore default uses the registry default (`Mod+K`) instead of the caller palette override. Caller overrides for every other command remain intact and continue appearing in palette action hints. No preference is saved or transmitted.

Unsupported initial values (including unsafe literal markup, empty/unrecognized strings and runtime null/numeric values) fail closed. The Commands hint shows `Shortcut unavailable` / `快捷键不可用`; its native button still opens the palette. The editor shows a localized error and choice/reset route. Invalid literals are not interpreted as HTML. Registry collisions invalidate both initial and edited choices. If another command owns the registry default, Restore default is disabled with a reason; selecting a free supported chord remains possible. This is bounded registry collision handling, not universal browser/OS conflict detection.

**Focus, selection and context semantics.** The existing InteractionDialog owns entry, trap, Escape, backdrop and restoration. Entry focuses the native select via `data-dialog-entry`; Tab/Shift+Tab wrap between the close button and Cancel. Apply, reset and dismissals restore the previously focused element when still connected (normally the launcher). A palette invoked while the launcher is focused restores there after a shared inspect action. The shared `Inspect 2 selected objects` action dispatches `{category: "LOCAL_EPHEMERAL", type: "inspect", open: true}` with source `COMMAND`, preserving selected refs, primary ref and local input draft. The shared `Ask Agent about …` palette action hands focus to the existing `Agent conversation` dialog and restores the Commands launcher on dismissal. Existing canonical commands remain disabled even with AVAILABLE access.

Input, textarea, select, nested contenteditable, active composition, isComposing/keyCode229, handled events, repeat, Shift, AltGraph, both primary modifiers and nonmatching/extra Alt modifiers are not intercepted. Only an exact active chord consumes default behavior. Existing modal DOM ownership blocks shortcut/launcher activation; editor and palette share one local panel state. Behind-modal programmatic clicks are blocked while these panels are open, and existing Agent/notification dialogs block both launchers. A direct shared-store Agent-open action retires the command panel and preserves Agent focus. No global modal registry/system was introduced.

Local command state is scoped to both Selection store identity and Selection lifetime. Workspace, project and surface changes, same-store Selection-owner retirement, and unmount retire editor/palette and local remapping. The next scope starts from its current caller binding, or registry default if no caller binding exists. Returning to a previous scope does not resurrect its local remap. Shell children are not keyed/remounted for this feature: edited child input and asset-browser visibility survive scoped rerenders; the existing notification identity/read-state continuity test remains passing. Retirement coverage calls the real in-memory Selection owner retirement method; no document lifecycle simulator or runtime lifecycle/persistence layer was added.

**Behavioral TDD and actual execution.** Every Vitest invocation used the existing frontend binary, runner config loader, no cache and JSON reporter/output in this writer directory. Each report has a same-stem `.log` containing unmodified combined subprocess output and `.exit.json` containing the exact argv, cwd and native exit. Exit codes were propagated, including all RED and development failures. The “green” or “final” word in an attempted filename does not override its recorded result.

| Run prefix | Native exit | Total | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: | ---: | ---: |
| `01-binding-red-20260908T033823459392Z.json` | 1 | 37 | 0 | 1 | 36 |
| `02-binding-green-20260908T033909996212Z.json` | 0 | 40 | 40 | 0 | 0 |
| `03-editor-red-20260908T034013179901Z.json` | 1 | 38 | 0 | 1 | 37 |
| `04-editor-green-20260908T034150919933Z.json` | 0 | 41 | 41 | 0 | 0 |
| `05-composition-red-20260908T034243178977Z.json` | 1 | 39 | 0 | 1 | 38 |
| `06-composition-green-20260908T034312465311Z.json` | 0 | 42 | 42 | 0 | 0 |
| `07-modal-red-20260908T034359098339Z.json` | 1 | 40 | 0 | 1 | 39 |
| `08-modal-green-20260908T034418073799Z.json` | 1 | 43 | 42 | 1 | 0 |
| `09-modal-green-20260908T034452607733Z.json` | 0 | 43 | 43 | 0 | 0 |
| `10-invalid-red-20260908T034611519073Z.json` | 1 | 47 | 3 | 1 | 43 |
| `11-invalid-green-20260908T034639057300Z.json` | 0 | 47 | 47 | 0 | 0 |
| `12-retirement-focused-20260908T034748914493Z.json` | 0 | 48 | 48 | 0 | 0 |
| `13-altgraph-red-20260908T034911688522Z.json` | 1 | 44 | 0 | 1 | 43 |
| `14-final-focused-20260908T034936042659Z.json` | 1 | 61 | 56 | 5 | 0 |
| `15-final-focused-20260908T035025208234Z.json` | 0 | 61 | 61 | 0 | 0 |

RED/GREEN evidence: 01→02 failed on `Commands ⌘K` instead of the caller binding, then passed after effective runtime/discovery binding; 03→04 failed because the Keyboard shortcut launcher did not exist, then passed after the editor flow; 05→06 failed because active composition without the per-key flag consumed the chord, then passed with composition ownership tracking; 07→09 failed because direct Agent activation left the editor stacked, then passed after local panel retirement. Run 08 retained a real selector failure (`Agent` instead of the existing `Agent conversation` label), corrected in the new test before 09. 10→11 failed because null silently restored the default, then passed after fail-closed external-value validation. 12 passed scope/owner/mount retirement coverage without requiring another product change. 13→15 failed because AltGraph was consumed, then passed with native AltGraph exclusion and accurate event modeling. Run 14’s five failures exposed Happy DOM’s AltGraph alias, documented below; all remain in the evidence. The new inspector selector was also aligned with the existing `Inspect 2 selected objects` label during the editor cycle. Existing test titles were never renamed.

Final command (cwd: the worktree `frontend` directory):

```text
./node_modules/.bin/vitest run --configLoader runner --no-cache --reporter=json --outputFile=/home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V4/writer/15-final-focused-20260908T035025208234Z.json src/components/app-shell/AppShell.test.tsx src/foundation/commandRegistry.test.ts src/localization/localization.test.tsx
```

Final file totals: `commandRegistry.test.ts` 4/4; `AppShell.test.tsx` 44/44; `localization.test.tsx` 13/13. Arithmetic was reconciled against individual JSON assertion statuses; Vitest reports filter-excluded `skipped` assertions under `numPendingTests` in RED runs. The final run has none. Nine new executed cases were added (eight shell, one registry). Existing literal test titles are preserved in the two edited test files; full identity comparison against the accepted V3 695 baseline belongs to Hermes and was not claimed by this focused run.

New behavioral case identities:

- bounded command palette shortcut resolution fails closed for unsupported external values and registry collisions while retaining other overrides
- session-local command palette shortcut applies, cancels and resets the shortcut while preserving focus, drafts and shared selection actions
- session-local command palette shortcut leaves native editing and handled gestures alone, including an active composition without a key flag
- session-local command palette shortcut keeps modal ownership for shortcuts and behind-modal activation and hands focus to a shared Agent action
- session-local command palette shortcut repairs an unsupported initial shortcut and retains native dialog focus in 'en'
- session-local command palette shortcut repairs an unsupported initial shortcut and retains native dialog focus in 'zh-CN'
- session-local command palette shortcut rejects initial and edited collisions without replacing other commands or silently resetting
- session-local command palette shortcut retires only local remapping and editor state across scope, owner and mount lifetimes
- session-local command palette shortcut uses the supported caller binding for both discovery and exact keyboard activation

**Remaining verification limits.** Only focused Vitest was executed. No full suite, typecheck, lint, guard, build, dev server, browser, port, install, network publication or backend operation was run by the writer. The shared dialog’s existing responsive rules plus wrapping editor actions cover the intended desktop/390px layout in source; visual fit and actual pointer/keyboard focus behavior still require Hermes’s native browser checks in EN/ZH. Happy DOM `KeyboardEvent.getModifierState` aliases `AltGraph` to any `altKey` (installed implementation at `node_modules/happy-dom/src/event/events/KeyboardEvent.ts:60-63`). New chord tests therefore set an independent false AltGraph state for ordinary events, and the explicit rejection case sets it true; no dependency, global event prototype, existing test or product guard was weakened. Native Alt/AltGraph and OS/browser reservations remain browser-verification items. Existing shell access/notification consumers retain their accepted behavior; this feature adds no persistence/network integration or canonical authority.

`FINAL_WRITER_EVIDENCE.json`, `writer-product.patch`, `before/`, and the native Vitest reports/logs/exits are the writer handoff artifacts. The control plane owns progress/backend documents, full-tree evidence and publication. **No product source edits occur after this report.**
