# Planning Gate - Continuous Worker Delivery Lease Minimum

Date: 2026-06-30

Status: COMPLETED

## Purpose

This document closes Continuous Worker Ownership Slice C. The slice implements
the minimum durable delivery lease mechanism needed to keep one continuous
worker binding from being selected or run by two concurrent deliveries.

The slice is intentionally narrow. It does not implement lane ownership
tooling, private storage allocation, auto compact execution, `llm-auto`,
monitoring UI, provider calls, server/API session promotion, or a scheduler
strategy rewrite.

## Source Documents

- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`
- `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`

## Implementation

Implemented in `src/runtime/orchestration/continuous_worker_binding.py`:

1. Added durable delivery lease ledger schema:
   `DeliveryLeaseLedger`.
2. Added append-only compact audit event schema:
   `DeliveryLeaseEventRecord` and `JsonlDeliveryLeaseEventLog`.
3. Added public lease operations:
   `reserve_delivery_lease()`, `begin_delivery_lease_run()`,
   `complete_delivery_lease()`, `fail_delivery_lease_retryable()`,
   `fail_delivery_lease_terminal()`, `expire_delivery_lease()`,
   `release_delivery_lease()`, and `inspect_delivery_leases()`.
4. Added durable read/write helpers:
   `read_delivery_lease_ledger()` and `write_delivery_lease_ledger()`.
5. Added `binding_has_active_delivery_lease()` for delivery-time selection.
6. Kept the active lease definition as `reserved|running`.
7. Added a non-active durable `released` lease status so `releaseLease`
   preserves compact audit evidence instead of deleting the record.
8. Kept raw transcript and secret-like data rejected from lease payloads,
   transition metadata, and lease event logs.

Implemented in `src/runtime/orchestration/leader_worker_codex_delivery.py`:

1. Added request paths for the continuous-worker delivery lease ledger and
   event log.
2. During OpenCode continuous-worker binding lookup, skip a resolved binding
   when the lease ledger already has an active lease for that binding.
3. Reserve a lease only after delivery preparation succeeds.
4. Mark the lease `running` when runtime invocation begins.
5. Mark the lease `completed` on successful delivery.
6. Mark the lease `failed_retryable` or `failed_terminal` on runtime failure.
7. Preserve existing same-batch duplicate binding protection.

Implemented in `src/runtime/orchestration/codex_delivery_smoke.py`:

1. Added lease ledger and lease event log path pass-through for OpenCode smoke
   and bounded-loop delivery surfaces.

Exported the new lease symbols through `src/runtime/orchestration/__init__.py`.

## Contract Decisions

`releaseLease` is represented by durable status `released`, not by deleting a
lease row. This keeps the binding available for a new reserve while preserving
who released the lease and when.

Lease failure records remain compact. They store `failure_kind`, result or
invocation refs, runtime ids, and audit refs, but do not persist raw provider
transcripts or secret values.

The delivery supervisor enforcement is deliberately minimal:

- it only runs on the existing OpenCode continuous-worker binding lookup path;
- it does not alter candidate ordering;
- it does not implement lane ownership policy;
- it does not create or promote continuous worker bindings.

## Non-Goals Confirmed

This slice did not:

1. add Lane Ownership CLI/MCP/tooling;
2. allocate private storage folders;
3. implement auto compact;
4. implement `llm-auto`;
5. touch monitoring UI;
6. call real OpenCode, Codex, Qoder, or other providers;
7. promote server/API-created sessions to continuous workers;
8. rewrite scheduler readiness or candidate selection strategy.

## Validation

Validation passed on 2026-06-30:

```text
python -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/__init__.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_delivery_lease" -q
4 passed, 425 deselected

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or continuous_worker_ownership_schema or continuous_worker_delivery_lease" -q
19 passed, 410 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or worker_binding_blocks_same_session or opencode_bounded_loop_reuses_same_continuous_worker or marks_continuous_worker_binding_stale or active_delivery_lease" -q
6 passed, 423 deselected
```

Focused tests cover:

1. empty/read/write ledger behavior through reserve/readback;
2. reserve success;
3. second active reserve conflict for the same binding;
4. completed/released lease no longer blocking new reserve;
5. failed retryable lease no longer blocking new reserve;
6. secret/raw transcript rejection;
7. successful supervisor delivery producing reserved -> running -> completed
   lease evidence;
8. retryable runtime failure producing reserved -> running -> failed_retryable
   lease evidence;
9. supervisor skip when an already active durable lease exists.

## Next Recommended Slice

Slice D should be `Lane Ownership Tooling`: add host/leader-owned claim,
inspect, suspend, resume, transfer, and release surfaces for lane ownership.
Keep it separate from provider execution, private storage directory creation,
auto compact, `llm-auto`, and monitoring UI.
