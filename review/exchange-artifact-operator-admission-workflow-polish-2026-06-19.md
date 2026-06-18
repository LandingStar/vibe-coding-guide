# Review - ExchangeArtifact Operator Admission Workflow Polish

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-exchange-artifact-operator-admission-workflow-polish.md`

## Scope Reviewed

This slice polished the CLI/operator workflow around exact-version
ExchangeArtifact scheduler admission.

Implemented:

1. `doc-based-coding scheduler inspect-state`
2. `doc-based-coding scheduler project`
3. Scheduler smoke prompt guidance for:
   `resources read -> admit-exchange-artifact -> inspect-state -> project`
4. Focused tests for help, workflow success, missing required paths, missing
   snapshot failure, prompt guidance, and existing runtime/MCP boundaries.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k scheduler
1 passed, 17 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
267 passed
```

## Behavioral Notes

`inspect-state` is read-only. It reads scheduler snapshot and optional event
logs, then reports task/dependency/run/merge counts, state buckets, IDs, and
event-log clues. It does not write scheduler state, exchange artifacts,
projection artifacts, or Local Work Trajectory.

`project` is explicit projection refresh. It writes only the scheduler-derived
trajectory artifact, defaulting to
`.codex/progress-graph/scheduler-work-trajectory.json`. It does not run
providers, mutate scheduler state, mark exchange artifacts consumed, or mutate
`.codex/progress-graph/local-work-trajectory.json`.

The temp-project workflow test proves:

1. A stored batch submission artifact can be admitted from CLI.
2. Readback sees two proposed tasks, one dependency, and two submission events.
3. Projection writes the scheduler-derived trajectory artifact.
4. No agent-owned Local Work Trajectory artifact is created by the operator
   workflow.

## Explicit Non-Goals Preserved

This slice did not add:

1. Stored-artifact MCP admission/write tool.
2. Scheduler daemon or durable queue.
3. UI binding.
4. Provider execution.
5. Exchange artifact consumed ledger or lifecycle marking.
6. Global default scheduler snapshot/event-log policy.

## Follow-Up

The next implementation candidate remains separate from this slice. The
strongest immediate candidates are:

1. Stored-artifact MCP Admission Tool, after deciding the review/permission
   story for agent-callable scheduler mutation.
2. Exchange Artifact Lifecycle Ledger / Consumed Marking, if repeated operator
   admission needs duplicate-consumption controls.
3. Scheduler Daemon / Durable Queue, once provider/sandbox policy is sharper.
4. Host Evidence / Scheduler Admission UI Binding, once the UI branch is the
   active workstream again.
