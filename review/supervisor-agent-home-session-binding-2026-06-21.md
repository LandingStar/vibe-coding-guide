# Review - Supervisor Agent Home Session Binding

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-agent-home-session-binding.md`

## Scope Reviewed

This slice added a readback-only binding product between a host-managed
supervisor run and agent-private storage/context products.

Implemented:

1. Core runtime product:
   - `src.runtime.orchestration.supervisor_storage_binding`
   - `SupervisorAgentStorageBindingRequest`
   - `SupervisorAgentStorageBinding`
   - `build_supervisor_agent_storage_binding()`
2. Workflow bridge:
   - `tools.progress_graph.build_supervisor_dogfood_storage_binding()`
3. Exports from `src.runtime.orchestration` and `tools.progress_graph`.
4. Focused runtime tests.
5. Agent home / scratch design record update.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding.py src/runtime/orchestration/__init__.py tools/progress_graph/scheduler_supervisor_dogfood_workflow.py tools/progress_graph/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
2 passed, 251 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_supervisor_dogfood_workflow or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
4 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "agent_home_registration or scratch_manifest or cleanup_receipt or scheduler_supervisor_dogfood_workflow or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding"
7 passed, 246 deselected
```

## Behavioral Notes

The binding product maps:

1. `supervisor_id`, `session_id`, `run_id`, `host_id`, and `requested_by`;
2. one `context_session_id`;
3. scheduler task ids, context ids, and lane ids from scheduler state;
4. runtime session ids from scheduler run records;
5. one requested `AgentHomeRegistration`;
6. task-derived `AgentScratchSpace` records.

The helper over supervisor dogfood workflow results reads the already-produced
scheduler snapshot. It does not rerun the workflow or mutate scheduler state.

The fake runtime currently reuses runtime session/run ids across bounded daemon
ticks in some dogfood paths. The binding product intentionally preserves the
scheduler run-record facts instead of inventing globally unique runtime ids.

## Explicit Non-Goals Preserved

This slice did not:

1. add CLI, MCP, or Host UX surface;
2. run live Qoder or any real provider;
3. create agent home directories;
4. create scratch directories;
5. write scratch manifests;
6. approve persistent home registration;
7. archive, promote, delete, or clean scratch content;
8. refresh scheduler projection;
9. mutate Local Work Trajectory from scheduler/runtime/workflow code;
10. change supervisor, harness, lifecycle, scheduler, or storage governance
    semantics.

## Follow-Up

The next narrow backend slice should make the binding product durable as an
explicit evidence artifact or exchange artifact. That should happen before Host
UX binding, because UI needs a stable readback/product surface rather than
deriving storage facts from raw workflow internals.
