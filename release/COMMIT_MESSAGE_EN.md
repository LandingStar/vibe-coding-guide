# Commit Message (English)

```
release: finalize the v0.9.5 preview release surface and packaging consistency

Complete the progress-graph artifact consistency audit and converge the runtime, official instance, pack manifest, and release docs on 0.9.5. Harden the release pipeline with VSIX build/sync, stale artifact cleanup, Windows npm resolution, and installed-state MCP verification so the preview artifacts, version surfaces, and installation path stay aligned.

## Changes

- Refresh the real `.codex/progress-graph/latest.json`, `.dot`, and `.html` artifacts to remove the stale-artifact drift introduced after the recency-semantics safe stop, and recheck direction-candidate status consistency
- Synchronize the dual-package release surface to `0.9.5`, including the runtime, instance pack, pack manifest, official instance `__version__` / `runtime_compatibility`, and release docs
- Align the release docs and artifact surface on VS Code extension version `0.1.3`
- Update `scripts/release.py` to read the current extension version from `vscode-extension/package.json`, build and sync the VSIX into `release/`, and remove stale wheel / VSIX artifacts from older batches
- Resolve `npm.cmd` explicitly on Windows so Python subprocess packaging does not fail when `npm` is not shell-resolved
- Keep the delivery boundary unchanged: `doc-based-coding-v0.9.5.zip` continues to contain only the two wheels and release docs, while the VSIX remains a separate artifact

## Verified

- `pytest tests/test_progress_graph_doc_projection.py -q`: 3 passed
- `pytest tests -v --tb=short`: 1366 passed, 2 skipped
- `release/verify_version_consistency.py`: All versions consistent
- `scripts/release.py --no-isolation`: generated `release/doc-based-coding-v0.9.5.zip`
- `scripts/release.py --skip-tests --no-isolation`: generated and synced `release/doc-based-coding-0.1.3.vsix`
- Installed-state validation: `doc-based-coding-mcp --help`, `doc-based-coding info`, `doc-based-coding validate`, and `pytest tests/test_dual_package_distribution.py -q` (6 passed)
```
