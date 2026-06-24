# Planning Gate - Worker Patch Composition Preflight

> Date: 2026-06-24
> Status: IMPLEMENTED

## Trigger

The guide-worker Codex CLI path now supports:

- lane-bound worker planning and finite lane-parallel execution;
- git-worktree sandbox allocation and writeback receipts;
- one worker patch proposal artifact per worker;
- explicit single-patch `check`, `apply`, and `reject`.

The next fan-in gap is multiple worker patches from different lanes. A guide or
operator needs to know whether a set of patch proposals can be applied together,
which order is viable, and which patch creates the first conflict.

## Scope

Add a non-mutating composition preflight for worker patch proposals:

1. read multiple exact `worker_patch_review_proposal` artifacts from the
   ExchangeArtifact store;
2. validate each artifact has `patch_state=has_patch` and git diff evidence;
3. run the patches in an explicit order against a temporary copy of an
   explicitly supplied source workspace;
4. execute `git apply --check` and then `git apply` inside the temporary copy
   for each patch in order;
5. stop at the first failed check/apply and report the failing artifact;
6. return compact per-patch results, changed paths, touched path collisions,
   order, and final status;
7. expose the helper through a CLI surface for local/operator validation.

## Non-Goals

This gate does not:

1. mutate the source workspace;
2. apply multiple patches to the real source repository;
3. choose an automatic ordering algorithm beyond preserving caller order;
4. resolve conflicts;
5. clean up worker sandboxes;
6. compose binary patch semantics beyond what `git apply` supports;
7. expose a new MCP live-provider or Codex CLI execution surface;
8. mutate agent-owned Local Work Trajectory from runtime or CLI code;
9. bind Host UX review buttons.

## Contract

The preflight requires:

- `artifact_store_path`;
- two or more exact patch refs in caller-specified order;
- `source_workspace_root`;
- optional explicit `scratch_root` for temporary preflight workspaces.

The preflight creates a temporary workspace under `scratch_root` or the system
temp directory, copies the source workspace into it while ignoring `.git`, then
initializes a temporary git repository. The copy is disposable evidence for
patch composition only; source workspace mutation is forbidden.

The result is not an approval and not a merge. It is a readback product used by
the guide/operator to decide whether to apply, reject, reorder, or request
revision for individual patch proposals.

## Acceptance Criteria

This gate may close when:

1. a passing two-patch composition preflight reports `ok=true`, both patches
   applicable, and source workspace unchanged;
2. a conflicting two-patch preflight reports `ok=false` with the first failing
   patch and git stderr evidence;
3. touched path collisions are reported even when patches are sequentially
   applicable;
4. the CLI exposes the same helper without mutating source workspace;
5. focused validation passes.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_composition.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "worker_patch_composition" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched worker patch composition files>
```

## Residual Risk After Close

This slice should prove ordered fan-in preflight for multiple worker patch
proposals. It will not yet apply a full patch set, automate reorder search,
write review dispositions, schedule cleanup, or expose Host UX controls.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/worker_patch_composition.py`.
- New helper: `preflight_worker_patch_composition()`.
- New models:
  - `WorkerPatchCompositionRef`
  - `WorkerPatchCompositionStep`
  - `WorkerPatchCompositionPreflightResult`
- New parser: `worker_patch_composition_refs_from_tokens()`.
- The helper loads exact `worker_patch_review_proposal` artifacts, validates
  `patch_state=has_patch`, extracts `git_diff` evidence, copies the source
  workspace into a temporary workspace, initializes a temporary git repository,
  then applies patches in caller order inside that temporary workspace.
- The result reports per-step git check/apply status, failed ref, and touched
  path collisions while keeping `source_workspace_mutated=false`.

CLI:

- Added `doc-based-coding scheduler preflight-worker-patch-composition`.
- The CLI requires at least two `--patch-ref ARTIFACT_ID@VERSION` values and
  explicit `--source-workspace-root`.
- Optional `--scratch-root` chooses the parent directory for disposable
  preflight workspaces.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_composition.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "worker_patch_composition" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py -k "worker_patch_review or consume_worker_patch_review or action_candidate or consume_accepted_merge_candidate or agent_exchange_action_candidates or worker_patch_composition" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

Observed results:

```text
4 passed, 388 deselected
13 passed, 457 deselected
```
