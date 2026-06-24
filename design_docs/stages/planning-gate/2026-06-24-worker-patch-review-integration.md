# Planning Gate - Worker Patch Review Integration

> Date: 2026-06-24
> Status: IMPLEMENTED

## Trigger

The guide-worker stack can now plan lane-bound worker tasks, run Codex CLI
workers through a host-owned provider wrapper, allocate git-worktree sandboxes,
and write review-only worker writeback receipts. The remaining gap for real
worker edits is the bridge from sandbox changes into an explicit review /
merge product that the guide can inspect and later accept or reject.

The previous gate deliberately stopped before patch application:

- `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`

This gate adds the next narrow bridge: export worker sandbox changes as compact
patch-review artifacts and connect them to the existing action-candidate /
merge-gate model without applying changes automatically.

## Scope

Add a minimal worker patch review integration slice:

1. define a durable worker patch artifact summary produced from a worker run
   receipt and sandbox allocation;
2. for git-worktree sandboxes, collect changed file paths and a textual patch
   from the worker worktree without mutating the source workspace;
3. publish one compact `ExchangeArtifact` per worker patch proposal in the
   existing artifact store;
4. make each worker writeback receipt reference its patch artifact when one
   is available;
5. create explicit review metadata that can be read as a `merge_candidate`
   or review candidate by the existing action-candidate layer;
6. keep guide-worker runtime and MCP authority boundaries unchanged:
   runtime code does not mutate Local Work Trajectory, and MCP guide-worker
   orchestration remains fake-only.

## Non-Goals

This gate does not:

1. apply worker patches to the source workspace;
2. run `git merge`, `git apply`, branch checkout, or conflict resolution;
3. decide merge approval automatically;
4. clean up worker sandboxes after review;
5. create persistent agent homes;
6. expose live Codex CLI provider execution through MCP;
7. replace the existing `merge_candidate` disposition and
   `consume-accepted-merge-candidate` flow.

## Acceptance Criteria

This gate may close when:

1. a host-owned Codex guide-worker run with a git-worktree sandbox can produce
   a worker patch artifact summary for each completed worker task;
2. the patch artifact records task id, lane id, runtime provider, sandbox
   provider/allocation id, sandbox workspace root, changed paths, and a compact
   textual patch or explicit empty-patch state;
3. host evidence includes patch artifact refs from worker writeback receipts;
4. patch artifacts are stored as `ExchangeArtifact` records in the existing
   artifact store and can be inspected by existing action-candidate tooling;
5. no source workspace files are modified by patch export;
6. focused tests prove the git-worktree patch collection path and fake-only
   MCP guard remain intact.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_review.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py -k "worker_patch_review or guide_worker_provider_execution or codex_sandbox_receipts or codex_guide_worker" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "guide_worker_local_orchestration" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched worker patch review files>
```

## Residual Risk After Close

This gate should prove that worker sandbox edits can be recovered as reviewable
patch products. It will not yet prove automated patch application, conflict
resolution, cleanup-after-review, or multi-worker patch composition policy.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/worker_patch_review.py`.
- New product constants: `WORKER_PATCH_REVIEW_PRODUCT_TYPE` and
  `WORKER_PATCH_REVIEW_SCHEMA_VERSION`.
- New `WorkerPatchReviewArtifact` read model and
  `build_worker_patch_review_artifact(s)` helpers.
- Git-worktree patch collection reads `git status --porcelain` and
  `git diff --binary` from the allocated worker worktree path recorded in
  `GitWorktreeSandboxReceipt.worktree_path`.
- Patch proposal artifacts are `ExchangeArtifact(kind="proposal",
  intent="request_merge")` and include a `merges_into` relation so existing
  `agentExchangeActionCandidates` readback recognizes them as
  `merge_candidate`.

Host-owned wrapper:

- `run_host_owned_guide_worker_provider_execution()` now publishes worker
  patch proposal artifacts to the configured ExchangeArtifact store by default
  for git-worktree worker runs.
- Evidence now includes `worker_patch_artifact_refs`.
- Each `worker_writeback_receipt` includes `patch_artifact_ref` when a patch
  proposal artifact exists.
- Source workspace remains untouched; patch export only reads worker worktree
  state.

CLI:

- `doc-based-coding codex guide-worker-smoke --help` and
  `doc-based-coding qoder guide-worker-smoke --help` now state that
  git-worktree worker changes are exported as review-only worker patch
  artifacts and merge candidates, not applied automatically.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_review.py src/runtime/orchestration/__init__.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_mcp_admission.py -k "worker_patch_review or patch_review_candidate or codex_sandbox_receipts or qoder_guide_worker_smoke_help or codex_guide_worker_smoke_help or guide_worker_local_orchestration" -q
```

Observed results:

```text
22 passed, 470 deselected
```
