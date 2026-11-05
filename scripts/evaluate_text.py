#!/usr/bin/env python3
"""Evalúa un checkpoint RONIN sobre un corpus UTF-8 reservado e independiente."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.models.transformer import RoninLM
from ronin.tokenizer.byte import ByteTokenizer
from ronin.training.checkpoint import load_checkpoint
from ronin.utils.repro import seed_everything


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@torch.no_grad()
def evaluate_checkpoint(
    checkpoint: Path,
    validation_text: Path,
    profile: str,
    batches: int = 128,
    batch_size: int = 2,
    seed: int = 2026,
    device: str = "cpu",
    identity_gated_ninth_layer: bool = False,
) -> dict[str, object]:
    if batches < 1 or batch_size < 1:
        raise ValueError("batches y batch_size deben ser positivos")
    model_config, _ = get_profile(profile)
    if identity_gated_ninth_layer:
        model_config = replace(model_config, n_layers=model_config.n_layers + 1, identity_last_layer=True)
    tokenizer = ByteTokenizer()
    if model_config.vocab_size != tokenizer.vocab_size:
        raise ValueError("el perfil seleccionado no es compatible con ByteTokenizer")
    tokens = encode_text_file(validation_text, tokenizer)
    if tokens.numel() < model_config.context_length + 1:
        raise ValueError(
            f"el corpus de validación necesita al menos {model_config.context_length + 1} bytes"
        )

    seed_everything(seed)
    model = RoninLM(model_config)
    step = load_checkpoint(
        checkpoint,
        model,
        map_location="cpu",
        restore_rng=False,
    )
    target_device = torch.device(device)
    model.to(target_device)
    model.eval()
    sampler = NextTokenBatches(
        tokens, batch_size, model_config.context_length, seed=seed
    )
    iterator = iter(sampler)
    total_nll = 0.0
    total_tokens = 0
    for _ in range(batches):
        inputs, targets = next(iterator)
        _, loss = model(inputs.to(target_device), targets.to(target_device))
        if loss is None or not torch.isfinite(loss):
            raise FloatingPointError("la evaluación produjo una pérdida no finita")
        count = targets.numel()
        total_nll += float(loss) * count
        total_tokens += count

    mean_loss = total_nll / total_tokens
    return {
        "profile": profile,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256_file(checkpoint),
        "checkpoint_step": step,
        "validation_corpus": str(validation_text),
        "validation_sha256": sha256_file(validation_text),
        "tokenizer": "byte-v1",
        "seed": seed,
        "batches": batches,
        "batch_size": batch_size,
        "sequence_length": model_config.context_length,
        "evaluated_tokens": total_tokens,
        "parameter_count": model.parameter_count,
        "cross_entropy_nats_per_byte": mean_loss,
        "perplexity": math.exp(mean_loss),
        "bits_per_byte": mean_loss / math.log(2.0),
        "device": str(target_device),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--validation-text", type=Path, required=True)
    parser.add_argument("--profile", choices=["tiny"], default="tiny")
    parser.add_argument("--batches", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--identity-gated-ninth-layer", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = evaluate_checkpoint(
        args.checkpoint,
        args.validation_text,
        args.profile,
        batches=args.batches,
        batch_size=args.batch_size,
        seed=args.seed,
        device=args.device,
        identity_gated_ninth_layer=args.identity_gated_ninth_layer,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
