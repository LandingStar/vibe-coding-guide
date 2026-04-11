from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[3]
CREATE_SANDBOX_SCRIPT = (
    REPO_ROOT
    / ".codex/handoff-system/scripts/create_rebuild_rehearsal_sandbox.py"
)
ACCEPT_SCRIPT = (
    REPO_ROOT
    / ".codex/handoff-system/skill/project-handoff-accept/scripts/intake_handoff.py"
)
REBUILD_SCRIPT = (
    REPO_ROOT
    / ".codex/handoff-system/skill/project-handoff-rebuild/scripts/rebuild_handoff.py"
)


def test_create_rebuild_rehearsal_sandbox_supports_manual_rebuild_flow(tmp_path: Path) -> None:
    sandbox_path = tmp_path / "rebuild-sandbox"
    create_result = subprocess.run(
        [
            sys.executable,
            str(CREATE_SANDBOX_SCRIPT),
            "--output-dir",
            str(sandbox_path),
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert create_result.returncode == 0
    create_payload = json.loads(create_result.stdout)
    assert create_payload["status"] == "ok"
    assert Path(create_payload["current_path"]).exists()
    assert Path(create_payload["source_handoff_path"]).exists()
    assert Path(create_payload["rehearsal_readme"]).exists()

    accept_result = subprocess.run(
        [sys.executable, str(ACCEPT_SCRIPT), "--current", "--json"],
        cwd=sandbox_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert accept_result.returncode == 1
    accept_payload = json.loads(accept_result.stdout)
    assert accept_payload["status"] == "blocked"
    assert any("missing authoritative ref" in issue for issue in accept_payload["blocking_issues"])
    assert not any(
        "active handoff body still mentions canonical draft state" in warning
        for warning in accept_payload["warnings"]
    )

    rebuild_result = subprocess.run(
        [sys.executable, str(REBUILD_SCRIPT), "--current", "--json"],
        cwd=sandbox_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rebuild_result.returncode == 0
    rebuild_payload = json.loads(rebuild_result.stdout)
    assert rebuild_payload["status"] == "ok"
    assert Path(rebuild_payload["report_path"]).exists()
    assert Path(rebuild_payload["rebuilt_handoff_path"]).exists()
