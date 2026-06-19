# Review - Scheduler Operator Multi-Lane Dogfood Fixture

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-multilane-dogfood-fixture.md`

## Summary

Added a second deterministic Scheduler Operator dogfood fixture without
replacing the existing simple two-task fixture.

The new fixture produces one fake-runtime scheduler batch:

```text
dogfood:api-design
dogfood:data-schema
dogfood:client-integration
dogfood:integration-verify
```

It spans four lanes (`lane:api`, `lane:data`, `lane:client`, `lane:qa`) and
contains four cross-lane dependencies, including fan-in to client and QA.

## Changed Files

- `src/runtime/orchestration/scheduler_operator_fixture.py`
- `src/runtime/orchestration/__init__.py`
- `src/__main__.py`
- `tests/test_runtime_orchestration.py`
- `tests/test_cli.py`
- `tests/test_mcp_admission.py`
- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-multilane-dogfood-fixture.md`

## Operator Surface

- `seed_scheduler_operator_multilane_dogfood_fixture()` writes the candidate to
  the local ExchangeArtifact store.
- `doc-based-coding scheduler seed-dogfood-fixture --fixture multilane` exposes
  the fixture through the existing CLI seed command.
- `--fixture simple` remains the default behavior.
- `schedulerOperatorWorkflow` can admit, run, project, and read evidence for the
  new fixture.

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_operator_workflow"
5 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "multilane_dogfood_fixture or scheduler_operator_workflow or seed_dogfood_fixture_help"
5 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_operator_workflow"
1 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_doc_loop_prompts.py tests/test_mcp_admission.py -k "scheduler or exchange_artifact or host_evidence or operator_workflow"
137 passed
```

## Boundary Checks

- Existing simple dogfood fixture remains unchanged and default.
- Fixture seed mutates only ExchangeArtifact store.
- Workflow mutation remains opt-in through `admit`, `runLoop`, and
  `refreshProjection`.
- No live Qoder or real provider execution was added.
- No background daemon lifecycle was added.
- No ExchangeArtifact consumed marking was added.
- No scheduler/admission/evidence schema was changed.
- No agent-owned Local Work Trajectory mutation occurs from scheduler workflow
  code.
- No VS Code UI binding changed in this slice.

## Residual Risk

The richer fixture is still fake-runtime-only. It validates topology and
workflow plumbing, not real-provider behavior, runtime permission review, or UI
layout readability under a live host.
