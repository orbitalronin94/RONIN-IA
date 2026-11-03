"""Autoregressive generation utilities."""

from __future__ import annotations

import torch
from torch.nn import functional as F

from ronin.models.transformer import RoninLM


@torch.no_grad()
def generate(
    model: RoninLM,
    input_ids: torch.Tensor,
    max_new_tokens: int,
    temperature: float = 1.0,
    top_k: int | None = None,
) -> torch.Tensor:
    if max_new_tokens < 0 or temperature <= 0:
        raise ValueError("max_new_tokens must be non-negative and temperature positive")
    if top_k is not None and top_k < 1:
        raise ValueError("top_k must be positive")
    if input_ids.ndim != 2 or input_ids.shape[1] == 0:
        raise ValueError("input_ids must be a non-empty [batch, sequence] tensor")
    was_training = model.training
    model.eval()
    try:
        result = input_ids
        for _ in range(max_new_tokens):
            context = result[:, -model.config.context_length :]
            logits, _ = model(context)
            next_logits = logits[:, -1, :] / temperature
            if top_k is not None:
                k = min(top_k, next_logits.shape[-1])
                threshold = torch.topk(next_logits, k, dim=-1).values[:, -1, None]
                next_logits = next_logits.masked_fill(next_logits < threshold, float("-inf"))
            probabilities = F.softmax(next_logits, dim=-1)
            next_token = torch.multinomial(probabilities, num_samples=1)
            result = torch.cat((result, next_token), dim=1)
        return result
    finally:
        model.train(was_training)
