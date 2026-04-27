"""Programmatic queries for progress multigraphs."""

from __future__ import annotations

from pathlib import Path

from .model import ProgressGraph, ProgressMultiGraphHistory


def load_history(path: str | Path) -> ProgressMultiGraphHistory:
    return ProgressMultiGraphHistory.from_json(Path(path).read_text(encoding="utf-8"))


def query_graph_summary(history: ProgressMultiGraphHistory, graph_id: str) -> dict[str, object]:
    return history.current_graph(graph_id).summary()


def query_ready_nodes(history: ProgressMultiGraphHistory) -> list[dict[str, str]]:
    return history.global_ready_nodes()


def query_independent_graph_sets(
    history: ProgressMultiGraphHistory,
) -> list[list[str]]:
    return [list(group) for group in history.independent_graph_sets()]


def query_topological_layers(
    graph: ProgressGraph,
) -> list[list[str]]:
    return [list(layer) for layer in graph.topological_layers()]


def query_condensed_view(
    graph: ProgressGraph,
    collapsed_cluster_ids: set[str] | None = None,
) -> dict[str, object]:
    return graph.build_condensed_view(collapsed_cluster_ids=collapsed_cluster_ids)