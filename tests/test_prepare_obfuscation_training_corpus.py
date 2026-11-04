import hashlib
import json

import pytest

import scripts.prepare_obfuscation_training_corpus as prepare


def _case(record_id, split, text):
    return {
        "record_id": record_id,
        "split": split,
        "text": text,
        "case_type": "B",
        "label": "NO_MESSAGE_IN_CONTROL",
        "evidence_status": "synthetic_control",
        "mechanism": "Control sin carga útil insertada",
        "solution_summary": "No hay mensaje oculto en el control.",
        "reproduction_steps": ["Comprobar que no existe carga útil."],
        "evidence_refs": [],
        "source_id": "synthetic-control",
        "source_license": "Redacción propia",
        "confidence": 1.0,
        "synthetic": True,
    }


def test_exports_only_train_and_keeps_holdouts_out(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare, "validate_obfuscation_case", lambda row: [])
    rows = [
        _case("train-1", "train", "texto de entrenamiento"),
        _case("validation-1", "validation", "NO_INCLUIR_VALIDATION"),
        _case("test-1", "test", "NO_INCLUIR_TEST"),
    ]
    source = tmp_path / "cases.jsonl"
    raw = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    source.write_bytes(raw)
    case_manifest = {
        "dataset_id": "ronin-obfuscation-patterns-test",
        "record_count": 3,
        "dataset_sha256": hashlib.sha256(raw).hexdigest(),
        "counts_by_split": {"train": 1, "validation": 1, "test": 1, "holdout": 0},
    }
    manifest_path = tmp_path / "cases-manifest.json"
    manifest_path.write_text(json.dumps(case_manifest), encoding="utf-8")
    output = tmp_path / "train.txt"
    report_path = tmp_path / "training-manifest.json"

    report = prepare.prepare_training_corpus(source, manifest_path, output, report_path)

    content = output.read_text(encoding="utf-8")
    assert "texto de entrenamiento" in content
    assert "NO_INCLUIR_VALIDATION" not in content
    assert "NO_INCLUIR_TEST" not in content
    assert report["train_records"] == 1
    assert report["validation_reserved"] == 1
    assert report["test_reserved"] == 1
    assert report["training_text_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()


def test_rejects_case_jsonl_that_does_not_match_manifest(tmp_path):
    source = tmp_path / "cases.jsonl"
    source.write_text("{}\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "dataset_id": "x",
        "record_count": 1,
        "dataset_sha256": "0" * 64,
        "counts_by_split": {"train": 1, "validation": 0, "test": 0},
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256"):
        prepare.prepare_training_corpus(source, manifest, tmp_path / "out.txt", tmp_path / "out.json")
