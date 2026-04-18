"""Change impact analysis — propagate changes through the dependency graph."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from .model import DependencyGraph, GraphNode


@dataclass
class ChangeSet:
    """Describes a set of changes to analyze."""

    changed_files: list[str] = field(default_factory=list)
    changed_symbols: list[str] = field(default_factory=list)


@dataclass
class ImpactResult:
    """Result of change impact analysis."""

    direct: list[str] = field(default_factory=list)
    transitive: list[str] = field(default_factory=list)
    paths: dict[str, list[str]] = field(default_factory=dict)
    depth: int = 0


class ImpactAnalyzer:
    """Analyze change impact by propagating through dependency graph edges."""

    def __init__(self, graph: DependencyGraph, max_depth: int = 2) -> None:
        self.graph = graph
        self.max_depth = max_depth

    def _resolve_files_to_symbols(self, files: list[str]) -> list[str]:
        """Map changed file paths to symbol node IDs in the graph."""
        result: list[str] = []
        for f in files:
            norm = Path(f).as_posix()
            for node in self.graph.nodes.values():
                node_path = Path(node.file_path).as_posix()
                if node_path.endswith(norm) or norm.endswith(node_path):
                    result.append(node.id)
        return result

    def analyze(self, changes: ChangeSet) -> ImpactResult:
        """Propagate changes through the graph and return impact result."""
        # Collect all seed nodes
        seeds: set[str] = set(changes.changed_symbols)
        seeds.update(self._resolve_files_to_symbols(changes.changed_files))

        if not seeds:
            return ImpactResult(depth=self.max_depth)

        # BFS propagation via incoming edges (who depends on changed nodes)
        visited: set[str] = set()
        direct: list[str] = []
        transitive: list[str] = []
        paths: dict[str, list[str]] = {}

        # Queue: (node_id, depth, path_from_seed)
        queue: deque[tuple[str, int, list[str]]] = deque()

        for seed in seeds:
            visited.add(seed)
            for edge in self.graph._incoming.get(seed, []):
                if edge.source not in visited and edge.source not in seeds:
                    queue.append((edge.source, 1, [seed, edge.source]))

        while queue:
            node_id, depth, path = queue.popleft()

            if node_id in visited:
                continue
            visited.add(node_id)

            if depth == 1:
                direct.append(node_id)
            else:
                transitive.append(node_id)
            paths[node_id] = path

            if depth < self.max_depth:
                for edge in self.graph._incoming.get(node_id, []):
                    if edge.source not in visited and edge.source not in seeds:
                        queue.append(
                            (edge.source, depth + 1, path + [edge.source])
                        )

        return ImpactResult(
            direct=direct,
            transitive=transitive,
            paths=paths,
            depth=self.max_depth,
        )
