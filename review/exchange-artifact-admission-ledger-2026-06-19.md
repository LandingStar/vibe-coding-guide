# Review - ExchangeArtifact Admission Ledger

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-exchange-artifact-admission-ledger.md`

## Scope Reviewed

This slice added a durable local ledger for exact stored-artifact scheduler
admission attempts and wired it into the CLI operator admission surface.

Implemented:

1. Runtime ledger contract and JSON store:
   - `ExchangeArtifactAdmissionRecord`
   - `JsonExchangeArtifactAdmissionLedger`
   - `ExchangeArtifactAdmissionLedgerInspection`
   - default path
     `.codex/orchestration/exchange-artifact-admissions.json`
2. CLI admission duplicate policy:
   - `--admission-ledger-path`
   - `--allow-duplicate-admission`
   - `--actor`
3. CLI ledger readback:
   - `doc-based-coding scheduler inspect-admissions`
   - optional `--artifact-id` and `--version` filters
4. Scheduler smoke prompt and bootstrap prompt guidance for the expanded
   operator workflow.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
274 passed
```

## Behavioral Notes

Successful CLI admission now appends an `admitted` ledger record after
scheduler snapshot/event-log state is written. The CLI payload includes
`admission_ledger_path`, `admission_ledger_record_id`, and duplicate-policy
clues.

Duplicate exact `(artifact_id, version)` admission is rejected by default before
scheduler mutation when a prior `admitted` record exists. The rejection appends
`rejected_duplicate`, reports `duplicate_of`, and leaves scheduler snapshot and
event-log counts unchanged. `--replace-existing` does not bypass this ledger
policy.

Explicit duplicate admission requires `--allow-duplicate-admission`; when used,
the CLI can still pass `--replace-existing` for scheduler task replacement
semantics, and the ledger records `allow_duplicate=true`.

Admission failures after duplicate preflight append `failed` records when the
CLI has enough artifact identity and path context. Malformed ledger stores
surface readable errors and prevent scheduler mutation before preflight
continues.

`inspect-admissions` is read-only. It returns compact status counts, filtered
records, artifact IDs, errors, and authority clues. It does not mutate
scheduler state, exchange artifacts, projection artifacts, providers, or Local
Work Trajectory.

## Explicit Non-Goals Preserved

This slice did not add:

1. Stored-artifact MCP admission/write tool.
2. Scheduler daemon or durable queue behavior.
3. UI binding.
4. Provider execution.
5. Exchange-store consumed marking or lifecycle mutation.
6. Scheduler snapshot/event-log authority redesign.
7. Local Work Trajectory mutation from scheduler/operator commands.

## Follow-Up

The ledger closes the immediate duplicate/audit gap before broader mutation
surfaces. The strongest next narrow candidate is a stored-artifact MCP admission
tool that wraps the same exact-version admission path and reuses ledger
duplicate policy.

Daemon processing, UI binding, provider execution, and exchange-store lifecycle
consumed marking should remain separate gates.
