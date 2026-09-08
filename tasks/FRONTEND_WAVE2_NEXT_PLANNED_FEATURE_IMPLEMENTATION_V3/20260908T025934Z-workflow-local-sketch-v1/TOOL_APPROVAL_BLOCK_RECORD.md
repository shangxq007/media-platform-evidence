# V3 tool-approval block — preserved invocation and response

This is an additive record transcribed from this session's original tool exchange. INTERRUPTED_STATUS.md and existing implementation/test files are not rewritten by this record. V3 feature selection and implementation authorization remain effective; runtime consent is separate. No blocked invocation was retried or rerouted during approval diagnosis.

## Original invocation

Tool: functions.execute_code
Only supplied argument: code (reset omitted).
Exact code value:

```python
T2=T3.parent/'FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V2'
print('prior package scripts',[(p.name,p.stat().st_size) for p in T2.iterdir() if p.is_file() and p.suffix in ['.py','.json']]);print('V3 latest',[(p.name,p.stat().st_size) for p in (W/'frontend/src/product/workflow-sketch').glob('*')]);
print('preservation prefix',list(json.loads((T3/'PRESERVATION_BEFORE.json').read_text()))[:5])
```

Inherited kernel bindings at that call:

- T3: /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3
- W: /home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1
- json: imported Python json module.

Read targets, resolved from those bindings (not freshly inventoried):

1. /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V2 — top-level .py/.json filenames and sizes.
2. /home/user/Documents/workspace/projects/.worktrees/frontend-wave2-product-ux-v1/frontend/src/product/workflow-sketch — direct entries' filenames and sizes.
3. /home/user/Documents/workspace/audit-runs/FRONTEND_WAVE2_NEXT_PLANNED_FEATURE_IMPLEMENTATION_V3/PRESERVATION_BEFORE.json — parse JSON and display its first five keys.

## Original tool response

```json
{"status": "error", "error": "BLOCKED: execute_code script timed out without user response. The user has NOT consented to running this code. Do NOT retry, do NOT rephrase the script, and do NOT attempt the same outcome via a different tool. Silence is not consent.", "tool_calls_made": 0, "duration_seconds": 0}
```

No request_id or approval-resume handle was returned. duration_seconds=0 and tool_calls_made=0 are the original response fields, not a measurement of approval wait length.

## Normal approval mechanism and present limitation

Official references consulted:
- https://hermes-agent.nousresearch.com/docs/user-guide/features/code-execution/
- https://hermes-agent.nousresearch.com/docs/user-guide/security/
- https://hermes-agent.nousresearch.com/docs/guides/secure-hermes-on-a-work-machine

Read-only local implementation evidence:
- /home/user/.hermes/hermes-agent/tools/approval_gateway_wait.py:105-167: queue the request, await a human decision, remove the entry after timeout/completion, return the outcome.
- /home/user/.hermes/hermes-agent/tui_gateway/methods_prompt.py:1108-1172: approval.pending, approval.received, approval.respond; reconnect fallback locates a still-pending request by identity.
- /home/user/.hermes/hermes-agent/tools/approval.py:700-735: approval wait returns output or definitive BLOCKED; unresolved timeout is not consent.

The normal TUI path is a live approval.request card answered by the human via approval.respond. Reconnection fallback supports a still-pending request, not resurrection of a completed timeout. The returned timeout plus queue cleanup implementation means the original request cannot be treated as an actionable pending approval. No direct live pending-queue RPC was executed during this diagnosis.

The exposed execute_code tool has code/reset arguments, not a resume_approval or request_approval_only operation. The agent therefore cannot revive this request or manufacture consent. A fresh request would require resubmission, which remains explicitly prohibited by the current instruction. Do not change approval modes, allowlists, environment flags, transports, paths, or sessions to evade that prohibition. Do not invoke approval.respond on the user's behalf.

Remaining boundary: normal tool-level permission to resubmit the exact operation and a genuine new runtime approval, or an operator-supported approval recovery that explicitly supersedes the old restriction. Neither has been established here. V3 implementation continuation remains paused for this tool-permission boundary, not feature-scope approval. No Skill/Memory bodies or runtime approval settings were changed.
