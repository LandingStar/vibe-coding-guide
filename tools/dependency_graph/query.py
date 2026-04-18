"""Query interface for DependencyGraph — CLI and programmatic."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import DependencyGraph
from .impact import ChangeSet, ImpactAnalyzer, ImpactResult
from .coupling import CouplingAlert, CouplingChecker, CouplingStore


def load_graph(path: str | Path) -> DependencyGraph:
    """Load a dependency graph from a JSON file."""
    return DependencyGraph.from_json(Path(path).read_text(encoding="utf-8"))


def query_dependents(graph: DependencyGraph, node_id: str) -> list[dict]:
    """Return nodes that depend on *node_id*."""
    return [
        {"id": n.id, "kind": n.kind, "file": n.file_path, "line": n.line_number}
        for n in graph.dependents_of(node_id)
    ]


def query_dependencies(graph: DependencyGraph, node_id: str) -> list[dict]:
    """Return nodes that *node_id* depends on."""
    return [
        {"id": n.id, "kind": n.kind, "file": n.file_path, "line": n.line_number}
        for n in graph.dependencies_of(node_id)
    ]


def query_implementors(graph: DependencyGraph, protocol_id: str) -> list[dict]:
    """Return nodes that implement *protocol_id*."""
    return [
        {"id": n.id, "kind": n.kind, "file": n.file_path, "line": n.line_number}
        for n in graph.implementors_of(protocol_id)
    ]


def query_edges(graph: DependencyGraph, node_id: str, direction: str = "both") -> list[dict]:
    """Return edges involving *node_id*."""
    return [
        {
            "source": e.source,
            "target": e.target,
            "kind": e.kind,
            "file": e.file_path,
            "line": e.line_number,
        }
        for e in graph.edges_of(node_id, direction)
    ]


def query_impact(
    graph: DependencyGraph,
    changed_files: list[str] | None = None,
    changed_symbols: list[str] | None = None,
    max_depth: int = 2,
) -> dict:
    """Analyze change impact and return structured result."""
    analyzer = ImpactAnalyzer(graph, max_depth=max_depth)
    changes = ChangeSet(
        changed_files=changed_files or [],
        changed_symbols=changed_symbols or [],
    )
    result = analyzer.analyze(changes)
    return {
        "direct": result.direct,
        "transitive": result.transitive,
        "paths": result.paths,
        "depth": result.depth,
    }


def query_coupling(
    coupling_file: str | Path,
    changed_files: list[str] | None = None,
    changed_symbols: list[str] | None = None,
) -> list[dict]:
    """Check coupling annotations against changes."""
    store = CouplingStore(coupling_file)
    checker = CouplingChecker(store)
    alerts = checker.check(changed_files, changed_symbols)
    return [
        {
            "annotation_id": a.annotation_id,
            "description": a.description,
            "severity": a.severity,
            "triggered_by": a.triggered_by,
            "check_targets": [
                {"file_path": t.file_path, "symbol": t.symbol, "line_pattern": t.line_pattern}
                for t in a.check_targets
            ],
        }
        for a in alerts
    ]


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for graph queries."""
    parser = argparse.ArgumentParser(description="Query a dependency graph")
    parser.add_argument("graph_file", help="Path to graph JSON file")
    parser.add_argument(
        "command",
        choices=["dependents", "dependencies", "implementors", "edges", "summary", "impact", "coupling"],
        help="Query type",
    )
    parser.add_argument("node_id", nargs="?", help="Node ID to query")
    parser.add_argument(
        "--direction",
        choices=["incoming", "outgoing", "both"],
        default="both",
        help="Edge direction for 'edges' command",
    )
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=[],
        help="Changed file paths for 'impact' or 'coupling' command",
    )
    parser.add_argument(
        "--changed-symbols",
        nargs="*",
        default=[],
        help="Changed symbol IDs for 'impact' or 'coupling' command",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Max propagation depth for 'impact' command",
    )
    parser.add_argument(
        "--coupling-file",
        default=None,
        help="Path to coupling annotations JSON file",
    )

    args = parser.parse_args(argv)
    graph = load_graph(args.graph_file)

    if args.command == "summary":
        result = graph.summary()
    elif args.command == "impact":
        result = query_impact(
            graph,
            changed_files=args.changed_files,
            changed_symbols=args.changed_symbols,
            max_depth=args.max_depth,
        )
    elif args.command == "coupling":
        coupling_path = args.coupling_file or str(
            Path(args.graph_file).parent / "coupling_annotations.json"
        )
        result = query_coupling(
            coupling_path,
            changed_files=args.changed_files,
            changed_symbols=args.changed_symbols,
        )
    elif args.node_id is None:
        parser.error(f"node_id is required for '{args.command}' command")
        return
    elif args.command == "dependents":
        result = query_dependents(graph, args.node_id)
    elif args.command == "dependencies":
        result = query_dependencies(graph, args.node_id)
    elif args.command == "implementors":
        result = query_implementors(graph, args.node_id)
    elif args.command == "edges":
        result = query_edges(graph, args.node_id, args.direction)
    else:
        parser.error(f"Unknown command: {args.command}")
        return

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
