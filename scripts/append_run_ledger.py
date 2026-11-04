#!/usr/bin/env python3
"""Append a completed GitHub Actions run to docs/RUNS.md, idempotently."""
from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RUNBOOK = Path("docs/RUNS.md")
SUMMARIES = {
    "Integración continua": (
        "Lint, comprobación del paquete, pruebas y smoke test técnico."
    ),
    "Experimento oficial RONIN desde cero + MMLU-Pro completo": (
        "Entrenamiento oficial desde cero y evaluación MMLU-Pro holdout; "
        "consultar el artefacto del run para métricas y cobertura."
    ),
    "Experimento RONIN desde cero + MMLU-Pro reducido": (
        "Ciclo reducido manual de entrenamiento desde cero y evaluación "
        "estratificada; consultar artefactos y manifiestos."
    ),
    "Auditoría comparativa Supra → RONIN": (
        "Auditoría comparativa de las propuestas Supra frente a una ejecución "
        "oficial; no modifica pesos ni corpus."
    ),
    "Validar manifiesto de datasets externos": (
        "Validación estructural y de política del inventario de fuentes "
        "externas; no descarga ni entrena."
    ),
    "Ingesta de muestras CC0/CC-BY — Wikidata + Europe PMC": (
        "Obtención de muestras pequeñas de datos estructurados CC0 de Wikidata "
        "y resúmenes de artículos con licencia CC BY/CC0; publicación "
        "versionada y nunca admisión automática al entrenamiento."
    ),
    "Preparar corpus propio de Portfolio": (
        "Preparación, validación de autorización, hashes y manifiesto del corpus Portfolio."
    ),
    "Calibración REF — lógica y falacias": (
        "Validación de fixtures de lógica y falacias frente al esquema REF; no equivale a entrenamiento general."
    ),
    "Primera iteración y benchmark interno": (
        "Ciclo inicial y benchmark interno; consultar el artefacto para métricas y alcance."
    ),
    "Ciclos sintéticos de entrenamiento RONIN": (
        "Smoke tests con datos sintéticos aislados; no se consideran corpus de conocimiento ni entrenamiento oficial."
    ),
    "Auditoría de descargas reales del corpus": (
        "Auditoría de adquisición de corpus literario y biblioteca de codificación; revisar estados de derechos antes de uso."
    ),
    "Generar candidatos REF con Phi-4 (sin entrenar al estudiante)": (
        "Generación y auditoría de candidatos REF por tutor; las generaciones no se incorporan al estudiante ni al corpus automáticamente."
    ),
    "Preparar caché de tutores locales": (
        "Descarga y verificación de revisiones y hashes de modelos tutores; no transfiere pesos al estudiante."
    ),
    "Comparativa A-B de arquitecturas": (
        "Comparación experimental de arquitecturas con controles G-0; no asumir superioridad sin revisar métricas y ablations."
    ),
}


def safe(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ")
    for char in ("|", "[", "]", "(", ")", chr(96)):
        text = text.replace(char, "\\" + char)
    return re.sub(r"[<>]", "", text).strip()


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise SystemExit("GITHUB_EVENT_PATH is required")

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    run = event.get("workflow_run", event)
    run_id = str(run.get("id", ""))
    if not run_id:
        raise SystemExit("workflow_run.id is missing")

    RUNBOOK.parent.mkdir(parents=True, exist_ok=True)
    if RUNBOOK.exists():
        content = RUNBOOK.read_text(encoding="utf-8")
    else:
        content = (
            "# Libro de ejecuciones (runs) de RONIN-IA\n\n"
            "## Historial\n\n"
            "| Fecha UTC | Workflow / ejecución | Estado | "
            "Qué ocurrió / qué se incorporó | Commit |\n"
            "|---|---|---|---|---|\n"
        )

    if re.search(r"\b" + re.escape(run_id) + r"\b", content):
        print("Run already recorded: " + run_id)
        return 0

    completed = (
        run.get("updated_at")
        or run.get("completed_at")
        or run.get("created_at")
    )
    try:
        stamp = datetime.fromisoformat(
            completed.replace("Z", "+00:00")
        ).astimezone(UTC)
        date_text = stamp.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        date_text = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")

    raw_name = str(run.get("name") or "Workflow")
    name = safe(raw_name)
    url = safe(
        run.get("html_url")
        or (
            "https://github.com/"
            + os.environ.get("GITHUB_REPOSITORY", "")
            + "/actions/runs/"
            + run_id
        )
    )
    conclusion = safe(run.get("conclusion") or run.get("status") or "unknown")
    branch = safe(run.get("head_branch") or "")
    sha = safe(run.get("head_sha") or "")
    event_name = safe(run.get("event") or "")
    number = safe(run.get("run_number") or "")
    attempt = safe(run.get("run_attempt") or "1")

    summary = SUMMARIES.get(
        raw_name,
        "Ejecución de GitHub Actions; consultar logs y artefactos "
        "enlazados para el resultado detallado.",
    )
    head_commit = run.get("head_commit") or {}
    commit_message = safe(head_commit.get("message") or "")
    description = (
        summary
        + " Commit: "
        + commit_message
        + ". Trigger: "
        + event_name
        + "; rama: "
        + branch
        + "; intento: "
        + attempt
        + "."
    )
    row = (
        "| "
        + date_text
        + " | ["
        + name
        + " #"
        + number
        + " (run "
        + run_id
        + ")]("
        + url
        + ") | "
        + conclusion
        + " | "
        + description
        + " | "
        + (sha[:8] or "—")
        + " |\n"
    )
    marker = "|---|---|---|---|---|\n"
    if marker in content:
        content = content.replace(marker, marker + row, 1)
    else:
        content += "\n" + row

    RUNBOOK.write_text(content, encoding="utf-8")
    print("Recorded run " + run_id + ": " + name + " (" + conclusion + ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
