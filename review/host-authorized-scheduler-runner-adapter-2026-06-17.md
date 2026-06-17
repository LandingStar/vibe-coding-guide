# Host-Authorized Scheduler Runner Adapter Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-17-host-authorized-scheduler-runner-adapter.md`.

Verdict: ready for close review.

The implementation evidence satisfies the gate acceptance criteria. The gate
creates a host-authorized one-shot scheduler runner adapter and projection
wrapper without exposing real providers through MCP and without importing the
real Qoder SDK.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| A host runner request/result contract exists and is JSON-serializable. | `src/runtime/orchestration/scheduler_host_runner.py` defines `HostSchedulerRunRequest`, `HostSchedulerRunResult`, and `HostSchedulerRunResult.to_json_dict()`. `tests/test_runtime_orchestration.py::test_host_scheduler_runner_fake_result_is_json_serializable` serializes the compact result. | Met |
| A fake runtime scheduler run can complete through the host adapter and write a scheduler projection. | `run_host_authorized_scheduler_once()` builds runtime wiring, uses shared-process sandbox metadata, and calls `run_persisted_scheduler_once_with_wiring()`. `tools/progress_graph/scheduler_projection.py::run_host_authorized_scheduler_once_and_refresh_projection()` writes the scheduler-derived projection. Tests include `test_host_scheduler_runner_fake_result_is_json_serializable` and `test_host_authorized_scheduler_run_and_refresh_projection_preserves_agent_trajectory`. | Met |
| A mock-Qoder scheduler run can complete only through `host-authorized-adapter` with explicit grant and injected client. | `RuntimeRegistryWiringConfig` still requires `RuntimeHostInvocation(surface="host-authorized-adapter")`, `RuntimeProviderPermissionGrant`, and an injected `QoderQueryClient` for qoder. `test_host_scheduler_runner_mock_qoder_requires_host_authorization` covers rejection without the proper host surface/grant and success with an injected `_RecordingQoderClient`. | Met |
| MCP `schedulerRunOnceAndProject` still rejects `qoder` and remains fake-only. | `src/mcp/tools.py::scheduler_run_once_and_project()` rejects non-`fake` `runtimeProvider` before runtime wiring. `tests/test_mcp_tools.py -k "scheduler_run_once_and_project"` passes and includes fake-only rejection coverage. | Met |
| Result contract exposes runtime providers, host surface, stop reason, run count, output artifact refs, compact history/log references, and authority split flags. | `HostSchedulerRunResult.to_json_dict()` exposes `runtime_registry_providers`, `runtime_host_surface`, `stop_reason`, `run_count`, `output_artifact_refs`, `history_summary`, and `authority_split.local_work_trajectory_mutated=false`. Runtime tests assert these fields. | Met |
| Focused tests cover fake success, mock-Qoder success, missing host invocation or grant rejection, and MCP fake-only behavior. | Runtime tests cover fake and mock-Qoder host paths; MCP tests cover fake-only behavior; trajectory tests cover projection and authority split. | Met |
| Prompt / maintenance guidance explains the submit -> project -> host-run -> inspect loop without replacing `localTrajectory`. | `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` and the bootstrap copy document `HostSchedulerRunRequest`, `run_host_authorized_scheduler_once()`, `run_host_authorized_scheduler_once_and_refresh_projection()`, `history_summary`, and the MCP fake-only boundary. `tests/test_doc_loop_prompts.py::test_scheduler_mcp_smoke_prompt_covers_submit_project_run_lifecycle` covers the guidance. | Met |

## Validation

Focused validation run on 2026-06-17:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or run_persisted_scheduler_once_with"
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_authorized_scheduler_run_and_refresh_projection or run_persisted_scheduler_once_and_refresh_projection"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "scheduler_run_once_and_project"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "scheduler_submit_tasks"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_prompts_resources.py
21 passed
```

Combined focused regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_prompts_resources.py
280 passed, 1 skipped
```

Whitespace validation:

```text
git diff --check -- <touched host-runner/projection/prompt/review files>
no errors
```

Only Windows line-ending warnings were reported for existing tracked files.

## Residual Risk

The following items remain outside this gate and should not block close review:

1. Real Qoder SDK import and execution.
2. Real opencode adapter behavior.
3. Real process, Docker, remote VM, or git-worktree isolation.
4. Scheduler daemon behavior, parallel execution, retry loops, cancellation, and timeout enforcement.
5. MCP exposure for real providers.
6. Scheduler-driven mutation of agent-owned Local Work Trajectory.
7. Event-log truncation or rotation policy.

## Close Recommendation

Move the planning gate from `ACTIVE` to `READY-FOR-CLOSE-REVIEW`.

The next step should be a narrow follow-up direction analysis for the next
orchestration-layer slice. Based on the current boundary, the most natural
candidate is a controlled host-runtime dogfood path over the new adapter, still
without turning MCP into a real-provider execution surface.
