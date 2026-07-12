"""Instructions Generator — produce agent-instruction segments from Pack context.

Reads loaded PackContext (from Pipeline) and generates Markdown that can be
injected into Codex `AGENTS.md`, Copilot instruction files, or another static
instruction surface to enforce constraints at the instructions layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..pack.context_builder import PackContext


class InstructionsGenerator:
    """Generate instruction content from a PackContext.

    The generated Markdown includes:
    - Pack metadata (name, version, kind)
    - Declared document types with descriptions
    - Declared intents and gate levels
    - Rules / constraints (the most critical section)
    - Always-on content summaries
    - Workflow stage descriptions
    """

    def __init__(self, pack_context: PackContext, target: str = "generic") -> None:
        self._ctx = pack_context
        self._target = _normalize_instruction_target(target)

    def generate(self) -> str:
        """Generate the full Markdown instructions block.

        Returns a string that can be written to AGENTS.md, a Copilot
        instructions file, or appended to an existing instruction surface.
        """
        sections: list[str] = []
        sections.append(self._header())
        sections.append(self._constraints_section())
        sections.append(self._conversation_progression_section())
        sections.append(self._work_agent_local_trajectory_section())
        sections.append(self._workspace_dbc_relay_section())
        sections.append(self._temporary_override_section())
        sections.append(self._external_skill_interaction_section())
        sections.append(self._document_types_section())
        sections.append(self._intents_section())
        sections.append(self._gates_section())
        sections.append(self._always_on_section())
        sections.append(self._rules_section())
        return "\n".join(s for s in sections if s)

    def _header(self) -> str:
        meta = _TARGET_METADATA[self._target]
        lines = [f"# {meta['title']}", "", f"> {meta['note']}", ""]
        for m in self._ctx.manifests:
            lines.append(f"- Pack: **{m.name}** v{m.version} ({m.kind})")
            if m.scope:
                lines.append(f"  - Scope: {m.scope}")
        lines.append("")
        return "\n".join(lines)

    def _conversation_progression_section(self) -> str:
        """Render the structured conversation progression contract, if any."""
        rules = self._ctx.merged_rules
        if not rules:
            return ""

        contract = rules.get("conversation_progression")
        if not isinstance(contract, dict) or not contract:
            return ""

        lines = ["## Conversation Progression Contract", ""]

        if contract.get("termination_requires_user_permission"):
            lines.append(
                "- Do not end the conversation unless the user explicitly allows ending or pausing."
            )
        if contract.get("final_reply_requires_forward_question"):
            lines.append(
                "- Default reply shape: provide analysis or a recommendation first, then end with a forward question."
            )
        if contract.get("question_must_include_analysis"):
            lines.append(
                "- The closing question must include your own analysis, recommendation, or tentative judgment."
            )

        required_for = contract.get("structured_confirmation_required_for", [])
        if isinstance(required_for, list) and required_for:
            lines.append(
                "- For structured confirmation during "
                + ", ".join(str(item) for item in required_for)
                + ", use the host's available confirmation surface when one exists; otherwise use a clear textual forward question after presenting your recommendation."
            )

        if contract.get("phase_completion_requires_next_direction"):
            lines.append(
                "- After phase or write-back completion, prepare the next direction and ask instead of stopping."
            )

        exceptions = contract.get("allowed_non_question_endings", [])
        if isinstance(exceptions, list) and exceptions:
            lines.append(
                "- Allowed exceptions for a non-question ending: "
                + ", ".join(str(item) for item in exceptions)
                + "."
            )

        # Completion boundary static redundancy (方案 A)
        boundary = contract.get("completion_boundary_protocol")
        if isinstance(boundary, dict) and boundary:
            tool_name = boundary.get("mandatory_tool_call", "get_next_action")
            lines.append("")
            lines.append(
                f"- **Completion Boundary Rule**: When all tasks are done and no planning gate is active, "
                f"you MUST call `{tool_name}` before composing your response. "
                "Never end with \"shall we continue or stop?\" — "
                "always provide your analysis of the next direction."
            )

        lines.append("")
        return "\n".join(lines)

    def _work_agent_local_trajectory_section(self) -> str:
        """Render generic guidance for leader-owned local trajectory updates."""

        lines = [
            "## Work Agent Local Trajectory",
            "",
            "- For task-like implementation, validation, review, or write-back work, the agent owns Local Work Trajectory maintenance.",
            "- Direct `localTrajectory` mutation is leader/main/supervisor authority. Bounded workers/subagents must not call `localTrajectory` directly; they must put progress/status suggestions in `Subagent Report.trajectory_update` for the leader to consume. Worker report procedure: `docs/worker-trajectory-update-reporting.md`.",
            "- Do not wait for the user to ask for trajectory updates. Start or continue the trajectory as part of doing the work.",
            "- Use the MCP `localTrajectory` tool as the preferred mutation surface when it is available to a leader/main/supervisor context.",
            "- Before substantial task work begins, judge whether the task is large enough or split-worthy enough to need distinct Local Work lanes. If yes or uncertain, follow `design_docs/tooling/local-work-lane-splitting/README.md`; keep detailed lane split criteria there, not in generated instructions.",
            "- Leader-worker is recommended for single-lane Local Work and required when Local Work has two or more lanes. In multi-lane work, model workers and the leader as activatable lifecycle participants: they may wait for dependencies, review, or messages, and message-driven reactivation must remain auditable.",
            "- A multi-lane Local Work Trajectory proves only a logical split, not runtime worker dispatch. For leader-worker work with two or more lanes, retain auditable collaboration evidence through worker reports, ExchangeArtifact history, scheduler events, or runtime invocation audit; if dispatch is unavailable, record an explicit orchestration blocker instead of claiming worker collaboration.",
            "- Call `localTrajectory start` when beginning a tracked task and no active trajectory exists; include `sourceGraphId` and `sourceNodeId` on `start` when a visible owning progress-map node is known so the trajectory is attached from birth.",
            "- Call `append` for planned or observed milestones; call `advance` when the active milestone is complete.",
            "- Use `localTrajectory addLane` as soon as a clearly separate work context must begin; use `merge` only to add an explicit fan-in marker when that lane rejoins a target lane.",
            "- Use `localTrajectory addCompound` when a planned phase should appear as one large event with its own child trajectory; it does not pack or move existing events.",
            "- Use `localTrajectory packRange` only to pack an existing continuous same-lane event interval into one compound event while preserving the interval in the child trajectory.",
            "- Use `localTrajectory appendChild`, `advanceChild`, and `closeChild` to continue or finish the child trajectory of an existing compound parent.",
            "- Use `localTrajectory relate` to record explicit `depends_on`, `waits_for`, `unblocks`, `hands_off`, `syncs_from`, or `approves_new_line` metadata between existing events when the relation matters for reading the work map.",
            "- Use `localTrajectory setAnchor` when the current trajectory should move under a different global progress-map node after start; pass both `sourceGraphId` and `sourceNodeId`, or pass neither to clear the anchor.",
            "- Do not treat Local Work Trajectory addCompound, packRange, child trajectory actions, merge, or relate as dependency scheduling, conflict resolution, or grouped review semantics.",
            "- After validation or delivery is complete, continue calling `localTrajectory advance` until completed validation/delivery milestones are no longer left as `pending` or `in_progress`.",
            "- If `localTrajectory` is required but missing from the available tools, report a tool exposure / MCP binding problem explicitly and use the repository's local trajectory API only when the current project rules allow local file mutation.",
            "- When worker execution uses a backend runtime such as Codex, Qoder, or opencode, prefer host-owned wrappers that record compact runtime invocation audit/retry records. Do not persist raw transcripts or secret values.",
            "- Do not ask the user to manually maintain Local Work Trajectory nodes.",
            "- 当涉及UI等图像的工作时，在验收前务必使用截图性质工具进行验证。 For UI or other image-like output, use screenshot-style validation before acceptance.",
            "",
        ]
        return "\n".join(lines)

    def _workspace_dbc_relay_section(self) -> str:
        """Render guidance for workspace-bound DBC command relay usage."""

        lines = [
            "## Workspace DBC Command Relay",
            "",
            "- When MCP exposes `workspaceDbcCommand`, use it for DBC CLI-equivalent checks or operator commands instead of asking the model to resolve `doc-based-coding` from PATH, virtualenvs, or checkout locations.",
            "- Treat `workspaceDbcCommand` as a per-agent, workspace-bound relay: it is provided by that agent's MCP server instance and should run against that agent's current project root.",
            "- Prefer dedicated structured MCP tools such as `localTrajectory`, `get_next_action`, or scheduler tools when they exist; use the relay only for CLI surfaces without a dedicated tool.",
            "- If a DBC CLI-equivalent action is needed but neither a dedicated MCP tool nor `workspaceDbcCommand` is exposed, report the MCP/tool exposure problem explicitly instead of falling back to a global `doc-based-coding` command.",
            "",
        ]
        return "\n".join(lines)

    def _temporary_override_section(self) -> str:
        """Render the temporary override guidance, if configured."""
        rules = self._ctx.merged_rules
        if not rules:
            return ""

        config = rules.get("temporary_override")
        if not isinstance(config, dict) or not config:
            return ""

        lines = ["## Temporary Rule Override", ""]

        if config.get("require_user_authorisation"):
            lines.append(
                "- Temporary override of an instruction-layer constraint requires explicit user authorisation in the current conversation."
            )

        overridable = config.get("overridable_constraints", [])
        if isinstance(overridable, list) and overridable:
            lines.append(
                "- Overridable constraints: " + ", ".join(str(c) for c in overridable) + "."
            )

        non_overridable = config.get("non_overridable_constraints", [])
        if isinstance(non_overridable, list) and non_overridable:
            lines.append(
                "- Non-overridable (always enforced): " + ", ".join(str(c) for c in non_overridable) + "."
            )

        mcp_tool = config.get("mcp_tool")
        if mcp_tool:
            lines.append(
                f"- Use the `{mcp_tool}` MCP tool to register, revoke, or list overrides."
            )

        scopes = config.get("scopes", [])
        if isinstance(scopes, list) and scopes:
            lines.append(
                "- Override scopes: " + ", ".join(f"`{s}`" for s in scopes) + "."
            )

        if config.get("session_overrides_expire_at_safe_stop"):
            lines.append(
                "- Session-scoped and until-next-safe-stop overrides automatically expire during safe-stop writeback."
            )

        lines.append("")
        return "\n".join(lines)

    def _external_skill_interaction_section(self) -> str:
        """Render the structured external skill interaction contract, if any."""
        rules = self._ctx.merged_rules
        if not rules:
            return ""

        contract = rules.get("external_skill_interaction")
        if not isinstance(contract, dict) or not contract:
            return ""

        lines = ["## External Skill Interaction Contract", ""]

        if contract.get("model_may_initiate_when_rules_allow"):
            lines.append(
                "- External skills may be model-initiated when the governing workflow allows that branch."
            )
        if contract.get("slash_is_explicit_route_not_only_surface"):
            lines.append(
                "- Slash routing remains a valid explicit route, but it is not the only invocation surface."
            )

        automatic_stop = contract.get("automatic_stop_signal")
        if automatic_stop:
            lines.append(
                f"- `{automatic_stop}` is the only automatic stop signal for the external skill branch."
            )
        if contract.get("non_blocked_results_may_continue"):
            lines.append(
                "- If the result is not blocked, the model may continue to the next directly relevant step."
            )
        if contract.get("result_payload_may_be_skill_specific"):
            lines.append(
                "- Skill payloads may remain skill-specific, but the top-level continuation semantics must stay stable."
            )

        authority_primitives = contract.get("authority_transfer_requires_primitives", [])
        if isinstance(authority_primitives, list) and authority_primitives:
            lines.append(
                "- Authority transfer must go through explicit primitives: "
                + ", ".join(str(item) for item in authority_primitives)
                + "."
            )

        reference_family = contract.get("reference_implementation_family")
        if reference_family:
            lines.append(
                f"- Current reference implementation family: `{reference_family}`."
            )

        distribution_rule = contract.get("companion_distribution_rule")
        if distribution_rule:
            lines.append(
                f"- Companion distribution rule: `{distribution_rule}` protects authority -> shipped copies consistency."
            )

        lines.append("")
        return "\n".join(lines)

    def _constraints_section(self) -> str:
        """Generate the constraints block from merged_rules."""
        rules = self._ctx.merged_rules
        if not rules:
            return ""

        lines = ["## Constraints (MUST obey)", ""]

        # Extract constraints from rules structure
        constraints = rules.get("constraints", {})
        if isinstance(constraints, dict):
            for cid, desc in constraints.items():
                if isinstance(desc, str):
                    lines.append(f"- **{cid}**: {desc}")
                elif isinstance(desc, dict):
                    msg = desc.get("description", desc.get("message", str(desc)))
                    severity = desc.get("severity", "")
                    sev_tag = f" [{severity}]" if severity else ""
                    lines.append(f"- **{cid}**{sev_tag}: {msg}")
        elif isinstance(constraints, list):
            for item in constraints:
                if isinstance(item, str):
                    lines.append(f"- {item}")
                elif isinstance(item, dict):
                    cid = item.get("id", item.get("name", ""))
                    msg = item.get("description", item.get("message", str(item)))
                    lines.append(f"- **{cid}**: {msg}")

        # Also check top-level rule keys that look like constraints
        for key in ("always_on_rules", "behavioral_rules", "safety_rules"):
            sub = rules.get(key, [])
            if isinstance(sub, list):
                for item in sub:
                    if isinstance(item, str):
                        lines.append(f"- {item}")

        lines.append("")
        return "\n".join(lines)

    def _document_types_section(self) -> str:
        doc_types = self._ctx.merged_document_types
        if not doc_types:
            return ""
        lines = ["## Document Types", ""]
        lines.append("The following document types are recognized by the governance system:")
        lines.append("")
        for dt in doc_types:
            lines.append(f"- `{dt}`")
        lines.append("")
        return "\n".join(lines)

    def _intents_section(self) -> str:
        intents = self._ctx.merged_intents
        if not intents:
            return ""
        lines = ["## Recognized Intents", ""]
        lines.append("User input will be classified into one of these intents:")
        lines.append("")
        for intent in intents:
            lines.append(f"- `{intent}`")
        lines.append("")
        return "\n".join(lines)

    def _gates_section(self) -> str:
        gates = self._ctx.merged_gates
        if not gates:
            return ""
        lines = ["## Gate Levels", ""]
        lines.append("Every action is gated at one of these levels:")
        lines.append("")
        for gate in gates:
            desc = _GATE_DESCRIPTIONS.get(gate, "")
            suffix = f" — {desc}" if desc else ""
            lines.append(f"- `{gate}`{suffix}")
        lines.append("")
        return "\n".join(lines)

    def _always_on_section(self) -> str:
        content = self._ctx.always_on_content
        if not content:
            return ""
        lines = ["## Always-On Context", ""]
        lines.append("The following files are always loaded into context:")
        lines.append("")
        for filename in sorted(content.keys()):
            lines.append(f"### `{filename}`")
            lines.append("")
            summary = self._summarize_content(content[filename])
            if summary:
                lines.append(summary)
                lines.append("")
        return "\n".join(lines)

    def _rules_section(self) -> str:
        """Emit full rules dict as structured Markdown."""
        rules = self._ctx.merged_rules
        if not rules:
            return ""

        # Skip 'constraints' key (already handled in constraints_section)
        other_rules = {k: v for k, v in rules.items() if k != "constraints"}
        if not other_rules:
            return ""

        lines = ["## Rules Configuration", ""]
        for key, value in other_rules.items():
            if key in ("always_on_rules", "behavioral_rules", "safety_rules"):
                continue  # already in constraints section
            lines.append(f"### {key}")
            lines.append("")
            if isinstance(value, dict):
                for sk, sv in value.items():
                    lines.append(f"- **{sk}**: {sv}")
            elif isinstance(value, list):
                for item in value:
                    lines.append(f"- {item}")
            else:
                lines.append(f"{value}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _summarize_content(text: str, max_lines: int = 20) -> str:
        """Extract a summary from file content.

        Strategy: keep headings and the first non-empty line after each
        heading, up to *max_lines* output lines.
        """
        src_lines = text.splitlines()
        out: list[str] = []
        for line in src_lines:
            if len(out) >= max_lines:
                out.append("*(truncated)*")
                break
            stripped = line.strip()
            if stripped.startswith("#"):
                out.append(stripped)
            elif stripped and (not out or out[-1].startswith("#") or out[-1] == ""):
                out.append(stripped)
        return "\n".join(out)


def generate_instructions(pack_context: PackContext, target: str = "generic") -> str:
    """Convenience function — generate instructions from a PackContext."""
    return InstructionsGenerator(pack_context, target=target).generate()


def generate_instructions_from_project(
    project_root: str | Path,
    target: str = "generic",
) -> str:
    """Generate instructions by auto-discovering packs from a project root.

    This is the main entry point for CLI usage.
    """
    # Import here to avoid circular dependency
    from .pipeline import Pipeline

    pipeline = Pipeline.from_project(project_root, dry_run=True, audit=False)
    return InstructionsGenerator(pipeline.pack_context, target=target).generate()


def infer_instruction_target(output_path: str | Path | None) -> str | None:
    """Infer a target from a conventional output filename."""
    if output_path is None:
        return None

    name = Path(output_path).name.lower()
    if name in {"agents.md", "agents.override.md"}:
        return "codex"
    if name == "copilot-instructions.md":
        return "copilot"
    return None


# ── Constants ────────────────────────────────────────────────────────────

_TARGET_METADATA: dict[str, dict[str, str]] = {
    "generic": {
        "title": "Governance Instructions (auto-generated from Pack)",
        "note": (
            "This block is tool-agnostic. Paste it into `AGENTS.md` or another "
            "instruction surface used by your coding agent."
        ),
    },
    "codex": {
        "title": "Governance Instructions for Codex",
        "note": (
            "Paste this content into a repository-level `AGENTS.md` so Codex can "
            "discover it automatically."
        ),
    },
    "copilot": {
        "title": "Copilot Workspace Instructions",
        "note": (
            "Paste this content into `.github/copilot-instructions.md` or another "
            "Copilot instruction file."
        ),
    },
}


def _normalize_instruction_target(target: str) -> str:
    normalized = target.strip().lower()
    if normalized not in _TARGET_METADATA:
        allowed = ", ".join(sorted(_TARGET_METADATA))
        raise ValueError(f"Unsupported instructions target: {target!r}. Expected one of: {allowed}.")
    return normalized

_GATE_DESCRIPTIONS: dict[str, str] = {
    "inform": "Low-impact action; proceed and inform the user",
    "review": "Medium-impact action; present for user review before proceeding",
    "approve": "High-impact action; MUST get explicit user approval before proceeding",
}
