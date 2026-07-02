# Planning Gate - OpenCode Serve Readiness Contract

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now matches Codex for the current host-owned one-shot worker runtime
surface. The remaining OpenCode-specific gap is server/session lifecycle:
OpenCode can run a headless `opencode serve` process and `opencode run` can
attach to it, but dbc did not yet have a safe operator surface for inspecting
that attach target.

This gate starts the server/session work without making the scheduler own the
OpenCode server process.

## Scope

Add a narrow OpenCode serve readiness contract:

1. add a credential-safe runtime helper for OpenCode serve readiness;
2. expose CLI:
   `doc-based-coding opencode serve-readiness`;
3. inspect OpenCode CLI availability and a configurable attach target health
   endpoint;
4. default to `127.0.0.1:4096` and `/global/health`;
5. support `--require-healthy` for strict host provisioning checks;
6. support basic-auth credential lookup through named environment variables
   without printing secret values;
7. report an explicit authority split showing that dbc did not start, stop,
   restart, supervise, run providers, mutate scheduler state, or mutate Local
   Work Trajectory.

## Non-Goals

This gate does not:

1. start or stop `opencode serve`;
2. manage a durable OpenCode server process;
3. implement a long-lived OpenCode worker/session pool;
4. call OpenCode's task HTTP API directly;
5. expose real OpenCode provider execution through MCP;
6. change scheduler/delivery state;
7. rename historical provider-parametric `CodexDelivery...` types.

## Implementation

Completed the serve readiness contract:

1. added `src/runtime/orchestration/opencode_serve_lifecycle.py`;
2. exported `OpenCodeServeReadinessRequest`,
   `OpenCodeServeReadinessReport`, and
   `inspect_opencode_serve_readiness()`;
3. added CLI:
   `doc-based-coding opencode serve-readiness`;
4. the CLI accepts:
   `--executable`, `--hostname`, `--port`, `--attach-url`, `--health-path`,
   `--health-timeout-seconds`, `--require-healthy`,
   `--username-env-var`, and `--password-env-var`;
5. readiness reports include attach/health URLs, health status, auth
   configured flag, credential env var names, and mutation authority split;
6. `docs/opencode-host-provisioning-check-guide.md` documents the host-owned
   boundary.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_serve_lifecycle.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_serve_readiness" -q
3 passed, 369 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_serve_readiness" -q
3 passed, 142 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

This gate establishes safe attach-target inspection. Remaining OpenCode work:

1. durable long-lived OpenCode server/session lifecycle policy;
2. optional host-owned serve start/stop receipt contract, if desired;
3. direct HTTP/server adapter, only after the lifecycle contract is accepted;
4. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
