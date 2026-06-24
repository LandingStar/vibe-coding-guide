# Planning Gate - Guide Worker Local Trajectory Orchestration MVP

> Date: 2026-06-23
> Status: COMPLETED

## Trigger

The completed guide/worker exchange dogfood proved that a guide and worker can
coordinate through `ExchangeArtifact` products and explicit scheduler candidate
consumption. The next requested capability is narrower but closer to actual
work:

1. on one Local Work Trajectory, a guide agent should assign sufficiently
   concrete worker instructions;
2. worker agents should own most concrete implementation work;
3. work on different trajectory lanes should be eligible for limited
   parallel scheduling.

## Boundary

This slice adds a scheduler-owned orchestration helper. It does not make Local
Work Trajectory the authority.

Authority split:

1. `ExchangeArtifact` records guide instructions and worker-facing products.
2. Scheduler snapshot/event log owns task lifecycle.
3. Scheduler admission ledger records exact coordination-product admission.
4. Local Work Trajectory remains a projection/readback target, not a task
   lifecycle source.

## Scope

Implement one deterministic MVP workflow:

1. guide creates one structured instruction artifact;
2. guide creates one scheduler batch submission with worker tasks;
3. worker tasks are assigned to trajectory lanes via
   `ContextScope.lane_id`;
4. the batch is admitted into scheduler state through the existing exact
   admission path;
5. a finite `parallel_wave` selector picks at most one ready worker task per
   lane;
6. selected tasks are executed through the fake runtime adapter for this slice;
7. result readback reports:
   - guide artifact id/version;
   - submitted worker task ids;
   - lane ids;
   - planned parallel waves;
   - run task ids;
   - authority split.

## Parallelism Semantics

The first version defines scheduling parallelism, not OS-thread or process
parallelism.

A `parallel_wave` is a deterministic set of ready worker tasks where no two
tasks share the same `ContextScope.lane_id`. The current executor may still run
the selected tasks sequentially through the fake runtime, but the wave is the
stable contract that future Qoder/opencode/Codex runtime providers can execute
concurrently.

Tasks in the same lane remain serial unless later gates add lane-local
sub-scheduling.

## Non-Goals

This gate does not:

1. run live Qoder, opencode, Codex, or other external providers;
2. start background daemons or OS services;
3. mutate agent-owned `.codex/progress-graph/local-work-trajectory.json` from
   runtime code;
4. implement autonomous guide-agent policy for arbitrary tasks;
5. implement UI binding;
6. implement true process/thread-level parallel execution;
7. infer task splits from free text;
8. create persistent agent home directories.

## Acceptance Criteria

This gate may close only when:

1. runtime code can create a guide instruction artifact and scheduler batch
   submission for at least two lanes;
2. worker instructions include concrete title, instruction, lane id, visible
   artifacts, and acceptance criteria;
3. exact admission persists scheduler snapshot/event log state and admission
   ledger records;
4. the first parallel wave contains no more than one ready task from any lane;
5. tasks from different lanes can complete in one bounded orchestration call;
6. same-lane tasks are not selected into the same wave;
7. output reports the scheduling-vs-execution distinction explicitly;
8. runtime/CLI tests cover the two-lane happy path and same-lane serialization;
9. docs/checklist mention this as an in-progress or completed narrow gate.

## Initial Implementation Recommendation

Add a new runtime helper rather than expanding the completed dogfood helper:

```text
run_guide_worker_local_trajectory_orchestration()
```

Expose the helper through one CLI operator surface:

```text
doc-based-coding scheduler guide-worker-local-orchestration
```

MCP exposure should be a follow-up unless a concrete caller requires it.

## Implemented Surface

Runtime:

- `src/runtime/orchestration/guide_worker_local_orchestration.py`
- `GuideWorkerInstruction`
- `GuideWorkerLocalOrchestrationRequest`
- `GuideWorkerLocalOrchestrationResult`
- `GuideWorkerParallelWave`
- `run_guide_worker_local_trajectory_orchestration()`
- `select_ready_worker_parallel_wave()`

CLI:

- `doc-based-coding scheduler guide-worker-local-orchestration`

The CLI default scenario creates two worker tasks on `lane:client` and
`lane:server`, admits them as a scheduler batch, and runs one bounded fake
runtime wave. Custom worker splitting remains a follow-up guide-policy gate.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
```

Focused implementation validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "guide_worker_local_orchestration or guide_worker_parallel_wave" -q
```

Observed result:

```text
3 passed, 359 deselected
```

After export-list and formatting polish, the combined focused/adjacent
guide-worker check also passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py -k "guide_worker_local_orchestration or guide_worker_parallel_wave or guide_worker_exchange_dogfood" -q
```

Observed result:

```text
5 passed, 384 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py -k "guide_worker_exchange_dogfood or guide_worker_local_orchestration or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or decide_agent_action_candidate or consume_accepted_scheduler_candidate" -q
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <changed files for this gate>
mcp__doc_based_coding.analyze_changes
```

Observed result:

```text
8 passed, 96 deselected
21 passed
doc-loop validator passed
git diff --check passed with Windows line-ending warnings only
analyze_changes returned no impact nodes and no coupling alerts
```

## Residual Risk

This closes only the first fake-runtime-safe orchestration slice.

Still separate:

1. autonomous guide-agent policy for arbitrary task splitting;
2. custom worker instruction intake beyond the default CLI scenario;
3. true process/provider-level parallel execution;
4. real Qoder/opencode/Codex runtime execution;
5. UI binding over the new wave metadata;
6. MCP wrapper, if a Codex-facing direct tool becomes necessary.
