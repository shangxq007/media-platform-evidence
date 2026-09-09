# Parent commands for the actual external29 driver

Run from the continuation root. Every referenced executable and fixed input below exists. The two parent-authored JSON inputs and their exact fields are listed in `integration-001/INPUTS_NEEDED.json`.

```bash
K=/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/continuation-002-approved-bookkeeping
I="$K/integration-001"
DRIVER="$I/tooling/executor/external29_driver.py"
BINDING="$I/evidence/RUNTIME_BINDING_LAUNCH_READY.json"
BINDING_SHA256=52a918e472bffcc61b9e23ec85b5a623de83fb1817645d128ba3678c4fe5ecb7
RUN_ID=candidate-formal-002-integration-001
DISPOSITION="$I/evidence/PARENT_DISPOSITION_INPUT.json"
REVIEW="$I/evidence/PARENT_IMPLEMENTATION_REVIEW.json"
```

Verify the already-built immutable binding and current executor identity without creating a run or consuming an attempt:

```bash
cd "$K"
sha256sum -c <(printf '%s  %s\n' \
  52a918e472bffcc61b9e23ec85b5a623de83fb1817645d128ba3678c4fe5ecb7 "$BINDING" \
  858f1760acd6db2a78f688d25568373172a0553b296b647f5dd037bdec2f6ec1 "$I/evidence/qualification-005/QUALIFICATION.json" \
  1484bf7e78d3629b1124729ccf4c73a7af183d1d54008f4abf0df14120559678 "$I/evidence/EXECUTOR_IDENTITY.json")
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" identity \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256"
```

Parent-only preparation. These commands have not been run by integration qualification. They create only the new exclusive run namespace and its isolated sources/outputs/caches.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" prepare \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256"
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" endpoints \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256"
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" revalidate \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256"
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" disposition \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256" \
  --input "$DISPOSITION"
```

The single formal entry below durably creates `FORMAL_ATTEMPT.json` before observer registration, policy capture/build, baseline, preflight, prestart, or any gate. It keeps one `BoundaryObserver`, `Engine`, and `RunAdapter` alive through command-before/after, gate, final, coverage, and seal. There is no standalone baseline or preflight command.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B "$DRIVER" formal \
  --run-id "$RUN_ID" --binding "$BINDING" --binding-sha256 "$BINDING_SHA256" \
  --review "$REVIEW" \
  --applicability "$K/dependency-review/CURRENT_APPLICABILITY.json" \
  --private-map "$K/dependency-review/private/ELIGIBLE_SKILLS_MAP.private.json"
```

Do not repeat `prepare`, `endpoints`, `revalidate`, `disposition`, or `formal` in this namespace after any failure. Do not use `candidate-formal-001`, rebuild a failed baseline, dispatch a third attempt, or invoke the old `formal-tooling/executor/runner.py` entry.
