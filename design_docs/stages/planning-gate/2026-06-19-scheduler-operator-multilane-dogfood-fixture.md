# Planning Gate: Scheduler Operator Multi-Lane Dogfood Fixture

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed `Scheduler Operator Unified Workflow Surface` gate produced a
shared host-neutral workflow:

- backend helper `run_scheduler_operator_workflow()`
- MCP `schedulerOperatorWorkflow`
- CLI `doc-based-coding scheduler operator-workflow`

The current dogfood fixture is intentionally small: one lane and two
fake-runtime tasks. That is enough for smoke testing, but too weak for
validating scheduler admission, projection, and evidence readback over a future
multi-agent-like topology.

## Scope

This gate adds a second deterministic dogfood fixture:

```text
api lane  -> client lane -> qa lane
data lane -> client lane -> qa lane
data lane -------------> qa lane
```

The fixture remains fake-runtime-only and is still just an ExchangeArtifact
admission candidate until an operator explicitly runs admission.

## Acceptance

1. A deterministic fake-runtime multi-lane scheduler task batch fixture exists.
2. The existing simple dogfood fixture remains unchanged and remains the CLI
   default.
3. The new fixture can be seeded through the CLI without admitting tasks.
4. The new fixture can be admitted, run through bounded fake scheduler loop,
   projected, and read back through `schedulerOperatorWorkflow`.
5. MCP can route `schedulerOperatorWorkflow` over the new fixture.
6. Authority split remains explicit:
   - fixture seed mutates only ExchangeArtifact store;
   - workflow mutates only the explicitly requested scheduler/admission/evidence
     projection surfaces;
   - no provider other than fake runs;
   - Local Work Trajectory is not mutated by scheduler workflow code.

## Non-Goals

- Do not replace the simple two-task fixture.
- Do not bind or redesign UI in this gate.
- Do not run live Qoder or any real provider.
- Do not start a background scheduler daemon.
- Do not mark ExchangeArtifact versions consumed.
- Do not mutate agent-owned Local Work Trajectory from scheduler workflow code.

## Validation Plan

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_operator_workflow"

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "multilane_dogfood_fixture or scheduler_operator_workflow"

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_operator_workflow"
```

Before close, run the broader scheduler/operator focused regression used by the
previous gate.
