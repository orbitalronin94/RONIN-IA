"""Validated model and training configuration profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

ProfileName = Literal["tiny", "seed-0", "seed-1", "seed-2"]


@dataclass(frozen=True)
class ModelConfig:
    vocab_size: int = 16_384
    context_length: int = 512
    n_layers: int = 4
    n_heads: int = 4
    d_model: int = 256
    dropout: float = 0.0
    bias: bool = False

    def validate(self) -> None:
        if self.vocab_size < 2:
            raise ValueError("vocab_size must be >= 2")
        if self.context_length < 1:
            raise ValueError("context_length must be positive")
        if self.n_layers < 1 or self.n_heads < 1 or self.d_model < 1:
            raise ValueError("layers, heads and model width must be positive")
        if self.d_model % self.n_heads:
            raise ValueError("d_model must be divisible by n_heads")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")


@dataclass(frozen=True)
class TrainingConfig:
    batch_size: int = 8
    gradient_accumulation_steps: int = 1
    learning_rate: float = 3e-4
    min_learning_rate: float = 3e-5
    weight_decay: float = 0.1
    warmup_steps: int = 100
    max_steps: int = 1_000
    grad_clip_norm: float = 1.0
    seed: int = 1337
    precision: Literal["auto", "fp32", "bf16", "fp16"] = "auto"
    checkpoint_every: int = 250

    def validate(self) -> None:
        if self.batch_size < 1 or self.gradient_accumulation_steps < 1:
            raise ValueError("batch size and gradient accumulation must be positive")
        if self.learning_rate <= 0 or self.min_learning_rate < 0:
            raise ValueError("learning rates must be non-negative and max LR positive")
        if self.min_learning_rate > self.learning_rate:
            raise ValueError("min_learning_rate cannot exceed learning_rate")
        if self.weight_decay < 0 or self.warmup_steps < 0 or self.max_steps < 1:
            raise ValueError("invalid optimizer or schedule settings")
        if self.grad_clip_norm <= 0 or self.checkpoint_every < 1:
            raise ValueError("grad_clip_norm and checkpoint_every must be positive")


# Parameter targets are approximate and are verified by the ronin count-params CLI.
# The tokenizer vocabulary is part of the architecture, so it affects counts.
PROFILES: dict[str, tuple[ModelConfig, TrainingConfig]] = {
    "tiny": (
        ModelConfig(vocab_size=256, context_length=128, n_layers=8, n_heads=8, d_model=320),
        TrainingConfig(batch_size=2, max_steps=100, warmup_steps=10, checkpoint_every=50),
    ),
    "seed-0": (
        ModelConfig(vocab_size=16_384, context_length=1_024, n_layers=19, n_heads=12, d_model=768),
        TrainingConfig(batch_size=1, gradient_accumulation_steps=16, max_steps=10_000),
    ),
    "seed-1": (
        ModelConfig(vocab_size=32_000, context_length=2_048, n_layers=32, n_heads=24, d_model=1_536),
        TrainingConfig(batch_size=1, gradient_accumulation_steps=64, max_steps=100_000),
    ),
    "seed-2": (
        ModelConfig(vocab_size=32_000, context_length=4_096, n_layers=34, n_heads=32, d_model=4_096),
        TrainingConfig(batch_size=1, gradient_accumulation_steps=128, max_steps=300_000),
    ),
}


def get_profile(name: ProfileName | str) -> tuple[ModelConfig, TrainingConfig]:
    """Return a validated immutable profile pair."""
    try:
        model, training = PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Unknown profile {name!r}; choose from {', '.join(PROFILES)}") from exc
    model.validate()
    training.validate()
    return model, training


def profile_dict(name: ProfileName | str) -> dict[str, dict[str, object]]:
    model, training = get_profile(name)
    return {"model": asdict(model), "training": asdict(training)}
