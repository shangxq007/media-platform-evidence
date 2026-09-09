# V11 additive image-acquisition continuation

**PERFORMED_BOUNDED_IMAGE_ACQUISITION_TIMEOUT.** Exactly one native acquisition was attempted through the original, unmodified task-private engine wrapper. No application or adapter was executed.

- Fixed image: `ghcr.io/gitroomhq/postiz-app@sha256:785f97312f66a347fb96cdccc4ded5a33ced69a672c89a9adc8054e7d6a21dc5`; explicit `linux/amd64`, `--retry=0`.
- Start: 2026-09-09T11:37:27.436364+00:00; finish: 2026-09-09T11:42:27.502449+00:00.
- Fixed deadline: 300 seconds; measured elapsed: 300.066111 seconds including termination. Native process return code **-9 (SIGKILL at deadline)**, not a successful pull. No further retry authorized or performed.
- Exact-image read-back: exit **1**, image unavailable. Five original dependency image identities/digests remain in the task store; zero containers, zero volumes, only the existing `podman` network definition.
- Task image-temp files: 929439240 bytes before; 1777160928 after pull; 1777160928 after inventory. Progress snapshots show actual growth, then stable byte totals in the final minute. These are temporary files, **not validated layer-completion percentages or resumability proof**.
- Native post-pull inventory reported automatically deleting an incomplete layer. No manual cleanup, global store access, or privilege/network changes were performed.

## Offline verification and preserved history

Nine saved registry manifests rehashed to their existing pins. Both research pin inputs agree. Original Compose references match all nine image pins; the redacted resolved config matches its enabled services. Reviewed official Compose/dynamicconfig source hashes match. Static config retains linux/amd64, internal-only named networks and loopback-only configured bindings. No secret env file was read or interpolated, no configuration changed, and no listener was created.

Candidate release remains **v2.23.0**, source commit `1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9`, compose commit `dd4969e5e694cd009619a0d53cff14c21104580b`. These are source/pin identities, **not a runtime version claim or signed image attestation**.

An initial new offline checker stopped before acquisition with `KeyError: spotlight`: disabled auxiliary services are absent from the resolved redacted Compose. The checker was corrected to require the disabled profile for omitted services. Its initial snapshots remain at this directory root; the sole acquisition receipts are under `bounded-attempt-01/`.

All original allowlisted deployment files, their manifest, and the selected sealed continuation ZIP/receipt remain hash-identical (22 preserved files). Old timeout evidence was not overwritten. This additive report supersedes **only the image workline's NOT_PERFORMED status** with an evidenced attempted/timeout result; the existing sealed package is not modified, unsealed, or republished.

## Separate unexecuted gate

**LOCAL_EMPTY_INSTANCE_CHECK = NOT_RUN_ENVIRONMENT_UNQUALIFIED.** No startup, readiness/root HTTP request, DB/data mount, account creation, OAuth, real upstream API, post/upload/media operation, denied adapter/socket test, or alternative test execution environment was used. No B/A, runtime-version, or independent-acceptance claim follows from this acquisition.

The bounded recovery budget is exhausted. Image completion remains blocked by the measured acquisition timeout; this is not evidence of a registry outage or application defect. Further acquisition would require new owner direction; application startup separately requires a qualified environment and its own boundary checks.

## Evidence handling

`PUBLIC_SAFE_ALLOWLIST.json` is the only additive publication candidate list; nothing was published. It excludes tooling and all private engine/auth/environment/cache contents. Native logs were reviewed: only fixed image/blob digests and normal copy progress appear. Cache evidence contains file stat metadata only. Do not archive the deployment directory, engine cache, secret files, or unallowlisted continuation files.
