# Planning Gate - Supervisor Agent Home Session Binding

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/supervisor-dogfood-workflow-followup-direction-analysis.md`
recommends binding agent home, temporary scratch, and context-session facts to
the supervisor run identity before adding Host UX or durable supervisor evidence.

## Problem

`Supervisor Dogfood Workflow` now proves this deterministic fake-runtime
sequence:

```text
seed fixture -> exact admission -> lifecycle start -> supervisor step -> final readback
```

The workflow result preserves stable host/operator identity:

```text
supervisor_id / session_id / run_id / host_id / requested_by
```

Agent-private storage products already exist in
`src/runtime/orchestration/agent_storage.py`, but they are not yet connected to
supervisor runs. Without that binding, later multi-agent work has no compact,
auditable product that says which supervisor run owns which context session,
which temporary scratch spaces are in scope, and which persistent home
registration request should be reviewed.

## Scope

### Slice 1 - Core Binding Product

Add a runtime product that binds one supervisor run to:

1. one agent id;
2. one context-session id;
3. scheduler task ids and task context ids observed in scheduler readback;
4. runtime session ids recorded by scheduler run records;
5. one `AgentHomeRegistration` request;
6. zero or more `AgentScratchSpace` records derived from scheduler tasks.

The product must be JSON-readable and must include explicit authority facts.

### Slice 2 - Workflow Readback Helper

Add a deterministic helper for supervisor dogfood workflow results that:

1. reads the scheduler snapshot already produced by the workflow;
2. derives the binding product from the workflow request identity and scheduler
   readback;
3. does not rerun the scheduler workflow;
4. does not create directories, write storage manifests, or clean scratch.

### Slice 3 - Focused Tests

Add focused tests for:

1. identity mapping from supervisor workflow result to binding product;
2. task/context/runtime-session readback derivation;
3. home registration request and scratch-space products;
4. explicit non-goals in authority facts;
5. validation for missing supervisor identity.

## Non-Goals

This gate does not:

1. Add CLI, MCP, or Host UX surface.
2. Run live Qoder or any real provider.
3. Create agent home directories.
4. Create scratch directories.
5. Write scratch manifests.
6. Archive, promote, delete, or clean scratch content.
7. Decide persistent home approval.
8. Refresh scheduler projection.
9. Mutate Local Work Trajectory from scheduler/runtime/workflow code.
10. Change supervisor, harness, lifecycle, scheduler, or storage governance
    semantics.

## Acceptance Criteria

The gate may close when:

1. the binding product can be built from a deterministic fake-runtime supervisor
   dogfood workflow result;
2. the binding product reports supervisor identity, context-session identity,
   scheduler task/context ids, runtime session ids, home registration request,
   and scratch-space facts;
3. authority facts explicitly preserve no directory creation, no cleanup, no
   projection refresh, and no Local Work Trajectory mutation;
4. focused tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. Core runtime product:
   - `src.runtime.orchestration.supervisor_storage_binding`
   - `SupervisorAgentStorageBindingRequest`
   - `SupervisorAgentStorageBinding`
   - `build_supervisor_agent_storage_binding()`
2. Workflow readback helper:
   - `tools.progress_graph.build_supervisor_dogfood_storage_binding()`
3. Package exports from:
   - `src.runtime.orchestration`
   - `tools.progress_graph`
4. Focused tests in:
   - `tests/test_runtime_orchestration.py`
5. Design record update:
   - `design_docs/agent-home-and-scratch-space-design-record.md`

The binding product reads scheduler snapshot facts after a completed supervisor
dogfood workflow. It maps supervisor identity to one context-session id, task /
context / lane ids, runtime session ids, one requested `AgentHomeRegistration`,
and task-derived `AgentScratchSpace` facts.

The implementation remains product/readback-only. It does not create agent home
directories, create scratch directories, write scratch manifests, approve
persistent home registration, execute cleanup, refresh scheduler projection, or
mutate Local Work Trajectory from scheduler/runtime/workflow code.

## Validation

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding.py src/runtime/orchestration/__init__.py tools/progress_graph/scheduler_supervisor_dogfood_workflow.py tools/progress_graph/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
2 passed, 251 deselected
```

Wider adjacent validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
4 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "agent_home_registration or scratch_manifest or cleanup_receipt or scheduler_supervisor_dogfood_workflow or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
7 passed, 246 deselected
```

## Review Evidence

- `review/supervisor-agent-home-session-binding-2026-06-21.md`
