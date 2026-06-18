# ExchangeArtifact Operator Admission Surface Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

`review/exchange-artifact-exact-version-scheduler-admission-2026-06-19.md`
closed the runtime helper that admits an exact stored `ExchangeArtifact`
version into scheduler-owned snapshot/event-log state.

The remaining gap is operator usability: a host or developer can inspect
stored admission candidates through `dbc://exchange-artifacts/bundle`, but
cannot trigger the exact-version admission from a stable non-Python entrypoint.

## Decision

Use a CLI-first operator surface:

```text
doc-based-coding scheduler admit-exchange-artifact
```

This command should wrap `admit_exchange_artifact_version_to_scheduler()` and
print the helper's JSON result.

## Why CLI First

1. The runtime helper is already contract-tested; CLI binding is a thin adapter.
2. Operators and host scripts need a stable non-Python command before UI or MCP
   write exposure.
3. MCP write exposure is a broader trust surface because it lets an agent mutate
   scheduler state from the tool channel.
4. The CLI can be validated without provider credentials, daemon loops, or UI
   state.
5. Keeping admission separate from scheduler projection makes the authority
   split visible: admission writes scheduler state, projection remains an
   explicit later read/view refresh.

## Selected Scope

The first operator surface should:

1. Require `--artifact-id`, `--version`, `--snapshot-path`, and
   `--event-log-path`.
2. Use `.codex/orchestration/exchange-artifacts.json` as the default
   `--artifact-store-path`, resolved under the project root.
3. Accept `--replace-existing`.
4. Accept optional `--timestamp`.
5. Resolve relative paths under the project root.
6. Print JSON shaped by `PersistedExchangeArtifactAdmissionResult.to_json_dict()`,
   plus `ok=true`.
7. Return exit code 1 with a readable error and no scheduler mutation when the
   helper rejects the artifact.

## Explicit Non-Goals

This direction does not:

1. Add a stored-artifact MCP write tool.
2. Add UI controls.
3. Execute providers or run scheduler tasks.
4. Refresh scheduler-derived trajectory projection.
5. Mark exchange artifacts consumed.
6. Choose default scheduler snapshot or event-log paths.
7. Mutate agent-owned Local Work Trajectory.

## Recommended Planning Gate

Create a narrow gate:

```text
2026-06-19-exchange-artifact-operator-admission-cli.md
```

Acceptance should focus on CLI success/error behavior, prompt guidance, and
status write-back. MCP and UI should remain separate later gates.
