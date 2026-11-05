"""Single scale-independent training loop for every RONIN profile."""

from __future__ import annotations

import json
import math
import random
import statistics
import time
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import torch
from torch import nn

from ronin.config import TrainingConfig
from ronin.training.checkpoint import load_checkpoint
from ronin.utils.repro import seed_everything


def resolve_precision(requested: str, device: torch.device) -> torch.dtype | None:
    if requested == "fp32":
        return None
    if requested == "bf16":
        if device.type != "cuda" or not torch.cuda.is_bf16_supported():
            raise RuntimeError("explicit bf16 currently requires a CUDA device with BF16 support")
        return torch.bfloat16
    if requested == "fp16":
        if device.type != "cuda":
            raise RuntimeError("fp16 autocast is supported here only on CUDA")
        return torch.float16
    if requested != "auto":
        raise ValueError(f"unknown precision: {requested}")
    if device.type == "cuda":
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return None


def learning_rate_at(step: int, config: TrainingConfig) -> float:
    if config.warmup_steps and step < config.warmup_steps:
        return config.learning_rate * (step + 1) / config.warmup_steps
    span = max(1, config.max_steps - config.warmup_steps)
    progress = min(1.0, max(0.0, (step - config.warmup_steps) / span))
    cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
    return config.min_learning_rate + cosine * (config.learning_rate - config.min_learning_rate)


def save_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    step: int,
    config: TrainingConfig,
    batch_generator: torch.Generator | None = None,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(
        {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scaler": scaler.state_dict(),
            "step": step,
            "training_config": config.__dict__,
            "torch_rng_state": torch.get_rng_state(),
            "cuda_rng_state_all": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
            "python_rng_state": random.getstate(),
            "numpy_rng_state": np.random.get_state(),
            "batch_generator_state": batch_generator.get_state() if batch_generator is not None else None,
        },
        temporary,
    )
    temporary.replace(destination)


def train(
    model: nn.Module,
    batches: Iterable[tuple[torch.Tensor, torch.Tensor]],
    config: TrainingConfig,
    device: torch.device | str = "cpu",
    checkpoint_dir: str | Path = "checkpoints",
    resume_from: str | Path | None = None,
    metrics_path: str | Path | None = None,
    stop_after_step: int | None = None,
    optimizer_mode: str = "default",
) -> list[float]:
    """Train to config.max_steps; optionally resume from a full checkpoint.

    Seed the model before construction with seed_everything(config.seed) when
    reproducible initialization is required. Resume requires an unchanged
    training config and a batch source whose generator state can be restored.
    """
    config.validate()
    if stop_after_step is not None and not 0 <= stop_after_step <= config.max_steps:
        raise ValueError("stop_after_step must be between zero and config.max_steps")
    if optimizer_mode not in {"default", "foreach", "fused"}:
        raise ValueError("optimizer_mode must be default, foreach, or fused")
    seed_everything(config.seed)
    device = torch.device(device)
    model.to(device)
    optimizer_kwargs = {"lr": config.learning_rate, "weight_decay": config.weight_decay}
    if optimizer_mode != "default":
        optimizer_kwargs[optimizer_mode] = True
    optimizer = torch.optim.AdamW(model.parameters(), **optimizer_kwargs)
    dtype = resolve_precision(config.precision, device)
    use_scaler = dtype == torch.float16 and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_scaler)
    batch_generator = getattr(batches, "generator", None)
    start_step = 0
    if resume_from is not None:
        start_step = load_checkpoint(
            resume_from,
            model,
            optimizer=optimizer,
            scaler=scaler,
            batch_generator=batch_generator if isinstance(batch_generator, torch.Generator) else None,
            map_location="cpu",
            expected_config=config.__dict__,
        )
        if start_step > config.max_steps:
            raise ValueError("checkpoint step exceeds configured max_steps")
    iterator = iter(batches)
    losses: list[float] = []
    step_seconds: list[float] = []
    checkpoint_seconds = 0.0
    training_started = time.perf_counter()

    effective_stop = config.max_steps if stop_after_step is None else stop_after_step
    if effective_stop < start_step:
        raise ValueError("stop_after_step precedes the restored checkpoint step")
    for step in range(start_step, effective_stop):
        step_started = time.perf_counter()
        lr = learning_rate_at(step, config)
        for group in optimizer.param_groups:
            group["lr"] = lr
        optimizer.zero_grad(set_to_none=True)
        accumulated = 0.0
        for _ in range(config.gradient_accumulation_steps):
            inputs, targets = next(iterator)
            inputs, targets = inputs.to(device), targets.to(device)
            with torch.autocast(device_type=device.type, dtype=dtype, enabled=dtype is not None):
                _, loss = model(inputs, targets)
                if loss is None:
                    raise RuntimeError("model did not return a training loss")
                scaled_loss = loss / config.gradient_accumulation_steps
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss at step {step}: {loss.item()}")
            scaler.scale(scaled_loss).backward()
            accumulated += float(loss.detach())
        scaler.unscale_(optimizer)
        grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)
        if not torch.isfinite(grad_norm):
            raise FloatingPointError(f"non-finite gradient norm at step {step}")
        scaler.step(optimizer)
        scaler.update()
        losses.append(accumulated / config.gradient_accumulation_steps)

        if (step + 1) % config.checkpoint_every == 0 or step + 1 == config.max_steps:
            checkpoint_started = time.perf_counter()
            save_checkpoint(
                Path(checkpoint_dir) / f"step-{step + 1:08d}.pt",
                model,
                optimizer,
                scaler,
                step + 1,
                config,
                batch_generator if isinstance(batch_generator, torch.Generator) else None,
            )
            checkpoint_seconds += time.perf_counter() - checkpoint_started
        step_seconds.append(time.perf_counter() - step_started)

    total_seconds = time.perf_counter() - training_started
    if metrics_path is not None:
        ordered = sorted(step_seconds)
        warmup_count = min(10, max(0, len(step_seconds) - 1))
        steady = sorted(step_seconds[warmup_count:]) or ordered
        p95_index = min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)
        batch_size = int(getattr(batches, "batch_size", config.batch_size))
        sequence_length = int(getattr(batches, "sequence_length", 0))
        examples = len(step_seconds) * batch_size * config.gradient_accumulation_steps
        metrics = {
            "steps_completed": len(step_seconds),
            "start_step": start_step,
            "target_steps": config.max_steps,
            "stop_after_step": effective_stop,
            "optimizer_mode": optimizer_mode,
            "total_training_seconds": total_seconds,
            "step_seconds_mean": statistics.mean(step_seconds) if step_seconds else 0.0,
            "step_seconds_median": statistics.median(step_seconds) if step_seconds else 0.0,
            "step_seconds_p95": ordered[p95_index] if ordered else 0.0,
            "steady_state_step_seconds_median": statistics.median(steady) if steady else 0.0,
            "checkpoint_seconds_total": checkpoint_seconds,
            "examples_processed": examples,
            "tokens_processed": examples * sequence_length,
            "examples_per_second": examples / total_seconds if total_seconds else 0.0,
            "tokens_per_second": examples * sequence_length / total_seconds if total_seconds else 0.0,
            "batch_size": batch_size,
            "sequence_length": sequence_length,
            "gradient_accumulation_steps": config.gradient_accumulation_steps,
            "device": str(device),
            "torch_num_threads": torch.get_num_threads(),
            "torch_num_interop_threads": torch.get_num_interop_threads(),
        }
        destination = Path(metrics_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)
    return losses
