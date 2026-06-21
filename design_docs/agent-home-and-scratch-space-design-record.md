# Agent Home And Scratch Space Design Record

> Date: 2026-06-16
> Status: design record

## Context

The orchestration layer needs to distinguish three concepts that are easy to mix together:

1. Agent runtime execution.
2. Project workspace edit authority.
3. Agent-private storage.

The user clarified a target capability:

1. An agent may have an independent runtime.
2. An agent may also request a registered private folder from the workspace-registration agent.
3. After audit approval, that folder can persist as the agent's private home for capability accumulation.
4. Even without registration, an agent should have temporary private space for context and scratch files.
5. Temporary space should be archived and deleted when the agent is merged, retired, or reclaimed.

This document records that boundary. It does not implement storage.

## Layering

Agent-private storage is not the same as runtime, context, or edit authority.

```text
Agent Runtime
  owns execution session, tools, model, and runtime events

Agent Home
  owns audited persistent private files for a registered agent

Agent Scratch Space
  owns temporary private files for a run, task, or lane

Context Bundle
  owns what project context is visible for the current task

Edit Scope Lease
  owns which project artifacts may be edited
```

An agent home may improve an agent's long-term capability, but it must not bypass context visibility, project authority, or edit leases.

## Agent Home

`AgentHome` is a registered persistent private folder.

It is created only after an auditable registration flow.

Recommended fields:

```text
AgentHomeRegistration
- registration_id
- agent_id
- requested_by
- purpose
- capability_domain
- storage_scope
- requested_path_hint
- registered_path
- visibility_policy
- retention_policy
- quota
- allowed_content_types
- denied_content_types
- allowed_sources
- denied_sources
- secret_policy
- audit_state
- approved_by
- created_at
- updated_at
```

### Intended Content

An agent home may contain:

1. Agent-owned long-term notes.
2. Domain-specific checklists.
3. Private prompt fragments.
4. Tool cache that is safe to persist.
5. De-identified lessons from previous work.
6. Personal templates for recurring task types.
7. Non-authoritative indexes or summaries with provenance.

### Disallowed Content By Default

An agent home should not contain:

1. API keys, tokens, or credentials.
2. Raw sensitive user content unless explicitly approved.
3. Unauthorized copies of project source files.
4. Patches that bypass merge / review.
5. Authority-doc claims without provenance.
6. Hidden task state that should belong to the scheduler.
7. Any content that would let the agent bypass `ContextBundle` or `EditScopeLease`.

## Agent Scratch Space

`AgentScratchSpace` is temporary private storage for a run, task, or lane.

Recommended fields:

```text
AgentScratchSpace
- scratch_id
- agent_id
- run_id
- task_id
- lane_id
- context_id
- path
- created_at
- expires_at
- archive_policy
- cleanup_policy
- manifest_path
- audit_state
```

Scratch space may contain:

1. Temporary notes.
2. Short-lived context summaries.
3. Experiments.
4. Generated test data.
5. Runtime transcript excerpts.
6. Draft artifacts not yet ready for review.

Scratch space must be reviewed before any content is moved into persistent agent home.

## Lifecycle

Recommended lifecycle:

```text
agent task starts
  -> scheduler allocates scratch space

agent needs persistent capability storage
  -> emits HomeRegistrationRequest

workspace-registration agent / scheduler audits request
  -> approve / reject / require changes

if approved
  -> AgentHome is created or bound

task finishes or agent is reclaimed
  -> scratch manifest is reviewed
  -> safe archival subset is archived
  -> approved capability subset may request promotion to AgentHome
  -> remaining scratch content is deleted
```

## Required Coordination Products

This capability adds several coordination artifacts:

1. `HomeRegistrationRequest`
2. `HomeRegistrationDecision`
3. `ScratchManifest`
4. `PrivateMemoryCandidate`
5. `RetentionReviewPacket`
6. `CleanupReceipt`

These should be modeled as exchange artifacts once the coordination artifact protocol is defined.

Current code support:

`src/runtime/orchestration/agent_storage.py` now defines the first code-level
product objects for:

1. `AgentHomeRegistration`
2. `AgentScratchSpace`
3. `ScratchManifestEntry`
4. `ScratchManifest`
5. `CleanupReceipt`

It also provides mapping helpers:

1. `agent_home_registration_to_artifact()`
2. `scratch_manifest_to_artifact()`
3. `cleanup_receipt_to_artifact()`
4. `build_supervisor_agent_storage_binding()`
5. `build_supervisor_storage_binding_evidence()`
6. `supervisor_storage_binding_evidence_summary_to_artifact()`

These helpers represent storage governance products as `ExchangeArtifact`
instances using `structured`, `storage_manifest`, and `log` payload parts. The
implementation is intentionally product-only: it does not create directories,
delete files, archive scratch content, or persist agent homes.

`build_supervisor_agent_storage_binding()` is the first binding product over a
host-managed supervisor run. It connects supervisor identity and scheduler
snapshot readback to:

1. a context-session id;
2. scheduler task / context / lane ids;
3. runtime session ids from scheduler run records;
4. one `AgentHomeRegistration` request;
5. task-derived `AgentScratchSpace` records.

It remains readback-only. It does not create agent home directories, create
scratch directories, write scratch manifests, approve home registration, run
cleanup, refresh scheduler projection, or mutate Local Work Trajectory.

`build_supervisor_storage_binding_evidence()` and the companion
`write_supervisor_storage_binding_evidence()` /
`read_supervisor_storage_binding_evidence_summary()` helpers make that binding
durable as an explicit evidence JSON product under `.codex/scheduler/evidence`.
The raw evidence embeds the binding payload for audit/replay, while the summary
readback exposes compact identity, scheduler, storage, metadata, and authority
facts without embedding raw binding internals.

The durable evidence support is still product/readback-only. It does not create
agent home directories, create scratch directories, write scratch manifests,
approve home registration, run cleanup, refresh scheduler projection, mutate
scheduler state, or mutate Local Work Trajectory.

`supervisor_storage_binding_evidence_summary_to_artifact()` projects the compact
evidence summary into a valid `ExchangeArtifact` with `structured`,
`storage_manifest`, `evidence`, `ref`, and `log` parts. This makes the durable
binding evidence versionable in the existing exact-version artifact store while
still avoiding raw `binding` payload embedding in the exchange artifact.

The projection is still contract/readback-only. It does not admit scheduler
work, mark artifacts consumed, create agent home directories, create scratch
directories, write scratch manifests, approve home registration, run cleanup,
refresh scheduler projection, mutate scheduler state, or mutate Local Work
Trajectory.

## Audit Requirements

The system should record:

1. Who requested a persistent home.
2. Why the home is needed.
3. Which path was approved.
4. Which content types are allowed.
5. Which sources may be copied into it.
6. Which retention policy applies.
7. Which scratch files were archived, promoted, or deleted.

The audit trail should be separate from raw runtime transcript. It should be compact enough to survive cleanup.

## Relationship To Local Work Trajectory

Local Work Trajectory should not become the storage authority.

It may display:

1. A home registration request.
2. A registration decision.
3. A scratch cleanup / archive event.
4. A private-memory promotion decision.

It should not display or persist private content by default.

## Open Questions

1. Which agent is the default workspace-registration authority?
2. Should registered homes live under `.codex/agents/`, an instance-defined path, or a separate external storage root?
3. Which retention policy should apply to scratch content by default?
4. Should `AgentHome` be portable across workspaces or project-local by default?
5. How should secret scanning be enforced before promotion from scratch to home?
