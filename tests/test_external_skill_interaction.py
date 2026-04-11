from __future__ import annotations

from pathlib import Path

from src.workflow.external_skill_interaction import (
    REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS,
    build_external_skill_interaction_contract,
)


def test_build_external_skill_interaction_contract_lists_existing_targets(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs" / "external-skill-interaction.md").write_text("authority", encoding="utf-8")
    (tmp_path / ".github" / "skills" / "project-handoff-generate").mkdir(parents=True)
    (tmp_path / ".github" / "skills" / "project-handoff-generate" / "SKILL.md").write_text("skill", encoding="utf-8")
    (tmp_path / "doc-loop-vibe-coding" / "references").mkdir(parents=True)
    (tmp_path / "doc-loop-vibe-coding" / "references" / "external-skill-interaction.md").write_text("reference", encoding="utf-8")

    contract = build_external_skill_interaction_contract(tmp_path)
    drift = contract["companion_distribution_rule"]

    assert contract["automatic_stop_signal"] == "blocked"
    assert contract["reference_implementation"]["family"] == "project-handoff-*"
    assert "docs/external-skill-interaction.md" in drift["authority_sources"]
    assert ".github/skills/project-handoff-generate/SKILL.md" in drift["shipped_copies"]
    assert "doc-loop-vibe-coding/references/external-skill-interaction.md" in drift["shipped_copies"]


def test_build_external_skill_interaction_contract_accepts_rule_overrides(tmp_path: Path) -> None:
    contract = build_external_skill_interaction_contract(
        tmp_path,
        {
            "external_skill_interaction": {
                "automatic_stop_signal": "halt",
                "authority_transfer_requires_primitives": ["handoff"],
            }
        },
    )

    assert contract["automatic_stop_signal"] == "halt"
    assert contract["authority_transfer_requires_primitives"] == ["handoff"]


def test_required_markers_are_stable() -> None:
    assert "blocked is the only automatic stop signal." in REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS
    assert len(REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS) >= 5