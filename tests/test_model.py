import torch

from ronin.config import ModelConfig
from ronin.models.transformer import RoninLM, apply_rope


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


def test_rope_preserves_shape_and_is_differentiable():
    x = torch.randn(2, 4, 7, 8, requires_grad=True)
    result = apply_rope(x, theta=10_000.0)
    assert result.shape == x.shape
    result.square().mean().backward()
    assert x.grad is not None
    assert torch.isfinite(x.grad).all()


def test_grouped_query_attention_forward_and_backward():
    config = ModelConfig(
        vocab_size=48,
        context_length=12,
        n_layers=1,
        n_heads=4,
        n_kv_heads=2,
        d_model=32,
    )
    model = RoninLM(config)
    tokens = torch.randint(0, config.vocab_size, (2, 7))
    logits, loss = model(tokens, tokens)
    assert logits.shape == (2, 7, config.vocab_size)
    assert loss is not None
    loss.backward()
    assert model.blocks[0].attention.k_proj.weight.grad is not None
    assert torch.isfinite(model.blocks[0].attention.k_proj.weight.grad).all()


def test_swiglu_and_rmsnorm_gradients_are_finite():
    config = ModelConfig(vocab_size=32, context_length=8, n_layers=1, n_heads=2, d_model=8)
    model = RoninLM(config)
    tokens = torch.randint(0, config.vocab_size, (2, 6))
    _, loss = model(tokens, tokens)
    loss.backward()
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    assert grads
    assert all(torch.isfinite(grad).all() for grad in grads)


def test_causal_attention_does_not_leak_future_tokens():
    config = ModelConfig(vocab_size=32, context_length=8, n_layers=2, n_heads=2, d_model=8)
    model = RoninLM(config).eval()
    first = torch.tensor([[1, 2, 3, 4, 5]])
    changed_future = torch.tensor([[1, 2, 3, 4, 9]])
    with torch.no_grad():
        logits_a, _ = model(first)
        logits_b, _ = model(changed_future)
    torch.testing.assert_close(logits_a[:, :4], logits_b[:, :4], rtol=0, atol=1e-6)
