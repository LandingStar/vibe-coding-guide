"""Pack discovery — locates pack manifests across project, user-global, and site-packages.

Moved from ``workflow.pipeline`` to ``pack.pack_discovery`` to respect the
layered dependency direction (pack is Layer 1, workflow is Layer 3).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────

MANIFEST_NAMES = ("pack-manifest.json",)
PACK_JSON_SUFFIX = ".pack.json"
CONFIG_FILE = ".codex/platform.json"
USER_DIR_ENV = "DOC_BASED_CODING_USER_DIR"
DEFAULT_USER_DIR_NAME = ".doc-based-coding"


# ── Helpers ───────────────────────────────────────────────────────────────


def user_global_base_dir() -> Path | None:
    """Return the user-global base directory, or None if it does not exist."""
    env = os.environ.get(USER_DIR_ENV)
    if env:
        base = Path(env)
    else:
        base = Path.home() / DEFAULT_USER_DIR_NAME
    return base if base.is_dir() else None


def user_global_packs_dir() -> Path | None:
    """Return the user-global packs directory, or None if it does not exist."""
    base = user_global_base_dir()
    if base is None:
        return None
    packs = base / "packs"
    return packs if packs.is_dir() else None


def read_pack_name(manifest_path: Path) -> str:
    """Read the ``name`` field from a pack manifest without full parsing."""
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return data.get("name", "")
    except Exception:
        return ""


def extract_pack_names(
    discovered: list[tuple[Path, Path]],
) -> set[str]:
    """Extract pack names from already-discovered manifest paths."""
    names: set[str] = set()
    for manifest, _ in discovered:
        name = read_pack_name(manifest)
        if name:
            names.add(name)
    return names


def discover_installed_packs() -> list[tuple[Path, Path]]:
    """Discover pack manifests from pip-installed Python packages.

    Scans ``site-packages`` directories for top-level packages that ship a
    ``pack-manifest.json`` file.  This enables ``pip install`` as the sole
    adoption step for official instance packs.
    """
    results: list[tuple[Path, Path]] = []
    try:
        import site
        import sys

        # Collect all site-packages directories
        site_dirs: list[str] = []
        try:
            site_dirs.extend(site.getsitepackages())
        except AttributeError:
            pass  # Not available in some virtualenvs
        user_site = getattr(site, "getusersitepackages", lambda: None)()
        if user_site:
            site_dirs.append(user_site)
        # Also check sys.path entries that look like site-packages
        for p in sys.path:
            if "site-packages" in p and p not in site_dirs:
                site_dirs.append(p)

        seen: set[Path] = set()
        for site_dir in site_dirs:
            sp = Path(site_dir)
            if not sp.is_dir():
                continue
            try:
                for child in sp.iterdir():
                    if not child.is_dir():
                        continue
                    manifest = child / "pack-manifest.json"
                    if manifest.exists() and child not in seen:
                        results.append(
                            (manifest.resolve(), child.resolve())
                        )
                        seen.add(child)
            except OSError:
                continue
    except Exception:
        pass  # site module unavailable or broken — skip silently
    return results


def resolve_pack_dirs(
    project_root: Path, dirs: list[str]
) -> list[tuple[Path, Path]]:
    """Resolve explicit pack_dirs from config to (manifest, base_dir) pairs."""
    results: list[tuple[Path, Path]] = []
    for d in dirs:
        dir_path = (project_root / d).resolve()
        if not dir_path.is_dir():
            continue
        # Look for manifest in directory
        for name in MANIFEST_NAMES:
            manifest = dir_path / name
            if manifest.exists():
                results.append((manifest, dir_path))
                break
        else:
            # Check for *.pack.json files
            for f in sorted(dir_path.iterdir()):
                if f.name.endswith(PACK_JSON_SUFFIX):
                    results.append((f, dir_path))
    return results


# ── Main entry point ──────────────────────────────────────────────────────


def discover_packs(
    project_root: Path,
    *,
    include_site_packages: bool = True,
    include_user_global: bool = True,
    extra_pack_dirs: tuple[str, ...] = (),
) -> list[tuple[Path, Path]]:
    """Auto-discover pack manifests under project_root.

    Returns list of (manifest_path, base_dir) tuples, ordered by kind
    priority (platform → instance → user-global → project-local).

    Discovery rules:
    0. User-global packs from ``~/.doc-based-coding/packs/`` (or DOC_BASED_CODING_USER_DIR).
    0b. Extra pack directories from user config ``extra_pack_dirs``.
    1. If .codex/platform.json exists and has ``pack_dirs``, use those.
    2. Otherwise scan:
       a. {root}/.codex/packs/*.pack.json
       b. {root}/*/pack-manifest.json (one-level subdirs)
       c. Installed Python packages carrying pack-manifest.json (via importlib.metadata)

    Args:
        include_site_packages: When False, skip scanning site-packages for
            installed packs.  Useful in tests that need full isolation.
        include_user_global: When False, skip scanning user-global packs
            directory.  Useful in tests that need full isolation.
        extra_pack_dirs: Additional directories to scan for packs (from
            user config).
    """
    # ── User-global packs ─────────────────────────────────────────────────
    user_results: list[tuple[Path, Path]] = []
    if include_user_global:
        user_dir = user_global_packs_dir()
        if user_dir is not None:
            for f in sorted(user_dir.iterdir()):
                if f.is_file() and (
                    f.name.endswith(PACK_JSON_SUFFIX)
                    or f.name in MANIFEST_NAMES
                ):
                    user_results.append((f, user_dir))

    # ── Extra pack dirs (from user config) ────────────────────────────────
    if extra_pack_dirs:
        seen_extra: set[Path] = set()
        for raw_dir in extra_pack_dirs:
            d = Path(raw_dir).expanduser().resolve()
            if not d.is_dir() or d in seen_extra:
                continue
            seen_extra.add(d)
            for f in sorted(d.iterdir()):
                if f.is_file() and (
                    f.name.endswith(PACK_JSON_SUFFIX)
                    or f.name in MANIFEST_NAMES
                ):
                    user_results.append((f, d))

    # ── Workspace packs ───────────────────────────────────────────────────
    config_path = project_root / CONFIG_FILE
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            dirs = config.get("pack_dirs", [])
            if dirs:
                results = resolve_pack_dirs(project_root, dirs)
                # Also scan .codex/packs/ for standalone pack files
                # not covered by explicit pack_dirs entries
                packs_dir = project_root / ".codex" / "packs"
                if packs_dir.is_dir():
                    seen_dirs = {r[1] for r in results}
                    seen_names = extract_pack_names(results)
                    for f in sorted(packs_dir.iterdir()):
                        if (
                            f.is_file()
                            and (
                                f.name.endswith(PACK_JSON_SUFFIX)
                                or f.name in MANIFEST_NAMES
                            )
                            and packs_dir not in seen_dirs
                        ):
                            name = read_pack_name(f)
                            if name and name not in seen_names:
                                results.append((f, packs_dir))
                                seen_names.add(name)
                    seen_dirs.add(packs_dir)  # prevent re-scan

                # Even with explicit config, also discover installed packs
                # to avoid requiring manual wiring for pip-installed packs
                if include_site_packages:
                    installed = discover_installed_packs()
                    seen_dirs = {r[1] for r in results}
                    seen_names = extract_pack_names(results)
                    for manifest, base in installed:
                        if base not in seen_dirs:
                            name = read_pack_name(manifest)
                            if name and name not in seen_names:
                                results.append((manifest, base))
                                seen_dirs.add(base)
                                seen_names.add(name)
                return user_results + results
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to convention-based discovery

    results: list[tuple[Path, Path]] = []

    # .codex/packs/*.pack.json
    packs_dir = project_root / ".codex" / "packs"
    if packs_dir.is_dir():
        for f in sorted(packs_dir.iterdir()):
            if f.name.endswith(PACK_JSON_SUFFIX) or f.name in MANIFEST_NAMES:
                results.append((f, packs_dir))

    # */pack-manifest.json (one-level subdirs)
    if project_root.is_dir():
        for child in sorted(project_root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                manifest = child / "pack-manifest.json"
                if manifest.exists():
                    results.append((manifest, child))

    # Installed Python packages carrying pack-manifest.json
    if include_site_packages:
        installed = discover_installed_packs()
        seen_dirs = {r[1] for r in results}
        seen_names = extract_pack_names(results)
        for manifest, base in installed:
            if base not in seen_dirs:
                name = read_pack_name(manifest)
                if name and name not in seen_names:
                    results.append((manifest, base))
                    seen_dirs.add(base)
                    seen_names.add(name)

    return user_results + results
