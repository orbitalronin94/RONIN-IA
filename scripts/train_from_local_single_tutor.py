#!/usr/bin/env python3
"""Una iteración de destilación local Qwen3-8B y entrenamiento/evaluación de RoninLM."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=96)
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20261106)
    parser.add_argument("--quantization", choices=["4bit", "8bit"], default="4bit")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--model-dir", type=Path, default=Path("models/teachers/qwen3-8b/4bit"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/qwen3-single-tutor"))
    parser.add_argument("--checkpoints", type=Path, default=Path("checkpoints/qwen3-single-tutor"))
    parser.add_argument("--init-checkpoint", type=Path)
    args = parser.parse_args()
    if not 1 <= args.steps <= 2000:
        parser.error("--steps debe estar entre 1 y 2000")

    try:
        import torch
    except ImportError:
        parser.error("PyTorch no está instalado")
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        parser.error("--device cuda solicitado pero CUDA no está disponible")

    subprocess.run([
        sys.executable, "scripts/distill_mmlu_pro_single_tutor.py",
        "--model-dir", str(args.model_dir),
        "--output-dir", str(args.output_dir),
        "--count", str(args.count),
        "--quantization", args.quantization,
        "--seed", str(args.seed),
    ], check=True)
    corpus = args.output_dir / "train.txt"
    if not corpus.is_file() or corpus.stat().st_size == 0:
        raise RuntimeError("El tutor no produjo corpus verificado; entrenamiento cancelado")

    training = [
        sys.executable, "scripts/train_text.py",
        "--text", str(corpus), "--profile", "tiny",
        "--steps", str(args.steps), "--context-length", "2048",
        "--seed", str(args.seed + 1), "--device", device,
        "--checkpoints", str(args.checkpoints),
        "--metrics-out", str(args.output_dir / "training-metrics.json"),
    ]
    if args.init_checkpoint:
        if not args.init_checkpoint.is_file():
            raise FileNotFoundError(args.init_checkpoint)
        training.extend(["--init-checkpoint", str(args.init_checkpoint)])
    subprocess.run(training, check=True)

    checkpoint = args.checkpoints / f"step-{args.steps:08d}.pt"
    if not checkpoint.is_file():
        raise RuntimeError(f"No se generó el checkpoint esperado: {checkpoint}")
    # Validation es la única señal de desarrollo. El split test no se carga aquí.
    subprocess.run([
        sys.executable, "scripts/evaluate_mmlu_pro.py",
        "--checkpoint", str(checkpoint), "--profile", "tiny",
        "--context-length", "2048", "--limit", "140",
        "--split", "validation", "--device", device,
        "--output", str(args.output_dir / "mmlu-pro-validation.json"),
    ], check=True)
    print(f"Checkpoint candidato: {checkpoint}")
    print(f"Evaluación de desarrollo: {args.output_dir / 'mmlu-pro-validation.json'}")
    print("No se promueve automáticamente: comparar con main y conservar test para la verificación final.")


if __name__ == "__main__":
    main()
