from scripts.prepare_synthetic_corpus import make_text


def test_synthetic_corpus_is_deterministic_and_seeded():
    assert make_text(123, 20) == make_text(123, 20)
    assert make_text(123, 20) != make_text(124, 20)


def test_synthetic_corpus_has_separate_records():
    text = make_text(7, 120)
    assert text.count("\n") == 120
    assert "Registro 0:" in text
    assert "Registro 119:" in text
