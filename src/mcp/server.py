"""MCP Server for doc-based-coding governance platform.

Exposes governance tools via the Model Context Protocol so that
compatible MCP clients such as Copilot, Codex, or other stdio-capable hosts
can inspect project constraint status and runtime-enforceable coverage for
the C1-C8 rule set.

Installed entry point:
    doc-based-coding-mcp --project /path/to/project

Module entry point:
    python -m src.mcp.server --project /path/to/project
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    EmbeddedResource,
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)

from .tools import GovernanceTools


def _find_project_root() -> Path:
    """Walk up from CWD to find project root."""
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        if (p / "design_docs").is_dir() or (p / ".codex").is_dir():
            return p
    return cwd


def create_server(project_root: Path, *, dry_run: bool = True) -> Server:
    """Create and configure the MCP server with governance tools."""
    server = Server("doc-based-coding-governance")
    tools = GovernanceTools(project_root, dry_run=dry_run)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="governance_decide",
                description=(
                    "Run the full governance chain (PDP → PEP) on user input. "
                    "Returns BLOCK if project constraints are violated (e.g. no planning-gate), "
                    "or ALLOW with intent classification, gate level, and execution result. "
                    "MUST be called before starting any significant work."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input_text": {
                            "type": "string",
                            "description": "The user's input text to classify and process through governance.",
                        },
                        "scope_path": {
                            "type": "string",
                            "description": (
                                "Optional file or directory path used to select the "
                                "matching pack-tree branch for scope-aware governance. "
                                "When omitted, global (unscoped) rules apply."
                            ),
                        },
                    },
                    "required": ["input_text"],
                },
            ),
            Tool(
                name="check_constraints",
                description=(
                    "Report project-level constraints (C1-C8), including which ones are "
                    "machine-checked versus still instruction-layer. Returns current violations, "
                    "files to re-read for context recovery, and project phase info. "
                    "Call this after context compression or at the start of a new client session."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="get_next_action",
                description=(
                    "Get the recommended next action based on current project state. "
                    "Returns instruction text, document references, and whether to ask the user. "
                    "Call this when unsure what to do next or after recovering from context compression."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="writeback_notify",
                description=(
                    "Notify that a phase or slice writeback has been completed. "
                    "Returns auto-progression recommendation with next steps. "
                    "MUST be called after completing a write-back to drive automatic phase progression."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "phase_description": {
                            "type": "string",
                            "description": "Description of the phase/slice that was just completed.",
                        },
                    },
                    "required": ["phase_description"],
                },
            ),
            Tool(
                name="get_pack_info",
                description=(
                    "Return information about loaded packs, merged intents, gates, and document types. "
                    "Use scope_path to filter by directory scope. Use level to control detail depth: "
                    "'metadata' (name/kind/provides/description only), "
                    "'manifest' (full capability sets, default), "
                    "'full' (manifest + always_on content summary)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "scope_path": {
                            "type": "string",
                            "description": (
                                "Optional file or directory path used to select the matching "
                                "pack-tree branch for scope-aware pack info."
                            ),
                        },
                        "level": {
                            "type": "string",
                            "description": (
                                "Detail level: 'metadata', 'manifest' (default), or 'full'."
                            ),
                            "enum": ["metadata", "manifest", "full"],
                        },
                    },
                },
            ),
            Tool(
                name="governance_override",
                description=(
                    "Register, revoke, or list temporary rule overrides. "
                    "Allows the model to record user-authorised, auditable, auto-expiring "
                    "exemptions from overridable constraints (C1, C2, C3, C6, C7). "
                    "Non-overridable constraints (C4, C5, C8) will be rejected."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["register", "revoke", "list"],
                            "description": "The override action to perform.",
                        },
                        "constraint": {
                            "type": "string",
                            "description": "Constraint identifier (e.g. 'C1'). Required for 'register'.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "User-authorised reason for the override. Required for 'register'.",
                        },
                        "scope": {
                            "type": "string",
                            "enum": ["turn", "session", "until-next-safe-stop"],
                            "description": "Override lifetime scope. Default: 'session'.",
                        },
                        "override_id": {
                            "type": "string",
                            "description": "Override ID to revoke. Required for 'revoke'.",
                        },
                    },
                    "required": ["action"],
                },
            ),
            Tool(
                name="query_decision_logs",
                description=(
                    "Query persisted decision log entries. "
                    "Supports filtering by trace_id, decision (ALLOW/BLOCK), and intent. "
                    "Returns the most recent entries first, up to the specified limit."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "trace_id": {
                            "type": "string",
                            "description": "Filter by trace ID.",
                        },
                        "decision": {
                            "type": "string",
                            "enum": ["ALLOW", "BLOCK"],
                            "description": "Filter by decision outcome.",
                        },
                        "intent": {
                            "type": "string",
                            "description": "Filter by intent classification.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum entries to return. Default: 50.",
                        },
                    },
                },
            ),
            Tool(
                name="impact_analysis",
                description=(
                    "Analyze change impact through the dependency graph. "
                    "Given changed files or symbols, propagates through the baseline "
                    "dependency graph to identify directly and transitively affected nodes. "
                    "Use this when modifying a Protocol, class, or module to discover "
                    "what else may need updating."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "changed_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed file paths.",
                        },
                        "changed_symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed symbol/node IDs (e.g. 'src.interfaces.WorkerBackend').",
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum propagation depth. Default: 2.",
                        },
                    },
                },
            ),
            Tool(
                name="coupling_check",
                description=(
                    "Check coupling annotations against changes. "
                    "Matches changed files or symbols against explicit semantic coupling "
                    "declarations and returns alerts for locations that may need syncing. "
                    "Use this when you've changed a file and want to check if any "
                    "coupled documentation or companion files need updating."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "changed_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed file paths.",
                        },
                        "changed_symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed symbol names.",
                        },
                    },
                },
            ),
            Tool(
                name="analyze_changes",
                description=(
                    "Unified change analysis: combines dependency-graph impact "
                    "propagation with coupling annotation checks in a single call. "
                    "Given changed files or symbols, returns both the set of directly/"
                    "transitively affected nodes AND any coupling alerts that need "
                    "syncing. Prefer this over calling impact_analysis and "
                    "coupling_check separately."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "changed_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed file paths.",
                        },
                        "changed_symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of changed symbol/node IDs (e.g. 'src.interfaces.WorkerBackend').",
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum propagation depth. Default: 2.",
                        },
                    },
                },
            ),
            Tool(
                name="promote_dogfood_evidence",
                description=(
                    "Run the full dogfood evidence-to-feedback pipeline: "
                    "evaluate symptoms against promotion thresholds (T1-T4/S1-S3), "
                    "build issue candidates for promoted symptoms, assemble a feedback "
                    "packet, and dispatch consumer payloads per the boundary matrix. "
                    "Use when dogfood observations need structured triage and feedback routing."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "symptoms": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "symptom_id": {"type": "string"},
                                    "symptom_summary": {"type": "string"},
                                    "evidence_refs": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "path": {"type": "string"},
                                                "section": {"type": "string"},
                                                "summary": {"type": "string"},
                                            },
                                            "required": ["path"],
                                        },
                                    },
                                    "category": {"type": "string"},
                                    "affects_next_gate": {"type": "boolean"},
                                    "requires_next_slice": {"type": "boolean"},
                                    "occurrence_count": {"type": "integer"},
                                    "impact_layers": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "minimal_reproducer": {"type": "string"},
                                    "expected": {"type": "string"},
                                    "actual": {"type": "string"},
                                    "evidence_excerpt": {"type": "string"},
                                    "environment": {"type": "string"},
                                    "non_goals": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                                "required": ["symptom_id", "symptom_summary"],
                            },
                            "description": "Symptom observations to evaluate for promotion.",
                        },
                        "existing_issue_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Previously promoted issue IDs for de-duplication (S2 check).",
                        },
                        "date": {
                            "type": "string",
                            "description": "Date label in YYYY-MM-DD format for packet ID generation.",
                        },
                        "judgment": {
                            "type": "string",
                            "description": "Human/domain judgment summary for the feedback packet.",
                        },
                        "next_step_implication": {
                            "type": "string",
                            "description": "What the next planning step should consider.",
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confidence level for the feedback packet. Default: medium.",
                        },
                        "non_goals": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "What this feedback explicitly does NOT address.",
                        },
                        "supersedes": {
                            "type": "string",
                            "description": "Packet ID this feedback replaces, if any.",
                        },
                        "auto_writeback": {
                            "type": "boolean",
                            "description": "If true, write consumer payloads to target documents. Default: false.",
                        },
                        "active_gate_path": {
                            "type": "string",
                            "description": "Relative path to the current active planning-gate file, for planning-gate consumer writeback.",
                        },
                    },
                    "required": ["symptoms"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        import json

        if name == "governance_decide":
            result = tools.governance_decide(
                arguments["input_text"],
                scope_path=arguments.get("scope_path", ""),
            )
        elif name == "check_constraints":
            result = tools.check_constraints()
        elif name == "get_next_action":
            result = tools.get_next_action()
        elif name == "writeback_notify":
            result = tools.writeback_notify(arguments["phase_description"])
        elif name == "get_pack_info":
            result = tools.get_info(
                scope_path=arguments.get("scope_path", ""),
                level=arguments.get("level", "manifest"),
            )
        elif name == "governance_override":
            action = arguments.get("action", "")
            result = tools.governance_override(
                action,
                constraint=arguments.get("constraint", ""),
                reason=arguments.get("reason", ""),
                scope=arguments.get("scope", "session"),
                override_id=arguments.get("override_id", ""),
            )
        elif name == "query_decision_logs":
            result = tools.query_decision_logs(
                trace_id=arguments.get("trace_id", ""),
                decision=arguments.get("decision", ""),
                intent=arguments.get("intent", ""),
                limit=arguments.get("limit", 50),
            )
        elif name == "impact_analysis":
            result = tools.impact_analysis(
                changed_files=arguments.get("changed_files"),
                changed_symbols=arguments.get("changed_symbols"),
                max_depth=arguments.get("max_depth", 2),
            )
        elif name == "coupling_check":
            result = tools.coupling_check(
                changed_files=arguments.get("changed_files"),
                changed_symbols=arguments.get("changed_symbols"),
            )
        elif name == "analyze_changes":
            result = tools.analyze_changes(
                changed_files=arguments.get("changed_files"),
                changed_symbols=arguments.get("changed_symbols"),
                max_depth=arguments.get("max_depth", 2),
            )
        elif name == "promote_dogfood_evidence":
            result = tools.promote_dogfood_evidence(
                symptoms=arguments.get("symptoms", []),
                existing_issue_ids=arguments.get("existing_issue_ids"),
                date=arguments.get("date", ""),
                judgment=arguments.get("judgment", ""),
                next_step_implication=arguments.get("next_step_implication", ""),
                confidence=arguments.get("confidence", "medium"),
                non_goals=arguments.get("non_goals"),
                supersedes=arguments.get("supersedes"),
                auto_writeback=arguments.get("auto_writeback", False),
                active_gate_path=arguments.get("active_gate_path"),
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        text = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        return [TextContent(type="text", text=text)]

    # ── Prompts ────────────────────────────────────────────────────────

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        prompt_list = tools.list_prompts()
        return [
            Prompt(
                name=p["name"],
                description=p.get("description", ""),
                arguments=[],
            )
            for p in prompt_list
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
        content = tools.get_prompt(name)
        if content is None:
            return GetPromptResult(
                description=f"Prompt '{name}' not found",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=f"Prompt '{name}' not found."),
                    )
                ],
            )
        return GetPromptResult(
            description=f"Pack prompt: {name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=content),
                )
            ],
        )

    # ── Resources ──────────────────────────────────────────────────────

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        resource_list = tools.list_resources()
        return [
            Resource(
                uri=r["uri"],
                name=r.get("name", r["uri"]),
                description=r.get("description", ""),
                mimeType=r.get("mimeType", "text/plain"),
            )
            for r in resource_list
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> str | bytes:
        content = tools.read_resource(str(uri))
        if content is None:
            return f"Resource '{uri}' not found."
        return content

    return server


async def run_stdio(project_root: Path, *, dry_run: bool = True) -> None:
    """Run MCP server over stdio transport."""
    server = create_server(project_root, dry_run=dry_run)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    parser = argparse.ArgumentParser(description="Doc-based-coding governance MCP server")
    parser.add_argument(
        "--project", type=str, default=None,
        help="Project root directory (auto-detected if not set)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Run in dry-run mode (no file writes, default)",
    )
    parser.add_argument(
        "--no-dry-run", action="store_true", default=False,
        help="Run in live mode (file writes enabled)",
    )
    args = parser.parse_args()

    project_root = Path(args.project) if args.project else _find_project_root()
    dry_run = not args.no_dry_run

    import asyncio
    asyncio.run(run_stdio(project_root, dry_run=dry_run))


if __name__ == "__main__":
    main()
