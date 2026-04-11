from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
REFRESH_SCRIPT_PATH = (
    REPO_ROOT
    / ".codex/handoff-system/skill/project-handoff-refresh-current/scripts/refresh_current.py"
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
            assert isinstance(result[current_list_key], list)
            result[current_list_key].append(line[4:])
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


def setup_repo_root(tmp_path: Path, *fixture_paths: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    for fixture_path in fixture_paths:
        frontmatter = load_frontmatter(fixture_path)
        for ref in frontmatter["authoritative_refs"]:
            ref_path = repo_root / ref
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            ref_path.write_text(f"fixture:{ref}\n", encoding="utf-8")

    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    return repo_root


def install_canonical_handoff(
    repo_root: Path,
    fixture_path: Path,
    *,
    file_name: str | None = None,
) -> Path:
    target_name = file_name or fixture_path.name
    handoff_path = repo_root / ".codex/handoffs/history" / target_name
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
    return handoff_path


def run_refresh(
    *,
    repo_root: Path,
    path: Path | None = None,
    latest_draft: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(REFRESH_SCRIPT_PATH)]
    if latest_draft:
        command.append("--latest-draft")
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


def run_accept_current(*, repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ACCEPT_SCRIPT_PATH), "--current", "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_refresh_promotes_draft_and_updates_current_mirror(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-stage-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    handoff_path = install_canonical_handoff(repo_root, fixture)

    result = run_refresh(repo_root=repo_root, latest_draft=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["selection_mode"] == "latest-draft"

    handoff_frontmatter = load_frontmatter(handoff_path)
    current_frontmatter = load_frontmatter(repo_root / ".codex/handoffs/CURRENT.md")
    assert handoff_frontmatter["status"] == "active"
    assert current_frontmatter["entry_role"] == "current-mirror"
    assert current_frontmatter["source_handoff_id"] == handoff_frontmatter["handoff_id"]

    accept_result = run_accept_current(repo_root=repo_root)
    assert accept_result.returncode == 0
    accept_payload = json.loads(accept_result.stdout)
    assert accept_payload["status"] == "ready-with-warnings"
    assert any("workspace is dirty" in warning for warning in accept_payload["warnings"])
    assert accept_payload["handoff_id"] == handoff_frontmatter["handoff_id"]


def test_refresh_supersedes_previous_active_handoff(tmp_path: Path) -> None:
    old_fixture = FIXTURE_DIR / "valid-phase-close.md"
    new_fixture = FIXTURE_DIR / "valid-stage-close.md"
    repo_root = setup_repo_root(tmp_path, old_fixture, new_fixture)
    old_path = install_canonical_handoff(repo_root, old_fixture, file_name="old-active.md")
    new_path = install_canonical_handoff(repo_root, new_fixture, file_name="new-draft.md")

    result = run_refresh(repo_root=repo_root, path=new_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"

    old_frontmatter = load_frontmatter(old_path)
    new_frontmatter = load_frontmatter(new_path)
    current_frontmatter = load_frontmatter(repo_root / ".codex/handoffs/CURRENT.md")
    assert old_frontmatter["status"] == "superseded"
    assert new_frontmatter["status"] == "active"
    assert new_frontmatter["supersedes"] == old_frontmatter["handoff_id"]
    assert current_frontmatter["source_handoff_id"] == new_frontmatter["handoff_id"]


def test_refresh_blocks_when_no_draft_is_available_for_auto_selection(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    install_canonical_handoff(repo_root, fixture)

    result = run_refresh(repo_root=repo_root, latest_draft=True)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["selection_mode"] == "latest-draft"
    assert any("no draft canonical handoff is available" in issue for issue in payload["blocking_issues"])
