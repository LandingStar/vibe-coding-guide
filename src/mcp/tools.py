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
from ..workflow.agent_output import FileSink, write_agent_output
from ..workflow.safe_stop_writeback import build_safe_stop_writeback_bundle
from ..workflow.temporary_override import (
    OVERRIDABLE_CONSTRAINTS,
    OverrideError,
    get_active_overrides,
    revoke_override as _revoke_override,
    save_override as _save_override,
)
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

    def __init__(
        self,
        project_root: str | Path,
        *,
        dry_run: bool = True,
        include_site_packages: bool = True,
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._dry_run = dry_run
        self._include_site_packages = include_site_packages
        self._pipeline: Pipeline | None = None
        self._init_error: ErrorInfo | None = None
        self._agent_output_sink = FileSink(self._project_root)
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
                self._project_root,
                dry_run=self._dry_run,
                audit=True,
                include_site_packages=self._include_site_packages,
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

    def write_output(self, content: str, *, title: str = "") -> str:
        """Write agent analysis to a visible surface and return the file path.

        Use this to surface analysis, tables, or summaries that the user
        needs to see. In MCP clients where chat text is invisible (e.g.
        VS Code Copilot Chat), this writes to .codex/agent-output/latest.md.
        """
        return self._agent_output_sink.write(content, title=title)

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

    # ── Hardcoded git remote guard (not overridable) ──────────────
    import re as _re

    _GIT_REMOTE_BLOCKED = ("push",)
    _GIT_REMOTE_RE = _re.compile(
        r"(?:^|[;&|]|\|\||&&|&)\s*"
        r'(?:"[^"]*[\\/])?'
        r"(?:[\w:/\\.-]*[\\/])?"
        r"git(?:\.exe)?\"?\s+"
        r"(?:" + "|".join(_GIT_REMOTE_BLOCKED) + r")"
        r"(?:\s|$|[;&|])",
        _re.IGNORECASE,
    )

    def _check_git_remote_guard(self, input_text: str) -> dict | None:
        """Return a BLOCK dict if input contains a remote git command."""
        # Only check terminal-command inputs
        lower = input_text.lower()
        if not lower.startswith("terminal-command:") and not lower.startswith("terminal:"):
            return None
        # Extract the command part after the prefix
        _, _, cmd = input_text.partition(":")
        cmd = cmd.strip()
        if not cmd:
            return None
        m = self._GIT_REMOTE_RE.search(cmd)
        if m is None:
            return None
        # Identify which subcommand matched
        matched = ""
        for sub in self._GIT_REMOTE_BLOCKED:
            if sub in m.group(0).lower():
                matched = sub
                break
        return {
            "decision": "BLOCK",
            "reason": f"Remote git operation '{matched}' is permanently blocked in this workspace.",
            "constraint_violated": ["C-HARDCODED-GIT-PUSH"],
            "required_action": "git push is disabled to prevent unintended remote modifications. Read-only operations (pull/fetch/clone) are allowed.",
            "hardcoded": True,
        }

    def _external_skill_interaction_contract(self) -> dict[str, Any]:
        merged_rules: dict[str, Any] | None = None
        if self._pipeline is not None:
            merged_rules = getattr(self._pipeline.pack_context, "merged_rules", {})
        return build_external_skill_interaction_contract(
            self._project_root,
            merged_rules,
        )

    def governance_decide(self, input_text: str, scope_path: str = "", action_type: str = "") -> dict:
        """Run PDP → PEP governance chain on input text.

        Returns structured result with envelope, execution result,
        and constraint check.

        When *scope_path* is provided, pack resolution uses only the
        matching branch of the pack tree (hierarchical scope-aware mode).

        When *action_type* is provided, tool-level permission policies
        (from pack rules.tool_permissions) are evaluated first.

        MCP tool behavior:
        - Always returns a ``decision`` field: "ALLOW" or "BLOCK"
        - On BLOCK: includes ``constraint_violated`` and ``required_action``
        - On ALLOW: includes full envelope and execution result
        """
        # ── Hardcoded guard: remote git operations ──
        git_block = self._check_git_remote_guard(input_text)
        if git_block is not None:
            return git_block

        err = self._require_pipeline()
        if err is not None:
            return err

        # ── Tool permission policy check (B-REF-4) ──
        if action_type:
            from ..pdp.tool_permission_resolver import resolve as _resolve_perm
            rule_config = self._pipeline.rule_config
            perm_result = _resolve_perm(action_type, rule_config.tool_permissions)
            if perm_result.permission == "deny":
                return {
                    "decision": "BLOCK",
                    "reason": perm_result.deny_message or f"Action '{action_type}' denied by tool permission policy.",
                    "constraint_violated": ["TOOL_PERMISSION_DENY"],
                    "required_action": "This action type is not permitted in the current pack configuration.",
                    "policy_source": perm_result.policy_source,
                }

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

        # Run governance chain (scoped or global)
        if scope_path:
            result = self._pipeline.process_scoped(input_text, scope_path)
        else:
            result = self._pipeline.process(input_text)
        # Slim pack_info summary (full details via get_pack_info tool)
        full_info = result.pack_info
        pack_info_summary: dict[str, Any] = {
            "packs": [
                {"name": p["name"], "version": p.get("version", ""), "kind": p.get("kind", "")}
                for p in full_info.get("packs", [])
            ],
            "merged_intents": full_info.get("merged_intents", []),
            "merged_gates": full_info.get("merged_gates", []),
        }
        # For scoped calls, include pack_tree resolution chain
        if "pack_tree" in full_info:
            pack_info_summary["pack_tree"] = full_info["pack_tree"]
        response: dict[str, Any] = {
            "decision": "ALLOW",
            "envelope": result.envelope,
            "execution": {
                k: v for k, v in result.execution.items() if k != "_rsm"
            },
            "intent": result.envelope.get("intent_result", {}).get("intent", "unknown"),
            "gate": result.envelope.get("gate_decision", {}).get("gate_level", "review"),
            "audit_event_count": len(result.audit_events),
            "pack_info": pack_info_summary,
            "decision_log_entry": result.decision_log_entry,
        }

        # Annotate with tool permission "ask" if applicable
        if action_type:
            from ..pdp.tool_permission_resolver import resolve as _resolve_perm
            rule_config = self._pipeline.rule_config
            perm_result = _resolve_perm(action_type, rule_config.tool_permissions)
            if perm_result.permission == "ask":
                response["tool_permission"] = {
                    "requires_confirmation": True,
                    "action_type": action_type,
                    "policy_source": perm_result.policy_source,
                }

        return response

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

    def governance_override(self, action: str, **kwargs: Any) -> dict:
        """Register, revoke, or list temporary rule overrides.

        Actions:
          - ``register``: requires ``constraint``, ``reason``, optional ``scope``
          - ``revoke``: requires ``override_id``
          - ``list``: no extra args

        Non-overridable constraints (C4, C5, C8) are rejected.
        """
        if action == "list":
            try:
                active = get_active_overrides(self._project_root)
                return {
                    "overrides": [o.to_dict() for o in active],
                    "overridable_constraints": sorted(OVERRIDABLE_CONSTRAINTS),
                }
            except Exception as exc:
                return {"error": f"Failed to list overrides: {exc}"}

        if action == "register":
            constraint = kwargs.get("constraint", "")
            reason = kwargs.get("reason", "")
            scope = kwargs.get("scope", "session")
            if not constraint or not reason:
                return {"error": "register requires 'constraint' and 'reason'."}
            try:
                override = _save_override(
                    self._project_root,
                    constraint=constraint,
                    reason=reason,
                    scope=scope,
                )
                return {
                    "registered": True,
                    "override": override.to_dict(),
                }
            except OverrideError as exc:
                return {"error": str(exc), "registered": False}

        if action == "revoke":
            override_id = kwargs.get("override_id", "")
            if not override_id:
                return {"error": "revoke requires 'override_id'."}
            found = _revoke_override(self._project_root, override_id)
            return {
                "revoked": found,
                "override_id": override_id,
            }

        return {"error": f"Unknown action: {action!r}. Use 'register', 'revoke', or 'list'."}

    def query_decision_logs(
        self,
        trace_id: str = "",
        decision: str = "",
        intent: str = "",
        has_merge_conflicts: bool | None = None,
        limit: int = 50,
    ) -> dict:
        """Query persisted decision log entries.

        Supports filtering by trace_id, decision (ALLOW/BLOCK), intent,
        and whether merge conflicts were recorded.
        Returns the most recent entries first, up to *limit*.
        """
        from ..audit.decision_log import DecisionLogStore

        store = DecisionLogStore(self._project_root / ".codex" / "decision-logs")
        entries = store.query(
            trace_id=trace_id or None,
            decision=decision or None,
            intent=intent or None,
            has_merge_conflicts=has_merge_conflicts,
            limit=limit,
        )
        filters: dict = {
            k: v for k, v in
            {"trace_id": trace_id, "decision": decision, "intent": intent}.items()
            if v
        }
        if has_merge_conflicts is not None:
            filters["has_merge_conflicts"] = has_merge_conflicts
        return {
            "entries": entries,
            "count": len(entries),
            "filters": filters,
        }

    def workflow_interrupt(self, reason: str, discovered_item: str, current_scope_ref: str = "") -> dict:
        """Signal a workflow interrupt when an out-of-scope item is discovered.

        This primitive implements the project rule:
        "若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope"

        Returns structured guidance directing the agent to write the
        discovered item to a planning-gate document rather than expanding
        scope in-place.
        """
        import uuid
        from datetime import datetime, timezone

        interrupt_id = f"int-{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Generate a suggested filename based on the discovered item
        slug = discovered_item[:60].lower()
        slug = "".join(c if c.isalnum() or c in "-_ " else "" for c in slug)
        slug = slug.strip().replace(" ", "-").replace("_", "-")
        slug = "-".join(part for part in slug.split("-") if part)[:40]
        date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        suggested_filename = f"design_docs/stages/planning-gate/{date_prefix}-{slug}.md"

        # Record to decision log if pipeline available
        decision_log_entry: dict[str, Any] | None = None
        if self._pipeline is not None:
            entry = {
                "interrupt_id": interrupt_id,
                "timestamp": timestamp,
                "type": "workflow_interrupt",
                "reason": reason,
                "discovered_item": discovered_item,
                "current_scope_ref": current_scope_ref or None,
                "suggested_redirect": suggested_filename,
            }
            try:
                from ..workflow.decision_log import record_entry
                record_entry(self._project_root, entry)
                decision_log_entry = entry
            except Exception:
                decision_log_entry = entry

        return {
            "status": "interrupted",
            "interrupt_id": interrupt_id,
            "timestamp": timestamp,
            "guidance": {
                "action": "write_to_planning_gate",
                "instruction": (
                    "You have signaled a scope interrupt. "
                    "Record the discovered item in a new planning-gate document. "
                    "Do NOT expand the current scope. "
                    "Resume current work only after the new planning-gate is addressed."
                ),
                "discovered_item": discovered_item,
                "reason": reason,
                "current_scope_ref": current_scope_ref or None,
                "suggested_filename": suggested_filename,
            },
            "decision_log_entry": decision_log_entry,
        }

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
            action["completion_boundary_reminder"] = (
                "CRITICAL: You are at a completion boundary. "
                "You MUST provide your own analysis of the next direction "
                "and end with a forward question that includes your recommendation. "
                "Do NOT ask the user whether to continue or stop."
            )

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

    def get_info(self, scope_path: str = "", level: str = "manifest") -> dict:
        """Return loaded pack info with optional scope filtering and detail level."""
        err = self._require_pipeline()
        if err is not None:
            return err
        from ..pack.manifest_loader import LoadLevel
        level_map = {"metadata": LoadLevel.METADATA, "manifest": LoadLevel.MANIFEST, "full": LoadLevel.FULL}
        load_level = level_map.get(level.lower(), LoadLevel.MANIFEST)
        result = dict(self._pipeline.info(scope_path=scope_path, level=load_level))
        result["external_skill_interaction_contract"] = (
            self._external_skill_interaction_contract()
        )
        return result

    # ── Dependency Graph Tools ─────────────────────────────────────────

    def impact_analysis(
        self,
        changed_files: list[str] | None = None,
        changed_symbols: list[str] | None = None,
        max_depth: int = 2,
    ) -> dict:
        """Analyze change impact through the dependency graph.

        Uses the baseline graph snapshot to propagate changes and
        identify directly and transitively affected nodes.
        """
        graph_path = self._project_root / "tools" / "dependency_graph" / "baseline_graph.json"
        if not graph_path.exists():
            return {
                "error": "baseline_graph.json not found",
                "suggestion": "Run build_baseline.py to generate the graph snapshot.",
            }
        try:
            from tools.dependency_graph.query import query_impact

            graph_text = graph_path.read_text(encoding="utf-8")
            from tools.dependency_graph.model import DependencyGraph

            graph = DependencyGraph.from_json(graph_text)
            return query_impact(
                graph,
                changed_files=changed_files or [],
                changed_symbols=changed_symbols or [],
                max_depth=max_depth,
            )
        except Exception as exc:
            _log.error("impact_analysis failed: %s", exc)
            return {"error": str(exc)}

    def coupling_check(
        self,
        changed_files: list[str] | None = None,
        changed_symbols: list[str] | None = None,
    ) -> dict:
        """Check coupling annotations against changes.

        Uses coupling_annotations.json to find semantic coupling
        alerts triggered by the given changes.
        """
        coupling_path = (
            self._project_root / "tools" / "dependency_graph" / "coupling_annotations.json"
        )
        if not coupling_path.exists():
            return {"alerts": [], "note": "No coupling_annotations.json found."}
        try:
            from tools.dependency_graph.query import query_coupling

            alerts = query_coupling(
                coupling_path,
                changed_files=changed_files or [],
                changed_symbols=changed_symbols or [],
            )
            return {"alerts": alerts}
        except Exception as exc:
            _log.error("coupling_check failed: %s", exc)
            return {"error": str(exc)}

    def analyze_changes(
        self,
        changed_files: list[str] | None = None,
        changed_symbols: list[str] | None = None,
        max_depth: int = 2,
    ) -> dict:
        """Unified change analysis combining impact propagation and coupling checks.

        Merges the results of ``impact_analysis`` and ``coupling_check``
        into a single response so the caller only needs one tool call.
        """
        impact = self.impact_analysis(
            changed_files=changed_files,
            changed_symbols=changed_symbols,
            max_depth=max_depth,
        )
        coupling = self.coupling_check(
            changed_files=changed_files,
            changed_symbols=changed_symbols,
        )
        return {
            "impact": impact,
            "coupling": coupling,
        }

    # ── Dogfood pipeline ───────────────────────────────────────────────

    def promote_dogfood_evidence(
        self,
        symptoms: list[dict],
        existing_issue_ids: list[str] | None = None,
        date: str = "",
        judgment: str = "",
        next_step_implication: str = "",
        confidence: str = "medium",
        non_goals: list[str] | None = None,
        supersedes: str | None = None,
        auto_writeback: bool = False,
        active_gate_path: str | None = None,
    ) -> dict:
        """Run the full dogfood pipeline: evaluate → build → assemble → dispatch.

        Returns decisions, promoted issues, feedback packet, and consumer payloads.
        If *auto_writeback* is True, also writes consumer payloads to target documents.
        """
        try:
            from ..dogfood import run_full_pipeline

            result = run_full_pipeline(
                symptoms=symptoms,
                existing_issue_ids=existing_issue_ids,
                date=date,
                judgment=judgment,
                next_step_implication=next_step_implication,
                confidence=confidence,
                non_goals=tuple(non_goals) if non_goals else (),
                supersedes=supersedes,
            )

            if auto_writeback and result.get("consumer_payloads") and result.get("packet"):
                from ..dogfood.writeback import write_consumer_payloads

                wb_results = write_consumer_payloads(
                    project_root=self._project_root,
                    consumer_payloads=result["consumer_payloads"],
                    packet_id=result["packet"]["packet_id"],
                    active_gate_path=active_gate_path,
                    dry_run=self._dry_run,
                )
                result["writeback_results"] = wb_results

            return result
        except Exception as exc:
            _log.error("promote_dogfood_evidence failed: %s", exc)
            return {"error": str(exc)}

    # ── Pack Integrity ─────────────────────────────────────────────────

    def pack_lock(self, pack_name: str = "") -> dict:
        """Lock one or all packs by recording content hash in pack-lock.json."""
        from ..pack.pack_integrity import load_lock, save_lock, compute_pack_hash

        err = self._require_pipeline()
        if err is not None:
            return err

        lock = load_lock(self._project_root)
        pipeline = self._pipeline
        manifest_dir_pairs = [
            (m, d)
            for m, d in getattr(pipeline, "_manifest_dir_pairs", [])
        ]

        # Fallback: rediscover packs if _manifest_dir_pairs not available
        if not manifest_dir_pairs:
            from ..pack.pack_discovery import discover_packs
            discovered = discover_packs(self._project_root)
            from ..pack import manifest_loader
            for manifest_path, base_dir in discovered:
                try:
                    m = manifest_loader.load(manifest_path)
                    manifest_dir_pairs.append((m, base_dir))
                except Exception:
                    continue

        locked: list[dict] = []
        for manifest, base_dir in manifest_dir_pairs:
            if pack_name and manifest.name != pack_name:
                continue
            entry = lock.lock_pack(
                name=manifest.name,
                version=manifest.version,
                kind=manifest.kind,
                base_dir=base_dir,
            )
            locked.append(entry.to_dict())

        if pack_name and not locked:
            return {"error": f"Pack '{pack_name}' not found"}

        save_lock(self._project_root, lock)
        return {"locked": locked, "total_entries": len(lock.entries)}

    def pack_unlock(self, pack_name: str) -> dict:
        """Remove a pack from pack-lock.json."""
        from ..pack.pack_integrity import load_lock, save_lock

        lock = load_lock(self._project_root)
        if lock.unlock_pack(pack_name):
            save_lock(self._project_root, lock)
            return {"unlocked": pack_name, "total_entries": len(lock.entries)}
        return {"error": f"Pack '{pack_name}' not found in lock file"}

    def pack_verify(self, pack_name: str = "") -> dict:
        """Verify pack integrity against pack-lock.json."""
        from ..pack.pack_integrity import load_lock, verify_pack

        err = self._require_pipeline()
        if err is not None:
            return err

        lock = load_lock(self._project_root)
        if not lock.entries:
            return {"status": "no_lock", "message": "No pack-lock.json entries found"}

        pipeline = self._pipeline
        manifest_dir_pairs = getattr(pipeline, "_manifest_dir_pairs", [])

        if not manifest_dir_pairs:
            from ..pack.pack_discovery import discover_packs
            from ..pack import manifest_loader
            discovered = discover_packs(self._project_root)
            manifest_dir_pairs = []
            for manifest_path, base_dir in discovered:
                try:
                    m = manifest_loader.load(manifest_path)
                    manifest_dir_pairs.append((m, base_dir))
                except Exception:
                    continue

        results: list[dict] = []
        for manifest, base_dir in manifest_dir_pairs:
            if pack_name and manifest.name != pack_name:
                continue
            r = verify_pack(manifest.name, base_dir, lock)
            results.append({
                "name": r.name,
                "status": r.status,
                "expected_hash": r.expected_hash,
                "actual_hash": r.actual_hash,
                "detail": r.detail,
            })

        # Also check locked packs not present in discovered set
        discovered_names = {m.name for m, _ in manifest_dir_pairs}
        for entry_name, entry in lock.entries.items():
            if pack_name and entry_name != pack_name:
                continue
            if entry_name not in discovered_names:
                results.append({
                    "name": entry_name,
                    "status": "missing_pack",
                    "expected_hash": entry.content_hash,
                    "actual_hash": "",
                    "detail": "Locked pack not found in workspace",
                })

        if pack_name and not results:
            return {"error": f"Pack '{pack_name}' not found"}

        summary = {
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "mismatch": sum(1 for r in results if r["status"] == "mismatch"),
            "missing_lock": sum(1 for r in results if r["status"] == "missing_lock"),
            "missing_pack": sum(1 for r in results if r["status"] == "missing_pack"),
        }
        return {"results": results, "summary": summary}

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
