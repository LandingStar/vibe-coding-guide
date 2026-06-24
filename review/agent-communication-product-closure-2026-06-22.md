# Agent Communication Product Closure Review

> Date: 2026-06-22
> Scope: agent-centered `ExchangeArtifact` communication product definition,
> read/write facilities, action-candidate bridge, accepted-candidate consumers,
> CLI/MCP exposure, prompts, and focused validation.
> Result: PASS

## Summary

Agent communication is now represented as artifact-centered coordination
products instead of unrestricted shared chat history.

The implemented product line is:

1. `ExchangeArtifact` as the versioned coordination product shell.
2. Per-agent mailbox read model for `inbox`, `outbox`, `related`, and
   `actionable` views.
3. Compact exchange history summary over causality and `log` parts.
4. Exact-version reply and lifecycle transition helpers.
5. Action-candidate detection for scheduler submission, review, handoff,
   blocker, and merge candidates.
6. Action-candidate disposition artifacts for `accept`, `reject`, `defer`,
   and `supersede`.
7. Accepted-candidate consumers for scheduler admission, review intake,
   handoff delivery, explicit merge-gate resolution, and explicit task
   blocking.

## Product Boundary

The closure preserves these boundaries:

1. Text alone does not mutate scheduler, review, handoff, merge, or blocker
   state.
2. `accept` is only a disposition product; real mutation requires the matching
   explicit consumer.
3. Scheduler candidate consumption goes through exact-version scheduler
   admission.
4. Review and handoff candidates use their owner adapters.
5. Merge consumption requires explicit `gateId` and `approved`.
6. Blocker consumption requires explicit `taskId` and `reason`.
7. Sensitive or redaction-required artifacts remain discoverable but do not
   expose raw preview payload content in mailbox/history/candidate read models.
8. Runtime/CLI/MCP agent communication helpers do not mutate Local Work
   Trajectory.

## Main Artifacts

Design and planning:

- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-routing-inbox.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-reply-and-lifecycle.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-history-summary.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-action-candidates.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-action-candidate-disposition.md`
- `design_docs/stages/planning-gate/2026-06-22-accepted-scheduler-candidate-disposition-consumer.md`
- `design_docs/stages/planning-gate/2026-06-22-agent-communication-non-scheduler-consumer-matrix.md`

Runtime:

- `src/runtime/orchestration/agent_communication.py`
- `src/runtime/orchestration/agent_exchange_history.py`
- `src/runtime/orchestration/agent_exchange_actions.py`
- `src/runtime/orchestration/agent_exchange_action_candidates.py`
- `src/runtime/orchestration/agent_exchange_action_disposition.py`
- `src/runtime/orchestration/agent_exchange_action_consumers.py`
- `src/runtime/orchestration/__init__.py`

Host surfaces:

- `src/__main__.py`
- `src/mcp/tools.py`
- `src/mcp/server.py`
- `design_docs/tooling/MCP Tool Surface Audit.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

Tests:

- `tests/test_runtime_orchestration_agent_communication.py`
- `tests/test_cli.py`
- `tests/test_mcp_tools.py`
- `tests/test_doc_loop_prompts.py`

## Surface Coverage

CLI surfaces:

- `doc-based-coding scheduler inspect-agent-mailbox`
- `doc-based-coding scheduler inspect-agent-history`
- `doc-based-coding scheduler inspect-agent-action-candidates`
- `doc-based-coding scheduler decide-agent-action-candidate`
- `doc-based-coding scheduler consume-accepted-scheduler-candidate`
- `doc-based-coding scheduler consume-accepted-review-candidate`
- `doc-based-coding scheduler consume-accepted-handoff-candidate`
- `doc-based-coding scheduler consume-accepted-merge-candidate`
- `doc-based-coding scheduler consume-accepted-blocker-candidate`
- `doc-based-coding scheduler reply-exchange-artifact`
- `doc-based-coding scheduler transition-exchange-artifact`

MCP surfaces:

- `agentExchangeMailbox`
- `agentExchangeHistory`
- `agentExchangeActionCandidates`
- `agentExchangeActionCandidateDecide`
- `agentExchangeAcceptedSchedulerCandidateConsume`
- `agentExchangeAcceptedReviewCandidateConsume`
- `agentExchangeAcceptedHandoffCandidateConsume`
- `agentExchangeAcceptedMergeCandidateConsume`
- `agentExchangeAcceptedBlockerCandidateConsume`
- `agentExchangeReply`
- `agentExchangeTransition`

Resource surfaces:

- `dbc://agent-exchange/history`
- `dbc://agent-exchange/action-candidates`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_communication.py src/runtime/orchestration/agent_exchange_actions.py src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/agent_exchange_action_disposition.py src/runtime/orchestration/agent_exchange_action_consumers.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
```

Focused product validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or decide_agent_action_candidate or consume_accepted_scheduler_candidate or consume_accepted_review_candidate or consume_accepted_handoff_candidate or consume_accepted_merge_candidate or consume_accepted_blocker_candidate or scheduler_mcp_smoke" -q
```

Observed result:

```text
39 passed, 191 deselected
```

Wider related validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -q
```

Observed result:

```text
230 passed
```

Diff check:

```text
git diff --check -- <agent communication runtime/CLI/MCP/test/prompt/doc files>
```

Observed result:

```text
No whitespace errors; Windows line-ending warnings only.
```

Change analysis:

```text
mcp__doc_based_coding.analyze_changes
```

Observed result:

- Impact graph: no direct/transitive baseline nodes reported.
- Coupling alert: `coupling-mcp-tools-registration`.
- Coverage: `src/mcp/server.py` includes both `list_tools` registration and
  `call_tool` routing for the new agent exchange surfaces; focused MCP tests
  cover those routes.

## Residual Risk

This review closes the first agent communication product and facility layer.
It does not claim completion of real multi-agent scheduling, guide/worker
runtime policy, UI integration, raw transcript retention, history compaction,
or real Qoder/opencode execution. Those should proceed as separate
orchestration slices over the now-established exchange artifact surfaces.
