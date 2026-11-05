import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM


def test_identity_gated_ninth_layer_starts_functionally_identical():
    base_config, _ = get_profile("tiny")
    expanded_config = type(base_config)(
        **{
            **base_config.__dict__,
            "n_layers": base_config.n_layers + 1,
            "identity_last_layer": True,
        }
    )
    torch.manual_seed(17)
    base = RoninLM(base_config).eval()
    expanded = RoninLM(expanded_config).eval()
    incompatible = expanded.load_state_dict(base.state_dict(), strict=False)
    expected_missing = {
        key for key in expanded.state_dict()
        if key.startswith(f"blocks.{base_config.n_layers}.") or key == "extra_layer_scale"
    }
    assert set(incompatible.missing_keys) == expected_missing
    assert incompatible.unexpected_keys == []
    with torch.no_grad():
        expanded.extra_layer_scale.zero_()
    tokens = torch.randint(0, base_config.vocab_size, (2, 24))
    with torch.no_grad():
        base_logits, _ = base(tokens)
        expanded_logits, _ = expanded(tokens)
    torch.testing.assert_close(expanded_logits, base_logits, rtol=0, atol=1e-6)


def test_identity_gate_receives_gradient():
    config, _ = get_profile("tiny")
    config = type(config)(
        **{
            **config.__dict__,
            "n_layers": config.n_layers + 1,
            "identity_last_layer": True,
        }
    )
    model = RoninLM(config)
    tokens = torch.randint(0, config.vocab_size, (2, 16))
    _, loss = model(tokens, tokens)
    assert loss is not None
    loss.backward()
    assert model.extra_layer_scale.grad is not None
    assert torch.isfinite(model.extra_layer_scale.grad)
    assert model.extra_layer_scale.grad.abs().item() > 0

def test_ninth_layer_parameter_budget_is_explicit():
    base_config, _ = get_profile("tiny")
    expanded_config = type(base_config)(
        **{
            **base_config.__dict__,
            "n_layers": base_config.n_layers + 1,
            "identity_last_layer": True,
        }
    )
    base = RoninLM(base_config)
    expanded = RoninLM(expanded_config)
    assert base.parameter_count == 9_922_880
    # Includes the scalar residual gate in addition to the new Transformer block.
    assert expanded.parameter_count == 11_152_961
