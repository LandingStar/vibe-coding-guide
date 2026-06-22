# Review - Supervisor Storage Binding Reference Inspection Surface

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-reference-inspection-surface.md`

## Scope Reviewed

This slice exposed supervisor storage binding artifact reference readiness as a
read-only inspection product before scheduler admission.

Implemented:

1. `BindingArtifactReferenceTaskInspection`;
2. `BindingArtifactReferenceInspection`;
3. `inspect_supervisor_storage_binding_artifact_refs_for_submission()`;
4. runtime exports from `src.runtime.orchestration`;
5. CLI `doc-based-coding scheduler inspect-binding-refs`;
6. MCP tool `schedulerBindingReferenceInspect`;
7. scheduler MCP prompt guidance;
8. MCP tool surface audit entry;
9. focused runtime, CLI, MCP, and prompt tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "binding_reference_inspection or supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version or scheduler_task_submission"
20 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "inspect_binding_refs or admit or operator_workflow or seed_dogfood_fixture"
13 passed, 35 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "binding_reference_inspect or admit or scheduler_operator_workflow"
4 passed, 10 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "admitExchangeArtifact or schedulerSubmitTasks or scheduler_projection"
13 passed, 73 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
passed

git diff --check -- src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py .codex/prompts/doc-loop/07-scheduler-mcp-smoke.md design_docs/tooling/MCP Tool Surface Audit.md design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-reference-inspection-surface.md review/supervisor-storage-binding-reference-inspection-surface-2026-06-22.md
passed
```

Change analysis:

```text
analyze_changes(...)
impact.direct = []
impact.transitive = []
coupling.alerts = [
  "coupling-mcp-tools-registration"
]
```

The coupling alert is expected for any new MCP tool method in
`src/mcp/tools.py`. This slice updated `src/mcp/server.py` tool schema and
`call_tool` routing, and `tests/test_mcp_admission.py` now verifies server list
and route behavior for `schedulerBindingReferenceInspect`.

## Behavioral Notes

`inspect_supervisor_storage_binding_artifact_refs_for_submission()` reads one
exact artifact id/version from `JsonArtifactVersionStore`, accepts only
`scheduler_task_submission` and `scheduler_task_batch_submission`, and delegates
per-task validation to `validate_supervisor_storage_binding_artifact_refs()`.

The returned product includes:

1. source artifact id/version;
2. submission product type;
3. task count;
4. per-task binding refs and checked refs;
5. readable per-task and aggregate errors;
6. `ok`;
7. authority split showing no scheduler/store/ledger/provider/evidence/
   projection/trajectory mutation.

The CLI surface exits non-zero when inspection errors exist, while still
printing the structured JSON product. The MCP tool returns the same product
without throwing for validation failures.

## Explicit Non-Goals Preserved

This slice did not:

1. admit scheduler submissions;
2. submit scheduler tasks;
3. write scheduler snapshots or event logs;
4. mutate ExchangeArtifact stores;
5. mutate admission ledgers;
6. mark artifacts consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home directories;
9. create scratch directories;
10. write scratch manifests;
11. approve persistent home registration;
12. archive, promote, delete, or clean scratch content;
13. run fake or real providers;
14. refresh scheduler projection;
15. add Host UX controls;
16. mutate Local Work Trajectory from runtime, CLI, or MCP code.

## Follow-Up

The next narrow backend-facing candidate is to record binding-reference
inspection or preflight summaries in operator workflow/admission readback
products only where that summary can remain read-only until an explicit
admission action is requested. Host UX visibility should consume the backend
inspection product rather than reimplement validation.
