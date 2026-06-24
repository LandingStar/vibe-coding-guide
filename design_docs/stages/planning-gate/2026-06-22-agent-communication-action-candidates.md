# Planning Gate: Agent Communication Action Candidates

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

The agent communication base now has:

1. per-agent mailbox readback;
2. exact-version reply artifacts;
3. exact-version lifecycle transitions;
4. compact communication history summaries.

The next missing product is a scheduler-facing bridge that tells guide agents
which communication artifacts look like actionable work candidates.

## Scope

### Slice 1 - Read-Only Runtime Model

Add a runtime read model that inspects existing `ExchangeArtifact` records and
classifies exact artifact versions into action candidates:

1. `scheduler_submission_candidate`
2. `review_candidate`
3. `handoff_candidate`
4. `blocker_candidate`
5. `merge_candidate`

The model must report:

1. source artifact id/version;
2. candidate type;
3. confidence;
4. lifecycle state;
5. producer/audience/scope;
6. structured reasons;
7. relation/ref/contract/admission clues;
8. suggested next surface, if known.

### Slice 2 - CLI/MCP/Resource Surfaces

Expose the same read model through:

```text
doc-based-coding scheduler inspect-agent-action-candidates
agentExchangeActionCandidates
dbc://agent-exchange/action-candidates
```

The CLI and MCP tool may filter by agent id, candidate type, and archived
inclusion.

### Slice 3 - Prompt And Audit Discovery

Update the scheduler MCP smoke prompt and MCP tool audit so agents can
discover this bridge and understand its boundary.

## Non-Goals

This gate does not:

1. admit scheduler submissions;
2. create scheduler tasks;
3. open review records;
4. create handoff files;
5. mutate exchange artifact lifecycle state;
6. mutate admission ledgers;
7. run providers;
8. refresh scheduler projections;
9. mutate Local Work Trajectory from runtime/CLI/MCP code;
10. decide final scheduling policy.

## Acceptance Criteria

1. Runtime code can classify action candidates from in-memory records.
2. Runtime code can inspect a JSON artifact store into the same shape.
3. Scheduler admission candidates reuse existing store inspection semantics
   instead of duplicating admission validation.
4. Review, handoff, blocker, and merge candidates are detected from
   `kind`/`intent` and `relation` parts.
5. Sensitive or redaction-required artifacts expose only compact clues, not raw
   text or structured payload bodies.
6. CLI, MCP tool, and MCP resource expose the same read model.
7. Tool-audit and prompt docs mention the surface.
8. Focused runtime, CLI, MCP/resource, prompt, diff-check, and change-analysis
   validation pass.

## Residual Risk After Close

This slice should only produce candidate readback. Follow-up slices still need
policy and explicit mutation surfaces that decide how a candidate becomes an
actual scheduler admission, review intake, handoff, blocker state, or merge
operation.

## Implementation Notes

### 2026-06-22 - Runtime Action-Candidate Read Model

Implemented:

1. `src/runtime/orchestration/agent_exchange_action_candidates.py`;
2. `AgentExchangeActionCandidate`;
3. `AgentExchangeActionCandidateSummary`;
4. `build_agent_exchange_action_candidates()`;
5. `inspect_agent_exchange_action_candidates()`;
6. runtime exports from `src.runtime.orchestration`.

The read model classifies:

1. `scheduler_submission_candidate` from existing store inspection admission
   candidate semantics via `detect_exchange_artifact_admission_candidates()`;
2. `review_candidate` from `kind=review`, `intent=require_review`, and review
   related relations;
3. `handoff_candidate` from `kind=handoff` and `relation:hands_off`;
4. `blocker_candidate` from `kind=blocker`, `intent=declare_blocked`, and
   blocker/wait relations;
5. `merge_candidate` from `intent=request_merge` and `relation:merges_into`.

Each candidate reports reasons, source artifact/version, lifecycle, producer,
audience, scope, relation/ref/contract/admission clues, and suggested next
surface. Sensitive or redaction-required artifacts preserve compact metadata
but do not expose raw text or structured payload bodies.

### 2026-06-22 - CLI/MCP/Resource Surfaces

Implemented:

1. CLI `doc-based-coding scheduler inspect-agent-action-candidates`;
2. MCP tool `agentExchangeActionCandidates`;
3. read-only resource `dbc://agent-exchange/action-candidates`;
4. tool-audit entry in `design_docs/tooling/MCP Tool Surface Audit.md`;
5. scheduler MCP smoke prompt entries in the local prompt and bootstrap copy.

All surfaces remain read-only:

1. no scheduler mutation;
2. no review mutation;
3. no handoff mutation;
4. no ExchangeArtifact store mutation;
5. no admission ledger mutation;
6. no provider execution;
7. no scheduler projection refresh;
8. no Local Work Trajectory mutation from runtime/CLI/MCP code.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/exchange_store.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "agent_exchange_action_candidates or inspect_agent_action_candidates" -q
7 passed, 171 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke" -q
1 passed, 20 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_help_includes_exchange_artifact_admission or inspect_agent_action_candidates or inspect_agent_history or inspect_agent_mailbox" -q
4 passed, 65 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "agent_exchange_action_candidates or agent_exchange_history or agent_exchange_mailbox" -q
8 passed, 88 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or scheduler_mcp_smoke" -q
24 passed, 175 deselected

git diff --check over slice files
passed with Windows line-ending warnings only

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and focused MCP
server route/resource tests for agentExchangeActionCandidates and
dbc://agent-exchange/action-candidates.
```
