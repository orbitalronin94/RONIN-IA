"""Transformer causal PyTorch con RoPE, RMSNorm, SwiGLU y GQA."""

from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from ronin.config import ModelConfig


class RMSNorm(nn.Module):
    """Normalización RMS con un único vector de escala aprendido."""

    def __init__(self, width: int, eps: float) -> None:
        super().__init__()
        self.weight = nn.Parameter(torch.ones(width))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        scale = torch.rsqrt(x.float().pow(2).mean(dim=-1, keepdim=True) + self.eps)
        return (x * scale.to(dtype=x.dtype)) * self.weight


def apply_rope(x: torch.Tensor, theta: float) -> torch.Tensor:
    """Aplica RoPE a un tensor [batch, heads, sequence, head_dim]."""
    length = x.shape[-2]
    head_dim = x.shape[-1]
    if head_dim % 2:
        raise ValueError("head_dim debe ser par para aplicar RoPE")
    device = x.device
    inv_freq = 1.0 / (
        theta ** (torch.arange(0, head_dim, 2, device=device, dtype=torch.float32) / head_dim)
    )
    positions = torch.arange(length, device=device, dtype=torch.float32)
    angles = torch.outer(positions, inv_freq)
    cos = angles.cos().to(dtype=x.dtype)[None, None, :, :]
    sin = angles.sin().to(dtype=x.dtype)[None, None, :, :]
    even = x[..., 0::2]
    odd = x[..., 1::2]
    rotated = torch.stack((even * cos - odd * sin, even * sin + odd * cos), dim=-1)
    return rotated.flatten(-2)


class CausalSelfAttention(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.n_heads = config.n_heads
        self.n_kv_heads = int(config.n_kv_heads)
        self.head_dim = config.d_model // config.n_heads
        self.n_rep = self.n_heads // self.n_kv_heads
        self.rope_theta = config.rope_theta
        kv_width = self.n_kv_heads * self.head_dim
        self.q_proj = nn.Linear(config.d_model, config.d_model, bias=config.bias)
        self.k_proj = nn.Linear(config.d_model, kv_width, bias=config.bias)
        self.v_proj = nn.Linear(config.d_model, kv_width, bias=config.bias)
        self.out_proj = nn.Linear(config.d_model, config.d_model, bias=config.bias)
        self.dropout = config.dropout

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch, length, width = x.shape
        q = self.q_proj(x).view(batch, length, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(x).view(batch, length, self.n_kv_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(x).view(batch, length, self.n_kv_heads, self.head_dim).transpose(1, 2)
        q = apply_rope(q, self.rope_theta)
        k = apply_rope(k, self.rope_theta)
        if self.n_rep > 1:
            k = k.repeat_interleave(self.n_rep, dim=1)
            v = v.repeat_interleave(self.n_rep, dim=1)
        y = F.scaled_dot_product_attention(
            q,
            k,
            v,
            attn_mask=None,
            dropout_p=self.dropout if self.training else 0.0,
            is_causal=True,
        )
        y = y.transpose(1, 2).contiguous().view(batch, length, width)
        return self.out_proj(y)


class SwiGLU(nn.Module):
    """Red feed-forward SwiGLU: down(silu(gate(x)) * up(x))."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        hidden = int(config.d_ff)
        self.gate_proj = nn.Linear(config.d_model, hidden, bias=config.bias)
        self.up_proj = nn.Linear(config.d_model, hidden, bias=config.bias)
        self.down_proj = nn.Linear(hidden, config.d_model, bias=config.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down_proj(F.silu(self.gate_proj(x)) * self.up_proj(x))


class TransformerBlock(nn.Module):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        self.norm_1 = RMSNorm(config.d_model, config.rms_norm_eps)
        self.attention = CausalSelfAttention(config)
        self.norm_2 = RMSNorm(config.d_model, config.rms_norm_eps)
        self.mlp = SwiGLU(config)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attention(self.norm_1(x))
        return x + self.mlp(self.norm_2(x))


class RoninLM(nn.Module):
    """Decodificador causal. El constructor inicializa todos los pesos localmente."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__()
        config.validate()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.dropout = nn.Dropout(config.dropout)
        self.blocks = nn.ModuleList(
            [TransformerBlock(config) for _ in range(config.n_layers)]
        )
        self.extra_layer_scale = (
            nn.Parameter(torch.zeros(())) if config.identity_last_layer else None
        )
        self.final_norm = RMSNorm(config.d_model, config.rms_norm_eps)
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        self.apply(self._init_weights)
        self.lm_head.weight = self.token_embedding.weight

    @staticmethod
    def _init_weights(module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def _forward_hidden(self, input_ids: torch.Tensor) -> torch.Tensor:
        if input_ids.ndim != 2:
            raise ValueError("input_ids debe tener forma [batch, secuencia]")
        _, length = input_ids.shape
        if length < 1 or length > self.config.context_length:
            raise ValueError("la secuencia debe estar entre 1 y context_length")
        x = self.dropout(self.token_embedding(input_ids))
        for index, block in enumerate(self.blocks):
            if self.extra_layer_scale is not None and index == len(self.blocks) - 1:
                x = x + self.extra_layer_scale * (block(x) - x)
            else:
                x = block(x)
        return x

    def forward_last_logits(
        self, input_ids: torch.Tensor, last_positions: torch.Tensor
    ) -> torch.Tensor:
        """Calcula logits solo en la última posición válida de cada secuencia."""
        hidden = self._forward_hidden(input_ids)
        batch, length, _ = hidden.shape
        if last_positions.ndim != 1 or last_positions.numel() != batch:
            raise ValueError("last_positions debe tener forma [batch]")
        if last_positions.dtype != torch.long:
            raise ValueError("last_positions debe usar dtype torch.long")
        if torch.any(last_positions < 0) or torch.any(last_positions >= length):
            raise ValueError("last_positions contiene una posición fuera de secuencia")
        rows = torch.arange(batch, device=hidden.device)
        selected_hidden = hidden[rows, last_positions.to(hidden.device)]
        return self.lm_head(self.final_norm(selected_hidden))

    def forward(
        self, input_ids: torch.Tensor, targets: torch.Tensor | None = None
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        hidden = self._forward_hidden(input_ids)
        batch, length, _ = hidden.shape
        logits = self.lm_head(self.final_norm(hidden))
        loss = None
        if targets is not None:
            if targets.shape != input_ids.shape:
                raise ValueError("targets debe tener la misma forma que input_ids")
            loss = F.cross_entropy(logits.reshape(batch * length, -1), targets.reshape(-1))
        return logits, loss

    @property
    def parameter_count(self) -> int:
        return sum(
            parameter.numel()
            for parameter in self.parameters()
            if parameter.requires_grad
        )
