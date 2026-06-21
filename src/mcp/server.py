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
                        "action_type": {
                            "type": "string",
                            "description": (
                                "Optional action type for tool-level permission check "
                                "(e.g. 'terminal_command', 'file_delete', 'git_push'). "
                                "When provided, pack-defined tool_permissions are evaluated "
                                "before the full PDP/PEP chain."
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
                    "Supports filtering by trace_id, decision (ALLOW/BLOCK), intent, "
                    "and whether merge conflicts were recorded. "
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
                        "has_merge_conflicts": {
                            "type": "boolean",
                            "description": "If true, only entries with merge conflicts; if false, only without.",
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
            Tool(
                name="workflow_interrupt",
                description=(
                    "Signal a workflow interrupt when an out-of-scope item is discovered "
                    "during execution. Returns structured guidance directing the agent "
                    "to write the discovered item to a planning-gate document rather than "
                    "expanding scope in-place. Implements the rule: 'if a new problem "
                    "exceeds the current slice, write to planning-gate first.'"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Why the interrupt is triggered (e.g. 'discovered new requirement beyond current scope').",
                        },
                        "discovered_item": {
                            "type": "string",
                            "description": "Description of the out-of-scope item found.",
                        },
                        "current_scope_ref": {
                            "type": "string",
                            "description": "Reference to the current planning-gate or phase doc (optional).",
                        },
                    },
                    "required": ["reason", "discovered_item"],
                },
            ),
            Tool(
                name="update_user_config",
                description=(
                    "Update a single field in the user-global config file "
                    "(~/.doc-based-coding/config.json). Returns the full config "
                    "after the update. Accepted fields: extra_pack_dirs, "
                    "default_model, default_llm_params."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "description": "The config field to update.",
                            "enum": ["extra_pack_dirs", "default_model", "default_llm_params"],
                        },
                        "value": {
                            "description": "The new value for the field.",
                        },
                    },
                    "required": ["field", "value"],
                },
            ),
            Tool(
                name="pack_lock",
                description=(
                    "Lock one or all packs by recording their content hash in "
                    "pack-lock.json. If no pack_name is given, locks all discovered packs."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pack_name": {
                            "type": "string",
                            "description": "Name of the pack to lock (optional — omit to lock all).",
                        },
                    },
                },
            ),
            Tool(
                name="pack_unlock",
                description=(
                    "Remove a pack from pack-lock.json. The pack will no longer "
                    "be verified on pipeline load."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pack_name": {
                            "type": "string",
                            "description": "Name of the pack to unlock.",
                        },
                    },
                    "required": ["pack_name"],
                },
            ),
            Tool(
                name="pack_verify",
                description=(
                    "Verify pack integrity against pack-lock.json. "
                    "Returns per-pack status (ok/mismatch/missing_lock/missing_pack)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pack_name": {
                            "type": "string",
                            "description": "Name of a specific pack to verify (optional — omit to verify all locked packs).",
                        },
                    },
                },
            ),
            Tool(
                name="check_reply_progression",
                description=(
                    "Check if an AI reply ending conforms to the conversation progression contract. "
                    "Detects forbidden patterns (pure yes/no, passive waiting) and verifies "
                    "presence of AI analysis + forward-driving question at the tail. "
                    "Call before sending a reply to ensure compliance."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "reply_text": {
                            "type": "string",
                            "description": "The full reply text to check for progression compliance.",
                        },
                    },
                    "required": ["reply_text"],
                },
            ),
            Tool(
                name="localTrajectory",
                description=(
                    "Agent-owned Local Work Trajectory mutation. Use start when beginning "
                    "a tracked task, append for planned or observed milestones, and advance "
                    "when the active milestone is complete. Use update to refine the current "
                    "milestone, block/wait for impediments, resume to continue, and close "
                    "when the single-line task is done. Use addLane to create one extra "
                    "lane with its first event. Use addLanes when one decision expands "
                    "several distinct lanes at once; this preserves a shared opening "
                    "source so the UI can render a merged fanout instead of overlapping "
                    "start-line edges. "
                    "Use addCompound to create a planned compound/phase event with its own "
                    "child trajectory; this does not pack or move existing events. "
                    "Use packRange to replace a continuous same-lane event interval with "
                    "a compound event and preserve the interval in its child trajectory. "
                    "Use packSubgraph to pack multiple lane-local continuous ranges into "
                    "one compound child trajectory with anchor/proxy parent projection. "
                    "Use appendChild, advanceChild, and closeChild to mutate the child "
                    "trajectory of an existing compound parent. "
                    "Use merge to add an explicit target-lane merge event and a merges_into "
                    "relation from a source lane event. "
                    "Use relate to record an explicit dependency, wait, unblock, handoff, "
                    "sync, or approval relation between existing events; relate is metadata "
                    "only and does not schedule work or resolve conflicts. "
                    "When starting a trajectory, pass sourceGraphId and sourceNodeId if the "
                    "owning global progress-map node is known, so the trajectory is visible "
                    "from birth. Use setAnchor later to move the current trajectory under a "
                    "specific global progress-map node; pass both sourceGraphId and "
                    "sourceNodeId, or pass neither to clear the anchor. "
                    "After validation or delivery completes, keep advancing until completed "
                    "milestones are not left pending or in_progress. This writes only the "
                    "local trajectory metadata artifact, not source files."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "start",
                                "append",
                                "advance",
                                "update",
                                "block",
                                "wait",
                                "resume",
                                "close",
                                "addLane",
                                "addLanes",
                                "addCompound",
                                "packRange",
                                "packSubgraph",
                                "appendChild",
                                "advanceChild",
                                "closeChild",
                                "merge",
                                "relate",
                                "setAnchor",
                            ],
                            "description": "Lifecycle action to perform.",
                        },
                        "laneLabel": {
                            "type": "string",
                            "description": "Short lane label for start.",
                        },
                        "firstEventTitle": {
                            "type": "string",
                            "description": "First active event title for start.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Trajectory title for start or event title for append.",
                        },
                        "eventKind": {
                            "type": "string",
                            "enum": [
                                "start",
                                "task",
                                "decision",
                                "review",
                                "wait",
                                "validation",
                                "writeback",
                                "handoff",
                                "compound",
                                "merge",
                                "close",
                            ],
                            "description": "Event kind for start or append.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Optional summary for append/update/resume/close.",
                        },
                        "reason": {
                            "type": "string",
                            "description": "Block or wait reason for block/wait.",
                        },
                        "guideContext": {
                            "type": "string",
                            "description": "Agent or document context responsible for this local trajectory.",
                        },
                        "currentEventId": {
                            "type": "string",
                            "description": "Optional active event id to advance.",
                        },
                        "laneId": {
                            "type": "string",
                            "description": "Optional lane id for addLane or append.",
                        },
                        "lanes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "laneLabel": {"type": "string"},
                                    "lane_label": {"type": "string"},
                                    "firstEventTitle": {"type": "string"},
                                    "first_event_title": {"type": "string"},
                                    "eventKind": {"type": "string"},
                                    "event_kind": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "laneId": {"type": "string"},
                                    "lane_id": {"type": "string"},
                                },
                            },
                            "description": "Lane specs for addLanes. Use when one source event opens multiple work contexts at once.",
                        },
                        "sourceEventId": {
                            "type": "string",
                            "description": "Optional event id that caused addLane, source event for merge/relate, or range start alias for packRange.",
                        },
                        "sourceLaneId": {
                            "type": "string",
                            "description": "Source lane id for merge.",
                        },
                        "targetLaneId": {
                            "type": "string",
                            "description": "Target lane id for merge. Defaults to lane:main.",
                        },
                        "targetEventId": {
                            "type": "string",
                            "description": "Optional target lane event id for merge, target event for relate, or range end alias for packRange.",
                        },
                        "relationKind": {
                            "type": "string",
                            "enum": [
                                "depends_on",
                                "waits_for",
                                "unblocks",
                                "hands_off",
                                "syncs_from",
                                "merges_into",
                                "proposes_new_line",
                                "approves_new_line",
                            ],
                            "description": "Relation kind for relate.",
                        },
                        "firstChildEventTitle": {
                            "type": "string",
                            "description": "Optional first active child event title for addCompound.",
                        },
                        "childLaneLabel": {
                            "type": "string",
                            "description": "Optional child trajectory lane label for addCompound or packRange.",
                        },
                        "parentEventId": {
                            "type": "string",
                            "description": "Compound parent event id for appendChild, advanceChild, or closeChild.",
                        },
                        "childTrajectoryId": {
                            "type": "string",
                            "description": "Child trajectory id for appendChild, advanceChild, or closeChild.",
                        },
                        "rangeStartEventId": {
                            "type": "string",
                            "description": "First event id in the same-lane continuous interval for packRange.",
                        },
                        "rangeEndEventId": {
                            "type": "string",
                            "description": "Last event id in the same-lane continuous interval for packRange.",
                        },
                        "packRanges": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "lane_id": {"type": "string"},
                                    "laneId": {"type": "string"},
                                    "range_start_event_id": {"type": "string"},
                                    "rangeStartEventId": {"type": "string"},
                                    "range_end_event_id": {"type": "string"},
                                    "rangeEndEventId": {"type": "string"},
                                },
                            },
                            "description": "Lane-local continuous ranges for packSubgraph.",
                        },
                        "anchorLaneId": {
                            "type": "string",
                            "description": "Selected anchor lane id for packSubgraph. Defaults to laneId or the first selected range lane.",
                        },
                        "sourceEndpointTrajectoryId": {
                            "type": "string",
                            "description": "Precise source endpoint trajectory id for cross-compound relate.",
                        },
                        "sourceEndpointEventId": {
                            "type": "string",
                            "description": "Precise source endpoint event id for cross-compound relate.",
                        },
                        "sourceEndpointParentEventId": {
                            "type": "string",
                            "description": "Immediate source compound parent event id for cross-compound relate.",
                        },
                        "sourceEndpointCompoundPath": {
                            "type": "string",
                            "description": "Slash-separated source compound path for cross-compound relate.",
                        },
                        "targetEndpointTrajectoryId": {
                            "type": "string",
                            "description": "Precise target endpoint trajectory id for cross-compound relate.",
                        },
                        "targetEndpointEventId": {
                            "type": "string",
                            "description": "Precise target endpoint event id for cross-compound relate.",
                        },
                        "targetEndpointParentEventId": {
                            "type": "string",
                            "description": "Immediate target compound parent event id for cross-compound relate.",
                        },
                        "targetEndpointCompoundPath": {
                            "type": "string",
                            "description": "Slash-separated target compound path for cross-compound relate.",
                        },
                        "sourceGraphId": {
                            "type": "string",
                            "description": "Global progress graph id for start or setAnchor. Provide with sourceNodeId, or omit both to start unanchored / clear the anchor.",
                        },
                        "sourceNodeId": {
                            "type": "string",
                            "description": "Global progress graph node id for start or setAnchor. Provide with sourceGraphId, or omit both to start unanchored / clear the anchor.",
                        },
                    },
                    "required": ["action"],
                },
            ),
            Tool(
                name="schedulerProjection",
                description=(
                    "Write a scheduler-derived Local Work Trajectory projection artifact. "
                    "Reads a scheduler snapshot plus optional scheduler/merge-gate JSONL "
                    "history logs, then writes .codex/progress-graph/scheduler-work-trajectory.json "
                    "by default. This is a read-only projection path and does not mutate "
                    "the agent-owned local-work-trajectory.json lifecycle artifact."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "schedulerEventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler task event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "mergeGateEventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler merge-gate event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "outputPath": {
                            "type": "string",
                            "description": "Optional output JSON path. Defaults to .codex/progress-graph/scheduler-work-trajectory.json.",
                        },
                        "trajectoryId": {
                            "type": "string",
                            "description": "Optional projected trajectory id.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional projected trajectory title.",
                        },
                        "guideContext": {
                            "type": "string",
                            "description": "Optional guide context stored on the projected trajectory.",
                        },
                        "sourceGraphId": {
                            "type": "string",
                            "description": "Optional owning progress graph id for the projection.",
                        },
                        "sourceNodeId": {
                            "type": "string",
                            "description": "Optional owning progress graph node id for the projection.",
                        },
                    },
                    "required": ["snapshotPath"],
                },
            ),
            Tool(
                name="schedulerSubmitTasks",
                description=(
                    "Submit structured scheduler task contracts into the scheduler-owned "
                    "snapshot and scheduler event log. This wraps the existing "
                    "scheduler_task_batch_submission ExchangeArtifact intake, appends "
                    "task_submitted events, and writes the scheduler snapshot. It does "
                    "not run tasks, refresh projection artifacts, or mutate the "
                    "agent-owned local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. If missing, submission starts from an empty SchedulerState. Relative paths resolve under the MCP project root.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Scheduler task event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "batch": {
                            "type": "object",
                            "description": (
                                "Optional scheduler_task_batch_submission payload using "
                                "scheduler_submission keys. CamelCase aliases are accepted."
                            ),
                        },
                        "batchId": {
                            "type": "string",
                            "description": "Batch id used when batch.batch_id is omitted.",
                        },
                        "tasks": {
                            "type": "array",
                            "description": (
                                "Task submission payloads. Each task uses the existing "
                                "scheduler_submission contract; camelCase aliases such as "
                                "taskId, contextScope, runtimeProvider, and outputArtifactId "
                                "are accepted."
                            ),
                            "items": {"type": "object"},
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional batch title.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Optional batch summary.",
                        },
                        "artifactId": {
                            "type": "string",
                            "description": "Optional source ExchangeArtifact id for this submission.",
                        },
                        "artifactVersion": {
                            "type": "string",
                            "description": "Optional source ExchangeArtifact version. Defaults to v1.",
                        },
                        "producer": {
                            "type": "string",
                            "description": "Producer stored on the source ExchangeArtifact. Defaults to schedulerSubmitTasks.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for the source log part and task_submitted events.",
                        },
                        "replaceExisting": {
                            "type": "boolean",
                            "description": "Whether submitted tasks may replace existing tasks with the same task_id. Default false.",
                        },
                    },
                    "required": ["snapshotPath", "eventLogPath"],
                },
            ),
            Tool(
                name="admitExchangeArtifact",
                description=(
                    "Admit one exact stored ExchangeArtifact scheduler submission into "
                    "scheduler snapshot/event-log state while recording the durable "
                    "admission ledger. Reuses the exact-version admission path and rejects "
                    "duplicate artifact/version admission by default before scheduler "
                    "mutation. This does not run providers, refresh scheduler projection, "
                    "mark exchange artifacts consumed, or mutate agent-owned "
                    "local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "artifactId": {
                            "type": "string",
                            "description": "Exact ExchangeArtifact id to admit.",
                        },
                        "version": {
                            "type": "string",
                            "description": "Exact ExchangeArtifact version to admit.",
                        },
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Scheduler task event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "artifactStorePath": {
                            "type": "string",
                            "description": "Optional ExchangeArtifact store path. Defaults to .codex/orchestration/exchange-artifacts.json.",
                        },
                        "admissionLedgerPath": {
                            "type": "string",
                            "description": "Optional admission ledger path. Defaults to .codex/orchestration/exchange-artifact-admissions.json.",
                        },
                        "allowDuplicateAdmission": {
                            "type": "boolean",
                            "description": "Explicitly allow re-admitting an already admitted exact artifact/version. Default false.",
                        },
                        "replaceExisting": {
                            "type": "boolean",
                            "description": "Whether admitted scheduler tasks may replace existing task ids. Separate from duplicate admission policy. Default false.",
                        },
                        "actor": {
                            "type": "string",
                            "description": "Actor recorded in the admission ledger. Defaults to mcp.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for scheduler task_submitted events.",
                        },
                    },
                    "required": ["artifactId", "version", "snapshotPath", "eventLogPath"],
                },
            ),
            Tool(
                name="schedulerRunOnceAndProject",
                description=(
                    "Run one bounded persisted scheduler pass with the built-in fake runtime "
                    "adapter, write the updated scheduler snapshot, and refresh the "
                    "scheduler-derived Local Work Trajectory projection. runtimeProvider "
                    "is accepted for forward compatibility but currently only 'fake' is "
                    "allowed; qoder and other real providers return a clear error until "
                    "host permission and adapter registry wiring are explicit. Requires "
                    "snapshotPath and eventLogPath; this does not mutate agent-owned "
                    "local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Scheduler task event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "mergeGateEventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler merge-gate event JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "outputPath": {
                            "type": "string",
                            "description": "Optional scheduler projection output JSON path. Defaults to .codex/progress-graph/scheduler-work-trajectory.json.",
                        },
                        "maxRuns": {
                            "type": "number",
                            "description": "Optional bounded maximum number of ready tasks to run.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp used for scheduler lifecycle events and fake runtime events.",
                        },
                        "runtimeProvider": {
                            "type": "string",
                            "description": (
                                "Optional runtime provider selector. Defaults to 'fake'. "
                                "Current MCP smoke path only accepts 'fake'; values such as "
                                "'qoder' are rejected with a provider guard error."
                            ),
                        },
                        "guideContext": {
                            "type": "string",
                            "description": "Optional guide context stored on the projected trajectory.",
                        },
                        "sourceGraphId": {
                            "type": "string",
                            "description": "Optional owning progress graph id for the projection.",
                        },
                        "sourceNodeId": {
                            "type": "string",
                            "description": "Optional owning progress graph node id for the projection.",
                        },
                    },
                    "required": ["snapshotPath", "eventLogPath"],
                },
            ),
            Tool(
                name="schedulerAuthorizationReadback",
                description=(
                    "Read-only scheduler authorization diagnostics over edit lease "
                    "declarations, scheduler-owned edit lease lifecycle records, and "
                    "metadata-only shared-process sandbox mount authorization. Reads "
                    "a scheduler snapshot plus optional scheduler event log recovery; "
                    "does not run providers, mutate scheduler state, refresh projection, "
                    "or mutate agent-owned local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "schedulerEventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler task event JSONL path. Relative paths resolve under the MCP project root and is replayed through the existing recovery path.",
                        },
                        "strict": {
                            "type": "boolean",
                            "description": "Whether event-log replay should reject unknown task events. Default true.",
                        },
                        "workspaceRoot": {
                            "type": "string",
                            "description": "Optional workspace root recorded in sandbox metadata readback. Defaults to the MCP project root.",
                        },
                        "scratchRoot": {
                            "type": "string",
                            "description": "Optional scratch root used only to compute readback scratch paths. Defaults to .codex/scratch.",
                        },
                    },
                    "required": ["snapshotPath"],
                },
            ),
            Tool(
                name="schedulerCleanupReceipts",
                description=(
                    "Explicitly clean cleanup-required git-worktree sandbox "
                    "allocations recorded in one durable sandbox allocation receipt "
                    "evidence artifact. Writes updated receipt evidence and returns "
                    "cleanup command receipt summaries. This does not mutate scheduler "
                    "state, run host tasks, refresh projection, start a daemon, or "
                    "mutate agent-owned local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "inputEvidencePath": {
                            "type": "string",
                            "description": "Input sandbox_allocation_receipt_evidence JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "outputEvidencePath": {
                            "type": "string",
                            "description": "Optional output evidence path. Relative paths resolve under the MCP project root.",
                        },
                        "outputEvidenceId": {
                            "type": "string",
                            "description": "Optional output evidence id. Defaults to '<input evidence id>:cleanup'.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for the cleanup evidence.",
                        },
                        "gitExecutable": {
                            "type": "string",
                            "description": "Optional git executable path/name. Defaults to git.",
                        },
                    },
                    "required": ["inputEvidencePath"],
                },
            ),
            Tool(
                name="schedulerOperatorWorkflow",
                description=(
                    "Run the explicit shared scheduler operator workflow: inspect "
                    "ExchangeArtifact scheduler-admission candidates, optionally admit "
                    "one exact artifact version, optionally run a bounded fake-runtime "
                    "scheduler loop with durable evidence, optionally refresh the "
                    "scheduler-derived projection, then read Host Evidence presentation. "
                    "Mutating steps are opt-in via admit/runLoop/refreshProjection; "
                    "this does not mutate agent-owned Local Work Trajectory."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "artifactId": {
                            "type": "string",
                            "description": "Exact ExchangeArtifact id to admit when admit=true.",
                        },
                        "version": {
                            "type": "string",
                            "description": "Exact ExchangeArtifact version to admit when admit=true.",
                        },
                        "admit": {
                            "type": "boolean",
                            "description": "Whether to admit the exact artifact/version. Default false.",
                        },
                        "runLoop": {
                            "type": "boolean",
                            "description": "Whether to run a bounded fake scheduler loop. Default false.",
                        },
                        "refreshProjection": {
                            "type": "boolean",
                            "description": "Whether to refresh scheduler-derived trajectory projection. Default false.",
                        },
                        "artifactStorePath": {
                            "type": "string",
                            "description": "Optional ExchangeArtifact store path.",
                        },
                        "admissionLedgerPath": {
                            "type": "string",
                            "description": "Optional admission ledger path.",
                        },
                        "snapshotPath": {
                            "type": "string",
                            "description": "Optional scheduler snapshot path. Defaults under .codex/scheduler.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler event log path. Defaults under .codex/scheduler.",
                        },
                        "mergeGateEventLogPath": {
                            "type": "string",
                            "description": "Optional scheduler merge-gate event log path.",
                        },
                        "projectionOutputPath": {
                            "type": "string",
                            "description": "Optional scheduler projection output path.",
                        },
                        "evidenceId": {
                            "type": "string",
                            "description": "Optional scheduler-loop evidence id when runLoop=true.",
                        },
                        "evidencePath": {
                            "type": "string",
                            "description": "Optional scheduler-loop evidence output path.",
                        },
                        "runtimeProvider": {
                            "type": "string",
                            "description": "Runtime provider selector. Current workflow only supports 'fake'.",
                        },
                        "maxTicks": {
                            "type": "integer",
                            "description": "Bounded loop max ticks. Default 3.",
                        },
                        "maxRunsPerTick": {
                            "type": "integer",
                            "description": "Bounded loop max task runs per tick. Default 1.",
                        },
                        "maxRuntimeFailures": {
                            "type": "integer",
                            "description": "Runtime failure stop threshold. Default 1.",
                        },
                        "allowDuplicateAdmission": {
                            "type": "boolean",
                            "description": "Allow duplicate exact artifact/version admission. Default false.",
                        },
                        "replaceExisting": {
                            "type": "boolean",
                            "description": "Allow admitted scheduler tasks to replace existing task ids. Default false.",
                        },
                        "actor": {
                            "type": "string",
                            "description": "Actor recorded in admission ledger. Defaults to mcp.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for scheduler and evidence events.",
                        },
                        "guideContext": {
                            "type": "string",
                            "description": "Optional guide context stored on the projection.",
                        },
                        "sourceGraphId": {
                            "type": "string",
                            "description": "Optional owning progress graph id for projection.",
                        },
                        "sourceNodeId": {
                            "type": "string",
                            "description": "Optional owning progress graph node id for projection.",
                        },
                    },
                },
            ),
            Tool(
                name="schedulerSandboxReceiptWorkflow",
                description=(
                    "Run the host sandbox receipt workflow: host allocation, durable "
                    "sandbox allocation receipt evidence readback, optional explicit "
                    "cleanup, and post-cleanup Host Evidence readback. Supports "
                    "run-once and daemon-loop modes over fake runtime wiring. Cleanup "
                    "runs only when cleanup=true. This does not refresh projection, "
                    "start a daemon service, run real providers, mutate "
                    "ExchangeArtifact/admission ledger state, or mutate agent-owned "
                    "local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "description": "Workflow mode: run-once or daemon-loop.",
                        },
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Scheduler event log JSONL path. Relative paths resolve under the MCP project root.",
                        },
                        "workspaceRoot": {
                            "type": "string",
                            "description": "Source git repository root for git-worktree allocation. Relative paths resolve under the MCP project root.",
                        },
                        "gitWorktreeSandboxRoot": {
                            "type": "string",
                            "description": "Git-worktree sandbox root. Relative paths resolve under the MCP project root.",
                        },
                        "allocationEvidenceId": {
                            "type": "string",
                            "description": "Required sandbox_allocation_receipt_evidence id.",
                        },
                        "allocationEvidencePath": {
                            "type": "string",
                            "description": "Optional allocation evidence output path.",
                        },
                        "cleanup": {
                            "type": "boolean",
                            "description": "Whether to run explicit cleanup. Default false.",
                        },
                        "cleanupEvidenceId": {
                            "type": "string",
                            "description": "Optional cleanup evidence id. Requires cleanup=true.",
                        },
                        "cleanupEvidencePath": {
                            "type": "string",
                            "description": "Optional cleanup evidence output path. Requires cleanup=true.",
                        },
                        "runtimeProvider": {
                            "type": "string",
                            "description": "Runtime provider selector. Current tool only supports fake.",
                        },
                        "maxRuns": {
                            "type": "integer",
                            "description": "run-once max runs. Default 1.",
                        },
                        "maxTicks": {
                            "type": "integer",
                            "description": "daemon-loop max ticks. Default 1.",
                        },
                        "maxRunsPerTick": {
                            "type": "integer",
                            "description": "daemon-loop max task runs per tick. Default 1.",
                        },
                        "maxRuntimeFailures": {
                            "type": "integer",
                            "description": "daemon-loop runtime failure stop threshold. Default 1.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for scheduler and evidence events.",
                        },
                        "gitExecutable": {
                            "type": "string",
                            "description": "Optional git executable path/name. Defaults to git.",
                        },
                    },
                    "required": [
                        "mode",
                        "snapshotPath",
                        "eventLogPath",
                        "workspaceRoot",
                        "gitWorktreeSandboxRoot",
                        "allocationEvidenceId",
                    ],
                },
            ),
            Tool(
                name="schedulerLifecycleControl",
                description=(
                    "Read or mutate the scheduler daemon lifecycle control file. "
                    "Actions are deterministic control-file operations only: inspect, "
                    "start, heartbeat, pause, resume, cancel, shutdown, and mark_stale. "
                    "This does not run providers, refresh scheduler projection, mutate "
                    "ExchangeArtifact/admission ledger state, or mutate agent-owned "
                    "local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Lifecycle action: inspect, start, heartbeat, pause, resume, cancel, shutdown, or mark_stale.",
                        },
                        "controlPath": {
                            "type": "string",
                            "description": "Scheduler daemon lifecycle control JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "snapshotPath": {
                            "type": "string",
                            "description": "Scheduler state snapshot JSON path. Required for action=start.",
                        },
                        "eventLogPath": {
                            "type": "string",
                            "description": "Scheduler task event JSONL path. Required for action=start.",
                        },
                        "daemonId": {
                            "type": "string",
                            "description": "Daemon owner id. Required for action=start.",
                        },
                        "runId": {
                            "type": "string",
                            "description": "Optional lifecycle run id stored in the control file.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for lifecycle transitions.",
                        },
                        "staleAfterSeconds": {
                            "type": "integer",
                            "description": "Optional heartbeat stale threshold in seconds.",
                        },
                        "nowEpochSeconds": {
                            "type": "integer",
                            "description": "Optional deterministic current epoch seconds for stale inspection.",
                        },
                    },
                    "required": ["action", "controlPath"],
                },
            ),
            Tool(
                name="schedulerLifecycleRunOnce",
                description=(
                    "Run one lifecycle-gated bounded scheduler daemon loop using the "
                    "built-in fake runtime only. The lifecycle control must already be "
                    "running; paused/cancelled/stopped/stale controls skip scheduler "
                    "mutation, and cancellation is consumed before provider execution. "
                    "This does not refresh scheduler projection, mutate ExchangeArtifact/"
                    "admission ledger state, or mutate agent-owned local-work-trajectory.json."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "controlPath": {
                            "type": "string",
                            "description": "Scheduler daemon lifecycle control JSON path. Relative paths resolve under the MCP project root.",
                        },
                        "runtimeProvider": {
                            "type": "string",
                            "description": "Runtime provider selector. Defaults to 'fake'; only 'fake' is accepted in this MCP surface.",
                        },
                        "timestamp": {
                            "type": "string",
                            "description": "Optional timestamp for the lifecycle-gated run.",
                        },
                        "maxTicks": {
                            "type": "integer",
                            "description": "Bounded loop max ticks. Default 1.",
                        },
                        "maxRunsPerTick": {
                            "type": "integer",
                            "description": "Bounded loop max task runs per tick. Default 1.",
                        },
                        "maxRuntimeFailures": {
                            "type": "integer",
                            "description": "Runtime failure stop threshold. Default 1.",
                        },
                    },
                    "required": ["controlPath"],
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
                action_type=arguments.get("action_type", ""),
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
                has_merge_conflicts=arguments.get("has_merge_conflicts"),
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
        elif name == "workflow_interrupt":
            result = tools.workflow_interrupt(
                reason=arguments["reason"],
                discovered_item=arguments["discovered_item"],
                current_scope_ref=arguments.get("current_scope_ref", ""),
            )
        elif name == "update_user_config":
            from ..pack.user_config import save_user_config
            from ..workflow.pipeline import _user_global_base_dir

            try:
                user_dir = _user_global_base_dir()
                result = save_user_config(
                    user_dir,
                    field=arguments["field"],
                    value=arguments["value"],
                )
            except (ValueError, OSError) as exc:
                result = {"error": str(exc)}
        elif name == "pack_lock":
            result = tools.pack_lock(pack_name=arguments.get("pack_name", ""))
        elif name == "pack_unlock":
            result = tools.pack_unlock(pack_name=arguments["pack_name"])
        elif name == "pack_verify":
            result = tools.pack_verify(pack_name=arguments.get("pack_name", ""))
        elif name == "check_reply_progression":
            from ..workflow.reply_progression import check_reply_progression
            result = check_reply_progression(arguments["reply_text"]).to_dict()
        elif name == "localTrajectory":
            result = tools.local_trajectory(
                arguments["action"],
                lane_label=arguments.get("laneLabel", ""),
                first_event_title=arguments.get("firstEventTitle", ""),
                title=arguments.get("title", ""),
                event_kind=arguments.get("eventKind", ""),
                summary=arguments.get("summary", ""),
                guide_context=arguments.get("guideContext", ""),
                current_event_id=arguments.get("currentEventId", ""),
                reason=arguments.get("reason", ""),
                lane_id=arguments.get("laneId", ""),
                lanes=arguments.get("lanes"),
                source_event_id=arguments.get("sourceEventId", ""),
                source_lane_id=arguments.get("sourceLaneId", ""),
                target_lane_id=arguments.get("targetLaneId", ""),
                target_event_id=arguments.get("targetEventId", ""),
                relation_kind=arguments.get("relationKind", ""),
                first_child_event_title=arguments.get("firstChildEventTitle", ""),
                child_lane_label=arguments.get("childLaneLabel", ""),
                range_start_event_id=arguments.get("rangeStartEventId", ""),
                range_end_event_id=arguments.get("rangeEndEventId", ""),
                pack_ranges=arguments.get("packRanges"),
                anchor_lane_id=arguments.get("anchorLaneId", ""),
                parent_event_id=arguments.get("parentEventId", ""),
                child_trajectory_id=arguments.get("childTrajectoryId", ""),
                source_endpoint_trajectory_id=arguments.get("sourceEndpointTrajectoryId", ""),
                source_endpoint_event_id=arguments.get("sourceEndpointEventId", ""),
                source_endpoint_parent_event_id=arguments.get("sourceEndpointParentEventId", ""),
                source_endpoint_compound_path=arguments.get("sourceEndpointCompoundPath", ""),
                target_endpoint_trajectory_id=arguments.get("targetEndpointTrajectoryId", ""),
                target_endpoint_event_id=arguments.get("targetEndpointEventId", ""),
                target_endpoint_parent_event_id=arguments.get("targetEndpointParentEventId", ""),
                target_endpoint_compound_path=arguments.get("targetEndpointCompoundPath", ""),
                source_graph_id=arguments.get("sourceGraphId", ""),
                source_node_id=arguments.get("sourceNodeId", ""),
            )
        elif name == "schedulerProjection":
            result = tools.scheduler_projection(
                snapshot_path=arguments.get("snapshotPath", ""),
                scheduler_event_log_path=arguments.get("schedulerEventLogPath", ""),
                merge_gate_event_log_path=arguments.get("mergeGateEventLogPath", ""),
                output_path=arguments.get("outputPath", ""),
                trajectory_id=arguments.get("trajectoryId", ""),
                title=arguments.get("title", ""),
                guide_context=arguments.get("guideContext", ""),
                source_graph_id=arguments.get("sourceGraphId", ""),
                source_node_id=arguments.get("sourceNodeId", ""),
            )
        elif name == "schedulerSubmitTasks":
            result = tools.scheduler_submit_tasks(
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                batch=arguments.get("batch"),
                batch_id=arguments.get("batchId", ""),
                tasks=arguments.get("tasks"),
                title=arguments.get("title", ""),
                summary=arguments.get("summary", ""),
                artifact_id=arguments.get("artifactId", ""),
                artifact_version=arguments.get("artifactVersion", "v1"),
                producer=arguments.get("producer", "schedulerSubmitTasks"),
                timestamp=arguments.get("timestamp", ""),
                replace_existing=arguments.get("replaceExisting", False),
            )
        elif name == "admitExchangeArtifact":
            result = tools.admit_exchange_artifact(
                artifact_id=arguments.get("artifactId", ""),
                version=arguments.get("version", ""),
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                artifact_store_path=arguments.get("artifactStorePath", ""),
                admission_ledger_path=arguments.get("admissionLedgerPath", ""),
                allow_duplicate_admission=arguments.get("allowDuplicateAdmission", False),
                replace_existing=arguments.get("replaceExisting", False),
                actor=arguments.get("actor", "mcp"),
                timestamp=arguments.get("timestamp", ""),
            )
        elif name == "schedulerRunOnceAndProject":
            result = tools.scheduler_run_once_and_project(
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                merge_gate_event_log_path=arguments.get("mergeGateEventLogPath", ""),
                output_path=arguments.get("outputPath", ""),
                max_runs=arguments.get("maxRuns"),
                timestamp=arguments.get("timestamp", ""),
                runtime_provider=arguments.get("runtimeProvider", "fake"),
                guide_context=arguments.get("guideContext", ""),
                source_graph_id=arguments.get("sourceGraphId", ""),
                source_node_id=arguments.get("sourceNodeId", ""),
            )
        elif name == "schedulerAuthorizationReadback":
            result = tools.scheduler_authorization_readback(
                snapshot_path=arguments.get("snapshotPath", ""),
                scheduler_event_log_path=arguments.get("schedulerEventLogPath", ""),
                strict=arguments.get("strict", True),
                workspace_root=arguments.get("workspaceRoot", ""),
                scratch_root=arguments.get("scratchRoot", ".codex/scratch"),
            )
        elif name == "schedulerCleanupReceipts":
            result = tools.scheduler_cleanup_receipts(
                input_evidence_path=arguments.get("inputEvidencePath", ""),
                output_evidence_path=arguments.get("outputEvidencePath", ""),
                output_evidence_id=arguments.get("outputEvidenceId", ""),
                timestamp=arguments.get("timestamp", ""),
                git_executable=arguments.get("gitExecutable", "git"),
            )
        elif name == "schedulerOperatorWorkflow":
            result = tools.scheduler_operator_workflow(
                artifact_id=arguments.get("artifactId", ""),
                version=arguments.get("version", ""),
                admit=arguments.get("admit", False),
                run_loop=arguments.get("runLoop", False),
                refresh_projection=arguments.get("refreshProjection", False),
                artifact_store_path=arguments.get("artifactStorePath", ""),
                admission_ledger_path=arguments.get("admissionLedgerPath", ""),
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                merge_gate_event_log_path=arguments.get("mergeGateEventLogPath", ""),
                projection_output_path=arguments.get("projectionOutputPath", ""),
                evidence_id=arguments.get("evidenceId", ""),
                evidence_path=arguments.get("evidencePath", ""),
                runtime_provider=arguments.get("runtimeProvider", "fake"),
                max_ticks=arguments.get("maxTicks", 3),
                max_runs_per_tick=arguments.get("maxRunsPerTick", 1),
                max_runtime_failures=arguments.get("maxRuntimeFailures", 1),
                allow_duplicate_admission=arguments.get("allowDuplicateAdmission", False),
                replace_existing=arguments.get("replaceExisting", False),
                actor=arguments.get("actor", "mcp"),
                timestamp=arguments.get("timestamp", ""),
                guide_context=arguments.get("guideContext", ""),
                source_graph_id=arguments.get("sourceGraphId", ""),
                source_node_id=arguments.get("sourceNodeId", ""),
            )
        elif name == "schedulerSandboxReceiptWorkflow":
            result = tools.scheduler_sandbox_receipt_workflow(
                mode=arguments.get("mode", ""),
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                workspace_root=arguments.get("workspaceRoot", ""),
                git_worktree_sandbox_root=arguments.get("gitWorktreeSandboxRoot", ""),
                allocation_evidence_id=arguments.get("allocationEvidenceId", ""),
                allocation_evidence_path=arguments.get("allocationEvidencePath", ""),
                cleanup=arguments.get("cleanup", False),
                cleanup_evidence_id=arguments.get("cleanupEvidenceId", ""),
                cleanup_evidence_path=arguments.get("cleanupEvidencePath", ""),
                runtime_provider=arguments.get("runtimeProvider", "fake"),
                max_runs=arguments.get("maxRuns", 1),
                max_ticks=arguments.get("maxTicks", 1),
                max_runs_per_tick=arguments.get("maxRunsPerTick", 1),
                max_runtime_failures=arguments.get("maxRuntimeFailures", 1),
                timestamp=arguments.get("timestamp", ""),
                git_executable=arguments.get("gitExecutable", "git"),
            )
        elif name == "schedulerLifecycleControl":
            result = tools.scheduler_lifecycle_control(
                action=arguments.get("action", ""),
                control_path=arguments.get("controlPath", ""),
                snapshot_path=arguments.get("snapshotPath", ""),
                event_log_path=arguments.get("eventLogPath", ""),
                daemon_id=arguments.get("daemonId", ""),
                run_id=arguments.get("runId", ""),
                timestamp=arguments.get("timestamp", ""),
                stale_after_seconds=arguments.get("staleAfterSeconds"),
                now_epoch_seconds=arguments.get("nowEpochSeconds"),
            )
        elif name == "schedulerLifecycleRunOnce":
            result = tools.scheduler_lifecycle_run_once(
                control_path=arguments.get("controlPath", ""),
                runtime_provider=arguments.get("runtimeProvider", "fake"),
                timestamp=arguments.get("timestamp", ""),
                max_ticks=arguments.get("maxTicks", 1),
                max_runs_per_tick=arguments.get("maxRunsPerTick", 1),
                max_runtime_failures=arguments.get("maxRuntimeFailures", 1),
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
