from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / ".codex/handoff-system/skill/project-handoff-accept/scripts/intake_handoff.py"
FIXTURE_DIR = REPO_ROOT / ".codex/handoff-system/tests/fixtures"
CURRENT_ENTRY_RELATIVE_PATH = Path(".codex/handoffs/CURRENT.md")


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
        else:
            result[key] = value
    return result


def setup_repo_root(tmp_path: Path, fixture_path: Path, *, make_dirty: bool = False) -> Path:
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

    if make_dirty:
        dirty_target = repo_root / frontmatter["authoritative_refs"][0]
        dirty_target.write_text(dirty_target.read_text(encoding="utf-8") + "dirty\n", encoding="utf-8")

    return repo_root


def install_current_mirror(repo_root: Path, fixture_path: Path) -> Path:
    fixture_frontmatter = load_frontmatter(fixture_path)
    history_path = repo_root / ".codex/handoffs/history" / fixture_path.name
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    current_path = repo_root / CURRENT_ENTRY_RELATIVE_PATH
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        "\n".join(
            [
                "---",
                f"handoff_id: {fixture_frontmatter['handoff_id']}",
                "entry_role: current-mirror",
                f"source_handoff_id: {fixture_frontmatter['handoff_id']}",
                f"source_path: {history_path.relative_to(repo_root)}",
                "source_hash: sha256:test",
                f"kind: {fixture_frontmatter['kind']}",
                "status: active",
                f"scope_key: {fixture_frontmatter['scope_key']}",
                f"safe_stop_kind: {fixture_frontmatter['safe_stop_kind']}",
                f"created_at: {fixture_frontmatter['created_at']}",
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
    subprocess.run(
        ["git", "add", str(history_path.relative_to(repo_root)), str(current_path.relative_to(repo_root))],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "add current mirror"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return current_path


def install_current_bootstrap_placeholder(repo_root: Path) -> Path:
    current_path = repo_root / CURRENT_ENTRY_RELATIVE_PATH
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        "\n".join(
            [
                "---",
                "entry_role: current-bootstrap",
                "status: bootstrap-placeholder",
                "created_at: 2026-04-06T00:00:00+08:00",
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
    return current_path


def run_accept(
    *,
    repo_root: Path,
    path: Path | None = None,
    use_current: bool = False,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH)]
    if use_current:
        command.append("--current")
    else:
        assert path is not None
        command.extend(["--handoff", str(path)])
    command.append("--json")
    return subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_accept_returns_ready_for_valid_phase_close_fixture(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    result = run_accept(path=fixture, repo_root=repo_root)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["kind"] == "phase-close"
    assert payload["scope_key"] == "effect-metadata"


def test_accept_returns_ready_with_warnings_for_draft_dirty_fixture(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-stage-close.md"
    repo_root = setup_repo_root(tmp_path, fixture, make_dirty=True)
    result = run_accept(path=fixture, repo_root=repo_root)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready-with-warnings"
    assert "handoff status is draft" in payload["warnings"]


def test_accept_supports_current_entry_and_resolves_to_canonical_handoff(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    current_path = install_current_mirror(repo_root, fixture)
    result = run_accept(repo_root=repo_root, use_current=True)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["entry_mode"] == "current"
    assert payload["entry_path"] == str(current_path)
    assert payload["handoff_path"].replace("\\", "/").endswith(
        "/.codex/handoffs/history/valid-phase-close.md"
    )
    assert payload["handoff_id"] == "2026-04-07_1600_effect-metadata_phase-close"


def test_accept_blocks_when_current_entry_is_bootstrap_placeholder(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "valid-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    install_current_bootstrap_placeholder(repo_root)
    result = run_accept(repo_root=repo_root, use_current=True)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert "bootstrap placeholder" in payload["blocking_issues"][0]


def test_accept_reports_advisory_warnings_for_stale_active_handoff(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "warning-stale-active-phase-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    result = run_accept(path=fixture, repo_root=repo_root)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready-with-warnings"
    assert any(
        "Authoritative Sources section is missing refs from frontmatter" in warning
        for warning in payload["warnings"]
    )
    assert any(
        "active handoff body still mentions canonical draft state" in warning
        for warning in payload["warnings"]
    )


def test_accept_returns_blocked_when_authoritative_ref_is_missing(tmp_path: Path) -> None:
    fixture = FIXTURE_DIR / "invalid-missing-ref-stage-close.md"
    repo_root = setup_repo_root(tmp_path, fixture)
    result = run_accept(path=fixture, repo_root=repo_root)
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert any("missing authoritative ref" in issue for issue in payload["blocking_issues"])
