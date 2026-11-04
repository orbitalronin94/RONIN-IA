"""Esquema versionado para anotaciones epistemicas de REF."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

EPISTEMIC_CLASSES = frozenset(
    {"falsifiable", "non_falsifiable", "mixed", "undetermined"}
)
ENCODING_STATUSES = frozenset(
    {"clear", "possibly_encoded", "decoded", "unknown"}
)
GENRES = frozenset(
    {
        "scientific",
        "historical",
        "religious",
        "literary",
        "legal",
        "technical",
        "philosophical",
        "other",
        "unknown",
    }
)
CLAIM_TYPES = frozenset(
    {
        "empirical",
        "causal",
        "metaphysical",
        "normative",
        "metaphorical",
        "fictional",
        "mathematical",
        "procedural",
        "descriptive",
        "mixed",
        "unknown",
    }
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED = {
    "record_id",
    "text",
    "source_id",
    "source_sha256",
    "license",
    "epistemic_class",
    "claim_type",
    "genre",
    "encoding_status",
    "confidence",
    "annotator",
    "policy_version",
}


def validate_annotation(record: Mapping[str, Any]) -> None:
    """Valida una anotacion REF y lanza ValueError si incumple el esquema.

    La validacion es estructural: no certifica que la etiqueta sea correcta.
    Cada registro describe un fragmento/afirmacion, no necesariamente una obra.
    """

    missing = sorted(_REQUIRED - record.keys())
    if missing:
        raise ValueError(f"Faltan campos obligatorios: {', '.join(missing)}")

    for field in ("record_id", "text", "source_id", "license", "annotator", "policy_version"):
        if not isinstance(record[field], str) or not record[field].strip():
            raise ValueError(f"{field} debe ser una cadena no vacia")

    if not _SHA256.fullmatch(str(record["source_sha256"])):
        raise ValueError("source_sha256 debe contener 64 caracteres hexadecimales")

    if record["epistemic_class"] not in EPISTEMIC_CLASSES:
        raise ValueError("epistemic_class no pertenece al vocabulario REF")
    if record["encoding_status"] not in ENCODING_STATUSES:
        raise ValueError("encoding_status no pertenece al vocabulario REF")
    if record["genre"] not in GENRES:
        raise ValueError("genre no pertenece al vocabulario REF")
    if record["claim_type"] not in CLAIM_TYPES:
        raise ValueError("claim_type no pertenece al vocabulario REF")

    confidence = record["confidence"]
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise ValueError("confidence debe ser un numero entre 0 y 1")
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("confidence debe ser un numero finito entre 0 y 1")

    start = record.get("span_start")
    end = record.get("span_end")
    if (start is None) != (end is None):
        raise ValueError("span_start y span_end deben indicarse juntos")
    if start is not None:
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, int)
            or not isinstance(end, int)
            or start < 0
            or end <= start
            or end > len(record["text"])
        ):
            raise ValueError("El intervalo de caracteres no es valido")

    if record["epistemic_class"] == "falsifiable" and not record.get(
        "potential_falsifier"
    ):
        raise ValueError(
            "Una anotacion falsable debe describir un posible criterio de refutacion"
        )

    if record["encoding_status"] == "decoded" and not record.get("decoding_evidence"):
        raise ValueError(
            "Un texto marcado como decoded debe incluir decoding_evidence"
        )
