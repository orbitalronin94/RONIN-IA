import math

import torch

from ronin.config import ModelConfig
from ronin.evaluation.metrics import bits_per_byte, perplexity
from ronin.inference.generate import generate
from ronin.models.transformer import RoninLM


def test_metric_helpers():
    assert math.isclose(perplexity(0.0), 1.0)
    assert bits_per_byte(math.log(2.0) * 10, 10) == 1.0


def test_generation_appends_requested_tokens_and_restores_mode():
    config = ModelConfig(vocab_size=32, context_length=8, n_layers=1, n_heads=2, d_model=8)
    model = RoninLM(config)
    model.train()
    prompt = torch.tensor([[1, 2, 3]])
    output = generate(model, prompt, max_new_tokens=2, top_k=4)
    assert output.shape == (1, 5)
    assert model.training
