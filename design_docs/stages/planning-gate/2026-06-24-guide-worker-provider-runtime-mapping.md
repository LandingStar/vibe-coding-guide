# Planning Gate - Guide Worker Provider Runtime Mapping

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The guide-worker orchestration now has an MCP surface and a lane wave executor,
but worker tasks are still always emitted with `runtime_provider="fake"`. To
move toward real guide/worker agent collaboration, the runtime layer needs a
provider mapping seam where worker instructions can request a provider and a
host-authorized runtime registry can execute it.

## Scope

Add a narrow provider mapping contract:

1. extend `GuideWorkerInstruction` with `worker_runtime_provider`;
2. accept JSON/MCP-style `workerRuntimeProvider`;
3. emit scheduler worker tasks with the requested provider;
4. validate host-authorized execution using an injected mock Qoder adapter;
5. keep MCP `schedulerGuideWorkerLocalOrchestration.runtimeProvider` fake-only
   and reject live provider exposure through MCP.

## Non-Goals

This gate does not:

1. construct a real Qoder SDK client;
2. expose `runtimeProvider=qoder` through MCP;
3. run opencode/Codex providers;
4. implement autonomous guide splitting;
5. create persistent agent home or scratch directories;
6. mutate agent-owned Local Work Trajectory from runtime code.

## Acceptance Criteria

This gate may close only when:

1. a guide-worker instruction can request `workerRuntimeProvider="qoder"`;
2. the resulting scheduler task carries `agent.runtime_provider="qoder"`;
3. injected mock Qoder runtime execution completes through the existing wave
   executor;
4. MCP live-provider guard remains closed;
5. tests cover provider mapping and fake-only MCP guard;
6. docs/status mention that this is host-authorized adapter mapping, not live
   MCP provider execution.

## Implemented Surface

Runtime:

- `GuideWorkerInstruction.worker_runtime_provider`
- JSON/MCP intake alias `workerRuntimeProvider`
- Scheduler task emission with per-worker `AgentSpec.runtime_provider`

Validation path:

- Host-authorized Python callers can inject a runtime registry containing
  `QoderAgentRuntimeAdapter` backed by a mock `QoderQueryClient`.
- MCP `schedulerGuideWorkerLocalOrchestration` rejects non-fake
  `workerRuntimeProvider` values before state mutation.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or guide_worker_parallel_wave or guide_worker_instruction_parser" -q
```

Observed result:

```text
11 passed, 381 deselected
```

## Residual Risk

This is a provider mapping seam, not a live-provider launch.

Still separate:

1. host-owned wrapper for real Qoder credentials/readiness;
2. process/sandbox-level isolation for real worker agents;
3. autonomous guide policy that chooses provider/lane splits;
4. UI readback for provider-backed worker runs.
