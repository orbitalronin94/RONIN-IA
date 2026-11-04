"""Validación estructural del gate de auditoría de licencias del corpus.

Este módulo comprueba integridad y coherencia del informe; no emite dictámenes
jurídicos ni convierte metadatos de terceros en prueba de derechos.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

EXPECTED_SOURCES = {
    "project_gutenberg",
    "internet_archive",
    "common_corpus",
    "bookcorpusopen",
}


def validate_license_audit(audit: Mapping[str, Any]) -> None:
    """Lanza ValueError si el informe G-0 es incompleto o contradictorio."""
    if audit.get("schema_version") != "1.0":
        raise ValueError("schema_version debe ser '1.0'")

    sources = audit.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources debe ser una lista")

    source_ids = [item.get("id") for item in sources if isinstance(item, Mapping)]
    if len(source_ids) != len(sources):
        raise ValueError("Cada fuente debe ser un objeto")
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Hay identificadores de fuente duplicados")
    if set(source_ids) != EXPECTED_SOURCES:
        raise ValueError("El informe debe cubrir exactamente las cuatro fuentes autorizadas")

    for source in sources:
        for field in ("name", "base_url", "declared_license", "acquisition_status"):
            value = source.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{source['id']}: {field} debe ser texto no vacío")
        count = source.get("available_text_count")
        if count is not None and (
            isinstance(count, bool) or not isinstance(count, int) or count < 0
        ):
            raise ValueError(f"{source['id']}: available_text_count debe ser entero o null")
        if not isinstance(source.get("sources"), list) or not source["sources"]:
            raise ValueError(f"{source['id']}: faltan referencias de evidencia")

    gate = audit.get("gate")
    if not isinstance(gate, Mapping) or gate.get("id") != "G-0":
        raise ValueError("Falta el gate G-0")
    passed = gate.get("passed")
    downloads_authorized = gate.get("downloads_authorized")
    if not isinstance(passed, bool) or not isinstance(downloads_authorized, bool):
        raise ValueError("El gate debe declarar passed y downloads_authorized como booleanos")
    if downloads_authorized and not passed:
        raise ValueError("No se pueden autorizar descargas si G-0 no ha pasado")
    if passed and gate.get("status") != "PASS":
        raise ValueError("Un gate aprobado debe tener status PASS")
    if not passed and gate.get("status") != "FAIL":
        raise ValueError("Un gate no aprobado debe tener status FAIL")
    if not isinstance(gate.get("reason"), str) or not gate["reason"].strip():
        raise ValueError("El gate debe explicar su decisión")
