from pathlib import Path

import yaml


def test_rapid_open_training_loop_is_gated_and_keeps_final_test_unseen():
    path = Path(__file__).parents[1] / ".github" / "workflows" / "rapid-open-training-cycles.yml"
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert workflow["on"]["schedule"][0]["cron"] == "23 */6 * * *"
    job = workflow["jobs"]["rapid-cycles"]
    assert job["concurrency"] if "concurrency" in job else workflow["concurrency"]["cancel-in-progress"] == "false"
    steps = {step.get("name"): step for step in job["steps"]}
    assert "Gate G-0 — exigir autorización legal explícita" in steps
    assert steps["Preparar corpus abierto admitido y splits por obra"]["if"] == "steps.g0.outputs.authorized == 'true'"
    train = steps["Ejecutar ciclos rápidos con promoción conservadora"]["run"]
    assert '"--split", "validation"' in train
    assert '"--split", "test"' not in train
    assert 'm1["overall"]["accuracy"] > m0["overall"]["accuracy"]' in train
    assert 'lm1["bits_per_byte"] <= lm0["bits_per_byte"]' in train
    assert "MMLU-Pro test split is never used" in train
    assert "actions/cache/restore@v5" in str(job)
    assert "actions/cache/save@v5" in str(job)
