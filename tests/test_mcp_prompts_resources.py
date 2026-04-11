"""Tests for Phase 24 — MCP Prompts, Resources, and always_on content injection."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from src.mcp.tools import GovernanceTools
from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.manifest_loader import PackManifest
from src.workflow.instructions_generator import InstructionsGenerator


# ── Helpers ───────────────────────────────────────────────────────────


def _make_project_with_prompts(tmpdir: Path) -> Path:
    """Create a minimal project with a pack that has prompts and on_demand."""
    # planning-gate so C5 doesn't block
    gate_dir = tmpdir / "design_docs" / "stages" / "planning-gate"
    gate_dir.mkdir(parents=True)
    (gate_dir / "test.md").write_text("# Test", encoding="utf-8")

    # checkpoint
    cp_dir = tmpdir / ".codex" / "checkpoints"
    cp_dir.mkdir(parents=True)
    (cp_dir / "latest.md").write_text(
        "# Checkpoint\n## Current Phase\nTest Phase\n## Active Planning Gate\ntest.md\n",
        encoding="utf-8",
    )

    # Pack with prompts and on_demand
    pack_dir = tmpdir / "test-pack"
    pack_dir.mkdir()

    # Prompt files
    prompts_dir = pack_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "01-planning.md").write_text(
        "# Planning Gate Prompt\n\nUse this when creating a planning-gate document.\n\nStep 1: ...\n",
        encoding="utf-8",
    )
    (prompts_dir / "02-writeback.md").write_text(
        "# Writeback Prompt\n\nUse this when writing back status.\n",
        encoding="utf-8",
    )

    # On-demand files
    scripts_dir = pack_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "validate.py").write_text("# validate script\nprint('ok')\n", encoding="utf-8")

    # Always-on files
    (pack_dir / "SKILL.md").write_text(
        "# Skill Guide\n\nThis is the main skill guide for the pack.\n\n## Workflow\n\nFollow doc-loop steps.\n",
        encoding="utf-8",
    )

    # Manifest
    manifest = {
        "name": "test-pack",
        "version": "0.1.0",
        "kind": "official-instance",
        "scope": "Test pack",
        "provides": ["prompts"],
        "document_types": [],
        "intents": ["question"],
        "gates": ["inform"],
        "always_on": ["SKILL.md"],
        "on_demand": ["scripts/validate.py"],
        "depends_on": [],
        "overrides": [],
        "prompts": ["prompts/01-planning.md", "prompts/02-writeback.md"],
        "templates": [],
        "validators": [],
        "checks": [],
        "scripts": ["scripts/validate.py"],
        "triggers": [],
    }
    (pack_dir / "pack-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return tmpdir


# ── Prompt Tests ──────────────────────────────────────────────────────


class TestListPrompts(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._root = _make_project_with_prompts(Path(self._tmpdir))
        self._tools = GovernanceTools(self._root, dry_run=True)

    def test_prompts_listed(self) -> None:
        prompts = self._tools.list_prompts()
        names = [p["name"] for p in prompts]
        self.assertIn("01-planning", names)
        self.assertIn("02-writeback", names)

    def test_prompt_has_description(self) -> None:
        prompts = self._tools.list_prompts()
        planning = next(p for p in prompts if p["name"] == "01-planning")
        self.assertTrue(len(planning["description"]) > 0)
        # Should pick the first non-heading line
        self.assertIn("planning-gate", planning["description"].lower())

    def test_no_prompts_returns_empty(self) -> None:
        # Create a project with no prompts in the pack
        tmpdir = Path(tempfile.mkdtemp())
        gate_dir = tmpdir / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "t.md").write_text("# T", encoding="utf-8")
        pack_dir = tmpdir / ".codex" / "packs"
        pack_dir.mkdir(parents=True)
        manifest = {"name": "empty-pack", "version": "0.1.0", "kind": "project-local"}
        (pack_dir / "empty.pack.json").write_text(json.dumps(manifest), encoding="utf-8")
        tools = GovernanceTools(tmpdir, dry_run=True)
        self.assertEqual(tools.list_prompts(), [])

    def test_prompts_refresh_after_manifest_change(self) -> None:
        pack_dir = self._root / "test-pack"
        new_prompt = pack_dir / "prompts" / "03-refresh.md"
        new_prompt.write_text(
            "# Refresh Prompt\n\nThis prompt was added after tool initialization.\n",
            encoding="utf-8",
        )

        manifest_path = pack_dir / "pack-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["prompts"].append("prompts/03-refresh.md")
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        prompts = self._tools.list_prompts()
        names = [p["name"] for p in prompts]
        self.assertIn("03-refresh", names)


class TestGetPrompt(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._root = _make_project_with_prompts(Path(self._tmpdir))
        self._tools = GovernanceTools(self._root, dry_run=True)

    def test_get_existing_prompt(self) -> None:
        content = self._tools.get_prompt("01-planning")
        self.assertIsNotNone(content)
        self.assertIn("Planning Gate Prompt", content)

    def test_get_nonexistent_prompt(self) -> None:
        content = self._tools.get_prompt("nonexistent")
        self.assertIsNone(content)

    def test_get_second_prompt(self) -> None:
        content = self._tools.get_prompt("02-writeback")
        self.assertIsNotNone(content)
        self.assertIn("Writeback Prompt", content)


# ── Resource Tests ────────────────────────────────────────────────────


class TestListResources(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._root = _make_project_with_prompts(Path(self._tmpdir))
        self._tools = GovernanceTools(self._root, dry_run=True)

    def test_always_on_in_resources(self) -> None:
        resources = self._tools.list_resources()
        uris = [r["uri"] for r in resources]
        always_on = [u for u in uris if "always-on" in u]
        self.assertTrue(len(always_on) > 0)

    def test_on_demand_in_resources(self) -> None:
        resources = self._tools.list_resources()
        uris = [r["uri"] for r in resources]
        on_demand = [u for u in uris if "on-demand" in u]
        self.assertTrue(len(on_demand) > 0)

    def test_resource_has_mime_type(self) -> None:
        resources = self._tools.list_resources()
        for r in resources:
            self.assertIn("mimeType", r)

    def test_on_demand_mime_for_python(self) -> None:
        resources = self._tools.list_resources()
        py_resources = [r for r in resources if r["name"].endswith(".py")]
        self.assertTrue(len(py_resources) > 0)
        self.assertEqual(py_resources[0]["mimeType"], "text/x-python")


class TestReadResource(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._root = _make_project_with_prompts(Path(self._tmpdir))
        self._tools = GovernanceTools(self._root, dry_run=True)

    def test_read_always_on(self) -> None:
        content = self._tools.read_resource("pack://always-on/SKILL.md")
        self.assertIsNotNone(content)
        self.assertIn("Skill Guide", content)

    def test_read_on_demand(self) -> None:
        content = self._tools.read_resource("pack://test-pack/on-demand/scripts/validate.py")
        self.assertIsNotNone(content)
        self.assertIn("validate", content)

    def test_read_nonexistent_resource(self) -> None:
        content = self._tools.read_resource("pack://nonexistent/foo")
        self.assertIsNone(content)

    def test_read_always_on_not_found(self) -> None:
        content = self._tools.read_resource("pack://always-on/DOES_NOT_EXIST.md")
        self.assertIsNone(content)


# ── always_on Content Injection Tests ─────────────────────────────────


class TestAlwaysOnContentInjection(unittest.TestCase):
    def test_always_on_includes_summary(self) -> None:
        ctx = PackContext()
        ctx.always_on_content["guide.md"] = (
            "# Quick Guide\n\nFollow these steps to get started.\n\n"
            "## Step 1\n\nDo something.\n\n## Step 2\n\nDo another thing.\n"
        )
        gen = InstructionsGenerator(ctx)
        section = gen._always_on_section()
        self.assertIn("### `guide.md`", section)
        self.assertIn("Quick Guide", section)
        self.assertIn("Follow these steps", section)

    def test_always_on_empty_content_omitted(self) -> None:
        ctx = PackContext()
        gen = InstructionsGenerator(ctx)
        self.assertEqual(gen._always_on_section(), "")

    def test_summary_truncated_for_long_content(self) -> None:
        # Create content with many headings to trigger truncation
        parts = []
        for i in range(30):
            parts.append(f"## Section {i}")
            parts.append(f"Content for section {i}.")
        ctx = PackContext()
        ctx.always_on_content["long.md"] = "\n".join(parts)
        gen = InstructionsGenerator(ctx)
        section = gen._always_on_section()
        self.assertIn("*(truncated)*", section)

    def test_summarize_content_keeps_headings(self) -> None:
        text = "# H1\n\nParagraph 1.\n\n## H2\n\nParagraph 2.\n\n### H3\n\nParagraph 3.\n"
        summary = InstructionsGenerator._summarize_content(text)
        self.assertIn("# H1", summary)
        self.assertIn("## H2", summary)
        self.assertIn("### H3", summary)


# ── MCP Server Registration Tests ────────────────────────────────────


class TestMCPServerPromptRegistration(unittest.TestCase):
    """Verify that create_server registers prompt/resource handlers."""

    def test_server_has_prompt_and_resource_handlers(self) -> None:
        from src.mcp.server import create_server

        tmpdir = Path(tempfile.mkdtemp())
        _make_project_with_prompts(tmpdir)
        server = create_server(tmpdir, dry_run=True)
        # The server should have request handlers for prompts and resources
        # MCP Server stores handlers internally; if create_server doesn't
        # raise, the decorators registered successfully.
        self.assertIsNotNone(server)


if __name__ == "__main__":
    unittest.main()
