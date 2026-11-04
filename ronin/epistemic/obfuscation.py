"""Esquema de pares y casos para la biblioteca de opacidad de RONIN.

Las etiquetas describen evidencia del caso, no una predicción automática sobre
cualquier texto opaco. En particular, «sin mensaje» solo se admite para controles
sintéticos con generación reproducible.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

CASE_TYPES = frozenset({"A", "B", "C", "D"})
OBFUSCATION_LABELS = frozenset({
    "CONFIRMED_MESSAGE",
    "CONFIRMED_STRUCTURE",
    "NO_MESSAGE_IN_CONTROL",
    "UNSUPPORTED_CLAIM",
    "UNRESOLVED",
})
EVIDENCE_STATUSES = frozenset({
    "reproduced",
    "documented",
    "fictional_solved_in_narrative",
    "rejected_by_evidence",
    "unresolved",
})
SPLITS = frozenset({"train", "validation", "test", "holdout"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

_REQUIRED = {
    "record_id", "case_type", "label", "evidence_status", "text",
    "source_id", "source_sha256", "source_license", "evidence_refs",
    "mechanism", "confidence", "split", "synthetic", "annotator",
    "policy_version",
}


def validate_obfuscation_case(record: Mapping[str, Any]) -> list[str]:
    """Devuelve errores estructurales; no juzga la verdad de la anotación."""
    errors: list[str] = []
    missing = sorted(_REQUIRED - record.keys())
    if missing:
        errors.append(f"Faltan campos: {', '.join(missing)}")
        return errors

    for field in (
        "record_id", "text", "source_id", "source_license",
        "mechanism", "annotator", "policy_version",
    ):
        if not isinstance(record[field], str) or not record[field].strip():
            errors.append(f"{field} debe ser texto no vacío")

    if record["case_type"] not in CASE_TYPES:
        errors.append("case_type debe ser A, B, C o D")
    if record["label"] not in OBFUSCATION_LABELS:
        errors.append("Etiqueta de opacidad desconocida")
    if record["evidence_status"] not in EVIDENCE_STATUSES:
        errors.append("Estado de evidencia desconocido")
    if record["split"] not in SPLITS:
        errors.append("Partición desconocida")
    if not isinstance(record["source_sha256"], str) or not _SHA256.fullmatch(record["source_sha256"]):
        errors.append("source_sha256 debe ser SHA-256 hexadecimal")
    if not isinstance(record["evidence_refs"], list) or not record["evidence_refs"]:
        errors.append("evidence_refs debe contener al menos una referencia verificable")
    if isinstance(record["confidence"], bool) or not isinstance(record["confidence"], (int, float)) or not math.isfinite(record["confidence"]) or not 0 <= record["confidence"] <= 1:
        errors.append("confidence debe ser un número finito entre 0 y 1")
    if not isinstance(record["synthetic"], bool):
        errors.append("synthetic debe ser booleano")

    label = record["label"]
    status = record["evidence_status"]
    if label == "CONFIRMED_MESSAGE":
        if status not in {"reproduced", "documented", "fictional_solved_in_narrative"}:
            errors.append("Un mensaje confirmado requiere solución reproducida o documentada")
        if not record.get("solution_summary") or not record.get("reproduction_steps"):
            errors.append("Un mensaje confirmado requiere solution_summary y reproduction_steps")
    if label == "CONFIRMED_STRUCTURE" and not record.get("solution_summary"):
        errors.append("La estructura confirmada requiere solution_summary")
    if label == "NO_MESSAGE_IN_CONTROL":
        if record["case_type"] != "B" or not record["synthetic"]:
            errors.append("NO_MESSAGE_IN_CONTROL solo se admite para controles sintéticos tipo B")
        if not record.get("generator") or not record.get("generator_seed"):
            errors.append("El control negativo requiere generador y semilla reproducibles")
    if label == "UNSUPPORTED_CLAIM":
        if record["case_type"] != "D" or status != "rejected_by_evidence":
            errors.append("UNSUPPORTED_CLAIM exige caso D y evidencia que rechace la afirmación")
        if not record.get("rejected_claim"):
            errors.append("UNSUPPORTED_CLAIM requiere rejected_claim")
    if label == "UNRESOLVED" and status != "unresolved":
        errors.append("UNRESOLVED debe conservar el estado de evidencia unresolved")
    if record["split"] == "holdout" and record.get("used_for_training", False):
        errors.append("Holdout no puede utilizarse para entrenamiento")
    return errors
