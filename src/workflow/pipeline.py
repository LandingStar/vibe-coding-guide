"""Pipeline orchestrator — unified PDP → PEP governance chain.

Assembles ManifestLoader → ContextBuilder → OverrideResolver → PDP →
PEP into a single ``Pipeline.process(input)`` call.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..audit.audit_logger import AuditLogger, MemoryAuditBackend
from ..audit.decision_log import DecisionLogStore, build_entry as build_decision_log_entry
from ..pack import manifest_loader
from ..pack.context_builder import ContextBuilder, PackContext
from ..pack.manifest_loader import LoadLevel
from ..pack.override_resolver import RuleConfig, resolve as resolve_rules
from ..pack.pack_integrity import load_lock, verify_pack as _verify_pack_integrity
from ..pack.registrar import PackRegistrar
from ..pdp.decision_envelope import build_envelope
from ..pep.executor import Executor
from ..pep.writeback_engine import WritebackEngine

if TYPE_CHECKING:
    from ..interfaces import ContractFactory, ReportValidator, WorkerBackend

_log = logging.getLogger(__name__)


# ── Error info ────────────────────────────────────────────────────────────


@dataclass
class ErrorInfo:
    """Structured error record shared across Pipeline / MCP / CLI."""

    category: str  # init_failed | manifest_invalid | constraint_violated | process_failed | unknown
    message: str
    source: str = ""  # pipeline | mcp | cli | pack_loader
    suggestion: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {
            "error": self.category,
            "message": self.message,
        }
        if self.source:
            d["source"] = self.source
        if self.suggestion:
            d["suggestion"] = self.suggestion
        if self.detail:
            d["detail"] = self.detail
        return d


# ── Result types ──────────────────────────────────────────────────────────


@dataclass
class PipelineResult:
    """Typed result from a single ``Pipeline.process()`` call."""

    envelope: dict = field(default_factory=dict)
    execution: dict = field(default_factory=dict)
    audit_events: list[dict] = field(default_factory=list)
    pack_info: dict = field(default_factory=dict)
    decision_log_entry: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {
            "envelope": self.envelope,
            "execution": {
                k: v for k, v in self.execution.items() if k != "_rsm"
            },
            "audit_events": self.audit_events,
            "pack_info": self.pack_info,
        }
        if self.decision_log_entry:
            d["decision_log_entry"] = self.decision_log_entry
        return d


@dataclass
class ConstraintViolation:
    """A single constraint violation."""

    constraint: str  # e.g. "C5"
    message: str
    severity: str = "block"  # "block" | "warn"


@dataclass(frozen=True)
class ConstraintScope:
    """Describe how a project constraint is enforced."""

    constraint: str
    enforcement: str  # "machine-checked" | "instruction-layer"
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {
            "constraint": self.constraint,
            "enforcement": self.enforcement,
            "rationale": self.rationale,
        }


@dataclass
class ConstraintResult:
    """Result of project-level constraint checking."""

    violations: list[ConstraintViolation] = field(default_factory=list)
    files_to_reread: list[str] = field(default_factory=list)
    current_phase: str = ""
    active_planning_gate: str = ""
    machine_checked_constraints: list[ConstraintScope] = field(default_factory=list)
    instruction_layer_constraints: list[ConstraintScope] = field(default_factory=list)
    active_overrides: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return any(v.severity == "block" for v in self.violations)

    @property
    def runtime_enforcement_summary(self) -> str:
        machine_checked = ", ".join(
            scope.constraint for scope in self.machine_checked_constraints
        ) or "none"
        instruction_layer = ", ".join(
            scope.constraint for scope in self.instruction_layer_constraints
        ) or "none"
        return (
            f"Runtime currently machine-checks {machine_checked}. "
            f"{instruction_layer} remain instruction-layer constraints."
        )

    def to_dict(self) -> dict:
        blocking = [v.constraint for v in self.violations if v.severity == "block"]
        result: dict[str, Any] = {
            "command_status": "ok",
            "governance_status": "blocked" if blocking else "passed",
            "blocking_constraints": blocking,
            "violations": [
                {"constraint": v.constraint, "message": v.message, "severity": v.severity}
                for v in self.violations
            ],
            "has_blocking": self.has_violations,
            "files_to_reread": self.files_to_reread,
            "current_phase": self.current_phase,
            "active_planning_gate": self.active_planning_gate,
            "machine_checked_constraints": [
                scope.to_dict() for scope in self.machine_checked_constraints
            ],
            "instruction_layer_constraints": [
                scope.to_dict() for scope in self.instruction_layer_constraints
            ],
            "runtime_enforcement_summary": self.runtime_enforcement_summary,
        }
        if self.active_overrides:
            result["active_overrides"] = self.active_overrides
        return result


# ── Pack discovery (delegated to pack.pack_discovery) ─────────────────────

from ..pack.pack_discovery import (  # noqa: E402
    MANIFEST_NAMES as _MANIFEST_NAMES,
    PACK_JSON_SUFFIX as _PACK_JSON_SUFFIX,
    CONFIG_FILE as _CONFIG_FILE,
    USER_DIR_ENV as _USER_DIR_ENV,
    DEFAULT_USER_DIR_NAME as _DEFAULT_USER_DIR_NAME,
    user_global_base_dir as _user_global_base_dir,
    user_global_packs_dir as _user_global_packs_dir,
    discover_packs as _discover_packs,
    read_pack_name as _read_pack_name,
    extract_pack_names as _extract_pack_names,
    discover_installed_packs as _discover_installed_packs,
    resolve_pack_dirs as _resolve_pack_dirs,
)


# ── Constraint checking ──────────────────────────────────────────────────


def _extract_gate_status(head: str) -> str:
    """Extract Status value from a planning gate document header.

    Looks for ``- Status: **APPROVED**`` and returns lowercased status.
    Returns empty string if not found.
    """
    import re

    for line in head.splitlines():
        m = re.match(
            r"^-\s*Status:\s*\*{0,2}(\w[\w\s-]*\w?)\*{0,2}",
            line,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip().lower()
    return ""


_KEY_STATE_FILES = [
    "design_docs/Project Master Checklist.md",
    "design_docs/Global Phase Map and Current Position.md",
    ".codex/handoffs/CURRENT.md",
    ".codex/checkpoints/latest.md",
]

_EMPTY_PLANNING_GATE_MARKERS = frozenset({
    "", "(none)", "—", "-", "none", "n/a",
    "无活跃 gate", "无活跃gate", "无", "无活跃",
})

_MACHINE_CHECKED_CONSTRAINTS = (
    ConstraintScope(
        constraint="C4",
        enforcement="machine-checked",
        rationale="Workspace state can be inspected to confirm whether context recovery files exist and should be re-read.",
    ),
    ConstraintScope(
        constraint="C5",
        enforcement="machine-checked",
        rationale="Workspace state can be inspected to confirm whether a planning-gate document exists before larger implementation work.",
    ),
)

_INSTRUCTION_LAYER_CONSTRAINTS = (
    ConstraintScope(
        constraint="C1",
        enforcement="instruction-layer",
        rationale="Conversation-ending behavior depends on the agent's reply strategy, not on workspace state alone.",
    ),
    ConstraintScope(
        constraint="C2",
        enforcement="instruction-layer",
        rationale="Direction-document citation quality requires semantic review of the produced analysis, not a simple file-state check.",
    ),
    ConstraintScope(
        constraint="C3",
        enforcement="instruction-layer",
        rationale="Runtime can suggest next-step progression after writeback, but does not fully block or audit conversational follow-through.",
    ),
    ConstraintScope(
        constraint="C6",
        enforcement="instruction-layer",
        rationale="Scope-creep detection requires comparing newly discovered work against the active slice intent and is not fully derivable from current file state.",
    ),
    ConstraintScope(
        constraint="C7",
        enforcement="instruction-layer",
        rationale="Important-design-node detection depends on design semantics and explicit user review state, not just repository structure.",
    ),
    ConstraintScope(
        constraint="C8",
        enforcement="instruction-layer",
        rationale="Subagent ownership and shared-document boundaries depend on task-contract semantics and delegation behavior outside this runtime check.",
    ),
)


def _check_constraints(project_root: Path) -> ConstraintResult:
    """Report project-level constraint status and runtime coverage.

    Currently machine-checks:
    - C4: Key state files existence → files_to_reread
    - C5: Active planning-gate existence

    Reports as instruction-layer only:
    - C1, C2, C3, C6, C7, C8

    Also reads checkpoint state to expose current phase and active planning gate.
    Loads active temporary overrides and includes them in the result.
    """
    from .temporary_override import get_active_overrides

    result = ConstraintResult(
        machine_checked_constraints=list(_MACHINE_CHECKED_CONSTRAINTS),
        instruction_layer_constraints=list(_INSTRUCTION_LAYER_CONSTRAINTS),
    )

    # Load active temporary overrides
    active_overrides_list = []
    try:
        active_overrides_list = get_active_overrides(project_root)
        if active_overrides_list:
            result.active_overrides = [o.to_dict() for o in active_overrides_list]
    except Exception:
        pass  # override loading failure must not block constraint checking

    overridden_constraints = {
        o.constraint for o in active_overrides_list
        if o.status == "active"
    }

    # Files to reread for context recovery (C4)
    for rel in _KEY_STATE_FILES:
        p = project_root / rel
        if p.exists():
            result.files_to_reread.append(rel)

    # Read checkpoint if available
    checkpoint_path = project_root / ".codex" / "checkpoints" / "latest.md"
    if checkpoint_path.exists():
        try:
            from ..workflow.checkpoint import read_checkpoint

            cp = read_checkpoint(checkpoint_path)
            if cp.get("phase"):
                result.current_phase = cp["phase"]
            if cp.get("planning_gate"):
                result.active_planning_gate = cp["planning_gate"]
        except Exception:
            # Fallback: simple line scanning
            text = checkpoint_path.read_text(encoding="utf-8")
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if line.strip() == "## Current Phase" and i + 1 < len(lines):
                    result.current_phase = lines[i + 1].strip()
                elif line.strip() == "## Active Planning Gate" and i + 1 < len(lines):
                    val = lines[i + 1].strip()
                    if val not in _EMPTY_PLANNING_GATE_MARKERS:
                        result.active_planning_gate = val

    if result.active_planning_gate in _EMPTY_PLANNING_GATE_MARKERS:
        result.active_planning_gate = ""

    # C5: Check for active planning-gate
    planning_dir = project_root / "design_docs" / "stages" / "planning-gate"
    has_planning_gate = False
    if planning_dir.is_dir():
        for f in planning_dir.iterdir():
            if f.suffix == ".md" and f.name.lower() != "readme.md" and f.stat().st_size > 0:
                has_planning_gate = True
                # If no active_planning_gate from checkpoint, try to find
                # an APPROVED or DRAFT gate from the directory.
                if not result.active_planning_gate:
                    try:
                        head = f.read_text(encoding="utf-8")[:500]
                        status = _extract_gate_status(head)
                        if status in ("approved", "draft"):
                            result.active_planning_gate = f.relative_to(
                                project_root
                            ).as_posix()
                    except OSError:
                        pass
    if not has_planning_gate:
        # Downgrade C5 to "warn" when project is in initial state (no
        # checkpoint and no current_phase) — at this stage there is no
        # work context yet, so blocking is premature.
        checkpoint_exists = (project_root / ".codex" / "checkpoints" / "latest.md").exists()
        is_initial_state = not checkpoint_exists and not result.current_phase
        c5_severity = "warn" if is_initial_state else "block"
        c5_message = (
            "No planning-gate document found. "
            "Create one before starting implementation."
            if is_initial_state
            else "No planning-gate document found. "
            "Create one before large-scale implementation."
        )
        result.violations.append(ConstraintViolation(
            constraint="C5",
            message=c5_message,
            severity=c5_severity,
        ))

    return result


# ── Pipeline ─────────────────────────────────────────────────────────────


class Pipeline:
    """Stateless governance pipeline: PDP → PEP in one call.

    Does NOT maintain cross-call state. Each ``process()`` invocation
    is independent. The MCP layer is responsible for session state.
    """

    def __init__(
        self,
        pack_dirs: list[str | Path],
        project_root: str | Path,
        *,
        dry_run: bool = True,
        audit: bool = True,
        worker: WorkerBackend | None = None,
        contract_factory: ContractFactory | None = None,
        report_validator: ReportValidator | None = None,
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._dry_run = dry_run
        self._audit = audit
        self._worker = worker
        self._contract_factory = contract_factory
        self._report_validator = report_validator
        self._init_errors: list[ErrorInfo] = []
        self._user_config: Any = None  # set by from_project()

        # Load packs
        self._pack_context, self._rule_config, self._registrar, self._builder = (
            self._load_packs(pack_dirs)
        )

        # Validate depends_on
        self._dependency_status = manifest_loader.check_dependencies(
            self._pack_context.manifests,
        )

        # Validate overrides
        self._override_status = manifest_loader.check_overrides(
            self._pack_context.manifests,
        )

        # Validate consumes
        self._consumes_status = manifest_loader.check_consumes(
            self._pack_context.manifests,
        )

    @classmethod
    def from_project(
        cls,
        project_root: str | Path,
        *,
        dry_run: bool = True,
        audit: bool = True,
        worker: WorkerBackend | None = None,
        contract_factory: ContractFactory | None = None,
        report_validator: ReportValidator | None = None,
        include_site_packages: bool = True,
        include_user_global: bool = True,
    ) -> Pipeline:
        """Auto-discover packs from project root and create a Pipeline."""
        from ..pack.user_config import _EMPTY as _EMPTY_CONFIG, load_user_config

        root = Path(project_root).resolve()

        # Load user-global config
        user_config_obj = load_user_config(
            _user_global_base_dir() if include_user_global else None
        )

        discovered = _discover_packs(
            root,
            include_site_packages=include_site_packages,
            include_user_global=include_user_global,
            extra_pack_dirs=user_config_obj.extra_pack_dirs,
        )
        pack_dirs = [str(base_dir) for _, base_dir in discovered]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_dirs: list[str] = []
        for d in pack_dirs:
            if d not in seen:
                seen.add(d)
                unique_dirs.append(d)
        pipe = cls(
            pack_dirs=unique_dirs,
            project_root=root,
            dry_run=dry_run,
            audit=audit,
            worker=worker,
            contract_factory=contract_factory,
            report_validator=report_validator,
        )
        if user_config_obj is not _EMPTY_CONFIG:
            pipe._user_config = user_config_obj
        return pipe

    def _load_packs(
        self, pack_dirs: list[str | Path]
    ) -> tuple[PackContext, RuleConfig, PackRegistrar, ContextBuilder]:
        """Load and merge all packs from the given directories."""
        builder = ContextBuilder()
        registrar = PackRegistrar()
        manifest_dir_pairs: list[tuple[Any, Path]] = []
        for d in pack_dirs:
            dir_path = Path(d)
            if not dir_path.is_absolute():
                dir_path = self._project_root / dir_path

            # Find manifest in directory
            manifest_path = None
            for name in _MANIFEST_NAMES:
                candidate = dir_path / name
                if candidate.exists():
                    manifest_path = candidate
                    break
            if manifest_path is None:
                # Check *.pack.json
                for f in sorted(dir_path.iterdir()) if dir_path.is_dir() else []:
                    if f.name.endswith(_PACK_JSON_SUFFIX):
                        manifest_path = f
                        break
            if manifest_path is None:
                continue

            try:
                manifest = manifest_loader.load(manifest_path)
            except Exception as exc:
                err = ErrorInfo(
                    category="manifest_invalid",
                    message=f"Skipping pack at {manifest_path}: {exc}",
                    source="pack_loader",
                    suggestion="Check the pack manifest JSON for syntax or missing required fields.",
                    detail=str(exc),
                )
                _log.warning(err.message)
                self._init_errors.append(err)
                continue
            builder.add_pack(manifest, dir_path)
            manifest_dir_pairs.append((manifest, dir_path))

        # Pack integrity check (non-blocking — logs warnings)
        lock = load_lock(self._project_root)
        if lock.entries:
            for manifest, dir_path in manifest_dir_pairs:
                result = _verify_pack_integrity(manifest.name, dir_path, lock)
                if result.status == "mismatch":
                    err = ErrorInfo(
                        category="integrity_warning",
                        message=(
                            f"Pack '{result.name}' content changed since lock was recorded"
                        ),
                        source="pack_integrity",
                        suggestion="Run pack lock update to accept changes, or restore the original pack content.",
                        detail=f"expected={result.expected_hash} actual={result.actual_hash}",
                    )
                    _log.warning(err.message)
                    self._init_errors.append(err)
                elif result.status == "missing_pack":
                    err = ErrorInfo(
                        category="integrity_warning",
                        message=f"Pack '{result.name}' is locked but directory is missing",
                        source="pack_integrity",
                        detail=result.detail,
                    )
                    _log.warning(err.message)
                    self._init_errors.append(err)

        context = builder.build(level=LoadLevel.MANIFEST)
        rule_config = resolve_rules(context)

        # Register extensions (validators, triggers)
        for manifest, dir_path in manifest_dir_pairs:
            registrar.register(manifest, dir_path)

        return context, rule_config, registrar, builder

    def process(self, input_text: str) -> PipelineResult:
        """Run full PDP → PEP governance chain.

        Does NOT auto-check constraints. Call ``check_constraints()``
        separately if needed (MCP layer responsibility).
        """
        # Setup audit
        audit_logger: AuditLogger | None = None
        memory_backend: MemoryAuditBackend | None = None
        if self._audit:
            memory_backend = MemoryAuditBackend()
            audit_logger = AuditLogger(memory_backend)

        # PDP: build decision envelope
        envelope = build_envelope(
            input_text,
            rule_config=self._rule_config,
            audit_logger=audit_logger,
        )

        # PEP: execute
        writeback_engine = WritebackEngine(base_dir=self._project_root)
        executor = Executor(
            dry_run=self._dry_run,
            worker=self._worker,
            contract_factory=self._contract_factory,
            report_validator=self._report_validator,
            handoff_dir=self._project_root / ".codex" / "handoffs",
            writeback_engine=writeback_engine if not self._dry_run else None,
            audit_logger=audit_logger,
            validator_registry=self._registrar.registry,
        )
        execution = executor.execute(envelope)

        # Collect audit events
        audit_events: list[dict] = []
        if memory_backend:
            audit_events = [e.to_dict() for e in memory_backend.all_events]

        # Pack info
        pack_info = self.info()

        # Aggregate decision log entry
        dl_entry = build_decision_log_entry(
            envelope=envelope,
            execution=execution,
            audit_events=audit_events,
            pack_info=pack_info,
        )
        store = DecisionLogStore(self._project_root / ".codex" / "decision-logs")
        store.append(dl_entry)

        return PipelineResult(
            envelope=envelope,
            execution=execution,
            audit_events=audit_events,
            pack_info=pack_info,
            decision_log_entry=dl_entry.to_dict(),
        )

    def check_constraints(self) -> ConstraintResult:
        """Check project-level constraints. Independent of process()."""
        return _check_constraints(self._project_root)

    def process_scoped(self, input_text: str, scope_path: str) -> PipelineResult:
        """Run PDP → PEP governance chain with scope-aware pack selection.

        Uses *scope_path* to resolve which pack tree branch applies,
        building a scoped RuleConfig from only the matching pack chain.
        Falls back to the global (unscoped) behaviour if no pack has
        matching ``scope_paths``.
        """
        scoped_context = self._builder.build_scoped(scope_path, level=LoadLevel.MANIFEST)
        scoped_rule_config = resolve_rules(scoped_context)

        # Setup audit
        audit_logger: AuditLogger | None = None
        memory_backend: MemoryAuditBackend | None = None
        if self._audit:
            memory_backend = MemoryAuditBackend()
            audit_logger = AuditLogger(memory_backend)

        # PDP: build decision envelope with scoped rules
        envelope = build_envelope(
            input_text,
            rule_config=scoped_rule_config,
            audit_logger=audit_logger,
        )

        # PEP: execute
        writeback_engine = WritebackEngine(base_dir=self._project_root)
        executor = Executor(
            dry_run=self._dry_run,
            worker=self._worker,
            contract_factory=self._contract_factory,
            report_validator=self._report_validator,
            handoff_dir=self._project_root / ".codex" / "handoffs",
            writeback_engine=writeback_engine if not self._dry_run else None,
            audit_logger=audit_logger,
            validator_registry=self._registrar.registry,
        )
        execution = executor.execute(envelope)

        # Collect audit events
        audit_events: list[dict] = []
        if memory_backend:
            audit_events = [e.to_dict() for e in memory_backend.all_events]

        # Pack info (scoped)
        pack_info = self.info(scope_path=scope_path)

        # Aggregate decision log entry
        dl_entry = build_decision_log_entry(
            envelope=envelope,
            execution=execution,
            audit_events=audit_events,
            pack_info=pack_info,
            scope_path=scope_path,
        )
        store = DecisionLogStore(self._project_root / ".codex" / "decision-logs")
        store.append(dl_entry)

        return PipelineResult(
            envelope=envelope,
            execution=execution,
            audit_events=audit_events,
            pack_info=pack_info,
            decision_log_entry=dl_entry.to_dict(),
        )

    def info(self, *, scope_path: str = "", level: LoadLevel = LoadLevel.MANIFEST) -> dict:
        """Return info about loaded packs and merged configuration.

        When *scope_path* is given, the ``packs`` and ``merged_*`` sections
        reflect only the resolved pack chain for that scope.

        *level* controls the detail depth:
        - ``METADATA``: only basic pack identity (name/kind/provides/description)
        - ``MANIFEST``: full capability sets + rules (default)
        - ``FULL``: same as MANIFEST plus ``always_on_content`` summary
        """
        # Determine effective context
        if scope_path:
            effective_context = self._builder.build_scoped(scope_path, level=level)
        else:
            if level == LoadLevel.FULL:
                effective_context = self.pack_context  # triggers upgrade
            elif level <= self._pack_context.load_level:
                effective_context = self._pack_context
            else:
                effective_context = self._builder.build(level=level)

        manifests_info = []
        for m in effective_context.manifests:
            entry: dict = {
                "name": m.name,
                "version": m.version,
                "kind": m.kind,
                "description": m.description,
                "provides": m.provides,
            }
            if level >= LoadLevel.MANIFEST:
                entry.update({
                    "scope": m.scope,
                    "parent": m.parent,
                    "scope_paths": m.scope_paths,
                })
            manifests_info.append(entry)

        result: dict = {
            "packs": manifests_info,
            "load_level": level.name,
            "merged_provides": effective_context.merged_provides,
        }

        if level >= LoadLevel.MANIFEST:
            result["merged_intents"] = effective_context.merged_intents
            result["merged_gates"] = effective_context.merged_gates
            result["merged_document_types"] = effective_context.merged_document_types

            # Pack tree topology
            tree = self._builder.pack_tree
            tree_info: dict = {
                "roots": [m.name for m in tree.roots()],
                "depth": {name: tree.depth(name) for name in tree.all_names()},
            }
            if scope_path:
                chain = tree.resolve_scope(scope_path)
                tree_info["scope_path"] = scope_path
                tree_info["resolved_chain"] = [m.name for m in chain] if chain else []
            result["pack_tree"] = tree_info

            result.update(self._registrar.summary())
            if self._init_errors:
                result["init_warnings"] = [e.message for e in self._init_errors]
                result["init_errors"] = [e.to_dict() for e in self._init_errors]
            result["dependency_status"] = self._dependency_status
            result["consumes_status"] = self._consumes_status
            result["override_declarations"] = effective_context.merged_overrides
            result["override_warnings"] = self._override_status.get("warnings", [])
            if effective_context.merge_conflicts:
                result["merge_conflicts"] = effective_context.merge_conflicts

        if level >= LoadLevel.FULL:
            content = effective_context.always_on_content
            result["always_on_content_summary"] = {
                "file_count": len(content),
                "files": list(content.keys()),
                "total_chars": sum(len(v) for v in content.values()),
            }

        if self._user_config is not None:
            result["user_config"] = self._user_config.to_dict()

        return result

    @property
    def is_dry_run(self) -> bool:
        """Expose whether the pipeline is running in dry-run mode."""
        return self._dry_run

    @property
    def init_warnings(self) -> list[str]:
        """Warnings emitted during pipeline initialization (e.g. skipped packs).

        Backward-compatible string view — use ``init_errors`` for structured info.
        """
        return [e.message for e in self._init_errors]

    @property
    def init_errors(self) -> list[ErrorInfo]:
        """Structured errors recorded during pipeline initialization."""
        return list(self._init_errors)

    @property
    def pack_context(self) -> PackContext:
        """Expose the merged PackContext, upgrading to FULL on first access."""
        if self._pack_context.load_level < LoadLevel.FULL:
            self._pack_context = self._pack_context.upgrade(
                LoadLevel.FULL, builder=self._builder
            )
        return self._pack_context

    @property
    def rule_config(self) -> RuleConfig:
        """Expose the resolved RuleConfig for inspection."""
        return self._rule_config
