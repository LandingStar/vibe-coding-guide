# ExchangeArtifact Operator Admission Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The project now has a minimal operator admission chain:

1. `dbc://exchange-artifacts/bundle` and
   `doc-based-coding resources read dbc://exchange-artifacts/bundle` inspect the
   local durable `ExchangeArtifact` store without mutation.
2. `admit_exchange_artifact_version_to_scheduler()` admits one exact stored
   scheduler submission artifact from Python/runtime code.
3. `doc-based-coding scheduler admit-exchange-artifact` admits one exact stored
   scheduler submission artifact from a CLI operator surface.

The latest close review is:

- `review/exchange-artifact-operator-admission-cli-2026-06-19.md`

The broader orchestration boundary is still governed by:

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `review/research-compass.md`

## Current Gap

The stored-artifact admission path can write scheduler snapshot/event-log state,
but the operator workflow is still split into separate manual actions:

1. Inspect stored candidates.
2. Admit one exact candidate.
3. Optionally inspect scheduler state.
4. Optionally refresh scheduler-derived projection.
5. Optionally run a bounded scheduler pass later.

That split is acceptable for the first CLI admission slice, but it leaves a
small usability and verification gap before exposing any broader write surface.

The next direction should improve the operator's ability to prove what happened
without increasing scheduling authority or provider-execution scope too early.

## Candidate A — Operator Admission Workflow Polish

### Shape

Add a narrow operator-facing workflow around the existing CLI/runtime surfaces.

Possible deliverables:

1. A CLI readback command or output mode that summarizes the admitted scheduler
   state and event-log clues after admission.
2. A documented two-command or three-command operator recipe:
   inspect -> admit -> project/readback.
3. Optional CLI flag to refresh scheduler projection after admission, but only
   if it is explicitly named as projection refresh and remains separate from
   provider execution.
4. Tests proving the workflow does not run providers and does not mutate
   agent-owned Local Work Trajectory.

### Pros

1. Directly closes the remaining usability gap from the latest review.
2. Keeps trust surface low: still CLI/operator, not an agent-callable MCP write.
3. Produces better evidence for future MCP/UI decisions.
4. Builds on existing scheduler projection and resource-reading surfaces.

### Risks

1. If it combines too many actions, it may blur admission, projection, and run
   boundaries.
2. Projection refresh must remain clearly read/view-oriented.

### Fit

High. This is the smallest step that makes the current admission chain easier
to use and validate.

## Candidate B — Stored-Artifact MCP Admission Tool

### Shape

Expose an MCP write tool that wraps exact-version stored artifact admission.

### Pros

1. Lets Codex/Copilot/other MCP hosts trigger stored-artifact admission directly.
2. Completes symmetry with existing `schedulerSubmitTasks`.

### Risks

1. Larger trust surface: agent tool channel can mutate scheduler snapshot/event
   log state.
2. Needs clearer permission and review story than the CLI.
3. Could encourage agents to admit coordination products before operator review.
4. Should likely require exact artifact/version plus visible admission
   candidate inspection evidence.

### Fit

Medium, but premature as the immediate next step. It should be a separate
reviewed gate after operator workflow evidence is stronger.

## Candidate C — Scheduler Daemon / Durable Queue

### Shape

Move from bounded command-style scheduler actions to a daemon or durable queue
that repeatedly evaluates readiness and runs tasks.

### Pros

1. Moves toward the long-term multi-agent scheduler.
2. Addresses real orchestration lifecycle needs: retry, cancellation, timeout,
   queue loop, and durable recovery.

### Risks

1. Much larger scope than the current admission chain.
2. Requires sandbox, provider readiness, resource policy, and permission
   decisions to be sharper.
3. Likely needs new tests and operating protocols across many modules.

### Fit

Important but too broad for the immediate follow-up. It should be planned after
operator admission/readback and provider/sandbox policy are less rough.

## Candidate D — Host Evidence UI Binding

### Shape

Bind host evidence and scheduler/admission summaries into the VS Code progress
graph or another host panel.

### Pros

1. User-facing visibility improves quickly.
2. Existing presentation/resource surfaces already support safe read-only
   evidence consumption.

### Risks

1. There is already a dirty UI branch in the worktree; mixing it with scheduler
   admission may create scope bleed.
2. UI visibility without a smoother operator workflow may only expose the same
   manual seams.
3. UI work requires screenshot validation and can become visually expensive.

### Fit

Useful later, but not the next orchestration-layer step. Keep UI binding
separate unless the user explicitly switches back to graph/preview work.

## Recommendation

Choose Candidate A:

> Operator Admission Workflow Polish

The narrow planning gate should not add a stored-artifact MCP write tool,
provider execution, daemon behavior, or UI binding. It should make the current
operator chain easier to verify by improving readback/projection guidance and,
if justified, adding a clearly named projection refresh option or companion
readback command.

## Proposed Next Planning Gate

```text
2026-06-19-exchange-artifact-operator-admission-workflow-polish.md
```

Recommended acceptance:

1. The operator can inspect stored candidates, admit an exact version, and
   verify scheduler snapshot/event-log outcome from documented CLI surfaces.
2. Any optional projection refresh remains explicit and read/view-only.
3. The workflow does not run providers.
4. The workflow does not mutate `.codex/progress-graph/local-work-trajectory.json`.
5. Tests cover success and boundary behavior.
6. Prompt guidance distinguishes inspection, admission, projection refresh, and
   scheduler run.

## Deferred Candidates

1. Stored-artifact MCP admission tool.
2. Scheduler daemon / durable queue.
3. Host evidence / scheduler admission UI binding.
4. Exchange artifact lifecycle ledger / consumed marking.
