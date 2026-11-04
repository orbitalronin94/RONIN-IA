from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import yaml


def test_write_split_preserves_per_article_pmc_revision_and_metadata(tmp_path: Path, monkeypatch):
    from scripts.prepare_run5_candidates import write_split

    def fake_scan(command, check, capture_output, text):
        report_path = Path(command[command.index("--report") + 1])
        report_path.write_text(json.dumps({"status": "clean"}), encoding="utf-8")
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_scan)
    article_text = (
        "A sufficiently long scientific article excerpt describing cellular biology, "
        "molecular pathways, gene expression, and experimental methods. " * 8
    )
    revision = "PMC12345.1@metadata-etag:xml-md5"
    extra = {
        "pmcid": "PMC12345",
        "doi": "10.0000/example",
        "source_version_prefix": "PMC12345.1",
        "source_metadata_etag": "metadata-etag",
        "source_metadata_sha256": "metadata-sha",
        "source_metadata_url": "https://pmc-oa-opendata.s3.amazonaws.com/metadata/PMC12345.1.json",
        "source_xml_url": "s3://pmc-oa-opendata/PMC12345.1/PMC12345.1.xml?md5=xml-md5",
        "source_xml_md5": "xml-md5",
        "source_xml_sha256": "xml-sha",
        "source_is_pmc_openaccess": True,
        "source_is_manuscript": False,
        "source_is_historical_ocr": False,
        "source_is_retracted": False,
    }
    metadata = write_split(
        [(
            "PMC12345.1",
            article_text,
            "CC BY 4.0",
            "https://europepmc.org/articles/PMC12345",
            0.91,
            {"semantic_density": 0.91},
            revision,
            extra,
        )],
        tmp_path / "biology_medicine",
        domain="biology_medicine",
        library_kind="base",
        source_revision="per-article-version-etag-v1",
        hkd_fraction=0.4,
        sample_dir=tmp_path / "human_review",
        global_seen_simhash={index: {} for index in range(4)},
        source_dataset="pmc-oa-opendata",
        license_policy=["CC BY 4.0", "CC0"],
    )

    sidecars = [
        json.loads(line)
        for line in (tmp_path / "biology_medicine" / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert sidecars[0]["source_dataset"] == "pmc-oa-opendata"
    assert sidecars[0]["source_revision"] == revision
    assert sidecars[0]["source_metadata_etag"] == "metadata-etag"
    assert sidecars[0]["source_xml_md5"] == "xml-md5"
    assert sidecars[0]["source_is_pmc_openaccess"] is True
    assert metadata["source_dataset"] == "pmc-oa-opendata"
    assert metadata["source_revision"] == "per-article-version-etag-v1"
    assert metadata["license_policy"] == ["CC BY 4.0", "CC0"]


def test_pmc_consolidation_workflow_uses_unescaped_source_run_id():
    workflow_path = (
        Path(__file__).parents[1]
        / ".github"
        / "workflows"
        / "consolidate-pmc-candidates.yml"
    )
    raw = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.load(raw, Loader=yaml.BaseLoader)
    assert "workflow_run" in workflow["on"]
    assert "workflow_dispatch" in workflow["on"]
    assert "source_run_id" in workflow["on"]["workflow_dispatch"]["inputs"]
    assert "\\\\${{" not in raw
    expected_run_id = "run-id: " + "$" + "{{ github.event.workflow_run.id || inputs.source_run_id }}"
    assert expected_run_id in raw