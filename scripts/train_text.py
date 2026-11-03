#!/usr/bin/env python3
"""Train the tiny profile on an operator-supplied UTF-8 text corpus.

This is a pipeline smoke/early experiment, not a claim of production-quality data.
The corpus must be licensed for model training and kept out of version control.
"""

from __future__ import annotations

import argparse
from pathlib import Path

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
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--checkpoints", type=Path, default=Path("checkpoints/tiny"))
    args = parser.parse_args()

    model_config, training_config = get_profile(args.profile)
    if args.steps is not None:
        if not 1 <= args.steps <= 1_000:
            parser.error("--steps must be between 1 and 1000 for the tiny profile")
        from dataclasses import replace
        training_config = replace(\n            training_config,\n            max_steps=args.steps,\n            warmup_steps=min(training_config.warmup_steps, max(1, args.steps // 10)),\n        )
    tokens = encode_text_file(args.text, ByteTokenizer())
    if model_config.vocab_size != ByteTokenizer.vocab_size:
        raise ValueError("tiny profile and byte tokenizer vocabulary do not match")
    seed_everything(training_config.seed)
    model = RoninLM(model_config)
    batches = NextTokenBatches(
        tokens, training_config.batch_size, model_config.context_length, training_config.seed
    )
    losses = train(
        model, batches, training_config, device=args.device, checkpoint_dir=args.checkpoints
    )
    print(
        f"Completed {len(losses)} steps; final loss={losses[-1]:.5f}. "
        "This run is not a held-out evaluation."
    )


if __name__ == "__main__":
    main()
