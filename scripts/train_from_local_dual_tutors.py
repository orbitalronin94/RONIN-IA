#!/usr/bin/env python3
"""Ejecuta una iteración completa: dos tutores locales, filtro gold y entrenamiento RONIN."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--steps", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20261105)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/dual-distillation"))
    parser.add_argument("--checkpoints", type=Path, default=Path("checkpoints/dual-teacher-candidate"))
    args = parser.parse_args()
    if not 1 <= args.steps <= 1000:
        parser.error("--steps debe estar entre 1 y 1000")
    try:
        import torch
    except ImportError:
        parser.error("PyTorch no está instalado")
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        parser.error("--device cuda solicitado pero CUDA no está disponible")

    generation = [
        sys.executable, "scripts/distill_mmlu_pro_dual_tutor.py",
        "--count", str(args.count),
        "--quantization", args.quantization,
        "--seed", str(args.seed),
        "--output-dir", str(args.output_dir),
    ]
    subprocess.run(generation, check=True)

    corpus = args.output_dir / "train.txt"
    if not corpus.is_file() or corpus.stat().st_size == 0:
        raise RuntimeError("El filtro dual no produjo un corpus; entrenamiento cancelado")

    training = [
        sys.executable, "scripts/train_text.py",
        "--text", str(corpus),
        "--profile", "tiny",
        "--steps", str(args.steps),
        "--context-length", "2048",
        "--seed", str(args.seed + 1),
        "--device", device,
        "--checkpoints", str(args.checkpoints),
        "--metrics-out", str(args.output_dir / "training-metrics.json"),
    ]
    print(f"Dispositivo de entrenamiento del estudiante: {device}")
    subprocess.run(training, check=True)
    checkpoint = args.checkpoints / f"step-{args.steps:08d}.pt"
    if not checkpoint.is_file():
        raise RuntimeError(f"No se generó el checkpoint esperado: {checkpoint}")

    evaluation = [
        sys.executable, "scripts/evaluate_mmlu_pro.py",
        "--checkpoint", str(checkpoint),
        "--profile", "tiny",
        "--context-length", "2048",
        "--limit", "140",
        "--split", "test",
        "--device", device,
        "--output", str(args.output_dir / "mmlu-pro-test-eval.json"),
    ]
    subprocess.run(evaluation, check=True)
    print(f"Entrenamiento completado. Checkpoint: {checkpoint}")
    print(f"Holdout MMLU-Pro test: {args.output_dir / 'mmlu-pro-test-eval.json'}")
    print("La promoción sigue pendiente de comparación con el checkpoint de main.")


if __name__ == "__main__":
    main()
