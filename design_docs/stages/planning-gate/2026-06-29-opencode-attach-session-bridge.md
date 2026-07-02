# Planning Gate - OpenCode Attach Session Bridge

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now matches the current Codex one-shot worker runtime chain for
provider adapter, guide-worker smoke, mixed-provider smoke, delivery-once,
bounded supervisor loop, live concurrent worker smoke, retry/audit,
lane-distinct concurrency, and review-only git-worktree patch proposal
publication.

The next small gap is that OpenCode has host-visible `run --attach`,
`--session`, `--continue`, and `--fork` flags that Codex does not model in the
same way. The repository already carries these options in the OpenCode CLI
client and CLI surfaces, but the behavior needs to be formalized so the
remaining `opencode serve` work is not confused with this narrower bridge.

## Scope

Close the attach/session bridge as a documented OpenCode parity slice:

1. keep OpenCode execution host-owned and process-client backed through
   `opencode run`;
2. pass `--attach URL`, `--session ID`, `--continue`, and `--fork` to
   OpenCode when explicitly configured;
3. expose the same OpenCode session flags on guide-worker, mixed-provider,
   delivery-once, bounded-loop, and live-concurrency smoke CLI surfaces;
4. reject invalid combinations:
   `--session-id` with `--continue-session`, and `--fork-session` without
   either `--session-id` or `--continue-session`;
5. record attach/session/fork facts in compact runtime result metadata without
   storing raw transcript or secret values;
6. document that the host owns any `opencode serve` process lifecycle and this
   gate does not implement an HTTP/server runtime adapter.

## Non-Goals

This gate does not:

1. start, stop, restart, or supervise `opencode serve`;
2. call OpenCode's HTTP API directly;
3. implement a long-lived worker pool or daemon;
4. persist raw OpenCode transcripts;
5. expose real OpenCode provider execution through MCP;
6. make OpenCode the scheduler, leader, Local Work Trajectory owner, or patch
   merge authority;
7. rename historical `CodexDelivery...` product types.

## Implementation

Completed the OpenCode attach/session bridge:

1. `OpenCodeCliClientConfig` carries `attach_url`, `session_id`,
   `continue_session`, and `fork_session`;
2. config validation rejects conflicting session selection and fork-without-
   base-session combinations;
3. `OpenCodeCliProcessClient._build_command()` maps these fields to:
   `opencode run --attach`, `--session`, `--continue`, and `--fork`;
4. `output_format="text"` maps to OpenCode CLI `--format default`, while
   `json` remains `json`;
5. result metadata includes `attached_to_server`, `attach_url`, `session_id`,
   `continue_session`, and `fork_session`;
6. CLI surfaces expose the bridge through:
   `doc-based-coding opencode guide-worker-smoke`,
   `doc-based-coding provider guide-worker-smoke`,
   `doc-based-coding scheduler opencode-delivery-supervisor-once`,
   `doc-based-coding scheduler opencode-delivery-supervisor-loop`, and
   `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`;
7. docs now describe the bridge as a host-owned attachment/session selector,
   not as dbc-owned `opencode serve` lifecycle management.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_cli_client.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_cli_process_client_can_attach_to_server_session or opencode_cli_process_client_validates_session_config or opencode_cli_process_client_prefers_task_runtime_workspace" -q
3 passed, 363 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_guide_worker_smoke_help or opencode_guide_worker_smoke_rejects_conflicting_session_options or provider_guide_worker_smoke_rejects_invalid_opencode_fork_session or scheduler_opencode_delivery_supervisor_help or scheduler_opencode_delivery_supervisor_rejects_conflicting_session_options or scheduler_opencode_delivery_supervisor_loop_help or scheduler_opencode_delivery_supervisor_loop_rejects_invalid_fork_session or live_opencode_concurrent_worker_smoke_help" -q
8 passed, 128 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now has basic Codex-level worker runtime parity plus an OpenCode-
specific attach/session CLI bridge. Remaining work is deliberately beyond this
bridge:

1. `opencode serve` / HTTP-server runtime adapter and server lifecycle
   contract;
2. durable long-lived worker session lifecycle policy, including session reuse,
   expiry, recovery, and compaction;
3. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
