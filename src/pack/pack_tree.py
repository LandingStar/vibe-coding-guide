"""Pack tree — build a single-inheritance tree from pack manifests."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .manifest_loader import PackManifest

logger = logging.getLogger(__name__)


@dataclass
class _TreeNode:
    """Internal tree node wrapping a PackManifest."""

    manifest: PackManifest
    children: list[_TreeNode] = field(default_factory=list)
    parent_node: _TreeNode | None = None
    depth: int = 0


class PackTree:
    """Single-inheritance tree built from a list of PackManifest instances.

    Each pack may declare a ``parent`` field pointing to another pack's
    name.  Packs without a parent are roots.  The result is a forest
    (one or more independent trees).

    Validation performed during construction:

    * Duplicate pack names → ``ValueError``
    * Circular parent references → ``ValueError``
    * Orphan parent reference (parent not in manifest list) →
      warning logged, pack treated as root
    """

    def __init__(self, manifests: list[PackManifest]) -> None:
        self._nodes: dict[str, _TreeNode] = {}
        self._roots: list[_TreeNode] = []
        self._build(manifests)

    # ── Public query API ──────────────────────────────────────────────

    def roots(self) -> list[PackManifest]:
        """Return all root manifests (no parent)."""
        return [n.manifest for n in self._roots]

    def children(self, pack_name: str) -> list[PackManifest]:
        """Return direct child manifests of *pack_name*."""
        node = self._nodes.get(pack_name)
        if node is None:
            return []
        return [c.manifest for c in node.children]

    def ancestors(self, pack_name: str) -> list[PackManifest]:
        """Return the ordered ancestor chain from root to parent (excludes self)."""
        node = self._nodes.get(pack_name)
        if node is None:
            return []
        result: list[PackManifest] = []
        cur = node.parent_node
        while cur is not None:
            result.append(cur.manifest)
            cur = cur.parent_node
        result.reverse()
        return result

    def chain(self, pack_name: str) -> list[PackManifest]:
        """Return the full chain from root to *pack_name* (inclusive)."""
        node = self._nodes.get(pack_name)
        if node is None:
            return []
        return self.ancestors(pack_name) + [node.manifest]

    def depth(self, pack_name: str) -> int:
        """Return the depth of *pack_name* (root = 0, -1 if not found)."""
        node = self._nodes.get(pack_name)
        if node is None:
            return -1
        return node.depth

    def all_names(self) -> list[str]:
        """Return all pack names in the tree."""
        return list(self._nodes.keys())

    def resolve_scope(self, scope_path: str) -> list[PackManifest] | None:
        """Find the best matching pack chain for *scope_path*.

        Walks all nodes with ``scope_paths`` declared and selects the
        **deepest** (most specific) match whose ``scope_paths`` prefix-
        matches *scope_path*.  Returns the full chain from root to that
        node, or ``None`` if no node matches.

        Packs without ``scope_paths`` are considered to match all paths
        (wildcard), but they never beat a node with an explicit prefix
        match.
        """
        best_node: _TreeNode | None = None
        best_depth = -1
        best_prefix_len = -1

        for node in self._nodes.values():
            if not node.manifest.scope_paths:
                # Wildcard node — only used as fallback
                if best_node is None:
                    best_node = node
                    best_depth = node.depth
                elif node.depth > best_depth and best_prefix_len < 0:
                    best_node = node
                    best_depth = node.depth
                continue

            for prefix in node.manifest.scope_paths:
                if scope_path.startswith(prefix):
                    plen = len(prefix)
                    # Prefer longer prefix; on tie prefer deeper node
                    if plen > best_prefix_len or (
                        plen == best_prefix_len and node.depth > best_depth
                    ):
                        best_node = node
                        best_depth = node.depth
                        best_prefix_len = plen

        if best_node is None:
            return None
        return self.chain(best_node.manifest.name)

    # ── Construction ──────────────────────────────────────────────────

    def _build(self, manifests: list[PackManifest]) -> None:
        # Step 1: create nodes, check for duplicate names
        for m in manifests:
            if m.name in self._nodes:
                raise ValueError(
                    f"Duplicate pack name: {m.name!r}"
                )
            self._nodes[m.name] = _TreeNode(manifest=m)

        # Step 2: link parent → child (detect orphan parents)
        for name, node in self._nodes.items():
            parent_name = node.manifest.parent
            if not parent_name:
                continue
            parent_node = self._nodes.get(parent_name)
            if parent_node is None:
                logger.warning(
                    "Pack %r declares parent %r which is not found; "
                    "treating as root",
                    name,
                    parent_name,
                )
                continue
            node.parent_node = parent_node
            parent_node.children.append(node)

        # Step 3: identify roots
        for node in self._nodes.values():
            if node.parent_node is None:
                self._roots.append(node)

        # Step 4: detect cycles (any node not reachable from a root)
        visited: set[str] = set()
        stack: list[_TreeNode] = list(self._roots)
        while stack:
            cur = stack.pop()
            if cur.manifest.name in visited:
                continue
            visited.add(cur.manifest.name)
            stack.extend(cur.children)

        unvisited = set(self._nodes.keys()) - visited
        if unvisited:
            raise ValueError(
                f"Circular parent reference detected involving: "
                f"{sorted(unvisited)}"
            )

        # Step 5: compute depths via BFS from roots
        from collections import deque

        queue: deque[_TreeNode] = deque()
        for root in self._roots:
            root.depth = 0
            queue.append(root)
        while queue:
            cur = queue.popleft()
            for child in cur.children:
                child.depth = cur.depth + 1
                queue.append(child)

        # Step 6: validate scope_paths overlap among siblings
        self._check_scope_overlap()

    def _check_scope_overlap(self) -> None:
        """Detect overlapping scope_paths among sibling packs (same parent)."""
        # Group siblings by parent
        siblings_groups: dict[str | None, list[_TreeNode]] = {}
        for node in self._nodes.values():
            parent_key = node.parent_node.manifest.name if node.parent_node else None
            siblings_groups.setdefault(parent_key, []).append(node)

        for _parent, siblings in siblings_groups.items():
            # Collect all (prefix, pack_name) pairs
            scoped: list[tuple[str, str]] = []
            for node in siblings:
                for prefix in node.manifest.scope_paths:
                    scoped.append((prefix, node.manifest.name))

            # Check pairwise overlap
            for i, (prefix_a, name_a) in enumerate(scoped):
                for prefix_b, name_b in scoped[i + 1 :]:
                    if name_a == name_b:
                        continue
                    if prefix_a.startswith(prefix_b) or prefix_b.startswith(prefix_a):
                        raise ValueError(
                            f"Overlapping scope_paths among siblings: "
                            f"{name_a!r} ({prefix_a!r}) and "
                            f"{name_b!r} ({prefix_b!r})"
                        )
