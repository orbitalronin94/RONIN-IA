"""Recuento analítico de parámetros sin reservar memoria para los pesos."""

from __future__ import annotations

from ronin.config import ModelConfig


def count_parameters(config: ModelConfig) -> int:
    """Devuelve el número exacto de parámetros entrenables del modelo actual."""
    config.validate()
    d_model = config.d_model
    head_dim = d_model // config.n_heads
    kv_width = int(config.n_kv_heads) * head_dim
    d_ff = int(config.d_ff)

    embeddings = config.vocab_size * d_model
    per_block = (
        d_model * d_model
        + 2 * d_model * kv_width
        + d_model * d_model
        + 3 * d_model * d_ff
        + 2 * d_model
    )
    if config.bias:
        per_block += 3 * d_model + 2 * kv_width + 2 * d_ff
    final_norm = d_model
    return embeddings + config.n_layers * per_block + final_norm
