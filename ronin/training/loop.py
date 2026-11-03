"""Single scale-independent training loop for every RONIN profile."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable

import torch
from torch import nn

from ronin.config import TrainingConfig


def resolve_precision(requested: str, device: torch.device) -> torch.dtype | None:
    if requested == "fp32":
        return None
    if requested == "bf16":
        if device.type == "cuda" and not torch.cuda.is_bf16_supported():
            raise RuntimeError("bf16 requested but this CUDA device does not support it")
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
    path: str | Path, model: nn.Module, optimizer: torch.optim.Optimizer, step: int,
    config: TrainingConfig,
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    torch.save(
        {
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "step": step,
            "training_config": config.__dict__,
            "torch_rng_state": torch.get_rng_state(),
            "cuda_rng_state_all": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
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
) -> list[float]:
    """Train for max_steps; returns scalar losses for run-level reporting."""
    config.validate()
    device = torch.device(device)
    model.to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay
    )
    dtype = resolve_precision(config.precision, device)
    use_scaler = dtype == torch.float16 and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use_scaler)
    iterator = iter(batches)
    losses: list[float] = []

    for step in range(config.max_steps):
        lr = learning_rate_at(step, config)
        for group in optimizer.param_groups:
            group["lr"] = lr
        optimizer.zero_grad(set_to_none=True)
        accumulated = 0.0
        for _ in range(config.gradient_accumulation_steps):
            inputs, targets = next(iterator)
            inputs, targets = inputs.to(device), targets.to(device)
            with torch.autocast(
                device_type=device.type, dtype=dtype, enabled=dtype is not None
            ):
                _, loss = model(inputs, targets)
                if loss is None:
                    raise RuntimeError("model did not return a training loss")
                scaled_loss = loss / config.gradient_accumulation_steps
            if not torch.isfinite(loss):
                raise FloatingPointError(f"non-finite loss at step {step}: {loss.item()}")
            scaler.scale(scaled_loss).backward()
            accumulated += float(loss.detach())
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)
        scaler.step(optimizer)
        scaler.update()
        losses.append(accumulated / config.gradient_accumulation_steps)

        if (step + 1) % config.checkpoint_every == 0:
            save_checkpoint(
                Path(checkpoint_dir) / f"step-{step + 1:08d}.pt",
                model, optimizer, step + 1, config,
            )
    return losses
