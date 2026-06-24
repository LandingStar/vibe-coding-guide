# Planning Gate - Agent Communication History Summary

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-agent-communication-routing-inbox.md`
completed the per-agent read model, and
`design_docs/stages/planning-gate/2026-06-22-agent-communication-reply-and-lifecycle.md`
completed the first write-side reply/lifecycle loop.

The next missing product is not another mutation surface. Agents and guide
agents need a compact history view answering:

```text
what happened in this exchange?
which artifacts replied to, caused, superseded, or depended on which others?
which compact log entries are available for review?
which participants appear in the exchange history?
```

## Problem

Without a shared history summary, each runtime adapter, guide agent, or UI
surface would have to scan raw store records directly and re-derive causality,
participants, lifecycle counts, and log timelines. That would encourage ad hoc
conversation-history handling and weaken the artifact-centered communication
contract.

The project already has the needed raw materials:

1. `ExchangeArtifact.causality`;
2. `ExchangeArtifact.parts[]` with `log` parts;
3. `JsonArtifactVersionStore`;
4. `CoordinationEvent.to_exchange_log()` for future event-log bridges.

This slice should make those materials readable as one compact product without
introducing a chat transcript store.

## Scope

### Slice 1 - Runtime Read Model

Add a read-only runtime facility that builds a compact communication history
summary over stored `ExchangeArtifact` versions.

It should report:

1. store path / existence / isolated read errors;
2. artifact and version counts;
3. participant counts derived from producer, audience, visibility audience,
   scope agent, log actors, and relation endpoints;
4. lifecycle counts;
5. causality edges from `replies_to`, `depends_on`, `supersedes`, and
   `caused_by`;
6. compact log entries ordered by timestamp / sequence / store order;
7. optional filtering by `agent_id` and `correlation_id`.

### Slice 2 - Redacted Timeline Entries

The history summary may expose metadata, causality, lifecycle state, and log
entries. It must not expose raw text or structured payload contents from
sensitive or redaction-required artifacts.

### Slice 3 - CLI/MCP/Resource Surface

Expose the same read model through:

```text
doc-based-coding scheduler inspect-agent-history
agentExchangeHistory
dbc://agent-exchange/history
```

All three surfaces are read-only.

## Non-Goals

This gate does not:

1. store raw transcripts;
2. create a general chat system;
3. mutate ExchangeArtifact lifecycle;
4. create reply artifacts;
5. admit scheduler tasks;
6. run providers;
7. refresh scheduler projection;
8. create agent home or scratch directories;
9. mutate Local Work Trajectory from runtime/CLI/MCP code;
10. implement scheduler handoff/review integration.

## Acceptance Criteria

The gate may close only when:

1. runtime code can summarize ExchangeArtifact history from in-memory records;
2. runtime code can inspect a JSON artifact store into the same history shape;
3. causality edges cover replies, depends, supersedes, and caused-by;
4. log entries include timestamp, actor, action, channel, summary, related
   artifact ids, and source artifact/version clues;
5. participant and lifecycle counts are covered by focused tests;
6. sensitive/redaction-required artifacts do not expose raw text or structured
   payload content in the history summary;
7. CLI, MCP tool, and resource surfaces expose the same read model;
8. tool-audit and prompt docs mention the surface;
9. focused runtime, CLI, MCP/resource, prompt, diff-check, and change-analysis
   validation pass.

## Residual Risk After Close

This slice gives guide agents and runtime agents a shared communication-history
read model. It still does not decide which history should trigger scheduler
admission, handoff, review, retention, or compaction. Those remain later
coordination-policy slices.

## Implementation Notes

### 2026-06-22 - Runtime History Summary

Implemented:

1. `src/runtime/orchestration/agent_exchange_history.py`;
2. `AgentExchangeHistorySummary`;
3. `AgentExchangeCausalityEdge`;
4. `AgentExchangeHistoryLogEntry`;
5. `build_agent_exchange_history_summary()`;
6. `inspect_agent_exchange_history_summary()`;
7. exports from `src.runtime.orchestration`.

The read model reports:

1. store path, existence, and isolated read errors;
2. artifact/version counts;
3. participant counts from producer, audience, visibility audience, scope
   agent, relation endpoints, contract parties, refs, and log actors;
4. lifecycle counts;
5. causality edges from `replies_to`, `depends_on`, `supersedes`, and
   `caused_by`;
6. compact log entries with timestamp, actor, action, channel, summary,
   related artifact/event/run ids, sequence, clock, and source artifact/version
   clues;
7. optional `agent_id`, `correlation_id`, and `include_archived` filters.

Sensitive or redaction-required artifacts remain visible through metadata,
causality, lifecycle, and compact log clues, but the history summary does not
expose raw text or structured payload content.

### 2026-06-22 - CLI/MCP/Resource Surfaces

Implemented:

1. CLI `doc-based-coding scheduler inspect-agent-history`;
2. MCP tool `agentExchangeHistory`;
3. read-only resource `dbc://agent-exchange/history`;
4. tool-audit entry in `design_docs/tooling/MCP Tool Surface Audit.md`;
5. scheduler MCP smoke prompt entries in local prompt and bootstrap copy.

All surfaces remain read-only:

1. no scheduler mutation;
2. no ExchangeArtifact store mutation;
3. no admission ledger mutation;
4. no provider execution;
5. no scheduler projection refresh;
6. no Local Work Trajectory mutation from runtime/CLI/MCP code.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py -q
10 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange_history or inspect_agent_history or scheduler_mcp_smoke" -q
9 passed, 183 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or inspect_agent_history or scheduler_mcp_smoke" -q
17 passed, 175 deselected

.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

git diff --check over slice files
passed with Windows line-ending warnings only

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and focused MCP
server route/resource tests for agentExchangeHistory and
dbc://agent-exchange/history.
```
