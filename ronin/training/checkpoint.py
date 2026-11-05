"""Checkpoint restore helpers for model and optimizer state."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import torch
from torch import nn


def load_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer | None = None,
    scaler: torch.cuda.amp.GradScaler | None = None,
    batch_generator: torch.Generator | None = None,
    map_location: str | torch.device = "cpu",
    restore_rng: bool = True,
    expected_config: dict[str, object] | None = None,
) -> int:
    """Restore a checkpoint and return the next training step to execute."""
    checkpoint = torch.load(path, map_location=map_location, weights_only=False)
    if not isinstance(checkpoint, dict):
        raise ValueError("checkpoint must be a state_dict or checkpoint mapping")
    if "model" in checkpoint:
        state_dict = checkpoint["model"]
        step = int(checkpoint.get("step", 0))
        if expected_config is not None and checkpoint.get("training_config") != expected_config:
            raise ValueError("resume configuration differs from checkpoint training_config")
    else:
        state_dict = checkpoint
        step = 0  # compact weights keep provenance in weights/main-model.json
        if expected_config is not None:
            raise ValueError("compact state_dict has no training_config")
    if not isinstance(state_dict, dict) or not state_dict:
        raise ValueError("checkpoint has no model state_dict")
    if not all(isinstance(value, torch.Tensor) for value in state_dict.values()):
        raise ValueError("compact state_dict must contain only tensors")
    model.load_state_dict(state_dict, strict=True)
    if optimizer is not None:
        if "optimizer" not in checkpoint:
            raise ValueError("checkpoint has no optimizer state")
        optimizer.load_state_dict(checkpoint["optimizer"])
    if scaler is not None and checkpoint.get("scaler") is not None:
        scaler.load_state_dict(checkpoint["scaler"])
    if restore_rng:
        saved_batch_state = checkpoint.get("batch_generator_state")
        if saved_batch_state is not None and batch_generator is None:
            raise ValueError(
                "checkpoint contains sampler state but no compatible batch generator was supplied"
            )
        if batch_generator is not None and saved_batch_state is not None:
            batch_generator.set_state(saved_batch_state)
        if checkpoint.get("torch_rng_state") is not None:
            torch.set_rng_state(checkpoint["torch_rng_state"].cpu())
        if checkpoint.get("cuda_rng_state_all") is not None and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(checkpoint["cuda_rng_state_all"])
        if checkpoint.get("python_rng_state") is not None:
            random.setstate(checkpoint["python_rng_state"])
        if checkpoint.get("numpy_rng_state") is not None:
            np.random.set_state(checkpoint["numpy_rng_state"])
    return step
