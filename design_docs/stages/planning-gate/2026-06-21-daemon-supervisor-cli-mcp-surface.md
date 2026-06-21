# Planning Gate - Daemon Supervisor CLI/MCP Surface

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-managed-daemon-supervisor-contract-followup-direction-analysis.md`
recommends exposing the runtime-only host-managed daemon supervisor step through
operator invocation surfaces.

## Problem

The runtime now has:

```text
SchedulerDaemonSupervisorRequest
SchedulerDaemonSupervisorStatus
SchedulerDaemonSupervisorResult
run_scheduler_daemon_supervisor_step()
```

Codex and operator workflows can call the policy-controlled bounded harness
through CLI/MCP, but cannot yet call the supervisor layer that adds
host/session/run identity, cancellation-source metadata, and lifecycle status
readback.

This slice should answer:

```text
Can the project expose the daemon supervisor step through CLI/MCP without
changing runtime semantics or adding Host UX/background services?
```

## Scope

### Slice 1 - CLI Surface

Add a CLI subcommand over `run_scheduler_daemon_supervisor_step()`.

Required behavior:

1. require explicit `--supervisor-id` and `--control-path`;
2. keep `--runtime-provider fake` only;
3. accept supervisor metadata:
   - `--session-id`
   - `--run-id`
   - `--host-id`
   - `--requested-by`
   - `--status-readback-at`
   - `--cancellation-source`
   - `--cancellation-reason`
4. accept the same bounded harness and policy controls as lifecycle harness;
5. return supervisor result JSON unchanged.

### Slice 2 - MCP Surface

Register one MCP tool:

```text
schedulerDaemonSupervisorStep
```

The tool should map explicit camelCase fields to
`SchedulerDaemonSupervisorRequest` and return the supervisor result JSON.

### Slice 3 - Focused Tests

Add focused tests covering:

1. CLI smoke executes supervisor over fake runtime and returns status readback;
2. CLI rejects non-fake runtime provider;
3. MCP tool registration includes supervisor fields;
4. MCP cancelled/deadline preflight does not read or mutate control files;
5. MCP executed supervisor returns `harness_policy_result`.

## Non-Goals

This gate does not:

1. Change `run_scheduler_daemon_supervisor_step()` semantics.
2. Change harness or policy semantics.
3. Add Host UX binding.
4. Run live Qoder or any real provider.
5. Start an OS service, watcher, timer, or unbounded daemon.
6. Refresh scheduler projection automatically.
7. Run or hide sandbox cleanup.
8. Mutate ExchangeArtifact lifecycle or admission ledger state.
9. Mutate Local Work Trajectory from scheduler runtime, CLI, or MCP code.
10. Bind agent home, scratch retention, or context-session storage lifecycle.

## Acceptance Criteria

The gate may close when:

1. CLI can invoke one daemon supervisor step and returns supervisor result JSON.
2. MCP exposes `schedulerDaemonSupervisorStep`.
3. CLI/MCP stay fake-runtime-only and bounded.
4. Preflight and executed paths are covered by focused tests.
5. Review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. CLI surface:
   - `doc-based-coding scheduler lifecycle supervisor-step`
2. MCP/GovernanceTools surface:
   - `GovernanceTools.scheduler_daemon_supervisor_step()`
   - MCP tool `schedulerDaemonSupervisorStep`
3. Shared mapping over:
   - `SchedulerDaemonSupervisorRequest`
   - `SchedulerDaemonHarnessRequest`
   - `SchedulerDaemonHarnessPolicy`
   - `run_scheduler_daemon_supervisor_step()`
4. Scheduler MCP prompt updates in current and bootstrap prompt surfaces.
5. `design_docs/tooling/MCP Tool Surface Audit.md` update.
6. Focused CLI, MCP, server routing, and prompt tests.

The new CLI/MCP surfaces preserve the runtime supervisor result JSON shape and
add only the normalized `runtime_provider` clue on MCP responses. They remain
fake-runtime-only, explicit-path, bounded, and side-effect constrained.

## Validation

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/scheduler_daemon_supervisor.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
5 passed, 38 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle or scheduler_daemon_supervisor"
5 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
13 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py
86 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_supervisor or scheduler_daemon_harness or scheduler_daemon_lifecycle"
19 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
43 passed
```

## Review Evidence

- `review/daemon-supervisor-cli-mcp-surface-2026-06-21.md`
- `design_docs/daemon-supervisor-cli-mcp-surface-followup-direction-analysis.md`
