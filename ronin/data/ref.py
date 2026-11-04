"""Validación estructural de respuestas propuestas con el esquema REF."""
from __future__ import annotations

import re
from dataclasses import dataclass

FIELDS = ("RESPUESTA", "CLASE_EPISTEMICA", "TIPO_DE_AFIRMACION", "GENERO", "ESTADO_DE_CODIFICACION", "EVIDENCIA", "INCERTIDUMBRE", "POSIBLE_REFUTACION", "REVISION")
ENUMS = {
    "CLASE_EPISTEMICA": {"falsifiable", "non_falsifiable", "mixed", "undetermined"},
    "TIPO_DE_AFIRMACION": {"empirical", "causal", "metaphysical", "normative", "metaphorical", "fictional", "mathematical", "procedural", "descriptive", "mixed", "unknown"},
    "GENERO": {"scientific", "historical", "religious", "literary", "legal", "technical", "philosophical", "other", "unknown"},
    "ESTADO_DE_CODIFICACION": {"clear", "possibly_encoded", "decoded", "unknown"},
}
_HEADING = re.compile(r"(?m)^\s*(" + "|".join(FIELDS) + r")\s*:\s*")
_CONFIDENCE = re.compile(r"(?:confianza(?:\s+razonada)?|confidence)\s*[:=]\s*(0(?:\.\d+)?|1(?:\.0+)?)(?![.,]\d)", re.IGNORECASE)

@dataclass(frozen=True)
class RefValidation:
    valid: bool
    sections: dict[str, str]
    issues: tuple[str, ...]
    confidence: float | None


def parse_ref_completion(completion: str) -> RefValidation:
    """Comprueba estructura y etiquetas, nunca la verdad de la respuesta."""
    if not isinstance(completion, str) or not completion.strip():
        return RefValidation(False, {}, ("respuesta vacía o no textual",), None)
    matches = list(_HEADING.finditer(completion))
    sections: dict[str, str] = {}
    issues: list[str] = []
    for index, match in enumerate(matches):
        name = match.group(1)
        if name in sections:
            issues.append(f"apartado duplicado: {name}")
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(completion)
        sections[name] = completion[match.end():end].strip()
    for name in FIELDS:
        if name not in sections:
            issues.append(f"falta el apartado {name}")
        elif not sections[name]:
            issues.append(f"apartado vacío: {name}")
    for name, allowed in ENUMS.items():
        value = sections.get(name, "").split(";", 1)[0].split(",", 1)[0].strip().lower()
        if value and value not in allowed:
            issues.append(f"etiqueta no permitida en {name}: {value}")
    confidence = None
    confidence_matches = list(_CONFIDENCE.finditer(sections.get("INCERTIDUMBRE", "")))
    if len(confidence_matches) != 1:
        issues.append("INCERTIDUMBRE debe contener exactamente una confianza numérica entre 0 y 1")
    else:
        confidence = float(confidence_matches[0].group(1))
    coding = sections.get("ESTADO_DE_CODIFICACION", "").split(";", 1)[0].strip().lower()
    if coding == "decoded":
        evidence = sections.get("EVIDENCIA", "").lower()
        if not any(term in evidence for term in ("referencia", "fuente", "prueba", "evidencia", "verific")):
            issues.append("decoded requiere describir evidencia verificable en EVIDENCIA")
    return RefValidation(not issues, sections, tuple(issues), confidence)
