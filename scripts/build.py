#!/usr/bin/env python3
"""Build automation for doc-based-coding dual-package distribution.

Builds both the runtime wheel and the official instance pack wheel,
with pre-build version consistency checks and post-build content
verification.

Usage:
    python scripts/build.py          # Full build
    python scripts/build.py --dry-run  # Show build plan without building
    python scripts/build.py --skip-checks  # Skip version consistency check
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from release_versioning import require_normal_semver

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = ROOT
INSTANCE_DIR = ROOT / "doc-loop-vibe-coding"
DIST_DIR = ROOT / "dist"

# Minimum expected file counts in each wheel
MIN_RUNTIME_PY_FILES = 50
MIN_INSTANCE_FILES = 30


def _read_version(pyproject: Path) -> str:
    """Extract version from pyproject.toml."""
    import re

    text = pyproject.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        print(f"ERROR: Cannot read version from {pyproject}", file=sys.stderr)
        sys.exit(1)
    try:
        return require_normal_semver(m.group(1), str(pyproject.relative_to(ROOT)))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def _clean(dry_run: bool = False) -> None:
    """Remove old build artifacts."""
    dirs_to_clean = [
        ROOT / "build",
        ROOT / "dist",
        ROOT / "dist-verify",
        ROOT / "dist-verify-instance",
        ROOT / "doc_based_coding_runtime.egg-info",
        INSTANCE_DIR / "build",
        INSTANCE_DIR / "doc_loop_vibe_coding.egg-info",
    ]
    for d in dirs_to_clean:
        if d.exists():
            if dry_run:
                print(f"  [dry-run] Would remove: {d.relative_to(ROOT)}")
            else:
                shutil.rmtree(d)
                print(f"  Removed: {d.relative_to(ROOT)}")


def _check_version_consistency() -> bool:
    """Run the version consistency checker."""
    script = ROOT / "release" / "verify_version_consistency.py"
    if not script.exists():
        print("WARNING: verify_version_consistency.py not found, skipping", file=sys.stderr)
        return True
    result = subprocess.run(
        [sys.executable, str(script), "--skip-wheel-files"],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        return False
    return True


def _check_secret_hygiene() -> bool:
    """Run the repository secret hygiene scanner."""
    script = ROOT / "scripts" / "scan_secrets.py"
    result = subprocess.run(
        [sys.executable, str(script), "--scope", "worktree"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, end="", file=sys.stderr)
        return False
    return True


def _build_wheel(project_dir: Path, output_dir: Path, label: str, *, no_isolation: bool = False) -> Path | None:
    """Build a wheel for the given project directory."""
    print(f"\n{'='*60}")
    print(f"Building {label}...")
    print(f"{'='*60}")

    cmd = [sys.executable, "-m", "build", "--wheel", "--outdir", str(output_dir)]
    if no_isolation:
        cmd.append("--no-isolation")
    cmd.append(str(project_dir))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR: Build failed for {label}", file=sys.stderr)
        print(result.stdout, end="")
        print(result.stderr, end="", file=sys.stderr)
        return None

    # Find the built wheel
    wheels = list(output_dir.glob("*.whl"))
    if not wheels:
        print(f"ERROR: No wheel found in {output_dir}", file=sys.stderr)
        return None

    # Return the newest wheel
    wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    print(f"  Built: {wheel.name} ({wheel.stat().st_size / 1024:.1f} KB)")
    return wheel


def _verify_wheel(
    wheel_path: Path,
    label: str,
    min_files: int,
    required_entries: list[str],
    required_members: list[str] | None = None,
) -> bool:
    """Verify wheel content integrity."""
    print(f"\nVerifying {label} wheel content...")
    ok = True

    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
        py_files = [n for n in names if n.endswith(".py")]
        all_files = [n for n in names if not n.endswith("/")]

        print(f"  Total files: {len(all_files)}")
        print(f"  Python files: {len(py_files)}")

        if len(all_files) < min_files:
            print(
                f"  WARNING: Expected at least {min_files} files, got {len(all_files)}",
                file=sys.stderr,
            )
            ok = False

        # Check for required entry point markers in RECORD or metadata
        metadata_files = [n for n in names if "METADATA" in n or "entry_points" in n]
        metadata_content = ""
        for mf in metadata_files:
            metadata_content += zf.read(mf).decode("utf-8", errors="replace")

        for entry in required_entries:
            if entry in metadata_content:
                print(f"  Entry point '{entry}': found")
            else:
                # Check in console_scripts section
                ep_files = [n for n in names if "entry_points.txt" in n]
                found = False
                for ef in ep_files:
                    if entry in zf.read(ef).decode("utf-8", errors="replace"):
                        found = True
                        break
                if found:
                    print(f"  Entry point '{entry}': found")
                else:
                    print(f"  WARNING: Entry point '{entry}' not found in wheel metadata", file=sys.stderr)
                    ok = False

        for member in required_members or []:
            if member in names:
                print(f"  Required member '{member}': found")
            else:
                print(f"  WARNING: Required member '{member}' not found in wheel", file=sys.stderr)
                ok = False

    if ok:
        print(f"  Verification: PASSED")
    else:
        print(f"  Verification: WARNINGS")
    return ok


def _run_installed_worker_report_smoke(
    runtime_wheel: Path,
    instance_wheel: Path,
) -> bool:
    """Prove worker-report consumption from isolated installed wheel contents."""

    print("\nRunning installed-layout worker-report smoke...")
    with tempfile.TemporaryDirectory(prefix="dbc-installed-worker-report-") as temp_dir:
        smoke_root = Path(temp_dir)
        install_root = smoke_root / "installed"
        workspace_root = smoke_root / "workspace"
        install_root.mkdir()
        workspace_root.mkdir()

        install = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--quiet",
                "--no-deps",
                "--target",
                str(install_root),
                str(runtime_wheel),
                str(instance_wheel),
            ],
            cwd=str(smoke_root),
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            print("  ERROR: isolated wheel installation failed", file=sys.stderr)
            print(install.stdout, end="")
            print(install.stderr, end="", file=sys.stderr)
            return False

        env = os.environ.copy()
        env["PYTHONPATH"] = str(install_root)
        import_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, pathlib, src, doc_loop_vibe_coding; "
                    "root=pathlib.Path(r'" + str(install_root) + "').resolve(); "
                    "paths=[pathlib.Path(src.__file__).resolve(), "
                    "pathlib.Path(doc_loop_vibe_coding.__file__).resolve()]; "
                    "assert all(path.is_relative_to(root) for path in paths), paths; "
                    "print(json.dumps([str(path) for path in paths]))"
                ),
            ],
            cwd=str(smoke_root),
            env=env,
            capture_output=True,
            text=True,
        )
        if import_probe.returncode != 0:
            print("  ERROR: wheel import isolation probe failed", file=sys.stderr)
            print(import_probe.stdout, end="")
            print(import_probe.stderr, end="", file=sys.stderr)
            return False

        bootstrap = subprocess.run(
            [
                sys.executable,
                "-m",
                "doc_loop_vibe_coding.scripts.bootstrap_doc_loop",
                "--target",
                str(workspace_root),
                "--project-name",
                "installed-worker-report-smoke",
                "--force",
            ],
            cwd=str(smoke_root),
            env=env,
            capture_output=True,
            text=True,
        )
        if bootstrap.returncode != 0:
            print("  ERROR: installed instance bootstrap failed", file=sys.stderr)
            print(bootstrap.stdout, end="")
            print(bootstrap.stderr, end="", file=sys.stderr)
            return False

        report_path = workspace_root / ".dbc" / "agent-output" / "report-smoke.json"
        report_path.parent.mkdir(parents=True)
        report_path.write_text(
            json.dumps(
                {
                    "report_id": "report-installed-wheel-smoke",
                    "contract_id": "contract-installed-wheel-smoke",
                    "status": "completed",
                    "changed_artifacts": ["smoke.txt"],
                    "verification_results": ["installed-layout smoke"],
                    "trajectory_update": {
                        "lane_id": "lane:installed-smoke",
                        "task_id": "task/installed-smoke",
                        "event_status": "completed",
                        "summary": "Installed wheel consumed the workspace report contract.",
                        "suggested_action": "append",
                    },
                }
            ),
            encoding="utf-8",
        )
        consume = subprocess.run(
            [
                sys.executable,
                "-m",
                "src",
                "scheduler",
                "consume-worker-trajectory-report",
                "--report-path",
                ".dbc/agent-output/report-smoke.json",
                "--caller-role",
                "leader",
            ],
            cwd=str(workspace_root),
            env=env,
            capture_output=True,
            text=True,
        )
        if consume.returncode != 0:
            print("  ERROR: installed runtime could not consume worker report", file=sys.stderr)
            print(consume.stdout, end="")
            print(consume.stderr, end="", file=sys.stderr)
            return False

        try:
            payload = json.loads(consume.stdout)
        except json.JSONDecodeError as exc:
            print(f"  ERROR: installed runtime returned invalid JSON: {exc}", file=sys.stderr)
            print(consume.stdout, end="")
            return False
        trajectory_path = workspace_root / ".dbc" / "progress-graph" / "local-work-trajectory.json"
        if payload.get("status") != "consumed" or not trajectory_path.is_file():
            print(
                "  ERROR: installed runtime did not produce the expected consumed trajectory state",
                file=sys.stderr,
            )
            print(consume.stdout, end="")
            return False

        print(f"  Imported from isolated target: {import_probe.stdout.strip()}")
        print("  Bootstrap contract and CLI consumption: PASSED")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Build doc-based-coding dual-package wheels")
    parser.add_argument("--dry-run", action="store_true", help="Show build plan without building")
    parser.add_argument("--skip-checks", action="store_true", help="Skip version consistency check")
    parser.add_argument("--skip-clean", action="store_true", help="Skip cleaning old artifacts")
    parser.add_argument("--no-isolation", action="store_true", help="Build without isolated venv (avoids PyPI downloads)")
    args = parser.parse_args()

    version = _read_version(ROOT / "pyproject.toml")
    instance_version = _read_version(INSTANCE_DIR / "pyproject.toml")

    print(f"doc-based-coding Build Script")
    print(f"{'='*60}")
    print(f"Runtime version:  {version}")
    print(f"Instance version: {instance_version}")
    print(f"Output directory: {DIST_DIR.relative_to(ROOT)}")
    print()

    if args.dry_run:
        print("[DRY RUN MODE]")
        print()
        print("Build plan:")
        print(f"  1. Clean old artifacts")
        _clean(dry_run=True)
        print(f"  2. Run version consistency and secret hygiene checks")
        print(f"  3. Build runtime wheel: doc_based_coding_runtime-{version}-py3-none-any.whl")
        print(f"  4. Build instance wheel: doc_loop_vibe_coding-{instance_version}-py3-none-any.whl")
        print(f"  5. Verify wheel contents")
        print(f"  6. Run installed-layout worker-report smoke")
        return 0

    # Step 1: Clean
    if not args.skip_clean:
        print("Step 1: Cleaning old build artifacts...")
        _clean()
    else:
        print("Step 1: Skipping clean (--skip-clean)")

    # Step 2: Version consistency check
    if not args.skip_checks:
        print("\nStep 2: Running pre-build checks...")
        print("  Checking version consistency...")
        if not _check_version_consistency():
            print("\nERROR: Version consistency check failed. Fix before building.", file=sys.stderr)
            return 1
        print("  Checking secret hygiene...")
        if not _check_secret_hygiene():
            print("\nERROR: Secret hygiene check failed. Remove or redact secrets before building.", file=sys.stderr)
            return 1
    else:
        print("\nStep 2: Skipping pre-build checks (--skip-checks)")

    # Ensure dist directory exists
    DIST_DIR.mkdir(exist_ok=True)

    # Step 3: Build runtime wheel
    runtime_wheel = _build_wheel(RUNTIME_DIR, DIST_DIR, "doc-based-coding-runtime", no_isolation=args.no_isolation)
    if runtime_wheel is None:
        return 1

    # Step 4: Build instance wheel
    instance_wheel = _build_wheel(INSTANCE_DIR, DIST_DIR, "doc-loop-vibe-coding", no_isolation=args.no_isolation)
    if instance_wheel is None:
        return 1

    # Step 5: Verify wheels
    print(f"\n{'='*60}")
    print("Step 5: Verifying wheel contents...")
    print(f"{'='*60}")

    r_ok = _verify_wheel(
        runtime_wheel,
        "runtime",
        MIN_RUNTIME_PY_FILES,
        ["doc-based-coding", "doc-based-coding-mcp"],
        [
            "tools/__init__.py",
            "tools/progress_graph/__init__.py",
            "tools/progress_graph/doc_projection.py",
            "tools/progress_graph/trajectory.py",
            "tools/dependency_graph/baseline_graph.json",
            "tools/dependency_graph/coupling_annotations.json",
            "tools/dependency_graph/query.py",
            "tools/dependency_graph/reference_adapter.py",
        ],
    )
    i_ok = _verify_wheel(
        instance_wheel,
        "instance",
        MIN_INSTANCE_FILES,
        ["doc-loop-bootstrap", "doc-loop-validate-doc", "doc-loop-validate-instance"],
        [
            "doc_loop_vibe_coding/assets/bootstrap/docs/worker-trajectory-update-reporting.md",
            "doc_loop_vibe_coding/assets/bootstrap/docs/specs/subagent-report.schema.json",
        ],
    )
    installed_smoke_ok = False
    if r_ok and i_ok:
        installed_smoke_ok = _run_installed_worker_report_smoke(
            runtime_wheel,
            instance_wheel,
        )

    # Summary
    print(f"\n{'='*60}")
    print("Build Summary")
    print(f"{'='*60}")
    print(f"  Runtime wheel:  {runtime_wheel.name} ({'OK' if r_ok else 'WARNINGS'})")
    print(f"  Instance wheel: {instance_wheel.name} ({'OK' if i_ok else 'WARNINGS'})")
    print(f"  Installed smoke: {'OK' if installed_smoke_ok else 'FAILED'}")
    print(f"  Output: {DIST_DIR.relative_to(ROOT)}/")

    if r_ok and i_ok and installed_smoke_ok:
        print(f"\nBuild completed successfully.")
        return 0

    print(f"\nBuild failed verification.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
