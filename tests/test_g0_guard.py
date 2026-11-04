"""Pruebas del guard fail-closed que protege G-0."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "assert_g0_passed.py"


def run_guard(tmp_path: Path, gate: dict) -> subprocess.CompletedProcess[str]:
    report = tmp_path / "license_audit.json"
    report.write_text(
        json.dumps({"gate": gate}),
        encoding="utf-8",
    )
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--report", str(report)],
        capture_output=True,
        check=False,
        text=True,
    )


def test_g0_fail_blocks_corpus_operations(tmp_path: Path) -> None:
    result = run_guard(
        tmp_path,
        {
            "id": "G-0",
            "passed": False,
            "status": "FAIL",
            "downloads_authorized": False,
            "reason": "Pendiente de revisión documental",
        },
    )
    assert result.returncode == 1
    assert "bloqueados" in result.stdout


def test_g0_requires_all_four_authorization_conditions(tmp_path: Path) -> None:
    result = run_guard(
        tmp_path,
        {
            "id": "G-0",
            "passed": True,
            "status": "PASS",
            "downloads_authorized": False,
        },
    )
    assert result.returncode == 1


def test_g0_pass_authorizes_only_when_explicitly_complete(tmp_path: Path) -> None:
    result = run_guard(
        tmp_path,
        {
            "id": "G-0",
            "passed": True,
            "status": "PASS",
            "downloads_authorized": True,
        },
    )
    assert result.returncode == 0
    assert "G-0 PASS" in result.stdout
