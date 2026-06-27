# Planning Gate - Codex Delivery Sandbox Patch Review Closure

> Date: 2026-06-27
> Status: COMPLETED

## Trigger

The bounded Codex delivery supervisor can now activate ready scheduler tasks,
deliver Codex workers, consume successful output artifacts, surface permission
review, and retry eligible interrupted or transient failed delivery records.

The remaining boundary before using Codex delivery for real code worker tasks
is sandbox/writeback integration. The older guide-worker provider wrapper can
already export git-worktree edits as review-only
`worker_patch_review_proposal` artifacts, but the newer continuous Codex
delivery supervisor does not yet allocate a sandbox or publish patch review
products.

## Scope

Add a narrow bridge from Codex delivery supervisor success handling to the
existing sandbox and patch review products:

1. allow a Codex delivery supervisor pass to opt into orchestration preflight
   sandbox allocation;
2. support `shared-process` by default and `git-worktree` only when the host
   provides an explicit workspace root and git-worktree sandbox root;
3. pass the preflight runtime workspace to Codex CLI so a git-worktree task can
   execute in the worker sandbox;
4. after a successful Codex run, publish a review-only
   `worker_patch_review_proposal` artifact for git-worktree executions;
5. expose patch artifact refs in the supervisor record and delivery metadata;
6. keep result completion, patch review, patch apply, and sandbox cleanup as
   separate operator decisions.

## Non-Goals

This gate does not:

1. apply patches to the source workspace;
2. clean up git-worktree sandboxes automatically;
3. implement patch conflict resolution or multi-worker patch composition;
4. resume a live Codex process mid-turn;
5. expose live provider execution through MCP;
6. mutate agent-owned Local Work Trajectory from runtime code;
7. redesign scheduler edit-lease admission.

## Acceptance Criteria

This gate may close when:

1. Codex delivery supervisor requests can enable sandbox preflight with an
   explicit `workspace_root` and optional `git_worktree_sandbox_root`;
2. a git-worktree scheduled Codex task receives a runtime task whose
   `runtime_workspace_root`, `sandbox_provider`, `sandbox_allocation_id`, and
   `visible_mounts` reflect the allocated sandbox;
3. a successful git-worktree Codex delivery publishes a
   `worker_patch_review_proposal` artifact into the existing
   `JsonArtifactVersionStore`;
4. the supervisor result, JSON readback, and delivery acknowledgement metadata
   expose the patch artifact ref and patch state;
5. successful result consumption still writes `task_completed` independently
   from patch review, and no source patch is applied automatically;
6. permission-review and failed-runtime paths do not publish patch proposals;
7. default shared-process Codex delivery behavior remains compatible with the
   C1-C4 tests.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor and (patch_review or sandbox or consume_success or permission or retry)" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md design_docs/Project Master Checklist.md
```

## Residual Risk After Close

This gate should make Codex delivery review-safe for sandboxed code edits. It
will not make multi-worker patch ordering, cleanup timing, or operator UI
review flows automatic. Those remain separate product gates.

## Implemented Surface

Runtime:

- `CodexDeliverySupervisorRequest.enable_sandbox_preflight`
- `workspace_root`, `scratch_root`, `git_worktree_sandbox_root`, and
  `git_executable`
- `publish_worker_patch_artifacts`
- `worker_patch_guide_agent_id` and `worker_patch_target_task_id`
- `CodexDeliveryWorkerPatchReviewPublication`

Behavior:

- Default Codex delivery behavior remains shared-process and unchanged unless
  sandbox preflight is explicitly enabled.
- When sandbox preflight is enabled, the supervisor builds an
  `OrchestrationPreflightBundle` and passes the preflight runtime task to
  Codex CLI.
- For git-worktree sandboxes, successful Codex output can publish a
  `worker_patch_review_proposal` artifact through the existing
  `build_worker_patch_review_artifact()` helper.
- Patch proposal publication happens before successful result consumption, so
  a patch publication failure does not write `task_completed`.
- Delivery acknowledgement metadata and supervisor JSON readback include
  compact patch artifact refs without embedding the patch text.
- Patch application and sandbox cleanup remain separate explicit operator
  actions.

CLI:

- `doc-based-coding scheduler codex-delivery-supervisor-once`
- `doc-based-coding scheduler codex-delivery-supervisor-loop`

Both expose:

- `--enable-sandbox-preflight`
- `--workspace-root`
- `--scratch-root`
- `--git-worktree-sandbox-root`
- `--git-executable`
- `--publish-worker-patch-artifacts`
- `--worker-patch-guide-agent-id`
- `--worker-patch-target-task-id`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_delivery_supervisor or codex_result_consumer or codex_permission or worker_patch_review" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor or consume_worker_patch_review or review_worker_patch" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

Observed results:

```text
13 passed, 323 deselected
5 passed, 97 deselected
23 passed, 313 deselected
9 passed, 93 deselected
doc-loop validation passed
```
