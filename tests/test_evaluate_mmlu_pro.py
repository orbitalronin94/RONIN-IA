from pathlib import Path

import pytest
import torch

from ronin.config import get_profile
from ronin.models.transformer import RoninLM
from scripts.evaluate_mmlu_pro import (
    DATASET_REVISION,
    evaluate_rows,
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
    for batched_row, single_row in zip(batched["details"], single["details"]):
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
