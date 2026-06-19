# Planning Gate - Scheduler Daemon Lifecycle CLI/MCP Surface

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/scheduler-daemon-lifecycle-cli-mcp-surface-direction-analysis.md`
recommends exposing the completed scheduler daemon lifecycle contract through a
small CLI/MCP read-write surface before attempting a real background daemon,
Host UX binding, or real provider loop.

## Problem

The runtime now has:

```text
SchedulerDaemonLifecycleControl
SchedulerDaemonLifecycleRequest
SchedulerDaemonLifecycleRunOnceRequest
apply_scheduler_daemon_lifecycle_action()
inspect_scheduler_daemon_lifecycle_control()
run_scheduler_daemon_lifecycle_once()
```

But local operators and Codex/MCP callers cannot yet exercise those controls
without importing Python helpers directly.

This slice should answer:

```text
Can the project expose lifecycle control through explicit CLI and MCP surfaces
while preserving the existing scheduler authority boundary?
```

## Scope

### Slice 1 - CLI Lifecycle Subcommands

Add a scheduler lifecycle namespace:

```text
doc-based-coding scheduler lifecycle inspect
doc-based-coding scheduler lifecycle start
doc-based-coding scheduler lifecycle heartbeat
doc-based-coding scheduler lifecycle pause
doc-based-coding scheduler lifecycle resume
doc-based-coding scheduler lifecycle cancel
doc-based-coding scheduler lifecycle shutdown
doc-based-coding scheduler lifecycle run-once
```

The CLI should:

1. require `--control-path` for all lifecycle operations;
2. require `--snapshot-path`, `--event-log-path`, and `--daemon-id` for
   `start`;
3. keep `run-once` fake-runtime only in this slice;
4. return JSON payloads from the runtime helpers;
5. report missing control files clearly for readback / run-once;
6. avoid projection refresh unless a later explicit workflow composes it.

### Slice 2 - MCP Lifecycle Tools

Add two MCP tools:

```text
schedulerLifecycleControl
schedulerLifecycleRunOnce
```

`schedulerLifecycleControl` maps only to deterministic lifecycle control file
actions and inspection. `schedulerLifecycleRunOnce` maps to
`run_scheduler_daemon_lifecycle_once()` and stays fake-runtime only.

Inputs should use MCP-facing camelCase fields and resolve relative paths under
the MCP project root.

### Slice 3 - Prompt / Maintenance Guidance

Update scheduler MCP smoke prompt guidance so agents know:

1. lifecycle control is scheduler-owned state, not agent-owned Local Work
   Trajectory;
2. mutating lifecycle actions write only the lifecycle control file;
3. `run-once` may mutate scheduler snapshot/event log only through the bounded
   scheduler loop;
4. projection refresh remains explicit and separate.

### Slice 4 - Focused Tests

Add focused tests for:

1. CLI inspect/start/pause/resume/cancel/shutdown;
2. CLI run-once running fake-runtime loop and cancelled skip;
3. MCP lifecycle control action routing;
4. MCP lifecycle run-once routing;
5. MCP server tool exposure and schema fields;
6. prompt guidance mentions lifecycle tools and preserved boundaries.

## Non-Goals

This gate does not:

1. Start a persistent background daemon process.
2. Add sleeps, polling, filesystem watch, OS service registration, or process
   supervision.
3. Run real Qoder or any other external provider through generic MCP.
4. Add Host UX binding.
5. Refresh scheduler projection automatically from lifecycle control actions.
6. Mutate ExchangeArtifact lifecycle or admission ledger state.
7. Mutate agent-owned Local Work Trajectory from scheduler code, CLI scheduler
   tools, or MCP scheduler tools.
8. Change scheduler task admission, event-log compaction, or projection
   semantics.

## Acceptance Criteria

The gate may close when:

1. CLI lifecycle subcommands exist and preserve authority split.
2. MCP lifecycle tools exist, are listed by the MCP server, and route to runtime
   helpers.
3. `run-once` remains fake-runtime only and lifecycle-gated.
4. Missing path / missing control errors are readable.
5. Focused CLI, MCP, runtime, and prompt tests pass.
6. Review/status docs record validation and preserved non-goals.

## Implementation Summary

Completed on 2026-06-20.

This slice exposed the scheduler daemon lifecycle control contract through
thin CLI and MCP surfaces.

Implemented:

1. CLI scheduler lifecycle namespace:
   - `doc-based-coding scheduler lifecycle inspect`
   - `doc-based-coding scheduler lifecycle start`
   - `doc-based-coding scheduler lifecycle heartbeat`
   - `doc-based-coding scheduler lifecycle pause`
   - `doc-based-coding scheduler lifecycle resume`
   - `doc-based-coding scheduler lifecycle cancel`
   - `doc-based-coding scheduler lifecycle shutdown`
   - `doc-based-coding scheduler lifecycle run-once`
2. MCP tools:
   - `schedulerLifecycleControl`
   - `schedulerLifecycleRunOnce`
3. MCP server list/call routing and schema descriptions.
4. Scheduler MCP smoke prompt guidance in repo-local and bootstrap copies.
5. Focused CLI and MCP tests over lifecycle transitions, run-once, server
   exposure, and fake-runtime guard behavior.

The new surface preserves explicit path inputs. Lifecycle control actions write
only the lifecycle control file. `run-once` remains fake-runtime only and may
mutate scheduler snapshot/event-log state only through
`run_scheduler_daemon_lifecycle_once()`. Projection refresh remains separate.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed
```

Wider regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
34 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
191 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
20 passed
```

## Non-Goals Preserved

This slice did not add:

1. A persistent background daemon process.
2. Sleep / polling / filesystem watch / OS service registration / process
   supervision.
3. Real Qoder or external provider execution through generic MCP.
4. Host UX binding.
5. Automatic scheduler projection refresh from lifecycle actions.
6. ExchangeArtifact lifecycle or admission ledger mutation.
7. Scheduler-code / CLI / MCP mutation of agent-owned Local Work Trajectory.
8. Scheduler task admission, event-log compaction, or projection semantic
   changes.
