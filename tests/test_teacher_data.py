import hashlib
import json

import pytest

from ronin.data.corpus import prepare
from ronin.data.prompts import build_prompts
from ronin.data.teacher import generate_completion, verify_teacher_manifest, write_teacher_dataset


def test_prompt_curriculum_is_deterministic_and_validated():
    assert build_prompts(3) == build_prompts(3)
    assert len(build_prompts(21)) == 21
    with pytest.raises(ValueError):
        build_prompts(0)


def test_generation_rejects_empty_prompt():
    with pytest.raises(ValueError, match="vacío"):
        generate_completion(object(), object(), "  ")


def test_teacher_dataset_requires_verified_mit_manifest(tmp_path):
    with pytest.raises(ValueError, match="MIT"):
        write_teacher_dataset(
            ["Explica algo"], tmp_path / "data.jsonl", object(), object(),
            {"license": "apache-2.0", "license_verified": True},
        )


def test_teacher_record_has_provenance_and_student_stays_random(tmp_path, monkeypatch):
    import ronin.data.teacher as teacher

    monkeypatch.setattr(teacher, "generate_completion", lambda *args, **kwargs: "Respuesta local.")
    manifest = {
        "model_id": "openai-community/gpt2",
        "revision": "a" * 40,
        "license": "mit",
        "license_verified": True,
        "license_url": "https://huggingface.co/openai-community/gpt2",
        "trust_remote_code": True,
    }
    output = tmp_path / "teacher.jsonl"
    count = write_teacher_dataset(["Explica una idea."], output, object(), object(), manifest)
    assert count == 1
    record = json.loads(output.read_text(encoding="utf-8"))
    expected = hashlib.sha256(
        b"Explica una idea.\nRespuesta local."
    ).hexdigest()
    assert record["sha256"] == expected
    assert record["teacher_model_license"] == "MIT"
    assert record["student_initialization"] == "random"
    assert record["teacher_weights_imported_into_student"] is False
    assert record["teacher_model_license_verified"] is True
    assert record["teacher_trust_remote_code"] is True
    assert record["generated_output_license"] == "not_asserted"
    assert record["generated_output_redistribution"] == "not_published"


def test_prepared_corpus_accepts_only_verified_local_mit_records(tmp_path, monkeypatch):
    import ronin.data.teacher as teacher

    monkeypatch.setattr(teacher, "generate_completion", lambda *args, **kwargs: "Respuesta local.")
    manifest = {
        "model_id": "openai-community/gpt2",
        "revision": "b" * 40,
        "license": "mit",
        "license_verified": True,
        "license_url": "https://huggingface.co/openai-community/gpt2",
    }
    source = tmp_path / "teacher.jsonl"
    write_teacher_dataset(["Explica una idea."], source, object(), object(), manifest)
    destination = tmp_path / "corpus.txt"
    assert prepare(source, destination) == 1
    corpus = destination.read_text(encoding="utf-8")
    assert "### Instrucción" in corpus
    assert "### Respuesta del tutor" in corpus
    assert "Respuesta local." in corpus



def test_teacher_manifest_verifies_every_local_file(tmp_path):
    weights = tmp_path / "model.safetensors"
    weights.write_bytes(b"verified model bytes")
    manifest = {
        "model_id": "openai-community/gpt2",
        "revision": "a" * 40,
        "license": "mit",
        "license_verified": True,
        "license_url": "https://huggingface.co/openai-community/gpt2",
        "weights_format": "safetensors",
        "files_sha256": {
            "model.safetensors": hashlib.sha256(weights.read_bytes()).hexdigest(),
        },
    }
    verify_teacher_manifest(tmp_path, manifest)

    weights.write_bytes(b"tampered model bytes")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_teacher_manifest(tmp_path, manifest)


def test_teacher_manifest_rejects_untracked_and_unsafe_files(tmp_path):
    weights = tmp_path / "model.safetensors"
    weights.write_bytes(b"model")
    digest = hashlib.sha256(weights.read_bytes()).hexdigest()
    manifest = {
        "model_id": "openai-community/gpt2",
        "revision": "a" * 40,
        "license": "mit",
        "license_verified": True,
        "license_url": "https://huggingface.co/openai-community/gpt2",
        "weights_format": "safetensors",
        "files_sha256": {"../model.safetensors": digest},
    }
    with pytest.raises(ValueError, match="inventario|Ruta insegura"):
        verify_teacher_manifest(tmp_path, manifest)

    manifest["files_sha256"] = {"model.safetensors": digest}
    (tmp_path / "unexpected.bin").write_bytes(b"extra")
    with pytest.raises(ValueError, match="inventario"):
        verify_teacher_manifest(tmp_path, manifest)


def test_phi4_mini_instruct_uses_builtin_transformers_model():
    from scripts.download_teacher_models import ALLOW_PATTERNS, ALLOWED_MODELS

    model = ALLOWED_MODELS["phi-4-mini-instruct"]
    assert model["repo_id"] == "microsoft/Phi-4-mini-instruct"
    assert model["license_url"] == "https://huggingface.co/microsoft/Phi-4-mini-instruct"
    assert model["trust_remote_code"] is False
    assert "model*.safetensors" in ALLOW_PATTERNS
    assert "*.py" not in ALLOW_PATTERNS
