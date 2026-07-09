# Log-like Record Standard Draft

## Document Position

This is an internal tooling draft for log-like records across the
doc-based-coding platform.

It is not yet an authoritative `docs/` contract. It should guide near-term
implementation and review of runtime logs, audit receipts, scheduler events,
agent communication records, validation records, trajectory records, and other
append/readback products. After enough practice, promote the stable parts into a
formal platform document under `docs/`.

Related existing contract:

- `docs/runtime-log-decoration-contract.md`

That contract defines the bottom-layer decoration/projection mechanism. This
draft defines the higher-level expectations for what log-like records should
contain and how readable/auditable they should be.

## Problem

The project has many record families:

- decision logs
- runtime invocation logs
- scheduler events
- leader-worker dispatcher and delivery events
- ExchangeArtifact logs and communication history
- worker reports and worker trajectory suggestions
- Local Work Trajectory mutations
- validation, doctor, and self-check receipts
- UI screenshot/evidence records
- sandbox, cleanup, and host evidence receipts

These records are useful, but their shape, readability, and cross-reference
behavior are inconsistent. A reviewer often has to inspect multiple JSON/JSONL
files, infer which records belong together, compare timestamps, and decode
surface-specific fields before understanding what happened.

This draft standardizes expectations without requiring one universal schema for
all record kinds.

## Design Principle

Use a shared base envelope plus domain-specific profiles.

Do not force every log family into one giant schema. Every record family may
keep its own domain fields, but it should expose enough common envelope and
reference fields for humans, models, monitoring UI, and audit tools to build a
clear story.

## Base Envelope

Every new or revised log-like record SHOULD expose these fields, either directly
or through a stable adapter/readback projection:

```text
schema_version
record_id
record_kind
timestamp
actor
action
status
summary
reason
run_id
correlation_id
subject_refs
input_refs
output_refs
evidence_refs
related_record_ids
next_hint
sensitivity
redaction_state
raw_payload_persisted
```

Field expectations:

- `schema_version`: stable version for this record family.
- `record_id`: unique within its log family.
- `record_kind`: compact type name, such as `runtime_invocation`,
  `scheduler_event`, `worker_report`, or `validation_receipt`.
- `timestamp`: ISO-8601 timestamp with timezone.
- `actor`: agent, host, tool, user-facing surface, or system component that
  produced the record.
- `action`: verb-like action, such as `dispatch_worker`, `run_provider`,
  `validate`, `write_report`, `advance_trajectory`, or `capture_screenshot`.
- `status`: normalized lifecycle/status value where practical, such as
  `started`, `succeeded`, `failed`, `blocked`, `waiting`, `skipped`,
  `partial`, `accepted`, `rejected`, or `consumed`.
- `summary`: bounded human-readable one-sentence description.
- `reason`: required for `failed`, `blocked`, `waiting`, `skipped`, permission
  denial, fallback, retry, compaction, and path-resolution records.
- `run_id`: task/run boundary id when the record belongs to a specific run.
- `correlation_id`: cross-product id for grouping records that are causally
  related but may not share one run boundary.
- `subject_refs`: the things this record is about, such as task, lane, worker,
  trajectory event, artifact, file, screenshot, provider session, or progress
  node refs.
- `input_refs`: inputs consumed by the action.
- `output_refs`: outputs produced by the action.
- `evidence_refs`: durable evidence paths or artifact refs that support the
  record.
- `related_record_ids`: adjacent records that help reconstruct the story.
- `next_hint`: where a human/model should look next when auditing or debugging.
- `sensitivity`: compact classification, such as `public`, `internal`,
  `sensitive`, or `secret-bearing-redacted`.
- `redaction_state`: `not_needed`, `redacted`, `contains_no_raw_secret`,
  `requires_review`, or similar.
- `raw_payload_persisted`: boolean. Runtime transcripts, provider raw output,
  command raw stdout/stderr, and secret-bearing payloads should normally be
  `false`.

## Readability Contract

Every important record should be useful when read alone.

Minimum human-readable requirements:

- `summary` MUST explain the event without requiring the reader to decode
  domain-specific field names.
- `reason` MUST be present when something did not follow the ordinary success
  path.
- `next_hint` SHOULD point to a useful inspection surface, report, or evidence
  file when the record is not self-contained.
- Status values SHOULD be normalized enough for simple filtering.
- Large nested payloads SHOULD be summarized by ids, counts, statuses, and
  bounded text rather than copied wholesale.
- A log family SHOULD provide a compact readback or summary product when raw
  JSONL is too noisy for routine review.

Bad pattern:

```json
{ "event_kind": "x", "metadata": { "a": "...many details..." } }
```

Better pattern:

```json
{
  "record_kind": "scheduler_event",
  "action": "mark_task_waiting",
  "status": "waiting",
  "summary": "Task frontend waits for engine-api to complete.",
  "reason": "Dependency dep-engine-api-front-end requires source task complete.",
  "subject_refs": [{"kind": "task", "id": "task:frontend"}],
  "input_refs": [{"kind": "dependency", "id": "dep-engine-api-front-end"}],
  "next_hint": "Inspect scheduler state for task:engine-api."
}
```

## Reference Contract

References should be structured enough to survive movement between tools.

Recommended shape:

```json
{
  "kind": "artifact|file|task|lane|worker|trajectory|event|provider_session|screenshot|command",
  "id": "stable-id-if-any",
  "path": "relative-or-absolute-path-if-needed",
  "version": "optional-version",
  "label": "short human label",
  "role": "input|output|evidence|subject|related"
}
```

Guidance:

- Prefer workspace-relative paths for project artifacts.
- Use absolute paths only when the artifact is explicitly outside the workspace
  or the record is an environment/provisioning receipt.
- Do not use plain path strings when the role or artifact kind matters.
- For ExchangeArtifact, scheduler task, trajectory, worker binding, and runtime
  session refs, keep stable ids even when files move.

## Redaction And Sensitivity Contract

This draft inherits secret-handling expectations from:

- `design_docs/tooling/Secret Hygiene and Log Redaction Standard.md`

Additional log-like record rules:

- Records MUST NOT persist raw secrets.
- Records SHOULD NOT persist raw provider transcripts by default.
- Command stdout/stderr SHOULD be summarized with byte counts and bounded
  summaries unless explicitly promoted to a safe evidence artifact.
- If a record summarizes a secret-bearing action, preserve structure and redact
  values.
- Adapters and readbacks MUST avoid turning compact logs into a second channel
  for arbitrary raw metadata.

## Retention And Compaction Contract

Log families should declare their intended lifecycle:

- `durable_audit`: retained as part of the workspace audit trail.
- `runtime_recent`: retained while useful, then compacted.
- `debug_ephemeral`: may be deleted after validation or safe stop.
- `derived_projection`: can be regenerated from source records.

Compaction must preserve:

- record family and schema version
- time range
- run/correlation ids
- actors and subjects
- terminal status
- failure/blocking/skipped reasons
- evidence refs
- any security/redaction decisions

For future LLM-assisted compaction, forced compaction must record why it
overrode or bypassed model judgment and retain enough before/after evidence to
improve the compactor.

## Domain Profiles

Each domain profile extends the base envelope with its own required fields.

### Decision Log

Required domain fields:

- decision id / trace id
- intent
- gate
- decision
- constraint violations
- pack names / versions

Readability focus:

- explain why the action was allowed, blocked, or sent to review
- point to any violated rule or governing pack

### Runtime Invocation

Required domain fields:

- provider
- runtime surface
- invocation id
- task id / worker id / lane id when available
- attempt count
- retry policy
- final error kind
- authority split

Readability focus:

- summarize what was invoked and whether it actually ran
- make retryable/non-retryable status obvious
- never persist raw transcript text by default

### Scheduler Event

Required domain fields:

- task id
- from/to state
- dependency refs
- lease refs
- output artifact refs

Readability focus:

- explain why a task became ready, waiting, running, complete, or failed
- separate scheduling parallelism from actual process/provider concurrency

### Exchange / Agent Communication

Required domain fields:

- artifact id and version
- producer
- audience
- lifecycle state
- intent / kind
- causality refs
- correlation id

Readability focus:

- explain who is telling whom what, and what response or action is expected
- expose mailbox/history readback without raw transcript persistence

### Worker Report

Required domain fields:

- worker id
- lane id / task id
- assigned scope
- changed surfaces
- validation evidence
- `trajectory_update` suggestions, if any

Readability focus:

- make clear what the worker claims to have completed
- keep Local Work Trajectory mutation authority with leader/main/supervisor

### Local Work Trajectory Event

Required domain fields:

- trajectory id
- lane id
- event id
- event kind
- relation kind when applicable
- anchor refs when applicable

Readability focus:

- explain why a line was opened, advanced, packed, related, merged, or closed
- distinguish visible work topology from scheduler/provider execution evidence

### Validation / Doctor / Self-check Receipt

Required domain fields:

- command or check profile
- checked surfaces
- pass/fail/warn counts
- blocking findings
- evidence refs

Readability focus:

- make the final verdict obvious
- list what was not checked
- point to remediation docs or next checks

### UI Screenshot Evidence

Required domain fields:

- screenshot path
- viewport
- route/page/state under test
- assertion summary
- related test command

Readability focus:

- explain what visual state the screenshot proves
- distinguish visual inspection evidence from unit/API test evidence

### Sandbox / Cleanup / Host Evidence Receipt

Required domain fields:

- sandbox/allocation id
- provider
- workspace/worktree refs
- cleanup lifecycle
- retained evidence refs
- deleted/archived scope summary

Readability focus:

- make it clear what was isolated, retained, deleted, or left for review
- avoid storing raw path dumps unless needed for audit

## Adoption Guidance

Near-term work should use this draft as a checklist:

1. New log-like records expose the base envelope or an adapter projection to it.
2. Existing records get adapters/readbacks before invasive storage migration.
3. Human-facing inspection commands prefer summary/readback products over raw
   JSONL dumps.
4. Tests verify at least one success and one non-success readability path for
   each important record family.
5. Runtime log decoration stays readback/projection oriented unless a separate
   gate explicitly changes persistence authority.

## Open Questions

- Should `run_id` become mandatory for all task-like records, or only for
  execution/test runs?
- Should there be a repository-level run index that groups all records by
  `run_id`?
- Which existing log families should be migrated first: runtime invocation,
  scheduler, ExchangeArtifact history, or validation receipts?
- How should monitoring UI distinguish source records from derived projections?

## Promotion Todo

After multiple implementation slices use this draft successfully, extract the
stable base envelope, readability contract, reference contract, and redaction
rules into an authoritative `docs/` platform contract. Keep domain-specific
profiles either in that contract or in separate companion docs, depending on
how much they stabilize.
