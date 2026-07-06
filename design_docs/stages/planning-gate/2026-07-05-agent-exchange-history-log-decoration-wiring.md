# Planning Gate - Agent Exchange History Log Decoration Wiring

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Wire runtime log decoration into the agent communication history readback path.

Exchange history is the primary compact audit surface for agent-to-agent
communication products. Decorating this readback path makes the common log
pipeline useful for communication-history review without changing the exchange
artifact store.

## Scope

1. Add optional `LogDecorationPipeline` support to
   `build_agent_exchange_history_summary()` and
   `inspect_agent_exchange_history_summary()`.
2. Return decoration evidence for each compact log entry.
3. Preserve source artifact id/version clues in bounded fields.
4. Keep default behavior unchanged when no pipeline is provided.
5. Avoid mutating the exchange artifact store, admission ledger, scheduler, or
   Local Work Trajectory.

## Non-Goals

This gate does not:

1. add CLI flags;
2. rewrite ExchangeArtifact payloads;
3. decorate non-log payload parts;
4. change ExchangeArtifact validation or lifecycle behavior;
5. persist decoration evidence as authoritative exchange history.

## Acceptance Criteria

This gate closes only when:

1. Exchange history readback accepts an optional decoration pipeline.
2. Summary JSON exposes decoration evidence while preserving existing
   `log_entries`.
3. Tests prove decorated readback is side-effect free.
4. Tests prove source artifact/version clues are preserved in decorated fields.
5. Existing exchange history tests continue to pass.

## Implementation

Runtime:

- `AgentExchangeHistorySummary` now carries `log_decoration_results`.
- `build_agent_exchange_history_summary()` and
  `inspect_agent_exchange_history_summary()` accept optional
  `decoration_pipeline`.
- Exchange history log entries are projected back through the existing
  `ExchangeLog` adapter with source artifact/version fields attached.

Docs:

- `docs/runtime-log-decoration-contract.md` documents exchange history
  readback wiring.

Tests:

- Added decorated exchange history readback coverage in
  `tests/test_runtime_orchestration_agent_communication.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/log_decoration.py src/runtime/orchestration/log_decoration_adapters.py tests/test_runtime_orchestration_agent_communication.py
passed

python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "agent_exchange_history" -q
4 passed, 24 deselected

python -m pytest tests/test_mcp_tools.py -k "AgentExchangeHistory" -q
3 passed, 110 deselected

python -m pytest tests/test_cli.py -k "agent_history" -q
1 passed, 180 deselected

git diff --check -- src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/log_decoration.py src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py tests/test_runtime_orchestration_agent_communication.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-agent-exchange-history-log-decoration-wiring.md design_docs/stages/planning-gate/2026-07-05-runtime-invocation-readback-log-decoration-wiring.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate keeps ExchangeArtifact storage authoritative and immutable during
readback. Decoration evidence is a derived inspection product, not a persisted
exchange lifecycle event.
