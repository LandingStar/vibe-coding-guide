"""PackRegistrar — bridge Pack manifest extensions to runtime registries.

Reads validators, checks, scripts, and triggers declared in a PackManifest
and auto-registers the runtime-consumable ones into the platform registry
infrastructure.

Validator scripts are loaded as Python modules; if a module exposes a
``validate(data: dict) -> dict`` function it is wrapped as a
ScriptValidator. Check scripts follow the same pattern but expose
``check(context: dict) -> dict`` and are wrapped as ScriptCheck.
CLI-only self-check/bootstrap scripts should stay in the manifest's
``scripts`` field rather than ``validators`` or ``checks``.

Triggers are registered as lightweight event stubs in the
TriggerDispatcher.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
from types import ModuleType
from typing import Any

from ..validators.base import TriggerResult, ValidationResult
from ..validators.registry import ValidatorRegistry
from ..validators.script_check import ScriptCheck
from ..validators.script_validator import ScriptValidator
from ..validators.trigger_dispatcher import TriggerDispatcher

_log = logging.getLogger(__name__)


# ── Script Loading ────────────────────────────────────────────────────


def _load_module(path: Path) -> ModuleType | None:
    """Dynamically load a Python module from *path*.

    Returns ``None`` on any failure (logged as warning).
    """
    try:
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            _log.warning("Cannot create module spec for %s", path)
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    except Exception as exc:
        _log.warning("Failed to load module %s: %s", path, exc)
        return None


# ── Stub Trigger ──────────────────────────────────────────────────────


class _EventStubTrigger:
    """Minimal Trigger that records invocation for a declared event type."""

    def __init__(self, event_type: str, pack_name: str) -> None:
        self.event_type = event_type
        self.pack_name = pack_name

    def handle(self, event: dict) -> TriggerResult:
        return TriggerResult(
            handled=True,
            output={
                "source": f"pack:{self.pack_name}",
                "event_type": self.event_type,
            },
        )


# ── PackRegistrar ─────────────────────────────────────────────────────


class PackRegistrar:
    """Bridge between Pack manifests and ValidatorRegistry/TriggerDispatcher.

    Usage::

        registrar = PackRegistrar()
        registrar.register(manifest, base_dir)
        registry = registrar.registry
        dispatcher = registrar.dispatcher
    """

    def __init__(
        self,
        registry: ValidatorRegistry | None = None,
        dispatcher: TriggerDispatcher | None = None,
    ) -> None:
        self.registry = registry or ValidatorRegistry()
        self.dispatcher = dispatcher or TriggerDispatcher()
        self._registered_validators: list[str] = []
        self._registered_checks: list[str] = []
        self._registered_triggers: list[str] = []
        self._skipped: list[str] = []
        self._skipped_details: list[dict[str, str]] = []

    def register(self, manifest: Any, base_dir: Path) -> None:
        """Register extensions declared in *manifest* rooted at *base_dir*."""
        pack_name = getattr(manifest, "name", "unknown")
        self._register_validators(manifest, base_dir, pack_name)
        self._register_checks(manifest, base_dir, pack_name)
        self._register_triggers(manifest, pack_name)

    def _record_skip(
        self,
        *,
        name: str,
        path: Path,
        reason: str,
        detail: str = "",
    ) -> None:
        self._skipped.append(name)
        entry = {
            "name": name,
            "reason": reason,
            "path": str(path),
        }
        if detail:
            entry["detail"] = detail
        self._skipped_details.append(entry)

    def _register_validators(
        self, manifest: Any, base_dir: Path, pack_name: str
    ) -> None:
        for rel in getattr(manifest, "validators", None) or []:
            path = base_dir / rel
            name = f"{pack_name}:{Path(rel).stem}"
            if not path.exists():
                _log.warning("Validator script not found: %s", path)
                self._record_skip(
                    name=name,
                    path=path,
                    reason="missing-path",
                    detail="Validator script not found",
                )
                continue
            if not path.suffix == ".py":
                self._record_skip(
                    name=name,
                    path=path,
                    reason="unsupported-extension",
                    detail=f"Unsupported validator extension: {path.suffix or '<none>'}",
                )
                continue
            mod = _load_module(path)
            if mod is None:
                self._record_skip(
                    name=name,
                    path=path,
                    reason="load-failed",
                    detail="Failed to import validator module",
                )
                continue
            validate_fn = getattr(mod, "validate", None)
            if callable(validate_fn):
                sv = ScriptValidator(validate_fn)
                self.registry.register_validator(name, sv)
                self._registered_validators.append(name)
            else:
                # No validate() function — record as a manifest boundary mismatch.
                self._record_skip(
                    name=name,
                    path=path,
                    reason="missing-validate",
                    detail="Script does not expose callable validate(data) -> dict",
                )
                _log.info(
                    "Script %s has no validate(data)->dict function; skipped auto-registration",
                    path,
                )

    def _register_triggers(self, manifest: Any, pack_name: str) -> None:
        for event_type in getattr(manifest, "triggers", None) or []:
            name = f"{pack_name}:{event_type}"
            stub = _EventStubTrigger(event_type, pack_name)
            self.dispatcher.register(event_type, stub)
            self._registered_triggers.append(name)

    def _register_checks(self, manifest: Any, base_dir: Path, pack_name: str) -> None:
        for rel in getattr(manifest, "checks", None) or []:
            path = base_dir / rel
            name = f"{pack_name}:{Path(rel).stem}"
            if not path.exists():
                _log.warning("Check script not found: %s", path)
                self._record_skip(
                    name=name,
                    path=path,
                    reason="missing-path",
                    detail="Check script not found",
                )
                continue
            if path.suffix != ".py":
                self._record_skip(
                    name=name,
                    path=path,
                    reason="unsupported-extension",
                    detail=f"Unsupported check extension: {path.suffix or '<none>'}",
                )
                continue
            mod = _load_module(path)
            if mod is None:
                self._record_skip(
                    name=name,
                    path=path,
                    reason="load-failed",
                    detail="Failed to import check module",
                )
                continue
            check_fn = getattr(mod, "check", None)
            if callable(check_fn):
                script_check = ScriptCheck(check_fn)
                self.registry.register_check(name, script_check)
                self._registered_checks.append(name)
            else:
                self._record_skip(
                    name=name,
                    path=path,
                    reason="missing-check",
                    detail="Script does not expose callable check(context) -> dict",
                )
                _log.info(
                    "Script %s has no check(context)->dict function; skipped auto-registration",
                    path,
                )

    @property
    def registered_validators(self) -> list[str]:
        return list(self._registered_validators)

    @property
    def registered_checks(self) -> list[str]:
        return list(self._registered_checks)

    @property
    def registered_triggers(self) -> list[str]:
        return list(self._registered_triggers)

    @property
    def skipped(self) -> list[str]:
        return list(self._skipped)

    @property
    def skipped_details(self) -> list[dict[str, str]]:
        return [dict(item) for item in self._skipped_details]

    def summary(self) -> dict:
        """Return a summary dict suitable for Pipeline.info()."""
        return {
            "registered_validators": self._registered_validators,
            "registered_checks": self._registered_checks,
            "registered_triggers": self._registered_triggers,
            "skipped": self._skipped,
            "skipped_details": self.skipped_details,
        }
