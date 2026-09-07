Run these commands from this version root on the parent runtime. They perform fresh synthetic qualifications and prepare a new run; no product gate is part of this block. Each attempt is exclusive. A failed stage exits nonzero and retains its evidence; fix the cause and use a fresh attempt, never rewrite receipts or a baseline. Independent review remains REQUIRED/PENDING.

```bash
set -euo pipefail
cd /home/user/Documents/workspace/audit-runs/EP19_H7_EXACT_CANDIDATE_GATE_OUTPUT_ISOLATION_CORRECTION_AND_REVALIDATION_V1/run-output-completeness-20260907T143346Z
ep19_suffix="$(date -u +%Y%m%dT%H%M%SZ)-$(python3 -B -c 'import uuid; print(uuid.uuid4().hex[:8])')"
ep19_attempt="$PWD/qualification/parent-runtime-$ep19_suffix"
ep19_run_id="parent-correction-$ep19_suffix"
python3 -B qualification/parent_orchestration.py init --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py focused --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py controls --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py frontend --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py lean --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py formal --attempt "$ep19_attempt"
python3 -B qualification/parent_orchestration.py assemble --attempt "$ep19_attempt"
python3 -B executor/runner.py prepare --run-id "$ep19_run_id" --qualification "$ep19_attempt/QUALIFICATION.json"
python3 -B qualification/parent_orchestration.py cache --run-id "$ep19_run_id"
python3 -B executor/runner.py baseline --run-id "$ep19_run_id"
python3 -B executor/runner.py preflight --run-id "$ep19_run_id"
python3 -B qualification/parent_orchestration.py decision --run-id "$ep19_run_id"
printf '%s\n' "$ep19_attempt" "$ep19_run_id"
```

The focused stage runs `qualification/run.py --require-real-gradle` and records its exact new receipt path in `focused-pointer.json`. Parent already passed real Gradle and all 37 earlier methods; that historical result is retained. The corrected helper requires fresh evidence. A socket error in one execution context does not establish that parent runtimes are blocked.

The controls stage reruns collector, coverage, monitor/SHADOW, packaging, freshness/dependency, launch and preparation controls against the current executor. The frontend stage probes actual read-only bwrap, private PID lifecycle and run-owned XDG output. The Lean stage copies the existing materialized 4.19.0 cache, verifies all 4,617 file hashes and strict collector acceptance, then compiles a synthetic theorem through the actual FORMAL wrapper. The Coq stage uses an independent exact-candidate checkout as a read-only mount, the pinned cached image, synthetic proof input, native version/compile/output provenance, and explicit cleanup of its own containers. It uses `--pull=never --network=none`; it neither downloads nor executes the product formal script. It retains stopped containers until CID capture, then removes only those owned containers. A cleanup failure blocks assembly and identifies the affected evidence; no engine-wide cleanup is used.

`cache` copies the same verified Lean bytes into the new run before baseline. Original archive verification is not claimed. No Gradle, frontend build output, node_modules, JAR or receipt artifacts are seeded from historical runs. Existing gate dependency order and dependency discovery/immutability rules remain; `FRONTEND_INSTALL` remains the original parent-owned gate. Any later dependency resolution requires the parent's existing runtime authorization; these preparation commands perform no network access.

The assembly stage requires every current source-bound stage, native process/log/result evidence, nonempty passing case sets and real Gradle evidence. It emits an `ep19-output-corrections-v2` receipt consumed by `coverage.qualification_inputs` and the existing preflight. It refuses absent, failed or changed-helper evidence. It does not fill missing areas with PASS. `decision` checks both current and recorded ENGINEERING_READY preflight and writes the exact owner/seal/preflight-bound `engineering-launch.json`, with independent and monitor/preservation reviews PENDING and publication NOT_AUTHORIZED.

The following is supplied for the parent’s later product execution, after its readiness and preservation mapping disposition. It was NOT executed here and is deliberately outside the preparation block:

```bash
python3 -B executor/runner.py run --run-id "$ep19_run_id" --review "$PWD/outputs/continuation-runs/$ep19_run_id/engineering-launch.json"
```

If executing that command in a new shell, restore the exact printed run ID first. No publication command is supplied. General backend host/engine limitations and the original preservation contract remain unchanged.
