from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_check_outputs_constraints_only_without_text() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "constraints" in payload
    assert "pipeline" not in payload
    assert "requested_input" not in payload


def test_check_with_text_points_user_to_process() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src", "check", "测试", "输入"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["requested_input"] == "测试 输入"
    assert "process <text>" in payload["note"]
    assert "pipeline" not in payload


def test_help_text_describes_check_as_constraints_only() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src", "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "check [text]" in proc.stdout
    assert "Constraint/state check only" in proc.stdout