import json

import torch

from ronin.config import ModelConfig, TrainingConfig
from ronin.data.batches import NextTokenBatches
from ronin.models.transformer import RoninLM
from ronin.training.loop import train


def test_two_step_cpu_training_and_checkpoint(tmp_path):
    model_config = ModelConfig(vocab_size=16, context_length=8, n_layers=1, n_heads=2, d_model=8)
    training_config = TrainingConfig(
        batch_size=2, max_steps=2, warmup_steps=1, checkpoint_every=1, precision="fp32"
    )
    model = RoninLM(model_config)
    tokens = torch.randint(0, 16, (128,))
    batches = NextTokenBatches(tokens, 2, 8, seed=1)
    metrics_path = tmp_path / "training-metrics.json"
    losses = train(
        model,
        batches,
        training_config,
        device="cpu",
        checkpoint_dir=tmp_path,
        metrics_path=metrics_path,
    )
    assert len(losses) == 2
    assert all(torch.isfinite(torch.tensor(loss)) for loss in losses)
    assert (tmp_path / "step-00000001.pt").exists()
    assert (tmp_path / "step-00000002.pt").exists()
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert metrics["steps_completed"] == 2
    assert metrics["tokens_processed"] == 2 * 2 * 8
    assert metrics["tokens_per_second"] > 0
    assert metrics["checkpoint_seconds_total"] >= 0


def test_resume_restores_checkpoint_and_sampler_state(tmp_path):
    model_config = ModelConfig(vocab_size=16, context_length=8, n_layers=1, n_heads=2, d_model=8)
    training_config = TrainingConfig(
        batch_size=2, max_steps=2, warmup_steps=1, checkpoint_every=1, precision="fp32"
    )
    tokens = torch.randint(0, 16, (128,))
    first_model = RoninLM(model_config)
    train(
        first_model,
        NextTokenBatches(tokens, 2, 8, seed=1),
        training_config,
        device="cpu",
        checkpoint_dir=tmp_path,
    )
    resumed_model = RoninLM(model_config)
    resumed_losses = train(
        resumed_model,
        NextTokenBatches(tokens, 2, 8, seed=1),
        training_config,
        device="cpu",
        checkpoint_dir=tmp_path,
        resume_from=tmp_path / "step-00000001.pt",
    )
    assert len(resumed_losses) == 1
    assert all(torch.isfinite(torch.tensor(loss)) for loss in resumed_losses)


def test_vectorized_batches_preserve_sampler_values():
    tokens = torch.arange(64, dtype=torch.long)
    batches = iter(NextTokenBatches(tokens, 3, 7, seed=42))
    reference_generator = torch.Generator(device="cpu").manual_seed(42)
    offsets = torch.arange(7)
    max_start = tokens.numel() - 7 - 1
    for _ in range(4):
        inputs, targets = next(batches)
        starts = torch.randint(0, max_start + 1, (3,), generator=reference_generator)
        expected_inputs = torch.stack([tokens[i : i + 7] for i in starts.tolist()])
        expected_targets = torch.stack([tokens[i + 1 : i + 8] for i in starts.tolist()])
        assert torch.equal(inputs, expected_inputs)
        assert torch.equal(targets, expected_targets)
        assert torch.equal(inputs[:, 1:], targets[:, :-1])
        assert offsets.numel() == 7
