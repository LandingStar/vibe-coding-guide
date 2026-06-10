"""Reference adapters for generating dependency baseline graphs.

The adapters in this module are deliberately conservative. They are intended
to produce a contract-compatible ``baseline_graph.json`` without making the MCP
impact tools responsible for generating or refreshing it.
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .aggregator import _classify_edge, _uri_to_path
from .model import DependencyGraph, GraphEdge, GraphNode

CONTRACT_NAME = "dependency-baseline-generator-contract"
CONTRACT_VERSION = "0.1"
GENERATOR_ID = "doc-based-coding-reference-baseline-adapter"
GENERATOR_VERSION = "0.1.0"

DEFAULT_EXCLUDES = [
    ".git/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "node_modules/**",
]

LANGUAGE_PATTERNS = {
    "python": ["**/*.py"],
    "javascript": ["**/*.js", "**/*.mjs", "**/*.cjs", "**/*.jsx"],
}

FORBIDDEN_PATH_PARTS = {".venv", "venv", "__pycache__", "build", "dist", "node_modules"}


class BaselineAdapterError(RuntimeError):
    """Raised when a baseline lifecycle operation cannot be completed."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_language(language: str) -> str:
    normalized = language.strip().lower()
    if normalized in {"py", "python"}:
        return "python"
    if normalized in {"js", "javascript", "node"}:
        return "javascript"
    raise BaselineAdapterError(f"Unsupported language: {language}")


def _as_posix_relative(path: Path, project_root: Path) -> str:
    path = path.resolve()
    root = project_root.resolve()
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise BaselineAdapterError(f"Path is outside project root: {path}") from exc


def _module_id_from_relative_path(rel_path: str) -> str:
    path = Path(rel_path)
    without_suffix = path.with_suffix("")
    parts = list(without_suffix.parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(part for part in parts if part)


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        pattern = pattern.replace("\\", "/")
        if pattern.endswith("/**") and normalized.startswith(pattern[:-3].rstrip("/") + "/"):
            return True
        if fnmatch.fnmatch(normalized, pattern):
            return True
        if fnmatch.fnmatch(Path(normalized).name, pattern):
            return True
    return False


def _iter_source_files(
    project_root: Path,
    languages: Sequence[str],
    includes: Sequence[str] | None = None,
    excludes: Sequence[str] | None = None,
) -> list[Path]:
    include_patterns: list[str] = []
    if includes:
        include_patterns.extend(includes)
    else:
        for language in languages:
            include_patterns.extend(LANGUAGE_PATTERNS[language])

    exclude_patterns = list(DEFAULT_EXCLUDES)
    if excludes:
        exclude_patterns.extend(excludes)

    seen: set[Path] = set()
    files: list[Path] = []
    for pattern in include_patterns:
        for path in project_root.glob(pattern):
            if not path.is_file():
                continue
            rel = _as_posix_relative(path, project_root)
            if _matches_any(rel, exclude_patterns):
                continue
            if path not in seen:
                seen.add(path)
                files.append(path)
    return sorted(files)


def _add_node_once(graph: DependencyGraph, node: GraphNode) -> None:
    if node.id not in graph.nodes:
        graph.add_node(node)


def _add_edge_once(graph: DependencyGraph, edge: GraphEdge, seen_edges: set[tuple[Any, ...]]) -> None:
    key = (edge.source, edge.target, edge.kind, edge.file_path, edge.line_number)
    if key in seen_edges:
        return
    seen_edges.add(key)
    graph.add_edge(edge)


def _line_content(source_lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(source_lines):
        return source_lines[lineno - 1].rstrip()
    return ""


def _class_base_names(node: ast.ClassDef) -> list[str]:
    names: list[str] = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def _is_protocol_class(node: ast.ClassDef) -> bool:
    return "Protocol" in _class_base_names(node)


def _resolve_python_import_target(
    module_id: str,
    import_from_module: str | None,
    alias_name: str,
    graph: DependencyGraph,
) -> str | None:
    if import_from_module:
        symbol_candidate = f"{import_from_module}.{alias_name}"
        if symbol_candidate in graph.nodes:
            return symbol_candidate
        if import_from_module in graph.nodes:
            return import_from_module
    if alias_name in graph.nodes:
        return alias_name
    root_name = alias_name.split(".", 1)[0]
    if root_name in graph.nodes:
        return root_name
    if module_id != alias_name and alias_name in graph.nodes:
        return alias_name
    return None


def _discover_python(
    graph: DependencyGraph,
    project_root: Path,
    files: Sequence[Path],
    diagnostics: list[dict[str, Any]],
    seen_edges: set[tuple[Any, ...]],
) -> None:
    parsed: list[tuple[Path, str, list[str], ast.Module]] = []
    simple_name_index: dict[str, list[str]] = {}

    for path in files:
        rel = _as_posix_relative(path, project_root)
        module_id = _module_id_from_relative_path(rel)
        if not module_id:
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            diagnostics.append({
                "level": "warning",
                "language": "python",
                "file_path": rel,
                "message": f"Skipped Python file: {exc}",
            })
            continue

        source_lines = source.splitlines()
        parsed.append((path, rel, source_lines, tree))
        _add_node_once(graph, GraphNode(module_id, "module", rel, 1, module_id))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                kind = "protocol" if _is_protocol_class(node) else "class"
                symbol_id = f"{module_id}.{node.name}"
                _add_node_once(graph, GraphNode(symbol_id, kind, rel, node.lineno, module_id))
                simple_name_index.setdefault(node.name, []).append(symbol_id)
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                symbol_id = f"{module_id}.{node.name}"
                _add_node_once(graph, GraphNode(symbol_id, "function", rel, node.lineno, module_id))
                simple_name_index.setdefault(node.name, []).append(symbol_id)

    for _path, rel, source_lines, tree in parsed:
        module_id = _module_id_from_relative_path(rel)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _resolve_python_import_target(module_id, None, alias.name, graph)
                    if target:
                        _add_edge_once(
                            graph,
                            GraphEdge(module_id, target, "imports", rel, node.lineno),
                            seen_edges,
                        )
            elif isinstance(node, ast.ImportFrom):
                import_module = node.module
                for alias in node.names:
                    target = _resolve_python_import_target(module_id, import_module, alias.name, graph)
                    if target:
                        _add_edge_once(
                            graph,
                            GraphEdge(module_id, target, "imports", rel, node.lineno),
                            seen_edges,
                        )
            elif isinstance(node, ast.ClassDef):
                source_id = f"{module_id}.{node.name}"
                for base_name in _class_base_names(node):
                    targets = simple_name_index.get(base_name, [])
                    if len(targets) != 1:
                        continue
                    target = targets[0]
                    target_kind = graph.nodes[target].kind
                    kind = "implements" if target_kind == "protocol" else "inherits"
                    _add_edge_once(
                        graph,
                        GraphEdge(source_id, target, kind, rel, node.lineno),
                        seen_edges,
                    )

        # Conservative call/reference extraction is intentionally omitted. The
        # reference adapter prefers partial coverage plus diagnostics over a
        # noisy graph that looks more complete than it is.
        if "typing.Protocol" in "\n".join(source_lines):
            diagnostics.append({
                "level": "info",
                "language": "python",
                "file_path": rel,
                "message": "Protocol inheritance is detected by simple base-name matching.",
            })


JS_CLASS_RE = re.compile(
    r"^\s*(?:export\s+default\s+|export\s+)?class\s+([A-Za-z_$][\w$]*)(?:\s+extends\s+([A-Za-z_$][\w$]*))?",
)
JS_FUNCTION_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("
)
JS_ARROW_RE = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
)
JS_IMPORT_RE = re.compile(r"\bimport\b(?:[^'\"]*\bfrom\s*)?['\"]([^'\"]+)['\"]")
JS_NAMED_IMPORT_RE = re.compile(r"\bimport\s*\{([^}]+)\}\s*from\s*['\"]([^'\"]+)['\"]")
JS_REQUIRE_RE = re.compile(r"\brequire\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")


def _resolve_js_module(specifier: str, source_rel: str, graph: DependencyGraph) -> str | None:
    if not specifier.startswith("."):
        return None
    source_dir = Path(source_rel).parent
    base = source_dir / specifier
    candidate_paths = [base] if base.suffix else [
        Path(base.as_posix() + ".js"),
        Path(base.as_posix() + ".mjs"),
        Path(base.as_posix() + ".cjs"),
        Path(base.as_posix() + ".jsx"),
        base / "index.js",
    ]
    candidates = [_module_id_from_relative_path(path.as_posix()) for path in candidate_paths]
    for candidate in candidates:
        if candidate in graph.nodes:
            return candidate
    return None


def _js_imported_names(import_clause: str) -> list[str]:
    names: list[str] = []
    for part in import_clause.split(","):
        raw = part.strip()
        if not raw:
            continue
        # Handles `Foo as Bar` by linking to the exported source name.
        name = raw.split(" as ", 1)[0].strip()
        if name:
            names.append(name)
    return names


def _discover_javascript(
    graph: DependencyGraph,
    project_root: Path,
    files: Sequence[Path],
    diagnostics: list[dict[str, Any]],
    seen_edges: set[tuple[Any, ...]],
) -> None:
    parsed: list[tuple[str, list[str]]] = []
    simple_name_index: dict[str, list[str]] = {}
    extends_records: list[tuple[str, str, str, int]] = []

    for path in files:
        rel = _as_posix_relative(path, project_root)
        module_id = _module_id_from_relative_path(rel)
        if not module_id:
            continue
        try:
            source = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            diagnostics.append({
                "level": "warning",
                "language": "javascript",
                "file_path": rel,
                "message": f"Skipped JavaScript file: {exc}",
            })
            continue

        lines = source.splitlines()
        parsed.append((rel, lines))
        _add_node_once(graph, GraphNode(module_id, "module", rel, 1, module_id))

        for idx, line in enumerate(lines, start=1):
            class_match = JS_CLASS_RE.match(line)
            if class_match:
                name = class_match.group(1)
                symbol_id = f"{module_id}.{name}"
                _add_node_once(graph, GraphNode(symbol_id, "class", rel, idx, module_id))
                simple_name_index.setdefault(name, []).append(symbol_id)
                if class_match.group(2):
                    extends_records.append((symbol_id, class_match.group(2), rel, idx))
                continue

            function_match = JS_FUNCTION_RE.match(line) or JS_ARROW_RE.match(line)
            if function_match:
                name = function_match.group(1)
                symbol_id = f"{module_id}.{name}"
                _add_node_once(graph, GraphNode(symbol_id, "function", rel, idx, module_id))
                simple_name_index.setdefault(name, []).append(symbol_id)

    for rel, lines in parsed:
        module_id = _module_id_from_relative_path(rel)
        for idx, line in enumerate(lines, start=1):
            for match in JS_NAMED_IMPORT_RE.finditer(line):
                target_module = _resolve_js_module(match.group(2), rel, graph)
                if not target_module:
                    continue
                for imported_name in _js_imported_names(match.group(1)):
                    target_symbol = f"{target_module}.{imported_name}"
                    if target_symbol in graph.nodes:
                        _add_edge_once(
                            graph,
                            GraphEdge(module_id, target_symbol, "imports", rel, idx),
                            seen_edges,
                        )
            for match in JS_IMPORT_RE.finditer(line):
                target = _resolve_js_module(match.group(1), rel, graph)
                if target:
                    _add_edge_once(graph, GraphEdge(module_id, target, "imports", rel, idx), seen_edges)
            for match in JS_REQUIRE_RE.finditer(line):
                target = _resolve_js_module(match.group(1), rel, graph)
                if target:
                    _add_edge_once(graph, GraphEdge(module_id, target, "imports", rel, idx), seen_edges)

    for source_id, base_name, rel, line_number in extends_records:
        targets = simple_name_index.get(base_name, [])
        if len(targets) == 1:
            _add_edge_once(
                graph,
                GraphEdge(source_id, targets[0], "inherits", rel, line_number),
                seen_edges,
            )

    if files:
        diagnostics.append({
            "level": "info",
            "language": "javascript",
            "message": "JavaScript support is conservative: regex discovery covers modules, classes, functions, imports, require(), and simple extends clauses.",
        })


def _usage_records_from_fixture(fixture_path: Path) -> dict[str, list[dict[str, Any]]]:
    raw = json.loads(fixture_path.read_text(encoding="utf-8-sig"))
    if isinstance(raw, list):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in raw:
            if not isinstance(item, dict):
                continue
            target = item.get("target") or item.get("symbol_id") or item.get("node_id")
            if target:
                grouped.setdefault(str(target), []).append(item)
        return grouped
    if isinstance(raw, dict) and isinstance(raw.get("symbols"), dict):
        return raw["symbols"]
    if isinstance(raw, dict) and isinstance(raw.get("pylance_usages"), dict):
        return raw["pylance_usages"]
    if isinstance(raw, dict) and isinstance(raw.get("vscode_listCodeUsages"), list):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in raw["vscode_listCodeUsages"]:
            if not isinstance(item, dict):
                continue
            target = item.get("target") or item.get("symbol_id") or item.get("node_id")
            usages = item.get("usages") or item.get("records") or []
            if target and isinstance(usages, list):
                grouped.setdefault(str(target), []).extend(
                    record for record in usages if isinstance(record, dict)
                )
        return grouped
    if isinstance(raw, dict) and isinstance(raw.get("usages"), list):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in raw["usages"]:
            target = item.get("target") or item.get("symbol_id")
            if target:
                grouped.setdefault(str(target), []).append(item)
        return grouped
    raise BaselineAdapterError(f"Unsupported usage fixture shape: {fixture_path}")


def _path_from_usage_record(record: dict[str, Any], project_root: Path) -> str | None:
    raw_path = record.get("file_path") or record.get("path")
    raw_uri = record.get("file_uri") or record.get("uri")
    if raw_path:
        path = Path(str(raw_path))
    elif raw_uri:
        path = Path(_uri_to_path(str(raw_uri)))
    else:
        return None

    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return None


def _apply_usage_fixture(
    graph: DependencyGraph,
    project_root: Path,
    usage_fixture: Path,
    diagnostics: list[dict[str, Any]],
    seen_edges: set[tuple[Any, ...]],
) -> None:
    grouped = _usage_records_from_fixture(usage_fixture)
    applied = 0
    skipped = 0
    for target_id, records in grouped.items():
        target_node = graph.nodes.get(target_id)
        target_kind = target_node.kind if target_node else "class"
        if target_id not in graph.nodes:
            skipped += len(records)
            diagnostics.append({
                "level": "warning",
            "source": "pylance_usage_fixture",
            "message": f"Skipped usages for unknown target node: {target_id}",
            })
            continue
        for record in records:
            usage_type = record.get("usage_type") or record.get("kind") or "reference"
            if usage_type == "definition":
                continue
            rel_path = _path_from_usage_record(record, project_root)
            if not rel_path:
                skipped += 1
                continue
            source_module = _module_id_from_relative_path(rel_path)
            if not source_module:
                skipped += 1
                continue
            _add_node_once(graph, GraphNode(source_module, "module", rel_path, 1, source_module))
            symbol_name = str(record.get("symbol") or target_id.rsplit(".", 1)[-1])
            line_content = str(record.get("line_content") or "")
            edge_kind = _classify_edge(symbol_name, str(usage_type), line_content, target_kind)
            line_number = int(record.get("line") or record.get("line_number") or 0)
            _add_edge_once(
                graph,
                GraphEdge(source_module, target_id, edge_kind, rel_path, line_number),
                seen_edges,
            )
            applied += 1

    diagnostics.append({
        "level": "info",
        "source": "pylance_usage_fixture",
        "file_path": _as_posix_relative(usage_fixture, project_root)
        if usage_fixture.resolve().is_relative_to(project_root.resolve())
        else str(usage_fixture),
        "message": f"Applied {applied} Pylance-style usage records; skipped {skipped}.",
    })


def _sorted_payload(graph: DependencyGraph, metadata: dict[str, Any]) -> dict[str, Any]:
    nodes = {
        node_id: asdict(graph.nodes[node_id])
        for node_id in sorted(graph.nodes)
    }
    edges = [
        asdict(edge)
        for edge in sorted(
            graph.edges,
            key=lambda item: (item.source, item.target, item.kind, item.file_path, item.line_number),
        )
    ]
    return {"metadata": metadata, "nodes": nodes, "edges": edges}


def build_baseline_payload(
    project_root: Path,
    languages: Sequence[str],
    includes: Sequence[str] | None = None,
    excludes: Sequence[str] | None = None,
    usage_fixture: Path | None = None,
) -> dict[str, Any]:
    """Build a contract-compatible baseline payload."""
    project_root = project_root.resolve()
    normalized_languages = sorted({_normalize_language(language) for language in languages})
    files = _iter_source_files(project_root, normalized_languages, includes, excludes)
    graph = DependencyGraph()
    diagnostics: list[dict[str, Any]] = []
    seen_edges: set[tuple[Any, ...]] = set()

    python_files = [path for path in files if path.suffix == ".py"]
    javascript_files = [path for path in files if path.suffix in {".js", ".mjs", ".cjs", ".jsx"}]

    if "python" in normalized_languages:
        _discover_python(graph, project_root, python_files, diagnostics, seen_edges)
    if "javascript" in normalized_languages:
        _discover_javascript(graph, project_root, javascript_files, diagnostics, seen_edges)

    if usage_fixture is not None:
        _apply_usage_fixture(graph, project_root, usage_fixture.resolve(), diagnostics, seen_edges)
    else:
        diagnostics.append({
            "level": "info",
            "message": "No Pylance usage fixture provided; Python call/reference coverage is intentionally partial.",
        })

    toolchain: list[dict[str, str]] = []
    for lang in normalized_languages:
        if lang == "python":
            toolchain.append({"name": "python-ast-symbol-discovery", "version": "stdlib"})
            if usage_fixture is not None:
                toolchain.append({
                    "name": "pylance-usage-fixture",
                    "version": "vscode_listCodeUsages-compatible",
                })
        else:
            toolchain.append({"name": "javascript-regex-reference-scanner", "version": GENERATOR_VERSION})

    metadata = {
        "contract": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "generator_id": GENERATOR_ID,
        "generator_version": GENERATOR_VERSION,
        "created_at": _utc_now(),
        "workspace_root_policy": "paths relative to workspace root",
        "source_coverage": {
            "include": list(includes or [pattern for lang in normalized_languages for pattern in LANGUAGE_PATTERNS[lang]]),
            "exclude": list(DEFAULT_EXCLUDES) + list(excludes or []),
            "languages": normalized_languages,
        },
        "toolchain": toolchain,
        "diagnostics": diagnostics,
    }
    return _sorted_payload(graph, metadata)


def backup_baseline(path: Path) -> Path:
    """Create a timestamped backup beside *path* and return the backup path."""
    if not path.exists():
        raise BaselineAdapterError(f"Cannot back up missing baseline: {path}")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(f"{path.stem}.{timestamp}{path.suffix}.bak")
    shutil.copy2(path, backup)
    return backup


def find_baseline_backups(path: Path) -> list[Path]:
    """Return timestamped backups for *path*, newest first."""
    pattern = f"{path.stem}.*{path.suffix}.bak"
    return sorted(path.parent.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)


def write_baseline(
    output_path: Path,
    payload: dict[str, Any],
    *,
    overwrite: bool = True,
    backup: bool = False,
) -> Path | None:
    """Write a baseline payload, optionally backing up an existing file."""
    if output_path.exists() and not overwrite:
        raise BaselineAdapterError(f"Baseline already exists: {output_path}")
    backup_path = backup_baseline(output_path) if backup and output_path.exists() else None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return backup_path


def validate_baseline_payload(payload: dict[str, Any], project_root: Path | None = None) -> dict[str, Any]:
    """Validate a baseline payload and return structured diagnostics."""
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload.get("nodes"), dict):
        errors.append("Top-level 'nodes' must be an object.")
    if not isinstance(payload.get("edges"), list):
        errors.append("Top-level 'edges' must be a list.")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "summary": None}

    try:
        graph = DependencyGraph.from_json(json.dumps(payload))
    except Exception as exc:  # noqa: BLE001 - validation must report arbitrary shape failures.
        errors.append(f"DependencyGraph.from_json failed: {exc}")
        return {"ok": False, "errors": errors, "warnings": warnings, "summary": None}

    for node in graph.nodes.values():
        _validate_graph_path(node.file_path, f"node {node.id}", errors, project_root)
    for edge in graph.edges:
        _validate_graph_path(edge.file_path, f"edge {edge.source}->{edge.target}", errors, project_root)
        if edge.source not in graph.nodes:
            warnings.append(f"Edge source is not a node: {edge.source}")
        if edge.target not in graph.nodes:
            warnings.append(f"Edge target is not a node: {edge.target}")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        warnings.append("Top-level metadata is missing; runtime can still consume nodes/edges.")
    elif metadata.get("contract") != CONTRACT_NAME:
        warnings.append("metadata.contract does not match the dependency baseline contract name.")

    return {"ok": not errors, "errors": errors, "warnings": warnings, "summary": graph.summary()}


def _validate_graph_path(
    file_path: str,
    owner: str,
    errors: list[str],
    project_root: Path | None,
) -> None:
    path = Path(file_path)
    if path.is_absolute():
        if project_root is not None:
            try:
                path.resolve().relative_to(project_root.resolve())
            except ValueError:
                errors.append(f"{owner} has absolute path outside project root: {file_path}")
                return
        errors.append(f"{owner} has absolute path; baseline paths must be workspace-relative: {file_path}")
        return
    parts = set(path.parts)
    forbidden = sorted(parts & FORBIDDEN_PATH_PARTS)
    if forbidden:
        errors.append(f"{owner} contains excluded path segment(s): {', '.join(forbidden)}")


def validate_baseline_file(path: Path, project_root: Path | None = None) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return validate_baseline_payload(payload, project_root)


def repair_baseline_payload(payload: dict[str, Any], project_root: Path) -> dict[str, Any]:
    """Normalize paths, remove duplicate edges, and sort baseline contents."""
    nodes_raw = payload.get("nodes", {})
    edges_raw = payload.get("edges", [])
    repaired = DependencyGraph()
    diagnostics = list(payload.get("metadata", {}).get("diagnostics", []))

    for node_id, node_data in nodes_raw.items():
        data = dict(node_data)
        data["file_path"] = _repair_path(str(data.get("file_path", "")), project_root)
        try:
            _add_node_once(repaired, GraphNode(**data))
        except TypeError as exc:
            diagnostics.append({
                "level": "warning",
                "source": "repair",
                "message": f"Skipped invalid node {node_id}: {exc}",
            })

    seen_edges: set[tuple[Any, ...]] = set()
    for edge_data in edges_raw:
        data = dict(edge_data)
        data["file_path"] = _repair_path(str(data.get("file_path", "")), project_root)
        try:
            edge = GraphEdge(**data)
        except TypeError as exc:
            diagnostics.append({
                "level": "warning",
                "source": "repair",
                "message": f"Skipped invalid edge: {exc}",
            })
            continue
        if edge.source not in repaired.nodes or edge.target not in repaired.nodes:
            diagnostics.append({
                "level": "warning",
                "source": "repair",
                "message": f"Dropped edge with missing endpoint: {edge.source}->{edge.target}",
            })
            continue
        _add_edge_once(repaired, edge, seen_edges)

    metadata = dict(payload.get("metadata", {}))
    metadata.setdefault("contract", CONTRACT_NAME)
    metadata.setdefault("contract_version", CONTRACT_VERSION)
    metadata.setdefault("generator_id", GENERATOR_ID)
    metadata.setdefault("generator_version", GENERATOR_VERSION)
    metadata["repaired_at"] = _utc_now()
    metadata["diagnostics"] = diagnostics
    return _sorted_payload(repaired, metadata)


def _repair_path(file_path: str, project_root: Path) -> str:
    path = Path(file_path)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(project_root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()
    return file_path.replace("\\", "/")


def rollback_baseline(output_path: Path, backup_path: Path | None = None) -> Path:
    """Restore *output_path* from a specific or latest backup."""
    selected = backup_path
    if selected is None:
        backups = find_baseline_backups(output_path)
        if not backups:
            raise BaselineAdapterError(f"No backups found for {output_path}")
        selected = backups[0]
    if not selected.exists():
        raise BaselineAdapterError(f"Backup not found: {selected}")
    shutil.copy2(selected, output_path)
    return selected


def _print_result(result: dict[str, Any]) -> None:
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _add_generation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--output", default="tools/dependency_graph/baseline_graph.json")
    parser.add_argument(
        "--language",
        action="append",
        choices=["python", "javascript", "py", "js"],
        default=None,
        help="Language to include. Can be repeated. Defaults to python.",
    )
    parser.add_argument("--include", action="append", default=None, help="Glob include pattern.")
    parser.add_argument("--exclude", action="append", default=None, help="Glob exclude pattern.")
    parser.add_argument(
        "--usage-fixture",
        "--pylance-usage-fixture",
        dest="usage_fixture",
        default=None,
        help="Optional Pylance vscode_listCodeUsages-compatible usage fixture JSON.",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reference dependency baseline adapter lifecycle CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new baseline; fails if output exists.")
    _add_generation_args(create_parser)
    create_parser.add_argument("--force", action="store_true", help="Overwrite an existing baseline.")

    refresh_parser = subparsers.add_parser("refresh", help="Refresh a baseline and back up the previous file.")
    _add_generation_args(refresh_parser)
    refresh_parser.add_argument("--no-backup", action="store_true", help="Do not back up an existing baseline.")

    generate_parser = subparsers.add_parser("generate", help="Generate a baseline, overwriting output by default.")
    _add_generation_args(generate_parser)
    generate_parser.add_argument("--backup", action="store_true", help="Back up an existing baseline before writing.")

    validate_parser = subparsers.add_parser("validate", help="Validate an existing baseline.")
    validate_parser.add_argument("--project-root", default=".")
    validate_parser.add_argument("--path", default="tools/dependency_graph/baseline_graph.json")

    repair_parser = subparsers.add_parser("repair", help="Normalize and repair an existing baseline.")
    repair_parser.add_argument("--project-root", default=".")
    repair_parser.add_argument("--path", default="tools/dependency_graph/baseline_graph.json")
    repair_parser.add_argument("--no-backup", action="store_true")

    rollback_parser = subparsers.add_parser("rollback", help="Restore a baseline from a backup.")
    rollback_parser.add_argument("--path", default="tools/dependency_graph/baseline_graph.json")
    rollback_parser.add_argument("--backup", default=None, help="Specific backup file. Defaults to latest.")

    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command in {"create", "refresh", "generate"}:
            project_root = Path(args.project_root).resolve()
            output = Path(args.output)
            if not output.is_absolute():
                output = project_root / output
            languages = [_normalize_language(item) for item in (args.language or ["python"])]
            fixture = Path(args.usage_fixture).resolve() if args.usage_fixture else None
            payload = build_baseline_payload(
                project_root,
                languages,
                includes=args.include,
                excludes=args.exclude,
                usage_fixture=fixture,
            )
            backup = False
            overwrite = True
            if args.command == "create":
                overwrite = bool(args.force)
            elif args.command == "refresh":
                backup = not bool(args.no_backup)
            elif args.command == "generate":
                backup = bool(args.backup)
            backup_path = write_baseline(output, payload, overwrite=overwrite, backup=backup)
            result = validate_baseline_payload(payload, project_root)
            result.update({"output": str(output), "backup": str(backup_path) if backup_path else None})
            _print_result(result)
            return 0 if result["ok"] else 1

        if args.command == "validate":
            project_root = Path(args.project_root).resolve()
            path = Path(args.path)
            if not path.is_absolute():
                path = project_root / path
            result = validate_baseline_file(path, project_root)
            _print_result(result)
            return 0 if result["ok"] else 1

        if args.command == "repair":
            project_root = Path(args.project_root).resolve()
            path = Path(args.path)
            if not path.is_absolute():
                path = project_root / path
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            repaired = repair_baseline_payload(payload, project_root)
            backup_path = write_baseline(path, repaired, overwrite=True, backup=not bool(args.no_backup))
            result = validate_baseline_payload(repaired, project_root)
            result.update({"output": str(path), "backup": str(backup_path) if backup_path else None})
            _print_result(result)
            return 0 if result["ok"] else 1

        if args.command == "rollback":
            path = Path(args.path)
            backup_path = Path(args.backup) if args.backup else None
            restored = rollback_baseline(path, backup_path)
            _print_result({"ok": True, "output": str(path), "restored_from": str(restored)})
            return 0

    except BaselineAdapterError as exc:
        _print_result({"ok": False, "errors": [str(exc)]})
        return 2

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
