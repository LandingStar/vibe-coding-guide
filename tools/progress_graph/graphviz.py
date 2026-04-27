"""Graphviz DOT preview helpers for progress graph export surfaces."""

from __future__ import annotations

import re
from pathlib import Path

from .doc_projection import history_json_path
from .export import export_history_surface, load_export_surface
from .model import ProgressMultiGraphHistory

_DEFAULT_DOT_PATH = Path(".codex/progress-graph/latest.dot")
_NODE_KIND_SHAPES = {
    "task": "box",
    "milestone": "ellipse",
    "decision": "diamond",
    "reference": "note",
    "cluster": "folder",
}
_NODE_STATUS_FILL = {
    "pending": "lightgoldenrod1",
    "in_progress": "lightskyblue1",
    "blocked": "mistyrose",
    "completed": "honeydew2",
    "archived": "gray90",
}
_EDGE_STYLES = {
    "workflow": {"style": "solid", "color": "gray25"},
    "dependency": {"style": "dashed", "color": "darkgoldenrod4"},
    "linkage": {"style": "dotted", "color": "steelblue4"},
}


def dot_preview_path(project_root: str | Path) -> Path:
    return Path(project_root) / _DEFAULT_DOT_PATH


def build_export_surface_dot(surface: dict[str, object]) -> str:
    lines = [
        "digraph progress_preview {",
        '  graph [compound=true, rankdir="LR", labelloc="t", label="Project Progress Preview"];',
        '  node [fontname="Helvetica", style="rounded,filled"];',
        '  edge [fontname="Helvetica"];',
    ]

    for graph in list(surface.get("graphs", [])):
        graph_id = str(graph["graph_id"])
        cluster_name = _cluster_name(graph_id)
        summary = dict(graph.get("summary", {}))
        label = (
            f'{graph["title"]}\\n{graph_id}\\n'
            f'ready={summary.get("ready_node_count", 0)} '
            f'nodes={summary.get("node_count", 0)}'
        )
        lines.append(f"  subgraph {cluster_name} {{")
        lines.append(f"    label={_dot_string(label)};")
        lines.append('    color="gray70";')
        lines.append('    penwidth="1.2";')

        display = dict(graph.get("display", {}))
        for node in list(display.get("nodes", [])):
            lines.append(f"    {_dot_id(str(node['key']))} [{_display_node_attrs(node)}];")
        for edge in list(display.get("edges", [])):
            lines.append(
                f"    {_dot_id(str(edge['source_key']))} -> {_dot_id(str(edge['target_key']))} "
                f"[{_edge_attrs(str(edge['kind']))}];"
            )
        lines.append("  }")

    for edge in list(surface.get("cross_graph_edges", [])):
        attrs = _edge_attrs(str(edge["kind"]), cross_graph=True)
        lines.append(
            f"  {_dot_id(str(edge['source_display_key']))} -> {_dot_id(str(edge['target_display_key']))} [{attrs}];"
        )

    lines.append("}")
    return "\n".join(lines) + "\n"


def build_history_dot(
    history: ProgressMultiGraphHistory,
    *,
    collapsed_clusters_by_graph: dict[str, set[str]] | None = None,
) -> str:
    surface = export_history_surface(
        history,
        collapsed_clusters_by_graph=collapsed_clusters_by_graph,
    )
    return build_export_surface_dot(surface)


def write_history_dot(
    project_root: str | Path,
    *,
    history: ProgressMultiGraphHistory | None = None,
    collapsed_clusters_by_graph: dict[str, set[str]] | None = None,
) -> Path:
    root = Path(project_root)
    if history is None:
        surface = load_export_surface(
            history_json_path(root),
            collapsed_clusters_by_graph=collapsed_clusters_by_graph,
        )
        dot_text = build_export_surface_dot(surface)
    else:
        dot_text = build_history_dot(
            history,
            collapsed_clusters_by_graph=collapsed_clusters_by_graph,
        )
    path = dot_preview_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dot_text, encoding="utf-8")
    return path


def _display_node_attrs(node: dict[str, object]) -> str:
    kind = str(node.get("kind", "task"))
    title = str(node.get("title", node.get("id", "")))
    if kind == "cluster":
        member_count = len(list(node.get("member_ids", [])))
        label = f"{title}\\ncluster ({member_count})"
        attrs = {
            "label": label,
            "shape": _NODE_KIND_SHAPES[kind],
            "fillcolor": "gray95",
            "penwidth": "1.4",
        }
    else:
        status = str(node.get("status", "pending"))
        attrs = {
            "label": f"{title}\\n{status}",
            "shape": _NODE_KIND_SHAPES.get(kind, "box"),
            "fillcolor": _NODE_STATUS_FILL.get(status, "white"),
        }
    return _dot_attrs(attrs)


def _edge_attrs(kind: str, *, cross_graph: bool = False) -> str:
    attrs = dict(_EDGE_STYLES.get(kind, {"style": "solid", "color": "gray25"}))
    if cross_graph:
        attrs["constraint"] = "false"
        attrs["penwidth"] = "1.4"
    return _dot_attrs(attrs)


def _dot_attrs(attrs: dict[str, str]) -> str:
    return ", ".join(f"{key}={_dot_string(value)}" for key, value in attrs.items())


def _dot_id(value: str) -> str:
    return _dot_string(value)


def _dot_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', r'\"').replace("\n", r"\n")
    return f'"{escaped}"'


def _cluster_name(graph_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_]", "_", graph_id)
    return f"cluster_{safe}"