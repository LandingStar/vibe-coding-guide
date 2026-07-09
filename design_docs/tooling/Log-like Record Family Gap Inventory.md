# Log-like Record Family Gap Inventory

## Document Position

This is an internal gap inventory companion to:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `docs/runtime-log-decoration-contract.md`

It is not an implementation plan and not an authoritative `docs/` contract.
It records what the current log-like record families already provide, what is
missing for readability/audit use, and which families should be aligned first.

Date: 2026-07-07

## Scope

This first pass inspects two high-value record families:

- runtime invocation audit records
- scheduler event records

These two families are the best first targets because they sit on the main
agent-runtime execution path and directly affect debugging, monitoring UI, and
worker failure recovery.

## Current Baseline

Relevant implementation surfaces:

- `src/runtime/orchestration/runtime_invocation_audit.py`
- `src/runtime/orchestration/scheduler.py`
- `src/runtime/orchestration/scheduler_store.py`
- `src/runtime/orchestration/log_decoration_adapters.py`
- `src/runtime/orchestration/monitoring_api.py`

Relevant existing readback/adapter surfaces:

- `inspect_runtime_invocation_log()`
- `runtime_invocation_record_to_decoration_record()`
- `scheduler_event_to_decoration_record()`
- `JsonlRuntimeInvocationLog`
- `JsonlSchedulerEventLog`
- monitoring snapshot `runtimeInvocations`

## Runtime Invocation Records

### Existing Strengths

`RuntimeInvocationRecord` is already close to the draft standard in several
ways:

- durable `schema_version`
- stable `invocation_id`
- provider and runtime surface
- task, agent, session, and run clues
- start/end timestamps
- attempt count and retry policy
- per-attempt status, retryability, error kind, bounded summary, stdout/stderr
  byte counts, and metadata
- final error kind and final summary
- explicit authority split declaring no raw transcript persistence and no
  scheduler/exchange/trajectory mutation
- JSONL readback with parse errors that include file and line number
- compaction helper that archives old records
- decoration adapter for readback-only enrichment

This family is the current best example of compact runtime audit.

### Gaps Against Draft Standard

| Draft Field / Requirement | Current State | Gap |
| --- | --- | --- |
| `record_id` | `invocation_id` exists | No standard alias/projection called `record_id` in raw record |
| `record_kind` | Decoration adapter exposes `source_record_kind` | Raw record lacks explicit `record_kind=runtime_invocation` |
| `timestamp` | `started_at` and `ended_at` exist | No single primary timestamp field |
| `actor` | `agent_id` exists, adapter falls back to wrapper | Raw record does not distinguish actor role vs agent id |
| `action` | Adapter emits `runtime_invocation_<status>` | Raw record lacks action verb such as `run_provider` |
| `summary` | success often lives in attempt summary; failure in `final_summary` | Top-level success `summary` is often empty unless projected |
| `reason` | failure has `final_error_kind/final_summary` | no normalized top-level `reason`; success has no reason/diagnostic |
| `correlation_id` | sometimes derivable from invocation id or metadata | no first-class correlation field |
| `subject_refs` / `input_refs` / `output_refs` / `evidence_refs` | task/session/run/output clues exist in fields/metadata | references are not structured uniformly |
| `next_hint` | absent | reviewer must infer next inspection path |
| `sensitivity` / `redaction_state` | bounded redaction exists; authority split says raw transcript false | no explicit sensitivity or redaction state |
| `raw_payload_persisted` | authority split has `raw_transcript_persisted=false` | draft uses a broader concept; raw stdout/stderr policy is implicit |

### Readability Assessment

Current runtime invocation logs are mechanically useful and mostly safe, but
not yet ideal for human review:

- Success records can have an empty top-level `final_summary`, forcing readers
  to inspect attempts.
- Important routing details may be buried in `metadata` keys, not structured
  refs.
- A reviewer can determine what happened, but not always from one line.
- The existing decoration adapter is a good place to introduce draft-shaped
  readback before changing raw storage.

### Recommended First Alignment

Do not migrate the raw JSONL schema first.

Start with a readback/envelope projection:

- add a stable runtime-invocation draft-envelope projection in adapter/readback
  output;
- expose `summary`, `reason`, `subject_refs`, `output_refs`, `evidence_refs`,
  `next_hint`, `sensitivity`, and `redaction_state` from existing fields;
- keep raw JSONL backward compatible;
- add focused tests for success, failed non-retryable, failed retryable, and
  compacted-readback readability.

## Scheduler Event Records

### Existing Strengths

`SchedulerEvent` already records many state-machine facts:

- stable `event_id`
- `event_kind`
- timestamp
- task id
- from/to state
- reason
- run/session ids
- output artifact id/version
- dependency ids
- related artifact ids
- lease id and optional edit lease lifecycle record
- sequence
- metadata
- JSONL read/write
- replay semantics and recovery checks
- readable error if strict replay references an unknown task
- decoration adapter

This family is strong as replay/audit material for scheduler-owned task state.

### Gaps Against Draft Standard

| Draft Field / Requirement | Current State | Gap |
| --- | --- | --- |
| `schema_version` | scheduler snapshot has version; event JSONL line does not | raw event record lacks per-line schema version |
| `record_id` | `event_id` exists | no standard alias/projection in raw event |
| `record_kind` | adapter exposes `source_record_kind=scheduler_event` | raw event lacks explicit record kind |
| `actor` | adapter defaults to `scheduler` | raw event does not record producer/actor |
| `action` | event kind doubles as action | action is state-machine oriented, not always human-readable |
| `status` | to-state exists; event kind implies status | no normalized top-level status for filtering across families |
| `summary` | often absent; adapter uses `reason` as message | routine successful transitions often have empty reason/message |
| `reason` | exists | not consistently populated; sometimes only dependency ids explain waiting |
| `run_id` / `correlation_id` | run id exists; correlation id absent | no cross-product correlation id |
| `subject_refs` / `input_refs` / `output_refs` / `evidence_refs` | task/dependency/artifact/lease ids exist | refs are id lists rather than typed refs |
| `related_record_ids` | absent | event chains rely on sequence/timestamps |
| `next_hint` | absent | reviewer must infer whether to inspect task state, dependency, lease, or runtime log |
| `sensitivity` / `redaction_state` | absent | no explicit declaration, though content is usually compact |
| `raw_payload_persisted` | absent | metadata can contain unknown keys; policy is implicit |

### Readability Assessment

Scheduler events are reliable for replay but weak as standalone human-readable
records:

- Many successful lifecycle events have empty `reason`.
- `event_kind`, `from_state`, and `to_state` explain state transitions to code,
  but not always to a human.
- Dependency waits are understandable only after following dependency ids into
  the scheduler snapshot.
- Lease lifecycle data can be rich, but it is nested and not summarized.
- Audit-only events share the same event family as replay-affecting task
  events, which is technically valid but not visually obvious without knowing
  `_scheduler_event_is_audit_only()`.

### Recommended First Alignment

Scheduler should be the first storage-facing family to improve, but still via
compatible additive fields.

Recommended path:

1. Add a readback projection that emits draft-shaped records for scheduler
   events without changing JSONL persistence.
2. Add a helper that derives:
   - normalized `status`
   - one-sentence `summary`
   - required `reason` for waiting/blocked/failed/skipped/review states
   - typed refs for task, dependency, artifact, lease, run, session
   - `next_hint`
   - `replay_effect`: `state_mutating` or `audit_only`
3. After readback proves useful, add compatible raw fields for new writes:
   - `schema_version`
   - `actor`
   - `summary`
   - `correlation_id`
   - optional typed ref arrays
4. Keep replay behavior independent of the new readability fields.

## Cross-Family Findings

### Good Existing Direction

- The log decoration layer is already readback/projection oriented and avoids
  rewriting source logs.
- Runtime invocation records already include explicit authority split and raw
  transcript safety.
- Monitoring snapshot already provides frontend-friendly summaries for part of
  the runtime invocation surface.
- Scheduler replay already has strong recovery semantics and readable strict
  errors.

### Main Weakness

The project has strong machine logs but weaker human/audit envelopes.

Most existing records can answer "what did the machine do?" after inspection.
Fewer can answer "what happened, why, where should I look next?" from one
record or one compact readback.

### Most Important Standardization Gap

The most important shared missing abstraction is a typed reference envelope.

Many logs already contain ids and paths, but they use family-specific field
names. This makes monitoring UI, cross-log audit, and model-driven review
harder than necessary. A common `subject_refs/input_refs/output_refs/evidence_refs`
projection should come before large storage migrations.

## Recommended Alignment Order

1. **Scheduler event readback projection**
   - highest readability gap
   - directly helps task/lane/worker debugging
   - can be additive and non-mutating

2. **Runtime invocation readback projection**
   - already close to target
   - useful for provider/runtime failure diagnosis
   - good candidate for draft-envelope reference tests

3. **ExchangeArtifact communication history**
   - important for agent communication audit
   - already has causality/log concepts
   - should align after scheduler/runtime refs are stable

4. **Worker report and worker trajectory suggestions**
   - important for Local Work authority separation
   - should share typed refs with scheduler/trajectory records

5. **Validation/doctor/self-check receipts**
   - important for release and install troubleshooting
   - likely benefits from a compact human summary first

6. **UI screenshot and host evidence receipts**
   - important for frontend/visual validation
   - should adopt evidence refs and screenshot proof summaries

7. **Sandbox/cleanup/agent home lifecycle receipts**
   - important for safety and storage lifecycle
   - should align after ref/redaction rules are battle-tested

## Suggested Next Gate

Recommended next narrow gate:

```text
Scheduler Event Readback Envelope
```

Scope:

- implement a read-only projection from `SchedulerEvent` to the draft envelope;
- do not change JSONL persistence;
- do not change scheduler replay;
- add tests for ready/waiting/blocked/running/completed/audit-only events;
- expose enough fields for monitoring UI and CLI inspection to show readable
  summaries and next hints.

This gives the draft immediate practice while preserving compatibility.

## Non-goals For The Next Gate

- Do not migrate all historical logs.
- Do not force all record families into one schema.
- Do not change provider execution behavior.
- Do not change scheduler replay authority.
- Do not add raw transcript persistence.
- Do not make `run_id` mandatory for every historical record yet.
