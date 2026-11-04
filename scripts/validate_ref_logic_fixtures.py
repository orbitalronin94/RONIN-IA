"""Validación estructural de fixtures de lógica/falacias REF; no evalúa semántica."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ronin.epistemic.schema import validate_annotation


def validate_file(path: Path) -> int:
    seen: set[str] = set()
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("cada línea debe ser un objeto JSON")
            validate_annotation(record)
            record_id = record["record_id"]
            if record_id in seen:
                raise ValueError(f"record_id duplicado: {record_id}")
            seen.add(record_id)
            count += 1
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"{path}:{line_number}: {exc}") from exc
    if count == 0:
        raise SystemExit(f"{path}: no contiene fixtures")
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/fixtures/ref_logic_calibration.jsonl")
    args = parser.parse_args()
    count = validate_file(Path(args.input))
    print(f"OK: {count} fixtures REF estructuralmente válidos; no son datos de entrenamiento.")


if __name__ == "__main__":
    main()
