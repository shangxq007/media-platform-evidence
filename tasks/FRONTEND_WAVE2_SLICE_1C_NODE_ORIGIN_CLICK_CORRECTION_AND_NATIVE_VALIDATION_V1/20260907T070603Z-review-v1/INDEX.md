# Slice1C node-origin click correction — review index

Task: `FRONTEND_WAVE2_SLICE_1C_NODE_ORIGIN_CLICK_CORRECTION_AND_NATIVE_VALIDATION_V1`  
Delivery: `20260907T070603Z-review-v1`  
**Correction implemented; independent review REQUIRED/PENDING. Slice1C NOT accepted.**

The Owner accepted the prior diagnosis at evidence commit `0ceb2c25aa72a5e6d40730e9a895e64a1d41360f`. That old delivery remains unchanged. This is new frontend-only implementation/validation evidence; no product commit, freeze, merge or push and no backend change/request.

## Result
- Branch: `refs/heads/agent/frontend-wave2-product-ux-v1`; HEAD `f5e19cf53fd010eea2935dd29557e82a879e042c` was dirty, not the source authority.
- Baseline tree `ffeec76721e7334325a4a4c9f3aaea84174d0cb4` → corrected tree `00128d35b97775b97124ad1921053a0da282690d`. **Both are tree IDs, not commit URLs.**
- Exactly two changed product paths: WorkspaceCanvas.tsx and WorkspaceCanvas.test.tsx. One-shot origin/owner/context metadata handles the captured-stage click, preserving ordinary node activation instead of background clear. Group remains during possible drag; ordinary plain click still replaces membership, as in the accepted contract.
- Expected pre-fix RED; corrected Canvas97/97, full frontend370/370, architecture controls120/120, typecheck/lint/guard/build exit0. Lint46 warnings, Vite chunk-size advisory retained.
- Native click11/11. Route21/21. Lifecycle11/12. Supplemental6/6. **Unique native50 executed,49 pass,1 fail,0 not-run in that set.** Raw repeated executions56/pass54/fail2 are separately preserved.
- Real BFCache restoration proved. `real-pagehide-retires-before-suspension` still **FAIL**: observer sees old selection in its pagehide sample. Early observer/microtask ordering is suspected, not proven; no product lifecycle correction or waiver.

## Recommended reading order
1. [Full report](reports/FINAL_REPORT.txt), [exact two-file diff](verification/correction.patch), [source identities](source/SOURCE_IDENTITY.json).
2. [Corrected Canvas](source/current/frontend/src/product/canvas/WorkspaceCanvas.tsx), [tests](source/current/frontend/src/product/canvas/WorkspaceCanvas.test.tsx), [regression coverage matrix](verification/REGRESSION_MATRIX.json).
3. [Native click results](traces/click/CLICK_RESULTS.json), [machine index with ordered full raw traces/commands](INDEX.json), [observer](plans/helpers/passive.js), [native runner](plans/helpers/native_click_v1.py). Large raw files are not omitted: read their ordered parts via the machine index.
4. [Route first raw failure](traces/routes/native.log), [explicit collection change](traces/routes--collect/COLLECTION_CHANGE.json), [remaining route results](traces/routes--collect/NATIVE_ROUTE_RESULTS.json).
5. [Lifecycle results including FAIL](traces/lifecycle--collect/NATIVE_LIFECYCLE_RESULTS.json), [actual BFCache observations](traces/lifecycle--collect/BF_CACHE_RUNTIME_OBSERVATIONS.json), [unmodified failed assertions](traces/lifecycle--collect/COLLECTED_FAILURES.json), [frozen observer](plans/bound-harness/lifecycle-observer.js), [unchanged provider](source/current/frontend/src/interaction/SelectionContext.tsx).
6. [T17/preview supplement](traces/supplement/SUPPLEMENT_RESULTS.json), [check identity/count ledger](verification/NATIVE_CHECK_INDEX.json), [source preservation](verification/PRESERVATION_FINAL.json), [public review](verification/PUBLIC_CONTENT_REVIEW.json), [manifest](MANIFEST.sha256).

Build manifest SHA256: `9644fe897b61e912e9c60bd467b6bf0aec5d497d66f362838e2d6f4750ba331e`. The eight fresh artifacts, including WorkspaceCanvas-Dkcf9Dwz.js, are readable under build/; larger main bundle has ordered lossless chunks. [Build manifest](verification/BUILD_MANIFEST.sha256). Source-to-runtime binding is the actual recorded external production build, not a fabricated source map.

## Limits and next action
- Public payload is sufficient to inspect the bounded correction, executed assertions and retained failures, not to accept Slice1C.
- The pagehide observation boundary remains unresolved; actual restored empty state is not a substitute for the failed requirement.
- Local paths are aliased; original/public SHA256 and bytes are separate. Helpers with aliases are review copies, not turnkey scripts.
- Private browser profiles, Memory/Skills, full source-path census and unrelated worktree inventories are omitted. Full private filesystem preservation cannot be independently repeated from this subset.
- Physical OS IME/touch/screen-reader and actual backend integration not run. Counts50 refer only to the enumerated native contract identities.
- Raw multi-megabyte JSON files are delivered in ordered UTF-8-safe chunks; concatenate without separators. A part need not be valid JSON. The event timeline is a record-preserving derived projection backed by the full trace.
- Late lifecycle collection retains the failed original assertion and exit1. It is not a green replacement run.

Smallest next step: independently review this Canvas correction; separately qualify pagehide event/retirement observation timing without changing its acceptance requirement. Do not infer a new backend requirement or authorize SelectionContext/model edits from this evidence. H4 and tracked-dist remain UNRESOLVED.

All files: [machine index](INDEX.json) and [file-level provenance](provenance/FILES.json). BYTE_EXACT, REDACTED, DERIVED_SUMMARY and LOSSLESS_CHUNK have distinct meanings. Commit-pinned remote verification is recorded after push in a detached receipt, not self-embedded in this commit.
