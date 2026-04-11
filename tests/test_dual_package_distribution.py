from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path


from src.pack import manifest_loader


ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT / "doc-loop-vibe-coding"


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _load_instance_package_module():
    init_path = INSTANCE_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "doc_loop_vibe_coding",
        init_path,
        submodule_search_locations=[str(INSTANCE_DIR)],
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_pyproject_declares_console_scripts() -> None:
    pyproject = _load_toml(ROOT / "pyproject.toml")

    assert pyproject["project"]["name"] == "doc-based-coding-runtime"
    assert pyproject["project"]["version"] == "1.0.0"
    assert pyproject["project"]["scripts"] == {
        "doc-based-coding": "src.__main__:main",
        "doc-based-coding-mcp": "src.mcp.server:main",
    }

    dependencies = set(pyproject["project"]["dependencies"])
    assert "jsonschema>=4.0.0" in dependencies
    assert "mcp>=1.0.0" in dependencies


def test_instance_pyproject_declares_entry_points_and_dependency() -> None:
    pyproject = _load_toml(INSTANCE_DIR / "pyproject.toml")

    assert pyproject["project"]["name"] == "doc-loop-vibe-coding"
    assert pyproject["project"]["dependencies"] == [
        "doc-based-coding-runtime>=1.0.0,<2.0.0",
    ]
    assert pyproject["project"]["scripts"] == {
        "doc-loop-bootstrap": "doc_loop_vibe_coding.scripts.bootstrap_doc_loop:main",
        "doc-loop-validate-doc": "doc_loop_vibe_coding.scripts.validate_doc_loop:main",
        "doc-loop-validate-instance": "doc_loop_vibe_coding.scripts.validate_instance_pack:main",
    }

    package_data = set(pyproject["tool"]["setuptools"]["package-data"]["doc_loop_vibe_coding"])
    assert "pack-manifest.json" in package_data
    assert "assets/bootstrap/.codex/**/*" in package_data


def test_runtime_compatibility_matches_python_package_dependency() -> None:
    pyproject = _load_toml(INSTANCE_DIR / "pyproject.toml")
    manifest = manifest_loader.load(INSTANCE_DIR / "pack-manifest.json")

    assert manifest.runtime_compatibility == ">=1.0.0,<2.0.0"
    assert pyproject["project"]["dependencies"] == [
        f"doc-based-coding-runtime{manifest.runtime_compatibility}",
    ]


def test_instance_package_helpers_point_to_manifest() -> None:
    module = _load_instance_package_module()

    assert module.get_package_root() == INSTANCE_DIR
    assert module.get_manifest_path() == INSTANCE_DIR / "pack-manifest.json"


def test_validate_instance_pack_defaults_to_pack_root() -> None:
    result = subprocess.run(
        [sys.executable, str(INSTANCE_DIR / "scripts" / "validate_instance_pack.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 0, result.stdout + result.stderr