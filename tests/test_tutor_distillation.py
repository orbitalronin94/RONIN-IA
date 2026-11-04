from scripts.distill_mmlu_pro_tutor import build_record, parse_teacher_response, tutor_prompt


def test_parse_teacher_response_requires_explicit_answer_and_rationale():
    answer, rationale = parse_teacher_response(
        "ANSWER: C\nRATIONALE: La opción C satisface la condición indicada en el enunciado."
    )
    assert answer == "C"
    assert rationale.startswith("La opción C")


def test_parse_teacher_response_rejects_missing_or_too_short_rationale():
    assert parse_teacher_response("ANSWER: B\nRATIONALE: Sí.") == ("B", None)
    assert parse_teacher_response("La respuesta es B.") == (None, None)


def test_tutor_prompt_does_not_include_gold_answer():
    row = {"question": "¿Cuánto es 2+2?", "options": ["3", "4", "5"], "correct_index": 1}
    prompt = tutor_prompt(row)
    assert "ANSWER:" in prompt
    assert "RATIONALE:" in prompt
    assert "correct_index" not in prompt
    assert "No muestres deliberación privada" in prompt


def test_training_record_is_only_built_for_verified_correct_answer():
    row = {
        "id": "q1", "category": "mathematics",
        "question": "¿Cuánto es 2+2?", "options": ["3", "4", "5"],
        "correct_index": 1,
    }
    manifest = {
        "model_id": "microsoft/Phi-4-mini-instruct",
        "revision": "a" * 40,
        "license": "mit", "license_verified": True,
        "license_url": "https://huggingface.co/microsoft/Phi-4-mini-instruct",
    }
    record = build_record(row, "B", "La suma de dos y dos es cuatro.", manifest)
    assert record["teacher_correct"] is True
    assert record["source_split"] == "validation"
    assert record["student_weights_imported_from_teacher"] is False
    assert "Answer: B" in record["training_text"]
