# Bounded pre-seal correction handoff

This follow-up supersedes only the current-source claims in the initial handoff.
CODEX_FINAL.txt, initial handoff/controls/commands, initial qualification attempts,
original preimages, old executor sources and historical evidence remain untouched.
No formal prepare, product gates, new baseline, publication or policy change ran.

The preserved pre-follow-up snapshot is
[preimages/followup-20260907T183449Z](../preimages/followup-20260907T183449Z/).
Its manifest covers 1,056 files/links. The
[preservation readback](followup-review-002/preservation-readback.json) checks the
snapshot and 1,052 unchanged original files/links; four authorized source files
changed. This is endpoint byte/mode/link verification, not historical continuity.

Source modification inventory:

- `executor/decision_evidence.py`: START lookup exceptions and nonregular START
  entries now save NOT_ESTABLISHED plus the exact error and reject acceptance.
  An existing comparison rejection keeps its original reason. Stored evidence
  errors include the lifecycle error. No second comparison capture was added.
- `executor/execution.py`: exactly one line replaces `O=D.parent` with the literal
  original absolute TASK_ROOT named in PARENT_FOLLOWUP.md. Every other byte,
  including private D/H and all environment semantics, equals its preimage.
- `qualification/test_decisions.py`: retains 37 initial controls, strengthens the
  unchanged-source control to enforce the exact execution delta and unchanged
  runner, and adds eight bounded START/binding/tool/stale-identity controls.
- `qualification/qualify.py`: binds the follow-up authorization, ledger, preserved
  executor snapshot, original authority inputs and both tool trees. External
  read-only input snapshots have an explicit external-authority path prefix.
- New [follow-up controls ledger](FOLLOWUP_CONTROLS.md), this handoff, review diffs,
  inventories, preservation readback, command checks and retained attempt outputs.
  Earlier follow-up review artifacts remain retained too.

The [follow-up-only source diff](followup-review-002/followup-source.diff) and
[source inventory](followup-review-002/source-inventory.json) compare against the
snapshot immediately before this follow-up. The attempt's
[cumulative executor diff](runs/followup-attempt-003/source.diff) compares against
the original immutable executor preimages. Runner, observer, coverage,
preservation, bindings and all other executor helpers remain unchanged during
this follow-up. Observer SHA256 remains
`2e060dd77ed4b24132d581e36cc3fa84c8b67d928cd9ec7689dcdc8823e991e2`.

Qualification: **45 tests, zero failures/errors/skips**, native exit 0 in
[followup-attempt-003](runs/followup-attempt-003/):
[native log](runs/followup-attempt-003/native.log),
[process receipt](runs/followup-attempt-003/process.json),
[per-control results](runs/followup-attempt-003/test-results.json), and
[source/evidence closure](runs/followup-attempt-003/qualification.json).

Attempt 001 is retained with 43 passes and two failed test assumptions: cleanup
entries are descriptive matrix text, and original tools live in the prior
correction directory. These assertions were corrected without changing executor
behavior. Attempt 002 passed all 45 controls; attempt 003 binds the final ledger
clarification that qualification source snapshots copy tool inputs while working
tool trees remain unchanged. No attempt, partial write or log was overwritten.

START controls include injected FD-relative EACCES through real run_all, a native
symlink comparison and a native FIFO through real run_gate with the child asserted
uncalled. These fixtures do not execute products. All 29 bindings are generated
from the original authority and checked for private repositories/cwd/output/cache/
tmp paths; authoritative commands and cleanup descriptions are retained. All 343
working tool files match the prior correction's originals by path and SHA256.
The bound fixtures contain full all29 mappings and authority/tool digests. This
establishes path interpretation only, not executable visibility or isolation.

[Final parent-command checks](followup-command-checks-002/results.json) retain raw
logs for successful current verification, stale initial-source rejection, stale
prior-follow-up-source rejection, and output-directory reuse rejection.
To independently qualify, run from this workspace with a fresh output directory:

```bash
boundary="$PWD"
output_dir="$boundary/qualification/runs/parent-followup-$(date -u +%Y%m%dT%H%M%SZ)-$(python3 -B -c 'import uuid; print(uuid.uuid4().hex)')"
python3 -B "$boundary/qualification/qualify.py" --output-dir "$output_dir"
python3 -B "$boundary/qualification/qualify.py" --verify-output "$output_dir"
```

Receipt bounds remain sequential endpoints, metadata/digests only, unchanged
observer policy and original comparison obligations, including runtime/usage and
SHADOW handling. START presence does not prove process history; gate process
status stays NOT_ESTABLISHED. Exclusive read-only receipts cannot prove their own
write/fsync completion or resist owner tampering. Storage failure rejects with
its exact exception/stderr error and cannot promise persisted evidence.

The runtime analysis does **not** establish unchanged-contract isolation.
**Formal readiness remains NOT_ESTABLISHED.** No full gate graph or new baseline
is authorized until that boundary is satisfied. These fixture results do not
change that condition; parent owns any later namespace preparation and review.
