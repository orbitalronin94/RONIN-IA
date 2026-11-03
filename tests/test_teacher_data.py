import io
import json

import pytest

from ronin.data.prompts import build_prompts
from ronin.data.teacher import TeacherConfig, chat_completion, write_teacher_dataset
from scripts.prepare_teacher_corpus import prepare


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def fake_opener(request, timeout):
    assert request.full_url.endswith("/chat/completions")
    assert timeout == 90
    return FakeResponse({"choices": [{"message": {"content": "Una explicación clara."}}]})


def test_prompt_curriculum_is_deterministic_and_validated():
    assert build_prompts(3) == build_prompts(3)
    assert len(build_prompts(21)) == 21
    with pytest.raises(ValueError):
        build_prompts(0)


def test_teacher_client_uses_chat_completion_contract():
    config = TeacherConfig(
        base_url="https://api.example.test/v1",
        api_key="test-token",
        model="example-model",
    )
    assert chat_completion(config, "Explica una idea.", opener=fake_opener) == "Una explicación clara."


def test_teacher_data_requires_terms_confirmation(tmp_path):
    config = TeacherConfig(
        base_url="https://api.example.test/v1",
        api_key="test-token",
        model="example-model",
    )
    with pytest.raises(ValueError, match="review"):
        write_teacher_dataset(["Explica una idea."], tmp_path / "data.jsonl", config)


def test_teacher_data_to_corpus_round_trip(tmp_path):
    config = TeacherConfig(
        base_url="https://api.example.test/v1",
        api_key="test-token",
        model="example-model",
    )
    source = tmp_path / "teacher.jsonl"
    count = write_teacher_dataset(
        ["Explica una idea.", "Explica otra idea."],
        source,
        config,
        confirm_training_rights=True,
        opener=fake_opener,
    )
    assert count == 2
    records = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
    assert records[0]["training_terms_reviewed"] is True
    corpus = tmp_path / "corpus.txt"
    assert prepare(source, corpus) == 2
    text = corpus.read_text(encoding="utf-8")
    assert "### Instrucción" in text
    assert "### Respuesta del tutor" in text
    assert "Una explicación clara." in text


def test_prepare_rejects_modified_teacher_record(tmp_path):
    source = tmp_path / "bad.jsonl"
    source.write_text(
        json.dumps(
            {
                "prompt": "pregunta",
                "completion": "respuesta",
                "sha256": "not-the-right-hash",
                "source_type": "teacher_generated_text",
                "training_terms_reviewed": True,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="SHA-256"):
        prepare(source, tmp_path / "corpus.txt")
