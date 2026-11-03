"""Deterministic byte-level tokenizer baseline.

This is a transparent bootstrap tokenizer, not the final learned tokenizer.
It maps UTF-8 bytes to IDs 0..255 and reserves no external vocabulary.
"""

from __future__ import annotations


class ByteTokenizer:
    vocab_size = 256

    def encode(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))

    def decode(self, token_ids: list[int]) -> str:
        values = []
        for token_id in token_ids:
            if not 0 <= int(token_id) <= 255:
                raise ValueError(f"byte token out of range: {token_id}")
            values.append(int(token_id))
        return bytes(values).decode("utf-8", errors="replace")

    def to_dict(self) -> dict[str, object]:
        return {"type": "byte", "version": 1, "vocab_size": self.vocab_size}
