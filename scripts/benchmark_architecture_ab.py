#!/usr/bin/env python3
"""Controlled architecture comparison: historical GPT vs current RONIN."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from dataclasses import replace
from pathlib import Path

import torch

from ronin.config import get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.models.transformer import RoninLM as CurrentRoninLM
from ronin.tokenizer.byte import ByteTokenizer
from ronin.training.loop import train
from ronin.utils.repro import seed_everything


def load_legacy_class():
    source = Path(__file__).resolve().parents[1] / "ronin/models/legacy_transformer.py"
    spec = importlib.util.spec_from_file_location("ronin_legacy_transformer", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("No se pudo cargar la arquitectura histórica")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RoninLM


@torch.no_grad()
def evaluate(model, tokens: torch.Tensor, config, seed: int, batches: int, batch_size: int):
    model.eval()
    sampler = NextTokenBatches(tokens, batch_size, config.context_length, seed=seed)
    total_nll = 0.0
    total_tokens = 0
    iterator = iter(sampler)
    for _ in range(batches):
        x, y = next(iterator)
        _, loss = model(x, y)
        if loss is None or not torch.isfinite(loss):
            raise FloatingPointError("Pérdida no finita durante evaluación")
        count = y.numel()
        total_nll += float(loss) * count
        total_tokens += count
    mean_nll = total_nll / total_tokens
    return {
        "cross_entropy_nats_per_byte": mean_nll,
        "bits_per_byte": mean_nll / math.log(2.0),
        "perplexity": math.exp(mean_nll),
        "evaluated_tokens": total_tokens,
    }


def run_one(label, model_class, model_config, training_config, train_tokens,
            validation_tokens, seed, steps, batches, batch_size, output_dir):
    seed_everything(seed, deterministic=True)
    model = model_class(model_config)
    parameters = model.parameter_count
    sampler = NextTokenBatches(
        train_tokens, training_config.batch_size, model_config.context_length, seed=seed
    )
    run_config = replace(
        training_config,
        seed=seed,
        max_steps=steps,
        warmup_steps=min(training_config.warmup_steps, max(1, steps // 10)),
        checkpoint_every=steps,
    )
    started = time.perf_counter()
    train(
        model,
        sampler,
        run_config,
        device="cpu",
        checkpoint_dir=output_dir / label / str(seed),
    )
    elapsed = time.perf_counter() - started
    metrics = evaluate(model, validation_tokens, model_config, seed + 10_000, batches, batch_size)
    return {
        "architecture": label,
        "seed": seed,
        "parameters": parameters,
        "steps": steps,
        "training_seconds": elapsed,
        **metrics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--validation-text", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--seeds", default="1337,2027,42")
    parser.add_argument("--eval-batches", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.steps <= 1000 or args.eval_batches < 1 or args.batch_size < 1:
        parser.error("presupuesto o evaluación fuera de rango")
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    if not seeds:
        parser.error("se necesita al menos una semilla")

    model_config, base_training = get_profile("tiny")
    train_tokens = encode_text_file(args.train_text, ByteTokenizer())
    validation_tokens = encode_text_file(args.validation_text, ByteTokenizer())
    if model_config.vocab_size != ByteTokenizer.vocab_size:
        raise ValueError("tiny no coincide con ByteTokenizer")
    legacy_class = load_legacy_class()
    results = []
    for seed in seeds:
        for label, model_class in (
            ("historica_gpt_layernorm_gelu_abspos", legacy_class),
            ("actual_rope_rmsnorm_swiglu_gqa", CurrentRoninLM),
        ):
            print(f"Ejecutando {label}, semilla={seed}", flush=True)
            results.append(run_one(
                label, model_class, model_config, base_training, train_tokens,
                validation_tokens, seed, args.steps, args.eval_batches,
                args.batch_size, args.output.parent / "checkpoints",
            ))

    grouped = {}
    for label in sorted({row["architecture"] for row in results}):
        rows = [row for row in results if row["architecture"] == label]
        bpb = [row["bits_per_byte"] for row in rows]
        grouped[label] = {
            "runs": rows,
            "mean_bits_per_byte": sum(bpb) / len(bpb),
            "min_bits_per_byte": min(bpb),
            "max_bits_per_byte": max(bpb),
            "mean_training_seconds": sum(row["training_seconds"] for row in rows) / len(rows),
            "parameter_count": rows[0]["parameters"],
        }
    report = {
        "experiment": "architecture_ab_same_data_tokenizer_profile_steps_and_seeds",
        "profile": "tiny",
        "training_steps_per_run": args.steps,
        "seeds": seeds,
        "evaluation_batches": args.eval_batches,
        "evaluation_batch_size": args.batch_size,
        "sequence_length": model_config.context_length,
        "tokenizer": "byte-v1",
        "model_config": model_config.__dict__,
        "training_config": replace(base_training, max_steps=args.steps).__dict__,
        "architectures": grouped,
        "interpretation": (
            "Comparación del paquete arquitectónico completo. Los recuentos de parámetros "
            "pueden diferir; no es una comparación iso-parámetro ni a FLOPs igualados."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        label: {
            "mean_bits_per_byte": value["mean_bits_per_byte"],
            "parameter_count": value["parameter_count"],
            "mean_training_seconds": value["mean_training_seconds"],
        }
        for label, value in grouped.items()
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
