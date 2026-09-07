# Media Platform review evidence

This repository stores **review evidence**, not canonical product code. Evidence delivery commits are not product candidates, releases, deployments or implementation acceptance.

Start with [the task catalog](tasks/INDEX.json). Each task has a unique append-only delivery directory and readable `INDEX.md` / `INDEX.json`. Independent review remains **PENDING** until separately recorded.

## Pin a review
Use a full 40-character **evidence commit SHA** in GitHub `/blob/<commit>/.../INDEX.md` or `raw.githubusercontent.com/.../<commit>/.../INDEX.md`. Never put a product **tree** SHA into a commit URL. Detached post-push receipts record evidence commit identities without creating a self-hash cycle.

## Integrity and provenance
Each delivery's `MANIFEST.sha256` hashes its payload, including indexes but excluding itself. `provenance/FILES.json` binds original sealed archive paths and SHA256 values to public files, sizes and classifications. `INDEX.json` maps claims to evidence. Public metadata is DERIVED_SUMMARY; its final hashes are in the manifest and detached delivery receipt.

BYTE_EXACT means unchanged bytes. REDACTED means declared substitutions. DERIVED_SUMMARY means a separately identified projection or explanation. LOSSLESS_CHUNK means a UTF-8-safe part of a named parent: concatenate listed parts exactly, without separators. Parts need not be independently valid JSON/JavaScript. The parent records whether reconstruction equals the original or a redacted public derivative. No LFS pointers or base64 ZIP substitutes.

Public delivery is intentionally narrower than a private audit directory. Omitted private profiles, Memory, credentials, unrelated file inventories and predecessor archives are explicitly disclosed. Zero secret-scan matches alone do not establish suitability for publication.

## Future deliveries
Append a new unique delivery directory; do not overwrite old evidence, amend delivery history or force-push. Update catalogs by normal additive commits. Corrections require a new delivery with explicit supersession/provenance, preserving earlier failures and limitations. Keep product code changes, CI, hooks, package scripts and account settings outside this repository.
