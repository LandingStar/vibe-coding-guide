# Review - Scheduler Operator Workflow Dogfood Fixture

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-workflow-dogfood-fixture.md`

## Scope Reviewed

This slice added a controlled dogfood fixture for the Scheduler Operator
workflow.

Implemented:

1. `src/runtime/orchestration/scheduler_operator_fixture.py` creates a stable
   fake-runtime `scheduler_task_batch_submission` ExchangeArtifact candidate.
2. The fixture contains one dependency chain:
   - `dogfood:prepare`
   - `dogfood:verify`, depending on `dogfood:prepare`
3. `JsonArtifactVersionStore.put()` now supports explicit
   `replace_existing=True` while preserving duplicate rejection by default.
4. `doc-based-coding scheduler seed-dogfood-fixture` writes the fixture to the
   conventional local ExchangeArtifact store unless an explicit store path is
   provided.
5. The full CLI smoke now proves:
   `seed -> resources read -> admit -> inspect -> daemon-loop fake -> project -> host-evidence presentation`.

## Evidence

Automated validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "seed_scheduler_operator_dogfood_fixture"
2 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "seed_dogfood_fixture or scheduler_operator_workflow"
2 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_doc_loop_prompts.py -k "scheduler or exchange_artifact or host_evidence"
126 passed
```

The full workflow test verifies:

1. seeded ExchangeArtifact candidate discovery through
   `dbc://exchange-artifacts/bundle`;
2. explicit scheduler admission through `scheduler admit-exchange-artifact`;
3. bounded fake-runtime advancement through `scheduler daemon-loop`;
4. explicit scheduler-derived projection refresh through `scheduler project`;
5. Host Evidence readback through `dbc://host-evidence/presentation`;
6. no mutation of agent-owned Local Work Trajectory.

## Authority Boundary

The fixture is test/demo data injection only. It mutates the local
ExchangeArtifact store and does not admit tasks, run providers, refresh
projection, write Host Evidence, mark artifacts consumed, or mutate Local Work
Trajectory.

All downstream mutations remain explicit existing operator commands.

## Residual Risk

1. The fixture currently represents a single-lane two-task chain. It proves the
   operator workflow data path, not multi-lane scheduler projection readability.
2. This slice does not add a shared MCP/host workflow action. VS Code still calls
   existing CLI surfaces individually.
3. Live Qoder / real-provider execution remains intentionally outside this
   fixture.

## Follow-Up

The next useful slice is a contract-first MCP/host unified operator workflow
surface that packages inspect/admit/run/project/readback as one reusable host
workflow while keeping explicit mutation boundaries.
