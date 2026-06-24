# Planning Gate: Agent Communication Action Candidate Disposition

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`2026-06-22-agent-communication-action-candidates.md` added a read-only bridge
that classifies ExchangeArtifacts into scheduler, review, handoff, blocker, and
merge action candidates.

The next missing product is not the final action executor. The missing product
is a standard disposition artifact that records whether a guide agent, operator,
or responsible agent accepts, rejects, defers, or supersedes a specific
candidate.

Without this product, candidate handling would drift back into prose replies.

## Scope

### Slice 1 - Disposition Artifact Contract

Define one exact-version `ExchangeArtifact` product for action-candidate
disposition.

The structured payload should include:

1. `product_type="agent_exchange_action_candidate_disposition"`;
2. `candidate_id`;
3. `candidate_type`;
4. source artifact id/version;
5. disposition: `accept`, `reject`, `defer`, or `supersede`;
6. actor;
7. reason;
8. target surface, if the disposition is accepted;
9. optional replacement artifact/version for supersession.

The artifact should also include:

1. a `ref` part pointing at the source artifact exact version;
2. a compact `log` part;
3. causality linking to the source artifact.

### Slice 2 - Runtime Helper

Add a helper that:

1. reads the action candidate through the existing read model;
2. creates one exact-version disposition ExchangeArtifact;
3. writes only the local ExchangeArtifact store;
4. returns compact readback and authority split.

### Slice 3 - CLI/MCP Surfaces

Expose the helper through:

```text
doc-based-coding scheduler decide-agent-action-candidate
agentExchangeActionCandidateDecide
```

## Non-Goals

This gate does not:

1. admit scheduler submissions;
2. open review records;
3. write handoff JSON;
4. resolve scheduler merge gates;
5. mutate the source artifact lifecycle state;
6. mutate admission ledgers;
7. run providers;
8. refresh scheduler projections;
9. mutate Local Work Trajectory from runtime/CLI/MCP code.

## Acceptance Criteria

1. Runtime code can create a disposition artifact for one exact candidate.
2. The helper validates that the candidate exists in the current candidate
   read model.
3. The disposition artifact is machine-readable and references the exact source
   artifact/version.
4. CLI and MCP surfaces expose the same helper.
5. Tool-audit and prompt docs mention the surface.
6. Focused runtime, CLI, MCP, prompt, diff-check, and change-analysis
   validation pass.

## Residual Risk After Close

This slice records a decision product only. Follow-up slices still need the
policy and explicit executor surfaces that consume accepted dispositions and
perform scheduler admission, review intake, handoff persistence, blocker state
updates, or merge-gate resolution.

## Implementation Notes

### 2026-06-22 - Disposition Artifact Helper

Implemented:

1. `src/runtime/orchestration/agent_exchange_action_disposition.py`;
2. `ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE`;
3. `AgentExchangeActionCandidateDispositionResult`;
4. `decide_agent_exchange_action_candidate()`;
5. runtime exports from `src.runtime.orchestration`.

The helper:

1. resolves the candidate through `inspect_agent_exchange_action_candidates()`;
2. writes a new exact-version disposition `ExchangeArtifact`;
3. stores `product_type="agent_exchange_action_candidate_disposition"`;
4. includes a `ref` to the source artifact exact version;
5. includes compact causality and `log` clues;
6. writes only the local ExchangeArtifact store.

### 2026-06-22 - CLI/MCP Surfaces And Prompt Discovery

Implemented:

1. CLI `doc-based-coding scheduler decide-agent-action-candidate`;
2. MCP tool `agentExchangeActionCandidateDecide`;
3. tool-audit entry in `design_docs/tooling/MCP Tool Surface Audit.md`;
4. scheduler MCP smoke prompt entries in the local prompt and bootstrap copy.

All surfaces remain coordination-product-only:

1. no scheduler admission;
2. no review state mutation;
3. no handoff persistence;
4. no merge gate resolution;
5. no source ExchangeArtifact lifecycle mutation;
6. no admission ledger mutation;
7. no provider execution;
8. no scheduler projection refresh;
9. no Local Work Trajectory mutation from runtime/CLI/MCP code.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_exchange_action_disposition.py src/runtime/orchestration/agent_exchange_action_candidates.py src/runtime/orchestration/exchange_store.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "action_candidate_disposition or decide_agent_action_candidate or agent_exchange_action_candidate_decide" -q
5 passed, 178 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or inspect_agent_history or inspect_agent_action_candidates or decide_agent_action_candidate or scheduler_mcp_smoke" -q
29 passed, 175 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke" -q
1 passed, 20 deselected

git diff --check over slice files
passed with Windows line-ending warnings only

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and focused MCP
server route tests for agentExchangeActionCandidateDecide.
```
