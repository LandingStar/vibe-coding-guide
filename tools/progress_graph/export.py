"""User-facing export helpers for progress multigraphs."""

from __future__ import annotations

from pathlib import Path

from .model import ProgressCluster, ProgressEdge, ProgressGraph, ProgressMultiGraphHistory, ProgressNode

_EXPORT_SCHEMA_VERSION = "1.0"


def export_graph_surface(
    graph: ProgressGraph,
    *,
    collapsed_cluster_ids: set[str] | None = None,
) -> dict[str, object]:
    condensed = graph.build_condensed_view(collapsed_cluster_ids=collapsed_cluster_ids)
    return {
        "graph_id": graph.graph_id,
        "snapshot_id": graph.snapshot_id,
        "title": graph.title,
        "recorded_at": graph.recorded_at,
        "summary": graph.summary(),
        "raw": {
            "nodes": [_export_raw_node(graph.graph_id, node) for node in _sorted_nodes(graph)],
            "edges": [_export_raw_edge(graph.graph_id, edge) for edge in _sorted_edges(graph)],
            "clusters": [
                _export_raw_cluster(graph.graph_id, cluster)
                for cluster in _sorted_clusters(graph)
            ],
        },
        "display": {
            "nodes": [
                _export_display_node(graph.graph_id, node)
                for node in list(condensed["nodes"])
            ],
            "edges": [
                _export_display_edge(graph.graph_id, edge)
                for edge in list(condensed["edges"])
            ],
            "mapping": dict(condensed["mapping"]),
        },
        "ready_nodes": [
            {
                "id": node.id,
                "key": _scoped_key(graph.graph_id, node.id),
                "title": node.title,
                "kind": node.kind,
                "status": node.status,
            }
            for node in graph.ready_nodes()
        ],
        "topological_layers": [list(layer) for layer in graph.topological_layers()],
    }


def export_history_surface(
    history: ProgressMultiGraphHistory,
    *,
    collapsed_clusters_by_graph: dict[str, set[str]] | None = None,
) -> dict[str, object]:
    collapsed_clusters = collapsed_clusters_by_graph or {}
    graph_surfaces: list[dict[str, object]] = []
    display_ids_by_graph: dict[str, dict[str, str]] = {}

    for graph_id in sorted(history.current_snapshot_by_graph):
        surface = export_graph_surface(
            history.current_graph(graph_id),
            collapsed_cluster_ids=collapsed_clusters.get(graph_id),
        )
        graph_surfaces.append(surface)
        display_ids_by_graph[graph_id] = {
            node_id: str(display_id)
            for node_id, display_id in dict(surface["display"]["mapping"]).items()
        }

    ready_nodes = []
    for item in history.global_ready_nodes():
        ready_nodes.append(
            {
                **item,
                "node_key": _scoped_key(str(item["graph_id"]), str(item["node_id"])),
            }
        )

    cross_graph_edges = []
    for edge in sorted(
        history.cross_graph_edges,
        key=lambda item: (
            item.source_graph_id,
            item.source_node_id,
            item.target_graph_id,
            item.target_node_id,
            item.kind,
            item.is_directed,
            item.summary,
        ),
    ):
        source_display_id = display_ids_by_graph.get(edge.source_graph_id, {}).get(
            edge.source_node_id,
            edge.source_node_id,
        )
        target_display_id = display_ids_by_graph.get(edge.target_graph_id, {}).get(
            edge.target_node_id,
            edge.target_node_id,
        )
        cross_graph_edges.append(
            {
                "source_graph_id": edge.source_graph_id,
                "source_node_id": edge.source_node_id,
                "source_key": _scoped_key(edge.source_graph_id, edge.source_node_id),
                "source_display_id": source_display_id,
                "source_display_key": _scoped_key(edge.source_graph_id, source_display_id),
                "target_graph_id": edge.target_graph_id,
                "target_node_id": edge.target_node_id,
                "target_key": _scoped_key(edge.target_graph_id, edge.target_node_id),
                "target_display_id": target_display_id,
                "target_display_key": _scoped_key(edge.target_graph_id, target_display_id),
                "kind": edge.kind,
                "is_directed": edge.is_directed,
                "summary": edge.summary,
                "metadata": dict(edge.metadata),
            }
        )

    return {
        "schema_version": _EXPORT_SCHEMA_VERSION,
        "history_metadata": dict(history.metadata),
        "history_summary": history.summary(),
        "graphs": graph_surfaces,
        "cross_graph_edges": cross_graph_edges,
        "independent_graph_sets": [list(group) for group in history.independent_graph_sets()],
        "ready_nodes": ready_nodes,
    }


def load_export_surface(
    path: str | Path,
    *,
    collapsed_clusters_by_graph: dict[str, set[str]] | None = None,
) -> dict[str, object]:
    history = ProgressMultiGraphHistory.from_json(Path(path).read_text(encoding="utf-8"))
    return export_history_surface(
        history,
        collapsed_clusters_by_graph=collapsed_clusters_by_graph,
    )


def _sorted_nodes(graph: ProgressGraph) -> list[ProgressNode]:
    return [graph.nodes[node_id] for node_id in sorted(graph.nodes)]


def _sorted_edges(graph: ProgressGraph) -> list[ProgressEdge]:
    return sorted(
        graph.edges,
        key=lambda edge: (
            edge.source,
            edge.target,
            edge.kind,
            edge.is_directed,
            edge.summary,
        ),
    )


def _sorted_clusters(graph: ProgressGraph) -> list[ProgressCluster]:
    return [graph.clusters[cluster_id] for cluster_id in sorted(graph.clusters)]


def _export_raw_node(graph_id: str, node: ProgressNode) -> dict[str, object]:
    return {
        "id": node.id,
        "key": _scoped_key(graph_id, node.id),
        "graph_id": graph_id,
        "title": node.title,
        "kind": node.kind,
        "status": node.status,
        "summary": node.summary,
        "tags": list(node.tags),
        "metadata": dict(node.metadata),
    }


def _export_raw_edge(graph_id: str, edge: ProgressEdge) -> dict[str, object]:
    return {
        "source": edge.source,
        "source_key": _scoped_key(graph_id, edge.source),
        "target": edge.target,
        "target_key": _scoped_key(graph_id, edge.target),
        "kind": edge.kind,
        "is_directed": edge.is_directed,
        "summary": edge.summary,
        "metadata": dict(edge.metadata),
    }


def _export_raw_cluster(graph_id: str, cluster: ProgressCluster) -> dict[str, object]:
    return {
        "id": cluster.id,
        "key": _scoped_key(graph_id, cluster.id),
        "graph_id": graph_id,
        "title": cluster.title,
        "member_ids": list(cluster.member_ids),
        "member_keys": [_scoped_key(graph_id, member_id) for member_id in cluster.member_ids],
        "collapsed": cluster.collapsed,
        "summary": cluster.summary,
        "metadata": dict(cluster.metadata),
    }


def _export_display_node(graph_id: str, node: dict[str, object]) -> dict[str, object]:
    exported = dict(node)
    local_id = str(exported["id"])
    exported["key"] = _scoped_key(graph_id, local_id)
    exported["graph_id"] = graph_id
    member_ids = list(exported.get("member_ids", []))
    if member_ids:
        exported["member_keys"] = [_scoped_key(graph_id, member_id) for member_id in member_ids]
    return exported


def _export_display_edge(graph_id: str, edge: dict[str, object]) -> dict[str, object]:
    exported = dict(edge)
    exported["source_key"] = _scoped_key(graph_id, str(exported["source"]))
    exported["target_key"] = _scoped_key(graph_id, str(exported["target"]))
    return exported


def _scoped_key(graph_id: str, local_id: str) -> str:
    return f"{graph_id}::{local_id}"