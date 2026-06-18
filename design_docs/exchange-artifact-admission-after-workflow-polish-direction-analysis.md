# ExchangeArtifact Admission After Workflow Polish Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The current ExchangeArtifact admission chain now has an operator-verifiable
CLI workflow:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler inspect-state`
4. `doc-based-coding scheduler project`

Latest implementation review:

- `review/exchange-artifact-operator-admission-workflow-polish-2026-06-19.md`

Core architecture references:

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `review/research-compass.md`

## Current Position

The operator path is intentionally conservative:

1. Inspection is read-only.
2. Admission writes scheduler snapshot/event-log state.
3. Readback is read-only.
4. Projection refresh writes only scheduler-derived view artifacts.
5. Provider execution remains separate.
6. Agent-owned Local Work Trajectory remains separate.

This is enough for a human/operator or host script to prove the chain. It is
not yet enough to safely expose stored-artifact admission as an agent-callable
MCP write surface or to run a long-lived scheduler loop.

## Candidate A - Exchange Artifact Admission Ledger

### Shape

Add a durable, explicit ledger for stored-artifact admission decisions and
consumption state.

Possible deliverables:

1. `ExchangeArtifactAdmissionLedger` or equivalent local JSON/JSONL store.
2. Records for admission attempts, exact `(artifact_id, version)`, actor/surface,
   scheduler snapshot path, event-log path, submitted task IDs, decision time,
   result, and error summary.
3. Optional lifecycle projection from ledger state into inspection bundles,
   such as `admitted`, `failed`, `superseded`, or `consumed`.
4. Tests proving duplicate admission can be detected or reported without
   silently resubmitting the same artifact version.

### Pros

1. Directly addresses the biggest trust gap before MCP write exposure.
2. Preserves exact-version artifact semantics.
3. Gives future UI/MCP surfaces a clear audit object.
4. Fits the artifact-centered communication design: scheduler-relevant history
   is structured, not prose-only.

### Risks

1. Naming must not imply the exchange store itself becomes scheduler authority.
2. Duplicate policy needs a careful first version: warn, reject, or allow with
   explicit `--replace-existing`-like semantics.

### Fit

High. This is the strongest next narrow gate because it reduces risk before
opening broader mutation surfaces.

## Candidate B - Stored-Artifact MCP Admission Tool

### Shape

Expose an MCP write tool that wraps exact-version stored artifact admission.

Minimum requirements if selected:

1. Exact artifact ID and version are required.
2. Scheduler snapshot and event-log paths remain explicit.
3. The tool returns the same authority clues as the CLI.
4. The tool refuses or clearly reports duplicate admission once Candidate A
   exists.
5. It does not run providers, refresh projection, mark arbitrary lifecycle
   state, or mutate Local Work Trajectory.

### Pros

1. Lets Codex/Copilot hosts admit stored scheduler submissions without shelling
   out to CLI.
2. Completes symmetry with `schedulerSubmitTasks`.
3. Useful once guide agents begin producing scheduler submission artifacts.

### Risks

1. Agent-callable scheduler mutation is a larger trust surface than CLI.
2. Without a ledger, repeated admission can be hard to distinguish from
   intentional replacement.
3. Permission/review semantics would be under-specified if implemented
   immediately.

### Fit

Medium. It is valuable, but should follow or include a very small admission
ledger.

## Candidate C - Scheduler Daemon / Durable Queue

### Shape

Introduce a long-lived or repeated queue loop that evaluates scheduler
readiness and runs tasks under bounded policies.

### Pros

1. Moves closer to actual multi-agent orchestration.
2. Exercises retry, cancellation, timeout, and recovery concerns.
3. Builds on the existing bounded scheduler drain primitives.

### Risks

1. Still too broad immediately after operator admission.
2. Requires sharper sandbox/provider/readiness policy.
3. Daemon behavior without stronger admission audit may obscure who admitted
   which work.

### Fit

Important, but not the next gate.

## Candidate D - Host Evidence / Scheduler Admission UI Binding

### Shape

Bind exchange artifact candidates, admission results, scheduler readback, and
projection status into the VS Code progress graph or another host UI panel.

### Pros

1. Improves operator visibility.
2. Existing CLI/resource/presentation surfaces now provide clean data sources.
3. Can remain read-only at first.

### Risks

1. There is already a dirty UI branch in the worktree.
2. UI work needs screenshot validation and should not be mixed into the
   orchestration authority path.
3. It does not solve duplicate-consumption or MCP write trust semantics.

### Fit

Useful later. Keep separate unless the active workstream returns to graph/UI.

## Candidate E - Provider Execution Policy / Qoder Runtime Recheck

### Shape

Return to runtime/provider readiness after the admission chain can create and
inspect scheduled work.

Possible deliverables:

1. Recheck Qoder host provisioning.
2. Run a bounded fake or Qoder task from a scheduler-admitted artifact.
3. Record host evidence through existing evidence surfaces.

### Pros

1. Exercises the real reason admission exists: admitted work should eventually
   run.
2. Connects the operator chain with runtime evidence.

### Risks

1. Can accidentally mix admission policy, runtime execution, and host
   provisioning in one slice.
2. Current Qoder readiness was previously negative; environment may still not
   be provisioned.

### Fit

Medium. Better after ledger or if the user explicitly wants runtime dogfood
next.

## Recommendation

Choose Candidate A:

> Exchange Artifact Admission Ledger

Reasoning:

1. The latest workflow polish made admission visible but did not add a durable
   memory of admission decisions.
2. The next high-value mutation surface is likely MCP admission, but MCP write
   exposure should not arrive before duplicate/consumption/audit semantics are
   explicit.
3. A narrow ledger gate keeps authority contract-first and produces a reusable
   product for future CLI, MCP, UI, and daemon surfaces.

## Proposed Next Planning Gate

```text
2026-06-19-exchange-artifact-admission-ledger.md
```

Recommended acceptance:

1. Define the ledger contract before implementation.
2. Store exact artifact ID/version, actor/surface, scheduler persistence paths,
   task IDs, result status, timestamps, and error summaries.
3. Add a read-only inspection/readback surface for ledger entries.
4. Integrate admission helper or CLI enough to append ledger entries when
   explicitly enabled by the gate.
5. Prove duplicate admission is either rejected or visibly reported by policy.
6. Do not add stored-artifact MCP admission tool yet.
7. Do not run providers, daemon loops, or UI binding.

## Deferred Candidates

1. Stored-artifact MCP Admission Tool.
2. Scheduler Daemon / Durable Queue.
3. Host Evidence / Scheduler Admission UI Binding.
4. Provider Execution Policy / Qoder Runtime Recheck.
