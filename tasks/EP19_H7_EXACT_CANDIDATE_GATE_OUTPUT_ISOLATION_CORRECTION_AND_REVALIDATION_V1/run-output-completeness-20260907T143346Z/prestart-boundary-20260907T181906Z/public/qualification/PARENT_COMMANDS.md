# Parent commands: diagnostics only

Run from this boundary workspace. Both commands use Python with bytecode disabled.
The output must be a new canonical directory beneath `qualification/runs`.

```bash
boundary="$PWD"
output_dir="$boundary/qualification/runs/parent-$(date -u +%Y%m%dT%H%M%SZ)-$(python3 -B -c 'import uuid; print(uuid.uuid4().hex)')"
python3 -B "$boundary/qualification/qualify.py" --output-dir "$output_dir"
python3 -B "$boundary/qualification/qualify.py" --verify-output "$output_dir"
```

A nonzero first command is a retained failed attempt. Inspect its `native.log`,
`process.json`, `test-results.json` when produced, `source.diff`, and
`source-snapshot/`; repair only authorized sources, then choose a new output path.
Do not rerun into or delete a failed namespace. Verification is read-only and
rejects changed source/dependency identities, including runner/helper and the
qualification programs. `qualification.json` seals all retained regular evidence
files; deliberate fixture symlinks are retained, not traversed.

No command here prepares, seals or launches a formal product run. The imported
execution.D remains anchored to this private copy; only fixture tests patch it.
Parent owns review, publication and any future integration. Future launch seals
must explicitly include all copied executor source paths, including the new
helper, and existing qualification closure checks require matching helper and
qualification dependencies. These diagnostic results do not establish the other
formal readiness conditions and do not refresh an expected baseline.
