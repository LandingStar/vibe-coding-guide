# Planning Gate - Continuous Worker Ownership Schema Alignment

Date: 2026-06-30

Status: COMPLETED

## Purpose

This document closes Slice B for continuous worker ownership. The slice aligns
the runtime data-contract layer with the completed transition contract for lane
ownership, worker binding, delivery lease, private storage refs, and compact
policy defaults.

This is a schema/data-contract slice only. It does not implement scheduler
selection, runtime enforcement, provider calls, CLI/MCP/UI behavior, private
storage directory creation, auto compact execution, or `llm-auto` model
judgment.

## Source Documents

- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`
- `design_docs/stages/planning-gate/2026-06-29-continuous-worker-session-policy.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`

## Implementation

Implemented in `src/runtime/orchestration/continuous_worker_binding.py`:

1. Added `LaneOwnership` schema with:
   `ownership_id`, `scope_kind`, `scope_id`, `lane_ids`, `binding_id`,
   `worker_id`, `status`, `replacement_binding_id`, timestamps, `reason`,
   and `audit_refs`.
2. Added `DeliveryLease` schema with:
   `lease_id`, `binding_id`, `task_id`, `delivery_id`, `status`, timestamps,
   `failure_kind`, `result_ref`, and `audit_refs`.
3. Extended `ContinuousWorkerBinding` with:
   `generation`, `parent_binding_id`, `owned_lane_ids`,
   `private_storage_ref`, `private_storage_policy_ref`,
   `compact_policy_ref`, `compact_policy_default`, `last_compact_at`, and
   `compact_needed`.
4. Added public parsing helpers:
   `lane_ownership_from_json_dict()`,
   `delivery_lease_from_json_dict()`, and
   `continuous_worker_binding_from_json_dict()`.
5. Added pure data-layer active lease conflict helpers:
   `active_delivery_lease_conflicts()` and
   `validate_no_active_delivery_lease_conflicts()`.
6. Exported the new schema symbols through `src.runtime.orchestration`.

## Contract Decisions

Private storage remains a derived invariant for continuous worker bindings:

- no `has_private_storage` ownership boolean was added;
- `has_private_storage` is rejected on worker binding payloads;
- missing refs default to deterministic/policy references;
- no directory is created by this slice.

Compact policy remains schema-only:

- default is `auto`;
- `manual` is accepted only as an explicit policy value and cannot disable auto
  fallback;
- `llm-auto` is accepted as a future policy value/metadata slot only;
- no compact execution or model judgment is implemented.

Delivery leases remain schema-only:

- active statuses are `reserved` and `running`;
- data-layer conflict detection is available;
- no scheduler selection or runtime lease enforcement is implemented.

Secret safety is represented at the data-contract boundary:

- schema parsers reject raw transcript and secret-like fields in payload or
  metadata;
- authority split safety facts remain allowed and are not treated as persisted
  raw transcripts.

## Non-Goals Confirmed

This slice did not:

1. implement scheduler selection;
2. implement delivery lease runtime enforcement;
3. add lane ownership CLI/MCP/tooling;
4. create private storage directories;
5. implement auto compact behavior;
6. implement `llm-auto` model judgment;
7. touch monitoring UI;
8. call OpenCode, Codex, Qoder, or any other provider.

## Validation

Validation passed on 2026-06-30:

```text
python -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_ownership_schema" -q
9 passed, 415 deselected

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or continuous_worker_ownership_schema" -q
15 passed, 409 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or worker_binding_blocks_same_session or opencode_bounded_loop_reuses_same_continuous_worker or marks_continuous_worker_binding_stale" -q
4 passed, 420 deselected
```

Focused tests cover:

1. `LaneOwnership` round-trip;
2. `DeliveryLease` round-trip;
3. `ContinuousWorkerBinding` new fields round-trip;
4. rejection of `has_private_storage`;
5. default private storage refs and `auto` compact policy;
6. `manual` compact policy without disabling auto fallback;
7. `llm-auto` as future schema value only;
8. raw transcript / secret-like field rejection;
9. active delivery lease conflict detection.

## Next Recommended Slice

Slice C should be `Delivery Lease Minimum`: implement the durable compact lease
ledger or equivalent audit-backed mechanism so a binding cannot be selected by
two concurrent deliveries. Keep that slice separate from lane ownership CLI/MCP
tooling, private storage allocation, provider calls, and monitoring UI.
