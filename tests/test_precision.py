import pytest
import torch

from ronin.training.loop import resolve_precision


def test_auto_precision_uses_fp32_on_cpu():
    assert resolve_precision("auto", torch.device("cpu")) is None


def test_explicit_fp16_is_rejected_on_cpu():
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_precision("fp16", torch.device("cpu"))


def test_explicit_bf16_is_rejected_on_cpu():
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_precision("bf16", torch.device("cpu"))
