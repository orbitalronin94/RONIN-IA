import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANDIDATES = {
    "qwen3_base": "Qwen/Qwen3-0.6B",
    "instruction": "andresnowak/Qwen3-0.6B-instruction-finetuned_v2",
    "coding": "rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1",
    "luth": "kurakurai/Luth-0.6B-Instruct",
}
BASE_KEYS = (
    "model_type", "architectures", "hidden_size", "intermediate_size",
    "num_hidden_layers", "num_attention_heads", "num_key_value_heads",
    "head_dim", "vocab_size", "tie_word_embeddings",
)
TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt")
WEIGHT_SUFFIXES = (".safetensors", ".bin", ".pt", ".pth")
ADAPTER_MARKERS = ("adapter_model.", "adapter_config.", "lora", "gguf")


def is_full_weight_file(name):
    lower = name.lower()
    return lower.endswith(WEIGHT_SUFFIXES) and not any(marker in lower for marker in ADAPTER_MARKERS)


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "RONIN-IA-fusion-audit/1.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def audit(repo):
    result = {"repo": repo, "url": f"https://huggingface.co/{repo}", "errors": [], "warnings": []}
    try:
        info = get_json(f"https://huggingface.co/api/models/{repo}")
        files = {item.get("rfilename", "") for item in info.get("siblings", [])}
        result["revision"] = info.get("sha")
        result["license"] = (info.get("cardData") or {}).get("license")
        result["pipeline_tag"] = info.get("pipeline_tag")
        result["base_model_metadata"] = (info.get("cardData") or {}).get("base_model")
        result["full_weight_files"] = sorted(name for name in files if is_full_weight_file(name))
        result["has_full_weight_file"] = bool(result["full_weight_files"])
        result["adapter_files"] = sorted(name for name in files if any(marker in name.lower() for marker in ADAPTER_MARKERS))
        result["tokenizer_files"] = sorted(name for name in files if Path(name).name in TOKENIZER_FILES)
        result["file_count"] = len(files)
        try:
            config = get_json(f"https://huggingface.co/{repo}/resolve/{result['revision']}/config.json")
            result["config"] = {key: config.get(key) for key in BASE_KEYS if key in config}
        except Exception as exc:
            result["errors"].append(f"No se pudo leer config.json: {exc}")
        if not result["license"]:
            result["warnings"].append("Licencia no declarada en cardData; verificar manualmente.")
        if not result["has_full_weight_file"]:
            result["errors"].append("No se detectó un archivo de pesos completo; repositorios solo-adaptador/GGUF no sirven para esta evaluación directa.")
        if not result["tokenizer_files"]:
            result["errors"].append("No se detectaron archivos de tokenizer esperados.")
    except Exception as exc:
        result["errors"].append(f"Error consultando Hugging Face API: {exc}")
    return result


def main():
    reports = [audit(repo) for repo in CANDIDATES.values()]
    base = next((item for item in reports if item["repo"] == CANDIDATES["qwen3_base"]), {})
    base_config = base.get("config") or {}
    for item in reports:
        if item["repo"] == CANDIDATES["qwen3_base"]:
            item["compatibility_with_base"] = "reference"
            continue
        config = item.get("config") or {}
        mismatches = {key: {"base": base_config.get(key), "candidate": config.get(key)}
                      for key in BASE_KEYS if key in base_config and key in config and base_config[key] != config[key]}
        missing = [key for key in BASE_KEYS if key in base_config and key not in config]
        item["config_mismatches"] = mismatches
        item["config_fields_missing"] = missing
        if mismatches:
            item["errors"].append("La configuración difiere de la base; no fusionar sin análisis específico.")
        if missing:
            item["warnings"].append("Faltan campos de configuración para comparar: " + ", ".join(missing))
        item["compatibility_with_base"] = "config-compatible; tensor/tokenizer checks still required" if not mismatches and not missing and not item["errors"] else "not approved"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Metadata screening only; this does not perform or authorize a weight merge.",
        "base_repo": CANDIDATES["qwen3_base"],
        "candidates": reports,
        "decision": "NO MERGE until tensor names/shapes, tokenizer IDs, license terms, and behavior are verified.",
    }
    out = Path("fusion-audit-report.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nInforme guardado en {out}")
    return 1 if any(item.get("errors") for item in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
