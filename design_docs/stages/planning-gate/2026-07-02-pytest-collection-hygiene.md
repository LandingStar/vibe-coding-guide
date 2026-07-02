# Planning Gate - Pytest Collection Hygiene

Date: 2026-07-02

Status: COMPLETED

## Purpose

Fix the repo-root pytest collection path so broad smoke commands do not recurse
into runtime or temporary work directories.

The previous smoke sweep proved all `tests/` smoke nodes pass, but
`python -m pytest -k smoke` from the repository root failed during collection
with a Windows `PermissionError` under `tmp/pytest`. That is a collection
hygiene problem, not a smoke-test failure.

## Scope

- Add root pytest collection configuration.
- Keep default pytest collection focused on `tests/`.
- Exclude common runtime/cache/temp output directories from recursive
  collection.
- Validate repo-root smoke selection and focused smoke node count.
- Update Checklist and Local Work Trajectory.

## Non-Goals

- Do not change test behavior or assertions.
- Do not delete `tmp/pytest` or other user/runtime files.
- Do not modify release packaging behavior unless validation proves it is
  affected.
- Do not broaden this gate into full test-suite runtime cleanup.

## Acceptance Criteria

1. `python -m pytest -k smoke -q --color=no` from repo root no longer touches
   `tmp/pytest`.
2. `python -m pytest tests -k smoke -q --color=no` still passes.
3. Smoke collection still reports the expected `tests/` smoke node count.
4. `git diff --check` passes for touched files.

## Completion Notes

Implemented on 2026-07-02.

Added root pytest collection configuration in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
norecursedirs = [
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "release",
    "tmp",
]
```

This keeps default pytest collection focused on the authoritative test suite
and prevents root-level pytest commands from recursing into runtime/temp
artifacts such as `tmp/pytest`.

Validation passed:

```text
python -m pytest -k smoke -q --color=no
52 passed, 1 skipped, 2233 deselected

python -m pytest tests -k smoke -q --color=no
52 passed, 1 skipped, 2233 deselected

python -m pytest --collect-only -q --color=no
ROOT_COLLECT_SMOKE_NODE_COUNT=53

git diff --check -- pyproject.toml design_docs/stages/planning-gate/2026-07-02-pytest-collection-hygiene.md "design_docs/Project Master Checklist.md" .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors; it only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files. A
tailing-whitespace scan over `pyproject.toml` and this gate returned no
matches.
