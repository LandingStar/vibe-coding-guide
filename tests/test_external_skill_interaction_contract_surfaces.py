from __future__ import annotations

import json
from pathlib import Path

from src.workflow.external_skill_interaction import (
    REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS,
    build_external_skill_interaction_contract,
)


ROOT = Path(__file__).resolve().parent.parent


def test_handoff_reference_implementation_files_include_shared_markers() -> None:
    contract = build_external_skill_interaction_contract(ROOT)
    drift = contract["companion_distribution_rule"]

    for rel_path in drift["shipped_copies"]:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        for marker in REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS:
            assert marker in text


def test_official_instance_manifest_loads_external_skill_interaction_reference() -> None:
    manifest_path = ROOT / "doc-loop-vibe-coding" / "pack-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "references/external-skill-interaction.md" in manifest["always_on"]


def test_authority_doc_includes_shared_markers() -> None:
    text = (ROOT / "docs" / "external-skill-interaction.md").read_text(encoding="utf-8")
    for marker in REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS:
        assert marker in text