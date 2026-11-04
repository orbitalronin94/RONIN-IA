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
    parser.add_argument("--seed", type=int, default=None, help="semilla de inicialización y muestreo")
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
    if args.steps is not None:
        if not 1 <= args.steps <= 1_000:
            parser.error("--steps must be between 1 and 1000 for the tiny profile")
        training_config = replace(
            training_config,
            max_steps=args.steps,
            warmup_steps=min(training_config.warmup_steps, max(1, args.steps // 10)),
        )
    if args.seed is not None:
        training_config = replace(training_config, seed=args.seed)
    tokens = encode_text_file(args.text, ByteTokenizer())
    if model_config.vocab_size != ByteTokenizer.vocab_size:
        raise ValueError("tiny profile and byte tokenizer vocabulary do not match")
    seed_everything(training_config.seed)
    model = RoninLM(model_config)
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
