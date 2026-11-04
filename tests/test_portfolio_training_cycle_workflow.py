from pathlib import Path

import yaml


def test_portfolio_training_cycle_is_reproducible_and_separates_evaluation():
    workflow_path = Path(__file__).parents[1] / ".github" / "workflows" / "portfolio-training-cycle.yml"
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert "workflow_dispatch" in workflow["on"]
    assert "push" in workflow["on"]
    job = workflow["jobs"]["portfolio-training"]
    assert job["env"]["PORTFOLIO_REVISION"] == "fffc234fdf3f82b6a90d56ae9b190d1c0de79690"
    assert job["env"]["MMLU_REVISION"] == "b189ec765aa7ed75c8acfea42df31fdae71f97be"
    assert job["env"]["STEPS"] == "${{ github.event_name == 'workflow_dispatch' && inputs.steps || (github.event_name == 'push' && '1000' || '100') }}"
    assert job["env"]["SEEDS"] == "${{ github.event_name == 'workflow_dispatch' && inputs.seeds || (github.event_name == 'push' && '1337,2027,42' || '1337') }}"
    assert job["env"]["MMLU_LIMIT"] == "${{ github.event_name == 'workflow_dispatch' && inputs.mmlu_limit || '140' }}"

    steps = job["steps"]
    by_name = {step.get("name"): step for step in steps}
    portfolio = by_name["Obtener Portfolio en revisión inmutable"]
    assert portfolio["with"]["ref"] == job["env"]["PORTFOLIO_REVISION"]

    validation = by_name["Verificar autorización, finalidad y hash del corpus"]["run"]
    assert "autorización expresa" in validation
    assert "entrenamiento únicamente" in validation
    assert "corpus_sha256" in validation

    cycle = by_name["Entrenar cada semilla y evaluar MMLU-Pro antes/después"]["run"]
    assert "--text /tmp/ronin-portfolio/processed/train.txt" in cycle
    assert "--revision \"$MMLU_REVISION\"" in cycle
    assert "--limit \"$MMLU_LIMIT\"" in cycle
    assert "mmlu-inicial.json" in cycle
    assert "mmlu-final.json" in cycle

    summary = by_name["Consolidar métricas, cobertura y procedencia"]["run"]
    assert '"used_for_training": False' in summary
    assert 'initial["selected_items"] == final["selected_items"]' in summary

    artifact = by_name["Publicar informes sin corpus ni checkpoints"]
    assert artifact["with"]["path"] == "reports/"
