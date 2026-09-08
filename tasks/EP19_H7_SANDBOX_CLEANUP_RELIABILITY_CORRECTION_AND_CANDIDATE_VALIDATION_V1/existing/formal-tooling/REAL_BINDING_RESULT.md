# Real binding repair completed

**PASS:** actual Git/source/DELTA binding, candidate-bound synthetic qualification **158/158**, builder exit **0**, detached capsule controls **13/13**, and final **551-path** qualification closure. `formal_ready=false`; no producer reruns, Gradle, probes, formal execution, product workloads, checkout mutations, commits or publishing occurred. All writes were within `formal-tooling`.

## Exact handoff

- Candidate: `a29864343ed4f630b052c20d86c23b240f13cfd0`; tree: `fd37409d0274662abbe86f69e3d963c05b379696`.
- Source: `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/checkout`.
- Immediate parent: `689ab9456461a8d19a72d059f5157092efc43aff`; canonical comparison base: `86d6aef94fd5e58da552e97c11473cff6eca734e`.
- Native DELTA: `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/candidate-preparation/native-delta-001/DELTA.json`.
- DELTA SHA-256: `4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e`.
- Config: `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/candidate-inputs-v3/BINDING.json`.
- **Config SHA-256: `3a5cdfe0557eed59c32d3e2602d62cabe9462a937c966f4f294b5f7b029d8d56`.**
- Fresh qualification: `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/receipts/SYNTHETIC-20260908T212234Z-0ff24873/FRESH.json`.
- Capsule: `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/candidate-qualification-v3/QUALIFICATION.json`.
- Capsule SHA-256: `7c787d6e27b367c065de9dd01dfd4a2b71e89ac6c60bb30ea702f0c19fc8dc54`.

The v2 binding schema is unchanged; `candidate-inputs-v3` is the fresh exclusive directory name. No `candidate-inputs-v2` directory existed when checked; the parent's rejected CLI receipt remains untouched. Both sealed run names remain `candidate-formal-001` and `candidate-formal-002`; neither was launched by this repair.

## Correction and evidence

Only `executor/identity_delta.py`, `tests/test_identity_delta.py`, and `tests/CONTROL_IDENTITIES.json` changed in the qualified source set. The preimages, exact diff and hashes are under `real-binding-repair/before/`, `IMPLEMENTATION.diff`, and `SOURCE_CHANGES.json`. BINDING_STEPS.md now identifies the completed real inputs; its previous version is preserved.

The RED regression read the actual sealed saved native output before changing the validator. It exited 1 with `CHANGE_IMPACT_POLICY_OR_SCHEMA`. `real-binding-repair/RED.log`, `RED.process.json`, and `RED_SOURCE_BINDING.json` preserve the measured failure and exact executable/test preimages. That same positive regression passes in the completed candidate-bound qualification.

Read-only Git object reads proved classifier bytes identical in the immutable parent and candidate. The source SHA-256 is `d426f7748ef265fd9457ddd7f7cb3e0565d420ac9bb57bec7f8be3cf75cc106f`; `CLASSIFIER_SOURCE_PROOF.json` records the comparison. Validation requires unchanged classifier tree entries and this reviewed source digest. It selects only the pinned constants, pure path functions and Classification class for in-process evaluation. The classifier CLI, Git-diff producer, output writers and other I/O functions are not loaded or invoked.

Expected path categories, aggregate CATEGORY_ORDER and policy now come from those actual pure definitions applied to the verified canonical diff. The measured output must match exactly. Actual category order is `docs`, `backend_test`, `backend_runtime`, `unknown`. The seven historical requirement flags remain exactly true. The actual `runtime_image_publish=true` value is classifier metadata, **not product publication authorization**. There is no publication action or new authority path.

The added controls reject alphabetical categories, invented path categories, internally consistent but wrong category mappings, the old publishing metadata value, each relaxed requirement flag, integer policy values, extra/missing policy fields, and unverified classifier bytes. Independently specified path variants exercise changing categories and publishing metadata while blocking subprocess/file I/O. A further control proves that even correctly derived policy cannot drop historical requirements. The synthetic fixtures now carry the real pinned classifier instead of a comment-only mock.

All 147 prior control identities remain among the 158 successful controls, including the 49 historical baseline identities. No tests failed, errored, skipped or duplicated. Existing detached capsule negatives all passed. The actual binding CLI and final runtime object-source verifier both used real Git transport; synthetic Git fixtures remain confined to the existing synthetic controls.

The generated CHANGE_IMPACT file is byte-identical to the saved native stdout. The original 7,973 accepted identities plus the source/XML-verified 27 additions yield **8,000 expected identities**, retaining all **29 original skips**. This is expected inventory accounting, not a new full-suite execution result. Existing native receipts are consumed as supplied, never reconstructed.

All gate parsers, 29 gate requirements, matrix derivation, native acceptance, ancestry, identity/skip reconciliation, one-shot namespaces, historical authority, Lean/V2 dependencies and preservation predicates remain unchanged. The builder and capsule enforce the existing exact-reuse-or-bound-fresh qualification path.

## Executed validation and artifacts

`real-binding-repair/BINDING-001`, `BUILD-001`, `CAPSULE-001`, and `AUDIT-001` each contain exclusive `RAW.log` and `PROCESS.json` files with exact argv, timestamps, PID, exit and log digest. The synthetic namespace contains its own raw log, process receipt, result and FRESH document. `REAL_BINDING_RESULT.json` records artifact paths and SHA-256 digests.

The initial attempt to use `tools/run_logged.py` before binding creation stopped during import with `SEALED_CANDIDATE_INPUT_REQUIRED`; the binding CLI had not started. The standalone external `real-binding-repair/capture.py` then captured binding creation without importing the bound runtime. No access-control denial or bypass occurred.

Exact candidate-bound qualification command, executed from `/home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling`:

```bash
python3 -B qualification/qualify_synthetic.py --config /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/candidate-inputs-v3/BINDING.json --sha256 3a5cdfe0557eed59c32d3e2602d62cabe9462a937c966f4f294b5f7b029d8d56
```

For builder, detached controls and final audit, the process environment bound the exact `H7_BINDING_CONFIG` and `H7_BINDING_SHA256` above; detached controls additionally set `H7_TEST_CAPSULE` to the exact capsule above. Captured inner commands:

```bash
python3 -B qualification/candidate_binding.py --candidate a29864343ed4f630b052c20d86c23b240f13cfd0 --tree fd37409d0274662abbe86f69e3d963c05b379696 --immediate-parent 689ab9456461a8d19a72d059f5157092efc43aff --canonical-comparison-base 86d6aef94fd5e58da552e97c11473cff6eca734e --clone-source /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/checkout --reviewed-delta /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/candidate-preparation/native-delta-001/DELTA.json --reviewed-delta-sha256 4be8b7982481a10599d9a43980603c30abc00a2da934eecab03ecab97562ac9e --run-id candidate-formal-001 --run-id candidate-formal-002 --output /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/candidate-inputs-v3

python3 -B qualification/build_qualification.py --fresh /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/receipts/SYNTHETIC-20260908T212234Z-0ff24873/FRESH.json --output /home/user/Documents/workspace/audit-runs/EP19_H7_SANDBOX_CLEANUP_RELIABILITY_CORRECTION_AND_CANDIDATE_VALIDATION_V1/formal-tooling/candidate-qualification-v3

python3 -B tests/verify_capsule.py

python3 -B real-binding-repair/final_audit.py
```

The final audit additionally exercised the runtime's read-only `execution.verify_object_source()`, checked the exact native-output bytes and preserved inventory prefix/skip set, parsed all 58 external Python programs, and verified that all **2,686 previously recorded receipt/native-evidence files** retain their original hashes. Earlier success and failure receipts remain preserved. The final capsule seals current executable sources, config, DELTA closure, native receipts, generated inputs and fresh qualification evidence.

This completes the authorized external repair and real candidate binding exercise. Native preparation, formal gates, product workload acceptance and publication remain outside this repair; synthetic qualification does not establish formal readiness.
