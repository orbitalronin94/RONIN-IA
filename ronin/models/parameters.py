"""Analytical parameter accounting without allocating model weights."""

from __future__ import annotations

from ronin.config import ModelConfig


def count_parameters(config: ModelConfig) -> int:
    """Return exact trainable parameter count for the current tied-weight model."""
    config.validate()
    d = config.d_model
    embedding = config.vocab_size * d + config.context_length * d
    # QKV + attention projection + two-layer 4x MLP + two block layer norms.
    per_block = 12 * d * d + 4 * d
    # QKV (3d), attention projection (d), MLP hidden (4d) and output (d).
    if config.bias:
        per_block += 9 * d
    final_norm = 2 * d
    return embedding + config.n_layers * per_block + final_norm
