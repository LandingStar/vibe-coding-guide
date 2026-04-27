"""Project doc-loop sources -> progress graph projection."""

from __future__ import annotations

import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path

from src.workflow.checkpoint import read_checkpoint

from .model import (
    CrossGraphEdge,
    ProgressEdge,
    ProgressGraph,
    ProgressMultiGraphHistory,
    ProgressNode,
)

_DEFAULT_HISTORY_PATH = Path(".codex/progress-graph/latest.json")
_PHASE_MAP_PATH = Path("design_docs/Global Phase Map and Current Position.md")
_GLOBAL_DIRECTION_CANDIDATES_PATH = Path("design_docs/direction-candidates-after-phase-35.md")
_RESEARCH_COMPASS_PATH = Path("review/research-compass.md")
_DEFAULT_DIRECTION_ANALYSIS_PATH = Path(
    "design_docs/project-progress-phase-map-projection-followup-direction-analysis.md"
)
_EMPTY_ACTIVE_SLICE_MARKERS = (
    "no active planning-gate",
    "no active planning gate",
    "无 active planning-gate",
    "无 active planning gate",
)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$")
_PHASE_MAP_ENTRY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+(.+)$")
_PLANNING_GATE_REF_RE = re.compile(r"(design_docs/stages/planning-gate/[^\s`'\"，。；]+\.md)")
_DIRECTION_CANDIDATE_HEADING_RE = re.compile(r"^###\s+([A-Z])\.\s+(.+)$")
_DIRECTION_RECOMMENDED_RE = re.compile(r"(?:新)?候选\s+([A-Z])")
_GLOBAL_DIRECTION_CANDIDATE_RE = re.compile(r"^- 候选\s+(\d+)：`?([^`]+?)`?\s*$")
_GLOBAL_DIRECTION_LETTERED_CANDIDATE_RE = re.compile(r"^###\s+((?:新候选)\s+)?([A-Z])\.\s+(.+)$")
_GLOBAL_DIRECTION_RECOMMENDED_RE = re.compile(r"候选\s+(\d+)")
_GLOBAL_DIRECTION_SECTION_DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\b")
_DOC_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_DOC_LINK_WITH_LABEL_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BACKTICK_REF_RE = re.compile(r"`([^`]+)`")
_PROJECT_PROGRESS_FOLLOWUP_PATH_RE = re.compile(
    r"design_docs/project-progress-[^`\s)]+followup-direction-analysis\.md"
)
_RECENT_PHASE_MAP_ENTRY_LIMIT = 8


def history_json_path(project_root: str | Path) -> Path:
    return Path(project_root) / _DEFAULT_HISTORY_PATH


def load_doc_progress_history(project_root: str | Path) -> ProgressMultiGraphHistory:
    path = history_json_path(project_root)
    if not path.exists():
        return ProgressMultiGraphHistory(metadata={"source": "doc-loop"})
    return ProgressMultiGraphHistory.from_json(path.read_text(encoding="utf-8"))


def write_doc_progress_history(
    project_root: str | Path,
    *,
    history: ProgressMultiGraphHistory | None = None,
) -> Path:
    root = Path(project_root)
    built = build_doc_progress_history(root, history=history)
    path = history_json_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(built.to_json(), encoding="utf-8")
    return path


def build_doc_progress_history(
    project_root: str | Path,
    *,
    history: ProgressMultiGraphHistory | None = None,
) -> ProgressMultiGraphHistory:
    root = Path(project_root)
    built = history or load_doc_progress_history(root)
    recorded_at = datetime.now(timezone.utc).isoformat()
    snapshot_label = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

    checkpoint_graph = build_checkpoint_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("checkpoint-current"),
        recorded_at=recorded_at,
    )
    planning_gate_graph = build_planning_gate_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("planning-gates-index"),
        recorded_at=recorded_at,
    )
    phase_map_graph = build_phase_map_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("phase-map-current-position"),
        recorded_at=recorded_at,
    )
    direction_analysis_graph = build_direction_analysis_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("direction-analysis-current"),
        recorded_at=recorded_at,
    )
    global_direction_candidates_graph = build_global_direction_candidates_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("direction-candidates-global"),
        recorded_at=recorded_at,
    )
    checklist_graph = build_checklist_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("project-checklist-current"),
        recorded_at=recorded_at,
    )
    research_compass_graph = build_research_compass_graph(
        root,
        snapshot_label=snapshot_label,
        parent_snapshot_id=built.current_snapshot_by_graph.get("research-compass-current"),
        recorded_at=recorded_at,
    )

    built.add_snapshot(checkpoint_graph)
    built.add_snapshot(planning_gate_graph)
    built.add_snapshot(phase_map_graph)
    built.add_snapshot(direction_analysis_graph)
    built.add_snapshot(global_direction_candidates_graph)
    built.add_snapshot(checklist_graph)
    built.add_snapshot(research_compass_graph)
    built.metadata.update(
        {
            "source": "doc-loop",
            "latest_projection_at": recorded_at,
            "history_path": _DEFAULT_HISTORY_PATH.as_posix(),
        }
    )
    built.cross_graph_edges = _build_cross_graph_edges(
        checkpoint_graph,
        planning_gate_graph,
        phase_map_graph,
        direction_analysis_graph,
        global_direction_candidates_graph,
        checklist_graph,
        research_compass_graph,
    )
    built.validate()
    return built


def build_checkpoint_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    checkpoint_path = root / ".codex/checkpoints/latest.md"
    data = read_checkpoint(checkpoint_path)
    graph = ProgressGraph(
        graph_id="checkpoint-current",
        snapshot_id=f"{snapshot_label}-checkpoint-current",
        parent_snapshot_id=parent_snapshot_id,
        title="Checkpoint Current",
        recorded_at=recorded_at or data.get("timestamp", ""),
        metadata={
            "source_path": checkpoint_path.relative_to(root).as_posix(),
            "phase": str(data.get("phase", "")),
            "planning_gate": str(data.get("planning_gate", "")),
            "pending_decision": str(data.get("pending_decision", "")),
        },
    )

    phase = str(data.get("phase", "")).strip()
    if phase:
        graph.add_node(
            ProgressNode(
                id="milestone:current-phase",
                title=phase,
                kind="milestone",
                status="in_progress",
                metadata={"source_section": "Current Phase"},
            )
        )

    active_gate = str(data.get("planning_gate", "")).strip()
    if active_gate:
        graph.add_node(
            ProgressNode(
                id="reference:active-planning-gate",
                title=active_gate,
                kind="reference",
                status="in_progress",
                metadata={"source_section": "Active Planning Gate"},
            )
        )

    pending_decision = str(data.get("pending_decision", "")).strip()
    if pending_decision:
        graph.add_node(
            ProgressNode(
                id="decision:pending-user",
                title=pending_decision,
                kind="decision",
                status="pending",
                metadata={"source_section": "Pending User Decision"},
            )
        )

    previous_todo_id: str | None = None
    for index, todo in enumerate(data.get("todos", []), start=1):
        node_id = f"todo:{index:03d}"
        graph.add_node(
            ProgressNode(
                id=node_id,
                title=str(todo.get("title", "")),
                status=_map_checkbox_status(str(todo.get("status", "not-started"))),
                metadata={
                    "source_section": "Current Todo",
                    "position": str(index),
                },
            )
        )
        if previous_todo_id:
            graph.add_edge(
                ProgressEdge(
                    source=previous_todo_id,
                    target=node_id,
                    kind="workflow",
                )
            )
        previous_todo_id = node_id

    return graph


def build_planning_gate_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    planning_dir = root / "design_docs/stages/planning-gate"
    graph = ProgressGraph(
        graph_id="planning-gates-index",
        snapshot_id=f"{snapshot_label}-planning-gates-index",
        parent_snapshot_id=parent_snapshot_id,
        title="Planning Gates Index",
        recorded_at=recorded_at,
        metadata={"source_dir": planning_dir.relative_to(root).as_posix()},
    )

    for path in sorted(planning_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        relative_path = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        title = _extract_title(text) or path.stem
        status_raw = _extract_gate_status(text)
        graph.add_node(
            ProgressNode(
                id=relative_path,
                title=title,
                kind="task",
                status=_map_gate_status(status_raw),
                metadata={
                    "source_path": relative_path,
                    "status_raw": status_raw,
                    "date_hint": _extract_date_hint(path.name),
                },
            )
        )

    return graph


def build_phase_map_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    phase_map_path = root / _PHASE_MAP_PATH
    graph = ProgressGraph(
        graph_id="phase-map-current-position",
        snapshot_id=f"{snapshot_label}-phase-map-current-position",
        parent_snapshot_id=parent_snapshot_id,
        title="Global Phase Map Current Position",
        recorded_at=recorded_at,
        metadata={"source_path": phase_map_path.relative_to(root).as_posix()},
    )
    if not phase_map_path.exists():
        return graph

    text = phase_map_path.read_text(encoding="utf-8")
    source_node_id = "reference:source-document"
    graph.add_node(
        ProgressNode(
            id=source_node_id,
            title=phase_map_path.relative_to(root).as_posix(),
            kind="reference",
            status="completed",
            metadata={
                "source_section": "source-document",
                "source_path": phase_map_path.relative_to(root).as_posix(),
            },
        )
    )
    first_event_node_id: str | None = None
    previous_node_id: str | None = None
    for index, entry in enumerate(_parse_recent_phase_map_entries(text), start=1):
        node_id = f"event:{index:03d}"
        if first_event_node_id is None:
            first_event_node_id = node_id
        graph.add_node(
            ProgressNode(
                id=node_id,
                title=entry["title"],
                kind="milestone",
                status="completed",
                summary=entry["summary"],
                metadata={
                    "source_section": "recent-history",
                    "source_path": phase_map_path.relative_to(root).as_posix(),
                    "date": entry["date"],
                    "position": str(index),
                    "planning_gate_refs": "|".join(entry["planning_gate_refs"]),
                },
            )
        )
        if previous_node_id:
            graph.add_edge(
                ProgressEdge(
                    source=previous_node_id,
                    target=node_id,
                    kind="workflow",
                )
            )
        previous_node_id = node_id

        if first_event_node_id:
            graph.add_edge(
                ProgressEdge(
                    source=source_node_id,
                    target=first_event_node_id,
                    kind="reference",
                )
            )

    return graph


def build_checklist_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    checklist_path = root / "design_docs/Project Master Checklist.md"
    text = checklist_path.read_text(encoding="utf-8")
    snapshot_fields = _parse_bullet_fields(_extract_section(text, "当前快照"))
    active_todo_section = _extract_section(text, "活跃待办")
    graph = ProgressGraph(
        graph_id="project-checklist-current",
        snapshot_id=f"{snapshot_label}-project-checklist-current",
        parent_snapshot_id=parent_snapshot_id,
        title="Project Checklist Current",
        recorded_at=recorded_at,
        metadata={
            "source_path": checklist_path.relative_to(root).as_posix(),
            "snapshot_date": snapshot_fields.get("Snapshot Date", ""),
            "current_phase": snapshot_fields.get("Current Phase", ""),
            "safe_stop_status": snapshot_fields.get("Safe Stop Status", ""),
        },
    )

    source_node_id = "reference:source-document"
    graph.add_node(
        ProgressNode(
            id=source_node_id,
            title=checklist_path.relative_to(root).as_posix(),
            kind="reference",
            status="completed",
            metadata={
                "source_section": "source-document",
                "source_path": checklist_path.relative_to(root).as_posix(),
            },
        )
    )
    first_content_node_id: str | None = None

    current_phase = snapshot_fields.get("Current Phase", "").strip()
    if current_phase:
        if first_content_node_id is None:
            first_content_node_id = "milestone:current-phase"
        graph.add_node(
            ProgressNode(
                id="milestone:current-phase",
                title=current_phase,
                kind="milestone",
                status="in_progress",
                metadata={"source_section": "当前快照"},
            )
        )

    active_slice = snapshot_fields.get("Active Slice", "").strip()
    if active_slice:
        active_status = "pending" if _is_empty_active_slice(active_slice) else "in_progress"
        if first_content_node_id is None:
            first_content_node_id = "milestone:active-slice"
        graph.add_node(
            ProgressNode(
                id="milestone:active-slice",
                title=active_slice,
                kind="milestone",
                status=active_status,
                metadata={"source_section": "当前快照"},
            )
        )

    latest_completed = snapshot_fields.get("Latest Completed Slice", "").strip()
    if latest_completed:
        if first_content_node_id is None:
            first_content_node_id = "milestone:latest-completed-slice"
        graph.add_node(
            ProgressNode(
                id="milestone:latest-completed-slice",
                title=latest_completed,
                kind="milestone",
                status="completed",
                metadata={"source_section": "当前快照"},
            )
        )

    previous_todo_id: str | None = None
    for index, (title, status) in enumerate(_parse_checkbox_lines(active_todo_section), start=1):
        node_id = f"todo:{index:03d}"
        if first_content_node_id is None:
            first_content_node_id = node_id
        graph.add_node(
            ProgressNode(
                id=node_id,
                title=title,
                status=status,
                metadata={
                    "source_section": "活跃待办",
                    "position": str(index),
                },
            )
        )
        if previous_todo_id:
            graph.add_edge(
                ProgressEdge(
                    source=previous_todo_id,
                    target=node_id,
                    kind="workflow",
                )
            )
        previous_todo_id = node_id

        if first_content_node_id:
            graph.add_edge(
                ProgressEdge(
                    source=source_node_id,
                    target=first_content_node_id,
                    kind="reference",
                )
            )

    return graph


def build_research_compass_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    source_path = root / _RESEARCH_COMPASS_PATH
    graph = ProgressGraph(
        graph_id="research-compass-current",
        snapshot_id=f"{snapshot_label}-research-compass-current",
        parent_snapshot_id=parent_snapshot_id,
        title="Research Compass Current",
        recorded_at=recorded_at,
        metadata={"source_path": source_path.relative_to(root).as_posix()},
    )
    if not source_path.exists():
        return graph

    source_path_str = source_path.relative_to(root).as_posix()
    text = source_path.read_text(encoding="utf-8")
    graph.add_node(
        ProgressNode(
            id="reference:source-document",
            title=source_path_str,
            kind="reference",
            status="completed",
            metadata={
                "source_section": "source-document",
                "source_path": source_path_str,
            },
        )
    )

    entries = _parse_research_compass_entries(text, source_path=source_path_str)
    entry_paths = {str(entry["path"]) for entry in entries}
    topics = _parse_research_compass_topics(
        text,
        source_path=source_path_str,
        known_entry_paths=entry_paths,
    )
    graph.metadata.update(
        {
            "source_path": source_path_str,
            "entry_count": str(len(entries)),
            "topic_count": str(len(topics)),
        }
    )
    for entry in entries:
        node_id = str(entry["path"])
        graph.add_node(
            ProgressNode(
                id=node_id,
                title=str(entry["title"]),
                kind="reference",
                status="completed",
                summary=str(entry["summary"]),
                metadata={
                    "source_section": "全量研究地图",
                    "source_path": source_path_str,
                    "reference_path": node_id,
                    "relevance": str(entry["relevance"]),
                    "first_read_scenario": str(entry["first_read_scenario"]),
                },
            )
        )
        graph.add_edge(
            ProgressEdge(
                source="reference:source-document",
                target=node_id,
                kind="reference",
            )
        )

    for topic in topics:
        topic_id = _research_compass_topic_node_id(str(topic["title"]))
        graph.add_node(
            ProgressNode(
                id=topic_id,
                title=str(topic["title"]),
                kind="milestone",
                status="completed",
                summary=str(topic["summary"]),
                metadata={
                    "source_section": "按问题检索",
                    "source_path": source_path_str,
                    "reference_paths": "|".join(topic["reference_paths"]),
                    "reference_count": str(len(topic["reference_paths"])),
                },
            )
        )
        graph.add_edge(
            ProgressEdge(
                source="reference:source-document",
                target=topic_id,
                kind="reference",
            )
        )
        for reference_path in topic["reference_paths"]:
            if reference_path not in graph.nodes:
                continue
            graph.add_edge(
                ProgressEdge(
                    source=topic_id,
                    target=reference_path,
                    kind="reference",
                )
            )

    return graph


def build_global_direction_candidates_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    source_path = root / _GLOBAL_DIRECTION_CANDIDATES_PATH
    graph = ProgressGraph(
        graph_id="direction-candidates-global",
        snapshot_id=f"{snapshot_label}-direction-candidates-global",
        parent_snapshot_id=parent_snapshot_id,
        title="Global Direction Candidates",
        recorded_at=recorded_at,
        metadata={"source_path": source_path.relative_to(root).as_posix()},
    )
    if not source_path.exists():
        return graph

    text = source_path.read_text(encoding="utf-8")
    source_node_id = "reference:source-document"
    graph.add_node(
        ProgressNode(
            id=source_node_id,
            title=source_path.relative_to(root).as_posix(),
            kind="reference",
            status="completed",
            metadata={
                "source_section": "source-document",
                "source_path": source_path.relative_to(root).as_posix(),
            },
        )
    )
    sections = _parse_global_direction_candidate_sections(text)
    graph.metadata.update(
        {
            "source_path": source_path.relative_to(root).as_posix(),
            "section_count": str(len(sections)),
        }
    )
    previous_section_id: str | None = None
    latest_index = _select_latest_global_direction_candidate_section_index(sections)
    first_section_id: str | None = None
    for index, section in enumerate(sections, start=1):
        section_id = f"section:{index:03d}"
        if first_section_id is None:
            first_section_id = section_id
        status_mode = str(section["status_mode"])
        recency_date = _extract_global_direction_section_date(str(section["title"]))
        is_latest = latest_index is not None and index == latest_index and status_mode == "latest"
        section_status = "in_progress" if status_mode == "latest" and is_latest else "completed"
        graph.add_node(
            ProgressNode(
                id=section_id,
                title=str(section["title"]),
                kind="milestone",
                status=section_status,
                summary=str(section["completed_boundary"]),
                metadata={
                    "source_section": str(section["title"]),
                    "source_path": source_path.relative_to(root).as_posix(),
                    "position": str(index),
                    "recommended_candidate": str(section["recommended_candidate"]),
                    "current_preference": str(section["current_preference"]),
                    "status_mode": status_mode,
                    "recency_date": recency_date,
                    "is_latest": "true" if is_latest else "false",
                },
            )
        )
        if previous_section_id:
            graph.add_edge(
                ProgressEdge(
                    source=previous_section_id,
                    target=section_id,
                    kind="workflow",
                )
            )
        previous_section_id = section_id

        recommended_candidate = str(section["recommended_candidate"])
        for candidate in section["candidates"]:
            candidate_key = str(candidate["key"])
            candidate_id = f"{section_id}:candidate:{candidate_key}"
            if status_mode == "recommended":
                candidate_status = "in_progress" if bool(candidate["recommended"]) else "pending"
            elif is_latest:
                candidate_status = "in_progress" if candidate_key == recommended_candidate else "pending"
            else:
                candidate_status = "completed"
            graph.add_node(
                ProgressNode(
                    id=candidate_id,
                    title=f"{candidate['label']}. {candidate['title']}",
                    kind="decision",
                    status=candidate_status,
                    summary=str(candidate["action"]),
                    metadata={
                        "source_section": str(section["title"]),
                        "source_path": source_path.relative_to(root).as_posix(),
                        "candidate_key": candidate_key,
                        "candidate_number": candidate_key,
                        "recommended": "true" if bool(candidate["recommended"]) else "false",
                        "judgment": str(candidate.get("judgment", "")),
                        "action": str(candidate["action"]),
                        "basis_refs": "|".join(candidate["basis_refs"]),
                    },
                )
            )
            graph.add_edge(
                ProgressEdge(
                    source=section_id,
                    target=candidate_id,
                    kind="candidate",
                )
            )

    if first_section_id:
        graph.add_edge(
            ProgressEdge(
                source=source_node_id,
                target=first_section_id,
                kind="reference",
            )
        )

    return graph


def _select_latest_global_direction_candidate_section_index(
    sections: list[dict[str, object]],
) -> int | None:
    latest_sections: list[tuple[str, int, int]] = []
    for index, section in enumerate(sections, start=1):
        if str(section.get("status_mode")) != "latest":
            continue
        recency_date = _extract_global_direction_section_date(str(section.get("title", "")))
        latest_sections.append((recency_date, -index, index))
    if not latest_sections:
        return None
    return max(latest_sections)[2]


def _extract_global_direction_section_date(title: str) -> str:
    match = _GLOBAL_DIRECTION_SECTION_DATE_RE.match(title.strip())
    if not match:
        return ""
    return match.group(1)


def build_direction_analysis_graph(
    project_root: str | Path,
    *,
    snapshot_label: str,
    parent_snapshot_id: str | None = None,
    recorded_at: str = "",
) -> ProgressGraph:
    root = Path(project_root)
    analysis_path = root / _resolve_current_direction_analysis_path(root)
    graph = ProgressGraph(
        graph_id="direction-analysis-current",
        snapshot_id=f"{snapshot_label}-direction-analysis-current",
        parent_snapshot_id=parent_snapshot_id,
        title="Current Direction Analysis",
        recorded_at=recorded_at,
        metadata={"source_path": analysis_path.relative_to(root).as_posix()},
    )
    if not analysis_path.exists():
        return graph

    text = analysis_path.read_text(encoding="utf-8")
    title = _extract_title(text) or analysis_path.stem
    recommended_candidate = _extract_recommended_candidate_letter(text)
    graph.title = title
    graph.metadata.update(
        {
            "source_path": analysis_path.relative_to(root).as_posix(),
            "recommended_candidate": recommended_candidate,
        }
    )
    graph.add_node(
        ProgressNode(
            id="analysis:current",
            title=title,
            kind="decision",
            status="in_progress",
            summary="Current active follow-up direction analysis entry.",
            metadata={
                "source_path": analysis_path.relative_to(root).as_posix(),
                "recommended_candidate": recommended_candidate,
            },
        )
    )

    for candidate in _parse_direction_candidates(text):
        option = str(candidate["option"]).lower()
        node_id = f"candidate:{option}"
        is_recommended = option.upper() == recommended_candidate
        graph.add_node(
            ProgressNode(
                id=node_id,
                title=f"{candidate['option']}. {candidate['title']}",
                kind="decision",
                status="in_progress" if is_recommended else "pending",
                summary=str(candidate["action"]),
                metadata={
                    "source_section": "候选路线",
                    "source_path": analysis_path.relative_to(root).as_posix(),
                    "option": str(candidate["option"]),
                    "recommended": "true" if is_recommended else "false",
                    "action": str(candidate["action"]),
                    "judgment": str(candidate["judgment"]),
                    "basis_refs": "|".join(candidate["basis_refs"]),
                },
            )
        )
        graph.add_edge(
            ProgressEdge(
                source="analysis:current",
                target=node_id,
                kind="candidate",
            )
        )

    return graph


def _build_cross_graph_edges(
    checkpoint_graph: ProgressGraph,
    planning_gate_graph: ProgressGraph,
    phase_map_graph: ProgressGraph,
    direction_analysis_graph: ProgressGraph,
    global_direction_candidates_graph: ProgressGraph,
    checklist_graph: ProgressGraph,
    research_compass_graph: ProgressGraph,
) -> list[CrossGraphEdge]:
    edges: list[CrossGraphEdge] = []
    seen: set[tuple[str, str, str, str, str]] = set()

    def add_edge(edge: CrossGraphEdge) -> None:
        edge_key = (
            edge.source_graph_id,
            edge.source_node_id,
            edge.target_graph_id,
            edge.target_node_id,
            edge.kind,
        )
        if edge_key in seen:
            return
        seen.add(edge_key)
        edges.append(edge)

    gate_ref = checkpoint_graph.nodes.get("reference:active-planning-gate")
    if gate_ref and gate_ref.title in planning_gate_graph.nodes:
        add_edge(
            CrossGraphEdge(
                source_graph_id="checkpoint-current",
                source_node_id="reference:active-planning-gate",
                target_graph_id="planning-gates-index",
                target_node_id=gate_ref.title,
                kind="linkage",
            )
        )

    for node in phase_map_graph.nodes.values():
        planning_gate_refs = [
            ref
            for ref in node.metadata.get("planning_gate_refs", "").split("|")
            if ref
        ]
        for gate_path in planning_gate_refs:
            if gate_path not in planning_gate_graph.nodes:
                continue
            add_edge(
                CrossGraphEdge(
                    source_graph_id="phase-map-current-position",
                    source_node_id=node.id,
                    target_graph_id="planning-gates-index",
                    target_node_id=gate_path,
                    kind="linkage",
                )
            )

    doc_ref_targets = _build_doc_ref_target_map(
        phase_map_graph,
        direction_analysis_graph,
        global_direction_candidates_graph,
        checklist_graph,
        research_compass_graph,
    )
    for source_graph_id, graph in (
        ("direction-analysis-current", direction_analysis_graph),
        ("direction-candidates-global", global_direction_candidates_graph),
    ):
        for node in graph.nodes.values():
            basis_refs = [
                ref
                for ref in node.metadata.get("basis_refs", "").split("|")
                if ref
            ]
            for ref in basis_refs:
                if ref in planning_gate_graph.nodes:
                    add_edge(
                        CrossGraphEdge(
                            source_graph_id=source_graph_id,
                            source_node_id=node.id,
                            target_graph_id="planning-gates-index",
                            target_node_id=ref,
                            kind="linkage",
                        )
                    )
                    continue

                target = doc_ref_targets.get(ref)
                if not target or target[0] == source_graph_id:
                    continue
                add_edge(
                    CrossGraphEdge(
                        source_graph_id=source_graph_id,
                        source_node_id=node.id,
                        target_graph_id=target[0],
                        target_node_id=target[1],
                        kind="linkage",
                    )
                )
    return edges


def _build_doc_ref_target_map(
    phase_map_graph: ProgressGraph,
    direction_analysis_graph: ProgressGraph,
    global_direction_candidates_graph: ProgressGraph,
    checklist_graph: ProgressGraph,
    research_compass_graph: ProgressGraph,
) -> dict[str, tuple[str, str]]:
    mapping: dict[str, tuple[str, str]] = {}

    phase_map_source = str(phase_map_graph.metadata.get("source_path", ""))
    if phase_map_source and "reference:source-document" in phase_map_graph.nodes:
        mapping[phase_map_source] = ("phase-map-current-position", "reference:source-document")

    direction_analysis_source = str(direction_analysis_graph.metadata.get("source_path", ""))
    if direction_analysis_source and "analysis:current" in direction_analysis_graph.nodes:
        mapping[direction_analysis_source] = ("direction-analysis-current", "analysis:current")

    global_direction_source = str(global_direction_candidates_graph.metadata.get("source_path", ""))
    if global_direction_source and "reference:source-document" in global_direction_candidates_graph.nodes:
        mapping[global_direction_source] = ("direction-candidates-global", "reference:source-document")

    checklist_source = str(checklist_graph.metadata.get("source_path", ""))
    if checklist_source and "reference:source-document" in checklist_graph.nodes:
        mapping[checklist_source] = ("project-checklist-current", "reference:source-document")

    research_compass_source = str(research_compass_graph.metadata.get("source_path", ""))
    if research_compass_source and "reference:source-document" in research_compass_graph.nodes:
        mapping[research_compass_source] = ("research-compass-current", "reference:source-document")
    for node in research_compass_graph.nodes.values():
        reference_path = str(node.metadata.get("reference_path", ""))
        if reference_path:
            mapping[reference_path] = ("research-compass-current", node.id)

    return mapping


def _extract_title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _extract_date_hint(file_name: str) -> str:
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", file_name)
    return match.group(1) if match else ""


def _extract_gate_status(text: str) -> str:
    patterns = (
        re.compile(r"^[>\-\*\s]*状态:\s*\*{0,2}([^*`|]+?)\*{0,2}\s*$"),
        re.compile(r"^[>\-\*\s]*Status:\s*\*{0,2}([^*`|]+?)\*{0,2}(?:\s*\([^)]*\))?\s*$", re.IGNORECASE),
        re.compile(r"^\|\s*状态\s*\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|$"),
        re.compile(r"^\|\s*Status\s*\|\s*\*{0,2}([^|*]+?)\*{0,2}\s*\|$", re.IGNORECASE),
    )
    for line in text.splitlines()[:40]:
        stripped = line.strip()
        for pattern in patterns:
            match = pattern.match(stripped)
            if match:
                return match.group(1).strip().lower()
    return ""


def _map_gate_status(status_raw: str) -> str:
    normalized = status_raw.strip().lower()
    if normalized in {"active", "in-progress", "in progress"}:
        return "in_progress"
    if normalized in {"complete", "completed", "closed", "done"}:
        return "completed"
    if normalized in {"paused", "blocked"}:
        return "blocked"
    if normalized in {"approved", "draft"}:
        return "pending"
    return "pending"


def _map_checkbox_status(status_raw: str) -> str:
    normalized = status_raw.strip().lower()
    if normalized in {"done", "x", "complete", "completed", "closed"}:
        return "completed"
    if normalized in {"in-progress", "in progress", "-", "active"}:
        return "in_progress"
    if normalized in {"paused", "blocked"}:
        return "blocked"
    return "pending"


def _extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    target = heading.strip()
    start_index = -1
    heading_level = 0
    for index, line in enumerate(lines):
        match = _HEADING_RE.match(line.strip())
        if not match:
            continue
        if match.group(2).strip() == target:
            start_index = index + 1
            heading_level = len(match.group(1))
            break
    if start_index < 0:
        return ""

    collected: list[str] = []
    for line in lines[start_index:]:
        match = _HEADING_RE.match(line.strip())
        if match and len(match.group(1)) <= heading_level:
            break
        collected.append(line)
    return "\n".join(collected)


def _parse_bullet_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        key, _, value = stripped[2:].partition(":")
        if not key or not value:
            continue
        fields[key.strip()] = value.strip().strip("`")
    return fields


def _parse_checkbox_lines(text: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped.startswith("- ["):
            continue
        marker = stripped[3] if len(stripped) > 3 else " "
        title = stripped[6:].strip() if len(stripped) > 6 else ""
        items.append((title, _map_checkbox_status({"x": "done", "-": "in-progress"}.get(marker, "not-started"))))
    return items


def _parse_recent_phase_map_entries(text: str) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = _PHASE_MAP_ENTRY_RE.match(stripped)
        if not match:
            continue
        date_hint, raw_entry = match.groups()
        entry_text = raw_entry.strip()
        if not entry_text:
            continue
        entries.append(
            {
                "date": date_hint,
                "title": _summarize_phase_map_entry(entry_text),
                "summary": f"{date_hint} {entry_text}",
                "planning_gate_refs": _extract_planning_gate_refs(entry_text),
            }
        )
    if len(entries) <= _RECENT_PHASE_MAP_ENTRY_LIMIT:
        return entries
    return entries[-_RECENT_PHASE_MAP_ENTRY_LIMIT:]


def _summarize_phase_map_entry(entry_text: str) -> str:
    for separator in ("；", "。"):
        head, found, _ = entry_text.partition(separator)
        if found and head.strip():
            return head.strip()
    return entry_text.strip()


def _extract_planning_gate_refs(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in _PLANNING_GATE_REF_RE.finditer(text):
        gate_path = match.group(1)
        if gate_path in seen:
            continue
        seen.add(gate_path)
        refs.append(gate_path)
    return refs


def _parse_direction_candidates(text: str) -> list[dict[str, object]]:
    section = _extract_section(text, "候选路线")
    if not section:
        return []

    entries: list[dict[str, object]] = []
    current_option = ""
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        if not current_option or not current_title:
            return
        block_text = "\n".join(current_lines)
        entries.append(
            {
                "option": current_option,
                "title": current_title,
                "action": _extract_prefixed_line_value(block_text, "做什么"),
                "judgment": _extract_prefixed_line_value(block_text, "当前判断"),
                "basis_refs": _extract_doc_links(block_text),
            }
        )

    for line in section.splitlines():
        match = _DIRECTION_CANDIDATE_HEADING_RE.match(line.strip())
        if match:
            flush()
            current_option = match.group(1).strip()
            current_title = _strip_recommendation_suffix(match.group(2).strip())
            current_lines = []
            continue
        if current_option:
            current_lines.append(line)
    flush()
    return entries


def _extract_recommended_candidate_letter(text: str) -> str:
    section = _extract_section(text, "当前 AI 倾向判断")
    if not section:
        return ""
    match = _DIRECTION_RECOMMENDED_RE.search(section)
    return match.group(1).strip().upper() if match else ""


def _extract_prefixed_line_value(text: str, prefix: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("-"):
            continue
        payload = stripped[1:].strip()
        key, _, value = payload.partition("：")
        if key.strip() == prefix and value:
            return value.strip()
    return ""


def _extract_doc_links(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for match in _DOC_LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target in seen:
            continue
        seen.add(target)
        refs.append(target)
    return refs


def _extract_document_refs(text: str) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()

    for match in _DOC_LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not _looks_like_doc_ref(target) or target in seen:
            continue
        seen.add(target)
        refs.append(target)

    for match in _BACKTICK_REF_RE.finditer(text):
        target = match.group(1).strip()
        if not _looks_like_doc_ref(target) or target in seen:
            continue
        seen.add(target)
        refs.append(target)

    return refs


def _parse_research_compass_entries(
    text: str,
    *,
    source_path: str,
) -> list[dict[str, str]]:
    section = _extract_section(text, "全量研究地图")
    if not section:
        return []

    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        cells = _split_markdown_table_row(stripped)
        if len(cells) < 5:
            continue
        title, target = _extract_markdown_link(cells[0])
        normalized_target = _normalize_doc_ref(target, source_path=source_path)
        if not normalized_target or normalized_target in seen:
            continue
        seen.add(normalized_target)
        entries.append(
            {
                "path": normalized_target,
                "title": title or normalized_target,
                "summary": cells[2],
                "relevance": cells[3],
                "first_read_scenario": cells[4],
            }
        )
    return entries


def _parse_research_compass_topics(
    text: str,
    *,
    source_path: str,
    known_entry_paths: set[str],
) -> list[dict[str, object]]:
    section = _extract_section(text, "按问题检索")
    if not section:
        return []

    topics: list[dict[str, object]] = []
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        if not current_title:
            return
        reference_paths: list[str] = []
        seen: set[str] = set()
        for ref in _extract_document_refs("\n".join(current_lines)):
            normalized = _normalize_doc_ref(ref, source_path=source_path)
            if not normalized or normalized not in known_entry_paths or normalized in seen:
                continue
            seen.add(normalized)
            reference_paths.append(normalized)
        if not reference_paths:
            return
        topics.append(
            {
                "title": current_title,
                "summary": f"按问题检索 · 关联 {len(reference_paths)} 个研究入口",
                "reference_paths": reference_paths,
            }
        )

    for line in section.splitlines():
        match = _HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 3:
            flush()
            current_title = match.group(2).strip()
            current_lines = []
            continue
        if current_title:
            current_lines.append(line)
    flush()
    return topics


def _parse_global_direction_candidate_sections(text: str) -> list[dict[str, object]]:
    sections: list[dict[str, object]] = []
    current_title = ""
    current_lines: list[str] = []

    def flush() -> None:
        if not current_title:
            return
        section_text = "\n".join(current_lines)
        if _contains_numbered_global_direction_candidate_blocks(section_text):
            sections.append(_parse_numbered_global_direction_candidate_section(current_title, section_text))
            return
        if _contains_lettered_global_direction_candidate_blocks(section_text):
            sections.append(_parse_lettered_global_direction_candidate_section(current_title, section_text))

    for line in text.splitlines():
        match = _HEADING_RE.match(line.strip())
        if match and len(match.group(1)) == 2:
            flush()
            current_title = match.group(2).strip()
            current_lines = []
            continue
        if current_title:
            current_lines.append(line)
    flush()
    return sections


def _contains_numbered_global_direction_candidate_blocks(section_text: str) -> bool:
    return any(_GLOBAL_DIRECTION_CANDIDATE_RE.match(line.strip()) for line in section_text.splitlines())


def _contains_lettered_global_direction_candidate_blocks(section_text: str) -> bool:
    return any(_match_global_lettered_candidate_heading(line) for line in section_text.splitlines())


def _match_global_lettered_candidate_heading(line: str) -> re.Match[str] | None:
    match = _GLOBAL_DIRECTION_LETTERED_CANDIDATE_RE.match(line.strip())
    return match


def _parse_numbered_global_direction_candidate_section(
    section_title: str,
    section_text: str,
) -> dict[str, object]:
    completed_boundary = _extract_prefixed_line_value(section_text, "已完成边界")
    current_preference = _extract_prefixed_line_value(section_text, "当前倾向")
    recommended_candidate = _extract_global_recommended_candidate_number(current_preference)
    candidates: list[dict[str, object]] = []
    current_number = ""
    current_candidate_title = ""
    current_candidate_lines: list[str] = []

    def flush_candidate() -> None:
        if not current_number or not current_candidate_title:
            return
        block_text = "\n".join(current_candidate_lines)
        candidates.append(
            {
                "key": current_number,
                "label": f"候选 {current_number}",
                "title": current_candidate_title,
                "action": _extract_prefixed_line_value(block_text, "做什么"),
                "basis_refs": _extract_document_refs(block_text),
                "judgment": "",
                "recommended": current_number == recommended_candidate,
            }
        )

    for line in section_text.splitlines():
        match = _GLOBAL_DIRECTION_CANDIDATE_RE.match(line.strip())
        if match:
            flush_candidate()
            current_number = match.group(1).strip()
            current_candidate_title = match.group(2).strip()
            current_candidate_lines = []
            continue
        if current_number:
            current_candidate_lines.append(line)
    flush_candidate()

    return {
        "title": section_title,
        "completed_boundary": completed_boundary,
        "current_preference": current_preference,
        "recommended_candidate": recommended_candidate,
        "status_mode": "latest",
        "candidates": candidates,
    }


def _parse_lettered_global_direction_candidate_section(
    section_title: str,
    section_text: str,
) -> dict[str, object]:
    completed_boundary = _extract_prefixed_line_value(section_text, "已完成边界")
    candidates: list[dict[str, object]] = []
    current_letter = ""
    current_label = ""
    current_candidate_title = ""
    current_candidate_lines: list[str] = []

    def flush_candidate() -> None:
        if not current_letter or not current_candidate_title or not current_label:
            return
        block_text = "\n".join(current_candidate_lines)
        judgment = _extract_prefixed_line_value(block_text, "当前判断")
        candidates.append(
            {
                "key": current_letter.lower(),
                "label": current_label,
                "title": current_candidate_title,
                "action": _extract_prefixed_line_value(block_text, "做什么"),
                "basis_refs": _extract_document_refs(block_text),
                "judgment": judgment,
                "recommended": _is_recommended_global_candidate_judgment(judgment),
            }
        )

    for line in section_text.splitlines():
        match = _match_global_lettered_candidate_heading(line)
        if match:
            flush_candidate()
            prefix = (match.group(1) or "").strip()
            current_letter = match.group(2).strip().upper()
            current_label = f"{prefix} {current_letter}".strip() if prefix else current_letter
            current_candidate_title = match.group(3).strip()
            current_candidate_lines = []
            continue
        if current_letter:
            current_candidate_lines.append(line)
    flush_candidate()

    recommended_candidate = next(
        (str(candidate["key"]) for candidate in candidates if bool(candidate["recommended"])),
        "",
    )
    current_preference = next(
        (str(candidate["judgment"]) for candidate in candidates if bool(candidate["recommended"])),
        "",
    )
    return {
        "title": section_title,
        "completed_boundary": completed_boundary,
        "current_preference": current_preference,
        "recommended_candidate": recommended_candidate,
        "status_mode": "recommended",
        "candidates": candidates,
    }


def _is_recommended_global_candidate_judgment(judgment: str) -> bool:
    normalized = judgment.replace("*", "").replace("`", "").strip()
    if not normalized or "不推荐" in normalized:
        return False
    return normalized.startswith("推荐") or "优先推荐" in normalized or "默认推荐" in normalized


def _extract_global_recommended_candidate_number(text: str) -> str:
    match = _GLOBAL_DIRECTION_RECOMMENDED_RE.search(text)
    return match.group(1).strip() if match else ""


def _split_markdown_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    if not stripped:
        return []
    return [cell.strip() for cell in stripped.split("|")]


def _extract_markdown_link(text: str) -> tuple[str, str]:
    match = _DOC_LINK_WITH_LABEL_RE.search(text)
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def _research_compass_topic_node_id(title: str) -> str:
    return f"topic:{title.strip()}"


def _normalize_doc_ref(target: str, *, source_path: str) -> str:
    cleaned = target.split("#", 1)[0].strip()
    if not cleaned or cleaned.startswith(("http://", "https://", "mailto:")):
        return ""
    if cleaned.startswith(("./", "../")):
        cleaned = posixpath.join(posixpath.dirname(source_path), cleaned)
    normalized = posixpath.normpath(cleaned).replace("\\", "/")
    return normalized if _looks_like_doc_ref(normalized) else ""


def _looks_like_doc_ref(value: str) -> bool:
    normalized = value.strip()
    return "/" in normalized and normalized.endswith((".md", ".py", ".ts", ".tsx", ".json"))


def _strip_recommendation_suffix(title: str) -> str:
    return re.sub(r"（推荐）$", "", title).strip()


def _resolve_current_direction_analysis_path(project_root: Path) -> Path:
    checklist_path = project_root / "design_docs/Project Master Checklist.md"
    if checklist_path.exists():
        text = checklist_path.read_text(encoding="utf-8")
        active_todo_section = _extract_section(text, "活跃待办")
        matches: list[str] = []
        for line in active_todo_section.splitlines():
            if not line.startswith("- "):
                continue
            matches.extend(_PROJECT_PROGRESS_FOLLOWUP_PATH_RE.findall(line))
        if matches:
            return Path(matches[-1])
    return _DEFAULT_DIRECTION_ANALYSIS_PATH


def _is_empty_active_slice(value: str) -> bool:
    normalized = value.strip().lower()
    return any(marker in normalized for marker in _EMPTY_ACTIVE_SLICE_MARKERS)