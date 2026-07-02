# Planning Gate - OpenCode Sandbox Patch Review Parity

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode already had the Codex-level worker runtime path for provider adapter,
guide-worker smoke, mixed-provider smoke, delivery-once, bounded supervisor
loop, and live concurrent worker smoke. The remaining near-term functional gap
was that Codex delivery exposed the host-owned git-worktree sandbox preflight
and review-only `worker_patch_review_proposal` publication path through its
delivery surfaces, while OpenCode delivery still presented this as unsupported
at the CLI/operator boundary.

## Scope

Close the review-only sandbox patch gap for OpenCode without treating OpenCode
as a patch merge authority:

1. allow OpenCode delivery-once to accept explicit sandbox preflight and
   worker patch publication flags;
2. allow OpenCode bounded/live loop surfaces to accept the same review-only
   sandbox preflight flags;
3. keep Codex-only CLI sandbox and approval-policy flags rejected on OpenCode
   surfaces;
4. reuse the existing provider-parametric preflight, git-worktree sandbox, and
   worker patch review artifact pipeline;
5. verify that OpenCode patch proposals record
   `runtime_provider="opencode"`;
6. update the operator guide and compact checklist.

## Non-Goals

This gate does not:

1. start or manage `opencode serve`;
2. implement long-lived OpenCode sessions;
3. expose live OpenCode provider execution through MCP;
4. auto-apply OpenCode worker patches to the source workspace;
5. make OpenCode the scheduler, leader, Local Work Trajectory owner, or patch
   merge authority;
6. rename historical `CodexDelivery...` product types.

## Implementation

Completed the OpenCode sandbox patch review parity slice:

1. `opencode-delivery-supervisor-once` now accepts:
   `--enable-sandbox-preflight`, `--workspace-root`, `--scratch-root`,
   `--git-worktree-sandbox-root`, `--git-executable`,
   `--publish-worker-patch-artifacts`,
   `--worker-patch-guide-agent-id`, and
   `--worker-patch-target-task-id`;
2. `opencode-delivery-supervisor-loop` and
   `live-opencode-concurrent-worker-smoke` accept the same review-only sandbox
   preflight options through the shared OpenCode loop parser;
3. OpenCode still rejects Codex CLI-specific `--sandbox` and
   `--ask-for-approval`;
4. OpenCode delivery reuses `build_orchestration_preflight_bundle()` and
   `build_worker_patch_review_artifact()` through the shared delivery
   supervisor, so the patch proposal product shape stays identical to Codex
   except for provider identity;
5. successful OpenCode git-worktree runs can now publish
   `worker_patch_review_proposal` artifacts with
   `runtime_provider="opencode"` and no source workspace mutation.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_publishes_git_worktree_patch_review or codex_delivery_supervisor_publishes_git_worktree_patch_review" -q
2 passed, 362 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor_help or opencode_delivery_supervisor_cli_requires_sandbox_for_patch_publish or opencode_delivery_supervisor_loop_help or opencode_delivery_supervisor_loop_cli_requires_sandbox_for_patch_publish or live_opencode_concurrent_worker_smoke_help" -q
5 passed, 127 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor or bounded_opencode_delivery_supervisor_loop or live_opencode_concurrent_worker_smoke or codex_delivery_supervisor_publishes_git_worktree_patch_review" -q
6 passed, 358 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or live_opencode_concurrent_worker_smoke" -q
12 passed, 120 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now matches Codex for the current one-shot worker runtime execution
chain: provider adapter, guide-worker smoke, mixed-provider smoke,
delivery-once, bounded loop, live concurrent smoke, result consumption,
retry/audit, lane-distinct concurrency, and review-only git-worktree patch
proposal publication.

Remaining OpenCode work is now beyond basic one-shot Codex-level parity:

1. `opencode serve` / HTTP-server runtime adapter;
2. long-lived OpenCode worker sessions;
3. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
