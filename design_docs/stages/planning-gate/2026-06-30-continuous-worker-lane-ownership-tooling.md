# Planning Gate - Continuous Worker Lane Ownership Tooling

Date: 2026-06-30

Status: COMPLETED

## Purpose

This document closes Continuous Worker Ownership Slice D. The slice implements
the minimum host/leader-owned Lane Ownership tooling needed to claim, activate,
inspect, suspend, resume, transfer, and release lane or lane-group ownership
with compact audit evidence.

The slice stays at the durable data/tooling layer. It does not implement
provider execution, Lane Ownership CLI/MCP, private storage directory creation,
auto compact, `llm-auto`, monitoring UI, server/API session promotion, or a
scheduler strategy rewrite.

## Source Documents

- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-delivery-lease-minimum.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`

## Implementation

Implemented in `src/runtime/orchestration/continuous_worker_binding.py`:

1. Added durable lane ownership ledger schema:
   `LaneOwnershipLedger`.
2. Added append-only compact audit event schema:
   `LaneOwnershipEventRecord` and `JsonlLaneOwnershipEventLog`.
3. Added public lane ownership operations:
   `claim_lane_ownership()`, `activate_lane_ownership()`,
   `inspect_lane_ownerships()`, `suspend_lane_ownership()`,
   `resume_lane_ownership()`, `transfer_lane_ownership()`, and
   `release_lane_ownership()`.
4. Added durable read/write helpers:
   `read_lane_ownership_ledger()` and `write_lane_ownership_ledger()`.
5. Added conflict helpers:
   `selectable_lane_ownership_conflicts()` and
   `validate_no_selectable_lane_ownership_conflicts()`.
6. Added `lane_ownership_allows_delivery()` for a minimal delivery-time read.
7. Rejected raw transcript and secret-like values from lane ownership payloads,
   transition metadata, and event logs.

Implemented in `src/runtime/orchestration/leader_worker_codex_delivery.py`:

1. Added `continuous_worker_lane_ownership_ledger_path` to the delivery
   supervisor request.
2. During OpenCode continuous-worker binding lookup, skip a resolved binding
   when lane ownership records exist for the lane and the binding is not a
   selectable owner.
3. Kept candidate ordering unchanged.

Implemented in `src/runtime/orchestration/codex_delivery_smoke.py`:

1. Added lane ownership ledger path pass-through for OpenCode smoke and
   bounded-loop delivery surfaces.

Exported the new lane ownership symbols through
`src/runtime/orchestration/__init__.py`.

## Contract Decisions

`claimed` and `active` are selectable ownership states. `claimed` remains
selectable so the first validation delivery can activate ownership; `active`
represents steady-state ownership.

`suspended`, `transferred`, and `released` are not selectable.

Conflict detection is lane-id based rather than only scope-id based. A
lane-group claim for `lane:server` conflicts with a lane claim for
`lane:server`, and two lane-group claims conflict when their `lane_ids`
intersect.

Repeated `claimLane` against an already selectable ownership is rejected. The
caller must use `transferOwnership`, `releaseOwnership`, or
`suspendOwnership` first.

The minimal delivery selection read is intentionally narrow:

- it only runs on the existing OpenCode continuous-worker binding lookup path;
- it does not rewrite scheduler readiness;
- it does not create ownership;
- it does not promote server/API-created sessions;
- it only prevents delivery when an existing ownership record makes the binding
  non-selectable for that lane.

## Non-Goals Confirmed

This slice did not:

1. call OpenCode, Codex, Qoder, or any provider;
2. add Lane Ownership CLI/MCP;
3. allocate private storage directories;
4. implement auto compact;
5. implement `llm-auto`;
6. touch monitoring UI;
7. rewrite scheduler strategy;
8. promote server/API-created sessions.

## Validation

Validation passed on 2026-06-30:

```text
python -m py_compile src/runtime/orchestration/continuous_worker_binding.py src/runtime/orchestration/__init__.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "lane_ownership" -q
7 passed, 428 deselected

python -m pytest tests/test_runtime_orchestration.py -k "continuous_worker_binding or continuous_worker_ownership_schema or continuous_worker_delivery_lease or lane_ownership" -q
25 passed, 410 deselected

python -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor_uses_continuous_worker_binding or worker_binding_blocks_same_session or opencode_bounded_loop_reuses_same_continuous_worker or marks_continuous_worker_binding_stale or active_delivery_lease or suspended_lane_ownership" -q
7 passed, 428 deselected
```

Two pytest runs on Windows emitted a post-success access violation stack trace
inside pytest/importlib/pathlib while still returning exit code `0`. The same
focused and adjacent selections were rerun successfully, and the crash did not
correspond to a Python assertion failure.

Focused tests cover:

1. lane ownership claim, inspect, ledger readback, and event readback;
2. lane-group claim with preserved `lane_ids`;
3. lane vs lane-group conflict on shared lane id;
4. release followed by a new claim;
5. activate, suspend, resume, transfer lifecycle transitions;
6. `suspended` and `transferred` becoming non-selectable;
7. conflict helper validation;
8. `lane_ownership_allows_delivery()` for claimed/suspended states;
9. raw transcript / secret-like metadata rejection;
10. delivery supervisor skip when lane ownership is suspended.

## Next Recommended Slice

Slice E should be `Server/API Session Promotion`: add explicit host-owned
promotion from a `server_api_created` OpenCode session into a continuous worker
binding. Keep it separate from private storage directory allocation, auto
compact, `llm-auto`, and monitoring UI.
