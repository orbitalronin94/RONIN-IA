from pathlib import Path

import yaml


def test_official_training_workflow_excludes_portfolio_and_requires_sixteen_libraries():
    workflow_path = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "ronin-official-training-holdout.yml"
    )
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert "workflow_dispatch" in workflow["on"]
    assert "push" not in workflow["on"]
    assert "pull_request" not in workflow["on"]
    job = workflow["jobs"]["ronin-training"]
    assert job["env"]["MMLU_REVISION"] == "b189ec765aa7ed75c8acfea42df31fdae71f97be"
    assert job["env"]["STEPS"] == "${{ inputs.steps || '1000' }}"
    assert job["env"]["SEEDS"] == "${{ inputs.seeds || '1337' }}"
    assert job["env"]["MMLU_LIMIT"] == "${{ inputs.mmlu_limit || '0' }}"
    assert job["timeout-minutes"] == "360"

    steps = job["steps"]
    by_name = {step.get("name"): step for step in steps}
    assert "Obtener Portfolio en revisión inmutable" not in by_name
    assert "Preparar corpus de Portfolio" not in by_name
    assert "Verificar autorización, finalidad y hash del corpus" not in by_name
    assert "Gate obligatorio: dieciséis bibliotecas admitidas antes del entrenamiento oficial" in by_name
    gate = by_name["Gate obligatorio: ocho bibliotecas admitidas antes de RUN #5"]["run"]
    assert "validate_sixteen_libraries.py --require-ready --corpus-root /tmp/ronin-sixteen-libraries" in gate

    cycle = by_name["Entrenar desde cero y evaluar el test externo completo antes/después"]["run"]
    assert "--text /tmp/ronin-training/combined-train.txt" in cycle
    assert '--revision "$MMLU_REVISION"' in cycle
    assert '--limit "$MMLU_LIMIT"' in cycle
    assert "mmlu-inicial.json" in cycle
    assert "mmlu-final.json" in cycle

    mixture = by_name["Construir mezcla balanceada de las dieciséis bibliotecas admitidas"]["run"]
    assert "--input portfolio=" not in mixture
    assert "--input mathematics_hkd=" in mixture
    assert "--input logic_epistemology_hkd=" in mixture
    assert "--input philosophy_hkd=" in mixture
    assert "--input physics_hkd=" in mixture
    assert "--input chemistry_hkd=" in mixture
    assert "--input biology_medicine_hkd=" in mixture
    assert "--input computer_science_hkd=" in mixture
    assert "--input law_economics_social_sciences_hkd=" in mixture
    for library in ["mathematics", "logic_epistemology", "philosophy", "physics", "chemistry", "biology_medicine", "computer_science", "law_economics_social_sciences"]:
        assert f"--input {library}=" in mixture
    assert "--input phi4_tutor=" not in mixture

    assert "Generar propuestas Phi-4 y auditar REF sin publicar salidas" not in by_name
    assert "Adquirir biblioteca primaria de criptografía como corpus auxiliar" not in by_name

    summary = by_name["Consolidar métricas, cobertura y procedencia"]["run"]
    assert '"used_for_training": False' in summary
    assert '"training_corpora"' in summary
    assert '"role": "retrieval_only_fallback"' in summary
    assert '"used_for_training": False' in summary
    assert '"expected_full_test_items": 12032' in summary
    assert 'initial["selected_items"] == final["selected_items"]' in summary

    artifact = by_name["Publicar informes y manifiestos sin corpus ni checkpoints"]
    assert artifact["with"]["path"] == "reports/"
    assert artifact["with"]["name"] == "ronin-official-full-mmlu-training-cycle"
