# Planning Gate — Host-Owned Qoder Smoke Runner Helper

> Date: 2026-06-17
> Status: READY-FOR-CLOSE-REVIEW

## Trigger

`design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/controlled-real-qoder-wrapper-spike-followup-direction-analysis.md`

This gate converts the Qoder wrapper seam into a repeatable host-owned smoke
runner helper. It stays on the existing one-shot dogfood harness and does not
expand into daemon scheduling, UI evidence consumption, MCP real-provider
execution, or production sandboxing.

## Problem

The project now has:

```text
QoderSDKQueryClient
QoderSDKQueryClientConfig
QoderAgentRuntimeAdapter
RuntimeHostInvocation(surface="host-authorized-adapter")
RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)
run_host_runtime_dogfood_harness()
HostSchedulerRunEvidence
```

However, a caller still has to manually assemble snapshot paths, host
invocation, permission grant, wrapper config, evidence path, policy, and
projection settings to run a Qoder smoke. That makes the next live or
negative-path validation too easy to perform inconsistently.

## Authority Inputs

- `design_docs/controlled-real-qoder-wrapper-spike-followup-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`
- `review/controlled-real-qoder-wrapper-spike-2026-06-17.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Scope

This gate adds a host-owned Qoder smoke runner helper around the existing
wrapper and dogfood harness.

### Slice 1 — Smoke Runner Helper

Add a helper that:

1. Builds a minimal one-task Qoder scheduler snapshot when requested.
2. Constructs `QoderSDKQueryClient` from host-owned config when no injected
   `QoderQueryClient` is supplied.
3. Constructs `RuntimeHostInvocation(surface="host-authorized-adapter")`.
4. Constructs `RuntimeProviderPermissionGrant(provider="qoder",
   allow_sdk_client=True)`.
5. Calls `run_host_runtime_dogfood_harness()`.
6. Returns compact paths and the existing harness result.

### Slice 2 — Deterministic Validation

Add focused tests that prove:

1. Injected mock Qoder client path writes evidence and scheduler projection.
2. The helper initializes the smoke scheduler snapshot when requested.
3. Missing auth/SDK through the real wrapper fails closed before evidence or
   projection writes.
4. Snapshot task state remains `proposed` after readiness failure.

### Slice 3 — Prompt / Maintenance Guidance

Update scheduler smoke guidance to explain:

1. When to use the host-owned smoke helper.
2. How to run it with an injected client or real SDK wrapper.
3. Expected live and negative outcomes.
4. Credential hygiene.
5. Why MCP remains fake-only.

## Non-Goals

This gate does not:

1. Expose Qoder through MCP.
2. Add a scheduler daemon.
3. Add retry queues, cancellation, timeout policy, or event-log rotation.
4. Add UI evidence consumption.
5. Add Docker, git-worktree, remote VM, or any production sandbox.
6. Store raw transcripts or credentials in evidence, scheduler state, Local
   Work Trajectory, prompts, or review docs.
7. Promote Qoder internal subagents into project scheduler tasks or trajectory
   lanes.

## Acceptance Criteria

The gate may close only when:

1. A host-owned smoke helper exists outside MCP.
2. The helper reuses `QoderSDKQueryClient` / `QoderQueryClient` and
   `run_host_runtime_dogfood_harness()`.
3. The helper can create a minimal Qoder smoke scheduler snapshot.
4. The helper writes the same `HostSchedulerRunEvidence` shape as existing
   dogfood runs.
5. Deterministic injected-client tests pass.
6. Missing auth/SDK fail closed before evidence/projection writes and before
   scheduler task mutation.
7. Prompt guidance describes usage, negative paths, credential hygiene, and the
   MCP fake-only boundary.
8. Focused validation passes.

## Implementation Notes

### 2026-06-17 — Initial Helper Pass

Implemented:

1. `tools/progress_graph/qoder_smoke.py`
   - `QoderSmokeTaskConfig`
   - `HostOwnedQoderSmokeRunConfig`
   - `HostOwnedQoderSmokeRunResult`
   - `build_qoder_smoke_scheduler_state()`
   - `ensure_qoder_smoke_scheduler_snapshot()`
   - `run_host_owned_qoder_smoke()`
2. Exports updated in `tools/progress_graph/__init__.py`.
3. Focused tests added in `tests/test_progress_graph_trajectory.py`.

Current helper boundary:

1. It creates or reuses a scheduler snapshot.
2. It constructs host invocation and Qoder permission grant.
3. It delegates execution to `run_host_runtime_dogfood_harness()`.
4. It does not call MCP.
5. It does not mutate agent-owned Local Work Trajectory.
6. It does not store credentials or raw transcripts.

Focused validation so far:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "qoder_smoke or host_runtime_dogfood_harness"
6 passed
```

### 2026-06-17 — Close-Review Readiness

The gate is now `READY-FOR-CLOSE-REVIEW`.

Close-review evidence:

- `review/host-owned-qoder-smoke-runner-helper-2026-06-17.md`

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_tools.py tests/test_mcp_prompts_resources.py
295 passed, 1 skipped
```

Scope deliberately remains narrow:

1. Helper is host-owned and outside MCP.
2. Helper delegates to existing dogfood harness rather than implementing a
   second scheduler.
3. Live credentialed Qoder success remains a next-slice candidate, not a
   requirement for this helper slice.
