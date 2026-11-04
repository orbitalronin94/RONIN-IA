from pathlib import Path

import yaml


def test_run5_workflow_is_valid_yaml_and_declares_32_library_matrix():
    workflow_path = Path(".github/workflows/prepare-run5-corpus-candidates.yml")
    workflow = yaml.load(workflow_path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)

    assert workflow["name"] == "Preparar las 32 bibliotecas RUN 5 (16 dominios × General/HKD)"
    assert workflow["on"]["push"]["branches"] == ["main"]
    assert "workflow_dispatch" in workflow["on"]

    matrix = workflow["jobs"]["prepare-domain"]["strategy"]["matrix"]["domain"]
    assert len(matrix) == 16
    assert len(set(matrix)) == 16

    env = workflow["jobs"]["prepare-domain"]["env"]
    assert env["MIN_TRAIN_MIB"] == "${{ github.event.inputs.min_train_mib || '1' }}"

    assert workflow["jobs"]["aggregate-and-gate"]["needs"] == "prepare-domain"
