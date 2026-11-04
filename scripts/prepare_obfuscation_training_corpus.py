#!/usr/bin/env python3
"""Prepara únicamente el split train del corpus curado de codificación."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from ronin.epistemic.obfuscation import validate_obfuscation_case


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def render_case(row: dict[str, Any]) -> str:
    steps = row.get("reproduction_steps") or []
    refs = row.get("evidence_refs") or []
    fields = [
        "### Caso de codificación",
        f"ID: {row['record_id']}",
        f"Texto opaco: {row['text']}",
        f"Clase: {row['case_type']}",
        f"Etiqueta: {row['label']}",
        f"Estado de evidencia: {row.get('evidence_status', 'unknown')}",
        f"Mecanismo: {row.get('mechanism', 'No especificado')}",
        f"Resumen: {row.get('solution_summary') or 'No hay solución documentada; no inferir una.'}",
        f"Afirmación evaluada: {row.get('rejected_claim', 'No aplica')}",
        "Pasos de reproducción:",
        *(f"- {step}" for step in steps),
        "Referencias:",
        *(f"- {ref}" for ref in refs),
        f"Fuente: {row.get('source_id', 'unknown')}",
        f"Licencia de fuente: {row.get('source_license', 'No declarada')}",
        f"Confianza de anotación (no calibrada): {row.get('confidence', 'unknown')}",
        f"Control sintético: {'sí' if row.get('synthetic') else 'no'}",
        "",
    ]
    return "\n".join(fields)


def prepare_training_corpus(
    input_path: str | Path,
    case_manifest_path: str | Path,
    output_path: str | Path,
    report_path: str | Path,
) -> dict[str, Any]:
    input_path = Path(input_path)
    case_manifest_path = Path(case_manifest_path)
    output_path = Path(output_path)
    report_path = Path(report_path)

    raw = input_path.read_bytes()
    case_manifest = json.loads(case_manifest_path.read_text(encoding="utf-8"))
    if sha256(raw) != case_manifest.get("dataset_sha256"):
        raise ValueError("SHA-256 del JSONL no coincide con el manifiesto")
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    if len(rows) != case_manifest.get("record_count"):
        raise ValueError("El número de registros no coincide con el manifiesto")

    split_counts = Counter()
    label_counts = Counter()
    train_rows = []
    synthetic_count = 0
    curated_count = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Cada registro debe ser un objeto JSON")
        errors = validate_obfuscation_case(row)
        if errors:
            raise ValueError(f"Registro {row.get('record_id', 'unknown')} inválido: {errors}")
        split = row.get("split")
        if split not in {"train", "validation", "test"}:
            raise ValueError(f"Split no permitido: {split!r}")
        split_counts[split] += 1
        if split == "train":
            train_rows.append(row)
            label_counts[row["label"]] += 1
            if row.get("synthetic") is True:
                synthetic_count += 1
            else:
                curated_count += 1

    expected_splits = case_manifest.get("counts_by_split", {})
    if dict(split_counts) != expected_splits:
        raise ValueError(
            f"Los splits reales {dict(split_counts)} no coinciden con el manifiesto {expected_splits}"
        )
    if not train_rows:
        raise ValueError("No hay registros train para preparar")

    encoded = "\n".join(render_case(row) for row in train_rows).encode("utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encoded)

    report = {
        "schema": "ronin-obfuscation-training-corpus-v1",
        "dataset_id": case_manifest["dataset_id"],
        "source_dataset_sha256": case_manifest["dataset_sha256"],
        "training_text_sha256": sha256(encoded),
        "total_records": len(rows),
        "train_records": len(train_rows),
        "validation_reserved": split_counts["validation"],
        "test_reserved": split_counts["test"],
        "train_counts_by_label": dict(sorted(label_counts.items())),
        "synthetic_train_records": synthetic_count,
        "non_synthetic_train_records": curated_count,
        "policy": (
            "Solo se exporta split=train. Los splits validation/test y los textos "
            "completos de las fuentes primarias permanecen fuera del entrenamiento."
        ),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--case-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = prepare_training_corpus(args.input, args.case_manifest, args.output, args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
