#!/usr/bin/env python3
"""Scan commit candidates for high-confidence secret patterns.

The scanner intentionally reports only detector names and locations. It never
prints the matched value.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MAX_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class SecretDetector:
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class SecretHit:
    path: str
    line: int
    detector: str
    source: str


DETECTORS: tuple[SecretDetector, ...] = (
    SecretDetector("openai_or_dashscope_sk", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}")),
    SecretDetector("github_pat", re.compile(r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{20,}")),
    SecretDetector("github_token", re.compile(r"(?<![A-Za-z0-9])gh[opsu]_[A-Za-z0-9]{20,}")),
    SecretDetector("aws_access_key", re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}")),
    SecretDetector("google_api_key", re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_-]{20,}")),
    SecretDetector("bearer_token", re.compile(r"(?i)(?<![A-Za-z0-9])Bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
)

GIT_GREP_PATTERN = "|".join(detector.pattern.pattern for detector in DETECTORS)


SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "build",
    "dist",
    "dist-verify",
    "dist-verify-instance",
    "htmlcov",
    "node_modules",
}


def _run_git(root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=str(root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _git_paths(root: Path, args: Sequence[str]) -> list[str]:
    result = _run_git(root, args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return [
        part.decode("utf-8", errors="replace")
        for part in result.stdout.split(b"\0")
        if part
    ]


def _should_skip_path(path: str) -> bool:
    parts = Path(path).parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    if any(part.startswith(".venv") for part in parts):
        return True
    if any(part.startswith("dist-verify") for part in parts):
        return True
    return False


def scan_text(path: str, text: str, *, source: str) -> list[SecretHit]:
    hits: list[SecretHit] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for detector in DETECTORS:
            if detector.pattern.search(line):
                hits.append(
                    SecretHit(
                        path=path,
                        line=line_number,
                        detector=detector.name,
                        source=source,
                    )
                )
    return hits


def _scan_bytes(path: str, data: bytes, *, source: str) -> list[SecretHit]:
    if b"\0" in data:
        return []
    text = data.decode("utf-8", errors="replace")
    return scan_text(path, text, source=source)


def _read_file(path: Path, *, max_bytes: int) -> bytes | None:
    if not path.is_file():
        return None
    if path.stat().st_size > max_bytes:
        return None
    return path.read_bytes()


def scan_worktree(root: Path, *, max_bytes: int) -> list[SecretHit]:
    paths = _git_paths(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    hits: list[SecretHit] = []
    for rel_path in paths:
        if _should_skip_path(rel_path):
            continue
        data = _read_file(root / rel_path, max_bytes=max_bytes)
        if data is None:
            continue
        hits.extend(_scan_bytes(rel_path, data, source="worktree"))
    return hits


def scan_staged(root: Path, *, max_bytes: int) -> list[SecretHit]:
    paths = _git_paths(root, ["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"])
    hits: list[SecretHit] = []
    for rel_path in paths:
        if _should_skip_path(rel_path):
            continue
        result = _run_git(root, ["show", f":{rel_path}"])
        if result.returncode != 0 or len(result.stdout) > max_bytes:
            continue
        hits.extend(_scan_bytes(rel_path, result.stdout, source="staged"))
    return hits


def scan_history(root: Path, *, max_bytes: int) -> list[SecretHit]:
    revs = _run_git(root, ["rev-list", "--all"])
    if revs.returncode != 0:
        raise RuntimeError(revs.stderr.decode("utf-8", errors="replace").strip())
    hits: list[SecretHit] = []
    for rev in revs.stdout.decode("ascii", errors="replace").splitlines():
        result = _run_git(root, ["grep", "-n", "-I", "-P", GIT_GREP_PATTERN, rev, "--"])
        if result.returncode == 1:
            continue
        if result.returncode != 0:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
        for raw_line in result.stdout.decode("utf-8", errors="replace").splitlines():
            parsed = _parse_git_grep_line(raw_line)
            if parsed is None:
                continue
            path, line_number, text = parsed
            if _should_skip_path(path):
                continue
            for detector in DETECTORS:
                if detector.pattern.search(text):
                    hits.append(
                        SecretHit(
                            path=path,
                            line=line_number,
                            detector=detector.name,
                            source=f"history:{rev[:7]}",
                        )
                    )
    return hits


def _parse_git_grep_line(line: str) -> tuple[str, int, str] | None:
    """Parse '<rev>:<path>:<line>:<text>' from git grep output."""
    parts = line.split(":", 3)
    if len(parts) != 4:
        return None
    _rev, path, line_number_text, text = parts
    try:
        line_number = int(line_number_text)
    except ValueError:
        return None
    return path, line_number, text


def format_hits(hits: Iterable[SecretHit]) -> str:
    return "\n".join(
        f"{hit.path}:{hit.line}: {hit.detector} ({hit.source})"
        for hit in hits
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan Git commit candidates for high-confidence secrets.")
    parser.add_argument(
        "--scope",
        choices=("worktree", "staged", "history"),
        default="worktree",
        help="Scan Git commit candidates, staged blobs, or all local refs history.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root. Defaults to this project root.")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Skip files/blobs larger than this.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    try:
        if args.scope == "worktree":
            hits = scan_worktree(root, max_bytes=args.max_bytes)
        elif args.scope == "staged":
            hits = scan_staged(root, max_bytes=args.max_bytes)
        else:
            hits = scan_history(root, max_bytes=args.max_bytes)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if hits:
        print("Secret scan failed. Potential secrets were found:", file=sys.stderr)
        print(format_hits(hits), file=sys.stderr)
        print("Matched values are intentionally not printed.", file=sys.stderr)
        return 1

    print(f"Secret scan passed: no high-confidence matches in {args.scope}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
