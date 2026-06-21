# Supervisor Storage Binding Evidence Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-evidence.md`
closed with a durable evidence product and compact summary readback for
supervisor storage/context binding.

Review evidence:

- `review/supervisor-storage-binding-evidence-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. deterministic supervisor dogfood workflow;
2. stable supervisor host/session/run identity;
3. a readback-only supervisor storage binding product;
4. durable supervisor storage binding evidence JSON;
5. compact readback through the existing Host Evidence bundle path.

The binding is durable as evidence, but it is not yet a coordination artifact
that another scheduled agent can consume as an exact versioned input.

## Candidate A - ExchangeArtifact Projection For Binding Evidence

### Goal

Represent supervisor storage binding evidence as an `ExchangeArtifact` with
stable product metadata and references to the evidence file.

### Why Useful

Agent coordination needs versioned intermediate products. An `ExchangeArtifact`
projection would let downstream scheduler tasks depend on the exact binding
evidence version without reading raw workflow internals or re-deriving storage
facts from snapshots.

### Boundary

Do not schedule downstream work automatically, mark artifacts consumed, approve
homes, create directories, write scratch manifests, or mutate Local Work
Trajectory.

## Candidate B - MCP Resource Readback For Binding Evidence

### Goal

Expose supervisor storage binding evidence summaries through existing MCP
resource/resource-inspection patterns.

### Why Useful

Codex and other MCP hosts could inspect durable binding evidence without direct
filesystem reads.

### Boundary

Keep it read-only. Do not add scheduler mutation or Host UX controls.

## Candidate C - Host UX Binding Evidence Visibility

### Goal

Show supervisor storage binding evidence in the operator UI.

### Why Useful

Operators should eventually see which supervisor run owns which context session,
home registration request, and scratch-space facts.

### Boundary

Requires screenshot validation and should consume existing durable evidence /
artifact readback. It should not compute binding facts from workflow internals.

## Recommendation

My current preference is Candidate A:

```text
ExchangeArtifact Projection For Supervisor Storage Binding Evidence
```

Reason:

1. durable evidence is now stable enough to reference;
2. multi-agent coordination needs a versioned intermediate product before UI
   presentation becomes the next bottleneck;
3. this continues the backend-first sequence and keeps Host UX downstream;
4. it avoids creating private storage directories or mutating scheduler state.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-exchange-artifact-projection.md`

Suggested first slice:

1. define a narrow artifact projection helper for supervisor storage binding
   evidence summaries;
2. include evidence id/path, binding id, supervisor/session/run identity,
   context session, scheduler task/context/lane ids, home registration clue,
   scratch ids, source snapshot path, metadata, and authority facts;
3. keep payload compact and avoid embedding the raw binding payload;
4. add focused tests for artifact shape, exact evidence version references, and
   preserved non-goals;
5. do not add scheduler admission, CLI/MCP/Host UX, home/scratch directory
   creation, cleanup, projection refresh, or Local Work Trajectory mutation.
