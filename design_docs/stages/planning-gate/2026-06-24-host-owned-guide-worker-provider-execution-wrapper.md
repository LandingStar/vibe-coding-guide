# Planning Gate - Host-Owned Guide Worker Provider Execution Wrapper

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

Guide-worker local orchestration can now map worker instructions to provider
runtime names, and the lane wave executor can run lane-distinct waves through an
injected runtime registry. The remaining gap is a host-owned wrapper that can
exercise provider-backed worker execution without opening live providers through
Codex MCP.

## Scope

Add a narrow host-owned execution wrapper:

1. compose `run_guide_worker_local_trajectory_orchestration()` with explicit
   host runtime wiring;
2. support Qoder worker providers through an injected `QoderQueryClient` or a
   host-constructed `QoderSDKQueryClient`;
3. preserve the MCP fake-only guard for `schedulerGuideWorkerLocalOrchestration`;
4. write compact host evidence for guide-worker provider execution;
5. expose a CLI command for host-owned Qoder guide-worker smoke runs;
6. validate with injected mock Qoder execution and readiness-negative behavior.

## Non-Goals

This gate does not:

1. expose live provider execution through MCP;
2. make Qoder SDK a hard runtime dependency;
3. add opencode/Codex providers;
4. create real agent home or persistent scratch directories;
5. persist raw transcripts, token values, or full SDK logs;
6. mutate agent-owned Local Work Trajectory from runtime/helper code;
7. implement autonomous guide policy for splitting arbitrary user work.

## Acceptance Criteria

This gate may close only when:

1. a host wrapper can run guide-worker instructions with
   `workerRuntimeProvider="qoder"` through an injected mock Qoder client;
2. the wrapper returns provider, lane, wave, run, output, path, and authority
   facts in a compact JSON shape;
3. evidence JSON is written only after provider readiness succeeds;
4. readiness-negative Qoder SDK setup fails before evidence/projection writes
   and without mutating Local Work Trajectory;
5. CLI help clearly states the host-owned boundary and no raw-token policy;
6. focused tests cover runtime wrapper, CLI help/negative path, and existing
   MCP fake-only behavior remains covered.

## Implemented Surface

Runtime/readback:

- `GuideWorkerLocalOrchestrationResult.to_json_dict()` now reports
  `runtime_provider` and `worker_runtime_providers` from final scheduler tasks
  instead of hard-coding `fake`.
- `run_guide_worker_local_trajectory_orchestration()` mirrors newly created
  guide/batch artifacts into a caller-supplied in-memory artifact store, so
  host-injected registries can safely mix fake and Qoder workers.

Host wrapper:

- `tools.progress_graph.guide_worker_provider_execution`
- `run_host_owned_guide_worker_provider_execution()`
- `HostOwnedGuideWorkerProviderExecutionConfig`
- `HostOwnedGuideWorkerProviderExecutionResult`
- evidence product: `host_guide_worker_provider_execution_evidence`

CLI:

- `doc-based-coding qoder guide-worker-smoke`

Documentation:

- scheduler MCP smoke prompt and bootstrap prompt now describe the host-owned
  wrapper and fake-only MCP boundary.
- `docs/qoder-host-provisioning-check-guide.md` now includes the guide-worker
  smoke command.
- `design_docs/tooling/MCP Tool Surface Audit.md` records the wrapper as
  non-MCP host-owned surface.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py tools/progress_graph/guide_worker_provider_execution.py tools/progress_graph/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py -k "guide_worker_provider_execution or guide_worker_local_orchestration_can_use_injected_qoder_worker_runtime or qoder_guide_worker_smoke" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py tests/test_cli.py tests/test_runtime_orchestration.py -k "guide_worker_local_orchestration or qoder_smoke or qoder_guide_worker_smoke or qoder_help" -q
```

Observed results:

```text
6 passed, 433 deselected
16 passed, 378 deselected
```

## Residual Risk

Still separate:

1. autonomous guide policy for deciding worker splits;
2. real host credential success evidence on a provisioned Qoder environment;
3. opencode/Codex provider adapters;
4. process/sandbox-level worker isolation beyond the existing shared-process
   scheduler preflight;
5. UI readback for provider-backed guide-worker evidence.
