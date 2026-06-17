# Host Evidence Consumer Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-host-evidence-consumer.md`
has reached `COMPLETED`.

The current boundary now proves:

1. Persisted `host_scheduler_run_evidence` JSON has a strict reader.
2. Downstream consumers can use `HostSchedulerRunEvidenceSummary` instead of
   binding to raw writer artifacts.
3. Progress graph / host surfaces can read
   `tools.progress_graph.read_host_evidence_bundle()`.
4. Missing evidence directories have a stable empty-bundle behavior.
5. Malformed evidence fails with explicit product/schema errors.
6. The consumer remains read-only and does not execute providers or mutate
   scheduler/local trajectory state.

Evidence review:

- `review/host-evidence-consumer-2026-06-18.md`

## Candidate A — MCP Resource Exposure For Host Evidence

Do what:

1. Expose host evidence bundle as a read-only MCP resource or resource-like
   prompt surface.
2. Keep execution fake-only; do not add real-provider MCP execution.
3. Reuse `read_host_evidence_bundle()` as the only reader.
4. Add tests proving the resource does not mutate scheduler or local
   trajectory artifacts.

Why first:

This makes the evidence visible to agents and host clients without touching
credential provisioning, daemon behavior, or VS Code UI work. It is the
smallest productization step after the consumer contract.

## Candidate B — VS Code / Preview UI Binding

Do what:

1. Add a UI panel or tab that displays host evidence summaries.
2. Show provider, host invocation, stop reason, output refs, and authority
   split.
3. Use screenshot-based validation before close.

Why not first:

There are existing unrelated VS Code/UI dirty files in the worktree. UI binding
should wait for a clean, narrow visual slice or an explicit decision to pick up
that UI branch.

## Candidate C — Credentialed Live Qoder Rerun

Do what:

1. Provision optional `qoder-agent-sdk` and host auth outside project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Read the generated evidence through the new consumer.

Why not first:

It depends on external host setup and credential availability. The project can
make progress by productizing existing evidence consumption first.

## Candidate D — Scheduler Daemon / Queue Loop

Do what:

1. Define queue polling, retry, timeout, cancellation, and event-log rotation.
2. Promote one-shot host runner toward durable scheduling.

Why not first:

Daemon semantics should wait until evidence visibility and host execution
contracts are stable enough for operators to inspect outcomes.

## Current Recommendation

Recommended next gate:

```text
MCP Resource Exposure For Host Evidence
```

The next slice should stay narrow:

1. Read-only exposure only.
2. No real-provider MCP execution.
3. No daemon.
4. No VS Code UI binding.
5. No credential provisioning.
6. Tests must prove the resource returns compact summaries and does not mutate
   scheduler/local trajectory artifacts.
