# Planning Gate: Accepted Scheduler Candidate Disposition Consumer

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

The agent communication flow now has:

1. action-candidate discovery;
2. explicit action-candidate disposition artifacts.

The next narrow bridge is consuming an accepted scheduler submission candidate
disposition through the existing exact-version scheduler admission path.

## Scope

### Slice 1 - Runtime Consumer

Add a helper that:

1. reads one exact disposition artifact;
2. verifies `product_type="agent_exchange_action_candidate_disposition"`;
3. verifies `disposition="accept"`;
4. verifies `candidate_type="scheduler_submission_candidate"`;
5. verifies `target_surface` is compatible with exact scheduler admission;
6. admits the referenced source artifact/version through
   `admit_exchange_artifact_version_with_ledger()`;
7. returns the disposition readback plus the existing admission result.

### Slice 2 - CLI/MCP Surfaces

Expose the helper through:

```text
doc-based-coding scheduler consume-accepted-scheduler-candidate
agentExchangeAcceptedSchedulerCandidateConsume
```

The surfaces must accept the same path controls as exact admission:

1. artifact store path;
2. disposition artifact id/version;
3. scheduler snapshot path;
4. scheduler event log path;
5. admission ledger path;
6. duplicate/replace/consume-on-success options;
7. actor/timestamp.

## Non-Goals

This gate does not:

1. create candidate dispositions;
2. admit non-scheduler candidates;
3. open review records;
4. write handoff JSON;
5. resolve merge gates;
6. run providers;
7. refresh scheduler projections;
8. mutate Local Work Trajectory from runtime/CLI/MCP code.

## Acceptance Criteria

1. Runtime code rejects missing, non-accepted, non-scheduler, or wrong-surface
   dispositions before scheduler mutation.
2. Accepted scheduler dispositions admit the exact referenced source artifact
   through the existing ledger-backed admission helper.
3. CLI and MCP expose the same consumer.
4. Tool-audit and prompt docs mention the surface.
5. Focused runtime, CLI, MCP, prompt, diff-check, and change-analysis
   validation pass.

## Residual Risk After Close

This slice only consumes scheduler submission candidates. Review, handoff,
blocker, and merge candidates still need separate explicit consumer slices.

## Implementation Notes

### 2026-06-22 - Runtime Consumer

Implemented:

1. `src/runtime/orchestration/agent_exchange_action_consumers.py`;
2. `ACCEPTED_SCHEDULER_ADMISSION_TARGET_SURFACES`;
3. `AcceptedSchedulerCandidateConsumptionResult`;
4. `consume_accepted_scheduler_action_candidate()`;
5. runtime exports from `src.runtime.orchestration`.

The helper:

1. reads one exact disposition artifact from the local ExchangeArtifact store;
2. verifies `product_type="agent_exchange_action_candidate_disposition"`;
3. verifies `disposition="accept"`;
4. verifies `candidate_type="scheduler_submission_candidate"`;
5. verifies `target_surface` is one of the exact scheduler admission surfaces;
6. calls `admit_exchange_artifact_version_with_ledger()` for the referenced
   source artifact/version;
7. returns disposition readback and the existing admission result.

### 2026-06-22 - CLI/MCP Surfaces And Prompt Discovery

Implemented:

1. CLI `doc-based-coding scheduler consume-accepted-scheduler-candidate`;
2. MCP tool `agentExchangeAcceptedSchedulerCandidateConsume`;
3. tool-audit entry in `design_docs/tooling/MCP Tool Surface Audit.md`;
4. scheduler MCP smoke prompt entries in the local prompt and bootstrap copy.

Boundary:

1. may write scheduler snapshot/event-log state through exact admission;
2. may write admission ledger records through exact admission;
3. may mark the admitted source artifact consumed only when
   `mark_consumed_on_success` is explicitly requested;
4. does not create disposition artifacts;
5. does not consume non-scheduler candidates;
6. does not open review records;
7. does not write handoff JSON;
8. does not resolve merge gates;
9. does not run providers;
10. does not refresh scheduler projections;
11. does not mutate Local Work Trajectory from runtime/CLI/MCP code.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_exchange_action_consumers.py src/runtime/orchestration/agent_exchange_action_disposition.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/exchange_store.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "accepted_scheduler_candidate_consumer or consume_accepted_scheduler_candidate or accepted_scheduler_candidate_consume" -q
5 passed, 183 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or decide_agent_action_candidate or consume_accepted_scheduler_candidate or scheduler_mcp_smoke" -q
31 passed, 178 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke" -q
1 passed, 20 deselected

git diff --check over slice files
passed with Windows line-ending warnings only

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and focused MCP
server route tests for agentExchangeAcceptedSchedulerCandidateConsume.
```
