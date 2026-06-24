# Planning Gate - Agent Communication Routing Inbox

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/agent-coordination-exchange-artifact-design-record.md` defines
artifact-centered agent communication, and the runtime already has
`ExchangeArtifact`, `JsonArtifactVersionStore`, `JsonlCoordinationEventLog`,
and exchange-store inspection.

However, those surfaces are still store-level. An agent can inspect all stored
coordination products, but there is no compact per-agent read model answering:

```text
what is addressed to me?
what did I produce?
what is related to me but not directly addressed?
which items look actionable?
```

## Problem

Without an agent mailbox/read model, the next orchestration layer would have to
scan raw exchange-store records directly and re-implement routing rules in
each runtime adapter, CLI, MCP tool, or UI surface.

That would weaken the artifact-centered design because "agent communication"
would remain an implicit filtering convention instead of a shared product
contract.

## Scope

### Slice 1 - Runtime Read Model

Add a read-only runtime facility that builds a per-agent mailbox over existing
`ExchangeArtifact` records.

It should classify exact artifact versions into:

1. `inbox`: directly addressed to the agent;
2. `outbox`: produced by the agent;
3. `related`: references, relations, logs, or scope mention the agent without
   direct address;
4. `actionable`: inbox items whose kind/intent/lifecycle imply agent attention.

### Slice 2 - Routing Rules

Routing should derive from existing artifact fields only:

1. `producer`;
2. top-level `audience`;
3. `visibility_policy.audience`;
4. `scope.agent_id`;
5. payload `relation`, `ref`, `contract`, `log`, and structured fields that
   mention the agent id.

No new message schema should be invented.

### Slice 3 - Redacted Preview

Mailbox items should expose compact metadata and a safe preview:

1. artifact id/version;
2. kind/intent/lifecycle/producer/audience/scope;
3. part types;
4. routing reasons;
5. actionable reasons;
6. text/structured preview only when the artifact is not marked sensitive or
   redaction-required.

Sensitive artifacts must remain discoverable but should not expose raw text or
structured payload content in the mailbox preview.

### Slice 4 - Store Inspection Entry

Add a convenience helper that reads a local `JsonArtifactVersionStore` path and
returns the mailbox read model with isolated read errors.

## Non-Goals

This gate does not:

1. add a chat system;
2. persist raw runtime transcripts;
3. mutate `ExchangeArtifact` lifecycle state;
4. mark artifacts consumed;
5. admit scheduler tasks;
6. run agent runtimes;
7. create agent home or scratch directories;
8. mutate Local Work Trajectory from runtime code;
9. add UI binding;
10. add CLI or MCP surfaces in this first slice.

## Acceptance Criteria

The gate may close only when:

1. runtime code can build a per-agent mailbox from in-memory artifact records;
2. runtime code can inspect a JSON artifact store into the same mailbox shape;
3. audience, visibility-policy audience, scope agent, producer, and relation
   references are covered by focused tests;
4. sensitive/redaction-required artifacts are discoverable but do not expose
   raw preview payloads;
5. the helper is exported through `src.runtime.orchestration`;
6. CLI and MCP read surfaces expose the same mailbox shape;
7. prompt/tool-audit docs mention the read surface so agents can discover it;
8. focused tests pass.

## Residual Risk After Close

This slice gives agents a stable read model, but it is not yet a complete
communication workflow. Later slices still need agent-facing CLI/MCP tools,
reply/consume lifecycle affordances, scheduler handoff integration, and
coordination-history compaction policy.

## Implementation Notes

### 2026-06-22 - Runtime Mailbox Read Model

Implemented:

1. `src/runtime/orchestration/agent_communication.py`;
2. `AgentMailboxItem` and `AgentMailbox`;
3. `build_agent_exchange_mailbox()` over already-loaded
   `ArtifactVersionRecord` values;
4. `inspect_agent_exchange_mailbox()` over a JSON artifact store path;
5. exports from `src.runtime.orchestration`;
6. focused tests in
   `tests/test_runtime_orchestration_agent_communication.py`.

Routing rules now cover:

1. direct top-level `audience`;
2. `visibility_policy.audience`;
3. `scope.agent_id`;
4. `producer` as outbox;
5. relation/ref/contract/log/structured payload mentions as related items.

Preview behavior:

1. non-sensitive items expose compact text, structured, relation, ref, or log
   clues;
2. sensitive or redaction-required items expose only metadata, part types, and
   a redaction reason;
3. the mailbox reports `authority_split` as read-model-only with no scheduler,
   exchange-store, or Local Work Trajectory mutation.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/agent_communication.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration_agent_communication.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py -q
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact or agent_home_registration or scratch_manifest or cleanup_receipt" -q
31 passed, 252 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_runtime_orchestration.py -k "agent_mailbox or exchange_artifact_json_round_trip or exchange_artifact_version_store or coordination_event_log" -q
10 passed, 277 deselected
```

### 2026-06-22 - Agent-Facing CLI/MCP Read Surface

Implemented:

1. CLI:

   ```text
   doc-based-coding scheduler inspect-agent-mailbox --agent-id ID
   ```

2. MCP tool:

   ```text
   agentExchangeMailbox
   ```

3. tool-audit entry in `design_docs/tooling/MCP Tool Surface Audit.md`;
4. scheduler MCP smoke prompt entries in the local prompt and bootstrap copy;
5. `.gitignore` test whitelist for
   `tests/test_runtime_orchestration_agent_communication.py`, because this
   repository ignores new `tests/*` files by default.

Both surfaces call the same `inspect_agent_exchange_mailbox()` runtime helper.
They remain read-only and report the same authority split:

1. no scheduler state mutation;
2. no ExchangeArtifact lifecycle mutation;
3. no admission ledger mutation;
4. no provider/runtime execution;
5. no projection refresh;
6. no Local Work Trajectory mutation.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/agent_communication.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py -k "agent_mailbox or agent_exchange_mailbox or inspect_agent_mailbox" -q
7 passed, 151 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_help_includes_exchange_artifact_admission or inspect_binding_refs_help or publish_storage_binding_artifact_help or admit_exchange_artifact_help or inspect_agent_mailbox" -q
5 passed, 61 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "agent_exchange_mailbox or admit_exchange_artifact" -q
7 passed, 81 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke" -q
1 passed, 19 deselected

mcp__doc_based_coding.analyze_changes
impact direct/transitive empty; coupling alert:
coupling-mcp-tools-registration triggered by src/mcp/tools.py.
Satisfied by src/mcp/server.py list_tools/call_tool updates and the focused
MCP server route test for agentExchangeMailbox.

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py -k "agent_mailbox or agent_exchange_mailbox or inspect_agent_mailbox or scheduler_mcp_smoke" -q
8 passed, 170 deselected

.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/agent_communication.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration_agent_communication.py tests/test_cli.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

git diff --check over slice files
passed with Windows line-ending warnings only
```
