import json

from scripts import append_run_ledger


def test_run_ledger_is_idempotent_and_records_failure(tmp_path, monkeypatch):
    runbook = tmp_path / "RUNS.md"
    runbook.write_text(
        "# Libro de ejecuciones (runs) de RONIN-IA\n\n"
        "## Historial\n\n"
        "| Fecha UTC | Workflow / ejecución | Estado | Qué ocurrió / qué se incorporó | Commit |\n"
        "|---|---|---|---|---|\n",
        encoding="utf-8",
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({
        "workflow_run": {
            "id": 123456789,
            "name": "Integración continua",
            "run_number": 429,
            "run_attempt": 1,
            "html_url": "https://github.com/example/repo/actions/runs/123456789",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "abcdef0123456789",
            "event": "push",
            "updated_at": "2026-11-04T12:00:00Z",
        }
    }), encoding="utf-8")
    monkeypatch.setattr(append_run_ledger, "RUNBOOK", runbook)
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("GITHUB_REPOSITORY", "example/repo")

    assert append_run_ledger.main() == 0
    first = runbook.read_text(encoding="utf-8")
    assert "123456789" in first
    assert "failure" in first
    assert "abcdef01" in first

    assert append_run_ledger.main() == 0
    second = runbook.read_text(encoding="utf-8")
    assert second.count("123456789") == 1
