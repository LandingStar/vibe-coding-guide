# Dependency Baseline Maintenance Prompt

Use this prompt only when the current task explicitly asks to create, refresh,
generate, validate, repair, roll back, or expand
`tools/dependency_graph/baseline_graph.json`.

Read first:

1. `docs/dependency-baseline-generator-contract.md`
2. `docs/dependency-baseline-maintenance-guide.md`
3. The current planning-gate that authorizes baseline work

Do not run these operations during ordinary implementation work just because
`impact_analysis` reports that no baseline exists.

## Create

Use create only for a first baseline or a deliberately new output path.

Recommended Python command:

```powershell
python -m tools.dependency_graph.reference_adapter create `
  --project-root . `
  --language python `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

If no Pylance fixture exists, create a degraded Python baseline only when the
planning-gate accepts partial coverage. Record that limitation.

## Collect Pylance Fixture

For Python work, prefer Pylance usage data over heuristic relation inference.

When VS Code / Pylance MCP is available:

1. Identify target symbols from the current baseline or adapter output.
2. Prioritize Protocols, public classes, public functions, package exports, and
   recently changed symbols.
3. Call `vscode_listCodeUsages` or an equivalent Pylance usage query for each
   target symbol.
4. Save the result as `tools/dependency_graph/pylance-usages.json`.
5. Run refresh with `--pylance-usage-fixture`.

If Pylance is unavailable, record that the baseline is an AST fallback with
partial Python call/reference coverage.

## Refresh

Use refresh when dependency-relevant structure changed:

- module layout
- public API
- symbol ownership
- generator configuration
- Pylance usage fixture
- JavaScript source coverage

```powershell
python -m tools.dependency_graph.reference_adapter refresh `
  --project-root . `
  --language python `
  --language javascript `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

Refresh should create a backup unless the planning-gate explicitly says not to.

## Generate

Use generate as the low-level scripted operation when an outer workflow already
owns overwrite and backup policy. Prefer create for first adoption and refresh
for ordinary maintenance.

```powershell
python -m tools.dependency_graph.reference_adapter generate `
  --project-root . `
  --language python `
  --language javascript `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

Add `--backup` only when the calling workflow has decided this command should
preserve the previous output.

## Validate

Run after create, refresh, repair, or rollback.

```powershell
python -m tools.dependency_graph.reference_adapter validate --project-root .
python -m pytest tests/test_dependency_graph*.py tests/test_mcp_tools.py -q
```

Check that metadata records source coverage and, for Python enhanced runs,
`pylance-usage-fixture`.

## Repair

Use repair only for mechanical fixes:

- path normalization
- duplicate edge removal
- dropping edges with missing endpoints

```powershell
python -m tools.dependency_graph.reference_adapter repair --project-root .
```

If the issue is semantic coverage, fix the generator or Pylance fixture and run
refresh instead.

## Rollback

Use rollback when a new baseline is worse than the previous one.

```powershell
python -m tools.dependency_graph.reference_adapter rollback `
  --path tools/dependency_graph/baseline_graph.json
```

Then validate and record the restored backup path.

## Expand Language Coverage

To add JavaScript conservative support:

```powershell
python -m tools.dependency_graph.reference_adapter refresh `
  --project-root . `
  --language python `
  --language javascript `
  --pylance-usage-fixture tools/dependency_graph/pylance-usages.json
```

Do not describe JavaScript output as a complete call graph. It covers modules,
classes, functions, imports, require calls, and simple extends clauses.

## Write-Back

Record:

- command run
- languages and include/exclude coverage
- Pylance fixture path or explicit absence
- validation result
- backup/rollback path if any
- known coverage limits
