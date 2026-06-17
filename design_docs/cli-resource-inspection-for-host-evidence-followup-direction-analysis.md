# CLI Resource Inspection For Host Evidence Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-cli-resource-inspection-for-host-evidence.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `doc-based-coding resources list` exposes the existing MCP resource list
   without starting an MCP host.
2. `doc-based-coding resources read dbc://host-evidence/bundle` reads compact
   host evidence bundle JSON through the same `GovernanceTools` resource path.
3. Missing resources return a clear non-zero CLI error.
4. Scheduler smoke prompt guidance includes the CLI fallback for hosts where MCP
   resource reading is unavailable.
5. The CLI path is read-only and does not execute providers or change resource
   contracts.

Evidence review:

- `review/cli-resource-inspection-for-host-evidence-2026-06-18.md`

## Candidate A — Resource Error Isolation

Do what:

1. Preserve strict runtime evidence validation for writer/reader tests.
2. Add a UI/resource-facing isolated error summary path for malformed evidence
   files.
3. Ensure one bad evidence file does not prevent `dbc://host-evidence/bundle`
   or CLI inspection from reporting the remaining valid summaries.
4. Keep error payloads compact and secret-safe.

Why first:

This is the cleanest next product-hardening slice. It improves future UI and
operator consumption while staying on the same read-only resource line. It does
not require the dirty VS Code UI branch, live SDK credentials, or scheduler
daemon work.

## Candidate B — VS Code / Preview UI Binding

Do what:

1. Surface host evidence summaries in the progress preview UI.
2. Display provider, invocation, stop reason, output refs, and authority split.
3. Validate visually with screenshot-based tooling.

Why not first:

The worktree currently contains unrelated dirty VS Code/UI files. Starting UI
binding now risks mixing a clean orchestration/resource line with unfinished UI
state.

## Candidate C — Credentialed Live Qoder Rerun

Do what:

1. Install optional `qoder-agent-sdk` and provide
   `QODER_PERSONAL_ACCESS_TOKEN` outside project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Inspect generated evidence through the MCP resource and CLI resource reader.

Why not first:

This depends on external host setup and credentials. It remains valuable, but
the product surface should first tolerate partial or malformed local evidence.

## Candidate D — CLI UX Polish

Do what:

1. Add optional `--json` / `--uri` filters or shorter table output.
2. Add examples to installation or operator docs.

Why not first:

The current CLI already satisfies the inspection contract. Error isolation
reduces future support risk more than formatting polish.

## Current Recommendation

Recommended next gate:

```text
Resource Error Isolation For Host Evidence
```

The next slice should stay narrow:

1. No UI binding.
2. No new MCP execution tool.
3. No provider execution.
4. No SDK installation or credential provisioning.
5. Keep strict writer/runtime validation separate from UI/resource-facing
   isolated error summaries.
