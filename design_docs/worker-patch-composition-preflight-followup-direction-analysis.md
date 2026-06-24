# Worker Patch Composition Preflight Follow-up Direction Analysis

> Date: 2026-06-24
> Status: direction analysis

## Trigger

`Worker Patch Composition Preflight` has closed:

- Planning gate:
  `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`
- Commit: `cd31275 feat: preflight worker patch composition`

The current guide-worker/Codex worker writeback path can now:

1. run planned lane-bound workers through host-owned Codex CLI wrapper;
2. allocate git-worktree worker sandboxes;
3. publish one review-only `worker_patch_review_proposal` per worker;
4. consume one accepted worker patch proposal through explicit
   `check` / `apply` / `reject`;
5. preflight multiple worker patch proposals in caller order without mutating
   the source workspace.

The next step should stay narrow. The preflight result is still only a
readback product; it is not an approval, not a merge, and not cleanup.

## Current Facts

- `preflight_worker_patch_composition()` reports ordered applicability,
  first-failing patch, and touched-path collisions in a temporary workspace.
- `consume_worker_patch_review_decision()` remains the only source-workspace
  patch apply/reject consumer, and it handles one accepted patch proposal.
- Worker patch proposals still surface through `merge_candidate` readback with
  recommended target surface `workerPatchReview`.
- Sandbox cleanup remains a separate explicit `scheduler cleanup-receipts`
  workflow.
- MCP guide-worker execution remains fake-only; live Codex/Qoder execution is
  host-owned CLI/runtime wrapper territory.
- Host UX does not yet expose a review workflow for worker patch proposals,
  composition preflight, or cleanup hints.

## Candidate 1: Host UX Patch Review Binding

Do:

1. surface worker patch proposals in Host UX as reviewable patch cards;
2. show proposal state, worker/lane/task refs, changed paths, and patch
   artifact id/version;
3. expose explicit `check`, `reject`, and single-patch `apply` actions through
   existing CLI/backend consumers;
4. show composition preflight status when multiple proposals are selected;
5. keep all operations explicit and preserve current MCP fake-only boundary.

Why:

- This is the highest user-facing gap after backend patch products exist.
- It makes the current review-only design operable without inventing
  multi-patch apply policy too early.
- It can reuse existing runtime/CLI surfaces instead of adding new mutation
  semantics.

Risks:

- UI needs screenshot validation.
- The UX must not imply that `merge_candidate` acceptance automatically applies
  a worker patch.
- Multi-selection must not silently become multi-patch apply.

## Candidate 2: Cleanup-after-review Automation Policy

Do:

1. define when a worker sandbox may be cleaned after patch apply/reject;
2. connect patch proposal lifecycle states to cleanup receipt selection;
3. provide a bounded operator helper that suggests or runs explicit cleanup
   over eligible sandbox receipts;
4. preserve review evidence before cleanup.

Why:

- Worker git-worktree sandboxes will accumulate quickly once real Codex worker
  runs become common.
- Cleanup is currently intentionally separate but still operator-heavy.

Risks:

- Cleanup is destructive relative to worker sandbox artifacts, so the policy
  needs stronger evidence and safety gates than patch preflight.
- Premature automation may remove useful debug context before Host UX review is
  comfortable.

## Candidate 3: Multi-patch Apply Policy

Do:

1. consume a successful composition preflight and exact accepted patch
   dispositions;
2. apply a full ordered patch set to an explicit source workspace;
3. transition each source worker patch proposal lifecycle deterministically;
4. fail closed if preflight is absent, stale, or does not match the requested
   patch order/source workspace.

Why:

- It closes the backend fan-in loop after composition preflight.
- It is necessary before truly parallel worker lanes can merge through one
  operator action.

Risks:

- It is a stronger mutation surface than current single-patch apply.
- It needs a clear stale-preflight identity model and likely a durable preflight
  artifact, not just a transient CLI result.
- It should probably come after Host UX or at least after a contract gate that
  defines how operators inspect the preflight evidence.

## Candidate 4: Agent Storage Isolation

Do:

1. move from storage binding evidence toward real agent home / scratch
   lifecycle primitives;
2. define persistent home registration and temporary scratch cleanup for real
   worker agents;
3. connect storage lifecycle to scheduler runs and guide-worker lanes.

Why:

- Larger agent collaboration eventually needs stronger private storage and
  lifecycle isolation.
- This is orthogonal to patch review but important before broader multi-agent
  scale.

Risks:

- It is a bigger architectural slice than the current patch-review fan-in path.
- It does not immediately improve the newly added worker patch composition
  capability.

## Recommendation

Default next gate:

> Host UX Patch Review Binding

Reason:

The backend now has enough patch proposal, single-patch consume, and multi-patch
preflight surfaces to make review visible and operable. Adding multi-patch
apply before a review UI risks creating a powerful mutation surface whose
evidence operators cannot comfortably inspect. Cleanup automation also depends
on a clearer review outcome loop. Agent storage isolation remains important,
but it is not the tightest continuation of the worker patch fan-in path.

## Proposed Next Planning Gate Boundary

Name:

> Host UX Worker Patch Review Binding

Initial scope:

1. read worker patch proposals from existing ExchangeArtifact/action-candidate
   surfaces;
2. display task/lane/worker/provider/sandbox refs, lifecycle state, changed
   paths, and patch artifact ref;
3. run existing CLI/backend single-patch `check` and `reject` actions from UI;
4. provide a non-mutating multi-selection preflight action over selected patch
   refs;
5. display preflight result, first failure, and touched-path collisions;
6. keep `apply` explicit and conservative; if included, only call the existing
   single-patch apply consumer and label it clearly as source workspace
   mutation;
7. validate with focused tests and screenshot-based Host UX verification.

Non-goals:

1. no automatic multi-patch apply;
2. no automatic ordering algorithm;
3. no sandbox cleanup execution;
4. no live provider execution through MCP;
5. no persistent agent home/scratch implementation.
