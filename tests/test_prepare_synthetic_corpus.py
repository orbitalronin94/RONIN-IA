from scripts.prepare_synthetic_corpus import DOMAINS, is_prime, make_text


def test_synthetic_curriculum_is_deterministic_and_seeded():
    assert make_text(123, 20) == make_text(123, 20)
    assert make_text(123, 20) != make_text(124, 20)


def test_synthetic_curriculum_has_balanced_domain_records():
    text = make_text(7, 120)
    assert text.count("[Registro ") == 120
    for domain in DOMAINS:
        assert text.count(f"dominio={domain}") == 15
    assert "Pregunta:" in text
    assert "Respuesta:" in text
    assert "Explicación:" in text


def test_synthetic_curriculum_contains_verifiable_content_not_gibberish():
    text = make_text(2026, 200)
    assert "bena" not in text
    assert "O(log n)" in text or "F=ma" in text or "módulo" in text
    assert is_prime(2)
    assert is_prime(97)
    assert not is_prime(1)
    assert not is_prime(91)


def test_synthetic_train_and_validation_seeds_change_the_examples():
    assert make_text(8675309, 200) != make_text(8675310, 200)
