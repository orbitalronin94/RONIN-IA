#!/usr/bin/env python3
"""Discover and screen 20 backup Qwen3-0.6B fusion candidates from Hugging Face.

This is a metadata-only discovery stage. It does not download weights, inspect
tensor shapes/tokenizer IDs, approve licenses, benchmark behavior, or merge models.
Run: python scripts/audit_fusion_backup_candidates.py
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_MODEL = "Qwen/Qwen3-0.6B"
TARGET_COUNT = 20
SEARCH_TERMS = ("Qwen3-0.6B", "Qwen3 0.6B")
API = "https://huggingface.co/api/models"
BASE_KEYS = (
    "model_type", "architectures", "hidden_size", "intermediate_size",
    "num_hidden_layers", "num_attention_heads", "num_key_value_heads",
    "head_dim", "vocab_size", "tie_word_embeddings",
)
TOKENIZER_FILES = {"tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"}
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt", ".pth")
EXCLUDED_REPOS = {
    BASE_MODEL.lower(),
    "andresnowak/qwen3-0.6b-instruction-finetuned_v2",
    "rohitnagareddy/qwen3-0.6b-coding-finetuned-v1",
    "kurakurai/luth-0.6b-instruct",
    "suayptalha/qwen3-0.6b-math-expert",
    "suayptalha/qwen3-0.6b-code-expert",
    "suayptalha/qwen3-0.6b-if-expert",
    "suayptalha/qwen3-0.6b-medical-expert",
    "rohitnagareddy/qwen3-0.6b-medical-finetuned-v1",
    "x32/qwen3-0.6b-grpo-gsm8k-think",
    "huihui-ai/huihui-qwen3-0.6b-abliterated-v2",
    "lunahr/qwen3-0.6b-abliterated",
    "codelion/qwen3-0.6b-pts-dpo",
    "jeehwon/qwen3-0.6b-distill",
    "jeehwon/qwen3-0.6b-distill_001",
    "rexhaif/qwen3-0.6b-mteval-sft",
    "rd211/qwen3-0.6b-instruct",
    "flare0p/qwen3-agentic-coder-0.6b",
    "maheshnagabhairava/best-security-practices-model",
    "moxstone/smalillm-qwen3-0.6b-finetuned",
    "cytoe/qwen_finetuned",
    "ya-yje-krasni/qwen3-0.6b-russian-dialogues",
    "tuandunghcmut/qwen3-ft-customer-dataset",
    "ontario/qwen3-0.6b-awesome-prompts",
}


def get_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "RONIN-IA-backup-fusion-audit/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def discover_repositories():
    """Search HF and rank candidates by downloads, while excluding known candidates."""
    found = {}
    for term in SEARCH_TERMS:
        params = urllib.parse.urlencode({
            "search": term, "limit": 100, "sort": "downloads", "direction": "-1"
        })
        for item in get_json(f"{API}?{params}"):
            repo = item.get("id")
            if not repo or repo.lower() in EXCLUDED_REPOS:
                continue
            # Prefer exact family/name matches to reduce unrelated results.
            name = repo.rsplit("/", 1)[-1].lower()
            if "qwen3" not in name or "0.6b" not in name:
                continue
            found[repo] = item
    ordered = sorted(
        found.values(),
        key=lambda item: (item.get("downloads", 0), item.get("likes", 0)),
        reverse=True,
    )
    return ordered[:TARGET_COUNT]


def audit_candidate(item, base_config):
    repo = item["id"]
    result = {
        "repo": repo,
        "url": f"https://huggingface.co/{repo}",
        "downloads_at_discovery": item.get("downloads"),
        "likes_at_discovery": item.get("likes"),
        "errors": [],
        "warnings": [],
    }
    try:
        info = get_json(f"{API}/{repo}")
        revision = info.get("sha")
        result["revision"] = revision
        result["license"] = (info.get("cardData") or {}).get("license")
        result["base_model_metadata"] = (info.get("cardData") or {}).get("base_model")
        siblings = info.get("siblings", [])
        files = {entry.get("rfilename", "") for entry in siblings}
        result["weight_files"] = sorted(
            name for name in files
            if name.lower().endswith(WEIGHT_SUFFIXES)
            and not any(marker in name.lower() for marker in
                        ("adapter_model.", "adapter_config.", "lora", "gguf"))
            and Path(name).name not in {
                "optimizer.pt", "optimizer.bin", "rng_state.pth",
                "scaler.pt", "scheduler.pt", "training_args.bin",
            }
        )
        result["has_full_weight_file"] = bool(result["weight_files"])
        result["tokenizer_files"] = sorted(
            name for name in files if Path(name).name in TOKENIZER_FILES
        )
        if revision:
            try:
                cfg = get_json(f"https://huggingface.co/{repo}/resolve/{revision}/config.json")
                result["config"] = {key: cfg.get(key) for key in BASE_KEYS if key in cfg}
            except Exception as exc:
                result["errors"].append(f"No se pudo leer config.json: {exc}")
        else:
            result["errors"].append("Hugging Face no devolvió una revisión identificable.")
        if not result["license"]:
            result["warnings"].append("Licencia no declarada en cardData; comprobar manualmente.")
        if not result["has_full_weight_file"]:
            result["warnings"].append("No se detectaron pesos completos estándar; puede ser un adaptador o formato no compatible.")
        if not result["tokenizer_files"]:
            result["warnings"].append("No se detectaron archivos de tokenizer habituales.")
        cfg = result.get("config", {})
        mismatches = {
            key: {"base": base_config[key], "candidate": cfg[key]}
            for key in BASE_KEYS
            if key in base_config and key in cfg and base_config[key] != cfg[key]
        }
        result["config_mismatches"] = mismatches
        result["compatibility_status"] = (
            "config-compatible; requires tensor/tokenizer/license/behavior checks"
            if cfg and not mismatches and result["has_full_weight_file"]
            else "not approved; manual review required"
        )
    except Exception as exc:
        result["errors"].append(f"Error consultando Hugging Face: {exc}")
        result["compatibility_status"] = "audit failed"
    return result


def main():
    base_info = get_json(f"{API}/{BASE_MODEL}")
    base_revision = base_info.get("sha")
    base_cfg = get_json(f"https://huggingface.co/{BASE_MODEL}/resolve/{base_revision}/config.json")
    base_config = {key: base_cfg.get(key) for key in BASE_KEYS if key in base_cfg}
    discovered = discover_repositories()
    candidates = [audit_candidate(item, base_config) for item in discovered]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Backup candidate discovery and metadata screening only; no merge is performed or approved.",
        "base_model": BASE_MODEL,
        "target_count": TARGET_COUNT,
        "discovered_count": len(candidates),
        "search_terms": list(SEARCH_TERMS),
        "selection": "Hugging Face search results ranked by downloads/likes; known primary candidates excluded.",
        "candidates": candidates,
        "limitations": [
            "Search results and download counts change over time; revisions are recorded when available.",
            "Matching config fields is not proof of tensor-shape or tokenizer-ID compatibility.",
            "Verify model license and upstream license terms before reuse.",
            "Do not merge candidates marked not approved; run tensor, tokenizer, and behavioral checks first.",
        ],
    }
    output = Path("fusion-backup-candidates-report.json")
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nInforme guardado en {output}")
    if len(candidates) < TARGET_COUNT:
        print(f"AVISO: se encontraron {len(candidates)} candidatos, menos de los {TARGET_COUNT} solicitados.")
    return 0 if base_config else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"Error fatal en auditoría de candidatos de respaldo: {exc}", file=sys.stderr)
        sys.exit(1)
