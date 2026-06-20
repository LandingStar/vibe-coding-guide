# Lease And Sandbox Authorization Readback Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-lease-and-sandbox-authorization-readback.md`
closed with a read-only runtime/MCP diagnostic product:

```text
SchedulerState / snapshot / optional event-log recovery
-> schedulerAuthorizationReadback
-> task edit lease declaration + lifecycle + sandbox mount authorization facts
```

Review evidence:

- `review/lease-and-sandbox-authorization-readback-2026-06-21.md`
- `review/sandbox-mount-binding-over-acquired-leases-2026-06-21.md`
- Research navigation: `review/research-compass.md`

## Current Position

The backend authority chain is now coherent for the first metadata-only edit
lease/sandbox loop:

1. scheduler admission classifies edit lease conflicts;
2. scheduler lifecycle records requested/acquired/released/revoked/expired
   authority;
3. preflight and metadata sandbox allocation consume acquired lifecycle records;
4. MCP readback reports the resulting authorization facts without mutation.

The remaining gap is not another hidden backend primitive. It is choosing where
to spend the next slice:

```text
make the authority visible to operators
or
start real isolation enforcement
```

## Candidate A - Host UX Binding For Authorization Readback

### Goal

Bind `schedulerAuthorizationReadback` into the existing scheduler/operator panel
as a read-only diagnostic section.

### Scope

1. Reuse MCP/CLI resource-style readback from the existing Host UX layer.
2. Show task edit lease declarations, lifecycle state, and sandbox
   authorization state.
3. Surface missing/non-acquired lifecycle rejection reasons clearly.
4. Preserve existing scheduler operator actions; do not add new mutation
   buttons.
5. Add screenshot-style validation because this is UI work.

### Why Now

The readback product is already implemented and tested. Binding it into Host UX
gives immediate operator value and makes the next real-provider work easier to
debug.

### Risks

1. UI surface may become noisy if it tries to show every field.
2. Existing progress graph / scheduler operator UI has unrelated dirty work in
   the workspace, so the slice must stage exact files and verify screenshots.
3. This does not improve actual sandbox enforcement.

### Recommended Gate

`Host UX Binding For Authorization Readback`

Keep the gate visual/read-only:

```text
no provider execution
no scheduler mutation
no projection mutation beyond existing panel reload behavior
no ExchangeArtifact/admission ledger mutation
no Local Work Trajectory mutation from UI
```

## Candidate B - Real Sandbox Provider Spike

### Goal

Introduce one real sandbox provider spike that consumes the same acquired lease
authorization metadata as the shared-process provider.

### Scope

The smallest viable spike should choose exactly one provider strategy, likely
`git-worktree` before Docker or remote VM, and prove:

1. deterministic allocation directory;
2. lease-scoped writable paths;
3. read-only required mounts or equivalent materialization;
4. cleanup/retention receipt;
5. fail-closed behavior when lifecycle authorization is missing or non-acquired.

### Why Not First

This is the highest-value safety direction, but it has a larger blast radius
than readback UI. It will touch filesystem behavior, cleanup policy, and
operator expectations. The readback UI can become the diagnostic surface used
while this spike is developed.

### Risks

1. Windows path behavior and cleanup semantics can dominate the slice.
2. Worktree/provider lifecycle may need a stronger persistence model than the
   current metadata-only allocation.
3. The provider may expose missing policy decisions around denied artifacts,
   symlinks, generated files, and cleanup on failure.

### Recommended Gate If Chosen

`Git Worktree Sandbox Provider Spike Over Acquired Leases`

Keep it fake-runtime compatible and do not mix with Host UX.

## Candidate C - Scheduler Authorization Readback CLI Surface

### Goal

Expose the same readback through `doc-based-coding scheduler ...` CLI for
operators without MCP.

### Why Lower Priority

MCP already provides the Codex-facing surface, and Host UX gives the larger
product payoff. CLI is useful, but it can follow the UI or provider spike once
the desired readback presentation is clearer.

## Candidate D - Lease Expiry Sweep In Daemon Loop

### Goal

Use explicit lifecycle time inputs in daemon/scheduler loop paths so expired
leases can be swept before preflight.

### Why Lower Priority

Expiry semantics exist, but automatic sweeping changes scheduling behavior. It
should follow better operator visibility and perhaps real sandbox provider
evidence.

## Recommendation

Choose Candidate A next:

```text
Host UX Binding For Authorization Readback
```

Reason:

1. the readback product exists and is narrow;
2. operator diagnosis is the immediate missing product layer;
3. UI readback will make future real sandbox provider failures easier to
   inspect;
4. it can stay read-only and low-risk if scoped carefully;
5. screenshot validation is already a project rule for UI work.

Candidate B should remain the next backend safety candidate after the operator
readback is visible.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-ux-authorization-readback-binding.md`

Suggested narrow scope:

1. add a read-only Authorization Readback section to the scheduler/operator
   panel;
2. consume MCP/shared readback output shape without changing backend schema;
3. render compact per-task status rows for lease lifecycle and sandbox
   authorization;
4. include empty/error/loading states;
5. validate with focused tests and screenshot-style evidence.

Suggested non-goals:

1. no real sandbox provider;
2. no new scheduler mutation buttons;
3. no CLI command;
4. no provider execution;
5. no ExchangeArtifact/admission ledger mutation;
6. no Local Work Trajectory mutation from UI;
7. no scheduler readback schema expansion unless a rendering blocker is found.
