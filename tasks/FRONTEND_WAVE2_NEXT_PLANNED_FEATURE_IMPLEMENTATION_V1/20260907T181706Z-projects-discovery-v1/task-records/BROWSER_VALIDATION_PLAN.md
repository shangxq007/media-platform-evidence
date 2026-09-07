# Focused browser acceptance plan

Run against final-tree external production build only, static local receiver with no upstream forwarding. Reuse contained Chromium/CDP harness. Required inputs use trusted CDP Tab/Enter/Escape/Space, pointer and text key events; any DOM locale selection/scroll assistance is labeled and not counted as native interaction. Native input traces and DOM observations are retained alongside screenshots.

- Ordinary Projects route: shared shell and localized unavailable/unknown states; no Projects query HTTP or simulated success.
- Explicit localhost fixture: visible simulation and recent/limited snapshot boundary, opaque names/descriptions/status content.
- Search by name and description; no-match state, reset; projected-status filtering and deterministic sort. No fabricated server pagination/count.
- Native keyboard inspect item, details render exact selected identity, no canonical Open/creation; Tab stays within shared dialog; Escape restores triggering inspect control. Reopen via pointer.
- Refresh/loading/cancel/retry; controlled source failure clears previous snapshot; error distinct from no matches; retry returns actual simulated response. Stale completion cannot restore cancelled data or steal focus.
- Unknown/denied/unsupported/unavailable and loaded-empty fixture outcomes.
- Narrow 390×844 Simplified Chinese and desktop 1440×1000 English: responsive filter controls/detail contents, no page overflow, readable labels. Relevant screenshots; no physical-mobile or screen-reader speech claims.
- Build binding: verify every emitted output's disk/served size and SHA-256 and required local references. Record assertion exit, harness exit and actual Chromium exit separately. Close browser naturally and verify task-owned listeners stop.

Component tests cover principal/tenant/session/workspace/source/request generation mismatches and deferred context transitions. If native harness injects a controlled adapter through React inspection, restrict to explicitly simulated source and disclose it; it is not server authorization or real integration. Never modify product build bytes or force a passed activeElement outcome.

Preserve failed attempts. Correct only demonstrated observer/precondition defects or authorized feature-local regressions; no optional new validation framework, unrelated diagnostics or additional feature work after required acceptance.
