# V3 control-plane source review before final gates

Current implementation remains unfrozen and unaccepted. Ordinary in-scope corrections are authorized by the Owner. Preserve writer attempts, including 10-component-route-green.json whose actual result is 16 passed / 2 failed despite its name, 11-component-route-green.json (18/18), and 12-targeted-final.json (35/35).

Findings in initial WorkflowSketch.tsx:
1. onNodeKeyDown returns for composing input without cancelling default Enter/Space button activation. Native button default activation can still call onClick. Prevent composing selectable-button activation and test defaultPrevented, not only absence of direct handler selection. This is not physical OS IME validation.
2. addNode (at capacity), removeSelected and discardSketch queue unconditional pendingFocus; a layout effect later reclaims focus without checking initiating-control ownership. Pass event.currentTarget, transfer only when it actually owns focus, and avoid delayed focus reclamation. A stable existing board is an acceptable capacity focus destination; the initial NEW test's last-card target was an implementation choice, not Owner acceptance authority. Keep a precise stable-enabled-focus assertion and document any NEW-test expectation change.
3. ownerChanged resets only sketch state. confirmingReset and pendingFocus are not bound to owner/lifetime, so an old confirmation may survive a scope transition. Reset all local UI state on exact owner change and ensure old confirm cannot affect a new sketch. Preserve shared Selection/pagehide engine untouched.

Require failing behavioral regressions first, retain fresh failed/passing outputs under distinct names, and re-run affected module/route/shared consumers after correction. No backend/source/permission scope expansion. No final validation or publication yet.
