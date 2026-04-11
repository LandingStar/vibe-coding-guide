"""Pipeline orchestrator — unified PDP → PEP governance chain.

Assembles ManifestLoader → ContextBuilder → OverrideResolver → PDP →
PEP into a single ``Pipeline.process(input)`` call.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..audit.audit_logger import AuditLogger, MemoryAuditBackend
from ..pack import manifest_loader
from ..pack.context_builder import ContextBuilder, PackContext
from ..pack.override_resolver import RuleConfig, resolve as resolve_rules
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

    def to_dict(self) -> dict:
        return {
            "envelope": self.envelope,
            "execution": {
                k: v for k, v in self.execution.items() if k != "_rsm"
            },
            "audit_events": self.audit_events,
            "pack_info": self.pack_info,
        }


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
        return {
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


# ── Pack discovery ────────────────────────────────────────────────────────

_MANIFEST_NAMES = ("pack-manifest.json",)
_PACK_JSON_SUFFIX = ".pack.json"
_CONFIG_FILE = ".codex/platform.json"


def _discover_packs(project_root: Path) -> list[tuple[Path, Path]]:
    """Auto-discover pack manifests under project_root.

    Returns list of (manifest_path, base_dir) tuples, ordered by kind
    priority (platform → instance → project-local).

    Discovery rules:
    1. If .codex/platform.json exists and has ``pack_dirs``, use those.
    2. Otherwise scan:
       a. {root}/.codex/packs/*.pack.json
       b. {root}/*/pack-manifest.json (one-level subdirs)
    """
    config_path = project_root / _CONFIG_FILE
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            dirs = config.get("pack_dirs", [])
            if dirs:
                return _resolve_pack_dirs(project_root, dirs)
        except (json.JSONDecodeError, KeyError):
            pass  # Fall through to convention-based discovery

    results: list[tuple[Path, Path]] = []

    # .codex/packs/*.pack.json
    packs_dir = project_root / ".codex" / "packs"
    if packs_dir.is_dir():
        for f in sorted(packs_dir.iterdir()):
            if f.name.endswith(_PACK_JSON_SUFFIX) or f.name in _MANIFEST_NAMES:
                results.append((f, packs_dir))

    # */pack-manifest.json (one-level subdirs)
    if project_root.is_dir():
        for child in sorted(project_root.iterdir()):
            if child.is_dir() and not child.name.startswith("."):
                manifest = child / "pack-manifest.json"
                if manifest.exists():
                    results.append((manifest, child))

    return results


def _resolve_pack_dirs(
    project_root: Path, dirs: list[str]
) -> list[tuple[Path, Path]]:
    """Resolve explicit pack_dirs from config to (manifest, base_dir) pairs."""
    results: list[tuple[Path, Path]] = []
    for d in dirs:
        dir_path = (project_root / d).resolve()
        if not dir_path.is_dir():
            continue
        # Look for manifest in directory
        for name in _MANIFEST_NAMES:
            manifest = dir_path / name
            if manifest.exists():
                results.append((manifest, dir_path))
                break
        else:
            # Check for *.pack.json files
            for f in sorted(dir_path.iterdir()):
                if f.name.endswith(_PACK_JSON_SUFFIX):
                    results.append((f, dir_path))
    return results


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

_EMPTY_PLANNING_GATE_MARKERS = frozenset({"", "(none)", "—", "-"})

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
    """
    result = ConstraintResult(
        machine_checked_constraints=list(_MACHINE_CHECKED_CONSTRAINTS),
        instruction_layer_constraints=list(_INSTRUCTION_LAYER_CONSTRAINTS),
    )

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
        result.violations.append(ConstraintViolation(
            constraint="C5",
            message="No planning-gate document found. Create one before large-scale implementation.",
            severity="block",
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

        # Load packs
        self._pack_context, self._rule_config, self._registrar = self._load_packs(pack_dirs)

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
    ) -> Pipeline:
        """Auto-discover packs from project root and create a Pipeline."""
        root = Path(project_root).resolve()
        discovered = _discover_packs(root)
        pack_dirs = [str(base_dir) for _, base_dir in discovered]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_dirs: list[str] = []
        for d in pack_dirs:
            if d not in seen:
                seen.add(d)
                unique_dirs.append(d)
        return cls(
            pack_dirs=unique_dirs,
            project_root=root,
            dry_run=dry_run,
            audit=audit,
            worker=worker,
            contract_factory=contract_factory,
            report_validator=report_validator,
        )

    def _load_packs(
        self, pack_dirs: list[str | Path]
    ) -> tuple[PackContext, RuleConfig, PackRegistrar]:
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

        context = builder.build()
        rule_config = resolve_rules(context)

        # Register extensions (validators, triggers)
        for manifest, dir_path in manifest_dir_pairs:
            registrar.register(manifest, dir_path)

        return context, rule_config, registrar

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
        )
        execution = executor.execute(envelope)

        # Collect audit events
        audit_events: list[dict] = []
        if memory_backend:
            audit_events = [e.to_dict() for e in memory_backend.all_events]

        # Pack info
        pack_info = self.info()

        return PipelineResult(
            envelope=envelope,
            execution=execution,
            audit_events=audit_events,
            pack_info=pack_info,
        )

    def check_constraints(self) -> ConstraintResult:
        """Check project-level constraints. Independent of process()."""
        return _check_constraints(self._project_root)

    def info(self) -> dict:
        """Return info about loaded packs and merged configuration."""
        manifests_info = []
        for m in self._pack_context.manifests:
            manifests_info.append({
                "name": m.name,
                "version": m.version,
                "kind": m.kind,
                "scope": m.scope,
                "provides": m.provides,
            })
        result = {
            "packs": manifests_info,
            "merged_intents": self._pack_context.merged_intents,
            "merged_gates": self._pack_context.merged_gates,
            "merged_document_types": self._pack_context.merged_document_types,
            "merged_provides": self._pack_context.merged_provides,
        }
        result.update(self._registrar.summary())
        if self._init_errors:
            result["init_warnings"] = [e.message for e in self._init_errors]
            result["init_errors"] = [e.to_dict() for e in self._init_errors]
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
        """Expose the merged PackContext for inspection."""
        return self._pack_context

    @property
    def rule_config(self) -> RuleConfig:
        """Expose the resolved RuleConfig for inspection."""
        return self._rule_config
