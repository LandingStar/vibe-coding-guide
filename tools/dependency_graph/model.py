"""Dependency graph data model: nodes, edges, and queryable graph."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

NodeKind = Literal["module", "class", "function", "protocol"]
EdgeKind = Literal["inherits", "implements", "imports", "calls", "references"]


@dataclass(frozen=True)
class GraphNode:
    """A symbol in the dependency graph."""

    id: str
    kind: NodeKind
    file_path: str
    line_number: int
    module: str


@dataclass(frozen=True)
class GraphEdge:
    """A directed relationship between two nodes."""

    source: str
    target: str
    kind: EdgeKind
    file_path: str
    line_number: int


class DependencyGraph:
    """Queryable dependency graph built from aggregated symbol relationships."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._outgoing: dict[str, list[GraphEdge]] = {}
        self._incoming: dict[str, list[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        self._outgoing.setdefault(node.id, [])
        self._incoming.setdefault(node.id, [])

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        self._outgoing.setdefault(edge.source, []).append(edge)
        self._incoming.setdefault(edge.target, []).append(edge)

    # --- queries ---

    def dependents_of(self, node_id: str) -> list[GraphNode]:
        """Return unique nodes that depend on *node_id* (incoming edges)."""
        seen: set[str] = set()
        result: list[GraphNode] = []
        for e in self._incoming.get(node_id, []):
            if e.source in self.nodes and e.source not in seen:
                seen.add(e.source)
                result.append(self.nodes[e.source])
        return result

    def dependencies_of(self, node_id: str) -> list[GraphNode]:
        """Return unique nodes that *node_id* depends on (outgoing edges)."""
        seen: set[str] = set()
        result: list[GraphNode] = []
        for e in self._outgoing.get(node_id, []):
            if e.target in self.nodes and e.target not in seen:
                seen.add(e.target)
                result.append(self.nodes[e.target])
        return result

    def implementors_of(self, protocol_id: str) -> list[GraphNode]:
        """Return nodes that implement or inherit from *protocol_id*."""
        return [
            self.nodes[e.source]
            for e in self._incoming.get(protocol_id, [])
            if e.kind in ("inherits", "implements") and e.source in self.nodes
        ]

    def edges_of(self, node_id: str, direction: str = "both") -> list[GraphEdge]:
        """Return edges involving *node_id*.

        direction: "outgoing", "incoming", or "both".
        """
        result: list[GraphEdge] = []
        if direction in ("outgoing", "both"):
            result.extend(self._outgoing.get(node_id, []))
        if direction in ("incoming", "both"):
            result.extend(self._incoming.get(node_id, []))
        return result

    # --- serialization ---

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(
            {
                "nodes": {nid: asdict(n) for nid, n in self.nodes.items()},
                "edges": [asdict(e) for e in self.edges],
            },
            indent=indent,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, data: str) -> DependencyGraph:
        raw = json.loads(data)
        graph = cls()
        for node_data in raw.get("nodes", {}).values():
            graph.add_node(GraphNode(**node_data))
        for edge_data in raw.get("edges", []):
            graph.add_edge(GraphEdge(**edge_data))
        return graph

    # --- summary ---

    def summary(self) -> dict:
        """Return a compact summary of graph contents."""
        from collections import Counter

        node_kinds = Counter(n.kind for n in self.nodes.values())
        edge_kinds = Counter(e.kind for e in self.edges)
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_kinds": dict(node_kinds),
            "edge_kinds": dict(edge_kinds),
        }
