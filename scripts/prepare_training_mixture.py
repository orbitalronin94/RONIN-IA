#!/usr/bin/env python3
"""Construye una mezcla reproducible de corpus de entrenamiento autorizados."""

from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path

_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_HOLDOUT_MARKERS = {"validation", "valid", "test", "eval", "benchmark"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_input(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("cada entrada debe tener formato nombre=ruta")
    name, raw_path = value.split("=", 1)
    if not _NAME.fullmatch(name) or not raw_path:
        raise argparse.ArgumentTypeError(f"entrada no válida: {value!r}")
    path = Path(raw_path)
    if any(part.lower() in _HOLDOUT_MARKERS for part in path.parts):
        raise argparse.ArgumentTypeError(f"no se permite usar un holdout como entrenamiento: {path}")
    if path.stem.lower() in _HOLDOUT_MARKERS:
        raise argparse.ArgumentTypeError(f"no se permite usar un holdout como entrenamiento: {path}")
    return name, path


def prepare_mixture(inputs: Iterable[tuple[str, Path]], output: Path, manifest_path: Path) -> dict:
    entries = list(inputs)
    if not entries:
        raise ValueError("se requiere al menos un corpus de entrenamiento")
    names = [name for name, _ in entries]
    if len(names) != len(set(names)):
        raise ValueError("los nombres de las fuentes deben ser únicos")

    output = output.resolve()
    manifest_path = manifest_path.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    output_digest = hashlib.sha256()
    total_input_bytes = 0

    with output.open("wb") as destination:
        for name, source_path in entries:
            source_path = source_path.resolve()
            if source_path in {output, manifest_path}:
                raise ValueError("los archivos de entrada no pueden sobrescribir las salidas")
            if not source_path.is_file():
                raise FileNotFoundError(f"no existe el corpus {name}: {source_path}")
            header = f"\n\n=== FUENTE DE ENTRENAMIENTO: {name} ===\n\n".encode()
            destination.write(header)
            output_digest.update(header)
            source_digest = hashlib.sha256()
            decoder = codecs.getincrementaldecoder("utf-8")("strict")
            source_bytes = 0
            last_byte = b""
            with source_path.open("rb") as source:
                while chunk := source.read(1024 * 1024):
                    decoder.decode(chunk, final=False)
                    source_digest.update(chunk)
                    output_digest.update(chunk)
                    destination.write(chunk)
                    source_bytes += len(chunk)
                    last_byte = chunk[-1:]
                decoder.decode(b"", final=True)
            if source_bytes == 0:
                raise ValueError(f"el corpus {name} está vacío")
            if last_byte != b"\n":
                destination.write(b"\n")
                output_digest.update(b"\n")
            rows.append({
                "id": name,
                "input_filename": source_path.name,
                "bytes": source_bytes,
                "sha256": source_digest.hexdigest(),
            })
            total_input_bytes += source_bytes

    for row in rows:
        row["byte_share"] = row["bytes"] / total_input_bytes

    result = {
        "schema": "ronin-training-mixture-v1",
        "source_count": len(rows),
        "total_input_bytes": total_input_bytes,
        "output_bytes": output.stat().st_size,
        "output_sha256": output_digest.hexdigest(),
        "sources": rows,
        "policy": (
            "Solo se mezclan archivos de entrenamiento explícitos. Los holdouts, "
            "benchmarks y corpus con revisión pendiente deben permanecer fuera."
        ),
    }
    manifest_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=parse_input, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    result = prepare_mixture(args.input, args.output, args.manifest)
    print(json.dumps({
        "source_count": result["source_count"],
        "total_input_bytes": result["total_input_bytes"],
        "output_bytes": result["output_bytes"],
        "output_sha256": result["output_sha256"],
        "sources": result["sources"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
