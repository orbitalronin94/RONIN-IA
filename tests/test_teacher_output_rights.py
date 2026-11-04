from __future__ import annotations

import json

from ronin.data import teacher


def test_generated_text_does_not_inherit_model_mit_license(monkeypatch, tmp_path):
    monkeypatch.setattr(teacher, "generate_completion", lambda *args, **kwargs: "Respuesta propuesta.")
    manifest = {
        "model_id": "microsoft/Phi-4-mini-instruct",
        "revision": "a" * 40,
        "license": "mit",
        "license_verified": True,
        "license_url": "https://huggingface.co/microsoft/Phi-4-mini-instruct",
        "trust_remote_code": True,
    }
    output = tmp_path / "teacher.jsonl"

    assert teacher.write_teacher_dataset(
        ["Explica una idea."], output, object(), object(), manifest
    ) == 1

    record = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert record["teacher_model_license"] == "MIT"
    assert record["teacher_model_license_verified"] is True
    assert record["generated_output_license"] == "not_asserted"
    assert record["generated_output_redistribution"] == "not_published"
    assert record["teacher_weights_imported_into_student"] is False
