# Planning Gate - Supervisor Dogfood Workflow

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/daemon-supervisor-cli-mcp-surface-followup-direction-analysis.md`
recommends proving the daemon supervisor invocation sequence before binding
agent home, storage lifecycle, or Host UX.

## Problem

The scheduler backend now exposes:

1. deterministic dogfood ExchangeArtifact fixtures;
2. exact scheduler admission;
3. lifecycle control start/readback;
4. policy-controlled bounded harness;
5. host-managed daemon supervisor step;
6. CLI and MCP invocation surfaces for one supervisor step.

Those pieces are tested individually, but the project does not yet have one
repeatable workflow that proves the intended operator sequence:

```text
seed scheduler work -> admit -> start lifecycle control -> supervisor step -> read back status
```

This slice should answer:

```text
Can a Codex/operator host run a deterministic fake-runtime supervisor dogfood
workflow and inspect the resulting scheduler/supervisor facts without adding
UI, real providers, projection refresh, cleanup, or scheduler-owned trajectory
mutation?
```

## Scope

### Slice 1 - Shared Workflow Helper

Add a host/operator workflow helper outside core scheduler runtime, next to
the existing progress-graph workflow helpers.

Required behavior:

1. seed an existing deterministic scheduler dogfood fixture;
2. admit the exact fixture version into scheduler snapshot/event-log state;
3. start lifecycle control explicitly;
4. invoke `run_scheduler_daemon_supervisor_step()`;
5. read back final lifecycle/scheduler facts;
6. return ordered step results and preserved authority split facts.

### Slice 2 - CLI Surface

Add one explicit CLI command:

```text
doc-based-coding scheduler supervisor-dogfood-workflow
```

The command should:

1. default to fake runtime;
2. accept explicit project-local paths for store, ledger, snapshot, event log,
   and lifecycle control;
3. accept fixture selection and supervisor identity metadata;
4. reject non-fake runtime provider.

### Slice 3 - MCP Surface

Register one MCP tool:

```text
schedulerSupervisorDogfoodWorkflow
```

The tool should map camelCase fields to the shared workflow helper and return
the workflow result JSON.

### Slice 4 - Focused Tests And Prompt Guidance

Add focused coverage for:

1. shared helper completes the simple fixture through supervisor readback;
2. CLI workflow smoke returns completed scheduler/supervisor facts;
3. CLI rejects non-fake runtime provider;
4. MCP tool registration/routing returns supervisor workflow result;
5. scheduler MCP prompt and tool audit document the new surface.

## Non-Goals

This gate does not:

1. Change scheduler daemon supervisor, harness, policy, or lifecycle semantics.
2. Run live Qoder or any real provider.
3. Add Host UX binding.
4. Start an OS service, watcher, timer, or unbounded daemon.
5. Refresh scheduler projection automatically.
6. Run or hide sandbox cleanup.
7. Mark ExchangeArtifact candidates consumed beyond explicit scheduler
   admission.
8. Mutate agent-owned Local Work Trajectory from scheduler runtime, CLI, MCP,
   or workflow code.
9. Bind agent home, scratch retention, or context-session storage lifecycle.

## Acceptance Criteria

The gate may close when:

1. shared helper can run seed -> admit -> lifecycle start -> supervisor step ->
   readback over fake runtime;
2. CLI/MCP expose the workflow and remain fake-runtime-only;
3. workflow result reports scheduler/supervisor facts and authority split;
4. focused tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. Shared workflow helper:
   - `tools.progress_graph.scheduler_supervisor_dogfood_workflow`
   - `SchedulerSupervisorDogfoodWorkflowRequest`
   - `SchedulerSupervisorDogfoodWorkflowResult`
   - `run_scheduler_supervisor_dogfood_workflow()`
2. CLI surface:
   - `doc-based-coding scheduler supervisor-dogfood-workflow`
3. MCP/GovernanceTools surface:
   - `GovernanceTools.scheduler_supervisor_dogfood_workflow()`
   - MCP tool `schedulerSupervisorDogfoodWorkflow`
4. Scheduler MCP prompt updates in current and bootstrap prompt surfaces.
5. `design_docs/tooling/MCP Tool Surface Audit.md` update.
6. Focused runtime workflow, CLI, MCP routing/schema, and prompt tests.

The workflow composes existing primitives rather than changing their semantics:
seed deterministic fixture, admit exact artifact/version, start lifecycle
control, run one fake-runtime supervisor step, and read final scheduler facts.
It does not refresh scheduler projection, run cleanup, start a service, or
mutate agent-owned Local Work Trajectory.

## Validation

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py tools/progress_graph/scheduler_supervisor_dogfood_workflow.py tools/progress_graph/__init__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow"
2 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "supervisor_dogfood_workflow"
2 passed, 43 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle or scheduler_supervisor or scheduler_daemon_supervisor"
5 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow or scheduler_daemon_supervisor or scheduler_daemon_harness or scheduler_daemon_lifecycle"
21 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
45 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
13 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py
86 passed
```

Coupling check:

```text
analyze_changes
impact: no direct/transitive baseline nodes reported
coupling: triggered coupling-mcp-tools-registration; satisfied by src/mcp/server.py list_tools and call_tool routing updates
```

## Review Evidence

- `review/supervisor-dogfood-workflow-2026-06-21.md`
