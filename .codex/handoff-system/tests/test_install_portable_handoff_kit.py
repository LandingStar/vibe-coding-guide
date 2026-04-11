from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALL_SCRIPT = (
    REPO_ROOT
    / ".codex/handoff-system/scripts/install_portable_handoff_kit.py"
)


def test_install_portable_handoff_kit_bootstraps_target_repo_and_registers_skills(
    tmp_path: Path,
) -> None:
    target_repo = tmp_path / "sample game repo"
    target_repo.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            str(INSTALL_SCRIPT),
            "--target-repo",
            str(target_repo),
            "--skill-prefix",
            "sample-game",
            "--register",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["skill_prefix"] == "sample-game"
    assert payload["skill_names"] == [
        "sample-game-handoff-generate",
        "sample-game-handoff-accept",
        "sample-game-handoff-refresh-current",
        "sample-game-handoff-rebuild",
    ]

    assert (target_repo / "design_docs/tooling/Session Handoff Standard.md").exists()
    assert (
        target_repo
        / "design_docs/tooling/Session Handoff Conditional Blocks.md"
    ).exists()
    assert (target_repo / "design_docs/Project Master Checklist.md").exists()
    assert (
        target_repo / "design_docs/Global Phase Map and Current Position.md"
    ).exists()

    current_path = target_repo / ".codex/handoffs/CURRENT.md"
    current_content = current_path.read_text(encoding="utf-8")
    assert "entry_role: current-bootstrap" in current_content
    assert "status: bootstrap-placeholder" in current_content

    generate_skill_path = (
        target_repo
        / ".codex/handoff-system/skill/sample-game-handoff-generate/SKILL.md"
    )
    generate_skill_text = generate_skill_path.read_text(encoding="utf-8")
    assert "name: sample-game-handoff-generate" in generate_skill_text
    assert "/sample-game-handoff-generate" in generate_skill_text

    generate_openai_yaml = (
        target_repo
        / ".codex/handoff-system/skill/sample-game-handoff-generate/agents/openai.yaml"
    ).read_text(encoding="utf-8")
    assert 'display_name: "Sample Game Handoff Generate"' in generate_openai_yaml

    registered_skill = target_repo / ".github/skills/sample-game-handoff-generate"
    assert registered_skill.is_symlink()
    assert registered_skill.resolve() == (
        target_repo / ".codex/handoff-system/skill/sample-game-handoff-generate"
    ).resolve()

