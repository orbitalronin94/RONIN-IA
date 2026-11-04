from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pmc_candidate_workflow_uses_only_supported_cli_arguments():
    workflow = (ROOT / ".github/workflows/prepare-run5-corpus-candidates.yml").read_text()
    adapter = (ROOT / "scripts/prepare_pmc_oa_candidates.py").read_text()
    pmc_call = workflow.split("python scripts/prepare_pmc_oa_candidates.py", 1)[1].split("\n          fi", 1)[0]

    assert 'parser.add_argument("--hkd-fraction"' not in adapter
    assert "--hkd-fraction" not in pmc_call


def test_candidate_artifact_names_match_official_run5_downloader():
    candidate_workflow = (ROOT / ".github/workflows/prepare-run5-corpus-candidates.yml").read_text()
    official_workflow = (ROOT / ".github/workflows/ronin-official-training-holdout.yml").read_text()

    producer_prefix = "ronin-datasets-run5-library-"
    assert producer_prefix in candidate_workflow
    assert f"pattern: {producer_prefix}*" in official_workflow
    assert "pattern: ronin-run5-library-*" not in official_workflow


def test_candidate_aggregator_downloads_the_same_artifact_family_as_workers():
    workflow = (ROOT / ".github/workflows/prepare-run5-corpus-candidates.yml").read_text()

    assert "pattern: ronin-datasets-run5-library-*" in workflow
    assert "name: ronin-datasets-run5-library-${{ matrix.domain }}" in workflow
    assert "name: ronin-datasets-run5-library-${{ matrix.domain }}-hkd" in workflow
