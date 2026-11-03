import hashlib
import json

import pytest

from ronin.data.prompts import build_prompts
from ronin.data.teacher import generate_completion, write_teacher_dataset


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
    }
    output = tmp_path / "teacher.jsonl"
    count = write_teacher_dataset(
        ["Explica una idea."], output, object(), object(), manifest
    )
    assert count == 1
    record = json.loads(output.read_text(encoding="utf-8"))
    expected = hashlib.sha256(
        "Explica una idea.\nRespuesta local.".encode("utf-8")
    ).hexdigest()
    assert record["sha256"] == expected
    assert record["teacher_license"] == "MIT"
    assert record["student_initialization"] == "random"
    assert record["teacher_weights_imported_into_student"] is False
