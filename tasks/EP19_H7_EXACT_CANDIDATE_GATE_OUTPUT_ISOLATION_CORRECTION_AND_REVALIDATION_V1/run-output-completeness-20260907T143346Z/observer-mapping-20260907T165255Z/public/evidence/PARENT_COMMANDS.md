Run this block in the normal parent host. It creates a fresh exclusive receipt, verifies the complete historical closure, and runs only the 25 affected observer fixtures. No product gates or runtime probes run in this block. Failures remain in their attempt directory; use a new directory after fixing a cause.

```bash
set -euo pipefail
cd /home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z/observer-mapping-20260907T165255Z
ep19_observer_attempt="$PWD/parent-rebind-$(date -u +%Y%m%dT%H%M%SZ)-$$"
bash ./parent_rebind.sh "$ep19_observer_attempt"
ep19_observer_qualification="$ep19_observer_attempt/QUALIFICATION.json"
cat "$ep19_observer_attempt/VALIDATION.json"
```

The completed local receipt is `binder-attempt-001/QUALIFICATION.json`. It already passes both coverage acceptance functions and the five actual qualification-schema clauses extracted from `runner.preflight`. `VALIDATION.json` binds its SHA-256. This is qualification readiness, not a full run preflight.

The 10 binder controls can be rerun separately, without repeating observer tests:

```bash
python3 -B test_binder.py \
  --out "$PWD/parent-binder-controls-$(date -u +%Y%m%dT%H%M%SZ)-$$" \
  --qualification "$ep19_observer_qualification"
```

The main parent owns the following later phases. Run them only when the parent is ready to create its fresh formal run; they were not executed in this task. Continue in the same shell to retain the receipt path.

```bash
cd ..
ep19_run_id="observer-restored-$(date -u +%Y%m%dT%H%M%SZ)-$$"
python3 -B executor/runner.py prepare \
  --run-id "$ep19_run_id" --qualification "$ep19_observer_qualification"
python3 -B qualification/parent_orchestration.py cache --run-id "$ep19_run_id"
```

`cache` is the existing exact-hash Lean cache preparation. Resolve any other parent runtime preparation before sealing, following the existing parent contract. The current receipt does not establish current container availability. Then:

```bash
python3 -B executor/runner.py baseline --run-id "$ep19_run_id"
python3 -B executor/runner.py preflight --run-id "$ep19_run_id"
```

Only after actual preflight reports `ENGINEERING_READY`, the existing parent decision command checks that readiness and writes its bound execution authorization. It preserves independent-review `PENDING`:

```bash
python3 -B qualification/parent_orchestration.py decision --run-id "$ep19_run_id"
python3 -B executor/runner.py run \
  --run-id "$ep19_run_id" \
  --review "$PWD/outputs/continuation-runs/$ep19_run_id/engineering-launch.json"
```

The last command is the parent product-gate invocation and is outside this task. These instructions introduce no independent-review ACCEPT or additional review launch blocker.
