# Correction 02 verification interface addendum

Existing writer/VERIFICATION_INTERFACE.md remains the source/gateway/fixture/time recipe. No changed exports, props, endpoint, DTO, route, locale label, DOM selector or Operation identifier. New behavior only:

- Shared Selection actions Clear selection, Hide inspector, Show inspector, Edit local properties, Ask Agent and Reveal primary clip reject callbacks retained from an older selection revision/lifetime, even when the same store and clip ID are reused. Newly rendered current buttons continue to dispatch through the same store.
- Opening mobile Selection properties or Timeline object metadata creates intent for the current selection target and lifetime. Clear, Hide, changed primary, or retirement invalidates the occurrence. Selecting the old or another target, or Show inspector, does not revive the old modal; explicit Open selection properties / Inspect selected metadata (or current keyboard I) opens anew.
- Desktop inspector still shows current selection when inspectorOpen is true. Current Canvas title edits keep the mobile dialog open. Workflow retains its dedicated inspector behavior.
- Close/Escape keeps existing InteractionDialog launcher restoration. When mobile launcher disappears and focus falls to body, fallback is existing #main-content; metadata target removal keeps its Timeline navigation region fallback. Focus on another connected element is preserved. Stale mobile Close/Hide callbacks cannot dismiss a fresh dialog occurrence.

Parent browser checks should separately exercise mobile track -> Open selection properties -> Clear track selection -> clip, metadata -> externally clear -> another selection, and revision/source replacement with each modal open separately. Preserve viewport/local time and test current explicit reopening. Happy DOM assertions are not native narrow-screen geometry/focus validation. Browser was not run here.
