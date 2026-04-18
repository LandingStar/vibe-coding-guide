#!/usr/bin/env python3
"""Pre-release version consistency checker.

Validates that the version string is consistent across:
- pyproject.toml (runtime)
- doc-loop-vibe-coding/pyproject.toml (instance pack)
- pack-manifest.json (instance pack)
- release/INSTALL_GUIDE.md
- release/RELEASE_NOTE.md
- release/README.md
- wheel filenames in release/

Usage:
    python release/verify_version_consistency.py [--fix]

Exit codes:
    0  All versions consistent
    1  Inconsistencies found (printed to stderr)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _read_toml_version(path: Path) -> str | None:
    """Extract version from a pyproject.toml without requiring tomllib."""
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^version\s*=\s*"([^"]+)"', line)
        if m:
            return m.group(1)
    return None


def _read_manifest_version(path: Path) -> str | None:
    """Extract version from pack-manifest.json."""
    import json

    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("version")
    except Exception:
        return None


def _find_version_refs_in_md(path: Path, pattern: re.Pattern[str]) -> list[str]:
    """Find all version-like strings matching pattern in a markdown file."""
    if not path.exists():
        return []
    return pattern.findall(path.read_text(encoding="utf-8"))


def _find_wheel_versions(release_dir: Path) -> dict[str, str]:
    """Extract versions from wheel filenames in release/."""
    results: dict[str, str] = {}
    for f in release_dir.iterdir():
        if f.suffix == ".whl":
            # e.g. doc_based_coding_runtime-0.9.1-py3-none-any.whl
            m = re.match(r"^(.+?)-(\d+\.\d+\.\d+[^-]*)-", f.name)
            if m:
                results[m.group(1)] = m.group(2)
    return results


def main() -> int:
    errors: list[str] = []

    # 1. Canonical version from runtime pyproject.toml
    runtime_toml = ROOT / "pyproject.toml"
    canonical = _read_toml_version(runtime_toml)
    if not canonical:
        errors.append(f"Cannot read version from {runtime_toml}")
        _report(errors)
        return 1

    print(f"Canonical version: {canonical}")

    # 2. Instance pack pyproject.toml
    instance_toml = ROOT / "doc-loop-vibe-coding" / "pyproject.toml"
    instance_ver = _read_toml_version(instance_toml)
    if instance_ver and instance_ver != canonical:
        errors.append(
            f"Instance pyproject.toml version={instance_ver}, expected {canonical}"
        )

    # 3. Instance pack-manifest.json
    manifest = ROOT / "doc-loop-vibe-coding" / "pack-manifest.json"
    manifest_ver = _read_manifest_version(manifest)
    if manifest_ver and manifest_ver != canonical:
        errors.append(
            f"pack-manifest.json version={manifest_ver}, expected {canonical}"
        )

    # 4. Wheel filenames in release/
    release_dir = ROOT / "release"
    wheel_versions = _find_wheel_versions(release_dir)
    for pkg, ver in wheel_versions.items():
        if ver != canonical:
            errors.append(f"Wheel {pkg} has version {ver}, expected {canonical}")

    # 5. Markdown files: check for stale version references
    #    Pattern matches common version formats like 0.9.1, 1.0.0
    #    in wheel names, zip names, and version headers
    version_in_filename = re.compile(
        r"(?:doc_based_coding_runtime|doc_loop_vibe_coding|doc-based-coding)[_-v]?"
        r"(\d+\.\d+\.\d+[a-z0-9]*)"
    )
    version_in_header = re.compile(
        r"doc-based-coding(?:-platform)?\s+v?(\d+\.\d+\.\d+[a-z0-9]*)"
    )

    md_files = [
        release_dir / "INSTALL_GUIDE.md",
        release_dir / "RELEASE_NOTE.md",
        release_dir / "README.md",
    ]

    for md_path in md_files:
        if not md_path.exists():
            continue
        content = md_path.read_text(encoding="utf-8")
        for pattern in (version_in_filename, version_in_header):
            for match in pattern.finditer(content):
                found_ver = match.group(1)
                if found_ver != canonical:
                    errors.append(
                        f"{md_path.name}: found version {found_ver} "
                        f"(in '{match.group(0)}'), expected {canonical}"
                    )

    # 6. RELEASE_NOTE.md title line
    release_note = release_dir / "RELEASE_NOTE.md"
    if release_note.exists():
        first_line = release_note.read_text(encoding="utf-8").split("\n", 1)[0]
        m = re.search(r"v?(\d+\.\d+\.\d+[a-z0-9]*)", first_line)
        if m and m.group(1) != canonical:
            errors.append(
                f"RELEASE_NOTE.md title version={m.group(1)}, expected {canonical}"
            )

    _report(errors)
    return 1 if errors else 0


def _report(errors: list[str]) -> None:
    if errors:
        print(f"\n{len(errors)} version inconsistencies found:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
    else:
        print("All versions consistent.")


if __name__ == "__main__":
    sys.exit(main())
