# Offline reproduction — no browser

Use a scratch copy of this commit-pinned task directory, preserving the downloaded evidence. Run only:

```sh
python3 -B helpers/reproduce.py  # expected exit 1: OLD validator falsely accepts both
python3 -B helpers/qualify.py    # expected exit 0: 181 offline cases
python3 -B helpers/reassess.py   # expected exit 0: existing proof reassessment
```

Do NOT run inputs/helpers/qualification.py, inputs/helpers/lifecycle_v2.py, or any historical native program. They are provenance/AST inputs only. The current qualifier extracts solely the original pure mutation statements. No install is needed; Python standard library only.

## Exact reviewer counterexamples
Old validator: [immutable original](https://raw.githubusercontent.com/shangxq007/media-platform-evidence/2a2d014890d3a0ff693f4ad876a39a0df4d236df/tasks/FRONTEND_WAVE2_SLICE_1C_PAGEHIDE_OBSERVATION_BOUNDARY_DIAGNOSIS_AND_CONDITIONAL_HARNESS_CORRECTION_V1/20260907T075559Z-review-v1/helpers/boundary_validator.py).
Original proof: [immutable original](https://raw.githubusercontent.com/shangxq007/media-platform-evidence/2a2d014890d3a0ff693f4ad876a39a0df4d236df/tasks/FRONTEND_WAVE2_SLICE_1C_PAGEHIDE_OBSERVATION_BOUNDARY_DIAGNOSIS_AND_CONDITIONAL_HARNESS_CORRECTION_V1/20260907T075559Z-review-v1/traces/lifecycle-v2/DEPARTURE_BOUNDARY_PROOF.json).
For A and B start with SEPARATE deep copies of proof.trace; preserve proof.armed and proof.actual_bfcache exactly. In seq 8 (notify), 10 (late-pagehide), 11 (freeze), for EVERY stores entry delete ONLY `lifetime` for A or ONLY `primary` for B. Do not modify any other value. Invoke verify(mutated_trace, original_armed, original_actual_bfcache). Expected rejection; old actual passed=true/errors=[] for both. Corrected validator rejects with field-specific MISSING errors.

The two exact mutated JSON files, hashes, original raw inputs, focused operation paths/values, old/new results, and original structured negative derivatives are in results/. Canonical input hashes use json.dumps(sort_keys=True,separators=(',',':')) UTF-8. File hashes separately refer to exact bytes. Explicit primary=null positive controls must pass; missing primary must fail.
