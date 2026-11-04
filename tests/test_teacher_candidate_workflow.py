from pathlib import Path


def test_retired_phi4_candidate_workflow_is_not_scheduled():
    path = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "teacher-candidate-generation.yml"
    )
    assert not path.exists()
