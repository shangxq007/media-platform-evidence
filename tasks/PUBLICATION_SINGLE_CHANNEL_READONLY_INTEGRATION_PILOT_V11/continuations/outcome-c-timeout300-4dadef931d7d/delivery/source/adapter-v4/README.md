# Owner-local external observation adapter v4

Runnable source definitions, authored offline. This is not an accepted media-platform Project, graph, publication-plan or EffectiveAccess API. Ordinary product frontend remains unavailable and untouched. External provider/instance/account/post references and all core relationships stay `PENDING_CORE_CONTRACT`.

Source layout:

- `model.py`: corrected v2 projection starting point, strengthened credential redaction, exact synthetic IP and required external identity validation.
- `wire.py`: socket-free exact HTTP framing, strict JSON and fixed raw-Authorization GET builders.
- `boundary.py`: closed source configuration, exact identity/query binding, receipt/revision, read reservation, retirement and client projection validation.
- `transport.py`: actual nonblocking socket/TLS IO with one absolute operation deadline and byte budget.
- `server.py`: one serial bounded handler, listener binds only `('127.0.0.1', 0)` and exposes its actual OS-assigned port through a trusted immutable `RuntimeHandle`; server-side upstream credential only.
- `runtime_handle.py`: pure owner-only bound-address metadata; no network deserializer or caller destination.
- `client_state.py`: immutable detached owner configuration, complete preflight, strict receipt/envelope validation and generation ordering.
- `client.py`: authenticated access→snapshot path; every IO operation checks its generation and deadline, and publication is atomic with newer-read/retirement state changes.
- `owner_runner.py`: actual combined bounded server/client lifecycle, passing the server handle directly to the client.
- `transport_tests.py`: unconditional actual synthetic HTTP unittest definitions. No skips/placeholders; never imported or collected in this packet.
- `test_correction_pure.py`, `run_pure.py`: only new v4 pure identities are selected in this packet. Historical pure sources are copied and preserved but their suites are not rerun. No fake IO is used for generation proofs.

The only execution allowed in this packet is `python3 -B ../correction-v4/verify_offline.py` from this directory. It compiles source in memory, inventories transport identities by AST and invokes only `run_pure.py`. The runner blocks socket audit events and imports of socket, asyncio and all transport/server/client modules. It never constructs an event loop or steps a coroutine. Pure HTTP grammar assertions are byte parsing, not HTTP execution.

## Future commands — NOT executed here

Prerequisites: Python 3.11+ standard library; independently qualified socket capability; OS-assigned ephemeral loopback listener capability for both adapter and synthetic peers; bounded serial test execution. Owner HTTP functionality authorization already exists. Current environment capability is `UNQUALIFIED`; do not probe, retry, change sandbox/network policy or ask renewed functionality approval in this packet.

From `adapter-v4/`, in a future capability-qualified gate:

```sh
python3 -B -m unittest -v transport_tests
```

This is synthetic transport evidence only, even if it later passes. Use a fresh future evidence directory and capture native exit, exact source hashes and per-test results. Definitions bind only loopback; no real provider or credentials needed. The fixture starts one synthetic upstream thread and one adapter thread, enforces bounded waits/joins, and closes every accepted socket. Test failure is a failure, not a skip.

For a separate later explicitly configured owner-local read, the owner supplies a JSON source config and server environment. No credentials are in JSON or CLI arguments. Fixed server environment names are `OBSERVATION_LOCAL_TOKEN` and `OBSERVATION_UPSTREAM_KEY`; they must differ and each be 16–4096 printable ASCII non-space characters. The combined owner process receives both; only the local token is passed to the Client object. The upstream key stays in Authority/server state. No credential discovery or retrieval occurs.

```sh
python3 -B owner_runner.py --config /OWNER_SUPPLIED/source.json --request-id owner-read-1
```

The combined runner validates inputs, starts the ephemeral server, waits at most two seconds for readiness, passes the in-memory non-secret handle directly to the client, performs one bounded read, retires the client/server, and joins the server thread within the configured bound. There is no persisted discovery, arbitrary URL/port option or application configuration mutation. Only a value-safe status/count is printed. `server.py` and `client.py` are library modules; no unimplemented separate-process launch recipe is offered. These commands are documentation, not instructions to execute during this offline task. Real reads additionally require exact approved provider version, host and literal IP, principal/tenant/session/workspace/project/source/owner binding, instance/account, half-open dates, organization-wide read consent and explicitly provided credentials. Core integration remains unresolved regardless of a successful local read.

## Closed configuration and protocol

Required JSON keys: `provider` (exact `postiz`), `instance_id`, `base`, `approved_ip`, `version` (exact `v2.23.0`), `binding`, `external_account_id`, `start_inclusive`, `end_exclusive`, `organization_read_consent` (exact true). Binding has exactly `scope` and `ownerId`; scope has exactly `principalId`, `tenantId` (string or null), `sessionId`, `workspaceId`, `projectId`, `sourceId`. Identifiers use the bounded model grammar.

Optional typed keys: `synthetic` and `content_allowed` booleans; integer `max_bytes` 1024–1048576, `timeout_seconds` 1–10, `max_reads` 1–60, `max_records` 1–200. Unknown/duplicate fields, coercions and JSON nonfinite constants fail. Config loading is capped at 16384 bytes. Source config is owner-controlled, never accepted from HTTP callers. Synthetic base must be HTTP at literal 127.0.0.1 with the same approved IP. Real base must be HTTPS; path is `/public/v1` or `/api/public/v1`, without userinfo/query/fragment/escapes. Connect uses only the approved literal IP, TLS checks the configured host, and proxies/DNS/caller destinations are not used.

Local methods are GET only: `/observations/access` and a canonical `/observations/snapshot?requestId=...&startInclusive=...&endExclusive=...`. Required headers bind raw local Authorization and exact `X-Observation-Identity` JSON (binding/provider/instance/account/startInclusive/endExclusive). Snapshot additionally binds server-issued `X-Observation-Revision`. The actual client obtains and validates the receipt first, then checks its exact echo and the closed snapshot projection. Local access is a 30-minute, nonrenewing owner-local receipt, narrower than platform authorization. Server restart issues a new opaque access revision, pinned in the runtime handle. Exact Host must match the actual bound port; localhost aliases and other ports fail. The internal handle issuer accepts only the owner runtime getsockname tuple; it is not an HTTP input or protection against hostile Python code already inside that owner process. Retirement never revives a client snapshot.

Upstream only GET integrations and posts, raw Authorization (no Bearer), exact configured dates; end translates to endExclusive minus one millisecond. Both endpoints read organization-wide; filtering an account does not reduce credential authority, so explicit organization-wide consent is mandatory. No limit/cursor/paging/retry/write request is generated. Two read slots are conservatively reserved before each snapshot; a failed request does not refund slots. An odd remaining slot cannot start a snapshot.

Headers cap at 16384 bytes. Only unambiguous Content-Length response framing is supported; transfer encoding, duplicate headers, folded/control headers, missing length, oversized body, trailing data and redirects fail closed. Each operation bounds all waits and response volume. Server volume cap is `2*(max_bytes+16384+1)+16384`; client cap is `2*(max_bytes+16384+1)` across access plus snapshot. Both upstream requests share the server's original deadline; the client uses one deadline across its complete roundtrip. Expiry/retirement/disconnect/extra body bytes are checked throughout IO. Cancellation drops outstanding results; already-delivered bytes cannot be recalled. Deadline exhaustion closes without a late error body. Descriptor close does not wait for peer/TLS teardown. Handler failures use fixed value-free classes and safe statuses; request, credentials, URLs, upstream messages and content are not logged.

Projection distinguishes absent required upstream identity/date (safe invalid read) from missing optional state (unknown), content not granted (omitted), and unavailable relations (`PENDING_CORE_CONTRACT`, never empty arrays). Recurrence and out-of-window records count as omissions; record caps mark partial. Unknown provider states and ERROR never invent attempts, outcomes or actual publication times. Credential checks include nested keys/values and encoded/escaped representations; this is bounded rejection of specified representations, not a claim to decode arbitrary transformations.

## V4 reconciliation and execution limits

Final v3 already had strict access-receipt boolean/lifetime checks and closed snapshot validation; v4 retains those and additionally validates the echoed receipt with exact types and the runtime revision. Snapshot provider/instance/account/window/access/contract must match the frozen configuration already matched to the access receipt. Starting a valid newer read invalidates an older generation even if the newer read later fails. The last accepted snapshot stays until replaced or retired; retirement clears it. Invalid request IDs fail before access acquisition and do not advance the generation.

Pre-read wrong revision returns safe 403 ACCESS_RETIRED without upstream reads. Active retirement, cancellation and deadline expiry close without a late response; already-sent bytes cannot be recalled. The corresponding authored real HTTP tests assert EOF/no publication, and two new concurrent-read definitions cover supersession during IO and a completed older HTTP response released after newer publication. The latter uses a bounded barrier at pure envelope acceptance after real HTTP, not simulated transport. Neither test is executed here.

All transport identities remain `NOT_RUN_CAPABILITY_UNQUALIFIED`. Syntax and pure evidence are not runtime verification or independent acceptance. No Outcome B; real/core binding remains unresolved.
