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
                    "Return information about loaded packs, merged intents, gates, and document types."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        import json

        if name == "governance_decide":
            result = tools.governance_decide(arguments["input_text"])
        elif name == "check_constraints":
            result = tools.check_constraints()
        elif name == "get_next_action":
            result = tools.get_next_action()
        elif name == "writeback_notify":
            result = tools.writeback_notify(arguments["phase_description"])
        elif name == "get_pack_info":
            result = tools.get_info()
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
