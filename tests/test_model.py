import torch

from ronin.config import ModelConfig
from ronin.models.transformer import RoninLM


def test_forward_and_loss_shapes():
    config = ModelConfig(vocab_size=32, context_length=16, n_layers=2, n_heads=4, d_model=32)
    model = RoninLM(config)
    tokens = torch.randint(0, config.vocab_size, (2, 8))
    logits, loss = model(tokens, tokens)
    assert logits.shape == (2, 8, config.vocab_size)
    assert loss is not None and torch.isfinite(loss)


def test_context_limit_is_enforced():
    config = ModelConfig(vocab_size=32, context_length=4, n_layers=1, n_heads=2, d_model=8)
    model = RoninLM(config)
    try:
        model(torch.zeros((1, 5), dtype=torch.long))
    except ValueError as exc:
        assert "context_length" in str(exc)
    else:
        raise AssertionError("overlong sequence should fail")


def test_embeddings_are_tied():
    config = ModelConfig(vocab_size=32, context_length=8, n_layers=1, n_heads=2, d_model=8)
    model = RoninLM(config)
    assert model.lm_head.weight.data_ptr() == model.token_embedding.weight.data_ptr()
