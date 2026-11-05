import hashlib
import json

import pytest

from ronin.data.local_dual_teacher import verify_manifest
from scripts.distill_mmlu_pro_dual_tutor import challenge_prompt, parse_response, tutor_prompt
from scripts.download_dual_teachers import MODELS


def test_dual_tutor_registry_uses_official_model_ids_and_licenses():
    assert MODELS["qwen3.6-27b"]["base_id"] == "Qwen/Qwen3.6-27B"
    assert MODELS["qwen3.6-27b"]["license"] == "apache-2.0"
    assert MODELS["qwen3.6-27b"]["quant_repo"] == "ggml-org/Qwen3.6-27B-GGUF"
    assert MODELS["qwen3.6-27b"]["files"]["4bit"].endswith("Q4_K_M.gguf")
    assert MODELS["qwen3.6-27b"]["files"]["8bit"].endswith("Q8_0.gguf")
    assert MODELS["deepseek-r1-distill-32b"]["base_id"] == (
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
    )
    assert MODELS["deepseek-r1-distill-32b"]["license"] == "mit"
    assert MODELS["deepseek-r1-distill-32b"]["upstream_base"] == "Qwen/Qwen2.5-32B"
    assert MODELS["deepseek-r1-distill-32b"]["upstream_base_license"] == "apache-2.0"
    assert MODELS["deepseek-r1-distill-32b"]["quant_repo"] == (
        "bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF"
    )


def test_dual_tutor_prompt_does_not_leak_gold_answer():
    row = {
        "question": "¿Cuánto es 2+2?",
        "options": ["3", "4", "5"],
        "correct_index": 1,
    }
    prompt = tutor_prompt(row)
    assert "ANSWER:" in prompt
    assert "RATIONALE:" in prompt
    assert "correct_index" not in prompt
    assert "no deliberación privada" in prompt


def test_socratic_challenge_compares_both_answers_without_gold_leakage():
    row = {
        "question": "¿Cuánto es 2+2?",
        "options": ["3", "4", "5"],
        "correct_index": 1,
    }
    prompt = challenge_prompt(
        row,
        {"answer": "B", "rationale": "La suma de dos y dos es cuatro."},
        {"answer": "A", "rationale": "Una explicación alternativa que debe contrastarse."},
    )
    assert "¿por qué es correcta tu respuesta?" in prompt
    assert "Tu respuesta provisional: B" in prompt
    assert "Respuesta independiente del otro tutor: A" in prompt
    assert "correct_index" not in prompt
    assert "No muestres deliberación privada" in prompt


def test_parser_extracts_answer_and_explanation():
    answer, rationale = parse_response(
        "ANSWER: B\nRATIONALE: La suma de dos y dos es cuatro porque se combinan "
        "dos unidades con otras dos unidades."
    )
    assert answer == "B"
    assert rationale.startswith("La suma")


def test_parser_rejects_unstructured_or_short_explanations():
    assert parse_response("La respuesta es B.") == (None, None)
    assert parse_response("ANSWER: A\nRATIONALE: Sí.") == ("A", None)


def test_manifest_verifies_apache_model(tmp_path):
    weights = tmp_path / "model-Q4_K_M.gguf"
    weights.write_bytes(b"local model fixture")
    manifest = {
        "model_id": "Qwen/Qwen3.6-27B",
        "revision": "a" * 40,
        "license": "apache-2.0",
        "license_verified": True,
        "trust_remote_code": False,
        "quantization_format": "GGUF",
        "quantization": "4bit",
        "quantized_file": weights.name,
        "quantized_file_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
    }
    (tmp_path / "ronin-teacher-manifest.json").write_text(json.dumps(manifest))
    assert verify_manifest(tmp_path, "4bit")["license"] == "apache-2.0"


def test_manifest_rejects_modified_or_unverified_files(tmp_path):
    weights = tmp_path / "model-Q4_K_M.gguf"
    weights.write_bytes(b"initial")
    manifest = {
        "model_id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
        "revision": "b" * 40,
        "license": "mit",
        "license_verified": True,
        "trust_remote_code": False,
        "quantization_format": "GGUF",
        "quantization": "4bit",
        "quantized_file": weights.name,
        "quantized_file_sha256": hashlib.sha256(b"initial").hexdigest(),
    }
    manifest_path = tmp_path / "ronin-teacher-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    weights.write_bytes(b"modified")
    with pytest.raises(ValueError, match="Hash.*incorrecto"):
        verify_manifest(tmp_path, "4bit")
    manifest["license_verified"] = False
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="licencia/código remoto"):
        verify_manifest(tmp_path, "4bit")
