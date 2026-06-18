# Qoder Host Provisioning Check Guide Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-qoder-host-provisioning-check-guide.md`
has reached `COMPLETED`.

The current boundary proves:

1. `QoderSDKHostReadinessReport` can report host SDK/auth readiness without
   executing Qoder or the scheduler.
2. `doc-based-coding qoder readiness` and `python -m src qoder readiness`
   expose secret-safe JSON for `env` and `qodercli` auth modes.
3. Future live Qoder smoke runs now have a repeatable preflight command.
4. The active host remains readiness-negative: the SDK is not importable and no
   token is present in `env` mode.
5. The Qoder SDK line remains a runtime-adapter support path, not the project
   scheduler.

Evidence review:

- `review/qoder-host-provisioning-check-guide-2026-06-18.md`
- `docs/qoder-host-provisioning-check-guide.md`

## Candidate A — ExchangeArtifact Durable Store Foundation

Do what:

1. Add a local durable artifact version store for `ExchangeArtifact`.
2. Preserve the current validation rule that scheduler-relevant content cannot
   exist only in prose.
3. Keep the existing `InMemoryArtifactVersionStore` for tests and injected
   runtime use.
4. Add focused tests proving round-trip, duplicate-version rejection, invalid
   artifact rejection, and list/latest behavior.
5. Update the exchange artifact design record and orchestration slice plan.

Why now:

The orchestration layer already has first-version product objects for:

1. scheduler task submissions,
2. agent home registration products,
3. scratch manifests and cleanup receipts,
4. runtime output artifacts,
5. coordination logs.

Those products currently have only an in-memory version store. That is enough
for unit tests, but it is too weak for real multi-agent coordination because
agents need stable artifact IDs and exact versions across turns, runs, and
future scheduler projections.

This slice advances the main product goal without waiting for Qoder host
provisioning.

## Candidate B — Host Evidence Preview UI Binding

Do what:

1. Bind `dbc://host-evidence/presentation` into the VS Code progress preview.
2. Show empty, degraded, failed, permission-review, and completed states.
3. Validate with screenshot-based tooling.

Why not first:

The worktree still contains unrelated VS Code/UI dirty files. UI binding is
useful, but it is not the best next clean slice while the orchestration product
definition still lacks durable exchange artifacts.

## Candidate C — Provisioned Live Qoder Rerun

Do what:

1. Install `qoder-agent-sdk` into the intended host runtime.
2. Provide host authentication without committing secrets.
3. Rerun the bounded live Qoder smoke path and inspect host evidence resources.

Why not first:

This is blocked by host environment work. The project can still move the
orchestration layer forward with fake-runtime and mockable runtime seams.

## Candidate D — Presentation Resource Timestamp Polish

Do what:

1. Decide whether `dbc://host-evidence/presentation` should include a generated
   timestamp.
2. Add deterministic tests for timestamp policy.

Why not first:

This is a small operator-facing polish item. It does not unblock multi-agent
coordination.

## Current Recommendation

Recommended next gate:

```text
ExchangeArtifact Durable Store Foundation
```

Reason: the current product direction is agent orchestration. The strongest
next move is to make the intermediate coordination product durable and
version-addressable before adding more agent scheduling behavior. Qoder remains
the preferred early runtime validation target, but it should not hold the core
orchestration layer hostage while the active host is not provisioned.

