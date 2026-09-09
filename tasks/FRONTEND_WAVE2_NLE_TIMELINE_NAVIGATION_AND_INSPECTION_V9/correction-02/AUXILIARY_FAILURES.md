# Preserved preliminary results

- red-lifecycle: 71 total = 62 passed + 9 failed. Seven behavioral failures; two toolbar reproduction cases failed at a wrong test label (Edit properties vs actual Edit local properties). This run is not the primary proof for those two cases.
- red-lifecycle-02: corrected labels, still before production edits. 71 total = 62 passed + 9 behavioral failures, zero skipped/runtime errors. Primary reproduction-first evidence. Exact test bytes retained under red-source; both runtime files were still byte-identical to before-source.
- green-lifecycle-01: initial production correction; 71/71 passed.
- green-lifecycle-02: extra regression coverage; 75 total = 74 passed + 1 test fixture lookup failure (Reference placeholder vs actual Canvas Project reference). Corrected test label only. No runtime correction was needed for this failure.
- focused: 503/503 passed, then the revision/source test was tightened to exercise metadata and shared mobile dialogs sequentially rather than stacking dialogs. All final checks were renewed after that test change.
- red-final-baseline: supplemental reproducibility check after implementation, using final test bytes with only the two saved pre-correction runtime files mounted over their original paths read-only. No worktree rollback or rewrite. 75 discovered = 13 behavioral failures + 62 filtered/skipped, zero passed/runtime errors. This is separately labeled and does not replace the actual pre-implementation RED.

All logs/reports remain preserved. SOURCE_DELTA.json uses TEST_RETAIN as a local test scope tag; SOURCE_DELTA_FINAL.json is the authoritative final delta and maps all four paths to their actual existing ledger classification REUSE, with scope classification separate.
