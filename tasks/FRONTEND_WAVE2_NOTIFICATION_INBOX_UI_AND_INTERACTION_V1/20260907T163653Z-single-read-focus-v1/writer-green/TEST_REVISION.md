# Stage 2 critical RED-test revision

## Rationale

The stage-1 tests over-constrained the focus destination to the same-row detail button. The Owner permits any stable meaningful control and directs the smallest existing strategy: the active All/Unread filter. That control is enabled during single/read-all mutation locks, already receives focused read-all transfers, remains connected when an Unread row is removed, and remains present when reconciliation fails closed. The revised tests therefore require synchronous transfer to the active filter and continued focus ownership, without adding row intent, selectors, refs, timers, or asynchronous reclaim behavior.

Programmatic activation remains separately protected: clicking the single-read control while Refresh (or another valid control) actually owns focus must not transfer focus.

## Identity mapping

Only tests in the stage-1-added `single-read focus continuity correction` group changed. The 64 original baseline tests, including their titles and assertions, remain byte-for-byte as recorded before this group.

| Stage-1 identity | Stage-2 identity / assertion |
| --- | --- |
| `keeps enabled same-row focus while an All single read is pending and after the retained row reconciles` | `keeps focus on the active All filter while a single read is pending and after the retained row reconciles`; same pending/success/reconciliation identity, filter focus replaces detail-button focus |
| `survives narrowly modeled native blur without leaving All single-read focus on BODY` | `keeps active All filter focus through narrowly modeled native single-read blur`; same modeled-blur identity, filter focus replaces detail-button focus |
| `moves focus from an unread row to the active Unread filter only when reconciliation removes that row` | `moves focus to the active Unread filter before disable and keeps it through row-removal reconciliation`; same Unread/removal identity, transfer timing corrected to synchronous pre-disable |
| `closes from actual enabled focus while a single read is pending and restores the launcher` | Title retained; actual active element is now the enabled active All filter |
| `retains enabled same-row focus after deferred single-read %s` | `retains active All filter focus after deferred single-read %s`; same failure/invalid/reject parameter identities |
| `keeps same-row focus during reconciliation loading and falls back when reconciliation fails closed` | `keeps active All filter focus during reconciliation loading and failure`; same loading/failure identity, no late fallback/reclaim requirement |
| `cannot let an old closed read unlock or focus over a newer reopened read` | Title retained; both old and reopened focus assertions now identify the corresponding active All filter |

The passing stage-1 identities for deliberate user movement, programmatic activation, context retirement, and unmount retirement were not weakened or renamed.

## Catalog-copy correction

The new deferred failure/invalid/reject test expected the non-catalog phrase `could not be marked as read`. The actual English catalog entry is `The notification could not be confirmed as read. Refresh before trying again.` The assertion now checks `could not be confirmed as read`. No catalog file was changed.

## Test-source comparison

A direct diff against `writer-red/TEST_SOURCE_RECORDED.tsx` showed changes only inside the stage-1-added single-read group listed above. Production source remained SHA-256 `9c8fe17ec79523d04a42b4c6c214b0942e0c25de345866d7b869ff0252ca5861` before RED2.
