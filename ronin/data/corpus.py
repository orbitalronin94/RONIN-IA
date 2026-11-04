"""Validación y preparación de corpus generados por tutores locales."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def prepare(source: str | Path, destination: str | Path) -> int:
    """Verifica la procedencia de cada registro antes de preparar texto de entrenamiento."""
    source_path = Path(source)
    destination_path = Path(destination)
    seen: set[str] = set()
    records: list[str] = []
    for line_number, line in enumerate(
        source_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON no válido en la línea {line_number}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"El registro debe ser un objeto JSON en la línea {line_number}")
        prompt = record.get("prompt")
        completion = record.get("completion")
        digest = record.get("sha256")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"Falta el prompt en la línea {line_number}")
        if not isinstance(completion, str) or not completion.strip():
            raise ValueError(f"Falta la respuesta en la línea {line_number}")
        if record.get("source_type") != "local_mit_teacher_generated_text":
            raise ValueError(f"Tipo de origen inesperado en la línea {line_number}")
        if (
            record.get("teacher_model_license") != "MIT"
            or record.get("teacher_model_license_verified") is not True
        ):
            raise ValueError(f"El modelo tutor no acredita licencia MIT en la línea {line_number}")
        if record.get("generated_output_license") != "not_asserted":
            raise ValueError(f"No se debe atribuir licencia automática a la salida en la línea {line_number}")
        if not record.get("teacher_model_license_url"):
            raise ValueError(f"Falta la procedencia de licencia del modelo en la línea {line_number}")
        if record.get("teacher_weights_loaded_locally") is not True:
            raise ValueError(f"No consta que el tutor se ejecutara localmente en la línea {line_number}")
        if record.get("teacher_weights_imported_into_student") is not False:
            raise ValueError(f"Se detectó una importación de pesos en la línea {line_number}")
        if record.get("student_initialization") != "random":
            raise ValueError(f"El estudiante no declara inicialización aleatoria en la línea {line_number}")
        if not record.get("teacher_revision"):
            raise ValueError(f"Falta la revisión del tutor en la línea {line_number}")
        expected = hashlib.sha256(
            (prompt.strip() + "\n" + completion.strip()).encode("utf-8")
        ).hexdigest()
        if digest != expected:
            raise ValueError(f"SHA-256 no coincide en la línea {line_number}")
        if digest in seen:
            continue
        seen.add(digest)
        records.append(
            "### Instrucción\n" + prompt.strip()
            + "\n\n### Respuesta del tutor\n" + completion.strip() + "\n\n"
        )
    if not records:
        raise ValueError("No se han encontrado ejemplos válidos del tutor")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text("".join(records), encoding="utf-8")
    return len(records)
