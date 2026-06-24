# Planning Gate - Worker Patch Apply/Reject Policy

> Date: 2026-06-24
> Status: IMPLEMENTED

## Trigger

`Worker Patch Review Integration` now exports worker git-worktree edits as
review-only `worker_patch_review_proposal` ExchangeArtifacts and exposes them
as existing `merge_candidate` readback items. That slice deliberately stopped
before applying patches, rejecting patches, resolving conflicts, or cleaning up
worker sandboxes:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`

The next narrow gap is an explicit operator/host-owned consumer for accepted
worker patch proposals.

## Scope

Add a minimal patch proposal decision consumer:

1. read an accepted `merge_candidate` disposition exact version;
2. verify its source artifact is exactly one `worker_patch_review_proposal`;
3. support an explicit action:
   - `check`: run patch conflict/readiness check only;
   - `apply`: apply the patch to an explicitly supplied source workspace;
   - `reject`: reject the patch proposal without applying it;
4. use `git apply --check` for readiness and `git apply` only for explicit
   `apply`;
5. transition the source patch proposal lifecycle:
   - `accepted` after successful `check`;
   - `consumed` after successful `apply`;
   - `rejected` after explicit `reject`;
6. return compact evidence including source/disposition ids, changed paths,
   patch state, git command return codes, and cleanup handoff hints;
7. expose the consumer as a CLI surface over runtime code.

## Non-Goals

This gate does not:

1. automatically consume generic `merge_candidate` artifacts;
2. replace `consume-accepted-merge-candidate` or scheduler merge gates;
3. infer target workspace from the patch artifact;
4. run branch merge, rebase, or conflict resolution;
5. compose multiple worker patches;
6. clean up worker sandboxes directly;
7. expose live Codex/Qoder provider execution through MCP;
8. mutate agent-owned Local Work Trajectory from runtime or CLI code.

## Contract

The consumer requires:

- exact `disposition_artifact_id` and `disposition_version`;
- an explicit action `check`, `apply`, or `reject`;
- an explicit `source_workspace_root` for `check` and `apply`;
- an accepted disposition whose `candidate_type` is `merge_candidate`;
- a source ExchangeArtifact containing one structured payload with
  `product_type=worker_patch_review_proposal`;
- a source patch payload with `patch_state=has_patch` for `check` or `apply`.

`check` and `apply` read the patch text from the source artifact evidence part.
`reject` does not require the patch to be applicable.

## Acceptance Criteria

This gate may close when:

1. runtime tests prove `check` detects an applicable worker patch without
   mutating the source workspace;
2. runtime tests prove `apply` applies the patch and marks the patch proposal
   consumed;
3. runtime tests prove `reject` marks the patch proposal rejected without
   running `git apply`;
4. focused CLI tests prove the new surface is discoverable and can apply a
   stored worker patch proposal;
5. docs record that sandbox cleanup remains a separate explicit
   `cleanup-receipts` step;
6. focused validation passes.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_review_consumer.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "worker_patch_review_consumer or worker_patch_review_apply" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched worker patch apply/reject files>
```

## Residual Risk After Close

This slice should prove a single accepted worker patch proposal can be checked,
applied, or rejected explicitly. It will not yet solve multi-patch ordering,
cross-lane conflict policy, automatic cleanup scheduling, or Host UX review
buttons.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/worker_patch_review_consumer.py`.
- New helper: `consume_worker_patch_review_decision()`.
- New result model: `WorkerPatchReviewConsumerResult`.
- Supported actions:
  - `check`: runs `git apply --check`, leaves source workspace unchanged, and
    transitions the worker patch proposal to `accepted` on success.
  - `apply`: runs `git apply --check` followed by `git apply`, then
    transitions the worker patch proposal to `consumed` on success.
  - `reject`: transitions the worker patch proposal to `rejected` without
    running git apply.
- Target surfaces for accepted dispositions:
  `workerPatchReview`, `cli:scheduler consume-worker-patch-review`, and
  `scheduler:worker-patch-review`.
- `agentExchangeActionCandidates` still reports worker patch proposals as
  `merge_candidate`, but now suggests `workerPatchReview` instead of generic
  `mergeIntake` for this product type.

CLI:

- Added `doc-based-coding scheduler consume-worker-patch-review`.
- The CLI requires exact disposition id/version and an explicit
  `--action check|apply|reject`.
- `check` and `apply` require explicit `--source-workspace-root`.
- The command reports `cleanup_surface="scheduler cleanup-receipts"` after a
  successful apply or explicit reject; cleanup itself remains a separate
  explicit step.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_patch_review_consumer.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_cli.py -k "worker_patch_review_consumer or worker_patch_review_apply or consume_worker_patch_review" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_mcp_tools.py -k "worker_patch_review or consume_worker_patch_review or action_candidate or consume_accepted_merge_candidate or agent_exchange_action_candidates" -q
```

Observed results:

```text
5 passed, 383 deselected
14 passed, 560 deselected
```
