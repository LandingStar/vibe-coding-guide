# Planning Gate - Autonomous Guide Instruction Planner

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

Guide-worker orchestration can now execute concrete `GuideWorkerInstruction`
objects, expose them through CLI/MCP, run lane-distinct waves, and map workers
to host-owned providers. The remaining gap for the requested single-trajectory
guide/worker collaboration is that one leader/guide agent still needs the
caller to provide `workerInstructions` directly instead of scheduling multiple
lane-bound workers from a higher-level local work task.

## Scope

Add the first deterministic single-leader guide instruction planner:

1. accept a higher-level local trajectory work description;
2. derive multiple concrete worker instructions from explicit lane specs or a narrow
   built-in two-lane fallback;
3. include task id, title, instruction, lane id, edit lease artifacts,
   acceptance criteria, output artifact id, and optional dependencies;
4. write the generated instructions through the existing guide instruction
   artifact and scheduler batch path;
5. expose the planner through CLI and MCP without changing existing explicit
   `workerInstructions` behavior;
6. validate that a single leader can schedule multiple workers and that
   different lanes still form bounded parallel waves.

## Non-Goals

This gate does not:

1. call an LLM to decide arbitrary decomposition;
2. implement a learned or heuristic project-wide planner;
3. open live provider execution through MCP;
4. create real agent home or scratch directories;
5. enforce write-back sandbox isolation beyond existing edit leases;
6. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
7. replace explicit `workerInstructions` for advanced callers.

## Acceptance Criteria

This gate may close when:

1. runtime requests can carry a guide task description and planner lane specs;
2. generated instructions are visible in the result payload and guide artifact;
3. explicit `workerInstructions` continue to take precedence when provided;
4. CLI can run the planner without manually supplied instruction JSON;
5. MCP can run the planner while preserving fake-only provider guards;
6. focused runtime/CLI/MCP tests prove generated lane-distinct instructions
   execute in a bounded wave.

## Implemented Surface

Runtime:

- `GuideWorkerPlannerLaneSpec`
- `GuideWorkerPlanningRequest`
- `GuideWorkerLocalOrchestrationRequest.planning_request`
- `GuideWorkerLocalOrchestrationResult.planned_worker_instructions`
- `GuideWorkerLocalOrchestrationResult.planning_source`

The runtime now resolves worker instructions in this order:

1. explicit `worker_instructions`;
2. deterministic planner output from `planning_request.lane_specs`;
3. the existing two-lane fallback planner.

Generated planner instructions include stable task ids, lane ids, worker
agent/runtime hints, edit-lease artifact hints, acceptance criteria,
dependencies mapped from lane ids to generated task ids, and output artifact
ids. The result payload reports planner/source metadata and the concrete
generated instructions.

CLI:

- `doc-based-coding scheduler guide-worker-local-orchestration`
- New arguments:
  - `--guide-task-title`
  - `--guide-task-summary`
  - repeatable `--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT]`

MCP:

- `schedulerGuideWorkerLocalOrchestration`
- New payload fields:
  - `guideTask`
  - `plannerLaneSpecs`

MCP remains fake-only. Non-fake `workerRuntimeProvider` values are rejected on
the actually executed source: explicit `workerInstructions` when present, or
planner lane specs when the planner is used. Explicit instructions still take
precedence over planner specs.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py -k "guide_worker_local_orchestration or scheduler_guide_worker_local_orchestration" -q
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched planner/runtime/CLI/MCP/test/doc files>
```

Observed results:

```text
15 passed, 385 deselected
21 passed
doc-loop validation passed
git diff --check: no whitespace errors; Windows line-ending warnings only
```

`analyze_changes` returned no impact nodes. It reported the expected
`coupling-mcp-tools-registration` must-sync alert for `src/mcp/tools.py`; the
server schema/routing was updated in `src/mcp/server.py` and covered by MCP
route tests.

## Residual Risk After Close

The planner is intentionally deterministic and narrow. It proves the scheduling
contract and data product shape for single-leader guide-owned decomposition,
but real judgment about arbitrary task splitting remains a later policy/runtime
slice.
