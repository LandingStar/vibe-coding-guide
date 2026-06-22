# Supervisor Storage Binding Artifact Publish Surface Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-supervisor-storage-binding-artifact-publish-surface.md`
closed with a runtime/CLI/MCP publish surface:

```text
publish_supervisor_storage_binding_artifact_from_evidence()
doc-based-coding scheduler publish-storage-binding-artifact
schedulerStorageBindingArtifactPublish
```

The surface reads one durable `supervisor_storage_binding_evidence` summary,
projects it into one compact exact-version `supervisor_storage_binding_artifact`
`ExchangeArtifact`, and writes it to the local artifact store.

## Current Position

The storage binding coordination chain now has two adjacent but still mostly
separate proof paths:

1. `Supervisor dogfood workflow -> storage binding -> durable evidence -> publish
   compact binding artifact`.
2. `binding-consumer fixture -> binding-ref inspection -> exact admission ->
   consume -> bounded fake runtime -> projection -> Host Evidence readback`.

The second path currently seeds its compact binding artifact directly through
`seed_scheduler_operator_binding_consumer_dogfood_fixture()`. That is useful for
deterministic testing, but it does not prove that a real durable supervisor
storage binding evidence file can enter the same downstream consumer closure
through the newly added publish surface.

## Candidate A - Evidence Publish To Consumer Closure

### Goal

Build a narrow backend dogfood closure that composes the existing products:

```text
run supervisor dogfood workflow
-> build and write supervisor storage binding evidence
-> publish evidence summary into ExchangeArtifact store
-> seed or build a scheduler submission that references the published artifact
-> run binding-ref inspection, exact admission, consume, bounded fake loop,
   projection refresh, and Host Evidence readback
```

### Why Useful

This is the shortest path to prove the new publish surface is operational, not
just a standalone mutation tool. It also preserves the current backend-first
sequence and uses fake runtime, so it does not depend on live Qoder readiness.

### Boundary

Do not create agent home directories, create scratch directories, write scratch
manifests, approve persistent homes, run cleanup, run live providers, or mutate
agent-owned Local Work Trajectory. The closure may mutate only the explicit
operator workflow stores it already owns: ExchangeArtifact store, admission
ledger, scheduler snapshot/event log, projection output, and Host Evidence
files.

## Candidate B - Real Agent Home / Scratch Lifecycle

### Goal

Move from readback products into actual storage lifecycle execution: approved
home registration, scratch directory creation, manifest writing, retention
review, promotion, archival, cleanup, and cleanup receipts.

### Why Useful

This is the long-term capability implied by `design_docs/agent-home-and-scratch-space-design-record.md`.
The system eventually needs real private storage lifecycle controls, not only
binding evidence and compact artifacts.

### Boundary

This is too large for the immediate next slice. It requires path governance,
secret scanning, quota/retention policy, cleanup guarantees, and stronger
audit UX. Entering it before proving the publish-to-consumer closure would make
the storage lifecycle gate carry too many unrelated risks.

## Candidate C - Host UX / Resource Visibility For Published Binding Artifacts

### Goal

Expose published supervisor storage binding artifacts more directly in Host UX
or MCP resources, including evidence refs, home/scratch clues, and downstream
consumer status.

### Why Useful

Operators need to understand which supervisor run produced which storage
binding artifact and which scheduler task consumed it.

### Boundary

This should stay downstream of a backend closure product. UI work requires
screenshot validation and should consume an already compact readback product
rather than re-deriving storage binding facts in frontend code.

## Recommendation

My current preference is Candidate A:

```text
Evidence Publish To Consumer Closure
```

Reason:

1. it directly validates the surface that just landed;
2. it keeps the next slice fake-runtime-backed and independent of live Qoder
   credentials;
3. it composes existing supervisor, evidence, publish, binding-ref, operator
   workflow, projection, and Host Evidence products instead of inventing a new
   storage lifecycle;
4. it gives Candidate B and Candidate C a stronger acceptance baseline later.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-evidence-publish-to-consumer-closure.md`

Suggested first slice:

1. add a backend workflow helper, likely in `tools.progress_graph`, that writes
   durable supervisor storage binding evidence and publishes it with the new
   publish helper;
2. build or seed one scheduler submission whose
   `supervisor_storage_binding_artifact` input ref points at the published
   artifact id/version rather than a directly seeded fixture artifact;
3. reuse existing `schedulerOperatorWorkflow` or
   `schedulerOperatorDogfoodClosure` pieces for inspection, exact admission,
   consumed marking, bounded fake loop, projection refresh, and Host Evidence
   readback;
4. return a compact closure summary that distinguishes durable evidence,
   published artifact, consuming submission, admission, runtime, projection,
   and Host Evidence phases;
5. add focused runtime and CLI tests first; add MCP only if the backend shape is
   stable enough inside the same narrow gate;
6. keep real directory creation, scratch manifests, retention review, cleanup,
   live providers, Host UX, and Local Work Trajectory mutation as non-goals.
