# Deployment handoff — V11 isolated empty Postiz preparation

## Outcome

**PREPARED_ONLY_IMAGE_PULL_BLOCKED. `LOCAL_EMPTY_INSTANCE_CHECK = NOT_RUN_NO_POSTIZ_INSTANCE`.**

A hardened, digest-pinned configuration was generated and successfully processed by real **podman-compose 1.5.0 `config`** (exit 0). An independent disposable container/network prerequisite check succeeded. **Postiz itself never started.** Its immutable image acquisition exceeded the explicit **300-second limit** and was terminated without retry. The final exact-image existence check returned exit 1. This is a bounded acquisition timeout, not proof of a registry outage or an application defect.

This does not establish a running empty application, an empty account-list response, application readiness, account integration, publication integration, or a product/adapter test pass. No adapter test was run here. The later reported writer sandbox socket EPERM was not worked around; this deployment lane stopped at its own acquisition blocker and performed read-only final inventory.

## Fixed identity and provenance

- Task directory: `TASKROOT/deployment/`
- Project: **`postiz-v11-empty-14e238fa9d`**.
- Candidate release: `v2.23.0`; reviewed source commit `1e4c8dd5c4f70c4d0abd01e23cc42d5b533d1ab9`.
- Official compose source commit: `dd4969e5e694cd009619a0d53cff14c21104580b`.
- Application image: `ghcr.io/gitroomhq/postiz-app@sha256:785f97312f66a347fb96cdccc4ded5a33ced69a672c89a9adc8054e7d6a21dc5`.
- All nine official service image manifests were rehashed against the research digest evidence, and both pin input files were checked for agreement. Compose and both dynamicconfig source hashes matched the research source manifest. Exact image references, including optional services, appear in `source-and-image-validation.json` and `compose.yaml`.
- `linux/amd64` explicitly selected. Tag/manifest resolution is **not signed source-to-image attestation**, vulnerability scanning, or runtime version verification.

## Configuration boundaries actually validated

`compose-validation.json` records the real compose parse/interpolation result and twelve boundary-check categories. `compose.config.redacted.yaml` is the actual resolved config with generated secrets replaced; it is evidence, not a runnable secret-bearing replacement.

- Explicit unique container, volume, and network names; no existing/EP19 database, cache, container or volume reused.
- Six fresh named volumes specified for application configuration/uploads, application Postgres/Redis, Temporal Postgres and Elasticsearch. None were created for the application stack.
- Two task-named **internal bridge networks**; no external network, host networking, privileged containers, Docker socket mounts, or non-task bind mount. Only copied dynamicconfig is mounted read-only.
- Only `127.0.0.1:45071:5000` for Postiz is enabled in the default service set. Optional Spotlight/UI bindings are loopback `45072`/`45073`, behind the disabled auxiliary profile. Temporal RPC and all databases/cache have no host port binding.
- Auxiliary Spotlight, Temporal UI and admin-tools remain disabled by profile.
- `DISABLE_REGISTRATION=true`, `RUN_CRON=false`; provider/payment/AI credentials remain blank. The upstream public Mastodon URL was cleared. Telemetry opt-out variables set. These variables alone are **not** claimed to disable every built-in worker or publish route.
- Outbound containment relies on internal-only networking plus no connected accounts/credentials, not on an invented Postiz send-disable flag. `NET_RAW`/`NET_ADMIN` dropped, no-new-privileges enabled. The engine wrapper removes ambient proxy variables on container create/run/start. Backend route authorization/egress enforcement on a running Postiz process remains untested.
- Secrets were randomly generated server-side into `private/local.env` at **0600**, parent `private/` at **0700**. No secret values or secret hashes belong in public evidence. `.gitignore` excludes private state and tooling. Publish only the explicit nonsecret manifest, never archive this whole directory.

## Actual runtime exercise and final state

The host has Podman 5.4.2 emulating Docker, rootless netavark. No standard Compose provider was installed. A local-only provider was installed under this deployment directory; no system packages, Docker defaults, firewall/sysctls or unrelated project files were changed. Pip emitted an ambient Hermes dependency-conflict warning for python-dotenv; installation used `--target tools`, so the Hermes installation was not modified. The local tool versions are podman-compose 1.5.0, PyYAML 6.0.3, python-dotenv 1.2.3.

The wrapper `podman-isolated` gives this task its own VFS graph store, runroot, temporary directory, network-config directory, cache and empty registry auth file, all beneath `deployment/private/`. Default Podman-store inventory was read only; no unrelated container environment or private database content was inspected.

Executed prerequisite scope:

1. Fresh isolated engine inventory: no containers or volumes; only the engine's default network definition.
2. Created and inspected `postiz-v11-empty-14e238fa9d-egress-preflight` with `internal=true`.
3. Pulled the exact Redis dependency image and ran a disposable **shell only**, not a Redis server, to read its network-namespace IPv4/IPv6 routing tables. IPv4 had only the connected subnet, no default route; IPv6 had local/link routes and reject/unreachable defaults. No public probe/social request was sent.
4. The route probe exited 0 with `--rm`; the exact preflight network was removed successfully.
5. Bounded image acquisition completed for application Postgres, Redis, Elasticsearch, Temporal Postgres and Temporal auto-setup. Postiz acquisition timed out at 300 seconds while copying layers. Optional images were not pulled.
6. Final read-back: **zero containers, zero volumes, no task-created networks, no scoped engine/conmon processes**, and no listeners at the configured ports. The isolated engine default `podman` network definition and **five dependency images** remain. Partial application download/cache state may remain under the private graph/tmp directories.

See `runtime-exercise.json`, `image-pull-results.json`, `engine-preflight.json`, and `final-runtime-state.json`. The latter is authoritative for final runtime state; `identity.json` records preparation identity rather than a successful deployment.

## Readiness / account gate

- No Postiz HTTP, public API, private API, OAuth/connect, upload, send or database-read request was made.
- No user/account/organization, fake historical post, provider connection, API key, or OAuth credential was created.
- Application health, frontend rendering, Temporal/application readiness and actual Postiz data emptiness are **NOT TESTED**.
- No existing account credential or exact channel binding was supplied. Registration is disabled. A new empty instance cannot satisfy authenticated account integration without a separately authorized initialization/credential step, which this task expressly forbids. Do not create accounts to clear this gate.
- An eventual successful empty public list would still not constitute real single-channel account integration.

## Runbook — preparation/validation only under current stop

From the exact task directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 validate.py
PYTHONDONTWRITEBYTECODE=1 python3 finalize-evidence.py
```

Do not rerun `prepare.py`: it intentionally refuses to overwrite the existing identity/secrets. Do not run raw `docker compose`, which uses the default engine store and lacks a provider. Do not print unredacted `podman_compose config` output. Do not run adapter tests through this engine or use it to evade the writer's sandbox denial.

Any later independently authorized continuation must first resolve the Postiz image acquisition blocker, recheck all exact pins and current port/name collisions, and establish the internal-network/proxy boundary for **every** service before starting Postiz. It must retain the fixed project and isolated engine wrapper, private env file, disabled auxiliary profile and no-account rule. If runtime compatibility fails, preserve the real error and stop; do not add host networking, default routes, host firewall/sysctl changes, relaxed registration, or real provider credentials. Readiness would be limited to service health and an approved unauthenticated root request; no OAuth/connect routes even if GET. No start command was executed in this handoff.

## Cleanup / retained state

Already cleaned and read back: the disposable route container and its exact preflight network. No application stack resources exist to stop or delete. No cleanup against the default Podman store is authorized or necessary.

**Explicitly retained:** `private/` (throwaway secrets, isolated engine dependency images and possible partial pull/temp state), `tools/` (local Compose provider), configuration, scripts and nonsecret evidence. These are not a retained running service. Keep `private/` access restricted. If the owner chooses to discard retained image state, use only this directory's `./podman-isolated rmi <exact-image-reference>` after confirming the empty container inventory; never global prune/reset, default-engine cleanup, or deletion of unrelated resources. Secret removal/recreation requires an explicit new preparation lifecycle; do not repurpose these throwaway credentials.

## Exact artifact paths

All paths below are relative to the task directory given above:

- `DEPLOYMENT_HANDOFF.md` — this report/runbook.
- `compose.yaml` — hardened digest-pinned deployment definition; secret placeholders only.
- `dynamicconfig/development-sql.yaml`, `dynamicconfig/development-cass.yaml` — byte-identical reviewed source copies.
- `identity.json`, `source-and-image-validation.json` — fixed resource identity and verified provenance.
- `compose-validation.json`, `compose.config.redacted.yaml` — real Compose config validation and safe resolved evidence.
- `engine-preflight.json`, `runtime-exercise.json`, `image-pull-results.json`, `final-runtime-state.json` — executed runtime prerequisites, actual blocker, final read-back.
- `public-artifact-manifest.json` — nonsecret artifact paths/hashes; **only these files may enter public evidence**.
- `prepare.py`, `validate.py`, `exercise-prerequisites.py`, `pull-images.py`, `finalize-evidence.py`, `podman-isolated` — task-only reproducible procedures; prerequisite/pull scripts are not application integration tests and are not instructions to retry after this stop.
- `.gitignore` — privacy exclusions.
- **PRIVATE / DO NOT PUBLISH:** `private/local.env`, `private/registry-auth.json`, remaining `private/` runtime state; `tools/` is excluded from public evidence.
