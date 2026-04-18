"""Coupling annotations — explicit semantic coupling declarations and checker."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class CouplingAnchor:
    """A location participating in a coupling relationship."""

    file_path: str
    symbol: str | None = None
    line_pattern: str | None = None


@dataclass
class CouplingAnnotation:
    """Describes a semantic coupling between multiple locations."""

    id: str
    description: str
    anchors: list[CouplingAnchor]
    severity: str = "should-check"  # "must-sync" | "should-check" | "info"


@dataclass
class CouplingAlert:
    """A coupling alert triggered by a change."""

    annotation_id: str
    description: str
    severity: str
    triggered_by: str
    check_targets: list[CouplingAnchor]


class CouplingStore:
    """Manage coupling annotations in a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.annotations: list[CouplingAnnotation] = []
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.annotations = [
            CouplingAnnotation(
                id=item["id"],
                description=item["description"],
                anchors=[CouplingAnchor(**a) for a in item["anchors"]],
                severity=item.get("severity", "should-check"),
            )
            for item in raw.get("annotations", [])
        ]

    def save(self) -> None:
        data = {
            "annotations": [
                {
                    "id": ann.id,
                    "description": ann.description,
                    "anchors": [asdict(a) for a in ann.anchors],
                    "severity": ann.severity,
                }
                for ann in self.annotations
            ]
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add(self, annotation: CouplingAnnotation) -> None:
        self.annotations.append(annotation)

    def remove(self, annotation_id: str) -> bool:
        before = len(self.annotations)
        self.annotations = [a for a in self.annotations if a.id != annotation_id]
        return len(self.annotations) < before

    def get(self, annotation_id: str) -> CouplingAnnotation | None:
        for a in self.annotations:
            if a.id == annotation_id:
                return a
        return None

    def list_all(self) -> list[CouplingAnnotation]:
        return list(self.annotations)


class CouplingChecker:
    """Check changes against coupling annotations and generate alerts."""

    def __init__(self, store: CouplingStore) -> None:
        self.store = store

    def check(
        self,
        changed_files: list[str] | None = None,
        changed_symbols: list[str] | None = None,
    ) -> list[CouplingAlert]:
        """Match changes against annotations and return alerts."""
        changed_files = changed_files or []
        changed_symbols = changed_symbols or []

        alerts: list[CouplingAlert] = []

        for ann in self.store.annotations:
            for anchor in ann.anchors:
                triggered_by = self._match_anchor(
                    anchor, changed_files, changed_symbols
                )
                if triggered_by:
                    # Collect other anchors as check targets
                    targets = [a for a in ann.anchors if a is not anchor]
                    alerts.append(
                        CouplingAlert(
                            annotation_id=ann.id,
                            description=ann.description,
                            severity=ann.severity,
                            triggered_by=triggered_by,
                            check_targets=targets,
                        )
                    )
                    break  # One match per annotation is enough

        return alerts

    @staticmethod
    def _match_anchor(
        anchor: CouplingAnchor,
        changed_files: list[str],
        changed_symbols: list[str],
    ) -> str | None:
        """Check if an anchor matches any changed file or symbol."""
        # Match by symbol
        if anchor.symbol and anchor.symbol in changed_symbols:
            return anchor.symbol

        # Match by file path (suffix match for flexibility)
        norm_anchor = Path(anchor.file_path).as_posix()
        for f in changed_files:
            norm_f = Path(f).as_posix()
            if norm_f.endswith(norm_anchor) or norm_anchor.endswith(norm_f):
                return f

        return None
