#!/usr/bin/env python3
"""Genera corpus sintéticos deterministas para probar el circuito sin datos externos.

El texto es artificial y no sirve para medir conocimiento ni competencia lingüística.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

SYLLABLES = (
    "bena", "doru", "fali", "gume", "hira", "javo", "keli", "luma",
    "mori", "nusa", "peta", "quro", "ravi", "seno", "tika", "vulo",
)
CONNECTORS = ("además", "después", "mientras", "entonces", "aunque", "por tanto")


def make_text(seed: int, sentences: int) -> str:
    rng = random.Random(seed)
    rows = []
    for index in range(sentences):
        subject, verb, object_ = (rng.choice(SYLLABLES) for _ in range(3))
        modifier = rng.choice(SYLLABLES)
        connector = rng.choice(CONNECTORS)
        rows.append(
            f"Registro {index}: {subject} {verb} {object_}; "
            f"{connector}, {modifier} {subject}.\n"
        )
    return "".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-sentences", type=int, default=12000)
    parser.add_argument("--validation-sentences", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=8675309)
    args = parser.parse_args()
    if args.train_sentences < 100 or args.validation_sentences < 100:
        parser.error("cada partición necesita al menos 100 frases")
    args.output.mkdir(parents=True, exist_ok=True)
    train = make_text(args.seed, args.train_sentences)
    validation = make_text(args.seed + 1, args.validation_sentences)
    (args.output / "train.txt").write_text(train, encoding="utf-8")
    (args.output / "validation.txt").write_text(validation, encoding="utf-8")
    print(
        f"Corpus sintético generado: train={len(train)} bytes, "
        f"validation={len(validation)} bytes; semilla={args.seed}"
    )


if __name__ == "__main__":
    main()
