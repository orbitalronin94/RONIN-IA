import torch

from ronin.config import ModelConfig
from ronin.models.transformer import RoninLM
from ronin.training.checkpoint import load_checkpoint


def test_loading_for_evaluation_does_not_require_training_sampler(tmp_path):
    config = ModelConfig(vocab_size=16, context_length=8, n_layers=1, n_heads=2, d_model=8)
    model = RoninLM(config)
    generator = torch.Generator().manual_seed(7)
    checkpoint = tmp_path / "evaluation.pt"
    torch.save(
        {
            "model": model.state_dict(),
            "step": 3,
            "batch_generator_state": generator.get_state(),
        },
        checkpoint,
    )

    restored = RoninLM(config)
    step = load_checkpoint(checkpoint, restored, restore_rng=False)

    assert step == 3
    for expected, actual in zip(model.parameters(), restored.parameters(), strict=True):
        assert torch.equal(expected, actual)
