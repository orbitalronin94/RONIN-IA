#!/usr/bin/env python3
"""Genera secuencias procedurales sintéticas; no descarga ni reutiliza corpus externo.

El conjunto solo sirve para arrancar y comprobar el pipeline byte-level. No aporta
conocimiento factual ni acredita capacidad lingüística o razonamiento general.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def render_record(index: int) -> str:
    """Renderiza una secuencia determinista a partir de un identificador."""
    a = (index * 7 + 3) % 97
    b = (index * 11 + 5) % 89
    c = (a + b) % 101
    parity = "even" if index % 2 == 0 else "odd"
    bits = format(index % 256, "08b")
    return (
        f"<sample id={index:06d}> "
        f"parity={parity}; a={a:02d}; b={b:02d}; sum={c:03d}; "
        f"bits={bits}; rotate={bits[1:]+bits[:1]}; "
        f"token=R{index % 13:02d}-K{(index * 3) % 17:02d}; "
        f"state=[{a % 5},{b % 7},{c % 11}] </sample>\n"
    )


def build(output: Path, train_count: int, validation_count: int) -> dict[str, object]:
    if train_count < 1 or validation_count < 1:
        raise ValueError("train_count y validation_count deben ser positivos")
    output.mkdir(parents=True, exist_ok=True)
    train = "".join(render_record(i) for i in range(train_count))
    # Disjoint identifiers: validation measures pattern generalization, not memorization.
    validation = "".join(
        render_record(train_count + 10_000 + i) for i in range(validation_count)
    )
    train_path = output / "train.txt"
    validation_path = output / "validation.txt"
    train_path.write_text(train, encoding="utf-8")
    validation_path.write_text(validation, encoding="utf-8")
    manifest = {
        "dataset_id": "ronin-procedural-synthetic-bootstrap-v1",
        "data_kind": "procedural_synthetic_not_external_corpus",
        "external_sources": [],
        "document_counts": {"train": train_count, "validation": validation_count},
        "split_policy": "disjoint deterministic identifier ranges",
        "training_sha256": hashlib.sha256(train.encode("utf-8")).hexdigest(),
        "validation_sha256": hashlib.sha256(validation.encode("utf-8")).hexdigest(),
        "training_eligible_as_knowledge_corpus": False,
        "claims": [
            "Pipeline bootstrap and byte-pattern learning only",
            "Not factual knowledge acquisition",
            "Not a substitute for licensed document training",
        ],
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-count", type=int, default=6000)
    parser.add_argument("--validation-count", type=int, default=1200)
    args = parser.parse_args()
    print(json.dumps(build(args.output, args.train_count, args.validation_count),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
