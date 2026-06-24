# Host UX Worker Patch Review Binding

> Date: 2026-06-25
> Status: IMPLEMENTED

## Trigger

`Worker Patch Composition Preflight` closed the backend fan-in preflight for
multiple `worker_patch_review_proposal` artifacts, but the operator still lacks
a Host UX surface for reviewing those proposals.

Direction source:

- `design_docs/worker-patch-composition-preflight-followup-direction-analysis.md`

## Goal

Bind the existing worker patch review products into the VS Code Host UX so an
operator can inspect proposal cards, run single-patch check/reject, and run a
non-mutating composition preflight over selected patches.

## Scope

This gate includes:

1. read worker patch proposals from the existing ExchangeArtifact/action
   candidate surfaces;
2. display artifact id/version, lifecycle, task/lane/worker/provider clues,
   patch state, changed paths, and target relation clues;
3. run a single-patch `check` through the accepted-disposition plus
   `consume-worker-patch-review` path;
4. run a single-patch `reject` through the accepted-disposition plus
   `consume-worker-patch-review` path;
5. run multi-selection composition preflight through
   `scheduler preflight-worker-patch-composition`;
6. report first failure and touched-path collisions from preflight results;
7. validate the Host UX binding with focused tests and screenshot-style
   browser verification.

## Non-goals

This gate does not:

1. apply a patch to the source workspace from Host UX;
2. apply multiple patches as one operation;
3. decide or reorder patch composition automatically;
4. clean worker sandboxes after review;
5. run live providers through MCP;
6. mutate agent-owned Local Work Trajectory from runtime or UI code.

## Contract

Worker patch proposals remain `merge_candidate` action candidates with:

- `suggested_next_surface="workerPatchReview"`;
- exact artifact source formatted as `ARTIFACT_ID@VERSION`;
- structured payload `product_type="worker_patch_review_proposal"`.

Host UX actions must preserve the current review chain:

1. write an accepted `agent_exchange_action_candidate_disposition` artifact for
   the selected candidate;
2. consume that accepted disposition through the worker patch review consumer;
3. expose the resulting mutation authority split to the operator.

For `check`, the source workspace may only be used for `git apply --check` and
the proposal lifecycle may move to `accepted` on success.

For `reject`, no git apply/check may run and the proposal lifecycle may move to
`rejected`.

For composition preflight, selected exact patch refs are applied only inside a
temporary workspace copied from the source workspace.

## Validation Plan

- Focused Python runtime/CLI tests for the operator helper.
- Focused TypeScript Host UX contract/render tests.
- Screenshot-style browser verification of the rendered worker patch review
  panel under `output/playwright/host-ux-worker-patch-review-binding/`.
- `git diff --check`.
- Doc-loop validation and change analysis if the touched surface requires it.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/worker_patch_review_operator.py`.
- New helper: `review_worker_patch_action_candidate()`.
- New result model: `WorkerPatchReviewOperatorResult`.
- The helper writes an accepted
  `agent_exchange_action_candidate_disposition` for one worker patch
  `merge_candidate`, then consumes that disposition through the existing
  worker patch review consumer.
- The operator helper is intentionally narrowed to `check|reject`; source
  workspace `apply` remains available only through the lower-level
  `consume-worker-patch-review` CLI/runtime consumer.

CLI:

- Added `doc-based-coding scheduler review-worker-patch`.
- The command requires `--candidate-id` and `--action check|reject`.
- `check` requires `--source-workspace-root` and runs `git apply --check`
  through the existing consumer without applying the patch.
- `reject` does not require a source workspace and does not run git apply.

Host UX:

- Scheduler Operator workflow now reads
  `dbc://agent-exchange/action-candidates` for worker patch candidates.
- Worker patch proposal cards show artifact ref, lifecycle, worker/lane/task
  clues, runtime/sandbox clues, patch state, changed paths, relation targets,
  and candidate reasons.
- UI actions exposed:
  - `Check` -> `scheduler review-worker-patch --action check`
  - `Reject` -> `scheduler review-worker-patch --action reject`
  - `Preflight selected patches` ->
    `scheduler preflight-worker-patch-composition`
- No Host UX `Apply` button is exposed in this slice.

Fixture:

- Added `vscode-extension/scripts/build-worker-patch-review-fixture.mjs` for
  screenshot-style verification of the rendered worker patch review panel.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\worker_patch_review_operator.py src\__main__.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "worker_patch_review_operator or worker_patch_review_consumer or worker_patch_composition_preflight" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "review_worker_patch or consume_worker_patch_review or preflight_worker_patch_composition or scheduler_help_includes_exchange_artifact_admission" -q
npm run build
node --test dist/test/schedulerOperatorContracts.test.js
node --test dist/test/progressGraphPreviewHtml.test.js
.\.venv\Scripts\python.exe doc-loop-vibe-coding\scripts\validate_doc_loop.py
git diff --check
```

Observed focused results:

```text
8 passed, 299 deselected
7 passed, 83 deselected
14 passed
21 passed
```

Screenshot-style verification:

```text
output/playwright/host-ux-worker-patch-review-binding/worker-patch-review-fixture.png
```

Change analysis:

```text
analyze_changes: no impact nodes and no coupling alerts
```

## Residual Risk After Close

This slice makes patch review operable from Host UX but still leaves the
stronger mutation and lifecycle policies for later gates:

1. no source-workspace apply from Host UX;
2. no multi-patch apply;
3. no automatic patch ordering or conflict resolution;
4. no sandbox cleanup automation after review;
5. no dedicated MCP/live-provider mutation surface.
