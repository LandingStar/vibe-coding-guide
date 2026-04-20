#!/usr/bin/env python3
"""Lint cross-package imports in src/ to enforce layered dependency direction.

Exit 0 if all imports comply (or match known exceptions).
Exit 1 if unknown violations are found.

See: design_docs/tooling/Module Dependency Direction Standard.md
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# Layer assignments: lower number = lower layer.
LAYER: dict[str, int] = {
    "interfaces": 0,
    "audit": 0,
    "review": 0,
    "validators": 0,
    "workers": 0,
    "adapters": 0,
    "pack": 1,
    "collaboration": 1,
    "subagent": 1,
    "pdp": 2,
    "pep": 2,
    "workflow": 3,
    "runtime": 4,
    "mcp": 5,
    "dogfood": 5,
    "__main__": 6,
}

# Known exceptions: (source_pkg, target_pkg)
KNOWN_EXCEPTIONS: set[tuple[str, str]] = set()


def _top_package(module_parts: list[str]) -> str | None:
    """Return the first src/ sub-package name from dotted import parts."""
    if not module_parts:
        return None
    # Handles both 'src.pack.foo' and relative '.pack.foo'
    for part in module_parts:
        if part in LAYER:
            return part
    return None


def _in_type_checking_block(node: ast.AST, tree: ast.Module) -> bool:
    """Return True if *node* lives inside an ``if TYPE_CHECKING:`` block."""
    for parent in ast.walk(tree):
        if isinstance(parent, ast.If):
            # Match `if TYPE_CHECKING:` regardless of import alias
            test = parent.test
            name = None
            if isinstance(test, ast.Name):
                name = test.id
            elif isinstance(test, ast.Attribute):
                name = test.attr
            if name == "TYPE_CHECKING" and node in ast.walk(parent):
                return True
    return False


def _collect_imports(tree: ast.Module) -> list[tuple[int, str]]:
    """Yield (lineno, dotted_module) for every import in the AST.

    Skips imports inside ``if TYPE_CHECKING:`` blocks since those are
    not runtime dependencies.
    """
    results: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if not _in_type_checking_block(node, tree):
                results.append((node.lineno, node.module))
        elif isinstance(node, ast.Import):
            if not _in_type_checking_block(node, tree):
                for alias in node.names:
                    results.append((node.lineno, alias.name))
    return results


def lint_file(filepath: Path, src_root: Path) -> list[str]:
    """Check a single file for layering violations. Returns list of messages."""
    rel = filepath.relative_to(src_root)
    parts = rel.parts  # e.g. ('pack', 'manifest_loader.py')
    if not parts:
        return []
    source_pkg = parts[0]
    if source_pkg not in LAYER:
        return []

    source_layer = LAYER[source_pkg]
    violations: list[str] = []

    try:
        source_code = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source_code, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    for lineno, module in _collect_imports(tree):
        module_parts = module.split(".")
        target_pkg = _top_package(module_parts)
        if target_pkg is None or target_pkg == source_pkg:
            continue
        if target_pkg not in LAYER:
            continue

        target_layer = LAYER[target_pkg]
        if target_layer > source_layer:
            pair = (source_pkg, target_pkg)
            if pair in KNOWN_EXCEPTIONS:
                continue
            violations.append(
                f"  {rel}:{lineno}  {source_pkg}(L{source_layer}) → "
                f"{target_pkg}(L{target_layer})  import {module}"
            )
    return violations


def main() -> int:
    src_root = Path(__file__).resolve().parent.parent / "src"
    if not src_root.is_dir():
        print(f"ERROR: src/ not found at {src_root}", file=sys.stderr)
        return 1

    all_violations: list[str] = []
    for py_file in sorted(src_root.rglob("*.py")):
        all_violations.extend(lint_file(py_file, src_root))

    if all_violations:
        print("Module dependency direction violations found:\n")
        for v in all_violations:
            print(v)
        print(f"\n{len(all_violations)} violation(s). See design_docs/tooling/Module Dependency Direction Standard.md")
        return 1

    print("All cross-package imports comply with layering rules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
