# Controlled Host Runtime Dogfood Harness Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`.

Verdict: ready for close review.

The implementation creates a compact host-run evidence JSON contract and a
repeatable host-runtime dogfood harness over the existing host-authorized
scheduler runner. It keeps scheduler state authoritative, keeps scheduler
projection read-only, does not mutate agent-owned Local Work Trajectory, keeps
MCP fake-only, and does not import or construct the real Qoder SDK.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| A host-run evidence JSON contract exists and is documented. | `src/runtime/orchestration/scheduler_dogfood.py` defines `HostSchedulerRunEvidence`, `HostSchedulerRunEvidenceWriteResult`, `build_host_scheduler_run_evidence()`, `write_host_scheduler_run_evidence()`, and constants for product type / schema version. The active gate documents the field set. | Met |
| A fake-runtime dogfood run can write evidence JSON and refresh scheduler projection. | `tools/progress_graph/scheduler_dogfood.py::run_host_runtime_dogfood_harness()` builds `HostSchedulerRunRequest`, calls `run_host_authorized_scheduler_once_and_refresh_projection()`, and writes evidence JSON. `tests/test_progress_graph_trajectory.py::test_host_runtime_dogfood_harness_fake_writes_evidence_and_projection` covers this path. | Met |
| A mock-Qoder host-authorized dogfood run can write the same evidence shape. | `tests/test_progress_graph_trajectory.py::test_host_runtime_dogfood_harness_mock_qoder_writes_same_evidence_shape` injects a mock `QoderQueryClient`, requires host authorization and grant, writes evidence, and verifies the same JSON shape. | Met |
| Evidence includes provider, host invocation, run count, stop reason, output artifact refs, permission-review tasks, history summary, and authority split flags. | `HostSchedulerRunEvidence.to_json_dict()` projects these fields from `HostSchedulerRunResult.to_json_dict()`. Runtime and progress-graph tests assert providers, host invocation reason, run count, stop reason, output refs, history summary, and authority split. | Met |
| MCP fake-only rejection remains covered. | Existing `schedulerRunOnceAndProject` behavior is unchanged. `tests/test_mcp_tools.py -k "scheduler_run_once_and_project"` passes, including qoder rejection coverage. | Met |
| Prompt / maintenance guidance explains how to run, inspect, and write back dogfood evidence without using `localTrajectory` as scheduler state. | `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` and the bootstrap copy now document `run_host_runtime_dogfood_harness()`, evidence JSON fields, default evidence path, and authority split. `tests/test_doc_loop_prompts.py::test_scheduler_mcp_smoke_prompt_covers_submit_project_run_lifecycle` covers the prompt. | Met |
| Focused tests cover fake evidence write, mock-Qoder evidence write, missing host authorization / grant rejection, and MCP fake-only behavior. | Runtime evidence tests, progress-graph harness tests, MCP tests, and prompt tests all pass. | Met |

## Validation

Focused validation run on 2026-06-17:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or host_scheduler_run_evidence"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_runtime_dogfood_harness or host_authorized_scheduler_run"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "scheduler_run_once_and_project"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed
```

Combined focused regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_prompts_resources.py
284 passed, 1 skipped
```

Whitespace validation:

```text
git diff --check -- <touched dogfood harness / prompt / gate files>
no errors
```

Only Windows line-ending warnings were reported for existing tracked files.

## Residual Risk

The following remain outside this gate and should not block close review:

1. Real Qoder SDK import and execution.
2. Real opencode runtime behavior.
3. Scheduler daemon behavior.
4. Real process, Docker, remote VM, or git-worktree isolation.
5. Retry, timeout, cancellation, or event-log rotation policy.
6. MCP exposure for real providers.
7. UI redesign or richer host UX consumption of evidence JSON.

## Close Recommendation

Move the planning gate from `ACTIVE` to `READY-FOR-CLOSE-REVIEW`.

The next follow-up should decide whether to proceed to a controlled real Qoder
wrapper spike, a host UX evidence consumer, or a daemon/sandbox preparatory
slice. Based on the current boundary, the highest-value next step is likely a
direction analysis comparing those paths before any real SDK execution is
authorized.
