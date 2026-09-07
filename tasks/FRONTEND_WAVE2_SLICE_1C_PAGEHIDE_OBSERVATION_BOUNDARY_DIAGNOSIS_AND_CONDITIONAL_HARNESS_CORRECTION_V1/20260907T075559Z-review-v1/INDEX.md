# Slice1C pagehide observation boundary — review index

**OBSERVER_BOUNDARY_DEFECT. External correction qualified; fresh lifecycle12/12 PASS. Independent review REQUIRED; Slice1C not accepted.**

Read [the full report](reports/FINAL_REPORT.txt) first. Product/backend changes0. Fixed tree `00128d35b97775b97124ad1921053a0da282690d`; fixed build manifest `9644fe897b61e912e9c60bd467b6bf0aec5d497d66f362838e2d6f4750ba331e`. No rebuild, product commit/freeze or backend dependency.

## Evidence path
1. [Prospective plan](verification/PROSPECTIVE_PLAN.txt), [measured execution/preservation](verification/FINAL_VERIFICATION.json), [disposition and limits](verification/DIAGNOSTIC_DISPOSITION.json).
2. [D1 ordered events](traces/D1/ORDERED_EVENTS.jsonl): original old microtask sample → synchronous same-store retirement stack → clean later pagehide → trusted freeze → real BFCache return. Original failure retained.
3. [D2 failure](traces/D2/FAILURE.json), [D3 corrected selector and limits](verification/D3_DISCRIMINATING_REASON.json), [D3 ordered events](traces/D3/ORDERED_EVENTS.jsonl): capture/preview nonempty first, capture released at notification, preview gone by later pagehide/freeze. Conditional probes had no marker hits; not direct entry/return proof.
4. [External change diff](verification/OBSERVER_AND_COLLECTOR.diff), [companion observer](helpers/lifecycle-boundary-v2.js), [strict boundary validator](helpers/boundary_validator.py), [15 qualification controls](traces/qualification/QUALIFICATION_RESULTS.json).
5. [12 fresh lifecycle results](traces/lifecycle-v2/NATIVE_LIFECYCLE_RESULTS.json), [matched departure proof and still-false old predicate](traces/lifecycle-v2/DEPARTURE_BOUNDARY_PROOF.json), [old/new assertion mapping](traces/lifecycle-v2/ASSERTION_MAPPING.json), [eleven unchanged assertion bodies](verification/ASSERTION_BODY_COMPARISON.json).
6. [Historical50 identity ledger](historical/NATIVE_CHECK_INDEX.json). It remains49/50, not relabelled fresh50/50. Unaffected Canvas97/frontend370/controls120/gates/native click11/routes21/supplement6 are REUSED with fixed identity, not rerun.

The actual retirement and clean same-event pagehide sample precede trusted freeze. We do not call a late listener the end of all dispatch work, use a timer as proof, or substitute restored emptiness. See the cited Chrome semantics and instrumentation limits in the report. Full commands, snapshots, failures, raw traces and all eight fixed build artifacts are indexed below; large files are lossless UTF-8 chunks.

## Limitations
- Only qualified Chromium persisted pagehide/freeze/restoration path; not universal browser/crash/discard proof.
- D2 diagnostic selector precondition failed. D1 preview selector evidence excluded. D3 provides nonempty preview/capture proof.
- D3 conditional probes resolved but produced no entry/return markers; no absence inference or direct handler-probe proof. Debugger overhead possible; D1 and fresh lifecycle have no Debugger instrumentation.
- No claim that late pagehide equals end of all dispatch. Same-store retirement and clean pagehide sample precede the trusted freeze checkpoint.
- Historical50 checks remain49pass/1fail (raw56/54/2). Fresh only12 lifecycle.15 qualification controls have separate denominator.
- Private browser profiles, full source-path/other-worktree inventories, Memory/Skills, credentials and redundant command copies omitted. Public subset cannot independently rerun the entire private preservation census.
- Path-aliased helper files are review copies; original bytes/hashes are separate. Chunks concatenate in listed order without separators.
- Independent review and H4/tracked-dist remain unresolved; no product acceptance/publication.

[Machine index / ordered artifact parts](INDEX.json) · [File provenance](provenance/FILES.json) · [Public content review](verification/PUBLIC_CONTENT_REVIEW.json) · [Manifest](MANIFEST.sha256).

Next: independent review of the qualified observer boundary and fresh lifecycle evidence. No new product/backend change is justified here. H4/tracked-dist remain UNRESOLVED. Prior deliveries are not modified.
