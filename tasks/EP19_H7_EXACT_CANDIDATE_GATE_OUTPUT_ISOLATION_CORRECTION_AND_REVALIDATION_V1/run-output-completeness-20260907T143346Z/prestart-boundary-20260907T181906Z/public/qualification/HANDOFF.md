# Diagnostics handoff

Implemented and qualified only the external decision diagnostics. The copied
`executor/runner.py` is the sole changed preexisting source; the new helper is
`executor/decision_evidence.py`. All other executor files match immutable preimages
byte-for-byte, including observe, preservation, coverage, execution and frozen
Shadow policy. No bytecode caches were created.

Final qualification: **37 tests, 0 failures, 0 errors, 0 skips**, native exit 0.
The tests use retained disposable fixtures; owner/expensive technical checks and
gates are explicitly adapted. No product gate, formal prepare or launch occurred.

- [Tested parent commands](PARENT_COMMANDS.md)
- [Risk controls and fixture limits](CONTROLS.md)
- [Final source diff](runs/attempt-002/source.diff)
- [Raw native unittest log](runs/attempt-002/native.log)
- [Native process receipt](runs/attempt-002/process.json)
- [Per-control results](runs/attempt-002/test-results.json)
- [Final source/evidence binding](runs/attempt-002/qualification.json)
- [Parent command checks](command-checks-001/results.json)

The parent command checks passed: current-source verification returned 0; obsolete
source verification and output-directory reuse both returned 1 as required. Their
native failure logs remain in `command-checks-001`. Attempt 001 passed its earlier
33 controls and is retained with its original source snapshot, logs and receipts;
its source binding correctly rejects against the revised implementation. Attempt
002 is the current qualified source snapshot. No unexpected failed suite occurred.
All expected rejection fixtures, native/injected error evidence and partial writes
remain in their attempt namespaces; no log was overwritten.

Receipts save the exact baseline/current decision values, raw baseline identity,
source/policy identities, capture interval/errors, field differences, phase and
bounded START/process status. The original mismatch reason and successful SHADOW
exception remain. Receipts are unique exclusive read-only files. Any write/fsync
failure rejects; even a complete JSON file alone does not establish writer success.
An unwritable or overlapping destination may leave no receipt; exact failures are
reported through exception/stderr, without a persistence promise.

Qualification is limited to these diagnostics. Captures remain sequential endpoint
observations. Directory entry events are still enforced by the unchanged observer;
file-scope directory captures retain their original metadata-only semantics. No
usage/runtime member is excluded and no baseline is refreshed. Historical scope
that overlaps decision-evidence remains a blocker. Formal readiness, publication
and any integration into the original executor remain with the parent.
