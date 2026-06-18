# Resource Error Isolation For Host Evidence Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-resource-error-isolation-for-host-evidence.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `HostEvidenceBundle` includes `error_count` and `errors[]`.
2. Malformed host evidence files are isolated per file while valid summaries
   remain visible.
3. Strict runtime evidence readers still reject malformed evidence.
4. MCP resource reads and CLI resource inspection observe the same robust
   bundle payload.
5. The resource/CLI line remains read-only and does not execute providers,
   refresh scheduler projections, or mutate Local Work Trajectory.

Evidence review:

- `review/resource-error-isolation-for-host-evidence-2026-06-18.md`

## Candidate A — Host Evidence Presentation Contract

Do what:

1. Add a pure presentation model over `HostEvidenceBundle`.
2. Normalize host evidence summaries into UI/operator-facing cards with stable
   status, title, subtitle, key facts, refs, and authority clues.
3. Normalize bundle errors into compact UI/operator-facing error rows.
4. Keep path fields explicit but avoid embedding raw evidence file content.
5. Reuse the existing resource/CLI payload as input; do not add execution.

Why first:

This is the smallest useful productization step after resource hardening. It
prepares VS Code or other host UI binding without touching the currently dirty
VS Code branch. It also creates a stable data contract that CLI, MCP clients,
or tests can inspect before any visual layer is wired.

## Candidate B — VS Code / Preview UI Binding

Do what:

1. Display host evidence presentation cards in the progress preview UI.
2. Surface provider, invocation, stop reason, output refs, authority split, and
   isolated read errors.
3. Validate visually with screenshot-based tooling.

Why not first:

The worktree still has unrelated VS Code/UI dirty files. A UI slice should
consume a stable presentation contract rather than binding directly to raw
bundle JSON while that branch is unsettled.

## Candidate C — Credentialed Live Qoder Rerun

Do what:

1. Provision optional `qoder-agent-sdk` and host authentication outside
   project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Inspect generated evidence through MCP resource, CLI resource, and the
   presentation contract.

Why not first:

This remains valuable, but it depends on external credentials and SDK
availability. The presentation contract can land without those prerequisites
and will make the eventual live result easier to inspect.

## Candidate D — Scheduler Daemon / Durable Queue

Do what:

1. Define polling, retry, cancellation, timeout, and event-log rotation.
2. Promote one-shot host runner toward durable scheduler operation.
3. Decide how daemon outcomes are written into host evidence and trajectory
   projections.

Why not first:

Daemon semantics are wider than the current productization line. The project
should first finish the inspectable evidence surfaces for one-shot runs.

## Current Recommendation

Recommended next gate:

```text
Host Evidence Presentation Contract
```

The next slice should stay narrow:

1. No VS Code UI binding.
2. No new MCP execution tool.
3. No provider execution.
4. No SDK installation or credential provisioning.
5. No scheduler daemon.
6. Tests should prove presentation output for empty bundles, successful
   summaries, permission-review / failed / partial stop states, and isolated
   read errors.
