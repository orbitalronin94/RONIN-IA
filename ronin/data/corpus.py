"""Validation and rendering of provenance-checked tutor datasets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def prepare(source: str | Path, destination: str | Path) -> int:
    """Verify every JSONL record before rendering prompt/answer training text."""
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
            raise ValueError(f"invalid JSON on line {line_number}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"record must be a JSON object on line {line_number}")
        prompt = record.get("prompt")
        completion = record.get("completion")
        digest = record.get("sha256")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"missing prompt on line {line_number}")
        if not isinstance(completion, str) or not completion.strip():
            raise ValueError(f"missing completion on line {line_number}")
        if record.get("source_type") != "teacher_generated_text":
            raise ValueError(f"unexpected source_type on line {line_number}")
        if record.get("training_terms_reviewed") is not True:
            raise ValueError(f"training terms not confirmed on line {line_number}")
        expected = hashlib.sha256(
            (prompt.strip() + "\n" + completion.strip()).encode("utf-8")
        ).hexdigest()
        if digest != expected:
            raise ValueError(f"SHA-256 mismatch on line {line_number}")
        if digest in seen:
            continue
        seen.add(digest)
        records.append(
            "### Instrucción\n"
            + prompt.strip()
            + "\n\n### Respuesta del tutor\n"
            + completion.strip()
            + "\n\n"
        )
    if not records:
        raise ValueError("no valid tutor examples found")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text("".join(records), encoding="utf-8")
    return len(records)
