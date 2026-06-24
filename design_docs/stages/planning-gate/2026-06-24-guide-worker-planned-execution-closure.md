# Planning Gate - Guide Worker Planned Execution Closure

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The guide-worker orchestration stack can now:

1. derive concrete lane-bound worker instructions from a high-level guide task
   and lane specs;
2. run lane-distinct worker waves through fake/mock runtime adapters;
3. run host-owned Qoder guide-worker waves through explicit host runtime
   wiring.

The remaining gap for the current objective is that the host-owned execution
wrapper still only accepts fixed or explicit `worker_instructions`. It cannot
yet execute planner-derived workers from the same guide task surface, and its
evidence only reports output refs instead of a per-worker execution receipt
that lets a guide or reviewer inspect whether each assigned worker completed
its lane.

## Scope

Add a narrow host-owned planned execution closure:

1. allow `HostOwnedGuideWorkerProviderExecutionConfig` to carry
   `GuideWorkerPlanningRequest`;
2. preserve explicit `worker_instructions` precedence when both explicit
   instructions and a planning request are present;
3. validate configured runtime providers against the actual instruction source
   that will execute;
4. include planner metadata and generated instructions in the host-owned
   evidence payload;
5. add compact per-worker execution receipts with task id, lane id, worker
   agent id, runtime provider, task state, run id, output artifact ref, and
   acceptance criteria;
6. cover planned multi-worker execution through injected mock Qoder and the
   existing lane wave executor.

## Non-Goals

This gate does not:

1. call an LLM to decide arbitrary task decomposition;
2. expose live provider execution through Codex MCP;
3. add opencode or Codex runtime providers;
4. create real agent home or persistent scratch directories;
5. execute repository edits in a real sandbox;
6. persist raw transcripts or provider logs;
7. mutate agent-owned Local Work Trajectory from runtime/helper code.

## Acceptance Criteria

This gate may close when:

1. host-owned guide-worker provider execution can run a planning request without
   explicit `worker_instructions`;
2. planner-derived qoder workers are executed through injected mock Qoder in a
   lane-distinct wave;
3. explicit `worker_instructions` still override a supplied planning request;
4. evidence payload reports planner source, planned worker instructions, and
   per-worker execution receipts;
5. provider validation rejects a planner-derived worker whose provider is not
   configured, before evidence writes;
6. focused runtime/CLI tests pass and MCP fake-only behavior remains unchanged.

## Implemented Surface

Runtime:

- `resolve_guide_worker_instructions()` exposes the same instruction resolution
  used by `run_guide_worker_local_trajectory_orchestration()`: explicit worker
  instructions first, then planner-derived instructions, then fallback planner.

Host-owned wrapper:

- `HostOwnedGuideWorkerProviderExecutionConfig.planning_request`
- `HostOwnedGuideWorkerProviderExecutionConfig.planner_worker_runtime_provider`
- `run_host_owned_guide_worker_provider_execution()`

The host-owned wrapper can now run planner-derived workers without explicit
`worker_instructions`. If one provider is configured, planned lanes without an
explicit `worker_runtime_provider` default to that provider. The Qoder CLI
surface sets this default to `qoder` when `--planner-lane` is supplied.

Evidence:

- `planning`
- `planned_worker_instructions`
- `worker_execution_receipts`

Each worker execution receipt includes task id, lane id, title, worker agent id,
runtime provider, task state, run id, session id, output artifact id/ref, and
acceptance criteria.

CLI:

- `doc-based-coding qoder guide-worker-smoke`
- New planner options:
  - `--guide-task-title`
  - `--guide-task-summary`
  - repeatable `--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT]`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile tools/progress_graph/guide_worker_provider_execution.py src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_doc_loop_prompts.py
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_doc_loop_prompts.py -k "guide_worker_provider_execution or qoder_guide_worker_smoke or scheduler_mcp_smoke_prompt_covers_submit_project_run_lifecycle or qoder_host_provisioning_guide" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or scheduler_guide_worker_local_orchestration or qoder_guide_worker_smoke" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched planned execution closure files>
```

Observed results:

```text
10 passed, 166 deselected
17 passed, 383 deselected
doc-loop validation passed
git diff --check: no whitespace errors; Windows line-ending warnings only
```

`analyze_changes` returned no impact nodes and no coupling alerts.

## Residual Risk After Close

This closure proves that one leader can schedule planner-derived workers and
that a host-owned runtime wrapper can execute and audit those workers. Real
code editing still depends on a live provider plus sandbox/writeback policy,
which remains a later slice.
