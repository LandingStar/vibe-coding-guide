# Host Evidence MCP Resource Exposure Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-host-evidence-mcp-resource-exposure.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `dbc://host-evidence/bundle` is available through the MCP resource surface.
2. The resource reads compact `HostEvidenceBundle` JSON.
3. Missing evidence directories return an empty bundle.
4. Reading the resource does not create scheduler projection or Local Work
   Trajectory artifacts.
5. The resource is read-only and does not execute fake or real providers.

Evidence review:

- `review/host-evidence-mcp-resource-exposure-2026-06-18.md`

## Candidate A — CLI Resource Inspection

Do what:

1. Add a `doc-based-coding resources list` CLI entry.
2. Add a `doc-based-coding resources read <uri>` CLI entry.
3. Reuse `GovernanceTools.list_resources()` and `read_resource()`.
4. Prove `dbc://host-evidence/bundle` can be inspected without MCP host setup.

Why first:

This turns the new resource into a host-visible operator surface without
touching the currently dirty VS Code UI branch and without requiring Qoder SDK
or credentials. It also gives future tests and users a simple way to inspect
resources outside an MCP client.

## Candidate B — VS Code / Preview UI Binding

Do what:

1. Display host evidence summaries in a host-visible panel or tab.
2. Show provider, invocation, stop reason, output refs, and authority split.
3. Validate visually with screenshot-based tools.

Why not first:

The worktree currently contains many unrelated VS Code/UI dirty files and
generated visual artifacts. Starting UI binding now would risk mixing this
clean orchestration/resource line with an unresolved UI branch.

## Candidate C — Credentialed Live Qoder Rerun

Do what:

1. Provision optional `qoder-agent-sdk` and `QODER_PERSONAL_ACCESS_TOKEN`
   outside project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Inspect generated evidence through `dbc://host-evidence/bundle`.

Why not first:

This depends on external host setup and credentials. It is valuable, but it
should not block productizing the evidence surfaces that already exist.

## Candidate D — Resource Error Isolation

Do what:

1. Soften `HostEvidenceBundle` reading so malformed evidence files become
   per-file error summaries instead of failing the whole bundle.
2. Preserve strict runtime reader behavior separately.

Why not first:

Useful for UI robustness, but the CLI inspection surface should land first so
there is a simple way to observe both success and failure behavior.

## Current Recommendation

Recommended next gate:

```text
CLI Resource Inspection For Host Evidence
```

The next slice should stay narrow:

1. CLI list/read only.
2. Reuse existing `GovernanceTools` resource methods.
3. No new MCP execution tool.
4. No UI binding.
5. No Qoder SDK installation or credential provisioning.
6. Tests should cover `dbc://host-evidence/bundle` empty-bundle read and
   resource listing.
