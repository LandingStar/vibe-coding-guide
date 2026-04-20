"""Context builder — merge multiple pack manifests into a unified PackContext."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path

from .manifest_loader import LoadLevel, PackManifest
from .pack_tree import PackTree

# Kind → numeric priority (higher number = higher precedence)
_KIND_PRIORITY: dict[str, int] = {
    "platform-default": 0,
    "official-instance": 1,
    "user-global": 2,
    "project-local": 3,
}


@dataclass
class PackContext:
    """Merged context from one or more pack manifests."""

    # Manifests sorted by precedence (platform → instance → project-local)
    manifests: list[PackManifest] = field(default_factory=list)

    # Merged capability sets (union of all packs)
    merged_intents: list[str] = field(default_factory=list)
    merged_gates: list[str] = field(default_factory=list)
    merged_document_types: list[str] = field(default_factory=list)
    merged_provides: list[str] = field(default_factory=list)

    # Always-on file content: filename → text
    always_on_content: dict[str, str] = field(default_factory=dict)

    # On-demand entries: relative path → base_dir (for lazy loading)
    on_demand_entries: dict[str, Path] = field(default_factory=dict)

    # Merged rules dict (later layers override earlier ones)
    merged_rules: dict = field(default_factory=dict)

    # Override declarations: pack_name → list of override targets
    merged_overrides: dict[str, list[str]] = field(default_factory=dict)

    # Detected rule merge conflicts (old_value overwritten by new_value)
    merge_conflicts: list[dict] = field(default_factory=list)

    # Current load level for this context
    load_level: LoadLevel = LoadLevel.FULL

    # Cache for lazily loaded on_demand content
    _on_demand_cache: dict[str, str] = field(
        default_factory=dict, repr=False, compare=False
    )

    def load_on_demand(self, key: str) -> str | None:
        """Lazily load an on-demand file by its relative path.

        Returns the file content as a string, or ``None`` if the key
        is not declared or the file does not exist.  Results are cached.
        """
        if key in self._on_demand_cache:
            return self._on_demand_cache[key]

        base_dir = self.on_demand_entries.get(key)
        if base_dir is None:
            return None

        path = base_dir / key
        if not path.exists():
            return None

        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return None

        self._on_demand_cache[key] = content
        return content

    def list_on_demand(self) -> list[str]:
        """Return the list of declared on-demand keys."""
        return list(self.on_demand_entries.keys())

    def upgrade(self, target: LoadLevel, *, builder: ContextBuilder | None = None) -> PackContext:
        """Return a new PackContext at *target* level.

        If the current level already meets or exceeds *target*, returns ``self``.
        Otherwise rebuilds from the stored manifests using the provided *builder*.
        A *builder* is required when upgrading (it holds the base_dir mapping).

        Raises:
            ValueError: if *target* > current level and no *builder* is supplied.
        """
        if self.load_level >= target:
            return self
        if builder is None:
            raise ValueError(
                f"Cannot upgrade from {self.load_level.name} to {target.name} "
                "without a ContextBuilder (base_dir mapping required)"
            )
        return builder.build(level=target)


class ContextBuilder:
    """Build a PackContext by registering and merging multiple packs."""

    def __init__(self) -> None:
        self._entries: list[tuple[PackManifest, Path]] = []
        self._pack_tree: PackTree | None = None

    def add_pack(self, manifest: PackManifest, base_dir: str | Path) -> None:
        """Register a pack manifest with its base directory.

        base_dir is used to resolve always_on file paths.
        """
        self._entries.append((manifest, Path(base_dir)))
        self._pack_tree = None  # invalidate cached tree

    @property
    def pack_tree(self) -> PackTree:
        """Return the PackTree for all registered manifests (cached)."""
        if self._pack_tree is None:
            self._pack_tree = PackTree([m for m, _ in self._entries])
        return self._pack_tree

    def build(self, *, level: LoadLevel = LoadLevel.FULL, scope_path: str = "") -> PackContext:
        """Merge all registered packs into a PackContext.

        Packs are sorted by kind priority (platform → instance → project-local).
        Within the same kind, insertion order is preserved.

        If *scope_path* is provided at FULL level, always_on content is
        only loaded from packs whose scope_paths match (or packs with no
        scope_paths, which are considered universal).
        """
        # Sort by kind priority
        sorted_entries = sorted(
            self._entries,
            key=lambda e: _KIND_PRIORITY.get(e[0].kind, -1),
        )
        return self._build_from_entries(sorted_entries, level=level, scope_path=scope_path)

    def build_scoped(self, scope_path: str, *, level: LoadLevel = LoadLevel.FULL) -> PackContext:
        """Build a scoped PackContext for the given working path.

        Uses PackTree to determine which pack chain applies,
        then merges only packs in that chain, in tree order
        (root → leaf, i.e. general → specific).

        Falls back to ``build()`` if no pack has scope_paths
        or no scope matches.
        """
        tree = self.pack_tree
        chain = tree.resolve_scope(scope_path)
        if chain is None:
            return self.build(level=level)

        # Filter entries to only include packs in the resolved chain,
        # preserving chain order (root → leaf).
        chain_names = [m.name for m in chain]
        chain_name_set = set(chain_names)
        entry_by_name: dict[str, tuple[PackManifest, Path]] = {}
        for m, d in self._entries:
            if m.name in chain_name_set:
                entry_by_name[m.name] = (m, d)

        ordered_entries = [entry_by_name[n] for n in chain_names if n in entry_by_name]
        return self._build_from_entries(ordered_entries, level=level)

    def _build_from_entries(
        self, entries: list[tuple[PackManifest, Path]], *, level: LoadLevel = LoadLevel.FULL,
        scope_path: str = "",
    ) -> PackContext:
        """Core merge logic shared by build() and build_scoped()."""
        manifests = [m for m, _ in entries]

        # --- METADATA level: only name/kind/provides/description ---
        merged_provides = _merge_unique([m.provides for m in manifests])

        if level <= LoadLevel.METADATA:
            return PackContext(
                manifests=manifests,
                merged_provides=merged_provides,
                load_level=level,
            )

        # --- MANIFEST level: capability sets + rules, no file content ---
        merged_intents = _merge_unique([m.intents for m in manifests])
        merged_gates = _merge_unique([m.gates for m in manifests])
        merged_document_types = _merge_unique([m.document_types for m in manifests])

        # Collect on_demand entries (later packs override)
        on_demand_entries: dict[str, Path] = {}
        for manifest, base_dir in entries:
            for rel_path in manifest.on_demand:
                on_demand_entries[rel_path] = base_dir

        # Merge rules dicts (later layers override).
        # deepcopy prevents mutation of manifest.rules when
        # _build_from_entries is called multiple times with shared manifests.
        merged_rules: dict = {}
        merge_conflicts: list[dict] = []
        last_source = ""
        for manifest in manifests:
            if manifest.rules:
                _deep_merge(
                    merged_rules,
                    copy.deepcopy(manifest.rules),
                    conflicts=merge_conflicts,
                    base_source=last_source,
                    overlay_source=manifest.name,
                )
                last_source = manifest.name

        # Extract override declarations and validate targets
        merged_overrides: dict[str, list[str]] = {}
        all_names = {m.name for m in manifests}
        for manifest in manifests:
            if manifest.overrides:
                merged_overrides[manifest.name] = list(manifest.overrides)

        if level <= LoadLevel.MANIFEST:
            return PackContext(
                manifests=manifests,
                merged_intents=merged_intents,
                merged_gates=merged_gates,
                merged_document_types=merged_document_types,
                merged_provides=merged_provides,
                on_demand_entries=on_demand_entries,
                merged_rules=merged_rules,
                merged_overrides=merged_overrides,
                merge_conflicts=merge_conflicts,
                load_level=level,
            )

        # --- FULL level: read always_on file content ---
        always_on_content: dict[str, str] = {}
        for manifest, base_dir in entries:
            # Conditional loading: if scope_path is given and the pack
            # declares scope_paths, skip if none match.
            if scope_path and manifest.scope_paths:
                if not any(scope_path.startswith(sp) for sp in manifest.scope_paths):
                    continue
            for rel_path in manifest.always_on:
                full_path = base_dir / rel_path
                if full_path.exists():
                    always_on_content[rel_path] = full_path.read_text(
                        encoding="utf-8"
                    )
                # Missing files are silently skipped (pack may declare optional content)

        return PackContext(
            manifests=manifests,
            merged_intents=merged_intents,
            merged_gates=merged_gates,
            merged_document_types=merged_document_types,
            merged_provides=merged_provides,
            always_on_content=always_on_content,
            on_demand_entries=on_demand_entries,
            merged_rules=merged_rules,
            merged_overrides=merged_overrides,
            merge_conflicts=merge_conflicts,
            load_level=level,
        )


def _merge_unique(lists: list[list[str]]) -> list[str]:
    """Merge multiple lists preserving first-seen order, deduplicated."""
    seen: set[str] = set()
    result: list[str] = []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _deep_merge(
    base: dict,
    overlay: dict,
    *,
    conflicts: list[dict] | None = None,
    base_source: str = "",
    overlay_source: str = "",
    _path: str = "",
) -> None:
    """Recursively merge overlay into base (in-place). Overlay wins on conflicts.

    When *conflicts* is provided, records each key overwrite as a conflict dict.
    """
    for key, value in overlay.items():
        current_path = f"{_path}.{key}" if _path else key
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(
                base[key], value,
                conflicts=conflicts,
                base_source=base_source,
                overlay_source=overlay_source,
                _path=current_path,
            )
        else:
            if key in base and conflicts is not None and base[key] != value:
                conflicts.append({
                    "path": current_path,
                    "old_value": base[key],
                    "new_value": value,
                    "old_source": base_source,
                    "new_source": overlay_source,
                })
            base[key] = value
