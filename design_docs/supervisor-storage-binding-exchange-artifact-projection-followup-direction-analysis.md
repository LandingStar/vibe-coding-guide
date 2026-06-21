# Supervisor Storage Binding ExchangeArtifact Projection Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-exchange-artifact-projection.md`
closed with a compact `SupervisorStorageBindingEvidenceSummary` to
`ExchangeArtifact` projection.

Review evidence:

- `review/supervisor-storage-binding-exchange-artifact-projection-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. deterministic supervisor dogfood workflow;
2. supervisor run identity and host/session/run readback;
3. supervisor storage/context binding product;
4. durable supervisor storage binding evidence JSON;
5. compact evidence summary readback;
6. compact exchange artifact projection that validates and can be written to
   the exact-version artifact store.

The projected artifact is a coordination product, but downstream tasks do not
yet have a narrow, explicit way to declare that they consume a specific binding
artifact version.

## Candidate A - Exact-Version Admission Readiness For Binding Artifacts

### Goal

Define the minimal contract that lets a downstream scheduler task declare a
specific supervisor storage binding artifact version as an input dependency.

### Why Useful

This would make the binding projection operational for coordination without
requiring tasks to inspect raw evidence JSON or workflow internals.

### Boundary

Keep it exact-version and read-only. Do not automatically schedule downstream
work, mark artifacts consumed, create storage directories, write scratch
manifests, refresh projection, or mutate Local Work Trajectory.

## Candidate B - MCP Resource Readback For Binding Artifacts

### Goal

Expose projected supervisor storage binding artifacts through existing MCP
resource/inspection patterns.

### Why Useful

Codex and other hosts could inspect the exact projected product from the
artifact store before admission semantics are expanded.

### Boundary

Read-only resource exposure only. No scheduler mutation and no Host UX controls.

## Candidate C - Host UX Binding Artifact Visibility

### Goal

Show projected binding artifacts in the operator UI.

### Why Useful

Operators should eventually see which storage/context binding artifacts are
available for downstream work.

### Boundary

This should stay downstream of a backend artifact/readback contract and requires
screenshot validation.

## Recommendation

My current preference is Candidate A:

```text
Exact-Version Admission Readiness For Supervisor Storage Binding Artifacts
```

Reason:

1. the artifact projection already validates and writes to the versioned store;
2. coordination value appears when downstream work can depend on an exact
   binding artifact version;
3. this preserves the backend-first sequence and leaves UI downstream;
4. it can remain a narrow contract/readiness slice without creating storage
   directories or mutating scheduler state beyond existing explicit admission
   paths.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-artifact-admission-readiness.md`

Suggested first slice:

1. define how a scheduler task or batch submission references a specific
   supervisor storage binding artifact id/version;
2. validate that the referenced artifact exists and has the expected compact
   product type;
3. preserve exact-version semantics and avoid raw evidence payload reads unless
   explicitly requested;
4. add focused tests for valid/missing/wrong-product references;
5. do not add Host UX, live provider, storage directory creation, cleanup, or
   Local Work Trajectory mutation.
