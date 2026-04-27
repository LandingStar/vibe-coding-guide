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
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

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
    return m.group(1)


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


def _verify_wheel(wheel_path: Path, label: str, min_files: int, required_entries: list[str]) -> bool:
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

    if ok:
        print(f"  Verification: PASSED")
    else:
        print(f"  Verification: WARNINGS")
    return ok


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
        print(f"  2. Run version consistency check")
        print(f"  3. Build runtime wheel: doc_based_coding_runtime-{version}-py3-none-any.whl")
        print(f"  4. Build instance wheel: doc_loop_vibe_coding-{instance_version}-py3-none-any.whl")
        print(f"  5. Verify wheel contents")
        return 0

    # Step 1: Clean
    if not args.skip_clean:
        print("Step 1: Cleaning old build artifacts...")
        _clean()
    else:
        print("Step 1: Skipping clean (--skip-clean)")

    # Step 2: Version consistency check
    if not args.skip_checks:
        print("\nStep 2: Checking version consistency...")
        if not _check_version_consistency():
            print("\nERROR: Version consistency check failed. Fix before building.", file=sys.stderr)
            return 1
    else:
        print("\nStep 2: Skipping version check (--skip-checks)")

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
    )
    i_ok = _verify_wheel(
        instance_wheel,
        "instance",
        MIN_INSTANCE_FILES,
        ["doc-loop-bootstrap", "doc-loop-validate-doc", "doc-loop-validate-instance"],
    )

    # Summary
    print(f"\n{'='*60}")
    print("Build Summary")
    print(f"{'='*60}")
    print(f"  Runtime wheel:  {runtime_wheel.name} ({'OK' if r_ok else 'WARNINGS'})")
    print(f"  Instance wheel: {instance_wheel.name} ({'OK' if i_ok else 'WARNINGS'})")
    print(f"  Output: {DIST_DIR.relative_to(ROOT)}/")

    if r_ok and i_ok:
        print(f"\nBuild completed successfully.")
        return 0
    else:
        print(f"\nBuild completed with warnings.", file=sys.stderr)
        return 0  # Warnings don't fail the build


if __name__ == "__main__":
    sys.exit(main())
