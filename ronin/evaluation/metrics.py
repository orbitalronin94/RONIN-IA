"""Tokenizer-aware language-model evaluation metrics."""

from __future__ import annotations

import math

import torch
from torch import nn


@torch.no_grad()
def evaluate_loss(
    model: nn.Module, batches, max_batches: int, device: torch.device | str = "cpu"
) -> float:
    if max_batches < 1:
        raise ValueError("max_batches must be positive")
    device = torch.device(device)
    was_training = model.training
    model.eval()
    losses: list[float] = []
    try:
        iterator = iter(batches)
        for _ in range(max_batches):
            inputs, targets = next(iterator)
            _, loss = model(inputs.to(device), targets.to(device))
            if loss is None or not torch.isfinite(loss):
                raise FloatingPointError("evaluation produced a non-finite loss")
            losses.append(float(loss))
    finally:
        model.train(was_training)
    return sum(losses) / len(losses)


def perplexity(mean_cross_entropy: float) -> float:
    if not math.isfinite(mean_cross_entropy):
        raise ValueError("cross entropy must be finite")
    return math.exp(min(mean_cross_entropy, 80.0))


def bits_per_byte(total_nll_nats: float, byte_count: int) -> float:
    if byte_count < 1 or not math.isfinite(total_nll_nats) or total_nll_nats < 0:
        raise ValueError("expected finite non-negative NLL and positive byte_count")
    return total_nll_nats / (math.log(2.0) * byte_count)
