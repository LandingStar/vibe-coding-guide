# Scheduler Daemon Lifecycle CLI/MCP Surface Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

The previous backend slices are now closed:

- `design_docs/stages/planning-gate/2026-06-20-scheduler-event-log-compaction-and-replay-hardening.md`
- `design_docs/stages/planning-gate/2026-06-20-background-scheduler-daemon-lifecycle-protocol.md`
- `review/background-scheduler-daemon-lifecycle-protocol-2026-06-20.md`

The scheduler now has:

1. durable snapshot and JSONL event-log replay / compaction boundaries;
2. a local scheduler daemon lifecycle control file;
3. deterministic lifecycle transitions for start, heartbeat, pause, resume,
   cancel, shutdown, stale inspection, and readback;
4. `run_scheduler_daemon_lifecycle_once()` as a lifecycle-gated wrapper over
   the existing bounded daemon loop.

The remaining gap is not a background process yet. The immediate gap is that
Codex / MCP callers and local operators do not have a small, documented
read/write surface for this lifecycle control object.

## Current Surface Pattern

Existing scheduler operator surfaces already follow a stable split:

1. CLI commands under `doc-based-coding scheduler ...` provide explicit local
   operator actions and print JSON payloads.
2. MCP tools expose narrow agent-callable operations with camelCase input
   names and explicit authority-split payloads.
3. Scheduler state mutation is always separated from projection refresh unless
   a workflow command explicitly composes both.
4. Real provider execution remains host-authorized and is not exposed through
   generic MCP scheduler tools.

Relevant examples:

- `doc-based-coding scheduler inspect-state`
- `doc-based-coding scheduler tick`
- `doc-based-coding scheduler daemon-loop`
- `doc-based-coding scheduler operator-workflow`
- `schedulerProjection`
- `schedulerRunOnceAndProject`
- `schedulerOperatorWorkflow`

This direction should preserve that shape.

## Candidate A - Minimal Lifecycle CLI/MCP Read-Write Surface

### Shape

Expose lifecycle control through a narrow pair of surfaces:

CLI:

```text
doc-based-coding scheduler lifecycle inspect
doc-based-coding scheduler lifecycle start
doc-based-coding scheduler lifecycle heartbeat
doc-based-coding scheduler lifecycle pause
doc-based-coding scheduler lifecycle resume
doc-based-coding scheduler lifecycle cancel
doc-based-coding scheduler lifecycle shutdown
doc-based-coding scheduler lifecycle run-once
```

MCP:

```text
schedulerLifecycleControl
schedulerLifecycleRunOnce
```

`schedulerLifecycleControl` should accept an `action` field and map only to
deterministic lifecycle-control transitions and inspection.
`schedulerLifecycleRunOnce` should wrap `run_scheduler_daemon_lifecycle_once()`
and should remain fake-runtime only unless a later host-authorized surface is
designed.

Both surfaces should require explicit paths by default:

```text
controlPath
snapshotPath
eventLogPath
```

The CLI may provide conventional examples under `.codex/scheduler/`, but tools
should not silently invent scheduler state paths when mutating state.

### Acceptance

1. CLI can inspect, start, pause, resume, cancel, shutdown, heartbeat, and run
   one lifecycle-gated fake-runtime bounded loop.
2. MCP exposes the same lifecycle contract with explicit path parameters.
3. Read-only inspection reports missing control files cleanly without creating
   them.
4. Mutating lifecycle actions write only the lifecycle control file, except
   `run-once`, which may mutate scheduler snapshot/event log only through the
   bounded scheduler loop.
5. Cancellation is consumed before provider execution, matching the runtime
   helper.
6. Authority split explicitly reports lifecycle-control mutation, scheduler
   state mutation, provider execution, projection refresh, ExchangeArtifact
   mutation, admission-ledger mutation, and Local Work Trajectory mutation.
7. Prompt / maintenance guidance explains when agents should call lifecycle
   tools and when they should not.

### Pros

1. Turns the lifecycle contract into an actually usable Codex/MCP facility.
2. Keeps the next step narrow and testable.
3. Preserves existing scheduler authority boundaries.
4. Gives later daemon hosting or UI binding a stable operator API to consume.

### Risks

1. A single MCP control tool with an `action` field can become too broad if it
   starts accepting workflow composition.
2. `run-once` can be misunderstood as a persistent daemon if names or payloads
   are vague.
3. Default paths can create hidden workspace coupling if mutating tools invent
   them silently.

### Fit

High. This is the recommended next slice.

## Candidate B - CLI Only First

### Shape

Expose lifecycle control only through `doc-based-coding scheduler lifecycle ...`
and leave MCP tools for a later slice.

### Pros

1. Lower immediate MCP schema and server registration surface.
2. Useful for operator debugging and local dogfood.

### Risks

1. Codex/agent workflows still cannot directly use the lifecycle control
   contract through MCP.
2. A later MCP slice may diverge from CLI if the contract is not designed
   together.

### Fit

Medium. Good if MCP surface churn is a concern, but weaker for the current
Codex-first support goal.

## Candidate C - Host UX Binding First

### Shape

Bind lifecycle controls into the existing VS Code Scheduler Operator Host UX.

### Pros

1. Makes lifecycle state visible to human operators.
2. Reuses existing Scheduler Operator panel patterns.

### Risks

1. Premature without CLI/MCP read-write semantics.
2. Pulls UI and screenshot validation into a backend control question.
3. Can blur lifecycle control with scheduler projection refresh and host
   workflow buttons.

### Fit

Later. UI should consume the stable surface, not define it.

## Candidate D - Real Background Daemon Host

### Shape

Start an actual long-running process or host-managed daemon that watches the
lifecycle control file and repeatedly runs scheduler loops.

### Pros

1. Moves closest to a real agent-cluster scheduler service.

### Risks

1. Too large for the next step.
2. Requires process supervision, polling policy, shutdown semantics, stale
   detection, host authorization, and failure recovery.
3. Would make mistakes in the control surface harder to unwind.

### Fit

Deferred. The read/write surface should come first.

## Recommendation

Choose Candidate A next:

> Minimal Lifecycle CLI/MCP Read-Write Surface

Reasoning:

1. `docs/codex-entry-contract.md` and `docs/host-interaction-model.md` define
   Codex as `AGENTS.md` + MCP + CLI/validation, so lifecycle control should be
   callable through the same path.
2. The runtime contract already exists; the missing piece is a thin interaction
   surface, not more daemon semantics.
3. Existing scheduler surfaces already have a clear CLI/MCP split and
   authority-split payload pattern.
4. This enables operator and agent dogfood without starting a persistent
   service.

## Proposed Next Planning Gate

```text
2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md
```

Recommended scope:

1. Add `doc-based-coding scheduler lifecycle <action>` subcommands.
2. Add MCP tools `schedulerLifecycleControl` and `schedulerLifecycleRunOnce`.
3. Keep MCP runtime provider fake-only for `runOnce`.
4. Add focused CLI tests for inspect/start/pause/resume/cancel/shutdown/run-once.
5. Add focused MCP tool and server routing tests.
6. Update scheduler MCP smoke prompt and bootstrap copy.
7. Update review/status docs after validation.

Recommended non-goals:

1. Do not start a persistent background daemon process.
2. Do not add sleep, polling, filesystem watch, OS service registration, or
   process supervision.
3. Do not run real Qoder or other external providers through generic MCP.
4. Do not add Host UX binding.
5. Do not refresh scheduler projection automatically from lifecycle control
   actions.
6. Do not mutate ExchangeArtifact lifecycle or admission ledger state.
7. Do not mutate agent-owned Local Work Trajectory from scheduler code or MCP
   scheduler tools.

## Deferred Direction Order

Recommended order after Candidate A:

1. `Lifecycle Host UX Readback / Control Binding`
2. `Edit Lease Conflict Policy Expansion`
3. `Runtime Subagent Policy`
4. `Real Background Daemon Host`
5. `Real Sandbox Provider Spike`

