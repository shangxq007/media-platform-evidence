# Minimal field/requirement contract (declared before implementation)

Scope: the existing observer format and acceptance predicates only. No collection, browser launch, observer/product change, or generic schema dependency. Three-argument verify() remains pure. Extra informational fields remain opaque and unchanged. Error format is CODE:path, deterministic traversal order. MISSING distinguishes absent keys; NULL distinguishes prohibited null; TYPE distinguishes wrong types; VALUE/SEMANTIC distinguish recorded values failing requirements. bool is never an integer. No inferred/defaulted values.

| Field | Required row/scope | Presence/type/null | Requirement / rejection |
|---|---|---|---|
| trace, expected | root arguments | dict, mandatory, no null | NULL/TYPE at argument |
| documentId | trace, expected, every row | nonempty str, no null | MISSING/NULL/TYPE/VALUE; semantic document equality |
| store,lifetime | expected, armed and snapshots on critical rows | positive int, not bool; no null | field error; exact store and distinct valid retired lifetime |
| revision | same scopes | int >=0, not bool; no null | field error; retired revision greater than armed |
| refs | same scopes | list, explicit []; no null | field error; expected nonempty, retired explicit empty |
| primary | expected | dict, mandatory, nonnull | field error; nonempty initial Selection |
| primary | critical snapshots | dict or explicit null, mandatory | missing != null; retired requires explicit null |
| rows | trace | list mandatory nonempty | field error / SEMANTIC missing_rows |
| seq,kind | every row | positive int (not bool), nonempty str | field error; contiguous sequence and required event kinds |
| armed, stores | early-pagehide, notify, late-pagehide, freeze | armed dict with expected fields; stores list of snapshot dicts | field error; critical rows exactly one same store; armed equals expected |
| event | early-pagehide, late-pagehide, freeze, early-pageshow | dict mandatory | field error |
| event.id,type,trusted | above events | positive int; matching event-type str; exact bool | field error; real lifecycle correlation, trusted acceptance events |
| event.persisted | pagehide/page-show rows | exact bool, no null | field error; selected departure/restoration must be true |
| event.persisted | freeze | mandatory explicit null (observer output) | field error if missing/invalid; not interpreted as false |
| departure.id,trusted,persisted | freeze | positive int and exact bools | field error; matches trusted persisted pagehide |
| dom.preview,dom.proposal | late-pagehide,freeze | exact bools mandatory | field error; both explicitly false |
| dom.capture | late-pagehide,freeze | list mandatory | field error; exactly one Canvas observation |
| capture entry.held | capture entries above | list mandatory, explicit [] allowed | field error; explicitly empty, missing does not prove release |
| actual_restoration | argument | exact bool, no null | NULL/TYPE; false -> semantic rejection |

Initial installation and initial pageshow/pre-arming rows may have armed=null and stores=[]; no retirement snapshot contract applies to them. Noncritical fields are not filled or dropped. Critical notify/late-pagehide/freeze state cannot pass on an absent key even if another row is complete. Primary null is legal for snapshot shape but only qualifies as empty when explicitly present. Early-pagehide snapshot may be selected; it is not required to be retired. Preserve original one-cycle requirement, notification/pagehide/freeze/restoration order and contradiction rejection. A same-event late-pagehide and freeze correlation also require recorded boolean evidence, not truthiness. These are matched departure observations, not an end-of-dispatch or timer proof.

Offline execution plan: reproduce.py expected exit1 for known false acceptance; qualify.py expected0 after correction, preserving any failed attempt separately. Existing qualification cases reconstructed from original qualification.py without executing it. Historical reload is replay of recorded IDs. Stop once focused contract cases and offline reassessment pass; no fuzzing or new collection.
