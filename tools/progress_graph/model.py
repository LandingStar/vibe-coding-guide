"""Snapshot-backed progress multigraph foundation."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from typing import Literal

ProgressNodeKind = Literal["task", "milestone", "decision", "reference"]
ProgressNodeStatus = Literal[
    "pending",
    "in_progress",
    "blocked",
    "completed",
    "archived",
]
ProgressEdgeKind = Literal["workflow", "dependency", "linkage"]

_READY_BLOCKING_EDGE_KINDS: tuple[ProgressEdgeKind, ...] = ("workflow", "dependency")
_COMPLETED_NODE_STATUSES = frozenset({"completed", "archived"})


@dataclass(frozen=True)
class ProgressNode:
    """A single progress node inside one graph snapshot."""

    id: str
    title: str
    kind: ProgressNodeKind = "task"
    status: ProgressNodeStatus = "pending"
    summary: str = ""
    tags: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProgressEdge:
    """A typed relationship between two nodes in the same graph."""

    source: str
    target: str
    kind: ProgressEdgeKind
    is_directed: bool = True
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProgressCluster:
    """A manually declared node group that can collapse into one display node."""

    id: str
    title: str
    member_ids: tuple[str, ...]
    collapsed: bool = False
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CrossGraphEdge:
    """A typed relationship between nodes that live in different current graphs."""

    source_graph_id: str
    source_node_id: str
    target_graph_id: str
    target_node_id: str
    kind: ProgressEdgeKind
    is_directed: bool = True
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class ProgressGraph:
    """A single graph snapshot with typed edges and cluster-aware queries."""

    def __init__(
        self,
        *,
        graph_id: str,
        snapshot_id: str,
        title: str,
        recorded_at: str = "",
        parent_snapshot_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.graph_id = graph_id
        self.snapshot_id = snapshot_id
        self.title = title
        self.recorded_at = recorded_at
        self.parent_snapshot_id = parent_snapshot_id
        self.metadata = dict(metadata or {})
        self.nodes: dict[str, ProgressNode] = {}
        self.edges: list[ProgressEdge] = []
        self.clusters: dict[str, ProgressCluster] = {}

    def add_node(self, node: ProgressNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ProgressEdge) -> None:
        self.edges.append(edge)

    def add_cluster(self, cluster: ProgressCluster) -> None:
        self.clusters[cluster.id] = cluster

    def predecessors(
        self,
        node_id: str,
        edge_kinds: tuple[ProgressEdgeKind, ...] | None = None,
    ) -> list[ProgressNode]:
        kinds = edge_kinds or ("workflow", "dependency", "linkage")
        seen: set[str] = set()
        result: list[ProgressNode] = []
        for edge in self.edges:
            if edge.kind not in kinds:
                continue
            if edge.is_directed and edge.target == node_id and edge.source in self.nodes:
                if edge.source not in seen:
                    seen.add(edge.source)
                    result.append(self.nodes[edge.source])
            elif not edge.is_directed:
                neighbor_id = None
                if edge.source == node_id and edge.target in self.nodes:
                    neighbor_id = edge.target
                elif edge.target == node_id and edge.source in self.nodes:
                    neighbor_id = edge.source
                if neighbor_id and neighbor_id not in seen:
                    seen.add(neighbor_id)
                    result.append(self.nodes[neighbor_id])
        return sorted(result, key=lambda node: node.id)

    def successors(
        self,
        node_id: str,
        edge_kinds: tuple[ProgressEdgeKind, ...] | None = None,
    ) -> list[ProgressNode]:
        kinds = edge_kinds or ("workflow", "dependency", "linkage")
        seen: set[str] = set()
        result: list[ProgressNode] = []
        for edge in self.edges:
            if edge.kind not in kinds:
                continue
            if edge.is_directed and edge.source == node_id and edge.target in self.nodes:
                if edge.target not in seen:
                    seen.add(edge.target)
                    result.append(self.nodes[edge.target])
            elif not edge.is_directed:
                neighbor_id = None
                if edge.source == node_id and edge.target in self.nodes:
                    neighbor_id = edge.target
                elif edge.target == node_id and edge.source in self.nodes:
                    neighbor_id = edge.source
                if neighbor_id and neighbor_id not in seen:
                    seen.add(neighbor_id)
                    result.append(self.nodes[neighbor_id])
        return sorted(result, key=lambda node: node.id)

    def ready_nodes(self) -> list[ProgressNode]:
        """Return nodes whose workflow/dependency predecessors are settled."""

        ready: list[ProgressNode] = []
        for node_id in sorted(self.nodes):
            node = self.nodes[node_id]
            if node.status != "pending":
                continue
            blockers = [
                predecessor
                for predecessor in self.predecessors(
                    node_id,
                    edge_kinds=_READY_BLOCKING_EDGE_KINDS,
                )
                if predecessor.status not in _COMPLETED_NODE_STATUSES
            ]
            if not blockers:
                ready.append(node)
        return ready

    def topological_layers(
        self,
        edge_kinds: tuple[ProgressEdgeKind, ...] = _READY_BLOCKING_EDGE_KINDS,
    ) -> tuple[tuple[str, ...], ...]:
        """Return deterministic DAG layers for workflow/dependency edges."""

        indegree = {node_id: 0 for node_id in self.nodes}
        outgoing: dict[str, set[str]] = defaultdict(set)
        for edge in self.edges:
            if edge.kind not in edge_kinds or not edge.is_directed:
                continue
            if edge.source not in self.nodes or edge.target not in self.nodes:
                continue
            if edge.target in outgoing[edge.source]:
                continue
            outgoing[edge.source].add(edge.target)
            indegree[edge.target] += 1

        queue = deque(sorted(node_id for node_id, degree in indegree.items() if degree == 0))
        layers: list[tuple[str, ...]] = []
        visited = 0
        while queue:
            current_layer = tuple(queue)
            layers.append(current_layer)
            next_layer: list[str] = []
            while queue:
                source = queue.popleft()
                visited += 1
                for target in sorted(outgoing.get(source, ())):
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        next_layer.append(target)
            queue.extend(sorted(next_layer))

        if visited != len(self.nodes):
            raise ValueError("workflow/dependency edges must form a DAG")
        return tuple(layers)

    def cluster_boundary(
        self,
        cluster_id: str,
        edge_kinds: tuple[ProgressEdgeKind, ...] | None = None,
    ) -> list[ProgressEdge]:
        cluster = self.clusters[cluster_id]
        members = set(cluster.member_ids)
        kinds = edge_kinds or ("workflow", "dependency", "linkage")
        return [
            edge
            for edge in self.edges
            if edge.kind in kinds
            and ((edge.source in members) ^ (edge.target in members))
        ]

    def build_condensed_view(
        self,
        collapsed_cluster_ids: set[str] | None = None,
    ) -> dict[str, object]:
        """Build a cluster-collapsed display view without losing node mapping."""

        explicit_ids = collapsed_cluster_ids or set()
        collapsed_ids = {
            cluster_id
            for cluster_id, cluster in self.clusters.items()
            if cluster.collapsed or cluster_id in explicit_ids
        }
        proxy_by_member: dict[str, str] = {}
        condensed_nodes: list[dict[str, object]] = []

        for cluster_id in sorted(collapsed_ids):
            cluster = self.clusters[cluster_id]
            condensed_nodes.append(
                {
                    "id": cluster.id,
                    "kind": "cluster",
                    "title": cluster.title,
                    "collapsed": True,
                    "member_ids": list(cluster.member_ids),
                    "summary": cluster.summary,
                }
            )
            for member_id in cluster.member_ids:
                proxy_by_member[member_id] = cluster.id

        for node_id in sorted(self.nodes):
            if node_id in proxy_by_member:
                continue
            node = self.nodes[node_id]
            condensed_nodes.append(
                {
                    "id": node.id,
                    "kind": node.kind,
                    "title": node.title,
                    "status": node.status,
                    "summary": node.summary,
                    "tags": list(node.tags),
                }
            )

        aggregated_edges: dict[tuple[str, str, str, bool], int] = defaultdict(int)
        for edge in self.edges:
            source = proxy_by_member.get(edge.source, edge.source)
            target = proxy_by_member.get(edge.target, edge.target)
            if source == target:
                continue
            aggregated_edges[(source, target, edge.kind, edge.is_directed)] += 1

        condensed_edges = [
            {
                "source": source,
                "target": target,
                "kind": kind,
                "is_directed": is_directed,
                "count": count,
            }
            for (source, target, kind, is_directed), count in sorted(aggregated_edges.items())
        ]
        return {
            "graph_id": self.graph_id,
            "snapshot_id": self.snapshot_id,
            "nodes": condensed_nodes,
            "edges": condensed_edges,
            "mapping": dict(sorted(proxy_by_member.items())),
        }

    def check_invariants(self) -> list[str]:
        errors: list[str] = []

        member_to_cluster: dict[str, str] = {}
        for cluster in self.clusters.values():
            for member_id in cluster.member_ids:
                if member_id not in self.nodes:
                    errors.append(f"cluster {cluster.id!r} references unknown node {member_id!r}")
                    continue
                previous_cluster = member_to_cluster.get(member_id)
                if previous_cluster and previous_cluster != cluster.id:
                    errors.append(
                        f"node {member_id!r} belongs to multiple clusters: {previous_cluster!r}, {cluster.id!r}"
                    )
                member_to_cluster[member_id] = cluster.id

        for edge in self.edges:
            if edge.source not in self.nodes:
                errors.append(f"edge source {edge.source!r} does not exist")
            if edge.target not in self.nodes:
                errors.append(f"edge target {edge.target!r} does not exist")

        try:
            self.topological_layers()
        except ValueError as exc:
            errors.append(str(exc))

        return errors

    def validate(self) -> None:
        errors = self.check_invariants()
        if errors:
            raise ValueError("; ".join(errors))

    def summary(self) -> dict[str, object]:
        edge_counts: dict[str, int] = defaultdict(int)
        for edge in self.edges:
            edge_counts[edge.kind] += 1
        return {
            "graph_id": self.graph_id,
            "snapshot_id": self.snapshot_id,
            "title": self.title,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "cluster_count": len(self.clusters),
            "edge_kinds": dict(sorted(edge_counts.items())),
            "ready_node_count": len(self.ready_nodes()),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "graph_id": self.graph_id,
            "snapshot_id": self.snapshot_id,
            "title": self.title,
            "recorded_at": self.recorded_at,
            "parent_snapshot_id": self.parent_snapshot_id,
            "metadata": dict(self.metadata),
            "nodes": {node_id: asdict(node) for node_id, node in sorted(self.nodes.items())},
            "edges": [asdict(edge) for edge in self.edges],
            "clusters": {
                cluster_id: asdict(cluster)
                for cluster_id, cluster in sorted(self.clusters.items())
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProgressGraph":
        graph = cls(
            graph_id=str(data["graph_id"]),
            snapshot_id=str(data["snapshot_id"]),
            title=str(data["title"]),
            recorded_at=str(data.get("recorded_at", "")),
            parent_snapshot_id=data.get("parent_snapshot_id") or None,
            metadata=dict(data.get("metadata", {})),
        )
        for node_data in dict(data.get("nodes", {})).values():
            graph.add_node(
                ProgressNode(
                    id=str(node_data["id"]),
                    title=str(node_data["title"]),
                    kind=str(node_data.get("kind", "task")),
                    status=str(node_data.get("status", "pending")),
                    summary=str(node_data.get("summary", "")),
                    tags=tuple(node_data.get("tags", [])),
                    metadata=dict(node_data.get("metadata", {})),
                )
            )
        for edge_data in list(data.get("edges", [])):
            graph.add_edge(
                ProgressEdge(
                    source=str(edge_data["source"]),
                    target=str(edge_data["target"]),
                    kind=str(edge_data["kind"]),
                    is_directed=bool(edge_data.get("is_directed", True)),
                    summary=str(edge_data.get("summary", "")),
                    metadata=dict(edge_data.get("metadata", {})),
                )
            )
        for cluster_data in dict(data.get("clusters", {})).values():
            graph.add_cluster(
                ProgressCluster(
                    id=str(cluster_data["id"]),
                    title=str(cluster_data["title"]),
                    member_ids=tuple(cluster_data.get("member_ids", [])),
                    collapsed=bool(cluster_data.get("collapsed", False)),
                    summary=str(cluster_data.get("summary", "")),
                    metadata=dict(cluster_data.get("metadata", {})),
                )
            )
        return graph

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "ProgressGraph":
        return cls.from_dict(json.loads(data))


class ProgressMultiGraphHistory:
    """Multi-graph current view plus snapshot-preserved history."""

    def __init__(self, *, metadata: dict[str, str] | None = None) -> None:
        self.metadata = dict(metadata or {})
        self.snapshots: dict[str, ProgressGraph] = {}
        self.current_snapshot_by_graph: dict[str, str] = {}
        self.cross_graph_edges: list[CrossGraphEdge] = []

    def add_snapshot(self, graph: ProgressGraph, *, make_current: bool = True) -> None:
        if graph.snapshot_id in self.snapshots:
            raise ValueError(f"duplicate snapshot_id: {graph.snapshot_id}")
        if graph.parent_snapshot_id:
            parent = self.snapshots.get(graph.parent_snapshot_id)
            if parent is None:
                raise ValueError(f"unknown parent_snapshot_id: {graph.parent_snapshot_id}")
            if parent.graph_id != graph.graph_id:
                raise ValueError("parent snapshot must belong to the same graph_id")
        graph.validate()
        self.snapshots[graph.snapshot_id] = graph
        if make_current:
            self.current_snapshot_by_graph[graph.graph_id] = graph.snapshot_id

    def current_graph(self, graph_id: str) -> ProgressGraph:
        snapshot_id = self.current_snapshot_by_graph[graph_id]
        return self.snapshots[snapshot_id]

    def history_for(self, graph_id: str) -> tuple[ProgressGraph, ...]:
        current = self.current_graph(graph_id)
        chain: list[ProgressGraph] = [current]
        seen = {current.snapshot_id}
        parent_snapshot_id = current.parent_snapshot_id
        while parent_snapshot_id:
            if parent_snapshot_id in seen:
                raise ValueError("snapshot parent chain contains a cycle")
            parent = self.snapshots[parent_snapshot_id]
            chain.append(parent)
            seen.add(parent.snapshot_id)
            parent_snapshot_id = parent.parent_snapshot_id
        return tuple(reversed(chain))

    def add_cross_graph_edge(self, edge: CrossGraphEdge) -> None:
        self.cross_graph_edges.append(edge)

    def independent_graph_sets(self) -> tuple[tuple[str, ...], ...]:
        graph_ids = sorted(self.current_snapshot_by_graph)
        parents = {graph_id: graph_id for graph_id in graph_ids}

        def find(graph_id: str) -> str:
            while parents[graph_id] != graph_id:
                parents[graph_id] = parents[parents[graph_id]]
                graph_id = parents[graph_id]
            return graph_id

        def union(left: str, right: str) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parents[right_root] = left_root

        for edge in self.cross_graph_edges:
            if edge.source_graph_id in parents and edge.target_graph_id in parents:
                union(edge.source_graph_id, edge.target_graph_id)

        groups: dict[str, list[str]] = defaultdict(list)
        for graph_id in graph_ids:
            groups[find(graph_id)].append(graph_id)
        return tuple(tuple(sorted(group)) for group in sorted(groups.values(), key=lambda item: item[0]))

    def global_ready_nodes(self) -> list[dict[str, str]]:
        ready: list[dict[str, str]] = []
        current_graphs = {
            graph_id: self.current_graph(graph_id)
            for graph_id in sorted(self.current_snapshot_by_graph)
        }
        for graph_id, graph in current_graphs.items():
            for node in graph.ready_nodes():
                if self._cross_graph_dependencies_resolved(current_graphs, graph_id, node.id):
                    ready.append(
                        {
                            "graph_id": graph_id,
                            "snapshot_id": graph.snapshot_id,
                            "node_id": node.id,
                            "title": node.title,
                        }
                    )
        return ready

    def _cross_graph_dependencies_resolved(
        self,
        current_graphs: dict[str, ProgressGraph],
        graph_id: str,
        node_id: str,
    ) -> bool:
        for edge in self.cross_graph_edges:
            if edge.kind not in _READY_BLOCKING_EDGE_KINDS or not edge.is_directed:
                continue
            if edge.target_graph_id != graph_id or edge.target_node_id != node_id:
                continue
            source_graph = current_graphs.get(edge.source_graph_id)
            if source_graph is None:
                return False
            source_node = source_graph.nodes.get(edge.source_node_id)
            if source_node is None or source_node.status not in _COMPLETED_NODE_STATUSES:
                return False
        return True

    def check_invariants(self) -> list[str]:
        errors: list[str] = []
        for graph in self.snapshots.values():
            errors.extend(graph.check_invariants())

        current_graphs = {
            graph_id: self.current_graph(graph_id)
            for graph_id in self.current_snapshot_by_graph
        }
        for edge in self.cross_graph_edges:
            source_graph = current_graphs.get(edge.source_graph_id)
            target_graph = current_graphs.get(edge.target_graph_id)
            if source_graph is None:
                errors.append(f"cross-graph edge source graph {edge.source_graph_id!r} does not exist")
                continue
            if target_graph is None:
                errors.append(f"cross-graph edge target graph {edge.target_graph_id!r} does not exist")
                continue
            if edge.source_node_id not in source_graph.nodes:
                errors.append(
                    f"cross-graph edge source node {edge.source_node_id!r} does not exist in graph {edge.source_graph_id!r}"
                )
            if edge.target_node_id not in target_graph.nodes:
                errors.append(
                    f"cross-graph edge target node {edge.target_node_id!r} does not exist in graph {edge.target_graph_id!r}"
                )
        return errors

    def validate(self) -> None:
        errors = self.check_invariants()
        if errors:
            raise ValueError("; ".join(errors))

    def summary(self) -> dict[str, object]:
        return {
            "current_graph_count": len(self.current_snapshot_by_graph),
            "snapshot_count": len(self.snapshots),
            "cross_graph_edge_count": len(self.cross_graph_edges),
            "independent_graph_sets": [list(group) for group in self.independent_graph_sets()],
            "ready_node_count": len(self.global_ready_nodes()),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "metadata": dict(self.metadata),
            "snapshots": {
                snapshot_id: graph.to_dict()
                for snapshot_id, graph in sorted(self.snapshots.items())
            },
            "current_snapshot_by_graph": dict(sorted(self.current_snapshot_by_graph.items())),
            "cross_graph_edges": [asdict(edge) for edge in self.cross_graph_edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProgressMultiGraphHistory":
        history = cls(metadata=dict(data.get("metadata", {})))
        for snapshot_id, graph_data in sorted(dict(data.get("snapshots", {})).items()):
            graph = ProgressGraph.from_dict(dict(graph_data))
            history.snapshots[snapshot_id] = graph
        history.current_snapshot_by_graph = dict(data.get("current_snapshot_by_graph", {}))
        history.cross_graph_edges = [
            CrossGraphEdge(
                source_graph_id=str(edge_data["source_graph_id"]),
                source_node_id=str(edge_data["source_node_id"]),
                target_graph_id=str(edge_data["target_graph_id"]),
                target_node_id=str(edge_data["target_node_id"]),
                kind=str(edge_data["kind"]),
                is_directed=bool(edge_data.get("is_directed", True)),
                summary=str(edge_data.get("summary", "")),
                metadata=dict(edge_data.get("metadata", {})),
            )
            for edge_data in list(data.get("cross_graph_edges", []))
        ]
        return history

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "ProgressMultiGraphHistory":
        return cls.from_dict(json.loads(data))