"""Tests for Phase 26 — on_demand lazy loading API."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.manifest_loader import load_dict


# ── Helpers ───────────────────────────────────────────────────────────


def _make_pack_with_on_demand(tmpdir: Path) -> Path:
    """Create a pack with on_demand files."""
    pack_dir = tmpdir / "test-pack"
    pack_dir.mkdir()

    # On-demand files
    scripts_dir = pack_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "validate.py").write_text(
        "# validate script\nprint('ok')\n", encoding="utf-8"
    )
    (scripts_dir / "bootstrap.py").write_text(
        "# bootstrap script\nprint('bootstrap')\n", encoding="utf-8"
    )

    docs_dir = pack_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text(
        "# User Guide\n\nStep 1: do something.\n", encoding="utf-8"
    )

    manifest_data = {
        "name": "test-pack",
        "version": "0.1.0",
        "kind": "official-instance",
        "on_demand": [
            "scripts/validate.py",
            "scripts/bootstrap.py",
            "docs/guide.md",
            "docs/nonexistent.md",  # does not exist
        ],
        "always_on": [],
    }
    manifest = load_dict(manifest_data)
    (pack_dir / "pack-manifest.json").write_text(
        json.dumps(manifest_data, indent=2), encoding="utf-8"
    )
    return pack_dir


# ── PackContext on_demand Tests ───────────────────────────────────────


class TestOnDemandEntries(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp())
        pack_dir = _make_pack_with_on_demand(self._tmpdir)
        manifest = load_dict(
            json.loads((pack_dir / "pack-manifest.json").read_text(encoding="utf-8"))
        )
        builder = ContextBuilder()
        builder.add_pack(manifest, pack_dir)
        self._ctx = builder.build()

    def test_on_demand_entries_populated(self) -> None:
        self.assertIn("scripts/validate.py", self._ctx.on_demand_entries)
        self.assertIn("scripts/bootstrap.py", self._ctx.on_demand_entries)
        self.assertIn("docs/guide.md", self._ctx.on_demand_entries)

    def test_list_on_demand(self) -> None:
        keys = self._ctx.list_on_demand()
        self.assertEqual(len(keys), 4)
        self.assertIn("scripts/validate.py", keys)


class TestLoadOnDemand(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp())
        pack_dir = _make_pack_with_on_demand(self._tmpdir)
        manifest = load_dict(
            json.loads((pack_dir / "pack-manifest.json").read_text(encoding="utf-8"))
        )
        builder = ContextBuilder()
        builder.add_pack(manifest, pack_dir)
        self._ctx = builder.build()

    def test_load_existing_file(self) -> None:
        content = self._ctx.load_on_demand("scripts/validate.py")
        self.assertIsNotNone(content)
        self.assertIn("validate", content)

    def test_load_guide_md(self) -> None:
        content = self._ctx.load_on_demand("docs/guide.md")
        self.assertIsNotNone(content)
        self.assertIn("User Guide", content)

    def test_load_nonexistent_file(self) -> None:
        content = self._ctx.load_on_demand("docs/nonexistent.md")
        self.assertIsNone(content)

    def test_load_undeclared_key(self) -> None:
        content = self._ctx.load_on_demand("totally/unknown.md")
        self.assertIsNone(content)

    def test_caching(self) -> None:
        # First load
        content1 = self._ctx.load_on_demand("scripts/validate.py")
        # Second load should come from cache
        content2 = self._ctx.load_on_demand("scripts/validate.py")
        self.assertEqual(content1, content2)
        # Verify it's in cache
        self.assertIn("scripts/validate.py", self._ctx._on_demand_cache)

    def test_load_multiple_files(self) -> None:
        c1 = self._ctx.load_on_demand("scripts/validate.py")
        c2 = self._ctx.load_on_demand("scripts/bootstrap.py")
        self.assertIsNotNone(c1)
        self.assertIsNotNone(c2)
        self.assertIn("validate", c1)
        self.assertIn("bootstrap", c2)


class TestMultiPackOnDemand(unittest.TestCase):
    """Test on_demand merging across multiple packs."""

    def test_later_pack_overrides(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())

        # Pack A (lower priority)
        pack_a_dir = tmpdir / "pack-a"
        pack_a_dir.mkdir()
        (pack_a_dir / "shared.md").write_text("content from A", encoding="utf-8")
        manifest_a = load_dict({
            "name": "pack-a",
            "version": "0.1.0",
            "kind": "platform-default",
            "on_demand": ["shared.md"],
        })

        # Pack B (higher priority)
        pack_b_dir = tmpdir / "pack-b"
        pack_b_dir.mkdir()
        (pack_b_dir / "shared.md").write_text("content from B", encoding="utf-8")
        manifest_b = load_dict({
            "name": "pack-b",
            "version": "0.1.0",
            "kind": "project-local",
            "on_demand": ["shared.md"],
        })

        builder = ContextBuilder()
        builder.add_pack(manifest_a, pack_a_dir)
        builder.add_pack(manifest_b, pack_b_dir)
        ctx = builder.build()

        content = ctx.load_on_demand("shared.md")
        self.assertIsNotNone(content)
        # project-local (B) should override platform-default (A)
        self.assertIn("content from B", content)


# ── MCP Resource Integration Test ────────────────────────────────────


class TestMCPResourceUsesOnDemand(unittest.TestCase):
    """Verify that GovernanceTools.read_resource() uses load_on_demand."""

    def test_on_demand_resource_via_mcp(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())

        # planning gate
        gate_dir = tmpdir / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "test.md").write_text("# Test", encoding="utf-8")

        # Pack with on_demand
        pack_dir = tmpdir / "my-pack"
        pack_dir.mkdir()
        scripts_dir = pack_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "helper.py").write_text("# helper", encoding="utf-8")

        manifest = {
            "name": "my-pack",
            "version": "0.1.0",
            "kind": "official-instance",
            "on_demand": ["scripts/helper.py"],
        }
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        from src.mcp.tools import GovernanceTools

        tools = GovernanceTools(tmpdir, dry_run=True)
        content = tools.read_resource("pack://my-pack/on-demand/scripts/helper.py")
        self.assertIsNotNone(content)
        self.assertIn("helper", content)


# ── Pipeline info on_demand Test ─────────────────────────────────────


class TestPipelineInfoOnDemand(unittest.TestCase):
    def test_pipeline_pack_context_has_on_demand(self) -> None:
        from src.workflow.pipeline import Pipeline

        tmpdir = Path(tempfile.mkdtemp())
        gate_dir = tmpdir / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "test.md").write_text("# Test", encoding="utf-8")

        pack_dir = tmpdir / ".codex" / "packs"
        pack_dir.mkdir(parents=True)
        (pack_dir / "data.txt").write_text("some data", encoding="utf-8")
        manifest = {
            "name": "local",
            "version": "0.1.0",
            "kind": "project-local",
            "on_demand": ["data.txt"],
        }
        (pack_dir / "local.pack.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        pipeline = Pipeline.from_project(tmpdir, dry_run=True)
        ctx = pipeline.pack_context
        self.assertIn("data.txt", ctx.list_on_demand())
        content = ctx.load_on_demand("data.txt")
        self.assertIsNotNone(content)
        self.assertEqual(content, "some data")


if __name__ == "__main__":
    unittest.main()
