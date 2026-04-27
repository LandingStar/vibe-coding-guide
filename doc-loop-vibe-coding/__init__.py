"""Official doc-loop instance package metadata and resource helpers."""

from __future__ import annotations

from pathlib import Path

__all__ = ["__version__", "get_manifest_path", "get_package_root"]

__version__ = "0.9.5"


def get_package_root() -> Path:
    """Return the installed root directory for the official instance package."""
    return Path(__file__).resolve().parent


def get_manifest_path() -> Path:
    """Return the installed pack-manifest.json path."""
    return get_package_root() / "pack-manifest.json"