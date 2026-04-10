"""File notifier — writes notifications as JSON files."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


class FileNotifier:
    """EscalationNotifier that writes each notification to a JSON file."""

    def __init__(self, *, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)

    def notify(self, notification: dict) -> dict:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        nid = notification.get("notification_id", "unknown")
        target = self._output_dir / f"{nid}.json"

        # Atomic write
        fd, tmp_path = tempfile.mkstemp(dir=str(self._output_dir), suffix=".tmp")
        try:
            content = json.dumps(notification, indent=2, ensure_ascii=False)
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            os.replace(tmp_path, str(target))
        except BaseException:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        return {
            "delivered": True,
            "channel": "file",
            "path": str(target),
        }
