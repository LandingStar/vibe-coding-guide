# Agent Coordination Exchange Artifact Design Record

> Date: 2026-06-16
> Status: design record

## Context

The project is moving from local work visualization toward an orchestration layer that can coordinate multiple agents.

The preferred communication style is artifact-centered:

1. Agents should not depend on unrestricted shared chat history.
2. Agent coordination should happen through auditable, versioned, and scoped intermediate products.
3. Scheduler-readable information should be structured, not hidden only in prose.
4. Raw runtime transcripts may exist for debugging, but they are not the orchestration authority.

This document defines a first-pass `ExchangeArtifact` shell and payload part taxonomy.

Related documents:

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`
- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`

## ExchangeArtifact

`ExchangeArtifact` is a coordination product created by an agent, scheduler, runtime adapter, reviewer, or workspace-registration authority.

It is not limited to instruction-style calls. A single shell can represent:

1. Query.
2. Informational update.
3. Proposal.
4. Blocker.
5. Result packet.
6. Review packet.
7. Interface contract.
8. Handoff.
9. Retention / cleanup decision.

Recommended minimal fields:

```text
ExchangeArtifact
- id
- kind
- intent
- producer
- audience
- scope
- causality
- lifecycle_state
- visibility_policy
- created_at
- version
- payload
```

### Field Notes

`kind` describes what the artifact is.

Examples:

```text
message
request
query
proposal
blocker
result
review
contract
handoff
retention
cleanup
```

`intent` describes what the artifact is trying to cause.

Examples:

```text
ask
inform
propose
require_review
request_merge
declare_blocked
unblock
supersede
request_registration
request_retention
```

`scope` should be able to reference:

```text
trajectory_id
lane_id
event_id
task_id
context_id
agent_id
runtime_session_id
```

`causality` should support:

```text
replies_to
depends_on
supersedes
caused_by
correlation_id
```

`lifecycle_state` should support:

```text
draft
proposed
accepted
rejected
consumed
superseded
archived
```

## Payload Parts

`payload.parts[]` is a multi-part list.

First-version required part types:

1. `text`
2. `structured`
3. `ref`
4. `artifact_delta`
5. `contract`
6. `evidence`
7. `relation`
8. `storage_manifest`
9. `log`

Future extension part types:

1. `media_ref`
2. `metric`
3. `secret_scan_result`
4. `permission_request`
5. `human_feedback`
6. `runtime_trace_excerpt`

## Required First-Version Parts

### text

Natural language explanation.

Use for:

1. Background.
2. Reasoning summary.
3. User-readable explanation.
4. Notes that do not directly drive scheduler state.

Rule:

> Text alone must not change scheduler state.

If content affects scheduling, review, dependency, merge, retention, or permission, it must also be represented by a structured part.

### structured

Schema-bound JSON-like content.

Use for:

1. Fielded decisions.
2. State summaries.
3. Checklists.
4. Parameters.
5. Extracted facts with provenance.

### ref

Reference to an external object without copying it.

Use for:

1. File paths.
2. Document anchors.
3. Code locations.
4. Trajectory events.
5. Scheduler runs.
6. Runtime sessions.
7. Existing artifacts.

### artifact_delta

Change-bearing output.

Use for:

1. Patch references.
2. Diff summaries.
3. Generated artifact references.
4. Changed-file manifests.
5. Candidate write-back payloads.

### contract

Coordination contract consumed by other agents or tasks.

Use for:

1. API contract.
2. Data schema.
3. Event protocol.
4. CLI surface.
5. Test interface.
6. Cross-lane dependency contract.

Contracts should be versioned. Consumers should reference the exact version they consumed.

Recommended fields:

```text
contract
- contract_id
- contract_kind
- version
- title
- producer
- consumers
- status
- schema_ref
- content
- compatibility
- supersedes
- effective_from
```

Recommended `contract_kind` values:

```text
api
data_schema
event_protocol
cli_surface
test_interface
coordination_protocol
storage_policy
```

Recommended `status` values:

```text
draft
proposed
accepted
deprecated
superseded
```

Contracts are coordination products, not hidden prompt context. A consumer should reference the exact `contract_id` and `version` it used through a `relation` or `ref` part.

### evidence

Validation or acceptance evidence.

Use for:

1. Test command result.
2. Screenshot reference.
3. Log excerpt summary.
4. Metric.
5. Manual validation note.
6. Failure reproduction evidence.

### relation

Scheduler-readable relationship declaration.

Use for:

1. Depends on.
2. Waits for.
3. Blocks.
4. Unblocks.
5. Merges into.
6. Hands off.
7. Proposes new lane.
8. Supersedes.

Rule:

> Any dependency, blocker, merge, handoff, or lane proposal must have a relation part. It must not exist only in text.

Recommended fields:

```text
relation
- relation_id
- relation_kind
- source
- target
- direction
- strength
- status
- reason
- since
- until
```

Recommended `relation_kind` values:

```text
depends_on
waits_for
blocks
unblocks
merges_into
hands_off
proposes_new_lane
approves_new_lane
supersedes
consumes_contract
produces_contract
```

Recommended `status` values:

```text
proposed
active
resolved
rejected
superseded
```

`relation.source` and `relation.target` should be typed references. They may point to tasks, trajectory events, lanes, contracts, artifacts, agents, runtime sessions, or exchange artifacts.

### storage_manifest

Agent-private storage inventory or storage decision material.

Use for:

1. Scratch manifest.
2. Archive request.
3. Cleanup receipt.
4. Private-memory candidate.
5. Home registration request support material.
6. Retention review packet support material.

This part is required because agent home and scratch space are first-class orchestration resources.

### log

Structured historical communication log entry or compact timeline segment.

Use for:

1. Historical communication management.
2. Timestamped exchange summaries.
3. Agent-to-agent coordination replay.
4. Correlating artifacts with runtime events.
5. Human-readable activity timelines.

Recommended fields:

```text
log
- timestamp
- actor
- action
- channel
- summary
- related_artifact_ids
- related_event_ids
- related_run_ids
- sequence
- clock
```

First-version required fields:

```text
timestamp
actor
action
```

These three fields are required so a historical entry can be ordered,
attributed, and classified during later communication-history review.

`log` is not the raw transcript. It is a compact coordination-history product.

Raw transcripts may be referenced through `ref` or future `runtime_trace_excerpt`, but should not be duplicated into `log` by default.

Current minimal implementation:

```text
ExchangeLog
- timestamp
- actor
- action
- channel
- summary
- related_artifact_ids
- related_event_ids
- related_run_ids
- sequence
- clock

ExchangePayloadPart(part_type="log", log=ExchangeLog(...))
CoordinationEvent.to_exchange_log()
```

The first runtime contract validates that `timestamp`, `actor`, and `action`
are present on each `log` payload part. `CoordinationEvent.to_exchange_log()`
provides the first bridge from append-only coordination history into the
exchange artifact payload shape.

## History Architecture

The project should eventually separate history into three layers:

### RawTranscript

Runtime-owned raw messages, tool calls, and model outputs.

Purpose:

1. Debugging.
2. Runtime inspection.
3. Short-term replay.

It may be sensitive, large, and retention-limited.

### CoordinationEventLog

Append-only orchestration event log.

Purpose:

1. Scheduler replay.
2. Audit.
3. Causality.
4. Agent coordination history.

This log references `ExchangeArtifact` IDs and compact `log` parts.

Current minimal implementation:

```text
JsonlCoordinationEventLog
- append(CoordinationEvent)
- read_all()
- event.to_exchange_log()
```

The first implementation is intentionally JSONL-based. It is enough for append-only audit and local tests, while avoiding a premature database dependency.

### ArtifactVersionStore

Immutable version store for exchange artifacts.

Purpose:

1. Preserve exact consumed versions.
2. Support supersession.
3. Avoid ambiguous "latest message" dependency.

Current minimal implementation:

```text
InMemoryArtifactVersionStore
- put(ExchangeArtifact)
- get(artifact_id, version)
- latest(artifact_id)
- list_versions(artifact_id)

JsonArtifactVersionStore
- put(ExchangeArtifact)
- get(artifact_id, version)
- latest(artifact_id)
- list_versions(artifact_id)

exchange_artifact_to_json_dict()
exchange_artifact_from_json_dict()
```

The in-memory implementation remains useful for runtime tests and injected
fake adapters. `JsonArtifactVersionStore` is the first local durable store: it
uses a caller-provided JSON path, validates scheduler-relevant artifact shape
before persistence, rejects overwriting an existing `(artifact_id, version)`
pair, and preserves exact artifact versions across process boundaries. It is
still a local file store, not a remote registry, database, or scheduler state
authority.

## Scheduler-Relevant Rule

Any content that affects scheduler state must be machine-readable.

Examples:

1. A blocker requires a `relation` part.
2. A new API surface requires a `contract` part.
3. A completed implementation requires `artifact_delta` and usually `evidence`.
4. A scratch cleanup request requires `storage_manifest`.
5. A historical timeline statement requires `log`.

Prose may explain these parts, but it must not be the only source of truth.

## Open Questions

1. Should `ExchangeArtifact.kind` be a fixed enum initially, or allow project-local extension?
2. Should `payload.parts[]` be ordered, typed by schema, or both?
3. Should `log` be one part per event, or allow compact timeline batches?
4. Which fields belong to `visibility_policy` in the first implementation?
5. How should `ExchangeArtifact` map to Local Work Trajectory node details without exposing private content?
