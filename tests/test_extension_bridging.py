"""Tests for Phase 25 — PackRegistrar (extension bridging)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.pack.manifest_loader import PackManifest, load, load_dict
from src.pack.registrar import PackRegistrar
from src.validators.registry import ValidatorRegistry
from src.validators.trigger_dispatcher import TriggerDispatcher


ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ───────────────────────────────────────────────────────────


def _make_pack_with_extensions(tmpdir: Path) -> tuple[PackManifest, Path]:
    """Create a pack dir with a validator script and triggers."""
    pack_dir = tmpdir / "test-pack"
    pack_dir.mkdir()

    # Validator script with validate() function
    scripts_dir = pack_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "check_fields.py").write_text(
        'def validate(data: dict) -> dict:\n'
        '    if "name" not in data:\n'
        '        return {"valid": False, "errors": ["missing name"]}\n'
        '    return {"valid": True, "errors": []}\n',
        encoding="utf-8",
    )

    # Validator script WITHOUT validate() function (should be skipped)
    (scripts_dir / "standalone.py").write_text(
        'import sys\nprint("standalone script")\n',
        encoding="utf-8",
    )

    manifest_data = {
        "name": "test-pack",
        "version": "0.1.0",
        "kind": "official-instance",
        "validators": [
            "scripts/check_fields.py",
            "scripts/standalone.py",
        ],
        "checks": [],
        "scripts": ["scripts/check_fields.py", "scripts/standalone.py"],
        "triggers": ["chat", "writeback"],
    }
    manifest = load_dict(manifest_data)
    (pack_dir / "pack-manifest.json").write_text(
        json.dumps(manifest_data, indent=2), encoding="utf-8"
    )
    return manifest, pack_dir


def _make_empty_pack(tmpdir: Path) -> tuple[PackManifest, Path]:
    """Create a pack with no extensions."""
    pack_dir = tmpdir / "empty-pack"
    pack_dir.mkdir()
    manifest_data = {
        "name": "empty-pack",
        "version": "0.1.0",
        "kind": "project-local",
    }
    manifest = load_dict(manifest_data)
    return manifest, pack_dir


# ── PackRegistrar Core Tests ──────────────────────────────────────────


class TestPackRegistrarValidators(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp())
        self._manifest, self._pack_dir = _make_pack_with_extensions(self._tmpdir)
        self._registrar = PackRegistrar()
        self._registrar.register(self._manifest, self._pack_dir)

    def test_validator_with_validate_fn_registered(self) -> None:
        names = self._registrar.registry.list_validators()
        self.assertIn("test-pack:check_fields", names)

    def test_validator_without_validate_fn_skipped(self) -> None:
        names = self._registrar.registry.list_validators()
        self.assertNotIn("test-pack:standalone", names)
        self.assertIn("test-pack:standalone", self._registrar.skipped)

    def test_registered_validator_works(self) -> None:
        v = self._registrar.registry.get_validator("test-pack:check_fields")
        self.assertIsNotNone(v)
        result = v.validate({"name": "test"})
        self.assertTrue(result.valid)

    def test_registered_validator_detects_error(self) -> None:
        v = self._registrar.registry.get_validator("test-pack:check_fields")
        result = v.validate({})
        self.assertFalse(result.valid)
        self.assertIn("missing name", result.errors)

    def test_registered_validators_list(self) -> None:
        self.assertEqual(self._registrar.registered_validators, ["test-pack:check_fields"])


class TestPackRegistrarTriggers(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = Path(tempfile.mkdtemp())
        self._manifest, self._pack_dir = _make_pack_with_extensions(self._tmpdir)
        self._registrar = PackRegistrar()
        self._registrar.register(self._manifest, self._pack_dir)

    def test_triggers_registered(self) -> None:
        self.assertIn("test-pack:chat", self._registrar.registered_triggers)
        self.assertIn("test-pack:writeback", self._registrar.registered_triggers)

    def test_trigger_dispatch_works(self) -> None:
        results = self._registrar.dispatcher.dispatch({"type": "chat", "data": "hello"})
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].handled)
        self.assertEqual(results[0].output["event_type"], "chat")

    def test_unregistered_event_no_dispatch(self) -> None:
        results = self._registrar.dispatcher.dispatch({"type": "unknown_event"})
        self.assertEqual(len(results), 0)


class TestPackRegistrarEmptyPack(unittest.TestCase):
    def test_empty_pack_no_error(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        manifest, pack_dir = _make_empty_pack(tmpdir)
        registrar = PackRegistrar()
        registrar.register(manifest, pack_dir)
        self.assertEqual(registrar.registered_validators, [])
        self.assertEqual(registrar.registered_triggers, [])
        self.assertEqual(registrar.skipped, [])


class TestPackRegistrarMissingFile(unittest.TestCase):
    def test_missing_validator_file_skipped(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        pack_dir = tmpdir / "bad-pack"
        pack_dir.mkdir()
        manifest = load_dict({
            "name": "bad-pack",
            "version": "0.1.0",
            "kind": "project-local",
            "validators": ["scripts/nonexistent.py"],
        })
        registrar = PackRegistrar()
        registrar.register(manifest, pack_dir)
        self.assertEqual(registrar.registered_validators, [])
        self.assertIn("bad-pack:nonexistent", registrar.skipped)
        detail = next(
            item for item in registrar.skipped_details if item["name"] == "bad-pack:nonexistent"
        )
        self.assertEqual(detail["reason"], "missing-path")


class TestPackRegistrarSummary(unittest.TestCase):
    def test_summary_dict(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        manifest, pack_dir = _make_pack_with_extensions(tmpdir)
        registrar = PackRegistrar()
        registrar.register(manifest, pack_dir)
        s = registrar.summary()
        self.assertIn("registered_validators", s)
        self.assertIn("registered_triggers", s)
        self.assertIn("skipped", s)
        self.assertIn("skipped_details", s)
        self.assertIn("test-pack:check_fields", s["registered_validators"])
        self.assertIn("test-pack:chat", s["registered_triggers"])
        detail = next(
            item for item in s["skipped_details"] if item["name"] == "test-pack:standalone"
        )
        self.assertEqual(detail["reason"], "missing-validate")


class TestPackRegistrarCustomRegistry(unittest.TestCase):
    def test_uses_provided_registry(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        manifest, pack_dir = _make_pack_with_extensions(tmpdir)
        reg = ValidatorRegistry()
        disp = TriggerDispatcher()
        registrar = PackRegistrar(registry=reg, dispatcher=disp)
        registrar.register(manifest, pack_dir)
        self.assertIn("test-pack:check_fields", reg.list_validators())
        self.assertIn("chat", disp.list_event_types())


# ── Pipeline Integration Tests ────────────────────────────────────────


class TestPipelineRegistrar(unittest.TestCase):
    def test_pipeline_info_includes_registrar(self) -> None:
        from src.workflow.pipeline import Pipeline

        tmpdir = Path(tempfile.mkdtemp())
        # Create minimal project with a planning-gate
        gate_dir = tmpdir / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "test.md").write_text("# Test", encoding="utf-8")
        # Pack with triggers
        pack_dir = tmpdir / ".codex" / "packs"
        pack_dir.mkdir(parents=True)
        manifest = {
            "name": "local-pack",
            "version": "0.1.0",
            "kind": "project-local",
            "triggers": ["chat"],
        }
        (pack_dir / "local.pack.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        pipeline = Pipeline.from_project(tmpdir, dry_run=True)
        info = pipeline.info()
        self.assertIn("registered_triggers", info)
        self.assertIn("local-pack:chat", info["registered_triggers"])

    def test_pipeline_info_exposes_skipped_details_for_official_instance(self) -> None:
        from src.workflow.pipeline import Pipeline

        pipeline = Pipeline.from_project(ROOT, dry_run=True)
        info = pipeline.info()
        self.assertIn("skipped_details", info)
        detail_names = {item["name"] for item in info["skipped_details"]}
        self.assertNotIn("doc-loop-vibe-coding:validate_doc_loop", detail_names)
        self.assertNotIn("doc-loop-vibe-coding:validate_instance_pack", detail_names)


class TestOfficialInstanceValidatorDiagnostics(unittest.TestCase):
    def test_official_instance_self_checks_stay_in_scripts_field(self) -> None:
        manifest = load(ROOT / "doc-loop-vibe-coding" / "pack-manifest.json")
        registrar = PackRegistrar()
        registrar.register(manifest, ROOT / "doc-loop-vibe-coding")

        self.assertEqual(manifest.validators, [])
        self.assertIn("scripts/validate_doc_loop.py", manifest.scripts)
        self.assertIn("scripts/validate_instance_pack.py", manifest.scripts)
        detail_names = {item["name"] for item in registrar.skipped_details}
        self.assertNotIn("doc-loop-vibe-coding:validate_doc_loop", detail_names)
        self.assertNotIn("doc-loop-vibe-coding:validate_instance_pack", detail_names)


if __name__ == "__main__":
    unittest.main()
