# Self-Check Doctor Framework

Date: 2026-06-29

## Goal

Design and implement the first unified `doc-based-coding doctor` framework so
host-facing self-checks share one contract, registry, CLI, and JSON schema.

This gate follows the contract in:

- `docs/self-check-doctor-contract.md`

## Scope

Implement:

1. `SelfCheckContext`, `SelfCheckResult`, `SelfCheckReport`, and registry /
   runner helpers.
2. `doc-based-coding doctor --profile codex|vscode|runtime|scheduler|mcp|all`.
3. The first production check: `codex.mcp_exposure`, using the existing
   credential-safe Codex MCP exposure diagnostic.
4. Compatibility wiring so `doc-based-coding codex readiness` keeps its
   current top-level fields and exposes the doctor-derived MCP exposure result.
5. Focused tests for registry/profile filtering, status aggregation,
   secret-safe contract, Codex MCP exposure migration, and CLI JSON output.
6. Documentation updates pointing installation/Codex entry guidance to
   `doc-based-coding doctor --profile codex`.

## Non-Goals

- Do not migrate OpenCode, Qoder, scheduler, or VS Code checks beyond leaving
  profile names and registration seams.
- Do not mutate Codex config or call `codex mcp add`.
- Do not start DBC MCP server or call MCP tools from doctor.
- Do not run provider tasks.
- Do not remove existing `codex readiness` compatibility output.
- Do not make bootstrap fail when Codex is unavailable.

## Acceptance Criteria

1. Contract documentation exists and covers positioning, schema, statuses, exit
   codes, registration API, secret-safe rules, and boundaries with existing
   commands.
2. Runtime registry supports private test registries and default production
   registry construction.
3. `doctor --profile codex` runs at least `codex.mcp_exposure`.
4. `doctor --profile all` includes registered checks; empty profiles return a
   structured skipped report.
5. `codex readiness` compatibility output does not regress and uses the same
   Codex MCP exposure check result shape as doctor.
6. Tests prove profile filtering, aggregation, secret-safe output,
   runner/which/path injection, and CLI JSON output.
7. Installation and Codex entry docs point users to doctor for MCP exposure
   diagnosis.
8. Validation commands pass:
   - focused runtime tests;
   - focused CLI tests;
   - `py_compile` for touched Python files;
   - `git diff --check` for touched files.

## Completion Notes

Implemented on 2026-06-29.

Contract:

- `docs/self-check-doctor-contract.md`

Runtime surface:

- `SelfCheckContext`
- `SelfCheckResult`
- `SelfCheckReport`
- `SelfCheckRegistry`
- `SelfCheckDefinition`
- `run_self_check_doctor(...)`
- `build_default_self_check_registry()`
- `doctor_exit_code(...)`

CLI surface:

- `doc-based-coding doctor --profile codex|vscode|runtime|scheduler|mcp|all`

Initial production check:

- `codex.mcp_exposure`

Compatibility:

- `doc-based-coding codex readiness` keeps the existing top-level Codex CLI
  readiness fields and exposes a doctor-derived `mcp_exposure` compatibility
  object with `doctor_check_id="codex.mcp_exposure"`.

Validation results:

- `python -m pytest tests/test_runtime_orchestration.py -k "codex_mcp_exposure or self_check or doctor_exit_code"`
  passed: `7 passed, 393 deselected`.
- `python -m pytest tests/test_cli.py -k "doctor or codex_readiness or top_level_help"`
  passed: `5 passed, 156 deselected`.
- `python -m py_compile src/runtime/orchestration/self_check.py src/runtime/orchestration/codex_mcp_diagnostics.py src/runtime/orchestration/__init__.py src/__main__.py`
  passed.
- `git diff --check` on touched files passed with Windows line-ending warnings
  only.
- Local smoke:
  - `python -m src doctor --profile codex` returned `overall_status=ok` and
    check `codex.mcp_exposure`.
  - `python -m src doctor --profile vscode` returned a structured skipped
    report with no registered checks.
  - `python -m src codex readiness` returned the compatibility
    `mcp_exposure.doctor_check_id`.

Non-goals preserved:

- No OpenCode/Qoder/scheduler readiness migration.
- Doctor does not call MCP tools, start MCP servers, mutate config, run
  providers, or read secret material.
