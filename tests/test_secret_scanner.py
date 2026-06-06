from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts import scan_secrets


ROOT = Path(__file__).resolve().parent.parent


def test_scan_text_detects_sk_secret_without_printing_value() -> None:
    secret = "sk-" + "A" * 32
    hits = scan_secrets.scan_text("example.txt", f"token={secret}", source="unit")

    assert len(hits) == 1
    assert hits[0].detector == "openai_or_dashscope_sk"
    assert secret not in scan_secrets.format_hits(hits)


def test_scan_text_ignores_sk_inside_words() -> None:
    hits = scan_secrets.scan_text("example.txt", "workspace-parallel-task-orchestration", source="unit")

    assert hits == []


def test_worktree_scan_reports_secret_location_without_value(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE)
    (repo / "leak.txt").write_text("key=sk-" + "B" * 32 + "\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scan_secrets.py"),
            "--root",
            str(repo),
            "--scope",
            "worktree",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "leak.txt:1: openai_or_dashscope_sk (worktree)" in result.stderr
    assert "sk-" + "B" * 32 not in result.stderr


def test_staged_scan_reads_index_blob(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE)
    (repo / "leak.txt").write_text("key=sk-" + "C" * 32 + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "leak.txt"], cwd=repo, check=True)
    (repo / "leak.txt").write_text("key=sk-REDACTED\n", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scan_secrets.py"),
            "--root",
            str(repo),
            "--scope",
            "staged",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "leak.txt:1: openai_or_dashscope_sk (staged)" in result.stderr
    assert "sk-" + "C" * 32 not in result.stderr


def test_history_scan_reports_committed_secret_without_value(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.PIPE)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
    (repo / "leak.txt").write_text("key=sk-" + "D" * 32 + "\n", encoding="utf-8")
    subprocess.run(["git", "add", "leak.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "add leak"], cwd=repo, check=True, stdout=subprocess.PIPE)

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scan_secrets.py"),
            "--root",
            str(repo),
            "--scope",
            "history",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "leak.txt:1: openai_or_dashscope_sk (history:" in result.stderr
    assert "sk-" + "D" * 32 not in result.stderr
