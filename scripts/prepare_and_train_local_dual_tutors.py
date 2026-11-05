#!/usr/bin/env python3
"""Descarga ambos tutores GGUF locales y ejecuta una iteración completa de RONIN."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.download_dual_teachers import download


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--models-dir", type=Path, default=Path("models/teachers"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/dual-distillation"))
    parser.add_argument("--checkpoints", type=Path, default=Path("checkpoints/dual-teacher-candidate"))
    args = parser.parse_args()

    # Descargas y verificaciones separadas; no se necesita ningún token de API.
    download("qwen3.6-27b", args.quantization, args.models_dir)
    download("deepseek-r1-distill-32b", args.quantization, args.models_dir)

    command = [
        sys.executable, "scripts/train_from_local_dual_tutors.py",
        "--count", str(args.count),
        "--quantization", args.quantization,
        "--steps", str(args.steps),
        "--seed", str(args.seed),
        "--device", args.device,
        "--output-dir", str(args.output_dir),
        "--checkpoints", str(args.checkpoints),
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
