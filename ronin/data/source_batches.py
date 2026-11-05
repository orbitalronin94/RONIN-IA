"""Deterministic source-aware next-token batches for corpus replay."""
from __future__ import annotations

from collections.abc import Iterator, Sequence
import torch

class SourceBalancedBatches:
    """Sample each row from a source chosen by fixed probabilities."""
    def __init__(self, sources: Sequence[tuple[str, torch.Tensor, float]], batch_size: int, sequence_length: int, seed: int = 1337):
        if not sources or batch_size < 1 or sequence_length < 1:
            raise ValueError("sources, batch_size and sequence_length must be valid")
        names, tokens, weights = [], [], []
        for name, tensor, weight in sources:
            if tensor.ndim != 1 or tensor.numel() < sequence_length + 1:
                raise ValueError(f"source {name} is too short for the requested context")
            if weight < 0:
                raise ValueError("source weights cannot be negative")
            names.append(name); tokens.append(tensor); weights.append(float(weight))
        if sum(weights) <= 0:
            raise ValueError("at least one source weight must be positive")
        self.names, self.tokens = names, tokens
        self.probabilities = torch.tensor(weights, dtype=torch.double)
        self.probabilities /= self.probabilities.sum()
        self.batch_size, self.sequence_length = batch_size, sequence_length
        self.generator = torch.Generator(device="cpu").manual_seed(seed)
        self.offsets = torch.arange(sequence_length)
        self.max_starts = [t.numel() - sequence_length for t in tokens]
        self.source_counts = [0 for _ in tokens]

    def __iter__(self) -> Iterator[tuple[torch.Tensor, torch.Tensor]]:
        while True:
            choices = torch.multinomial(self.probabilities, self.batch_size, replacement=True, generator=self.generator)
            x = torch.empty((self.batch_size, self.sequence_length), dtype=torch.long)
            y = torch.empty_like(x)
            for source_index, tokens in enumerate(self.tokens):
                rows = torch.nonzero(choices == source_index, as_tuple=False).flatten()
                if rows.numel() == 0:
                    continue
                starts = torch.randint(0, self.max_starts[source_index], (rows.numel(),), generator=self.generator)
                indices = starts.unsqueeze(1) + self.offsets.unsqueeze(0)
                x[rows] = tokens[indices]
                y[rows] = tokens[indices + 1]
                self.source_counts[source_index] += int(rows.numel())
            yield x, y

    def sampling_report(self) -> dict[str, object]:
        total = sum(self.source_counts)
        return {"sources": [{"name": name, "target_probability": float(self.probabilities[i]), "sampled_windows": self.source_counts[i], "observed_probability": self.source_counts[i] / total if total else 0.0} for i, name in enumerate(self.names)], "total_windows": total}
