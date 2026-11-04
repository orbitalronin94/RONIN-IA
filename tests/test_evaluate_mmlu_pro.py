from pathlib import Path

import pytest
import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from scripts.evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
    load_external_dataset,
    format_prompt,
    normalize_rows,
    rows_sha256,
    select_stratified,
)


def sample_rows():
    return [
        {
            "question_id": index,
            "question": f"Question {index}?",
            "options": ["first", "second", "third", "fourth"],
            "answer_index": index % 4,
            "category": "math" if index % 2 == 0 else "history",
            "src": "fixture",
        }
        for index in range(8)
    ]


def test_normalize_mmlu_pro_and_format_all_options():
    rows = normalize_rows(sample_rows())
    prompt = format_prompt(rows[0])
    assert len(rows) == 8
    assert "A. first" in prompt
    assert "D. fourth" in prompt
    assert prompt.endswith("Answer: ")


def test_normalize_removes_n_a_placeholders_and_remaps_answer_index():
    row = {
        "question_id": 99,
        "question": "Pick the valid answer.",
        "options": ["one", "two", "three", "N/A", "N/A"],
        "answer": "C",
        "answer_index": 2,
        "category": "other",
    }
    normalized = normalize_rows([row])[0]
    assert normalized["options"] == ["one", "two", "three"]
    assert normalized["correct_index"] == 2


def test_normalize_rejects_duplicate_question_ids():
    rows = sample_rows()
    rows[1]["question_id"] = rows[0]["question_id"]
    with pytest.raises(ValueError, match="duplicado"):
        normalize_rows(rows)


def test_stratified_sampling_is_deterministic_and_balanced():
    rows = normalize_rows(sample_rows())
    selected = select_stratified(rows, limit=4, seed=123)
    assert selected == select_stratified(rows, limit=4, seed=123)
    assert {row["category"] for row in selected} == {"math", "history"}
    assert sum(row["category"] == "math" for row in selected) == 2


def test_mmlu_evaluation_reports_accuracy_domain_and_context_coverage(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    rows = normalize_rows(sample_rows())
    # Un contexto de 128 bytes permite estas preguntas cortas sin truncamiento.
    report = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows[:2],
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
    )
    assert report["selected_items"] == 2
    assert report["evaluated_items"] == 2
    assert report["skipped_context_items"] == 0
    assert report["coverage"] == 1.0
    assert set(report["by_domain"]) == {"history", "math"}
    assert report["overall"]["total"] == 2


def test_mmlu_evaluation_never_truncates_long_prompts(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    rows = normalize_rows(sample_rows())
    rows[0]["question"] = "A very long question " * 20
    report = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows[:2],
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
    )
    assert report["selected_items"] == 2
    assert report["evaluated_items"] == 1
    assert report["skipped_context_items"] == 1
    assert report["coverage"] == 0.5
    assert report["skipped"][0]["reason"] == "exceeds_context_without_truncation"


def test_dataset_revision_is_pinned():
    assert DATASET_REVISION == "b189ec765aa7ed75c8acfea42df31fdae71f97be"



def test_batched_evaluation_matches_single_item_batches(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    rows = normalize_rows(sample_rows())
    single = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
        batch_token_budget=1,
    )
    batched = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
        batch_token_budget=8192,
    )
    assert batched["overall"] == single["overall"]
    assert batched["by_domain"] == single["by_domain"]
    assert [row["id"] for row in batched["details"]] == [
        row["id"] for row in single["details"]
    ]
    assert [row["predicted_index"] for row in batched["details"]] == [
        row["predicted_index"] for row in single["details"]
    ]
    for batched_row, single_row in zip(batched["details"], single["details"], strict=True):
        assert batched_row["candidate_log_probabilities"] == pytest.approx(
            single_row["candidate_log_probabilities"], abs=1e-5
        )
    assert batched["batching"]["batches"] < single["batching"]["batches"]


def test_batch_token_budget_must_be_positive(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    rows = normalize_rows(sample_rows())
    with pytest.raises(ValueError, match="batch_token_budget"):
        evaluate_rows(
            checkpoint=checkpoint,
            rows=rows[:1],
            all_rows_sha256=rows_sha256(rows),
            batch_token_budget=0,
        )



def test_forward_last_logits_matches_full_forward_for_each_sequence():
    config, _ = get_profile("tiny")
    model = RoninLM(config).eval()
    input_ids = torch.randint(0, config.vocab_size, (3, 37))
    positions = torch.tensor([36, 21, 9], dtype=torch.long)
    with torch.no_grad():
        full_logits, _ = model(input_ids)
        selected_logits = model.forward_last_logits(input_ids, positions)
    expected = full_logits[torch.arange(3), positions]
    torch.testing.assert_close(selected_logits, expected, rtol=1e-5, atol=1e-6)


def test_forward_last_logits_rejects_invalid_positions():
    config, _ = get_profile("tiny")
    model = RoninLM(config).eval()
    input_ids = torch.randint(0, config.vocab_size, (2, 8))
    with pytest.raises(ValueError, match="last_positions"):
        model.forward_last_logits(input_ids, torch.tensor([7], dtype=torch.long))
    with pytest.raises(ValueError, match="fuera de secuencia"):
        model.forward_last_logits(input_ids, torch.tensor([7, 8], dtype=torch.long))


def test_last_position_only_and_full_logits_evaluation_have_identical_predictions(tmp_path: Path):
    config, _ = get_profile("tiny")
    model = RoninLM(config)
    checkpoint = tmp_path / "model.pt"
    torch.save({"model": model.state_dict(), "step": 0}, checkpoint)
    rows = normalize_rows(sample_rows())
    full = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
        batch_token_budget=8192,
        last_token_only=False,
    )
    optimized = evaluate_rows(
        checkpoint=checkpoint,
        rows=rows,
        all_rows_sha256=rows_sha256(rows),
        context_length=128,
        batch_token_budget=8192,
        last_token_only=True,
    )
    assert full["inference_path"] == "full_sequence_logits"
    assert optimized["inference_path"] == "last_position_only"
    assert full["overall"] == optimized["overall"]
    assert full["by_domain"] == optimized["by_domain"]
    assert [row["predicted_index"] for row in full["details"]] == [
        row["predicted_index"] for row in optimized["details"]
    ]
    for full_row, optimized_row in zip(full["details"], optimized["details"], strict=True):
        assert optimized_row["candidate_log_probabilities"] == pytest.approx(
            full_row["candidate_log_probabilities"], abs=1e-5
        )


def test_external_loader_supports_validation_without_touching_test(monkeypatch):
    import sys
    import types

    calls = []
    class FakeDataset:
        def __iter__(self):
            return iter(sample_rows())

    def fake_load_dataset(dataset_id, *, split, revision):
        calls.append((dataset_id, split, revision))
        return FakeDataset()

    monkeypatch.setitem(sys.modules, "datasets", types.SimpleNamespace(load_dataset=fake_load_dataset))
    validation = load_external_dataset(DATASET_REVISION, split="validation")
    assert len(validation) == 8
    assert calls == [("TIGER-Lab/MMLU-Pro", "validation", DATASET_REVISION)]

    with pytest.raises(ValueError, match="split"):
        load_external_dataset(DATASET_REVISION, split="train")
