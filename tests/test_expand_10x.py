from dataclasses import replace

import torch

from ronin.config import ModelConfig
from ronin.models.transformer import RoninLM
from scripts.expand_and_train_10x import widen_swiglu


def test_swiglu_widening_preserves_logits_before_training() -> None:
    torch.manual_seed(7)
    base_config = ModelConfig(
        vocab_size=256, context_length=32, n_layers=2, n_heads=4,
        d_model=32, d_ff=64,
    )
    expanded_config = replace(base_config, d_ff=96)
    base = RoninLM(base_config).eval()
    expanded = RoninLM(expanded_config).eval()
    expanded.load_state_dict(widen_swiglu(base.state_dict(), expanded.state_dict()), strict=True)
    tokens = torch.tensor([[1, 3, 5, 7, 11, 13]], dtype=torch.long)
    with torch.no_grad():
        base_logits, _ = base(tokens)
        expanded_logits, _ = expanded(tokens)
    torch.testing.assert_close(expanded_logits, base_logits, rtol=1e-5, atol=1e-6)


def test_widening_rejects_non_swiglu_shape_changes() -> None:
    torch.manual_seed(11)
    config = ModelConfig(
        vocab_size=256, context_length=32, n_layers=1, n_heads=2,
        d_model=16, d_ff=32,
    )
    base = RoninLM(config)
    changed = dict(base.state_dict())
    changed["final_norm.weight"] = torch.zeros(17)
    target = dict(base.state_dict())
    target["final_norm.weight"] = torch.zeros(17)
    try:
        widen_swiglu(changed, target)
    except ValueError as error:
        assert "Unexpected shape change outside SwiGLU" in str(error)
    else:
        raise AssertionError("Expected incompatible non-SwiGLU shape to be rejected")
