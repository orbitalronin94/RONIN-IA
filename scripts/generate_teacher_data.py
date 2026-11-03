#!/usr/bin/env python3
"""Genera un corpus con un modelo auxiliar MIT descargado y ejecutado en local."""

from __future__ import annotations

import argparse
from pathlib import Path

from ronin.data.prompts import build_prompts
from ronin.data.teacher import load_local_teacher, write_teacher_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--output", type=Path, default=Path("artifacts/teacher/train.jsonl"))
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-new-tokens", type=int, default=192)
    parser.add_argument("--seed", type=int, default=1337)
    args = parser.parse_args()
    model, tokenizer, manifest = load_local_teacher(args.model_dir, args.device)
    count = write_teacher_dataset(
        build_prompts(args.count),
        args.output,
        model,
        tokenizer,
        manifest,
        max_new_tokens=args.max_new_tokens,
        seed=args.seed,
    )
    print(f"Se generaron {count} ejemplos con {manifest['model_id']} en {args.output}")


if __name__ == "__main__":
    main()
