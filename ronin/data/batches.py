"""Text corpus loading and deterministic next-token batches."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import torch

from ronin.tokenizer.byte import ByteTokenizer


def encode_text_file(path: str | Path, tokenizer: ByteTokenizer | None = None) -> torch.Tensor:
    tokenizer = tokenizer or ByteTokenizer()
    text = Path(path).read_text(encoding="utf-8")
    ids = tokenizer.encode(text)
    if len(ids) < 2:
        raise ValueError("corpus must contain at least two tokens")
    return torch.tensor(ids, dtype=torch.long)


class NextTokenBatches:
    """Infinite deterministic random-window sampler over a 1-D token tensor."""

    def __init__(
        self, tokens: torch.Tensor, batch_size: int, sequence_length: int, seed: int = 1337
    ) -> None:
        if tokens.ndim != 1 or tokens.numel() < sequence_length + 1:
            raise ValueError("tokens must be 1-D and longer than sequence_length")
        if batch_size < 1 or sequence_length < 1:
            raise ValueError("batch_size and sequence_length must be positive")
        self.tokens = tokens
        self.batch_size = batch_size
        self.sequence_length = sequence_length
        self.generator = torch.Generator(device="cpu").manual_seed(seed)
        self.max_start = tokens.numel() - sequence_length - 1

    def __iter__(self) -> Iterator[tuple[torch.Tensor, torch.Tensor]]:
        while True:
            starts = torch.randint(
                0, self.max_start + 1, (self.batch_size,), generator=self.generator
            )
            # Indexación vectorizada: evita dos bucles Python y torch.stack por batch.
            # Conserva exactamente los mismos starts y, por tanto, la secuencia aleatoria.
            offsets = torch.arange(self.sequence_length)
            indices = starts.unsqueeze(1) + offsets.unsqueeze(0)
            x = self.tokens[indices]
            y = self.tokens[indices + 1]
            yield x, y
