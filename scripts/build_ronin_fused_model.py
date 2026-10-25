#!/usr/bin/env python3
"""Create a reproducible experimental Qwen3-0.6B parameter merge.

This is a derived checkpoint, not a newly trained foundation model. The merge is
strictly gated on tokenizer equality and identical state-dict keys/shapes.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

BASE = "Qwen/Qwen3-0.6B"
CODER = "rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", default="ronin-fused-model")
    p.add_argument("--base-weight", type=float, default=0.75)
    p.add_argument("--coder-weight", type=float, default=0.25)
    args = p.parse_args()
    if abs(args.base_weight + args.coder_weight - 1.0) > 1e-8:
        p.error("Los pesos deben sumar 1.0")
    if not (0 < args.base_weight < 1 and 0 < args.coder_weight < 1):
        p.error("Esta prueba requiere una mezcla no trivial de ambos checkpoints")

    import torch
    from huggingface_hub import model_info
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    print(f"Base: {BASE}", flush=True)
    base_info = model_info(BASE)
    coder_info = model_info(CODER)
    base_license = str((getattr(base_info, "card_data", None) or {}).get("license") or "").lower()
    coder_license = str((getattr(coder_info, "card_data", None) or {}).get("license") or "").lower()
    if base_license not in {"apache-2.0"} or coder_license not in {"apache-2.0"}:
        raise RuntimeError(f"Licencias no verificadas para distribución: base={base_license!r}, coder={coder_license!r}")

    base_tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=False)
    coder_tok = AutoTokenizer.from_pretrained(CODER, trust_remote_code=False)
    base_vocab, coder_vocab = base_tok.get_vocab(), coder_tok.get_vocab()
    if base_vocab != coder_vocab:
        raise RuntimeError("Tokenizadores incompatibles: los vocabularios o los IDs difieren")

    # Keep the base checkpoint as the model object; load one source at a time
    # to cap peak memory on standard GitHub-hosted CPU runners.
    base = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.float32, low_cpu_mem_usage=True, trust_remote_code=False
    )
    base.eval()
    base_state = base.state_dict()
    print(f"Cargando candidato: {CODER}", flush=True)
    coder = AutoModelForCausalLM.from_pretrained(
        CODER, torch_dtype=torch.float32, low_cpu_mem_usage=True, trust_remote_code=False
    )
    coder.eval()
    coder_state = coder.state_dict()
    missing = sorted(set(base_state) - set(coder_state))
    extra = sorted(set(coder_state) - set(base_state))
    mismatches = [k for k in set(base_state) & set(coder_state) if base_state[k].shape != coder_state[k].shape]
    if missing or extra or mismatches:
        raise RuntimeError(f"Tensores incompatibles: missing={missing[:8]}, extra={extra[:8]}, shape={mismatches[:8]}")
    for key, tensor in base_state.items():
        other = coder_state[key]
        if tensor.is_floating_point():
            tensor.mul_(args.base_weight).add_(other, alpha=args.coder_weight)
        elif not torch.equal(tensor, other):
            raise RuntimeError(f"Tensor no flotante incompatible: {key}")
    del coder_state, coder
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    base.save_pretrained(out, safe_serialization=True, max_shard_size="2GB")
    base_tok.save_pretrained(out)
    report = {
        "name": "RONIN-IA Experimental Fusion 0.1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_model": BASE,
        "base_revision": base_info.sha,
        "specialist_model": CODER,
        "specialist_revision": coder_info.sha,
        "method": "strict weighted parameter average",
        "weights": {"base": args.base_weight, "coding_specialist": args.coder_weight},
        "license": {"base": base_license, "specialist": coder_license},
        "tokenizer_vocab_entries": len(base_vocab),
        "tensor_count": len(base_state),
        "quality_improvement_proven": False,
        "status": "EXPERIMENTAL — benchmark and runtime conversion required before replacing the app model",
    }
    (out / "ronin-fusion-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)

if __name__ == "__main__":
    main()
