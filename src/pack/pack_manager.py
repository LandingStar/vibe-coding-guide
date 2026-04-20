"""Pack management: install, remove, list, info operations.

Provides local pack lifecycle management via `.codex/packs/` and
`.codex/platform.json` integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

_log = logging.getLogger(__name__)


_CONFIG_FILE = ".codex/platform.json"
_PACKS_DIR = ".codex/packs"
_MANIFEST_NAME = "pack-manifest.json"


@dataclass
class PackInfo:
    """Summary information about a discovered pack."""

    name: str
    version: str
    kind: str
    source: str  # "config", "convention", "site-packages", "installed"
    path: Path
    manifest_path: Path
    runtime_compatibility: str = ""
    provides: list[str] | None = None
    checksum: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "kind": self.kind,
            "source": self.source,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "runtime_compatibility": self.runtime_compatibility,
            "provides": self.provides or [],
            "checksum": self.checksum,
        }


def _read_config(project_root: Path) -> dict[str, Any]:
    """Read .codex/platform.json, returning empty dict if not found."""
    config_path = project_root / _CONFIG_FILE
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_config(project_root: Path, config: dict[str, Any]) -> None:
    """Write .codex/platform.json, creating directories as needed."""
    config_path = project_root / _CONFIG_FILE
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_manifest(path: Path) -> dict[str, Any]:
    """Read and parse a pack manifest file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_checksum(path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def _get_runtime_version() -> str:
    """Get the current platform runtime version.

    Tries importlib.metadata first (works for pip-installed package),
    falls back to parsing pyproject.toml from the source tree.
    """
    try:
        from importlib.metadata import version as pkg_version
        return pkg_version("doc-based-coding-runtime")
    except Exception:
        pass
    # Fallback: parse pyproject.toml from source tree
    try:
        pyproject = Path(__file__).resolve().parent.parent.parent / "pyproject.toml"
        if pyproject.exists():
            import re
            text = pyproject.read_text(encoding="utf-8")
            m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1)
    except Exception:
        pass
    return ""


def _check_runtime_compatibility(specifier: str, runtime_version: str) -> bool:
    """Check if *runtime_version* satisfies *specifier* (PEP 440).

    Returns True if compatible, False otherwise.
    Raises ValueError for malformed specifiers.
    """
    if not specifier or not runtime_version:
        return True  # No specifier or no version → skip check
    try:
        spec = SpecifierSet(specifier)
    except InvalidSpecifier as exc:
        raise ValueError(
            f"Invalid runtime_compatibility specifier {specifier!r}: {exc}"
        ) from exc
    return Version(runtime_version) in spec


def list_packs(
    project_root: Path,
    *,
    include_site_packages: bool = True,
) -> list[PackInfo]:
    """List all discovered packs from all sources.

    Sources checked (in order):
    1. .codex/platform.json pack_dirs (source="config")
    2. .codex/packs/ installed packs (source="installed")
    3. Convention scan: */pack-manifest.json (source="convention")
    4. Site-packages auto-discovery (source="site-packages")
    """
    from .pack_discovery import discover_packs

    results: list[PackInfo] = []
    seen_names: set[str] = set()

    # Use the existing discovery mechanism
    discovered = discover_packs(
        project_root, include_site_packages=include_site_packages
    )

    for manifest_path, base_dir in discovered:
        try:
            manifest = _read_manifest(manifest_path)
        except (json.JSONDecodeError, OSError):
            continue

        name = manifest.get("name", "")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        # Determine source type
        packs_dir = (project_root / _PACKS_DIR).resolve()
        base_resolved = base_dir.resolve()
        if base_resolved.is_relative_to(packs_dir):
            source = "installed"
        elif _is_site_packages_path(base_resolved):
            source = "site-packages"
        else:
            # Check if in platform.json pack_dirs
            config = _read_config(project_root)
            pack_dirs = config.get("pack_dirs", [])
            rel = _try_relative(base_resolved, project_root)
            if rel and rel in pack_dirs:
                source = "config"
            else:
                source = "convention"

        # Look up stored checksum
        config_for_checksum = _read_config(project_root)
        stored_checksums = config_for_checksum.get("pack_checksums", {})

        results.append(PackInfo(
            name=name,
            version=manifest.get("version", ""),
            kind=manifest.get("kind", ""),
            source=source,
            path=base_dir,
            manifest_path=manifest_path,
            runtime_compatibility=manifest.get("runtime_compatibility", ""),
            provides=manifest.get("provides"),
            checksum=stored_checksums.get(name, ""),
        ))

    return results


def install_pack(source_path: Path, project_root: Path) -> PackInfo:
    """Install a pack from a local path into .codex/packs/.

    Args:
        source_path: Path to directory containing pack-manifest.json,
                     or path to a pack-manifest.json file directly.
        project_root: Project root directory.

    Returns:
        PackInfo for the installed pack.

    Raises:
        FileNotFoundError: If source_path or manifest doesn't exist.
        ValueError: If manifest is invalid or pack already installed.
    """
    source_path = source_path.resolve()

    # Resolve to directory + manifest
    if source_path.is_file() and source_path.name == _MANIFEST_NAME:
        manifest_path = source_path
        source_dir = source_path.parent
    elif source_path.is_dir():
        manifest_path = source_path / _MANIFEST_NAME
        source_dir = source_path
    else:
        raise FileNotFoundError(f"Not a valid pack source: {source_path}")

    if not manifest_path.exists():
        raise FileNotFoundError(f"No {_MANIFEST_NAME} found at {manifest_path}")

    # Parse manifest
    manifest = _read_manifest(manifest_path)
    name = manifest.get("name")
    if not name:
        raise ValueError(f"Manifest at {manifest_path} has no 'name' field")

    # Runtime compatibility check
    compat_spec = manifest.get("runtime_compatibility", "")
    if compat_spec:
        runtime_ver = _get_runtime_version()
        if runtime_ver and not _check_runtime_compatibility(compat_spec, runtime_ver):
            raise ValueError(
                f"Pack '{name}' requires runtime {compat_spec}, "
                f"but current runtime version is {runtime_ver}."
            )
        elif not runtime_ver:
            _log.warning(
                "Cannot determine runtime version; skipping "
                "runtime_compatibility check for pack %r",
                name,
            )

    # Target directory
    packs_dir = project_root / _PACKS_DIR
    target_dir = packs_dir / name

    if target_dir.exists():
        raise ValueError(
            f"Pack '{name}' is already installed at {target_dir}. "
            f"Remove it first with 'pack remove {name}'."
        )

    # Copy pack contents
    packs_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir)

    # Compute and store manifest checksum
    installed_manifest = target_dir / _MANIFEST_NAME
    checksum = _compute_checksum(installed_manifest)

    # Update platform.json
    config = _read_config(project_root)
    pack_dirs = config.get("pack_dirs", [])
    rel_path = f"{_PACKS_DIR}/{name}"
    if rel_path not in pack_dirs:
        pack_dirs.append(rel_path)
        config["pack_dirs"] = pack_dirs
    checksums = config.get("pack_checksums", {})
    checksums[name] = checksum
    config["pack_checksums"] = checksums
    _write_config(project_root, config)

    # Auto-lock: record content hash in pack-lock.json
    from .pack_integrity import load_lock, save_lock

    lock = load_lock(project_root)
    lock.lock_pack(
        name=name,
        version=manifest.get("version", ""),
        kind=manifest.get("kind", ""),
        base_dir=target_dir,
    )
    save_lock(project_root, lock)

    return PackInfo(
        name=name,
        version=manifest.get("version", ""),
        kind=manifest.get("kind", ""),
        source="installed",
        path=target_dir,
        manifest_path=installed_manifest,
        runtime_compatibility=manifest.get("runtime_compatibility", ""),
        provides=manifest.get("provides"),
        checksum=checksum,
    )


def remove_pack(name: str, project_root: Path) -> bool:
    """Remove an installed pack from .codex/packs/.

    Args:
        name: Pack name to remove.
        project_root: Project root directory.

    Returns:
        True if pack was removed, False if not found.

    Raises:
        ValueError: If trying to remove a non-installed pack.
    """
    target_dir = project_root / _PACKS_DIR / name

    if not target_dir.exists():
        return False

    # Verify it has a manifest (safety check)
    manifest_path = target_dir / _MANIFEST_NAME
    if not manifest_path.exists():
        raise ValueError(
            f"Directory {target_dir} exists but has no {_MANIFEST_NAME}. "
            f"Refusing to remove — manual inspection required."
        )

    # Remove directory
    shutil.rmtree(target_dir)

    # Update platform.json
    config = _read_config(project_root)
    pack_dirs = config.get("pack_dirs", [])
    rel_path = f"{_PACKS_DIR}/{name}"
    if rel_path in pack_dirs:
        pack_dirs.remove(rel_path)
        config["pack_dirs"] = pack_dirs
    checksums = config.get("pack_checksums", {})
    checksums.pop(name, None)
    if checksums:
        config["pack_checksums"] = checksums
    elif "pack_checksums" in config:
        del config["pack_checksums"]
    _write_config(project_root, config)

    # Auto-unlock: remove from pack-lock.json
    from .pack_integrity import load_lock, save_lock

    lock = load_lock(project_root)
    if lock.unlock_pack(name):
        save_lock(project_root, lock)

    return True


def get_pack_info(
    name: str,
    project_root: Path,
    *,
    include_site_packages: bool = True,
) -> PackInfo | None:
    """Get detailed info about a specific pack.

    Args:
        name: Pack name to look up.
        project_root: Project root directory.

    Returns:
        PackInfo if found, None otherwise.
    """
    packs = list_packs(project_root, include_site_packages=include_site_packages)
    for p in packs:
        if p.name == name:
            return p
    return None


def _is_site_packages_path(path: Path) -> bool:
    """Check if a path is inside a site-packages directory."""
    parts = path.parts
    return "site-packages" in parts


def _try_relative(path: Path, base: Path) -> str | None:
    """Try to compute a relative path string, returning None on failure."""
    try:
        rel = path.relative_to(base.resolve())
        return str(rel).replace("\\", "/")
    except ValueError:
        return None
