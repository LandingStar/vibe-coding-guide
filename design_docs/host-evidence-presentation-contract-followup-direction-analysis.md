# Host Evidence Presentation Contract Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-contract.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `HostEvidenceBundle` can be converted into `HostEvidencePresentation`.
2. Presentation cards expose stable operator-facing fields for provider,
   invocation, stop reason, output refs, and authority clues.
3. Isolated evidence read errors become presentation error rows.
4. Empty / completed / permission-review / failed / partial / degraded states
   are derived without re-reading raw `host_result`.
5. Existing MCP resource and CLI bundle payload remain unchanged.

Evidence review:

- `review/host-evidence-presentation-contract-2026-06-18.md`

## Candidate A — Presentation Resource / CLI Exposure

Do what:

1. Expose the presentation JSON as a read-only resource-like surface, likely
   `dbc://host-evidence/presentation`.
2. Add CLI inspection support through the existing `doc-based-coding resources`
   path if a new resource URI is chosen.
3. Reuse `read_host_evidence_bundle()` plus `build_host_evidence_presentation()`.
4. Prove the new presentation read is still read-only and does not mutate
   scheduler projection or Local Work Trajectory artifacts.

Why first:

This keeps momentum on the clean resource/CLI line and gives future VS Code UI
binding a stable host-readable payload. It avoids the unrelated dirty VS Code
branch and does not need Qoder credentials.

## Candidate B — VS Code / Preview UI Binding

Do what:

1. Display presentation cards and error rows in the progress preview host UI.
2. Show status, provider, invocation, outputs, authority clues, and read
   errors.
3. Validate visually with screenshot-based tooling.

Why not first:

This is the most product-visible next step, but the worktree still contains
unrelated VS Code/UI dirty files. UI binding should consume a stable
presentation resource or happen in a clean UI slice.

## Candidate C — Credentialed Live Qoder Rerun

Do what:

1. Provision optional `qoder-agent-sdk` and host authentication outside
   project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Inspect generated evidence through bundle and presentation surfaces.

Why not first:

This depends on external credentials and SDK availability. It should remain a
clear validation target, but it is not the cleanest next productization step.

## Candidate D — Scheduler Daemon / Durable Queue

Do what:

1. Define polling, retry, cancellation, timeout, and event-log rotation.
2. Promote one-shot host runner toward durable scheduler operation.
3. Decide how daemon outcomes are written into evidence and presentation
   surfaces.

Why not first:

Daemon semantics are a larger orchestration slice. The evidence inspection
surface should be complete enough for operators before daemon behavior expands.

## Current Recommendation

Recommended next gate:

```text
Host Evidence Presentation Resource Exposure
```

The next slice should stay narrow:

1. Read-only presentation exposure only.
2. No provider execution.
3. No scheduler daemon.
4. No VS Code UI binding.
5. No credential provisioning.
6. Tests should prove presentation JSON is inspectable through resource/CLI
   pathways and existing bundle payload remains unchanged.
