# Commit Message (English)

```text
release: package the v0.9.8 preview release

Package the current Local Work Trajectory and host coordination work into a new
preview release batch: move the runtime and official instance to 0.9.8, bump the
VS Code extension to 0.2.1, keep the graph component dependency pinned, and add
release-time secret hygiene checks.

## Changes

- Add the Local Work Trajectory MCP lifecycle surface and React Flow / ELK UI
- Support multi-line trajectory mapping for lane opening, merge/fan-in, and auxiliary relations
- Re-align docs and generated prompts so Codex remains the primary supported host chain
- Add secret scanning and the Secret Hygiene / Log Redaction standard
- Keep the VSIX graph runtime self-contained with the pinned graph engine tarball
- Refresh package versions, release docs, and official instance pack lock

## Verified

- `python release/verify_version_consistency.py`: passed
- `python scripts/scan_secrets.py --scope worktree`: passed
- `python -m pytest tests/test_doc_loop_prompts.py tests/test_error_recovery.py::TestPipelineInitResilience::test_no_warnings_when_all_packs_valid -q`: 3 passed
- `python scripts/release.py --no-isolation`: built wheels, ran full pytest (`1432 passed, 3 skipped`), packaged `doc-based-coding-0.2.1.vsix`, and generated `release/doc-based-coding-v0.9.8.zip`
```
