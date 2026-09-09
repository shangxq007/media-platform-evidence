# V11 execution environment recovery review

## Decision

**READ-ONLY INVESTIGATION COMPLETE; EXECUTION RECOVERY NOT QUALIFIED. Do not rerun the test yet.**

The earlier denial is explained by the actual Codex exec route, not a missing approval environment variable. Both original V11 sessions ran Codex **0.153.4**, `approval_policy = never`, `workspace-write`, and `network_access = false`. The installed CLI and version-matched upstream source confirm those semantics.

There is **no evidenced, already-approved working route** in the reviewed V11 records that provides exactly `127.0.0.1`, an ephemeral TCP port, the synthetic local client, and cleanup. There is a supported **experimental managed-proxy / isolated-network route** worth distinguishing from broad network access, but it is not an exact address/port capability grant and has not been exercised here. It must not be represented as an approved or tested recovery.

**Minimal permitted applied diff: empty.** No config or execution policy was changed. A bare `-c sandbox_workspace_write.network_access=true` is specifically **not permitted**: absent managed proxy enforcement, Linux retains the host network namespace. Turning sandboxing off, switching to an unsandboxed Hermes terminal to repeat the test, changing global configuration, or manufacturing an approval variable is not an acceptable substitute.

## Scope and preservation

Owner authorization considered: only bind `127.0.0.1` on an OS-assigned ephemeral port, a local test client, synthetic data, and cleanup. Prohibited: sandbox-off, global configuration changes, arbitrary network/host networking, denial bypass. The current phase explicitly forbids running sockets/tests or changing configuration.

All explicit writes in this investigation were confined to this new `continuation-environment/` directory: this report, sanitized policy evidence, help output, public documentation/source snapshots, and hash manifests. No product, adapter, existing receipt, router, account configuration, Skill, or Memory was modified. No model invocation, login, quota probe, sandbox command execution, socket test, or test rerun was performed. Public documentation was fetched as research; this did not grant network permission to the blocked Codex session.

## 1. Exact prior evidence and the actual route

Task root:

`/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11`

Read:

- `writer/BLOCKER.json`: `SANDBOX_SOCKET_DENIAL`; setup failure; behavioral assertions did not run.
- `writer/approval-retrigger-01/receipt.json`: one attempt; no approval requested, no prompt, policy `never`, no subsequent retry, blocked.
- **Actual native log path:** `/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11/APPROVAL_RETRIGGER_01_NATIVE.log` (not under `writer/`). This file contains the router-reconstructed assistant narrative, not a full native event stream; it alone is insufficient to establish effective policy.
- `writer/approval-retrigger-01/native-output.txt`: Python fails at **socket creation**, before successful bind: `socket.socket(AF_INET, SOCK_STREAM, 6)` → `PermissionError: [Errno 1] Operation not permitted`. The subsequent `could not bind ... ('127.0.0.1', 0)` is the setup error wrapping that failure. This is not evidence of a port collision or failed behavioral assertion.

The stronger native evidence is the sanitized extraction in `session-policy-evidence.json`, taken from these actual [REDACTED_ACCOUNT_LABEL] rollouts:

1. `[REDACTED_INTERNAL_ACCOUNT_PATH]`
2. `[REDACTED_INTERNAL_ACCOUNT_PATH]`

Each contains V11 task references. Each `session_meta` reports `source: exec`, `cli_version: 0.153.4`. Each `turn_context` at **line 8** records:

```json
{
  "cwd": "/home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1",
  "approval_policy": "never",
  "sandbox_policy": {
    "type": "workspace-write",
    "writable_roots": ["/home/user/Documents/workspace/audit-runs/PUBLICATION_SINGLE_CHANNEL_READONLY_INTEGRATION_PILOT_V11"],
    "network_access": false,
    "exclude_tmpdir_env_var": false,
    "exclude_slash_tmp": false
  },
  "model": "gpt-6-astra"
}
```

The **session root was the worktree**, not the adapter; the test's tool-specific working directory was `taskroot/adapter`. The V11 path was an additional writable root. The original filesystem policy was therefore wider than a continuation-only write scope; do not describe it as a taskroot-only filesystem sandbox.

## 2. Where approval, sandbox, and networking came from

| Layer | Read-only finding | Consequence |
|---|---|---|
| Router | `/home/user/.hermes/bin/codex-router`, lines 150–161: copies environment, sets account `CODEX_HOME`, defaults proxy variables, invokes `["codex", "exec", "--json"] + args` | Router does not inject approval policy or sandbox/network grants. |
| Account resolution | Current router state maps `[REDACTED_ACCOUNT_LABEL]` to `[REDACTED_INTERNAL_ACCOUNT_PATH]`; only name/home fields were selected | Effective account config is that home's `config.toml`, not simply `~/.codex/config.toml`. Auth contents were not read. |
| Account config | No `approval_policy`, `approvals_reviewer`, `sandbox_mode`, `sandbox_workspace_write`, `permissions`, `default_permissions`, `features`, or `profile` key present | `never` is not a configured [REDACTED_ACCOUNT_LABEL] approval setting; there is no [REDACTED_ACCOUNT_LABEL] network exception to recover. |
| `codex exec` harness | Version source `codex-rs/exec/src/lib.rs:408–453`: `approval_policy: Some(AskForApproval::Never)`; config rebuilt only for resolved auto-review behavior | Headless exec is the concrete source of `never`. Config core `mod.rs:3638–3642` prefers the harness approval override over config. A hypothetical `-c approval_policy=on-request` is not a demonstrated fix. |
| Sandbox CLI | User-provided route includes `--sandbox workspace-write`; source `exec/src/lib.rs:296–300` maps that argument to sandbox override; native context agrees | Workspace-write came from the launch selection. |
| Network default | Version schema `definitions.SandboxWorkspaceWrite.properties.network_access.default = false`; actual context records false | Default restricted networking applies; no per-loopback exception is implied. |
| Linux enforcement | Version `linux-sandbox/src/landlock.rs:186–216,250–253` rejects non-AF_UNIX socket creation and bind/listen/connect in Restricted mode with EPERM | Precisely consistent with the native failure; no new syscall probe was needed. |

Scoped config checks found no project `.codex/config.toml` inside the recorded worktree or along the inspected adapter/worktree ancestor paths except `/home/user/.codex/config.toml`, which also has no selected policy keys. That home file's mere presence in an ancestor walk does not establish it was loaded above the worktree project boundary. `/etc/codex/managed_config.toml` and `/etc/codex/requirements.toml` were absent. No claim is made that unavailable historical/cloud-managed layers were exhaustively reconstructed; the actual recorded turn policy is the effective-policy authority.

Current investigator environment: `CODEX_HOME`, `CODEX_ROUTER_BASE`, `CODEX_SANDBOX`, and `CODEX_SANDBOX_NETWORK_DISABLED` were unset; proxy variables were inspected only as set/unset. This is **not** a reconstruction of the historical child's entire environment. Router defaults include `http://127.0.0.1:7890`, but a provider proxy URL does not grant the child's test process loopback sockets.

Router lines 218–246 also show `--account [REDACTED_ACCOUNT_LABEL]` is a preference, **not exclusive pinning**: quota failures can fall through to another account. No router execution was attempted. Any future qualification must verify the actual selected home/session rather than assuming the argument establishes identity.

## 3. Supported configuration: broad switch versus isolated managed networking

### A. Legacy workspace-write network switch — supported, but prohibited here

The installed `codex exec --help` supports task-invocation `-c key=value` overrides. The schema and current configuration reference document:

```text
-c sandbox_workspace_write.network_access=true
```

This is not loopback-specific. In version source `linux-sandbox/src/linux_run_main.rs:432–442`, enabled network without managed routing selects `BwrapNetworkMode::FullAccess`; `bwrap.rs:86–104` defines FullAccess as keeping the **host network namespace**. `landlock.rs:96–116` skips the restricted network filter for enabled networking without managed proxy enforcement.

**Do not apply or execute this standalone change under the present authorization.**

### B. Managed proxy plus isolated Linux network — real supported mechanism, not yet a qualified exact grant

Unlike the standalone switch, Codex 0.153.4 includes:

- `features.network_proxy` (boolean or table), documented and schema-backed.
- `features.network_proxy.enabled`, `domains`, `allow_local_binding`, `allow_upstream_proxy`, `enable_socks5`, `enable_socks5_udp`, `proxy_url`, and defensive `dangerously_allow_*` booleans.
- Named `permissions.<name>.network` profiles and `default_permissions`. The installed `codex sandbox --help` also exposes `-P, --permission-profile`; this is not an `exec` flag, and no sandbox command was run.

**Both network-enabled permissions and the managed-proxy feature are necessary.** Config source `core/src/config/mod.rs:3621–3630` activates the proxy only when the feature is enabled **and** the selected permission profile already has network access. `permissions.rs:120–131` explicitly states that profile network settings do not themselves start the managed proxy. Enabling only `features.network_proxy` on the original network-disabled route is not an established fix.

When activated through Codex, Linux selects `ProxyOnly` ahead of FullAccess (`linux_run_main.rs:432–442`), uses a new network namespace (`bwrap.rs:86–104`), activates managed bridges (`linux_run_main.rs:223–237`), and uses ProxyRouted seccomp (`landlock.rs:218–246`). That seccomp mode permits AF_INET/AF_INET6 sockets inside the isolated namespace and is source-consistent with same-command local server/client operation. **It does not grant unrestricted host networking.** This is a source-based capability assessment, not a runtime success claim.

The feature is explicitly **Experimental, default disabled** in `features/src/lib.rs:1204–1212`. There is no evidence these prior V11 sessions used it.

#### Why this is not an exact permitted minimal diff yet

1. The exposed policy does not constrain the synthetic process's bind to exactly `127.0.0.1` and port `0`; ProxyRouted permits IP sockets generally within its isolated namespace, including IPv6. A domain allowlist controls proxy destinations, not the local server's bind address/port or synthetic-data discipline.
2. Managed routing starts additional proxy/bridge listeners and has its own lifecycle. Defaults include fixed host-loopback HTTP/SOCKS ports and SOCKS/UDP support (`network-proxy/src/config.rs:150–169`). Those defaults are not the requested single ephemeral test capability. An ephemeral-only, fully cleaned-up setup would require qualification of all supporting listeners, not merely a prompt assertion.
3. `allow_local_binding=true` is **not** a narrow Linux bind grant. Current docs describe broader local/private-network access; leave it false in any reviewed restricted candidate. Explicitly allowing proxy destination `127.0.0.1` can expose unrelated host-loopback services through the host-side proxy, rather than merely the test server inside the isolated namespace. Do not add that rule as an assumed fix.
4. Proxy domain restrictions do not cover model API traffic, web search, apps, or MCP. Existing provider connectivity is a separate control-plane route; enabling hosted tools is not authorized by the test exception.
5. Empty allowlists alone can interact with embedding approval policy hooks. Explicit deny semantics, source-version wildcard behavior, effective managed requirements, proxy configuration merge behavior, and fail-closed startup need review before asserting an all-egress-denied profile.
6. Source availability and schema acceptance do not prove this host can establish the required namespace/bridges. No setup attempt was authorized in this phase.

For clarity, the **documentary activation delta** would require the following pair, not either alone:

```diff
+ invocation override: sandbox_workspace_write.network_access = true
+ invocation override: features.network_proxy.enabled = true
```

**This pair is NOT a permitted or complete execution recipe. Do not apply it.** A reviewed candidate would also need explicit all-egress-denied proxy policy, no upstream chaining, no SOCKS/UDP, no broad local/private access or Unix-socket access, ephemeral loopback-only support listeners, unchanged filesystem containment, and verifiable cleanup. The investigation does not invent unsupported bind-address/port capability flags or claim that those qualifications have been met.

Therefore the answer is not “Codex only has broad networking,” but also not “a verified exact loopback-only task exception is ready.” **A narrower experimental mechanism exists; an exact, approved, operational V11 route remains unproven.** Under the Owner's strict capability interpretation, no nonempty permitted diff can currently be certified.

## 4. Approval and Hermes boundaries

Loaded `codex`, `coding-agent-account-routing`, `hermes-agent` plus its security/privacy reference, and `execution-route-preflight`. Fetched official Hermes docs index/security documentation. The older Codex skill's suggestion to use `danger-full-access` in problematic service environments is outside this Owner authorization and was not used. No Skill was edited.

Hermes shell smart/manual approvals and Codex child sandbox/approval policy are separate layers. A Hermes tool call being auto-approved does not change an existing Codex exec session's `never` policy or authorize the denied test on another execution route. No fake approval environment variable, `--approve-for-me` substitution, automatic reviewer, undocumented internal proxy flag, or sandbox bypass was used or proposed as a fix.

Current CLI top-level help exposes `-a/--ask-for-approval` with `on-request|never`; `codex exec --help` does not list that option and its version source supplies headless Never. Changing to an interactive route could provide an approval UI, but a UI does not itself establish the requested narrowly enforced network capability and is not an approved recovery here.

## 5. Sources, commands, versions, and integrity

Read-only command outputs retained locally (all returned exit 0):

- `command -v codex` → `/home/user/.npm-global/bin/codex`
- `codex --version` → `codex-cli 0.153.4`
- `codex --help` → `cli-help.txt`
- `codex exec --help` → `cli-exec-help.txt`
- `codex sandbox --help` → `cli-sandbox-help.txt` (**help only**)
- `codex debug --help` → `cli-debug-help.txt`

Actual JavaScript launcher:

`/home/user/.npm-global/lib/node_modules/@openai/codex/bin/codex.js`

Actual native binary:

`/home/user/.npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`

Selected SHA-256 values (calculated from actual bytes):

| Item | SHA-256 |
|---|---|
| Native binary | `56ef98ab4032d317ab26e9b5e5a175650717351edb16ed9cde0cb6d1734d62da` |
| Launcher | `61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70` |
| Router | `53908afc07a9b1fedc001e6e46cc4d09d33ae9d3f51b6c92f7ed9683c8ff868c` |
| Original blocker | `2dd913b1ac2a59db0f91031e53e5e07bce153e8dc47e300bc7e1d9c8f8febb09` |
| Retrigger receipt | `2ece2da0a7d3e1c3f08967e462bf3336de697c795a814833666a771cce91e5d8` |
| Actual retrigger native log | `2641ad90cb283d320645858ecc059715dac3348ec593e5d75bd6e3496f198a43` |

Complete local evidence paths, byte lengths, collection time, and hashes are in `local-source-hashes.json`; sanitized configuration is in `scoped-config-sanitized.json`. Rollout contents and credentials were not copied; only scoped policy metadata was retained.

Official references fetched:

- https://developers.openai.com/codex/security/
- https://developers.openai.com/codex/config-reference/
- https://hermes-agent.nousresearch.com/docs/llms.txt
- https://hermes-agent.nousresearch.com/docs/user-guide/security/
- Version-matched upstream source base: https://raw.githubusercontent.com/openai/codex/rust-v0.153.4/
- Exact source paths: `codex-rs/exec/src/lib.rs`, `codex-rs/core/config.schema.json`, `codex-rs/core/src/config/mod.rs`, `codex-rs/core/src/config/permissions.rs`, `codex-rs/linux-sandbox/src/{landlock,bwrap,linux_run_main,proxy_routing}.rs`, `codex-rs/network-proxy/src/{config,policy}.rs`, `codex-rs/features/src/lib.rs`, `codex-rs/network-proxy/README.md`.

Downloaded public sources/help have individual hashes and exact URLs/commands in `sources.json`. GitHub's recursive tree response for `rust-v0.153.4` reports tree SHA `3d2ee51ca2d5db578f328aa75e20aa22c0197c9a`; this is a **tree identifier, not a claimed native-binary build attestation or commit hash**. The release tag matches the reported CLI version; no reproducible-build equivalence was asserted.

The README and current docs have a relevant discrepancy: the README says a global `*` wildcard is rejected in its example, while its security notes qualify acceptance and current config-reference advertises global `*`. This is one reason no guessed all-egress-denied runnable profile was presented. Implementation and effective-policy readback must take precedence over an unchecked snippet.

## 6. Verification and remaining blocker

Verified without executing the blocked operation:

- Original failure classification and setup-only outcome from existing evidence.
- Native effective policy from both [REDACTED_ACCOUNT_LABEL] rollouts, including actual worktree root and additional writable task root.
- Installed CLI version/help, router behavior, scoped current account configuration, and version-matched policy/enforcement source.
- Public documentation/source and local evidence hashes captured; no credential values intentionally emitted or saved.

Remaining blocker: **no approved, verified exact-scope execution environment has been established**. Do not repeat the previous denied command. A future phase needs a reviewed supported route with an explicit capability/lifecycle contract covering both the test and infrastructure listeners, plus separate authorization for a bounded qualification. If that contract cannot be enforced by the supported route, report the limitation rather than expanding authorization or disabling containment.

Research-tool issues: `web_extract` could not extract with the configured search-only backend; public documents were retrieved through standard HTTPS reads instead. The optional BeautifulSoup module was absent; stdlib HTML text extraction was used, with original HTML retained. Neither issue affected the native-policy or version-source findings.
