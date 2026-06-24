# Planning Gate - Guide Worker Local Orchestration MCP Surface

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The completed guide-worker local trajectory orchestration MVP exposed a runtime
helper and CLI, but Codex-facing agents still cannot invoke that helper through
the MCP tool surface. The next slice needs a thin MCP wrapper and structured
worker instruction intake so a guide agent can hand concrete lane-bound work to
worker tasks without relying on the CLI default demo split.

## Scope

Implement a narrow MCP surface over the existing fake-runtime helper:

1. accept `workerInstructions` as structured MCP input;
2. normalize camelCase MCP fields into `GuideWorkerInstruction`;
3. persist guide instruction and scheduler batch artifacts through the existing
   helper;
4. admit the scheduler batch through the existing exact admission path;
5. run bounded fake-runtime scheduling waves with at most one ready task per
   lane per wave;
6. report scheduling parallelism separately from true process parallelism.

## Non-Goals

This gate does not:

1. run Qoder, opencode, Codex, or any live provider;
2. create a real process/thread pool;
3. infer worker splits from free text;
4. implement autonomous guide policy;
5. create agent home or scratch directories;
6. mutate agent-owned Local Work Trajectory files from runtime/MCP code;
7. add UI binding.

## Acceptance Criteria

This gate may close only when:

1. MCP tool `schedulerGuideWorkerLocalOrchestration` is listed with a documented
   `workerInstructions` schema;
2. the tool can run two custom worker instructions on different lanes and report
   one parallel wave containing both tasks;
3. two same-lane instructions are serialized across bounded waves;
4. `runtimeProvider != fake` fails closed with a clear error and no state
   mutation;
5. invalid instruction shapes return readable field-path errors;
6. focused MCP/runtime tests cover the above behavior;
7. Checklist, phase map, scheduler MCP prompt, bootstrap prompt, and MCP tool
   audit mention the new surface.

## Interface Draft

Tool:

```text
schedulerGuideWorkerLocalOrchestration
```

Core input:

```json
{
  "trajectoryId": "local-work:current",
  "guideAgentId": "agent:guide",
  "workerAgentId": "agent:worker",
  "artifactIdPrefix": "guide-worker-local-orchestration",
  "workerInstructions": [
    {
      "taskId": "task/client",
      "title": "Implement client slice",
      "instruction": "Concrete worker instruction",
      "laneId": "lane:client",
      "allowedArtifacts": ["client"],
      "acceptance": ["Observable acceptance criterion"],
      "dependsOnTaskIds": [],
      "outputArtifactId": "task/client:result"
    }
  ],
  "maxParallelLanes": 2,
  "maxWaves": 1,
  "runtimeProvider": "fake"
}
```

The result must preserve the existing runtime helper payload shape, including
`parallel_waves` and `authority_split.local_work_trajectory_mutated=false`.

## Implemented Surface

Runtime:

- `guide_worker_instruction_from_mapping()`
- `guide_worker_instructions_from_sequence()`

MCP:

- `schedulerGuideWorkerLocalOrchestration`

The MCP wrapper accepts custom `workerInstructions`, keeps `runtimeProvider`
fake-only, and delegates the actual workflow to
`run_guide_worker_local_trajectory_orchestration()`. Invalid instruction
payloads return stable JSON errors with field paths such as
`workerInstructions[0].instruction`.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "guide_worker_local_orchestration" -q
```

Observed result:

```text
4 passed, 22 deselected
```

Additional validation is recorded in the final write-back for this slice.

## Residual Risk

This closes only the Codex-facing fake-runtime MCP wrapper.

Still separate:

1. autonomous guide-agent policy for arbitrary task splitting;
2. true provider/process-level parallel execution;
3. Qoder/opencode/Codex runtime provider mapping;
4. UI readback over scheduling wave metadata;
5. agent home/scratch allocation and cleanup policy.
