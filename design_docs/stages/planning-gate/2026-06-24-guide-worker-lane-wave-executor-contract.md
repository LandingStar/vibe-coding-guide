# Planning Gate - Guide Worker Lane Wave Executor Contract

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The guide-worker local orchestration MCP surface can now create lane-bound
worker tasks and report scheduling waves, but the execution inside a wave is
still a serial loop. The next narrow slice should make the wave execution
contract explicit enough for future Qoder/opencode/Codex provider workers while
remaining safe under deterministic fake/mock validation.

## Scope

Add a bounded lane-distinct wave executor contract:

1. accept a selected `GuideWorkerParallelWave`;
2. preflight all selected ready tasks against the same scheduler state;
3. mark all selected tasks as running in the event log before runtime calls;
4. invoke runtime adapters for the wave through an injectable executor;
5. merge successful task results back into scheduler state in deterministic
   `task_id` order;
6. report execution mode, attempted parallelism, and deterministic merge facts.

## Parallelism Boundary

This gate may introduce implementation-level concurrent invocation for tests
through a standard-library executor, but it must not expose live provider
parallel execution through MCP. The contract remains provider-agnostic and
validated with fake/mock runtimes.

## Non-Goals

This gate does not:

1. call live Qoder/opencode/Codex providers;
2. make MCP `runtimeProvider=qoder` valid;
3. create persistent agent homes or scratch directories;
4. implement autonomous guide task splitting;
5. change Local Work Trajectory into the task lifecycle authority;
6. build UI readback.

## Acceptance Criteria

This gate may close only when:

1. runtime code exposes a wave executor result with attempted parallel task ids,
   completed task ids, failed task ids, and deterministic merge order;
2. guide-worker local orchestration can opt into the wave executor;
3. lane-distinct tasks complete through the executor and final scheduler state
   matches the previous serial behavior;
4. same-lane serialization still holds because wave selection remains unchanged;
5. tests prove that selected tasks are invoked by the executor as one wave and
   merged in deterministic order;
6. docs/checklist mention that this is still fake/mock-validated and not live
   provider execution.

## Implemented Surface

Runtime:

- `GuideWorkerWaveExecutionResult`
- `GuideWorkerWaveTaskRun`
- `execute_guide_worker_parallel_wave()`

Request / MCP option:

- `wave_execution_mode="serial" | "threaded"`
- MCP camelCase field: `waveExecutionMode`

The guide-worker orchestration loop now executes each selected
`GuideWorkerParallelWave` through the wave executor. The executor preflights all
selected ready tasks from the same state, records all `task_running` events
before runtime invocation, invokes runtime adapters as a batch, and merges
results back in sorted `task_id` order.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or guide_worker_parallel_wave or guide_worker_instruction_parser" -q
```

Observed result:

```text
9 passed, 381 deselected
```

## Residual Risk

This closes the fake/mock-validated executor contract only.

Still separate:

1. live Qoder/opencode/Codex provider execution;
2. provider permission grant and sandbox isolation policy;
3. autonomous guide splitting policy;
4. UI readback for wave executor metadata.
