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
    batches = NextTokenBatches(torch.randint(0, 16, (128,)), 2, 8, seed=1)
    losses = train(model, batches, training_config, device="cpu", checkpoint_dir=tmp_path)
    assert len(losses) == 2
    assert all(torch.isfinite(torch.tensor(loss)) for loss in losses)
    assert (tmp_path / "step-00000001.pt").exists()
    assert (tmp_path / "step-00000002.pt").exists()
