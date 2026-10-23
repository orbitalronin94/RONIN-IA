#!/usr/bin/env python3
"""Experimental equal-weight parameter averaging with strict compatibility gates.

This does not prove quality improvement. Run only after reviewing model licenses
and benchmark results. The output is local and is never published automatically.
"""
import argparse
import json
from pathlib import Path

MODELS = [
    ("base", "Qwen/Qwen3-0.6B"),
    ("instruction", "andresnowak/Qwen3-0.6B-instruction-finetuned_v2"),
    ("coding", "rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1"),
    ("luth", "kurakurai/Luth-0.6B-Instruct"),
]


def vocab_compatibility(reference, candidate):
    if reference != candidate:
        ref_keys, cand_keys = set(reference), set(candidate)
        shared = ref_keys & cand_keys
        mismatches = [t for t in shared if reference[t] != candidate[t]]
        return {
            "compatible": False,
            "base_only": len(ref_keys - cand_keys),
            "candidate_only": len(cand_keys - ref_keys),
            "shared_id_mismatches": len(mismatches),
        }
    return {"compatible": True, "base_only": 0, "candidate_only": 0, "shared_id_mismatches": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="ronin-fusion-experimental")
    parser.add_argument("--allow-unreviewed-licenses", action="store_true",
                        help="Explicitly acknowledge that license review is your responsibility.")
    args = parser.parse_args()
    if not args.allow_unreviewed_licenses:
        parser.error("Review all four model licenses first, then pass --allow-unreviewed-licenses to acknowledge that review.")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(max(1, min(4, __import__("os").cpu_count() or 1)))
    base_name, base_repo = MODELS[0]
    print(f"Loading reference model: {base_repo}", flush=True)
    merged_tokenizer = AutoTokenizer.from_pretrained(base_repo, trust_remote_code=False)
    reference_vocab = merged_tokenizer.get_vocab()
    merged = AutoModelForCausalLM.from_pretrained(
        base_repo, torch_dtype=torch.float32, low_cpu_mem_usage=True, trust_remote_code=False
    )
    merged.eval()
    report = {
        "method": "strict equal-weight parameter average (experimental)",
        "models": [repo for _, repo in MODELS],
        "license_review_acknowledged": True,
        "quality_improvement_proven": False,
        "checks": [],
        "decision": "NOT VALIDATED: run the Spanish benchmark and human review before use.",
    }
    reference_state = merged.state_dict()

    for count, (label, repo) in enumerate(MODELS[1:], start=2):
        print(f"Checking {label}: {repo}", flush=True)
        candidate_tokenizer = AutoTokenizer.from_pretrained(repo, trust_remote_code=False)
        vocab_check = vocab_compatibility(reference_vocab, candidate_tokenizer.get_vocab())
        if not vocab_check["compatible"]:
            raise RuntimeError(f"Tokenizer mismatch for {repo}: {vocab_check}")
        candidate = AutoModelForCausalLM.from_pretrained(
            repo, torch_dtype=torch.float32, low_cpu_mem_usage=True, trust_remote_code=False
        )
        try:
            candidate_state = candidate.state_dict()
            missing = sorted(set(reference_state) - set(candidate_state))
            extra = sorted(set(candidate_state) - set(reference_state))
            shape_mismatch = [
                key for key in set(reference_state) & set(candidate_state)
                if reference_state[key].shape != candidate_state[key].shape
            ]
            if missing or extra or shape_mismatch:
                raise RuntimeError(
                    f"Tensor mismatch for {repo}: missing={missing[:10]}, "
                    f"extra={extra[:10]}, shape_mismatch={shape_mismatch[:10]}"
                )
            nonfloating_mismatch = [
                key for key, ref_tensor in reference_state.items()
                if not ref_tensor.is_floating_point()
                and not torch.equal(ref_tensor, candidate_state[key])
            ]
            if nonfloating_mismatch:
                raise RuntimeError(f"Non-floating tensors differ for {repo}: {nonfloating_mismatch[:10]}")
            # Online mean avoids holding all four 0.6B models in memory at once.
            with torch.no_grad():
                for key, ref_tensor in reference_state.items():
                    if ref_tensor.is_floating_point():
                        ref_tensor.mul_((count - 1) / count).add_(candidate_state[key], alpha=1 / count)
            report["checks"].append({
                "label": label, "repo": repo, "compatible": True,
                "tokenizer": vocab_check, "tensor_count": len(reference_state),
            })
        finally:
            del candidate
            del candidate_state
            del candidate_tokenizer
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(output, safe_serialization=True)
    merged_tokenizer.save_pretrained(output)
    report["output_dir"] = str(output)
    (output / "fusion-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
