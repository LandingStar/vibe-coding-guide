# Agent Communication Non-Scheduler Consumer Matrix

> Date: 2026-06-22
> Status: COMPLETED

## Context

`ExchangeArtifact` communication now supports:

1. Agent mailbox / history read models.
2. Action-candidate detection.
3. Action-candidate disposition artifacts.
4. Accepted scheduler candidate consumption through exact scheduler admission.

The remaining candidate types must not be consumed ad hoc. This gate defines the
first non-scheduler consumer matrix before adding concrete consumers.

Primary references:

- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-action-candidates.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-action-candidate-disposition.md`
- `design_docs/stages/planning-gate/2026-06-22-accepted-scheduler-candidate-disposition-consumer.md`

## Candidate Consumer Matrix

| Candidate type | Accepted target surface | Existing owner surface | First consumer status | Mutation authority |
| --- | --- | --- | --- | --- |
| `review_candidate` | `reviewIntake` / `mcp:agentExchangeAcceptedReviewCandidateConsume` / `cli:scheduler consume-accepted-review-candidate` | `ReviewIntakeConsumer.register` through `dispatch_landing_consumer_payload` shape | Implement in this gate | Review intake state only |
| `handoff_candidate` | `handoffIntake` / `mcp:agentExchangeAcceptedHandoffCandidateConsume` / `cli:scheduler consume-accepted-handoff-candidate` | `HandoffConsumer.deliver` through `dispatch_landing_consumer_payload` shape | Implemented after the first review consumer | Handoff artifact/store only |
| `blocker_candidate` | `blockerState` / `mcp:agentExchangeAcceptedBlockerCandidateConsume` / `cli:scheduler consume-accepted-blocker-candidate` | Explicit scheduler task blocking with supplied `taskId` and `reason` | Implemented with explicit task mapping | Scheduler task blocker state only |
| `merge_candidate` | `mergeIntake` / `mcp:agentExchangeAcceptedMergeCandidateConsume` / `cli:scheduler consume-accepted-merge-candidate` | `resolve_scheduler_merge_gate()` with explicit `gateId` and `approved` decision | Implemented with explicit gate mapping | Merge gate state only |

## Review Consumer Contract

An accepted `review_candidate` disposition can be consumed only when:

1. The disposition artifact is an exact stored `ExchangeArtifact` version.
2. Its structured payload has
   `product_type=agent_exchange_action_candidate_disposition`.
3. Its `disposition` is `accept`.
4. Its `candidate_type` is `review_candidate`.
5. Its `target_surface` is one of the accepted review intake surfaces.
6. The source artifact version still exists in the same ExchangeArtifact store.

The consumer must:

1. Build one deterministic review intake payload from the source artifact and
   disposition.
2. Dispatch it through a configured `ReviewIntakeConsumer`.
3. Return a compact result with authority-split flags.

The consumer must not:

1. Mutate scheduler snapshot/event-log state.
2. Admit scheduler tasks.
3. Write handoff payloads.
4. Resolve merge gates.
5. Execute providers.
6. Refresh scheduler projection.
7. Mutate Local Work Trajectory.

## Handoff / Blocker / Merge Deferral

The first pass intentionally did not implement handoff, blocker, or merge
consumers.

Rationale:

- Handoff has a mature owner surface, but review gives a smaller first
  non-scheduler proof because `FeedbackAPIReviewIntakeConsumer` can be tested
  in memory without committing a file layout.
- Blocker needed a dedicated state owner before consumption could be
  authoritative. The implemented blocker consumer therefore requires an
  explicit scheduler `taskId` and `reason`; it does not infer a task from a
  generic `blocks` or `waits_for` relation.
- Merge needed an exact candidate-to-gate mapping before consumption could be safe.
  The implemented merge consumer therefore requires an explicit `gateId` and
  `approved` decision at consumption time; it does not infer a gate from a
  generic `merges_into` relation.

## Handoff Consumer Contract

An accepted `handoff_candidate` disposition can be consumed only when:

1. The disposition artifact is an exact stored `ExchangeArtifact` version.
2. Its structured payload has
   `product_type=agent_exchange_action_candidate_disposition`.
3. Its `disposition` is `accept`.
4. Its `candidate_type` is `handoff_candidate`.
5. Its `target_surface` is one of the accepted handoff intake surfaces.
6. The source artifact version still exists in the same ExchangeArtifact store.

The consumer must:

1. Build one schema-valid Handoff payload from the source artifact and
   disposition.
2. Keep source/disposition metadata inside allowed Handoff fields because
   `handoff.schema.json` has `additionalProperties=false`.
3. Validate the payload with `handoff_validator`.
4. Dispatch it through a configured `HandoffConsumer`.
5. Return a compact result with authority-split flags.

The consumer must not:

1. Mutate scheduler snapshot/event-log state.
2. Admit scheduler tasks.
3. Open review intake.
4. Resolve merge gates.
5. Execute providers.
6. Refresh scheduler projection.
7. Mutate Local Work Trajectory.

## Merge Consumer Contract

An accepted `merge_candidate` disposition can be consumed only when:

1. The disposition artifact is an exact stored `ExchangeArtifact` version.
2. Its structured payload has
   `product_type=agent_exchange_action_candidate_disposition`.
3. Its `disposition` is `accept`.
4. Its `candidate_type` is `merge_candidate`.
5. Its `target_surface` is one of the accepted merge intake surfaces.
6. The source artifact version still exists in the same ExchangeArtifact store.
7. The caller supplies an exact scheduler `gateId`.
8. The caller supplies an explicit `approved` boolean decision.

The consumer must:

1. Read scheduler snapshot state.
2. Resolve the exact merge gate through `resolve_scheduler_merge_gate()`.
3. Write the updated scheduler snapshot.
4. Optionally append to scheduler merge-gate event log when a path is supplied.
5. Store the disposition artifact exact version as the merge decision artifact
   reference.
6. Return a compact result with authority-split flags.

The consumer must not:

1. Infer a merge gate from a generic `merges_into` relation.
2. Admit scheduler tasks.
3. Open review intake.
4. Write handoff payloads.
5. Execute providers.
6. Refresh scheduler projection.
7. Mutate Local Work Trajectory.

## Blocker Consumer Contract

An accepted `blocker_candidate` disposition can be consumed only when:

1. The disposition artifact is an exact stored `ExchangeArtifact` version.
2. Its structured payload has
   `product_type=agent_exchange_action_candidate_disposition`.
3. Its `disposition` is `accept`.
4. Its `candidate_type` is `blocker_candidate`.
5. Its `target_surface` is one of the accepted blocker state surfaces.
6. The source artifact version still exists in the same ExchangeArtifact store.
7. The caller supplies an exact scheduler `taskId`.
8. The caller supplies a non-empty blocker `reason`.

The consumer must:

1. Read scheduler snapshot state.
2. Mark the exact task `blocked` with the supplied reason.
3. Write the updated scheduler snapshot.
4. Optionally append a `task_blocked` scheduler event when an event log path is
   supplied.
5. Return a compact result with authority-split flags.

The consumer must not:

1. Infer a task from a generic `blocks` or `waits_for` relation.
2. Admit scheduler tasks.
3. Open review intake.
4. Write handoff payloads.
5. Resolve merge gates.
6. Execute providers.
7. Refresh scheduler projection.
8. Mutate Local Work Trajectory.

## Validation Plan

1. Runtime tests for accepted review candidate consumption.
2. CLI test for `consume-accepted-review-candidate`.
3. MCP route test for `agentExchangeAcceptedReviewCandidateConsume`.
4. Regression test that the accepted scheduler consumer reports
   `consumption_state.exchange_store_mutated` correctly.
5. `py_compile` for touched runtime / CLI / MCP files.
6. Focused pytest for agent exchange, CLI, and MCP routes.
7. `git diff --check`.

## Completed Implementation

Implemented in this gate before handoff:

1. Updated action candidate suggested surfaces:
   - `review_candidate` -> `reviewIntake`
   - `handoff_candidate` -> `handoffIntake`
   - `blocker_candidate` -> `blockerState`
   - `merge_candidate` -> `mergeIntake`
2. Added accepted review candidate runtime consumer:
   `consume_accepted_review_action_candidate()`.
3. Added review target-surface whitelist:
   `ACCEPTED_REVIEW_INTAKE_TARGET_SURFACES`.
4. Added CLI:
   `doc-based-coding scheduler consume-accepted-review-candidate`.
5. Added MCP tool:
   `agentExchangeAcceptedReviewCandidateConsume`.
6. Fixed accepted scheduler consumer authority split to read
   `consumption_state.exchange_store_mutated`.
7. Updated MCP Tool Surface Audit and scheduler MCP smoke prompts with the
   accepted review candidate consumer boundary.

Implemented in the follow-up handoff slice:

1. Added accepted handoff candidate runtime consumer:
   `consume_accepted_handoff_action_candidate()`.
2. Added handoff target-surface whitelist:
   `ACCEPTED_HANDOFF_INTAKE_TARGET_SURFACES`.
3. Added CLI:
   `doc-based-coding scheduler consume-accepted-handoff-candidate`.
4. Added MCP tool:
   `agentExchangeAcceptedHandoffCandidateConsume`.
5. Updated MCP Tool Surface Audit and scheduler MCP smoke prompts with the
   accepted handoff candidate consumer boundary.

Implemented in the follow-up merge slice:

1. Added accepted merge candidate runtime consumer:
   `consume_accepted_merge_action_candidate()`.
2. Added merge target-surface whitelist:
   `ACCEPTED_MERGE_INTAKE_TARGET_SURFACES`.
3. Added CLI:
   `doc-based-coding scheduler consume-accepted-merge-candidate`.
4. Added MCP tool:
   `agentExchangeAcceptedMergeCandidateConsume`.
5. Updated MCP Tool Surface Audit and scheduler MCP smoke prompts with the
   accepted merge candidate consumer boundary.

Implemented in the follow-up blocker slice:

1. Added accepted blocker candidate runtime consumer:
   `consume_accepted_blocker_action_candidate()`.
2. Added blocker target-surface whitelist:
   `ACCEPTED_BLOCKER_STATE_TARGET_SURFACES`.
3. Added CLI:
   `doc-based-coding scheduler consume-accepted-blocker-candidate`.
4. Added MCP tool:
   `agentExchangeAcceptedBlockerCandidateConsume`.
5. Updated MCP Tool Surface Audit and scheduler MCP smoke prompts with the
   accepted blocker candidate consumer boundary.

Validation:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_exchange_action_consumers.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py
```

Passed.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "accepted_review_candidate or consume_accepted_review_candidate or accepted_scheduler_candidate_consumer_reports_exchange_store_consumption or agent_exchange_accepted_review_candidate_consume" -q
```

Result: `6 passed, 188 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "agent_exchange or accepted_scheduler_candidate or accepted_review_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or inspect_agent_action_candidates or decide_agent_action_candidate" -q
```

Result: `36 passed, 158 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke" -q
```

Result: `1 passed, 20 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or accepted_scheduler_candidate or accepted_review_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or inspect_agent_action_candidates or decide_agent_action_candidate or scheduler_mcp_smoke" -q
```

Result: `38 passed, 177 deselected`.

Handoff follow-up validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "accepted_handoff_candidate or consume_accepted_handoff_candidate or agent_exchange_accepted_handoff_candidate_consume" -q
```

Result: `5 passed, 194 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or accepted_scheduler_candidate or accepted_review_candidate or accepted_handoff_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or consume_accepted_handoff_candidate or inspect_agent_action_candidates or decide_agent_action_candidate or scheduler_mcp_smoke" -q
```

Result: `43 passed, 177 deselected`.

Merge follow-up validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "accepted_merge_candidate or consume_accepted_merge_candidate or agent_exchange_accepted_merge_candidate_consume" -q
```

Result: `5 passed, 199 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or accepted_scheduler_candidate or accepted_review_candidate or accepted_handoff_candidate or accepted_merge_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or consume_accepted_handoff_candidate or consume_accepted_merge_candidate or inspect_agent_action_candidates or decide_agent_action_candidate or scheduler_mcp_smoke" -q
```

Result: `48 passed, 177 deselected`.

Blocker follow-up validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "accepted_blocker_candidate or consume_accepted_blocker_candidate or agent_exchange_accepted_blocker_candidate_consume" -q
```

Result: `5 passed, 204 deselected`.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or accepted_scheduler_candidate or accepted_review_candidate or accepted_handoff_candidate or accepted_merge_candidate or accepted_blocker_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or consume_accepted_handoff_candidate or consume_accepted_merge_candidate or consume_accepted_blocker_candidate or inspect_agent_action_candidates or decide_agent_action_candidate or scheduler_mcp_smoke" -q
```

Result: `53 passed, 177 deselected`.

```text
mcp__doc_based_coding.analyze_changes
```

Result:

- Impact graph: no direct/transitive baseline nodes reported.
- Coupling alert: `coupling-mcp-tools-registration`.
- Coverage: `src/mcp/server.py` list/call route was updated and covered by
  MCP server route tests. The final checks after review, handoff, merge, and
  blocker prompt/audit updates reported the same single MCP registration
  coupling alert.

```powershell
git diff --check -- src/runtime/orchestration/agent_exchange_action_consumers.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py design_docs/stages/planning-gate/2026-06-22-agent-communication-non-scheduler-consumer-matrix.md
```

Result: no whitespace errors; Windows line-ending warnings only.
