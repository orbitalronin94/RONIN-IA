from scripts.build_benchmark_reasoning_corpus import (
    normalize_commonsense,
    normalize_gsm8k,
    render,
)


def test_gsm8k_keeps_source_solution_and_requires_final_answer_marker():
    row = {
        "question": "A shop has 12 apples and sells 5. How many remain?",
        "answer": "12 - 5 = 7\n#### 7",
    }
    record = normalize_gsm8k(row, 3)
    assert record is not None
    assert record["answer"] == row["answer"]
    assert record["rationale"] == "source_provided"
    assert normalize_gsm8k({"question": row["question"], "answer": "7"}, 4) is None


def test_commonsenseqa_maps_gold_label_without_inventing_rationale():
    row = {
        "question": "Where would someone usually keep a toothbrush?",
        "question_concept": "toothbrush",
        "choices": {
            "label": ["A", "B", "C"],
            "text": ["kitchen", "bathroom", "garage"],
        },
        "answerKey": "B",
    }
    record = normalize_commonsense(row, 7)
    assert record is not None
    assert record["answer_text"] == "bathroom"
    assert record["rationale"] == "not_provided_by_source"
    rendered = render(record)
    assert "Correct answer: B. bathroom" in rendered
    assert "not supplied in the source dataset" in rendered
