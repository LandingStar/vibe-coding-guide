#!/usr/bin/env python3
"""Release packaging for doc-based-coding dual-package distribution.

Builds wheels, runs full test suite, and packages a release zip.

Usage:
    python scripts/release.py                   # Full release
    python scripts/release.py --dry-run         # Show release plan
    python scripts/release.py --skip-tests      # Skip pytest (for iteration)
    python scripts/release.py --skip-electron-smoke  # Skip Electron smoke gate
    python scripts/release.py --version 0.9.2   # Override version for zip name
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from release_versioning import require_normal_semver

ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT / "dist"
RELEASE_DIR = ROOT / "release"
EXTENSION_DIR = ROOT / "vscode-extension"
EXTENSION_VENDOR_DIR = EXTENSION_DIR / "vendor"
ELECTRON_SMOKE_VSCODE_VERSION = "1.93.1"
ELECTRON_VSCODE_EXECUTABLE = (
    ROOT
    / "output"
    / "electron"
    / "vscode-executable"
    / ("Code.exe" if sys.platform.startswith("win") else "code")
)
ELECTRON_VSCODE_MANIFEST = ELECTRON_VSCODE_EXECUTABLE.parent / "manifest.json"
ELECTRON_SMOKE_SUMMARY = (
    ROOT
    / "output"
    / "electron"
    / "webview-runner-smoke"
    / "electron-webview-smoke-summary.json"
)

# Files to include in the release zip alongside the wheels
RELEASE_EXTRAS = [
    RELEASE_DIR / "INSTALL_GUIDE.md",
    RELEASE_DIR / "RELEASE_NOTE.md",
    RELEASE_DIR / "README.md",
]


def _read_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        return "unknown"
    return require_normal_semver(m.group(1), "runtime pyproject.toml")


def _read_extension_package_metadata() -> tuple[str, str]:
    package_json = json.loads((EXTENSION_DIR / "package.json").read_text(encoding="utf-8"))
    name = str(package_json.get("name", "doc-based-coding"))
    version = str(package_json.get("version", "unknown"))
    return name, version


def _resolve_npm_executable() -> str | None:
    candidates = ["npm.cmd", "npm"] if sys.platform.startswith("win") else ["npm"]
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _run_build(skip_checks: bool = False, no_isolation: bool = False) -> int:
    """Run the build script."""
    cmd = [sys.executable, str(ROOT / "scripts" / "build.py")]
    if skip_checks:
        cmd.append("--skip-checks")
    if no_isolation:
        cmd.append("--no-isolation")
    result = subprocess.run(cmd)
    return result.returncode


def _run_tests() -> bool:
    """Run the full test suite."""
    print(f"\n{'='*60}")
    print("Running full test suite...")
    print(f"{'='*60}")

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-v", "--tb=short"],
        cwd=str(ROOT),
    )
    return result.returncode == 0


def _display_path(path: Path) -> str:
    """Return a readable path for release diagnostics."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _preflight_electron_smoke_executable(
    *,
    executable_path: Path = ELECTRON_VSCODE_EXECUTABLE,
    manifest_path: Path = ELECTRON_VSCODE_MANIFEST,
    expected_version: str = ELECTRON_SMOKE_VSCODE_VERSION,
) -> tuple[bool, str]:
    """Check that release Electron smoke has an explicitly provisioned VS Code."""
    remediation = (
        "Run: npm run provision:electron:vscode --prefix vscode-extension -- "
        f"provision {expected_version}"
    )

    if not executable_path.exists():
        return (
            False,
            "Pre-provisioned VS Code executable is missing: "
            f"{_display_path(executable_path)}. {remediation}",
        )
    if not manifest_path.exists():
        return (
            False,
            "Pre-provisioned VS Code manifest is missing: "
            f"{_display_path(manifest_path)}. {remediation}",
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"Electron smoke manifest is invalid JSON: {_display_path(manifest_path)} ({exc})"

    version = str(manifest.get("version", ""))
    if version != expected_version:
        return (
            False,
            "Electron smoke manifest version mismatch: "
            f"expected {expected_version}, got {version or '<missing>'}. {remediation}",
        )

    target_executable = manifest.get("target_executable")
    if target_executable:
        try:
            target_path = Path(str(target_executable)).resolve()
            expected_path = executable_path.resolve()
        except OSError as exc:
            return False, f"Electron smoke manifest target_executable is invalid: {exc}"
        if target_path != expected_path:
            return (
                False,
                "Electron smoke manifest target_executable does not match release preflight path: "
                f"{target_path} != {expected_path}",
            )

    return True, (
        "Pre-provisioned VS Code executable ready: "
        f"version={version}, executable={_display_path(executable_path)}"
    )


def _assert_electron_smoke_summary(summary_path: Path = ELECTRON_SMOKE_SUMMARY) -> tuple[bool, str]:
    """Validate the Electron smoke evidence summary expected by release gate."""
    if not summary_path.exists():
        return False, f"Electron smoke summary was not produced: {_display_path(summary_path)}"

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, f"Electron smoke summary is invalid JSON: {_display_path(summary_path)} ({exc})"

    expected = {
        "ok": True,
        "panelVisible": True,
        "hasSchedulerTrajectoryRoot": True,
        "hasSchedulerTrajectoryPayload": True,
        "lanes": 4,
        "events": 6,
        "relations": 12,
    }
    mismatches = [
        f"{key}: expected {expected_value!r}, got {summary.get(key)!r}"
        for key, expected_value in expected.items()
        if summary.get(key) != expected_value
    ]
    if mismatches:
        return False, "Electron smoke summary assertions failed: " + "; ".join(mismatches)

    return True, f"Electron smoke summary assertions passed: {_display_path(summary_path)}"


def _run_electron_smoke_release_gate(dry_run: bool = False) -> bool:
    """Run release-grade Electron smoke through the explicit pre-provisioned gate."""
    print(f"\n{'='*60}")
    print("Running Electron smoke release gate...")
    print(f"{'='*60}")

    ok, message = _preflight_electron_smoke_executable()
    print(f"  {message}")
    if not ok:
        return False

    if dry_run:
        print("  [dry-run] Would run: npm run test:electron:smoke --prefix vscode-extension")
        return True

    npm_executable = _resolve_npm_executable()
    if npm_executable is None:
        print("ERROR: Could not find npm executable required to run Electron smoke.", file=sys.stderr)
        return False

    result = subprocess.run([npm_executable, "run", "test:electron:smoke"], cwd=str(EXTENSION_DIR))
    if result.returncode != 0:
        return False

    ok, message = _assert_electron_smoke_summary()
    print(f"  {message}")
    return ok


def _build_extension_package(dry_run: bool = False) -> Path | None:
    """Build the VS Code extension VSIX package."""
    package_name, version = _read_extension_package_metadata()
    vsix_path = EXTENSION_DIR / f"{package_name}-{version}.vsix"
    npm_executable = _resolve_npm_executable()

    print(f"\n{'='*60}")
    print(f"Packaging VS Code extension: {vsix_path.name}")
    print(f"{'='*60}")

    if dry_run:
        print(f"  [dry-run] Would create: {vsix_path.relative_to(ROOT)}")
        return vsix_path

    if vsix_path.exists():
        vsix_path.unlink()

    if npm_executable is None:
        print("ERROR: Could not find npm executable required to package the VS Code extension.", file=sys.stderr)
        return None

    result = subprocess.run([npm_executable, "run", "package"], cwd=str(EXTENSION_DIR))
    if result.returncode != 0:
        return None

    if not vsix_path.exists():
        print(f"ERROR: Expected VSIX not found: {vsix_path}", file=sys.stderr)
        return None

    return vsix_path


def _extension_vendor_artifacts() -> list[Path]:
    """Return extension-side pinned build inputs that should be auditable in the release zip."""
    if not EXTENSION_VENDOR_DIR.exists():
        return []
    return sorted(EXTENSION_VENDOR_DIR.glob("*.tgz"))


def _package_release(version: str, extension_vsix: Path, dry_run: bool = False) -> Path | None:
    """Package wheels and docs into a release zip."""
    zip_name = f"doc-based-coding-v{version}.zip"
    zip_path = RELEASE_DIR / zip_name

    wheels = sorted(DIST_DIR.glob("*.whl"))
    if not wheels:
        print("ERROR: No wheels found in dist/. Run build first.", file=sys.stderr)
        return None

    extras = [f for f in RELEASE_EXTRAS if f.exists()]
    extension_vendor_artifacts = _extension_vendor_artifacts()

    print(f"\n{'='*60}")
    print(f"Packaging release: {zip_name}")
    print(f"{'='*60}")
    print(f"  Wheels:")
    for w in wheels:
        print(f"    - {w.name}")
    print(f"  Documentation:")
    for e in extras:
        print(f"    - {e.name}")
    print(f"  VS Code Extension:")
    print(f"    - {extension_vsix.name}")
    if extension_vendor_artifacts:
        print(f"  Extension build inputs:")
        for artifact in extension_vendor_artifacts:
            print(f"    - vscode-extension/vendor/{artifact.name}")

    if dry_run:
        print(f"  [dry-run] Would create: {zip_path.relative_to(ROOT)}")
        print(f"  [dry-run] Would sync VSIX to: {(RELEASE_DIR / extension_vsix.name).relative_to(ROOT)}")
        for artifact in extension_vendor_artifacts:
            print(f"  [dry-run] Would include: vscode-extension/vendor/{artifact.name}")
        return zip_path

    # Remove old zip if exists
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for w in wheels:
            zf.write(w, w.name)
        for e in extras:
            zf.write(e, e.name)
        zf.write(extension_vsix, extension_vsix.name)
        for artifact in extension_vendor_artifacts:
            zf.write(artifact, f"vscode-extension/vendor/{artifact.name}")

    size_kb = zip_path.stat().st_size / 1024
    print(f"\n  Created: {zip_path.relative_to(ROOT)} ({size_kb:.1f} KB)")

    # Keep release/ aligned to the current package batch so the consistency
    # checker doesn't see stale wheel versions from older previews.
    for stale in RELEASE_DIR.glob("*.whl"):
        stale.unlink()
        print(f"  Removed stale wheel: {stale.name}")

    # Also copy wheels to release/ for easy access
    for w in wheels:
        dest = RELEASE_DIR / w.name
        if dest.exists():
            dest.unlink()
        shutil.copy2(w, dest)
        print(f"  Copied: {w.name} -> release/")

    for stale in RELEASE_DIR.glob("*.vsix"):
        stale.unlink()
        print(f"  Removed stale VSIX: {stale.name}")

    vsix_dest = RELEASE_DIR / extension_vsix.name
    if vsix_dest.exists():
        vsix_dest.unlink()
    shutil.copy2(extension_vsix, vsix_dest)
    print(f"  Copied: {extension_vsix.name} -> release/")

    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Package doc-based-coding release")
    parser.add_argument("--dry-run", action="store_true", help="Show release plan without executing")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running pytest")
    parser.add_argument(
        "--skip-electron-smoke",
        action="store_true",
        help="Skip release Electron smoke gate; provisioning remains explicit and no download is attempted",
    )
    parser.add_argument("--skip-checks", action="store_true", help="Skip version consistency check")
    parser.add_argument("--no-isolation", action="store_true", help="Build without isolated venv (avoids PyPI downloads)")
    parser.add_argument("--version", type=str, help="Override version for zip name")
    args = parser.parse_args()

    canonical_version = _read_version()
    try:
        version = require_normal_semver(args.version, "--version") if args.version else canonical_version
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if version != canonical_version:
        print(
            "ERROR: --version only selects the release batch name and must match "
            f"the canonical runtime package version {canonical_version}. "
            "Update pyproject.toml and related package metadata before packaging "
            f"{version}.",
            file=sys.stderr,
        )
        return 1

    print(f"doc-based-coding Release Script")
    print(f"{'='*60}")
    print(f"Version: {version}")
    print()

    if args.dry_run:
        print("[DRY RUN MODE]")
        print()
        print("Release plan:")
        print(f"  1. Build dual-package wheels with version and secret hygiene checks")
        print(f"  2. Run full test suite")
        print(f"  3. Build VS Code extension VSIX")
        if args.skip_electron_smoke:
            print(f"  4. Skip Electron smoke release gate (--skip-electron-smoke)")
        else:
            print(
                "  4. Run Electron smoke release gate with pre-provisioned "
                f"VS Code {ELECTRON_SMOKE_VSCODE_VERSION}"
            )
        print(f"  5. Package release zip: doc-based-coding-v{version}.zip")
        print()
        extension_vsix = _build_extension_package(dry_run=True)
        if extension_vsix is None:
            return 1
        if not args.skip_electron_smoke:
            print()
            print("Electron smoke release gate:")
            print(
                "  [dry-run] Would preflight: "
                f"{ELECTRON_VSCODE_EXECUTABLE.relative_to(ROOT)} and "
                f"{ELECTRON_VSCODE_MANIFEST.relative_to(ROOT)}"
            )
            print("  [dry-run] Would run: npm run test:electron:smoke --prefix vscode-extension")
            print(
                "  [dry-run] Missing pre-provisioned executable remediation: "
                "npm run provision:electron:vscode --prefix vscode-extension -- "
                f"provision {ELECTRON_SMOKE_VSCODE_VERSION}"
            )
        _package_release(version, extension_vsix, dry_run=True)
        return 0

    # Step 1: Build
    print("Step 1: Building wheels...")
    rc = _run_build(skip_checks=args.skip_checks, no_isolation=args.no_isolation)
    if rc != 0:
        print("\nERROR: Build failed.", file=sys.stderr)
        return 1

    # Step 2: Run tests
    if not args.skip_tests:
        print("\nStep 2: Running tests...")
        if not _run_tests():
            print("\nERROR: Tests failed. Fix before releasing.", file=sys.stderr)
            return 1
        print("\n  Tests: PASSED")
    else:
        print("\nStep 2: Skipping tests (--skip-tests)")

    # Step 3: Build VS Code extension
    print("\nStep 3: Building VS Code extension package...")
    extension_vsix = _build_extension_package()
    if extension_vsix is None:
        print("\nERROR: VS Code extension packaging failed.", file=sys.stderr)
        return 1
    print(f"\n  VSIX: {extension_vsix.relative_to(ROOT)}")

    # Step 4: Electron smoke release gate
    if args.skip_electron_smoke:
        print("\nStep 4: Skipping Electron smoke release gate (--skip-electron-smoke)")
    else:
        print("\nStep 4: Running Electron smoke release gate...")
        if not _run_electron_smoke_release_gate():
            print("\nERROR: Electron smoke release gate failed.", file=sys.stderr)
            return 1
        print("\n  Electron smoke: PASSED")

    # Step 5: Package
    print("\nStep 5: Packaging release...")
    zip_path = _package_release(version, extension_vsix)
    if zip_path is None:
        return 1

    # Summary
    print(f"\n{'='*60}")
    print("Release Summary")
    print(f"{'='*60}")
    print(f"  Version: {version}")
    print(f"  Zip:     {zip_path.relative_to(ROOT)}")
    print(f"  Wheels:  dist/")
    print(f"  VSIX:    {extension_vsix.relative_to(ROOT)}")
    print(f"  Electron smoke: {'SKIPPED' if args.skip_electron_smoke else 'PASSED'}")
    print(f"\n  Next steps:")
    print(f"    1. Verify installation in a clean venv")
    print(f"    2. Verify extension install from VSIX")
    print(f"    3. Test CLI entry points")
    print(f"    4. Tag the release if distributing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
