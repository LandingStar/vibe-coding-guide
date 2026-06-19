from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from release import _assert_electron_smoke_summary, _preflight_electron_smoke_executable  # noqa: E402
from scripts.release_versioning import is_normal_semver, is_semver, require_normal_semver


ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "version",
    [
        "0.9.6",
        "1.0.0",
        "2.10.3",
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0+build.7",
        "1.0.0-rc.1+build.7",
    ],
)
def test_is_semver_accepts_semver_2_versions(version: str) -> None:
    assert is_semver(version)


@pytest.mark.parametrize(
    "version",
    [
        "v1.0.0",
        "1.0",
        "1",
        "01.0.0",
        "1.02.0",
        "1.0.03",
        "1.0.0-01",
        "1.0.0+",
    ],
)
def test_is_semver_rejects_invalid_versions(version: str) -> None:
    assert not is_semver(version)


def test_packageable_release_versions_are_normal_semver_only() -> None:
    assert is_normal_semver("0.9.6")
    assert require_normal_semver("0.9.6", "test") == "0.9.6"

    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        require_normal_semver("1.0.0-rc.1", "test")


def test_release_dry_run_rejects_non_semver_override() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release.py"), "--dry-run", "--version", "v1.0.0"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 1
    assert "must be SemVer 2.0.0 without a leading 'v'" in result.stderr


def test_release_dry_run_rejects_version_that_does_not_match_package_metadata() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release.py"), "--dry-run", "--version", "9.9.9"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 1
    assert "must match the canonical runtime package version" in result.stderr


def test_release_dry_run_accepts_canonical_package_version() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release.py"), "--dry-run", "--version", version],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"doc-based-coding-v{version}.zip" in result.stdout


def test_release_dry_run_advertises_preprovisioned_electron_smoke_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release.py"), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Run Electron smoke release gate with pre-provisioned VS Code 1.93.1" in result.stdout
    assert "Would preflight: output" in result.stdout
    assert "npm run test:electron:smoke --prefix vscode-extension" in result.stdout
    assert "npm run provision:electron:vscode --prefix vscode-extension -- provision 1.93.1" in result.stdout


def test_release_dry_run_can_explicitly_skip_electron_smoke_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release.py"), "--dry-run", "--skip-electron-smoke"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Skip Electron smoke release gate (--skip-electron-smoke)" in result.stdout
    assert "npm run test:electron:smoke --prefix vscode-extension" not in result.stdout


def test_release_electron_smoke_preflight_reports_missing_executable(tmp_path: Path) -> None:
    executable = tmp_path / "vscode-executable" / "Code.exe"
    manifest = executable.parent / "manifest.json"

    ok, message = _preflight_electron_smoke_executable(
        executable_path=executable,
        manifest_path=manifest,
        expected_version="1.93.1",
    )

    assert ok is False
    assert "Pre-provisioned VS Code executable is missing" in message
    assert "provision 1.93.1" in message


def test_release_electron_smoke_preflight_accepts_valid_manifest(tmp_path: Path) -> None:
    executable = tmp_path / "vscode-executable" / "Code.exe"
    manifest = executable.parent / "manifest.json"
    executable.parent.mkdir(parents=True)
    executable.write_text("fake executable", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "product": "Visual Studio Code",
                "executable": "Code.exe",
                "version": "1.93.1",
                "target_executable": str(executable.resolve()),
                "sha256": "fake",
            }
        ),
        encoding="utf-8",
    )

    ok, message = _preflight_electron_smoke_executable(
        executable_path=executable,
        manifest_path=manifest,
        expected_version="1.93.1",
    )

    assert ok is True
    assert "version=1.93.1" in message


def test_release_electron_smoke_preflight_rejects_wrong_version(tmp_path: Path) -> None:
    executable = tmp_path / "vscode-executable" / "Code.exe"
    manifest = executable.parent / "manifest.json"
    executable.parent.mkdir(parents=True)
    executable.write_text("fake executable", encoding="utf-8")
    manifest.write_text(json.dumps({"version": "1.92.0"}), encoding="utf-8")

    ok, message = _preflight_electron_smoke_executable(
        executable_path=executable,
        manifest_path=manifest,
        expected_version="1.93.1",
    )

    assert ok is False
    assert "manifest version mismatch" in message
    assert "provision 1.93.1" in message


def test_release_electron_smoke_summary_assertions(tmp_path: Path) -> None:
    summary = tmp_path / "electron-webview-smoke-summary.json"
    summary.write_text(
        json.dumps(
            {
                "ok": True,
                "panelVisible": True,
                "hasSchedulerTrajectoryRoot": True,
                "hasSchedulerTrajectoryPayload": True,
                "lanes": 4,
                "events": 6,
                "relations": 12,
            }
        ),
        encoding="utf-8",
    )

    ok, message = _assert_electron_smoke_summary(summary)

    assert ok is True
    assert "assertions passed" in message


def test_release_script_does_not_call_electron_provisioning_or_download() -> None:
    source = (ROOT / "scripts" / "release.py").read_text(encoding="utf-8")

    assert "provision-electron-vscode.mjs" not in source
    assert "downloadAndUnzipVSCode" not in source
    assert "test:electron:smoke" in source
