# Planning Gate - Agent Communication Reply And Lifecycle

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-agent-communication-routing-inbox.md`
completed the per-agent mailbox read model over `ExchangeArtifact` records.

That makes coordination products visible to an agent, but it still leaves the
next step implicit:

```text
how does an agent reply to a coordination artifact?
how does an agent mark one exact artifact version accepted, rejected,
superseded, archived, or consumed without writing ad hoc store code?
```

## Problem

Without a shared reply/lifecycle surface, each agent runtime or operator would
have to manually create reply artifacts and mutate lifecycle states. That would
fragment causality, logs, and audit clues.

The project already has `ExchangeArtifact.causality.replies_to` and
`ExchangeArtifact.lifecycle_state`, so this slice should not invent a separate
chat thread or lifecycle store. It should provide the smallest write surface
over the existing exact-version artifact store.

## Scope

### Slice 1 - Reply Artifact Helper

Add a runtime helper that:

1. reads one exact source artifact version;
2. creates a new exact-version reply `ExchangeArtifact`;
3. sets `causality.replies_to` to the source artifact id/version token;
4. defaults reply audience to the source producer;
5. carries text and optional structured payload;
6. appends a compact `log` part;
7. writes the reply artifact to the same `JsonArtifactVersionStore`.

### Slice 2 - Lifecycle Transition Helper

Add a runtime helper that:

1. reads one exact artifact version;
2. replaces only that exact stored version;
3. changes lifecycle to an allowed first-slice target state;
4. appends a compact `log` part with actor, timestamp, action, and reason;
5. is idempotent when the exact version is already in the target state.

Allowed target states for this slice:

```text
accepted
rejected
consumed
superseded
archived
```

### Slice 3 - CLI/MCP Surfaces

Expose the same helpers as:

```text
doc-based-coding scheduler reply-exchange-artifact
doc-based-coding scheduler transition-exchange-artifact
agentExchangeReply
agentExchangeTransition
```

These are ExchangeArtifact store mutation surfaces only.

## Non-Goals

This gate does not:

1. add raw transcript persistence;
2. create a general chat system;
3. admit scheduler tasks;
4. run providers;
5. refresh scheduler projection;
6. mutate Local Work Trajectory from runtime/CLI/MCP code;
7. implement a full lifecycle state machine;
8. mark related input artifacts consumed automatically;
9. create agent home or scratch directories;
10. perform scheduler handoff/review integration.

## Acceptance Criteria

The gate may close only when:

1. runtime code can create and store a reply artifact with causality/log clues;
2. runtime code can transition one exact artifact version and preserve store
   ordering;
3. idempotent lifecycle transition is visible and non-mutating;
4. CLI and MCP surfaces expose reply and transition behavior;
5. mailbox/readback can observe resulting reply and lifecycle states;
6. tool-audit and prompt docs mention the surfaces;
7. focused runtime, CLI, MCP, prompt, diff-check, and change-analysis
   validation pass.

## Residual Risk After Close

This slice creates the first write-side communication loop, but it is still not
the complete agent collaboration workflow. Later slices need structured reply
templates by artifact kind, scheduler handoff/review integration, consumption
policy over related artifacts, and history compaction.

## Implementation Notes

### 2026-06-22 - Runtime Reply And Lifecycle Helpers

Implemented:

1. `src/runtime/orchestration/agent_exchange_actions.py`;
2. `reply_to_exchange_artifact()`;
3. `transition_exchange_artifact_lifecycle()`;
4. `AgentExchangeReplyResult`;
5. `AgentExchangeTransitionResult`;
6. exports from `src.runtime.orchestration`.

Reply behavior:

1. reads one exact source artifact version from `JsonArtifactVersionStore`;
2. creates a new exact-version reply `ExchangeArtifact`;
3. sets `causality.replies_to` and `caused_by` to the source
   `artifact_id@version` token;
4. defaults reply audience to the source producer;
5. preserves task/lane/context scope while setting reply `scope.agent_id` to
   the replying producer;
6. writes text and optional structured payload;
7. appends a compact `log` part with action
   `exchange_artifact_replied`.

Lifecycle transition behavior:

1. reads one exact stored artifact version;
2. replaces only that exact version;
3. allows first-slice target states `accepted`, `rejected`, `consumed`,
   `superseded`, and `archived`;
4. appends a compact `log` part with actor, timestamp, action, and reason;
5. returns `changed=false` without rewriting the store when the exact version
   is already in the target state.

Boundary:

1. mutates only the local ExchangeArtifact store;
2. does not admit scheduler tasks;
3. does not run providers;
4. does not write admission ledgers;
5. does not refresh scheduler projection;
6. does not create agent home or scratch directories;
7. does not mutate Local Work Trajectory from runtime code.

### 2026-06-22 - CLI/MCP Surfaces And Prompt Discovery

Implemented:

1. CLI `doc-based-coding scheduler reply-exchange-artifact`;
2. CLI `doc-based-coding scheduler transition-exchange-artifact`;
3. MCP tool `agentExchangeReply`;
4. MCP tool `agentExchangeTransition`;
5. MCP server schema and call routing;
6. tool-audit entries in `design_docs/tooling/MCP Tool Surface Audit.md`;
7. scheduler MCP smoke prompt entries in the local prompt and bootstrap copy.

The existing mailbox read model can observe both sides of the loop:

1. the reply artifact appears in the replying agent's outbox;
2. the reply artifact appears in the source producer's inbox;
3. transitioned lifecycle states are visible in mailbox/readback output.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_exchange or inspect_agent_mailbox or scheduler_mcp_smoke" -q
9 passed, 175 deselected

.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/agent_exchange_actions.py src/runtime/orchestration/agent_communication.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

git diff --check over slice files
passed with Windows line-ending warnings only

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and focused MCP
server route tests for agentExchangeReply and agentExchangeTransition.
```
