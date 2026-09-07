# Slice1C native Selection causal diagnosis — public review index

Task: `FRONTEND_WAVE2_SLICE_1C_NATIVE_SELECTION_PRECONDITION_CAUSAL_DIAGNOSIS_V1`  
Delivery: `20260907T053814Z-public-v1`  
Claimed outcome: **COMPLETE_CAUSAL_DIAGNOSIS / PRODUCT_DEFECT**  
Independent review: **PENDING**. Publication is evidence delivery, **not acceptance**.

## Claimed cause
A node-origin primary pointerdown selects project-node (revision 2), then captures on the stage. Zero-movement pointerup releases capture and leaves suppression false. Chromium delivers a trusted stage-targeted click; the Canvas background handler dispatches an empty LOCAL_EPHEMERAL selection, converted to an empty replace and revision 3. R1's unpaused synchronous notification stack identifies the caller; R2 captures the exact request and unchanged unique inventory. The store is not alleged to have incorrectly reconciled the ref.

## Read in this order
1. [Full report (declared local-path redactions only)](reports/FINAL_REPORT.txt), especially hypotheses, code/browser/harness/contract separation, tests and limitations.
2. [R1 raw event/store trace](traces/R1/trace.json), [record timeline](traces/R1/event-store-timeline.jsonl), [native CDP commands](traces/R1/native-commands.json), [unaltered assertion failure apart from path aliases](traces/R1/diagnostic.log).
3. [R2 raw targeted trace](traces/R2/trace.json), [timeline](traces/R2/event-store-timeline.jsonl), [prospective logpoints/source-bundle offsets](plans/R2/logpoints.json), [assertion failure](traces/R2/diagnostic.log). For complete R2 CDP commands, concatenate ordered parts listed in [machine index](INDEX.json); each part is readable text, not independently valid JSON.
4. [Passive observer](plans/helpers/passive.js), [bounded driver](plans/helpers/bounded_driver.py), [R1 prospective plan](plans/R1/prospective-plan.json), [R2 prospective plan](plans/R2/prospective-plan.json).
5. [WorkspaceCanvas source](source/frontend/src/product/canvas/WorkspaceCanvas.tsx), [Selection model](source/frontend/src/interaction/model.ts), [SelectionContext](source/frontend/src/interaction/SelectionContext.tsx), [synthetic Canvas tests](source/frontend/src/product/canvas/WorkspaceCanvas.test.tsx).
6. [Measured summary](verification/MEASURED_CAUSAL_SUMMARY.json), [scoped preservation receipt](verification/PRESERVATION_READBACK.json), [R1 teardown](plans/R1/teardown.json), [R2 teardown](plans/R2/teardown.json).
7. [File provenance/chunk order](provenance/FILES.json), [source-manifest subset](provenance/FROZEN_SOURCE_SUBSET.json), [public-content review](verification/PUBLIC_CONTENT_REVIEW.json), [manifest](MANIFEST.sha256).

## Exact source/build identity
Product tree: `ffeec76721e7334325a4a4c9f3aaea84174d0cb4` — **a tree, not a claimed published product commit**. Snapshots here are verified evidence, not accepted canonical product source. No product commit URLs are invented.

Source manifest SHA256: `d25eab4e6b4b225486e1128febe0b79ab7ba1a8fcbb7c9559ed82ba4d24b8d9b`  
Build manifest SHA256: `53597b2de327034d94a395513c9c12ebe881a34554ae40f80980618bc7482cf8`

| Source | Git blob |
|---|---|
| WorkspaceCanvas.tsx | `59853dd5028bca26a0e259312727e4448fc5d440` |
| interaction/model.ts | `c1f1337e993a5089fa5eed5b29054e3b6e21990b` |
| SelectionContext.tsx | `05e93cd94bbff6b2049869563b15d00df2e53913` |

[WorkspaceCanvas bundle](source/build/assets/WorkspaceCanvas-CJYBS6re.js) and [FoundationPages bundle containing store](source/build/assets/FoundationPages-hrn57YLE.js) are byte-exact. All eight build text artifacts are available; the larger main bundle is losslessly chunked. [Build manifest](verification/BUILD_MANIFEST.sha256) records original names/hashes; machine index maps names to parts.

Source-to-bundle map: Canvas pointerup source lines 148–158 → bundle line0 columns6717/6833; clear line183 → column7924; background click line276 → columns12690/12782. Model update lines61–64 → column8824; publish lines84–94 → column9619; reconcile lines95–98 → column10036; select lines99–118 → column10119; dispatch lines143–158 → column11622. These are reviewed zero-based bundle locations, **not manufactured source maps**. Raw stacks use Chrome's one-based notation.

## Original sealed artifact identities
- `FINAL_REPORT.txt`: `30a1921f95ccea38894c986c564e0f12f64bd0d3bc6103ee5240abfe7673f351`
- `NATIVE_SELECTION_CAUSAL_REVIEW_UPLOAD.txt`: `7d50f9cd7ebc0adef045b7ef661cd24baab0067e5e98302e3c02feab631a9355`
- `NATIVE_SELECTION_CAUSAL_REVIEW_PACKAGE.zip`: `7cad7128e784184a39e4df208bfc7adb44b4b4b20a9d09fa580b7ad21e098642`
- `EVIDENCE_MANIFEST.sha256`: `5d200af8b040b1a7a58e39349c52e2cbdef71904412b84f39a3c07d056df6c1c`
- `CREDENTIAL_SCAN.json`: `01fd246fc2899b4318d3dcb023a8e70b96e4a3e8f2c875918b6b656ebea6ed61`
- `DELIVERY_RECEIPT.json`: `7e662a402466e84507507f9941ca42f8ab53ae2e5aae75ad752910f69b55a4b6`

## Public scope and limits
- COMPLETE_FOR_STATED_CAUSAL_REVIEW_SCOPE: full R1/R2 causal records, source/test/helper bodies, production build text and failure records are readable. This does not establish diagnosis acceptance or fresh execution.
- Local filesystem paths are consistently aliased; native localhost fixture/CDP URLs, coordinates, button fields, stacks, revisions, inventory, timing, failures and schema collision are retained. Helpers/plans with aliases are review copies, not runnable reproduction installations.
- Screenshots, browser profiles, cookies/storage, full local port listings, private Memory/Skills, unrelated tracked-path/index/refs inventories and nested predecessor archives are not published. Screenshots were supplementary, not causal proof.
- Full 7948-entry source manifest and original ZIPs remain private/local; hashes and relevant source rows are published. Public review can verify all relevant source Git blobs and build bytes, but cannot independently repeat the full-repository/seven-lane preservation census or every predecessor qualification control from this subset.
- Historical reports describe the original package, not this public subset. Their NOT_UPLOADED historical statements remain preserved. This delivery has its own detached post-push receipt.
- The report acknowledges discarded unsolicited Debugger events; unhit probes alone do not prove absence. Original historical caller was not traced retroactively. R1 and R2 are exact-baseline diagnostic reproductions, not physical-device or full lifecycle acceptance.

The `kind="drag"` / `name="no-drag-return"` row collision is intentionally retained. Inspect by `name`; do not drop it by filtering only `kind="logpoint"`. No pause-free zero-overhead claim: R1 pointerdown-to-click 27.0 ms; R2 approximately34.4 ms. Debugger unsolicited-event accounting is incomplete, as the report discloses.

No product correction, frozen harness correction, new acceptance check, product candidate/release or publication occurred. Slice1C remains unaccepted. H4 ledger and tracked-dist policy remain unresolved; EP19 open; Roadmap23/Second Wave NO_GO.

The historical receipt says NOT_UPLOADED_LOCAL_FILES_ONLY and stays historical. A separate post-push delivery receipt records the evidence commit and remote readback. Send this INDEX.md URL pinned to the **full evidence commit SHA** to the reviewer; successful GitHub readback is not reviewer acceptance.
