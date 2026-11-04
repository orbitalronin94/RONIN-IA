"""Filtro epistemico de RONIN (REF).

Este paquete define anotaciones y validaciones; no infiere por si solo
la falsabilidad ni el significado de un texto.
"""

from ronin.epistemic.schema import (
    CLAIM_TYPES,
    ENCODING_STATUSES,
    EPISTEMIC_CLASSES,
    GENRES,
    validate_annotation,
)

__all__ = [
    "EPISTEMIC_CLASSES",
    "ENCODING_STATUSES",
    "GENRES",
    "CLAIM_TYPES",
    "validate_annotation",
]
