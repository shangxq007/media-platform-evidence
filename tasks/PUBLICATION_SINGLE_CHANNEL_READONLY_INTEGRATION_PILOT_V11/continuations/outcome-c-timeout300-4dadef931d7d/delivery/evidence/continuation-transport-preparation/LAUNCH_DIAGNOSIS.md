# CLI invocation failures (not tests)

Attempt 01: bare codex-router could not resolve in the background shell, exit 127. Original WRITER_STDERR.log and WRITER_NATIVE.jsonl retained.

Attempt 02: absolute router invocation reached Codex argument parsing, exit 2. Router source /home/user/.hermes/bin/codex-router line 160 injects `--json`; supplied `--json` duplicated it. Offline `/home/user/.npm-global/bin/codex exec --json --json --help` returned exact error `the argument '--json' cannot be used multiple times`. Original attempt02 logs retained. No writer/test/socket execution established for either failed attempt.

Attempt 03 corrects that exact parser issue by omitting caller --json, pins prior authorized [REDACTED_ACCOUNT_LABEL] and explicitly selects gpt-6-astra with openai provider because account config default is gpt-5.6-sol. Router status is only local eligibility, not live entitlement; actual writer execution will determine live availability. Retains workspace-write, approval never and network_access=false. No auth/config changes, new executor type, socket probe or policy bypass. Router output is reconstructed plain native text despite historical .jsonl suffix.
