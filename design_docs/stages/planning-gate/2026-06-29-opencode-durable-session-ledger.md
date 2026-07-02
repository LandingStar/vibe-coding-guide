# Planning Gate - OpenCode Durable Session Ledger

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now has one-shot worker runtime parity plus host-owned serve
readiness. The next gap toward stable continuous worker runtime is durable
session policy: OpenCode can select, continue, and fork sessions at CLI level,
but dbc had no durable local receipt for deciding which session should be
reused for a lane, worker, or task.

## Scope

Add the smallest durable OpenCode session layer:

1. define a local OpenCode session binding ledger;
2. support `claim`, `release`, and read-only `inspect`;
3. bind sessions to `lane`, `agent`, `task`, or `custom` scopes;
4. recommend `lane` as the default scope for same-lane continuity;
5. write only compact host-owned receipt data:
   attach URL, session ID, scope, owner/lane/worker refs, status, and timestamps;
6. expose CLI:
   `doc-based-coding opencode session claim|release|inspect`;
7. preserve authority split: no provider execution, no server lifecycle
   ownership, no scheduler/delivery mutation, no raw transcript, no secret
   persistence, no Local Work Trajectory mutation.

## Non-Goals

This gate does not:

1. create OpenCode sessions by running OpenCode;
2. start, stop, or supervise `opencode serve`;
3. automatically choose sessions for delivery execution;
4. implement a long-lived worker pool;
5. call OpenCode's HTTP API directly;
6. mutate scheduler or delivery state;
7. rename historical provider-parametric `CodexDelivery...` types.

## Implementation

Completed the durable session ledger slice:

1. added `src/runtime/orchestration/opencode_session_ledger.py`;
2. added durable schema `opencode-session-ledger.v1`;
3. added runtime helpers:
   `claim_opencode_session_binding()`,
   `release_opencode_session_binding()`,
   `inspect_opencode_session_bindings()`,
   `read_opencode_session_ledger()`, and
   `write_opencode_session_ledger()`;
4. added CLI:
   `doc-based-coding opencode session claim`,
   `doc-based-coding opencode session release`, and
   `doc-based-coding opencode session inspect`;
5. default ledger path:
   `.codex/runtime/opencode-session-ledger.json`;
6. documented session binding guidance in
   `docs/opencode-host-provisioning-check-guide.md`.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_session_ledger.py src/runtime/orchestration/opencode_serve_lifecycle.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_session_ledger" -q
2 passed, 372 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_session" -q
3 passed, 145 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

This gate creates the receipt layer but does not consume it during delivery.
Remaining OpenCode work:

1. wire session binding lookup into OpenCode delivery config generation;
2. define expiry/recovery policy for stale session bindings;
3. optional host-owned serve start/stop receipt contract;
4. direct server adapter, only after session lifecycle semantics stabilize;
5. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
