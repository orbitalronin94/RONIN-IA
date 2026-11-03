"""Configuraciones validadas de arquitectura y entrenamiento."""

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
    n_kv_heads: int | None = None
    d_ff: int | None = None
    rope_theta: float = 10_000.0
    rms_norm_eps: float = 1e-6

    def __post_init__(self) -> None:
        if self.n_kv_heads is None:
            object.__setattr__(self, "n_kv_heads", self.n_heads)
        if self.d_ff is None:
            object.__setattr__(self, "d_ff", (8 * self.d_model + 2) // 3)

    def validate(self) -> None:
        if self.vocab_size < 2:
            raise ValueError("vocab_size debe ser >= 2")
        if self.context_length < 1:
            raise ValueError("context_length debe ser positivo")
        if self.n_layers < 1 or self.n_heads < 1 or self.d_model < 1:
            raise ValueError("capas, cabezas y ancho del modelo deben ser positivos")
        if self.d_model % self.n_heads:
            raise ValueError("d_model debe ser divisible por n_heads")
        if self.n_kv_heads is None or self.n_kv_heads < 1:
            raise ValueError("n_kv_heads debe ser positivo")
        if self.n_heads % self.n_kv_heads:
            raise ValueError("n_heads debe ser divisible por n_kv_heads")
        if self.d_model // self.n_heads % 2:
            raise ValueError("la dimensión de cada cabeza debe ser par para RoPE")
        if self.d_ff is None or self.d_ff < 1:
            raise ValueError("d_ff debe ser positivo")
        if self.rope_theta <= 0 or self.rms_norm_eps <= 0:
            raise ValueError("rope_theta y rms_norm_eps deben ser positivos")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout debe estar en [0, 1)")


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
            raise ValueError("batch_size y gradient_accumulation_steps deben ser positivos")
        if self.learning_rate <= 0 or self.min_learning_rate < 0:
            raise ValueError("las tasas de aprendizaje deben ser válidas")
        if self.min_learning_rate > self.learning_rate:
            raise ValueError("min_learning_rate no puede superar learning_rate")
        if self.weight_decay < 0 or self.warmup_steps < 0 or self.max_steps < 1:
            raise ValueError("configuración de optimizador o planificador no válida")
        if self.grad_clip_norm <= 0 or self.checkpoint_every < 1:
            raise ValueError("grad_clip_norm y checkpoint_every deben ser positivos")


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
    """Devuelve el par validado e inmutable de un perfil."""
    try:
        model, training = PROFILES[name]
    except KeyError as exc:
        raise ValueError(f"Perfil desconocido {name!r}; elige entre {', '.join(PROFILES)}") from exc
    model.validate()
    training.validate()
    return model, training


def profile_dict(name: ProfileName | str) -> dict[str, dict[str, object]]:
    model, training = get_profile(name)
    return {"model": asdict(model), "training": asdict(training)}
