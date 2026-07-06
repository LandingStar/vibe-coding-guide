# Runtime Log Decoration Contract

## Purpose

The runtime log decoration contract is a bottom-layer foundation for enriching,
validating, redacting, and rewriting compact log records.

It is intended to support ordinary runtime logs, audit readbacks, agent
communication history, review records, lane-splitting records, and future
advisory-product pools without forcing each surface to invent its own
decorator shape.

## Runtime Surface

Current module:

```text
src/runtime/orchestration/log_decoration.py
```

Exported objects:

- `LogDecorationRecord`
- `LogDecorationResult`
- `LogDecorationPipelineResult`
- `LogDecorator`
- `LogDecorationPipeline`
- `AppendFieldsLogDecorator`
- `RequiredFieldsLogDecorator`
- `BoundedTextRewriteLogDecorator`

## Contract

`LogDecorationRecord` is a neutral record shape:

```text
record_id
timestamp
actor
action
channel
message
fields
decorations
```

Decorators run in order and return `LogDecorationResult` evidence. A decorator
declares one mode:

- `append_only`: may add metadata in `decorations`;
- `validator`: may report structured errors;
- `rewrite_allowed`: may rewrite bounded text and must report the rewrite.

`LogDecorationPipelineResult` returns the final record, per-decorator evidence,
combined errors, rewrite status, and an authority split showing that the
pipeline itself does not persist logs or mutate scheduler, exchange, delivery,
provider, or Local Work Trajectory state.

## Current Limits

The contract does not yet provide:

- JSONL persistence;
- CLI or MCP surfaces;
- migration of existing event logs;
- LLM summarization;
- raw transcript storage;
- binding to advisory pools or scheduler logs.

Existing logs can adopt this contract incrementally in later slices.

## Current Adapters

Current adapter module:

```text
src/runtime/orchestration/log_decoration_adapters.py
```

Exported projection helpers:

- `log_like_record_to_decoration_record`
- `decorate_log_like_records`
- `LogLikeRecordBatchDecorationResult`
- `exchange_log_to_decoration_record`
- `coordination_event_to_decoration_record`
- `scheduler_event_to_decoration_record`
- `scheduler_merge_gate_event_to_decoration_record`
- `runtime_invocation_record_to_decoration_record`
- `agent_activation_event_to_decoration_record`
- `leader_worker_dispatcher_tick_record_to_decoration_record`
- `run_event_to_decoration_record`
- `exchange_artifact_admission_record_to_decoration_record`
- `audit_event_to_decoration_record`
- `decision_log_entry_to_decoration_record`
- `continuous_worker_binding_event_to_decoration_record`
- `lane_ownership_event_to_decoration_record`
- `delivery_lease_event_to_decoration_record`
- `leader_worker_delivery_event_to_decoration_record`
- `trajectory_team_continuity_event_to_decoration_record`
- `opencode_serve_lifecycle_receipt_to_decoration_record`
- `cleanup_receipt_to_decoration_record`
- `git_worktree_command_receipt_to_decoration_record`
- `git_worktree_sandbox_receipt_to_decoration_record`
- `sandbox_allocation_to_decoration_record`
- `sandbox_allocation_receipt_evidence_to_decoration_record`
- `sandbox_allocation_receipt_evidence_summary_to_decoration_record`

These helpers are read-only projections from existing compact log records into
`LogDecorationRecord`. They do not append to JSONL files, mutate scheduler
state, consume exchange artifacts, run providers, or write Local Work
Trajectory.

Projection keeps source identity and relation clues such as event ids, task ids,
artifact ids, run/session ids, lifecycle/status fields, and the source record
kind. It deliberately does not copy arbitrary freeform `metadata` or audit
`detail` payloads wholesale; adapters expose only key lists and bounded summary
text unless a caller explicitly passes additional bounded fields.

`log_like_record_to_decoration_record` is the generic dispatcher for supported
compact record types. It raises a readable error for unsupported records so new
log surfaces are added through explicit adapters instead of accidental
best-effort serialization.

`decorate_log_like_records` is the adapter-layer batch helper. It projects each
supported record, runs a caller-provided `LogDecorationPipeline`, returns
per-record pipeline evidence, and reports unsupported records as isolated
errors. It remains read-model-only and does not persist decoration evidence.

This makes the decoration layer suitable for common validation, redaction, and
append-only enrichment while preserving each source log's existing authority and
persistence semantics.

Receipt and evidence adapters follow a stricter projection rule than ordinary
event adapters. They expose stable ids, status fields, counts, booleans, and
key lists, but they do not copy raw command output, arbitrary metadata values,
path lists, cleanup reasons, or embedded evidence payloads into decoration
fields. This keeps the log decoration layer usable for audit/readback without
turning it into a second persistence channel for sensitive or bulky runtime
products.

Current bottom-layer receipt/evidence coverage includes OpenCode serve
lifecycle receipts, agent scratch cleanup receipts, git-worktree command and
sandbox receipts, sandbox allocations, and sandbox allocation receipt evidence
summaries. Presentation-only host evidence cards and UI read models remain out
of scope for this bottom-layer adapter set unless a future gate promotes them
to runtime-owned audit records.

## Current Readback Wiring

`inspect_runtime_invocation_log()` accepts an optional `decoration_pipeline`.
When provided, the function decorates the same latest records selected by
`latest_limit` and returns `latest_decoration_results` in
`RuntimeInvocationLogSummary`.

`build_agent_exchange_history_summary()` and
`inspect_agent_exchange_history_summary()` also accept an optional
`decoration_pipeline`. When provided, they decorate compact exchange log
entries and return `log_decoration_results` alongside the existing
`log_entries`.

This is a readback-only integration:

- the runtime invocation JSONL log is not rewritten;
- the ExchangeArtifact store is not rewritten;
- raw transcripts remain unavailable;
- scheduler, exchange, provider, and Local Work Trajectory state are not
  mutated;
- default callers that do not pass a pipeline keep the existing inspection
  behavior, with empty decoration-result lists in JSON output.
