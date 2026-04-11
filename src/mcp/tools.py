"""MCP tool definitions for doc-based-coding governance platform.

Exposes Pipeline capabilities as MCP tools that any compatible MCP client
can call for structural constraint enforcement.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..pack.manifest_loader import PackManifest
from ..workflow.external_skill_interaction import (
    build_external_skill_interaction_contract,
)
from ..workflow.safe_stop_writeback import build_safe_stop_writeback_bundle
from ..workflow.pipeline import (
    ConstraintResult,
    ErrorInfo,
    Pipeline,
    PipelineResult,
)

_log = logging.getLogger(__name__)


class GovernanceTools:
    """Workspace-aware wrapper around Pipeline for MCP tool invocations.

    Rebuilds Pipeline state on public tool calls so long-lived MCP
    sessions keep seeing current pack manifests and derived context.
    """

    def __init__(self, project_root: str | Path, *, dry_run: bool = True) -> None:
        self._project_root = Path(project_root).resolve()
        self._dry_run = dry_run
        self._pipeline: Pipeline | None = None
        self._init_error: ErrorInfo | None = None
        self._refresh_pipeline()

    def _set_init_error(self, exc: Exception) -> None:
        self._pipeline = None
        self._init_error = ErrorInfo(
            category="init_failed",
            message=f"Pipeline failed to initialize: {exc}",
            source="mcp",
            suggestion="Check pack manifests and project structure, then retry or restart the MCP host if source code changed.",
            detail=str(exc),
        )
        _log.error("Pipeline initialization failed: %s", exc)

    def _refresh_pipeline(self) -> None:
        """Reload Pipeline from current workspace state."""
        try:
            self._pipeline = Pipeline.from_project(
                self._project_root, dry_run=self._dry_run, audit=True
            )
            self._init_error = None
        except Exception as exc:
            self._set_init_error(exc)

    def _require_pipeline(self, *, refresh: bool = True) -> dict | None:
        """Return an error dict if pipeline is unavailable, else None."""
        if refresh:
            self._refresh_pipeline()
        if self._pipeline is not None:
            return None
        if self._init_error is not None:
            return self._init_error.to_dict()
        return ErrorInfo(
            category="init_failed",
            message="Pipeline is not available.",
            source="mcp",
        ).to_dict()

    def _interaction_contract(self) -> dict[str, Any]:
        """Return the structured conversation progression contract."""
        default_contract: dict[str, Any] = {
            "termination_requires_user_permission": True,
            "final_reply_requires_forward_question": True,
            "question_must_include_analysis": True,
            "structured_confirmation_tool": "askQuestions",
            "structured_confirmation_required_for": [
                "choice",
                "approval",
                "direction confirmation",
                "phase progression",
            ],
            "phase_completion_requires_next_direction": True,
            "allowed_non_question_endings": [
                "user explicitly allows ending",
                "user explicitly allows pausing",
                "user explicitly requests no follow-up question this turn",
            ],
        }

        if self._pipeline is None:
            return default_contract

        merged_rules = getattr(self._pipeline.pack_context, "merged_rules", {})
        contract = merged_rules.get("conversation_progression")
        if isinstance(contract, dict) and contract:
            return dict(contract)
        return default_contract

    @staticmethod
    def _question_instruction() -> str:
        return (
            "Provide your analysis or recommendation first, then continue with a forward question. "
            "Use askQuestions when the user needs a structured choice, approval, direction confirmation, or phase progression decision."
        )

    def _external_skill_interaction_contract(self) -> dict[str, Any]:
        merged_rules: dict[str, Any] | None = None
        if self._pipeline is not None:
            merged_rules = getattr(self._pipeline.pack_context, "merged_rules", {})
        return build_external_skill_interaction_contract(
            self._project_root,
            merged_rules,
        )

    def governance_decide(self, input_text: str) -> dict:
        """Run PDP → PEP governance chain on input text.

        Returns structured result with envelope, execution result,
        and constraint check.

        MCP tool behavior:
        - Always returns a ``decision`` field: "ALLOW" or "BLOCK"
        - On BLOCK: includes ``constraint_violated`` and ``required_action``
        - On ALLOW: includes full envelope and execution result
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        # Pre-check constraints
        constraints = self._pipeline.check_constraints()
        if constraints.has_violations:
            blocking = [
                v for v in constraints.violations if v.severity == "block"
            ]
            return {
                "decision": "BLOCK",
                "reason": "; ".join(v.message for v in blocking),
                "constraint_violated": [v.constraint for v in blocking],
                "required_action": "Resolve blocking constraints before proceeding.",
                "constraints": constraints.to_dict(),
            }

        # Run governance chain
        result = self._pipeline.process(input_text)
        pack_info = dict(result.pack_info)
        pack_info["external_skill_interaction_contract"] = (
            self._external_skill_interaction_contract()
        )
        return {
            "decision": "ALLOW",
            "envelope": result.envelope,
            "execution": {
                k: v for k, v in result.execution.items() if k != "_rsm"
            },
            "intent": result.envelope.get("intent_result", {}).get("intent", "unknown"),
            "gate": result.envelope.get("gate_decision", {}).get("gate_level", "review"),
            "audit_event_count": len(result.audit_events),
            "pack_info": pack_info,
        }

    def check_constraints(self) -> dict:
        """Report project-level constraints and runtime enforcement coverage.

        Returns current constraint status, files to re-read for
        context recovery, project phase info, and which constraints are
        machine-checked versus still instruction-layer.
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        result = self._pipeline.check_constraints()
        return result.to_dict()

    def get_next_action(self) -> dict:
        """Recommend the next action based on project state.

        Reads checkpoint and planning-gate documents to determine
        what should happen next. Used by MCP clients after context
        compression or restart to recover state.
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        constraints = self._pipeline.check_constraints()

        # Determine next action based on state
        action: dict[str, Any] = {
            "files_to_reread": constraints.files_to_reread,
            "current_phase": constraints.current_phase,
            "active_planning_gate": constraints.active_planning_gate,
            "runtime_enforcement_summary": constraints.runtime_enforcement_summary,
        }

        if constraints.has_violations:
            blocking = [
                v for v in constraints.violations if v.severity == "block"
            ]
            action["instruction"] = (
                f"BLOCKED: {blocking[0].message} "
                "Resolve this before proceeding."
            )
            action["ask_user"] = False
        elif constraints.active_planning_gate:
            action["instruction"] = (
                f"Continue working on the active planning gate: "
                f"{constraints.active_planning_gate}. "
                "Read the planning document and proceed with the current slice."
            )
            action["ask_user"] = False
        else:
            action["instruction"] = (
                "No active planning gate found. "
                "Read the Project Master Checklist and Global Phase Map to "
                "determine the next direction. Prepare a direction analysis "
                "document with candidates sourced from: "
                "(1) Checklist todos/risks, "
                "(2) docs/ unimplemented capabilities, "
                "(3) review/research-compass.md insights, "
                "(4) issues discovered during recent phases."
            )
            action["document_refs"] = [
                "design_docs/Project Master Checklist.md",
                "design_docs/Global Phase Map and Current Position.md",
                "review/research-compass.md",
            ]
            action["ask_user"] = True
            action["interaction_contract"] = self._interaction_contract()
            action["question_instruction"] = self._question_instruction()

        return action

    def writeback_notify(self, phase_description: str) -> dict:
        """Notify that a phase/slice writeback has been completed.

        Returns recommendation for next steps. Used to drive
        automatic phase progression (C3).

        Args:
            phase_description: Description of what was just completed.
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        constraints = self._pipeline.check_constraints()

        # Scan for planning-gate documents that might indicate next steps
        gate_dir = self._project_root / "design_docs" / "stages" / "planning-gate"
        pending_gates: list[str] = []
        if gate_dir.is_dir():
            for f in sorted(gate_dir.iterdir()):
                if f.suffix == ".md" and f.name.lower() != "readme.md":
                    try:
                        head = f.read_text(encoding="utf-8")[:500]
                        # Parse Status line: look for "Status: **XXXX**"
                        status = _extract_gate_status(head)
                        if status in ("draft", "approved", "pending"):
                            pending_gates.append(f.name)
                    except OSError:
                        pass

        if not self._pipeline.is_dry_run:
            from ..workflow.checkpoint import sync_checkpoint_phase

            sync_checkpoint_phase(
                self._project_root,
                phase=phase_description,
                planning_gate="",
            )

        bundle = build_safe_stop_writeback_bundle(self._project_root)

        return {
            "phase_completed": phase_description,
            "auto_next": {
                "action": "prepare_direction_analysis" if not pending_gates else "execute_pending_gate",
                "pending_gates": pending_gates,
                "instruction": (
                    f"Phase '{phase_description}' completed. "
                    + (
                        f"Found {len(pending_gates)} pending planning gate(s): "
                        f"{', '.join(pending_gates)}. "
                        "Continue with the next pending gate."
                        if pending_gates
                        else
                        "No pending gates found. "
                        "Write back status to Checklist and Phase Map, then "
                        "prepare a direction analysis document for the next phase. "
                        "Use askQuestions to confirm direction with the user."
                    )
                ),
                "files_to_update": [
                    *bundle["files_to_update"],
                ],
            },
            "ask_user": True,
            "interaction_contract": self._interaction_contract(),
            "question_instruction": self._question_instruction(),
            "safe_stop_writeback_bundle": bundle,
        }

    def get_info(self) -> dict:
        """Return loaded pack info."""
        err = self._require_pipeline()
        if err is not None:
            return err
        result = dict(self._pipeline.info())
        result["external_skill_interaction_contract"] = (
            self._external_skill_interaction_contract()
        )
        return result

    # ── Prompts ────────────────────────────────────────────────────────

    def list_prompts(self) -> list[dict[str, str]] | dict:
        """Return prompt metadata from loaded packs.

        Each entry has ``name`` (slug) and ``description``.
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        results: list[dict[str, str]] = []
        ctx = self._pipeline.pack_context
        for manifest in ctx.manifests:
            base_dir = self._resolve_pack_base(manifest)
            for rel in getattr(manifest, "prompts", []) or []:
                path = base_dir / rel if base_dir else None
                name = Path(rel).stem
                # Read first non-heading line as description
                desc = f"Pack prompt from {manifest.name}: {rel}"
                if path and path.exists():
                    try:
                        lines = path.read_text(encoding="utf-8").splitlines()
                        for ln in lines:
                            stripped = ln.strip()
                            if stripped and not stripped.startswith("#"):
                                desc = stripped[:120]
                                break
                    except OSError:
                        pass
                results.append({"name": name, "description": desc})
        return results

    def get_prompt(self, name: str) -> str | None | dict:
        """Read a prompt file by slug name.

        Returns the file content as a string, or *None* if not found.
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        ctx = self._pipeline.pack_context
        for manifest in ctx.manifests:
            base_dir = self._resolve_pack_base(manifest)
            for rel in getattr(manifest, "prompts", []) or []:
                if Path(rel).stem == name:
                    path = base_dir / rel if base_dir else None
                    if path and path.exists():
                        try:
                            return path.read_text(encoding="utf-8")
                        except OSError:
                            return None
        return None

    # ── Resources ──────────────────────────────────────────────────────

    def list_resources(self) -> list[dict[str, str]] | dict:
        """Return resource metadata from loaded packs.

        Resources include *always_on* files (already in memory) and
        *on_demand* files (read on access).
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        results: list[dict[str, str]] = []
        ctx = self._pipeline.pack_context

        # always_on — already loaded into memory
        for filename in sorted(ctx.always_on_content.keys()):
            uri = f"pack://always-on/{filename}"
            results.append({
                "uri": uri,
                "name": filename,
                "description": f"Always-on context file (pre-loaded)",
                "mimeType": "text/markdown",
            })

        # on_demand — declared but loaded lazily
        for manifest in ctx.manifests:
            for rel in getattr(manifest, "on_demand", []) or []:
                uri = f"pack://{manifest.name}/on-demand/{rel}"
                results.append({
                    "uri": uri,
                    "name": rel,
                    "description": f"On-demand resource from {manifest.name}",
                    "mimeType": self._guess_mime(rel),
                })

        return results

    def read_resource(self, uri: str) -> str | None | dict:
        """Read a resource by its pack:// URI.

        always_on resources come from memory; on_demand resources are
        lazily loaded via PackContext.load_on_demand().
        """
        err = self._require_pipeline()
        if err is not None:
            return err

        ctx = self._pipeline.pack_context

        # always_on — pack://always-on/{filename}
        if uri.startswith("pack://always-on/"):
            filename = uri[len("pack://always-on/"):]
            return ctx.always_on_content.get(filename)

        # on_demand — pack://{pack_name}/on-demand/{rel_path}
        for manifest in ctx.manifests:
            prefix = f"pack://{manifest.name}/on-demand/"
            if uri.startswith(prefix):
                rel = uri[len(prefix):]
                return ctx.load_on_demand(rel)
        return None

    # ── Helpers ────────────────────────────────────────────────────────

    def _resolve_pack_base(self, manifest: PackManifest) -> Path | None:
        """Find the base directory corresponding to a loaded manifest."""
        ctx = self._pipeline.pack_context
        # ContextBuilder stores (manifest, base_dir) during add_pack;
        # we need to find the base_dir from the pack_dirs used by Pipeline.
        # Convention: look in project root and common locations.
        for candidate in [
            self._project_root / manifest.name,
            self._project_root / ".codex" / "packs",
        ]:
            if candidate.is_dir():
                return candidate
        return self._project_root

    @staticmethod
    def _guess_mime(rel: str) -> str:
        ext = Path(rel).suffix.lower()
        return {
            ".md": "text/markdown",
            ".json": "application/json",
            ".py": "text/x-python",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".txt": "text/plain",
        }.get(ext, "text/plain")


def _extract_gate_status(head: str) -> str:
    """Extract Status value from a planning gate document header.

    Looks for a line like ``- Status: **APPROVED**`` and returns
    the lowercased status string (e.g. "approved", "closed", "draft").
    Returns empty string if no status line found.
    """
    import re

    for line in head.splitlines():
        m = re.match(r"^-\s*Status:\s*\*{0,2}(\w[\w\s-]*\w?)\*{0,2}", line, re.IGNORECASE)
        if m:
            return m.group(1).strip().lower()
    return ""
