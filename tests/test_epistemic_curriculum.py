import pytest

from ronin.data.prompts import DOMAINS, build_prompts


def test_curriculum_is_deterministic_and_validated():
    assert build_prompts(3) == build_prompts(3)
    assert len(build_prompts(21)) == 21
    with pytest.raises(ValueError):
        build_prompts(0)


def test_curriculum_covers_all_domains_before_repeating():
    prompts = build_prompts(len(DOMAINS) * 4)
    assert len(DOMAINS) >= 12
    assert all(f"«{domain}»" in prompts[index * 4] for index, domain in enumerate(DOMAINS))
    assert len(set(prompts)) == len(prompts)


def test_curriculum_teaches_epistemic_distinctions_without_claiming_certainty():
    prompt = build_prompts(1)[0]
    for marker in (
        "CLASE_EPISTEMICA",
        "TIPO_DE_AFIRMACION",
        "GENERO",
        "ESTADO_DE_CODIFICACION",
        "EVIDENCIA",
        "INCERTIDUMBRE",
        "POSIBLE_REFUTACION",
        "REVISION",
    ):
        assert marker in prompt
    assert "no marques decoded sin evidencia documentada" in prompt


def test_curriculum_count_is_bounded():
    with pytest.raises(ValueError):
        build_prompts(501)
