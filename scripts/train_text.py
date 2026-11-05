#!/usr/bin/env python3
"""Train the tiny profile on an operator-supplied UTF-8 text corpus.

This is a pipeline smoke/early experiment, not a claim of production-quality data.
The corpus must be licensed for model training and kept out of version control.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.models.transformer import RoninLM
from ronin.tokenizer.byte import ByteTokenizer
from ronin.training.loop import train
from ronin.utils.repro import seed_everything


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", type=Path, required=True, help="approved UTF-8 corpus file")
    parser.add_argument("--profile", choices=["tiny"], default="tiny")
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None, help="tasa de aprendizaje para fine-tuning")
    parser.add_argument("--min-learning-rate", type=float, default=None, help="tasa mínima del scheduler")
    parser.add_argument("--context-length", type=int, default=None, help="Contexto en bytes; permite alinear el entrenamiento con el evaluador")
    parser.add_argument("--seed", type=int, default=None, help="semilla de inicialización y muestreo")
    parser.add_argument(
        "--init-checkpoint",
        type=Path,
        default=None,
        help="checkpoint previo del que cargar solo los pesos del modelo",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoints", type=Path, default=Path("checkpoints/tiny"))
    parser.add_argument("--metrics-out", type=Path, default=None, help="JSON con tiempos y throughput")
    parser.add_argument("--num-threads", type=int, default=None, help="Hilos intra-op de PyTorch")
    parser.add_argument("--interop-threads", type=int, default=None, help="Hilos inter-op de PyTorch")
    args = parser.parse_args()

    if args.num_threads is not None:
        if args.num_threads < 1:
            parser.error("--num-threads must be positive")
        torch.set_num_threads(args.num_threads)
    if args.interop_threads is not None:
        if args.interop_threads < 1:
            parser.error("--interop-threads must be positive")
        torch.set_num_interop_threads(args.interop_threads)

    model_config, training_config = get_profile(args.profile)
    if args.context_length is not None:
        if not 128 <= args.context_length <= 8192:
            parser.error("--context-length must be between 128 and 8192")
        model_config = replace(model_config, context_length=args.context_length)
    if args.steps is not None:
        if not 1 <= args.steps <= 1_000:
            parser.error("--steps must be between 1 and 1000 for the tiny profile")
        training_config = replace(
            training_config,
            max_steps=args.steps,
            warmup_steps=min(training_config.warmup_steps, max(1, args.steps // 10)),
        )
    overrides = {}
    if args.seed is not None:
        overrides["seed"] = args.seed
    if args.learning_rate is not None:
        if args.learning_rate <= 0:
            parser.error("--learning-rate must be positive")
        overrides["learning_rate"] = args.learning_rate
    if args.min_learning_rate is not None:
        if args.min_learning_rate < 0:
            parser.error("--min-learning-rate must be non-negative")
        overrides["min_learning_rate"] = args.min_learning_rate
    if overrides:
        training_config = replace(training_config, **overrides)
    training_config.validate()
    tokens = encode_text_file(args.text, ByteTokenizer())
    if model_config.vocab_size != ByteTokenizer.vocab_size:
        raise ValueError("tiny profile and byte tokenizer vocabulary do not match")
    seed_everything(training_config.seed)
    model = RoninLM(model_config)
    if args.init_checkpoint is not None:
        if not args.init_checkpoint.is_file():
            parser.error(f"no existe el checkpoint inicial: {args.init_checkpoint}")
        payload = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)
        state_dict = payload.get("model") if isinstance(payload, dict) else None
        if not isinstance(state_dict, dict):
            raise ValueError("el checkpoint inicial debe contener un state_dict en la clave 'model'")
        model.load_state_dict(state_dict, strict=True)
        print(f"Pesos iniciales cargados desde {args.init_checkpoint}")
    batches = NextTokenBatches(
        tokens, training_config.batch_size, model_config.context_length, training_config.seed
    )
    losses = train(
        model,
        batches,
        training_config,
        device=args.device,
        checkpoint_dir=args.checkpoints,
        metrics_path=args.metrics_out,
    )
    print(
        f"Completed {len(losses)} steps; final loss={losses[-1]:.5f}. "
        "This run is not a held-out evaluation."
    )


if __name__ == "__main__":
    main()
