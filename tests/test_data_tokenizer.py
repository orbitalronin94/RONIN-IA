import torch

from ronin.data.batches import NextTokenBatches
from ronin.tokenizer.byte import ByteTokenizer


def test_byte_tokenizer_round_trip():
    tokenizer = ByteTokenizer()
    text = "RONIN — modelo desde cero"
    assert tokenizer.decode(tokenizer.encode(text)) == text


def test_next_token_batch_alignment_and_reproducibility():
    tokens = torch.arange(100)
    a = next(iter(NextTokenBatches(tokens, batch_size=3, sequence_length=8, seed=9)))
    b = next(iter(NextTokenBatches(tokens, batch_size=3, sequence_length=8, seed=9)))
    x, y = a
    assert x.shape == (3, 8)
    assert torch.equal(y, x + 1)
    assert torch.equal(a[0], b[0])
