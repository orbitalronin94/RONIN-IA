#!/usr/bin/env python3
"""Valida la procedencia del JSONL del tutor y prepara un corpus de texto."""

from __future__ import annotations

import argparse
from pathlib import Path

from ronin.data.corpus import prepare


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/teacher/corpus.txt"))
    args = parser.parse_args()
    count = prepare(args.input, args.output)
    print(f"Se han validado y preparado {count} ejemplos en {args.output}")


if __name__ == "__main__":
    main()
