from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
REBUILD_SCRIPT_PATH = (
    REPO_ROOT
    / ".codex/handoff-system/skill/project-handoff-rebuild/scripts/rebuild_handoff.py"
)
ACCEPT_SCRIPT_PATH = (
    REPO_ROOT
    / ".codex/handoff-system/skill/project-handoff-accept/scripts/intake_handoff.py"
)
FIXTURE_DIR = REPO_ROOT / ".codex/handoff-system/tests/fixtures"


def load_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    assert match is not None
    frontmatter_text = match.group(1)
    result: dict[str, object] = {}
    current_list_key: str | None = None
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_list_key is not None:
            result.setdefault(current_list_key, [])
            existing = result[current_list_key]
            assert isinstance(existing, list)
            existing.append(line[4:])
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            result[key] = []
            current_list_key = key
        elif value == "[]":
            result[key] = []
        elif value == "null":
            result[key] = None
        else:
            result[key] = value
    return result


def setup_repo_root(tmp_path: Path, fixture_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    frontmatter = load_frontmatter(fixture_path)
    for ref in frontmatter["authoritative_refs"]:
        ref_path = repo_root / ref
        ref_path.parent.mkdir(parents=True, exist_ok=True)
        if "does-not-exist" not in ref:
            ref_path.write_text(f"fixture:{ref}\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    return repo_root


def install_canonical_handoff(repo_root: Path, fixture_path: Path) -> Path:
    handoff_path = repo_root / ".codex/handoffs/history" / fixture_path.name
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
    return handoff_path


def install_current_mirror(repo_root: Path, handoff_path: Path) -> None:
    frontmatter = load_frontmatter(handoff_path)
    current_path = repo_root / ".codex/handoffs/CURRENT.md"
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        "\n".join(
            [
                "---",
                f"handoff_id: {frontmatter['handoff_id']}",
                "entry_role: current-mirror",
                f"source_handoff_id: {frontmatter['handoff_id']}",
                f"source_path: {handoff_path.relative_to(repo_root)}",
                "source_hash: sha256:test",
                f"kind: {frontmatter['kind']}",
                "status: active",
                f"scope_key: {frontmatter['scope_key']}",
                f"safe_stop_kind: {frontmatter['safe_stop_kind']}",
                f"created_at: {frontmatter['created_at']}",
                "authoritative_refs:",
                "  - design_docs/Project Master Checklist.md",
                "  - design_docs/Global Phase Map and Current Position.md",
                "conditional_blocks: []",
                "other_count: 0",
                "---",
                "",
                "# Current Handoff Mirror",
                "",
                "当前入口镜像当前 active canonical handoff。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def install_current_bootstrap_placeholder(repo_root: Path) -> None:
    current_path = repo_root / ".codex/handoffs/CURRENT.md"
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        "\n".join(
            [
                "---",
                "entry_role: current-bootstrap",
                "status: bootstrap-placeholder",
                "created_at: 2026-04-08T00:00:00+08:00",
                "---",
                "",
                "# Current Handoff Placeholder",
                "",
                "当前尚未生成 active canonical handoff。",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run_rebuild(
    *,
    repo_root: Path,
    path: Path | None = None,
    use_current: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(REBUILD_SCRIPT_PATH)]
    if use_current:
        command.append("--current")
    elif path is not None:
        command.extend(["--handoff", str(path)])
    command.append("--json")
    return subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def run_accept(path: Path, *, repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ACCEPT_SCRIPT_PATH), "--handoff", str(path), "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_rebuild_creates_report_and_replacement_draft_from_blocked_handoff(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "invalid-missing-ref-stage-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    source_path = install_canonical_handoff(repo_root, fixture)

    result = run_rebuild(repo_root=repo_root, path=source_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["failure_class"] == "reality-mismatch"

    report_path = Path(payload["report_path"])
    rebuilt_path = Path(payload["rebuilt_handoff_path"])
    assert report_path.exists()
    assert rebuilt_path.exists()

    rebuilt_frontmatter = load_frontmatter(rebuilt_path)
    assert rebuilt_frontmatter["status"] == "draft"
    assert "design_docs/does-not-exist.md" not in rebuilt_frontmatter["authoritative_refs"]

    accept_result = run_accept(rebuilt_path, repo_root=repo_root)
    assert accept_result.returncode == 0
    accept_payload = json.loads(accept_result.stdout)
    assert accept_payload["status"] == "ready-with-warnings"


def test_rebuild_supports_current_entry_as_default_source(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "invalid-missing-ref-stage-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    source_path = install_canonical_handoff(repo_root, fixture)
    install_current_mirror(repo_root, source_path)

    result = run_rebuild(repo_root=repo_root, use_current=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["source_entry_mode"] == "current"
    assert payload["rebuilt_handoff_path"] is not None


def test_rebuild_writes_report_but_blocks_on_bootstrap_current(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    install_current_bootstrap_placeholder(repo_root)

    result = run_rebuild(repo_root=repo_root, use_current=True)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["failure_class"] == "invalid-handoff"
    assert payload["report_path"] is not None
    assert Path(payload["report_path"]).exists()
