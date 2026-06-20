# Host UX Authorization Readback Binding Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-host-ux-authorization-readback-binding.md`
> Status: COMPLETED

## Summary

The VS Code Progress Graph Preview / Scheduler Operator panel now consumes and
renders the read-only scheduler authorization diagnostics product.

The binding keeps the scheduler/operator authority split intact:

```text
Host UX reads schedulerAuthorizationReadback
-> renders edit lease declaration, lifecycle, and sandbox authorization facts
-> does not mutate scheduler, projection, ExchangeArtifact, admission ledger, or Local Work Trajectory
```

## Implemented

1. Added Scheduler Operator readback types and adapter in
   `vscode-extension/src/views/schedulerOperatorWorkflow.ts`.
2. The adapter calls existing runtime tooling:
   `GovernanceTools.scheduler_authorization_readback(...)`.
3. Extended Scheduler Operator workflow state with:
   - `authorizationReadback`
   - `authorizationReadError`
4. Added readback facts to the Progress Graph Preview shell signature so the
   panel refreshes when authorization diagnostics change.
5. Rendered a compact `Authorization Readback` section inside the existing
   Scheduler Operator card.
6. Covered empty, failed, and populated readback states in focused tests.

## Validation

Passed:

```text
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js vscode-extension/dist/test/progressGraphPreviewPanel.test.js
```

Focused result:

```text
26 passed
```

Screenshot-style validation:

```text
output/playwright/host-ux-authorization-readback/authorization-readback.png
```

The screenshot fixture confirms the rendered section contains:

```text
Authorization Readback
task-api
sandbox authorized
```

Broader extension test note:

```text
npm run test --prefix vscode-extension
```

The full extension suite built successfully and ran, but one existing dirty
workspace test failed outside this slice:

```text
ai chat prompt treats localTrajectory as the task-tracking mutation exception
```

Failure reason: the test expects `Use localTrajectory addLane as soon as a
distinct work context must begin`, while the current dirty source says `one
distinct work context`. This is unrelated to the authorization readback binding
files changed in this gate.

## Non-Goals Preserved

1. No real sandbox provider was implemented.
2. No scheduler mutation button was added.
3. No scheduler/admission/readback backend schema expansion was required.
4. No ExchangeArtifact store or admission ledger mutation was added.
5. No scheduler projection refresh behavior changed.
6. No UI-triggered Local Work Trajectory mutation was added.

## Residual Risk

The readback section is intentionally compact and inherits the existing
Scheduler Operator card density. A later UI polish gate may improve operator
readability, but this slice established the contract and read-only surface.

## Next Direction

The next backend safety candidate remains:

```text
Git Worktree Sandbox Provider Spike Over Acquired Leases
```

The Host UX readback can now serve as the diagnostic surface while real sandbox
provider behavior is introduced.
