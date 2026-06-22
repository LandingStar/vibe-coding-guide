# Review - Host UX Consumed ExchangeArtifact Operator Flow

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-22-host-ux-consumed-exchange-artifact-operator-flow.md`

## Scope Reviewed

This slice connected the ExchangeArtifact consumed lifecycle fact to Scheduler
Operator Host UX and the shared operator workflow.

Implemented:

1. `mark_consumed_on_success` on `SchedulerOperatorWorkflowRequest`;
2. CLI `scheduler operator-workflow --mark-consumed-on-success`;
3. MCP `schedulerOperatorWorkflow.markConsumedOnSuccess`;
4. Host UX action contract field `markConsumedOnSuccess`;
5. `SchedulerOperatorExchangeCandidate.lifecycleState`;
6. candidate rendering for lifecycle state, explicit `Admit + Consume`, and
   disabled `Consumed` historical records;
7. focused runtime, CLI, MCP, extension contract, and HTML rendering tests;
8. screenshot-style browser validation.

## Evidence

Syntax validation:

```text
.\.venv\Scripts\python.exe -m py_compile tools/progress_graph/scheduler_operator_workflow.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
passed
```

Focused backend validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "operator_workflow_can_mark_consumed_on_success or scheduler_operator_workflow_inspect_binding_refs_then_admit"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "operator_workflow_help_describes_opt_in_mutation or operator_workflow_cli_can_mark_consumed_on_success"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_operator_workflow"
4 passed
```

Focused extension validation:

```text
npm run build
passed

node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphSchedulerOperatorLifecycle.test.js
44 passed
```

Adjacent backend validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_workflow or exchange_artifact_store_inspection or admit_exchange_artifact_version"
22 passed, 256 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "operator_workflow or admit_exchange_artifact or exchange_artifacts_bundle"
13 passed, 41 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_operator_workflow or admit_exchange_artifact or exchange_artifacts_bundle"
8 passed, 11 deselected
```

Screenshot validation:

```text
output/playwright/host-ux-consumed-exchange-artifact-operator-flow/consumed-exchange-artifact-operator-flow.png
Width=1400 Height=2865 sampled_unique_colors=9
Browser text check included "Admit + Consume", "Consumed", and "lifecycle=consumed".
DOM check found one data-pg-mark-consumed-on-success="true" action and one disabled Consumed button.
```

Change analysis:

```text
analyze_changes
impact.direct=[]
impact.transitive=[]
coupling.alerts=[coupling-mcp-tools-registration]
```

The MCP coupling alert is expected for MCP tool surface changes and is
satisfied by `src/mcp/server.py` schema/routing updates plus MCP route tests.

## Behavioral Notes

Consumed ExchangeArtifact versions remain visible as audit history. The UI does
not hide consumed candidates.

Regular `Admit` continues to avoid lifecycle mutation. Only the explicit
`Admit + Consume` control sends `markConsumedOnSuccess=true`, and the backend
operator workflow marks the exact stored version consumed only after successful
admission.

Consumed candidates render a disabled `Consumed` button and expose no mutating
candidate action.

## Explicit Non-Goals Preserved

This slice did not:

1. hide or filter consumed candidates;
2. make regular Admit consume by default;
3. add a standalone consume-only Host UX action;
4. mutate input binding artifacts consumed;
5. change scheduler runtime execution semantics;
6. change ExchangeArtifact store schema;
7. add consumed filtering controls;
8. mutate agent-owned Local Work Trajectory from Host UX.

## Follow-Up

The operator lifecycle surface is now complete enough for dogfood. The next
useful backend direction is to continue the scheduler/operator orchestration
line where durable products can move from Host UX affordances into bounded
agent runtime execution and reviewable evidence.
