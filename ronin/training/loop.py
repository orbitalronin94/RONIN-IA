"""Single scale-independent training loop for every RONIN profile."""

from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable

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
    scaler: torch.cuda.amp.GradScaler,
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
) -> list[float]:
    """Train to config.max_steps; optionally resume from a full checkpoint.

    Seed the model before construction with seed_everything(config.seed) when
    reproducible initialization is required. Resume requires an unchanged
    training config and a batch source whose generator state can be restored.
    """
    config.validate()
    seed_everything(config.seed)
    device = torch.device(device)
    model.to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    dtype = resolve_precision(config.precision, device)
    use_scaler = dtype == torch.float16 and device.type == "cuda"
    scaler = torch.cuda.amp.GradScaler(enabled=use_scaler)
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

    for step in range(start_step, config.max_steps):
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
            save_checkpoint(
                Path(checkpoint_dir) / f"step-{step + 1:08d}.pt",
                model,
                optimizer,
                scaler,
                step + 1,
                config,
                batch_generator if isinstance(batch_generator, torch.Generator) else None,
            )
    return losses
