"""Conventional workspace artifact paths for DBC-owned runtime state."""

from __future__ import annotations

from pathlib import Path

DBC_ARTIFACT_ROOT = ".dbc"
LEGACY_CODEX_ARTIFACT_ROOT = ".codex"


def dbc_artifact_path(*parts: str) -> str:
    """Return a relative path under the DBC runtime artifact root."""

    return str(Path(DBC_ARTIFACT_ROOT).joinpath(*parts).as_posix())


DEFAULT_DBC_SCRATCH_ROOT = dbc_artifact_path("scratch")


def legacy_codex_artifact_path(*parts: str) -> str:
    """Return the previous relative path for legacy read compatibility."""

    return str(Path(LEGACY_CODEX_ARTIFACT_ROOT).joinpath(*parts).as_posix())


def legacy_artifact_path(relative_path: str | Path) -> Path:
    """Map a DBC relative path to its legacy .codex relative path."""

    path = Path(relative_path)
    parts = path.parts
    if not parts or parts[0] != DBC_ARTIFACT_ROOT:
        return path
    return Path(LEGACY_CODEX_ARTIFACT_ROOT, *parts[1:])


def project_root_from_artifact_path(path: str | Path) -> Path:
    """Infer the workspace root from a path under a DBC or legacy artifact root."""

    artifact_path = Path(path)
    parts = artifact_path.parts
    for marker in (DBC_ARTIFACT_ROOT, LEGACY_CODEX_ARTIFACT_ROOT):
        if marker not in parts:
            continue
        index = parts.index(marker)
        if index > 0:
            return Path(*parts[:index])
        return Path(".")
    return artifact_path.parent


def resolve_existing_artifact_path(
    project_root: str | Path,
    relative_path: str | Path,
    *,
    legacy_fallback: bool = True,
) -> Path:
    """Resolve a workspace artifact path, falling back to legacy .codex reads."""

    root = Path(project_root)
    requested = root / relative_path
    if requested.exists() or not legacy_fallback:
        return requested
    legacy = root / legacy_artifact_path(relative_path)
    if legacy != requested and legacy.exists():
        return legacy
    return requested
