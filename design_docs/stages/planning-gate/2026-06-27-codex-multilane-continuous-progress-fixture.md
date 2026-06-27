# Planning Gate - Codex Multi-Lane Continuous Progress Fixture

> Date: 2026-06-27
> Status: COMPLETED

## Trigger

C1 through C5 now make Codex CLI usable for single-provider bounded delivery
with durable success, permission/review outcomes, retry after interruption,
and sandbox patch-review boundaries.

The stable worker runtime target still requires proof that one host/operator
command can make progress across at least two lane-distinct worker contexts
without conflating context scope or claiming true process parallelism.

## Scope

Add a repeatable multi-lane Codex delivery fixture over the existing bounded
supervisor loop:

1. seed a scheduler snapshot with at least two independent ready Codex tasks in
   distinct lanes;
2. include at least one dependent Codex follow-up task that remains waiting
   until one source lane completes;
3. run the existing bounded loop over the seeded fixture through one command or
   helper;
4. expose lane/task state readback showing which lane tasks completed and
   which dependent task remained waiting or advanced;
5. keep execution serial inside the loop while preserving scheduling
   parallelism metadata.

## Non-Goals

This gate does not:

1. start simultaneous Codex CLI processes;
2. introduce distributed leases or worker daemons;
3. mutate agent-owned Local Work Trajectory from runtime code;
4. create a new scheduler model;
5. change sandbox patch review behavior from C5.

## Acceptance Criteria

This gate may close when:

1. the bounded Codex supervisor loop can initialize a multi-lane fixture with
   at least three tasks and at least two lane-distinct Codex workers;
2. at least two independent Codex tasks from different lanes can complete over
   bounded loop ticks;
3. at least one dependency edge is visible and recovered scheduler state shows
   the dependent task transitions only after its source task completes;
4. loop JSON readback includes target task states and task state counts for the
   multi-lane fixture;
5. the fixture remains fake-client testable without requiring live Codex CLI;
6. runtime code does not mutate Local Work Trajectory and does not claim true
   process-level parallelism.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "bounded_codex_delivery_supervisor_loop and multilane" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

## Residual Risk After Close

This fixture will prove lane-aware continuous progress metadata and bounded
serial execution. It will not prove true process-level parallelism,
operator-friendly routine status readback, or live multi-Codex execution under
real network instability.

## Implemented Surface

Runtime:

- `CodexDeliveryE2ESmokeRequest.fixture`
- `parallel_task_id`
- `parallel_agent_id`
- `parallel_lane_id`

Behavior:

- Default fixture remains `simple`.
- `fixture="multilane"` seeds:
  - one ready Codex worker in the primary lane;
  - one independent ready Codex worker in a second lane;
  - one follow-up Codex worker waiting on the primary lane task;
  - one non-Codex waiting control task.
- The existing bounded supervisor loop can complete both independent lane
  workers and then the dependent follow-up over bounded ticks.
- Loop JSON readback reports `target_task_states`, `task_state_counts`, and
  fixture metadata for the multi-lane fixture.
- Execution remains serial inside the bounded loop; this gate preserves
  scheduling parallelism metadata but does not claim true process-level
  parallelism.

CLI:

- `doc-based-coding scheduler codex-delivery-e2e-smoke --fixture simple|multilane`
- `doc-based-coding scheduler codex-delivery-supervisor-loop --fixture simple|multilane`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "bounded_codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "bounded_codex_delivery_supervisor_loop or codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

Observed results:

```text
4 passed, 333 deselected
2 passed, 100 deselected
14 passed, 323 deselected
doc-loop validation passed
```

One initial CLI focused run passed but printed a post-run Python access
violation from the interpreter process. The immediate rerun of the same CLI
selection passed cleanly and the runtime selection also passed.
