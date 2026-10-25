#!/usr/bin/env python3
"""Train a tiny character-level GPT-style model from random initialization.

This is a pipeline/proof-of-concept, not the 0.6B parameter Ronin model.
No pretrained weights or remote datasets are loaded.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import torch
from torch import nn


class TinyRoninGPT(nn.Module):
    def __init__(self, vocab_size: int, block_size: int, d_model: int, heads: int, layers: int):
        super().__init__()
        self.block_size = block_size
        self.token_embedding = nn.Embedding(vocab_size, d_model)
        self.position_embedding = nn.Embedding(block_size, d_model)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=heads,
            dim_feedforward=4 * d_model,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=layers, enable_nested_tensor=False)
        self.final_norm = nn.LayerNorm(d_model)
        self.lm_head = nn.Linear(d_model, vocab_size, bias=False)
        self.lm_head.weight = self.token_embedding.weight

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        batch, length = tokens.shape
        positions = torch.arange(length, device=tokens.device)
        x = self.token_embedding(tokens) + self.position_embedding(positions)[None, :, :]
        causal_mask = torch.triu(torch.ones(length, length, device=tokens.device, dtype=torch.bool), diagonal=1)
        x = self.transformer(x, mask=causal_mask)
        return self.lm_head(self.final_norm(x))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="experiments/ronin-from-scratch/corpus.txt")
    parser.add_argument("--output-dir", default="experiments/ronin-from-scratch/output")
    parser.add_argument("--steps", type=int, default=300, help="Target total optimizer steps; bounded to 1..1000")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--block-size", type=int, default=96)
    parser.add_argument("--d-model", type=int, default=128)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--layers", type=int, default=4)
    args = parser.parse_args()

    if not 1 <= args.steps <= 1000:
        raise SystemExit("--steps must be between 1 and 1000 for bounded CI runs")
    if args.d_model % args.heads:
        raise SystemExit("--d-model must be divisible by --heads")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    text = Path(args.data).read_text(encoding="utf-8")
    chars = sorted(set(text))
    if len(text) < args.block_size + 2 or len(chars) < 8:
        raise SystemExit("Training corpus is too small for the configured block size.")
    stoi = {char: i for i, char in enumerate(chars)}
    encoded = torch.tensor([stoi[c] for c in text], dtype=torch.long)
    split = max(args.block_size + 1, int(len(encoded) * 0.9))
    train_data, val_data = encoded[:split], encoded[split:]
    if len(val_data) < args.block_size + 1:
        val_data = train_data[-(args.block_size + 1):]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "latest.pt"
    config = {
        "model_name": "Ronin-FromScratch-Tiny-Exp-001",
        "initialization": "random",
        "pretrained_weights": False,
        "tokenization": "character",
        "vocab": chars,
        "block_size": args.block_size,
        "d_model": args.d_model,
        "heads": args.heads,
        "layers": args.layers,
        "parameter_count": None,
        "seed": args.seed,
    }
    model = TinyRoninGPT(len(chars), args.block_size, args.d_model, args.heads, args.layers).to(device)
    config["parameter_count"] = sum(p.numel() for p in model.parameters())
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    start_step = 0
    history: list[dict[str, float | int]] = []

    if args.resume and checkpoint_path.exists():
        saved = torch.load(checkpoint_path, map_location=device, weights_only=False)
        if saved.get("config") != config:
            raise SystemExit("Cached checkpoint configuration does not match current run; refusing unsafe resume.")
        model.load_state_dict(saved["model"])
        optimizer.load_state_dict(saved["optimizer"])
        start_step = int(saved.get("step", 0))
        history = saved.get("history", [])

    def batch(source: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        starts = torch.randint(0, len(source) - args.block_size - 1, (args.batch_size,))
        x = torch.stack([source[i:i + args.block_size] for i in starts]).to(device)
        y = torch.stack([source[i + 1:i + args.block_size + 1] for i in starts]).to(device)
        return x, y

    @torch.no_grad()
    def evaluate() -> tuple[float, float]:
        model.eval()
        losses = []
        for source in (train_data, val_data):
            x, y = batch(source)
            loss = nn.functional.cross_entropy(model(x).reshape(-1, len(chars)), y.reshape(-1))
            losses.append(float(loss.item()))
        model.train()
        return losses[0], losses[1]

    model.train()
    started = time.time()
    for step in range(start_step, args.steps):
        x, y = batch(train_data)
        logits = model(x)
        loss = nn.functional.cross_entropy(logits.reshape(-1, len(chars)), y.reshape(-1))
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        completed = step + 1
        if completed % 25 == 0 or completed == args.steps:
            train_loss, val_loss = evaluate()
            record = {"step": completed, "train_loss": train_loss, "val_loss": val_loss}
            history.append(record)
            print(json.dumps(record), flush=True)
            state = {
                "config": config,
                "model": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "step": completed,
                "history": history,
            }
            torch.save(state, checkpoint_path)

    if start_step >= args.steps:
        train_loss, val_loss = evaluate()
    else:
        train_loss, val_loss = evaluate()

    model.eval()
    with torch.no_grad():
        context = torch.tensor([[stoi.get(c, 0) for c in "Ronin:"]], dtype=torch.long, device=device)
        if context.shape[1] > args.block_size:
            context = context[:, -args.block_size:]
        generated = []
        for _ in range(240):
            logits = model(context[:, -args.block_size:])[:, -1, :]
            next_id = int(torch.argmax(logits, dim=-1).item())
            generated.append(chars[next_id])
            context = torch.cat([context, torch.tensor([[next_id]], device=device)], dim=1)

    state = {
        "config": config,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "step": max(start_step, args.steps),
        "history": history,
    }
    torch.save(state, checkpoint_path)
    metrics = {
        "experiment": "Ronin-FromScratch-Tiny-Exp-001",
        "training_mode": "random_initialization",
        "pretrained_weights_used": False,
        "dataset": str(args.data),
        "device": str(device),
        "seed": args.seed,
        "steps_completed": max(start_step, args.steps),
        "parameter_count": config["parameter_count"],
        "vocab_size": len(chars),
        "train_loss": train_loss,
        "validation_loss": val_loss,
        "perplexity_estimate": math.exp(min(val_loss, 20)),
        "elapsed_seconds_this_run": round(time.time() - started, 2),
        "note": "Tiny character-level pipeline demonstration; not a useful general-purpose model and not Ronin-0.6B.",
        "history": history,
        "sample": "Ronin:" + "".join(generated),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "sample.txt").write_text(metrics["sample"] + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in metrics.items() if k not in {"history", "sample"}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
