"""Discover top-level symbols (classes, functions, protocols) via AST scanning."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class DiscoveredSymbol:
    """A symbol found by AST scanning."""

    name: str
    qualified_name: str
    kind: str  # "class" | "function" | "protocol"
    file_path: str
    line_number: int
    bases: list[str]  # base class names for classes
    line_content: str  # the source line containing the symbol definition


def _module_name_from_path(file_path: Path, root: Path) -> str:
    """Convert a file path to a dotted module name relative to root's parent."""
    try:
        rel = file_path.relative_to(root.parent)
    except ValueError:
        rel = file_path
    parts = rel.with_suffix("").parts
    return ".".join(parts)


def _is_protocol(node: ast.ClassDef) -> bool:
    """Check if a class inherits from Protocol (by name)."""
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "Protocol":
            return True
        if isinstance(base, ast.Attribute) and base.attr == "Protocol":
            return True
    return False


def _base_names(node: ast.ClassDef) -> list[str]:
    """Extract base class names from a ClassDef."""
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
        elif isinstance(base, ast.Attribute):
            names.append(base.attr)
    return names


def _get_line_content(source_lines: list[str], lineno: int) -> str:
    """Get the source line content at a 1-based line number."""
    if 1 <= lineno <= len(source_lines):
        return source_lines[lineno - 1].rstrip()
    return ""


def discover_symbols(root: Path) -> Iterator[DiscoveredSymbol]:
    """Scan all .py files under *root* and yield top-level symbols.

    Only yields:
    - Top-level classes (including Protocol subclasses)
    - Top-level functions

    Skips:
    - Private names starting with '_' (except __init__.py module-level)
    - Nested classes/functions
    - Variables and constants
    """
    for py_file in sorted(root.rglob("*.py")):
        # Skip __pycache__ and build artifacts
        parts = py_file.parts
        if "__pycache__" in parts or "build" in parts:
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue

        source_lines = source.splitlines()
        module = _module_name_from_path(py_file, root)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                kind = "protocol" if _is_protocol(node) else "class"
                qualified = f"{module}.{node.name}"
                yield DiscoveredSymbol(
                    name=node.name,
                    qualified_name=qualified,
                    kind=kind,
                    file_path=str(py_file),
                    line_number=node.lineno,
                    bases=_base_names(node),
                    line_content=_get_line_content(source_lines, node.lineno),
                )
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                qualified = f"{module}.{node.name}"
                yield DiscoveredSymbol(
                    name=node.name,
                    qualified_name=qualified,
                    kind="function",
                    file_path=str(py_file),
                    line_number=node.lineno,
                    bases=[],
                    line_content=_get_line_content(source_lines, node.lineno),
                )
