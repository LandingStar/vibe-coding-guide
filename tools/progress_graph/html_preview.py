"""Self-contained HTML preview helpers for progress graph export surfaces."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from src.runtime.orchestration.artifact_paths import dbc_artifact_path

from .doc_projection import history_json_path
from .export import export_history_surface, load_export_surface
from .model import ProgressMultiGraphHistory

_DEFAULT_HTML_PATH = Path(dbc_artifact_path("progress-graph", "latest.html"))
_NODE_WIDTH = 220
_NODE_HEIGHT = 72
_LAYER_GAP = 88
_NODE_GAP = 28
_GRAPH_PADDING_X = 32
_GRAPH_PADDING_Y = 28
_NODE_STATUS_CLASS = {
    "pending": "pending",
    "in_progress": "in-progress",
    "blocked": "blocked",
    "completed": "completed",
    "archived": "archived",
}


def html_preview_path(project_root: str | Path) -> Path:
    return Path(project_root) / _DEFAULT_HTML_PATH


def build_export_surface_html(surface: dict[str, object]) -> str:
    history_summary = dict(surface.get("history_summary", {}))
    history_metadata = dict(surface.get("history_metadata", {}))
    graphs = list(surface.get("graphs", []))
    cross_graph_edges = list(surface.get("cross_graph_edges", []))
    ready_nodes = list(surface.get("ready_nodes", []))

    graph_sections = "\n".join(_render_graph_section(graph) for graph in graphs)
    cross_graph_html = _render_cross_graph_edges(cross_graph_edges)
    ready_nodes_html = _render_global_ready_nodes(ready_nodes)
    generated_at = str(history_metadata.get("latest_projection_at", ""))
    interaction_script = _render_interaction_script()

    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Project Progress Preview</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f3ee;
      --panel: #fffdf9;
      --ink: #1f2328;
      --muted: #5f6b76;
      --line: #d9d1c7;
      --accent: #114b5f;
      --accent-soft: #dbeaf0;
      --pending: #f9e7a8;
      --in-progress: #b9dcff;
      --blocked: #ffd8d2;
      --completed: #d8f0dc;
      --archived: #ececec;
      --cluster: #f0ede7;
      --workflow: #45515f;
      --dependency: #8a6d1f;
      --linkage: #2b5876;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "PingFang SC", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #fff7ea 0, var(--bg) 45%, #ece7df 100%);
    }}
    main {{
      width: min(1400px, calc(100vw - 32px));
      margin: 24px auto 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, #163645 0%, #114b5f 55%, #3f7f86 100%);
      color: #f8f4ef;
      padding: 24px 28px;
      border-radius: 20px;
      box-shadow: 0 20px 40px rgba(17, 75, 95, 0.22);
      margin-bottom: 20px;
    }}
    .hero h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .hero p {{ margin: 0; color: rgba(248, 244, 239, 0.84); line-height: 1.5; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid rgba(17, 75, 95, 0.08);
      border-radius: 16px;
      padding: 16px 18px;
      box-shadow: 0 8px 20px rgba(57, 49, 38, 0.08);
    }}
    .card .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }}
    .card .value {{ margin-top: 8px; font-size: 28px; font-weight: 700; }}
    .meta {{ margin-top: 12px; color: var(--muted); font-size: 13px; }}
    .section {{
      background: rgba(255, 253, 249, 0.86);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px;
      margin-bottom: 18px;
      box-shadow: 0 10px 22px rgba(57, 49, 38, 0.06);
    }}
    .section h2 {{ margin: 0 0 10px; font-size: 22px; }}
    .section .subtle {{ color: var(--muted); font-size: 13px; }}
    .graph-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 280px; gap: 18px; align-items: start; }}
    .graph-side {{ display: grid; gap: 12px; }}
    .graph-tools, .detail-stack {{ display: grid; gap: 10px; }}
    .filter-strip {{ display: grid; gap: 10px; }}
    .filter-search {{ width: 100%; border: 1px solid var(--line); border-radius: 12px; background: var(--panel); padding: 10px 12px; color: var(--ink); font: inherit; }}
    .filter-search::placeholder {{ color: var(--muted); }}
    .filter-chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .filter-chip {{ border: 1px solid rgba(17, 75, 95, 0.12); background: rgba(17, 75, 95, 0.04); color: var(--ink); border-radius: 999px; padding: 6px 10px; font: inherit; font-size: 12px; cursor: pointer; }}
    .filter-chip.is-active {{ background: var(--accent); color: #f8f4ef; border-color: var(--accent); }}
    .zoom-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }}
    .zoom-button {{ border: 1px solid rgba(17, 75, 95, 0.12); background: rgba(17, 75, 95, 0.04); color: var(--ink); border-radius: 999px; padding: 6px 12px; font: inherit; font-size: 12px; cursor: pointer; }}
    .zoom-button:disabled {{ cursor: default; opacity: 0.45; }}
    .zoom-level {{ color: var(--muted); font-size: 12px; min-width: 52px; text-align: right; }}
    .zoom-hint {{ color: var(--muted); font-size: 11px; }}
    .filter-summary {{ color: var(--muted); font-size: 12px; }}
    .badge-list, .edge-list, .ready-list {{ display: grid; gap: 8px; margin: 12px 0 0; padding: 0; list-style: none; }}
    .badge, .edge-item, .ready-item {{
      background: rgba(17, 75, 95, 0.04);
      border: 1px solid rgba(17, 75, 95, 0.08);
      border-radius: 12px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.45;
    }}
    .ready-item.is-hidden {{ display: none; }}
    .ready-item.is-selected {{ border-color: rgba(17, 75, 95, 0.24); background: rgba(17, 75, 95, 0.1); }}
    .list-action {{ display: block; width: 100%; padding: 0; border: 0; background: transparent; color: inherit; text-align: left; font: inherit; cursor: pointer; }}
    .edge-kind, .status-pill {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 700;
      margin-right: 6px;
      vertical-align: middle;
    }}
    .edge-kind.workflow {{ background: rgba(69, 81, 95, 0.12); color: var(--workflow); }}
    .edge-kind.dependency {{ background: rgba(138, 109, 31, 0.14); color: var(--dependency); }}
    .edge-kind.linkage {{ background: rgba(43, 88, 118, 0.14); color: var(--linkage); }}
    .status-pill.pending {{ background: rgba(249, 231, 168, 0.65); }}
    .status-pill.in-progress {{ background: rgba(185, 220, 255, 0.75); }}
    .status-pill.blocked {{ background: rgba(255, 216, 210, 0.75); }}
    .status-pill.completed {{ background: rgba(216, 240, 220, 0.85); }}
    .status-pill.archived {{ background: rgba(236, 236, 236, 0.9); }}
    .svg-wrap {{ overflow: auto; max-height: min(72vh, 960px); border-radius: 16px; border: 1px solid var(--line); background: white; }}
    svg {{ display: block; width: auto; max-width: none; height: auto; margin: 0 auto; background: linear-gradient(180deg, #fffdf9 0%, #f8f5ef 100%); }}
    .node-label {{ font-size: 12px; fill: var(--ink); font-weight: 600; }}
    .node-sub {{ font-size: 11px; fill: var(--muted); }}
    .interactive-node {{ cursor: pointer; transition: opacity 0.15s ease; }}
    .interactive-node .node-shape {{ transition: stroke 0.15s ease, stroke-width 0.15s ease, filter 0.15s ease; }}
    .interactive-node.is-muted {{ opacity: 0.18; }}
    .interactive-node.is-selected .node-shape, .interactive-node:focus-visible .node-shape {{ stroke: var(--accent); stroke-width: 3; filter: drop-shadow(0 0 10px rgba(17, 75, 95, 0.18)); }}
    .interactive-edge {{ transition: opacity 0.15s ease; }}
    .interactive-edge.is-muted {{ opacity: 0.12; }}
    .detail-card {{ background: var(--panel); border: 1px solid rgba(17, 75, 95, 0.08); border-radius: 16px; padding: 14px 16px; }}
    .detail-card h3 {{ margin: 0 0 8px; font-size: 16px; }}
    .detail-placeholder {{ margin: 0; color: var(--muted); font-size: 13px; line-height: 1.5; }}
    .detail-row {{ display: grid; gap: 4px; }}
    .detail-label {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .detail-value {{ font-size: 13px; line-height: 1.5; word-break: break-word; }}
    .detail-tags {{ display: flex; flex-wrap: wrap; gap: 6px; }}
    .detail-tag {{ background: var(--accent-soft); color: var(--accent); border-radius: 999px; padding: 4px 8px; font-size: 11px; font-weight: 700; }}
    .detail-meta {{ margin: 0; padding: 10px 12px; background: rgba(17, 75, 95, 0.04); border: 1px solid rgba(17, 75, 95, 0.08); border-radius: 12px; font-size: 12px; line-height: 1.45; white-space: pre-wrap; overflow: auto; }}
    .footer-note {{ color: var(--muted); font-size: 12px; margin-top: 8px; }}
    @media (max-width: 980px) {{
      .graph-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class=\"hero\">
      <h1>Project Progress Preview</h1>
      <p>当前已经存在轻量化图形展示。这个页面是在 export surface 和 DOT preview 之上补的第一版可直接打开 HTML 预览，用于把当前 progress graph 变成无需额外渲染步骤的图形化 artifact。</p>
      <div class=\"meta\">generated_from={escape(generated_at or 'unknown')} · schema={escape(str(surface.get('schema_version', 'unknown')))}</div>
    </section>
    <section class=\"cards\">
      <div class=\"card\"><div class=\"label\">Current Graphs</div><div class=\"value\">{len(graphs)}</div></div>
      <div class=\"card\"><div class=\"label\">Ready Nodes</div><div class=\"value\">{history_summary.get('ready_node_count', 0)}</div></div>
      <div class=\"card\"><div class=\"label\">Cross-Graph Edges</div><div class=\"value\">{len(cross_graph_edges)}</div></div>
      <div class=\"card\"><div class=\"label\">Independent Sets</div><div class=\"value\">{len(list(surface.get('independent_graph_sets', [])))}</div></div>
    </section>
    {graph_sections}
    <section class=\"section\">
      <h2>Global Ready Nodes</h2>
      {ready_nodes_html}
    </section>
    <section class=\"section\">
      <h2>Cross-Graph Edge Summary</h2>
      {cross_graph_html}
      <p class=\"footer-note\">第一版 HTML preview 暂不做跨图空间连线布局，跨图关系先以 display-aware 摘要列表呈现。</p>
    </section>
  </main>
  <script>{interaction_script}</script>
</body>
</html>
"""


def build_history_html(
    history: ProgressMultiGraphHistory,
    *,
    collapsed_clusters_by_graph: dict[str, set[str]] | None = None,
) -> str:
    surface = export_history_surface(
        history,
        collapsed_clusters_by_graph=collapsed_clusters_by_graph,
    )
    return build_export_surface_html(surface)


def write_history_html(
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
        html = build_export_surface_html(surface)
    else:
        html = build_history_html(
            history,
            collapsed_clusters_by_graph=collapsed_clusters_by_graph,
        )
    html = _strip_trailing_line_whitespace(html)
    path = html_preview_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def _strip_trailing_line_whitespace(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"


def _render_graph_section(graph: dict[str, object]) -> str:
    summary = dict(graph.get("summary", {}))
    display = dict(graph.get("display", {}))
    mapping = {str(raw_id): str(display_id) for raw_id, display_id in dict(display.get("mapping", {})).items()}
    layout = _build_graph_layout(graph)
    ready_nodes = list(graph.get("ready_nodes", []))
    graph_svg = _render_graph_svg(layout)
    graph_payload = _serialize_json_for_html(_build_graph_interaction_payload(graph))
    ready_html = (
        "<p class=\"subtle\">当前没有 ready nodes。</p>"
        if not ready_nodes
        else "<ul class=\"ready-list\">"
        + "".join(
            f"<li class=\"ready-item\" data-display-id=\"{escape(mapping.get(str(node.get('id', '')), str(node.get('id', ''))))}\">"
            f"<button type=\"button\" class=\"list-action\">"
            f"<span class=\"status-pill {_status_class(str(node.get('status', 'pending')))}\">{escape(str(node.get('status', 'pending')))}</span>{escape(str(node.get('title', '')))}"
            "</button></li>"
            for node in ready_nodes
        )
        + "</ul>"
    )

    badges = "".join(
        [
            f"<li class=\"badge\">snapshot={escape(str(graph.get('snapshot_id', '')))}</li>",
            f"<li class=\"badge\">nodes={summary.get('node_count', 0)} · edges={summary.get('edge_count', 0)} · clusters={summary.get('cluster_count', 0)}</li>",
            f"<li class=\"badge\">ready={summary.get('ready_node_count', 0)} · layers={len(list(graph.get('topological_layers', [])))}</li>",
        ]
    )

    return f"""
    <section class=\"section graph-section\" data-graph-id=\"{escape(str(graph.get('graph_id', '')))}\">
      <h2>{escape(str(graph.get('title', '')))}</h2>
      <div class=\"subtle\">graph_id={escape(str(graph.get('graph_id', '')))} · recorded_at={escape(str(graph.get('recorded_at', '')))}</div>
      <div class=\"graph-grid\">
        <div class=\"svg-wrap\">{graph_svg}</div>
        <div class=\"graph-side\">
          <ul class=\"badge-list\">{badges}</ul>
          <div class=\"graph-tools\">
            {_render_graph_controls()}
            {_render_graph_detail_panel()}
          </div>
          <div>
            <h3>Ready Nodes</h3>
            {ready_html}
          </div>
        </div>
      </div>
      <script type=\"application/json\" data-role=\"graph-payload\">{graph_payload}</script>
    </section>
    """


def _render_graph_controls() -> str:
    return """
    <div class="detail-card">
      <h3>Graph Controls</h3>
      <div class="filter-strip">
        <div class="zoom-row">
          <button type="button" class="zoom-button" data-role="zoom-out" aria-label="Zoom out current graph">-</button>
          <button type="button" class="zoom-button" data-role="zoom-reset" aria-label="Reset current graph zoom">100%</button>
          <button type="button" class="zoom-button" data-role="zoom-in" aria-label="Zoom in current graph">+</button>
          <div class="zoom-level" data-role="zoom-level">100%</div>
        </div>
        <div class="zoom-hint">Ctrl + 滚轮可缩放当前图。</div>
        <input type="search" class="filter-search" data-role="graph-search" placeholder="搜索当前图中的节点标题、ID 或摘要">
        <div class="filter-chip-row">
          <button type="button" class="filter-chip is-active" data-status-filter="all">All</button>
          <button type="button" class="filter-chip" data-status-filter="pending">Pending</button>
          <button type="button" class="filter-chip" data-status-filter="in_progress">In Progress</button>
          <button type="button" class="filter-chip" data-status-filter="blocked">Blocked</button>
          <button type="button" class="filter-chip" data-status-filter="completed">Completed</button>
          <button type="button" class="filter-chip" data-status-filter="archived">Archived</button>
        </div>
        <div class="filter-summary" data-role="filter-summary">visible 0 / 0</div>
      </div>
    </div>
    """


def _render_graph_detail_panel() -> str:
    return """
    <div class="detail-card" data-role="node-detail">
      <h3>Node Detail</h3>
      <div data-role="detail-body">
        <p class="detail-placeholder">选择图中的节点或 ready item 查看详情。</p>
      </div>
    </div>
    """


def _build_graph_layout(graph: dict[str, object]) -> dict[str, object]:
    display = dict(graph.get("display", {}))
    mapping = dict(display.get("mapping", {}))
    display_nodes = {str(node["id"]): dict(node) for node in list(display.get("nodes", []))}
    topological_layers = [list(layer) for layer in list(graph.get("topological_layers", []))]

    layer_by_display: dict[str, int] = {}
    for layer_index, layer in enumerate(topological_layers):
        for raw_node_id in layer:
            display_id = str(mapping.get(str(raw_node_id), str(raw_node_id)))
            previous = layer_by_display.get(display_id)
            if previous is None or layer_index < previous:
                layer_by_display[display_id] = layer_index

    fallback_layer = len(topological_layers)
    for display_id in sorted(display_nodes):
        layer_by_display.setdefault(display_id, fallback_layer)

    ordered_ids = sorted(display_nodes, key=lambda node_id: (layer_by_display[node_id], node_id))
    layers: dict[int, list[str]] = {}
    for display_id in ordered_ids:
        layers.setdefault(layer_by_display[display_id], []).append(display_id)

    positioned_nodes: list[dict[str, object]] = []
    positions: dict[str, dict[str, float]] = {}
    for layer_index, node_ids in sorted(layers.items()):
        for row_index, node_id in enumerate(node_ids):
            x = _GRAPH_PADDING_X + layer_index * (_NODE_WIDTH + _LAYER_GAP)
            y = _GRAPH_PADDING_Y + row_index * (_NODE_HEIGHT + _NODE_GAP)
            node = dict(display_nodes[node_id])
            node["x"] = x
            node["y"] = y
            node["width"] = _NODE_WIDTH
            node["height"] = _NODE_HEIGHT
            positioned_nodes.append(node)
            positions[node_id] = {"x": float(x), "y": float(y)}

    positioned_edges: list[dict[str, float | str]] = []
    for edge in list(display.get("edges", [])):
        source_id = str(edge["source"])
        target_id = str(edge["target"])
        if source_id not in positions or target_id not in positions:
            continue
        source = positions[source_id]
        target = positions[target_id]
        x1 = source["x"] + _NODE_WIDTH
        y1 = source["y"] + (_NODE_HEIGHT / 2)
        x2 = target["x"]
        y2 = target["y"] + (_NODE_HEIGHT / 2)
        mid_x = x1 + max((x2 - x1) / 2, 28)
        path = f"M{x1:.1f},{y1:.1f} C{mid_x:.1f},{y1:.1f} {mid_x:.1f},{y2:.1f} {x2:.1f},{y2:.1f}"
        positioned_edges.append(
            {
                "path": path,
            "source": source_id,
            "target": target_id,
                "kind": str(edge.get("kind", "workflow")),
                "count": float(edge.get("count", 1)),
            }
        )

    max_layer = max(layers, default=0)
    max_rows = max((len(node_ids) for node_ids in layers.values()), default=1)
    width = _GRAPH_PADDING_X * 2 + (max_layer + 1) * _NODE_WIDTH + max_layer * _LAYER_GAP
    height = _GRAPH_PADDING_Y * 2 + max_rows * _NODE_HEIGHT + max(0, max_rows - 1) * _NODE_GAP

    return {
        "width": width,
        "height": height,
        "nodes": positioned_nodes,
        "edges": positioned_edges,
    }


def _render_graph_svg(layout: dict[str, object]) -> str:
    nodes = list(layout.get("nodes", []))
    edges = list(layout.get("edges", []))
    width = int(layout.get("width", 400))
    height = int(layout.get("height", 240))

    edge_markup = "".join(
      f"<path d=\"{escape(str(edge['path']))}\" data-source-id=\"{escape(str(edge['source']))}\" data-target-id=\"{escape(str(edge['target']))}\" class=\"edge interactive-edge edge-{escape(str(edge['kind']))}\" marker-end=\"url(#arrow-{escape(str(edge['kind']))})\"></path>"
        for edge in edges
    )
    node_markup = "".join(_render_svg_node(node) for node in nodes)
    return f"""
    <svg width=\"{width}\" height=\"{height}\" viewBox=\"0 0 {width} {height}\" role=\"img\" aria-label=\"Progress graph preview\">
      <defs>
        <marker id=\"arrow-workflow\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#45515f\"></path></marker>
        <marker id=\"arrow-dependency\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#8a6d1f\"></path></marker>
        <marker id=\"arrow-linkage\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#2b5876\"></path></marker>
        <style>
          .edge {{ fill: none; stroke-width: 2.2; }}
          .edge-workflow {{ stroke: var(--workflow); }}
          .edge-dependency {{ stroke: var(--dependency); stroke-dasharray: 7 5; }}
          .edge-linkage {{ stroke: var(--linkage); stroke-dasharray: 2 6; }}
          .node-shape {{ stroke: rgba(31, 35, 40, 0.14); stroke-width: 1.5; }}
          .node-cluster {{ fill: var(--cluster); }}
          .node-pending {{ fill: var(--pending); }}
          .node-in-progress {{ fill: var(--in-progress); }}
          .node-blocked {{ fill: var(--blocked); }}
          .node-completed {{ fill: var(--completed); }}
          .node-archived {{ fill: var(--archived); }}
        </style>
      </defs>
      {edge_markup}
      {node_markup}
    </svg>
    """


def _render_svg_node(node: dict[str, object]) -> str:
    node_id = str(node.get("id", ""))
    kind = str(node.get("kind", "task"))
    title = _truncate(str(node.get("title", node_id)), 34)
    subtitle = _subtitle_for_node(node)
    x = float(node.get("x", 0))
    y = float(node.get("y", 0))
    width = float(node.get("width", _NODE_WIDTH))
    height = float(node.get("height", _NODE_HEIGHT))
    status_class = _node_fill_class(node)
    shape_markup = _render_node_shape(x, y, width, height, kind, status_class)
    text_x = x + (width / 2)
    text_y = y + (height / 2) - 6
    return f"""
      <g class=\"interactive-node\" data-node-id=\"{escape(node_id)}\" tabindex=\"0\" role=\"button\" aria-label=\"Inspect {escape(str(node.get('title', node_id)))}\">
        {shape_markup}
        <text x=\"{text_x:.1f}\" y=\"{text_y:.1f}\" text-anchor=\"middle\" class=\"node-label\">
          <tspan x=\"{text_x:.1f}\" dy=\"0\">{escape(title)}</tspan>
          <tspan x=\"{text_x:.1f}\" dy=\"17\" class=\"node-sub\">{escape(subtitle)}</tspan>
        </text>
      </g>
    """


def _render_node_shape(
    x: float,
    y: float,
    width: float,
    height: float,
    kind: str,
    status_class: str,
) -> str:
    classes = f"node-shape {status_class}"
    if kind == "cluster":
        classes += " node-cluster"
    if kind == "milestone":
        cx = x + width / 2
        cy = y + height / 2
        rx = width / 2
        ry = height / 2
        return f"<ellipse class=\"{classes}\" cx=\"{cx:.1f}\" cy=\"{cy:.1f}\" rx=\"{rx:.1f}\" ry=\"{ry:.1f}\"></ellipse>"
    if kind == "decision":
        cx = x + width / 2
        cy = y + height / 2
        points = [
            f"{cx:.1f},{y:.1f}",
            f"{x + width:.1f},{cy:.1f}",
            f"{cx:.1f},{y + height:.1f}",
            f"{x:.1f},{cy:.1f}",
        ]
        return f"<polygon class=\"{classes}\" points=\"{' '.join(points)}\"></polygon>"
    radius = 18 if kind == "cluster" else 14
    return f"<rect class=\"{classes}\" x=\"{x:.1f}\" y=\"{y:.1f}\" width=\"{width:.1f}\" height=\"{height:.1f}\" rx=\"{radius}\" ry=\"{radius}\"></rect>"


def _subtitle_for_node(node: dict[str, object]) -> str:
    kind = str(node.get("kind", "task"))
    if kind == "cluster":
        member_count = len(list(node.get("member_ids", [])))
        return f"cluster ({member_count})"
    return str(node.get("status", "pending"))


def _node_fill_class(node: dict[str, object]) -> str:
    if str(node.get("kind", "task")) == "cluster":
        return "node-cluster"
    return f"node-{_status_class(str(node.get('status', 'pending')))}"


def _status_class(status: str) -> str:
    return _NODE_STATUS_CLASS.get(status, "pending")


def _render_cross_graph_edges(edges: list[dict[str, object]]) -> str:
    if not edges:
        return "<p class=\"subtle\">当前没有 cross-graph edges。</p>"
    items = []
    for edge in edges:
        items.append(
            "<li class=\"edge-item\">"
            f"<span class=\"edge-kind {escape(str(edge.get('kind', 'workflow')))}\">{escape(str(edge.get('kind', 'workflow')))}</span>"
            f"{escape(str(edge.get('source_graph_id', '')))} / {escape(str(edge.get('source_display_id', '')))}"
            " → "
            f"{escape(str(edge.get('target_graph_id', '')))} / {escape(str(edge.get('target_display_id', '')))}"
            "</li>"
        )
    return f"<ul class=\"edge-list\">{''.join(items)}</ul>"


def _render_global_ready_nodes(nodes: list[dict[str, object]]) -> str:
    if not nodes:
        return "<p class=\"subtle\">当前没有 global ready nodes。</p>"
    items = []
    for node in nodes:
        items.append(
            "<li class=\"ready-item\">"
            f"{escape(str(node.get('graph_id', '')))} / {escape(str(node.get('title', '')))}"
            "</li>"
        )
    return f"<ul class=\"ready-list\">{''.join(items)}</ul>"


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)] + "…"


def _build_graph_interaction_payload(graph: dict[str, object]) -> dict[str, object]:
    raw = dict(graph.get("raw", {}))
    display = dict(graph.get("display", {}))
    raw_nodes = {str(node["id"]): dict(node) for node in list(raw.get("nodes", []))}
    display_nodes = {str(node["id"]): dict(node) for node in list(display.get("nodes", []))}
    mapping = {str(raw_id): str(display_id) for raw_id, display_id in dict(display.get("mapping", {})).items()}

    raw_ids_by_display: dict[str, list[str]] = {}
    for raw_id, display_id in mapping.items():
        raw_ids_by_display.setdefault(display_id, []).append(raw_id)

    payload_nodes: dict[str, dict[str, object]] = {}
    for display_id, display_node in display_nodes.items():
        raw_ids = sorted(
            set(raw_ids_by_display.get(display_id, []))
            or set(str(member_id) for member_id in list(display_node.get("member_ids", [])))
            or ({display_id} if display_id in raw_nodes else set())
        )
        raw_titles = [str(raw_nodes[raw_id].get("title", raw_id)) for raw_id in raw_ids if raw_id in raw_nodes]
        raw_summaries = [
            str(raw_nodes[raw_id].get("summary", "")).strip()
            for raw_id in raw_ids
            if raw_id in raw_nodes and str(raw_nodes[raw_id].get("summary", "")).strip()
        ]
        tags = sorted(
            {
                str(tag)
                for raw_id in raw_ids
                for tag in list(raw_nodes.get(raw_id, {}).get("tags", []))
                if str(tag).strip()
            }
        )
        title = str(display_node.get("title", display_id))
        kind = str(display_node.get("kind", "task"))
        status = str(display_node.get("status", "pending"))
        summary = str(display_node.get("summary", "")).strip() or (raw_summaries[0] if raw_summaries else "")
        payload_nodes[display_id] = {
            "id": display_id,
            "title": title,
            "kind": kind,
            "status": status,
            "summary": summary,
            "memberIds": raw_ids,
            "rawTitles": raw_titles,
            "tags": tags,
            "metadata": dict(display_node.get("metadata", {})),
            "searchText": " ".join(
                value
                for value in [display_id, title, kind, status, summary, *raw_ids, *raw_titles, *tags]
                if value
            ).lower(),
        }

    return {
        "graphId": str(graph.get("graph_id", "")),
        "nodeCount": len(payload_nodes),
        "nodes": payload_nodes,
    }


def _serialize_json_for_html(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")


def _render_interaction_script() -> str:
    return """
(() => {
  const escapeHtml = (value) => String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\"/g, '&quot;')
    .replace(/'/g, '&#39;');

  for (const section of document.querySelectorAll('.graph-section')) {
    const payloadEl = section.querySelector('[data-role="graph-payload"]');
    if (!payloadEl || !payloadEl.textContent) {
      continue;
    }

    let payload;
    try {
      payload = JSON.parse(payloadEl.textContent);
    } catch {
      continue;
    }

    const searchInput = section.querySelector('[data-role="graph-search"]');
    const filterSummary = section.querySelector('[data-role="filter-summary"]');
    const detailBody = section.querySelector('[data-role="detail-body"]');
    const svgWrap = section.querySelector('.svg-wrap');
    const svg = section.querySelector('.svg-wrap svg');
    const zoomOutButton = section.querySelector('[data-role="zoom-out"]');
    const zoomResetButton = section.querySelector('[data-role="zoom-reset"]');
    const zoomInButton = section.querySelector('[data-role="zoom-in"]');
    const zoomLevel = section.querySelector('[data-role="zoom-level"]');
    const filterButtons = Array.from(section.querySelectorAll('[data-status-filter]'));
    const nodeGroups = Array.from(section.querySelectorAll('g[data-node-id]'));
    const edgePaths = Array.from(section.querySelectorAll('path[data-source-id][data-target-id]'));
    const readyItems = Array.from(section.querySelectorAll('.ready-item[data-display-id]'));

    let activeStatus = 'all';
    let searchText = '';
    let selectedId = '';
    let zoom = 1;
    const minZoom = 0.6;
    const maxZoom = 2.4;
    const zoomStep = 0.2;
    const intrinsicWidth = svg ? Number(svg.getAttribute('width')) || svg.viewBox?.baseVal?.width || svg.getBoundingClientRect().width || 0 : 0;
    const intrinsicHeight = svg ? Number(svg.getAttribute('height')) || svg.viewBox?.baseVal?.height || svg.getBoundingClientRect().height || 0 : 0;

    const applyZoom = () => {
      if (!svg || !intrinsicWidth || !intrinsicHeight) {
        return;
      }

      const width = Math.max(1, Math.round(intrinsicWidth * zoom));
      const height = Math.max(1, Math.round(intrinsicHeight * zoom));
      svg.style.width = `${width}px`;
      svg.style.height = `${height}px`;

      if (zoomLevel) {
        zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
      }
      if (zoomOutButton instanceof HTMLButtonElement) {
        zoomOutButton.disabled = zoom <= minZoom + 0.001;
      }
      if (zoomInButton instanceof HTMLButtonElement) {
        zoomInButton.disabled = zoom >= maxZoom - 0.001;
      }
    };

    const setZoom = (nextZoom) => {
      zoom = Math.max(minZoom, Math.min(maxZoom, Number(nextZoom.toFixed(2))));
      applyZoom();
    };

    const renderDetail = (nodeId) => {
      if (!detailBody) {
        return;
      }

      const node = payload.nodes[nodeId];
      if (!node) {
        detailBody.innerHTML = '<p class="detail-placeholder">选择图中的节点或 ready item 查看详情。</p>';
        return;
      }

      const tags = Array.isArray(node.tags) && node.tags.length
        ? `<div class="detail-row"><span class="detail-label">Tags</span><div class="detail-tags">${node.tags.map((tag) => `<span class="detail-tag">${escapeHtml(tag)}</span>`).join('')}</div></div>`
        : '';
      const members = Array.isArray(node.rawTitles) && node.rawTitles.length
        ? `<div class="detail-row"><span class="detail-label">Raw Nodes</span><div class="detail-value">${node.rawTitles.map((title) => escapeHtml(title)).join(' · ')}</div></div>`
        : '';
      const summary = node.summary
        ? `<div class="detail-row"><span class="detail-label">Summary</span><div class="detail-value">${escapeHtml(node.summary)}</div></div>`
        : '';
      const metadata = node.metadata && Object.keys(node.metadata).length
        ? `<div class="detail-row"><span class="detail-label">Metadata</span><pre class="detail-meta">${escapeHtml(JSON.stringify(node.metadata, null, 2))}</pre></div>`
        : '';

      detailBody.innerHTML = `
        <div class="detail-stack">
          <div class="detail-row"><span class="detail-label">Title</span><div class="detail-value">${escapeHtml(node.title)}</div></div>
          <div class="detail-row"><span class="detail-label">ID</span><div class="detail-value">${escapeHtml(node.id)}</div></div>
          <div class="detail-row"><span class="detail-label">Kind / Status</span><div class="detail-value">${escapeHtml(node.kind)} / ${escapeHtml(node.status)}</div></div>
          ${summary}
          ${members}
          ${tags}
          ${metadata}
        </div>`;
    };

    const updateVisibility = () => {
      const visibleIds = new Set();

      for (const node of Object.values(payload.nodes)) {
        const matchesStatus = activeStatus === 'all' || node.status === activeStatus;
        const matchesSearch = !searchText || String(node.searchText || '').includes(searchText);
        if (matchesStatus && matchesSearch) {
          visibleIds.add(node.id);
        }
      }

      if (selectedId && !visibleIds.has(selectedId)) {
        selectedId = '';
      }

      for (const group of nodeGroups) {
        const nodeId = group.dataset.nodeId || '';
        group.classList.toggle('is-muted', !visibleIds.has(nodeId));
        group.classList.toggle('is-selected', nodeId === selectedId);
      }

      for (const edge of edgePaths) {
        const sourceId = edge.dataset.sourceId || '';
        const targetId = edge.dataset.targetId || '';
        edge.classList.toggle('is-muted', !(visibleIds.has(sourceId) && visibleIds.has(targetId)));
      }

      for (const item of readyItems) {
        const displayId = item.dataset.displayId || '';
        item.classList.toggle('is-hidden', !visibleIds.has(displayId));
        item.classList.toggle('is-selected', displayId === selectedId);
      }

      if (filterSummary) {
        filterSummary.textContent = `visible ${visibleIds.size} / ${payload.nodeCount}`;
      }

      renderDetail(selectedId);
    };

    const selectNode = (nodeId) => {
      if (!payload.nodes[nodeId]) {
        return;
      }
      selectedId = nodeId;
      updateVisibility();
      const selectedGroup = nodeGroups.find((group) => group.dataset.nodeId === nodeId);
      selectedGroup?.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
    };

    searchInput?.addEventListener('input', (event) => {
      searchText = String(event.target?.value || '').trim().toLowerCase();
      updateVisibility();
    });

    zoomOutButton?.addEventListener('click', () => setZoom(zoom - zoomStep));
    zoomResetButton?.addEventListener('click', () => setZoom(1));
    zoomInButton?.addEventListener('click', () => setZoom(zoom + zoomStep));
    svgWrap?.addEventListener('wheel', (event) => {
      if (!event.ctrlKey && !event.metaKey) {
        return;
      }
      event.preventDefault();
      setZoom(zoom + (event.deltaY < 0 ? 0.1 : -0.1));
    }, { passive: false });

    for (const button of filterButtons) {
      button.addEventListener('click', () => {
        activeStatus = button.dataset.statusFilter || 'all';
        for (const candidate of filterButtons) {
          candidate.classList.toggle('is-active', candidate === button);
        }
        updateVisibility();
      });
    }

    for (const group of nodeGroups) {
      const nodeId = group.dataset.nodeId || '';
      group.addEventListener('click', () => selectNode(nodeId));
      group.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectNode(nodeId);
        }
      });
    }

    for (const item of readyItems) {
      const displayId = item.dataset.displayId || '';
      item.addEventListener('click', () => selectNode(displayId));
    }

    applyZoom();
    updateVisibility();
  }
})();
    """
