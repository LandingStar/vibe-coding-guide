# Planning Gate - Codex Worker Sandbox Writeback Policy

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The guide-worker stack can now plan lane-bound workers, execute lane-distinct
waves, and use Codex CLI as a host-owned runtime provider. The remaining gap
for real worker code editing is not the provider invocation itself; it is the
policy boundary around worker filesystem isolation, writeback receipts, and
merge review.

This gate adds the first narrow host-owned bridge between guide-worker provider
execution and the existing sandbox receipt model.

## Scope

Add a minimal sandbox/writeback policy slice for host-owned Codex workers:

1. allow guide-worker instructions to request a sandbox profile, starting with
   `shared-process` and `git-worktree`;
2. let the host-owned guide-worker provider wrapper register an explicit
   `git-worktree` sandbox provider when requested;
3. write durable sandbox allocation receipt evidence for guide-worker provider
   execution when the host opts in;
4. surface per-worker writeback receipts derived from runtime artifact deltas
   and sandbox allocations;
5. surface merge review candidates only as compact evidence metadata; do not
   auto-merge worker worktrees into the source workspace;
6. keep MCP guide-worker orchestration fake-only.

## Non-Goals

This gate does not:

1. automatically apply worker patches to the source workspace;
2. run `git merge`, `git apply`, or branch integration for worker outputs;
3. create persistent agent home directories;
4. approve runtime permission requests from Codex workers;
5. expose live Codex CLI execution through MCP;
6. replace the existing scheduler merge-gate product.

## Acceptance Criteria

This gate may close when:

1. explicit guide-worker instructions and planner lane specs can declare a
   `sandboxProfile`;
2. default behavior remains `shared-process`;
3. a host-owned guide-worker provider execution configured with
   `git-worktree` writes sandbox allocation receipt evidence;
4. the guide-worker provider evidence includes worker writeback receipts with
   task id, lane id, runtime provider, sandbox provider, sandbox allocation id,
   output artifact ref, changed refs, and merge review state;
5. git-worktree receipts are visible without mutating Local Work Trajectory
   from runtime code;
6. focused tests prove the wrapper can run mock Codex workers through the
   sandbox receipt path and that MCP still rejects live worker providers.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py tests/test_cli.py -k "guide_worker_provider_execution or codex_worker_sandbox or sandbox_profile" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or codex_guide_worker" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched codex worker sandbox writeback files>
```

## Residual Risk After Close

This gate will prove that host-owned Codex workers can be run under an explicit
sandbox allocation policy and produce reviewable writeback evidence. It will
not yet prove automated multi-worker patch merge, conflict resolution, or
long-lived agent home promotion.

## Implemented Surface

Runtime:

- `GuideWorkerInstruction.sandbox_profile`
- `GuideWorkerPlannerLaneSpec.sandbox_profile`
- JSON/MCP alias: `sandboxProfile`
- `TaskSpec.runtime_workspace_root`, `scratch_path`,
  `sandbox_allocation_id`, `sandbox_provider`, and `visible_mounts`
- Guide-worker wave execution now passes the preflight runtime task to the
  runtime adapter so Codex CLI can run in the per-worker sandbox workspace.

Host-owned wrapper:

- `HostOwnedGuideWorkerProviderExecutionConfig.git_worktree_sandbox_root`
- `sandbox_allocation_evidence_id`
- `sandbox_allocation_evidence_path`
- `git_executable`
- `run_host_owned_guide_worker_provider_execution()` registers
  `GitWorktreeSandboxProvider` only when the host opts in.
- Provider evidence now includes `worker_writeback_receipts` and optional
  durable sandbox allocation receipt evidence path.

CLI:

- `doc-based-coding codex guide-worker-smoke` and
  `doc-based-coding qoder guide-worker-smoke` accept
  `--git-worktree-sandbox-root`, `--sandbox-allocation-evidence-id`, and
  `--sandbox-allocation-evidence-path`.
- `--planner-lane` accepts optional `SANDBOX_KIND` as
  `LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]`.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/preflight.py src/runtime/orchestration/codex_cli_client.py src/runtime/orchestration/guide_worker_local_orchestration.py src/mcp/tools.py src/mcp/server.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_mcp_admission.py -k "sandbox_profile or codex_sandbox_receipts or runtime_workspace or guide_worker_provider_execution or codex_guide_worker or qoder_guide_worker_smoke_help or guide_worker_local_orchestration" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

Observed results:

```text
29 passed, 461 deselected
doc-loop validation passed
git diff --check passed with Windows line-ending warnings only
analyze_changes returned no impact nodes; MCP registration coupling was covered
by src/mcp/server.py schema/routing updates and focused MCP route tests
```
