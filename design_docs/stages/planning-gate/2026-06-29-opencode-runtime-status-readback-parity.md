# Planning Gate - OpenCode Runtime Status Readback Parity

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

Codex had a read-only operator / guide-agent status surface:
`doc-based-coding scheduler inspect-codex-runtime-status`. OpenCode already
matched the execution side for provider adapter, delivery-once, bounded loop,
live concurrency smoke, sandbox preflight, patch proposal publication, and
attach/session bridge, but it lacked the same direct status readback command.

This left OpenCode usable but less inspectable than Codex after a bounded
worker loop.

## Scope

Add OpenCode runtime status readback parity:

1. make the existing runtime status helper provider-parametric while keeping
   Codex compatibility names;
2. add OpenCode request/status wrappers and `inspect_opencode_runtime_status()`;
3. add scheduler CLI command:
   `doc-based-coding scheduler inspect-opencode-runtime-status`;
4. report scheduler task states, delivery states, runtime invocation counts,
   artifact refs, safe `next_action`, and authority split without mutation;
5. make actionable pending delivery count filter by `runtime_provider`;
6. preserve existing `inspect-codex-runtime-status` JSON compatibility,
   including the historical `actionable_pending_codex_delivery_count` field.

## Non-Goals

This gate does not:

1. run OpenCode;
2. mutate scheduler, delivery, artifact, runtime invocation, or Local Work
   Trajectory state;
3. expose raw transcripts;
4. start or manage `opencode serve`;
5. change monitoring UI contracts;
6. complete provider-generic naming cleanup for all historical
   `CodexDelivery...` product types.

## Implementation

Completed OpenCode status readback parity:

1. `src/runtime/orchestration/codex_runtime_status.py` now has generic
   `ProviderRuntimeStatusRequest`, `ProviderRuntimeStatus`, and
   `inspect_provider_runtime_status()`;
2. existing Codex classes/functions remain compatible wrappers:
   `CodexRuntimeStatusRequest`, `CodexRuntimeStatus`, and
   `inspect_codex_runtime_status()`;
3. added OpenCode wrappers:
   `OpenCodeRuntimeStatusRequest`, `OpenCodeRuntimeStatus`, and
   `inspect_opencode_runtime_status()`;
4. status JSON now includes:
   `runtime_provider`,
   `delivery.actionable_pending_delivery_count`, and
   `delivery.actionable_pending_runtime_provider`;
5. Codex JSON still includes
   `delivery.actionable_pending_codex_delivery_count`;
6. added CLI:
   `doc-based-coding scheduler inspect-opencode-runtime-status`;
7. CLI help and scheduler command list expose the new read-only surface.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_runtime_status.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_runtime_status or opencode_runtime_status" -q
2 passed, 365 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_runtime_status or opencode_runtime_status" -q
4 passed, 134 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now has Codex-level execution and readback parity for the current
host-owned worker runtime path. Remaining work is:

1. `opencode serve` / HTTP-server lifecycle contract;
2. durable long-lived OpenCode worker session lifecycle policy;
3. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
