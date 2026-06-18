# Review - Stored-Artifact MCP Admission Tool

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-stored-artifact-mcp-admission-tool.md`

## Scope Reviewed

This slice exposed exact stored scheduler submission admission through MCP
while reusing the durable ExchangeArtifact admission ledger policy created in
the previous gate.

Implemented:

1. Shared runtime admission policy:
   - `admit_exchange_artifact_version_with_ledger()`
   - CLI and MCP now use the same duplicate/audit behavior.
2. MCP tool surface:
   - `GovernanceTools.admit_exchange_artifact()`
   - MCP server tool name `admitExchangeArtifact`
   - required fields `artifactId`, `version`, `snapshotPath`, `eventLogPath`
   - optional fields `artifactStorePath`, `admissionLedgerPath`,
     `allowDuplicateAdmission`, `replaceExisting`, `actor`, and `timestamp`
3. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
4. Tests covering successful MCP admission, duplicate rejection, explicit
   duplicate replay, missing inputs, and MCP server exposure/routing.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py::TestAdmitExchangeArtifact tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_submits_exact_single_task tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_rejects_duplicate_before_scheduler_mutation tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_allows_explicit_duplicate_admission
8 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py::TestAdmitExchangeArtifact
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
279 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py::test_admit_exchange_artifact_version_with_ledger_rejects_duplicate_before_scheduler_mutation
1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
198 passed
```

`tests/test_mcp_tools.py` is a local ignored MCP test harness in this
workspace. The committed regression surface for this slice is
`tests/test_mcp_admission.py` plus the existing tracked CLI/runtime/doc-loop
tests.

## Behavioral Notes

`admitExchangeArtifact` admits one exact stored `ExchangeArtifact` version into
scheduler snapshot/event-log state. Relative paths resolve under the MCP
project root. If paths are omitted where defaults are allowed, the tool uses
`.codex/orchestration/exchange-artifacts.json` and
`.codex/orchestration/exchange-artifact-admissions.json`.

The returned payload uses snake_case and includes scheduler and ledger clues:
`artifact_store_path`, `admission_ledger_path`,
`admission_ledger_record_id`, source artifact identity, submitted task IDs,
dependency IDs, submission event IDs, task/dependency counts, `ran_tasks=false`,
`refreshed_projection=false`, and `authority_split`.

Duplicate exact artifact/version admission is rejected by default before
scheduler mutation when a prior `admitted` ledger record exists. The rejection
returns a structured non-throwing `ok=false` payload and appends
`rejected_duplicate` to the ledger.

Intentional duplicate replay requires `allowDuplicateAdmission=true`.
`replaceExisting` remains scheduler task replacement semantics only and does
not bypass duplicate admission policy.

## Explicit Non-Goals Preserved

This slice did not add:

1. Scheduler daemon or durable queue behavior.
2. Provider execution through MCP.
3. Automatic scheduler projection refresh.
4. UI binding.
5. Exchange-store consumed marking or lifecycle mutation.
6. Scheduler snapshot/event-log authority redesign.
7. Local Work Trajectory mutation from scheduler admission.
8. Broad exchange artifact write/update tools beyond exact scheduler
   admission.

## Follow-Up

The MCP admission surface closes the immediate agent-callable exact admission
gap. The strongest next narrow candidate is exchange artifact lifecycle /
consumed-state projection, because operators and agents can now admit artifacts
through CLI or MCP but still need a first-class way to see whether a stored
artifact version is already admitted without manually joining the artifact
store and admission ledger.

Scheduler daemon processing, provider execution, UI binding, and richer
exchange artifact mutation should remain separate gates.
