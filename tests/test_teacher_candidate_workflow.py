from pathlib import Path

import yaml


def test_phi4_candidate_workflow_never_trains_or_publishes_generated_text():
    path = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "teacher-candidate-generation.yml"
    )
    workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert "workflow_dispatch" in workflow["on"]
    assert "workflow_run" in workflow["on"]
    job = workflow["jobs"]["generate-candidates"]
    steps = {step.get("name"): step for step in job["steps"]}
    audit = steps["Auditar estructura de las propuestas; no certificar veracidad"]["run"]
    assert '"used_for_training": False' in audit
    upload = steps["Publicar solo auditoría y metadatos, no las generaciones"]["with"]["path"]
    assert "teacher-candidate-summary.json" in upload
    assert "teacher-ref-audit.json" in upload
    assert "phi-4-mini-instruct.jsonl" not in upload
