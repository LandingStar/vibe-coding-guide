from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


LOCAL_PROMPTS = [
    ".codex/prompts/doc-loop/01-planning-gate.md",
    ".codex/prompts/doc-loop/02-execute-by-doc.md",
    ".codex/prompts/doc-loop/03-writeback.md",
]

BOOTSTRAP_PROMPTS = [
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/01-planning-gate.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/02-execute-by-doc.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/03-writeback.md",
]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_local_prompts_require_askquestions_for_progression() -> None:
    for rel_path in LOCAL_PROMPTS:
        text = _read(rel_path)
        assert "askQuestions" in text


def test_bootstrap_prompts_require_askquestions_for_progression() -> None:
    for rel_path in BOOTSTRAP_PROMPTS:
        text = _read(rel_path)
        assert "askQuestions" in text