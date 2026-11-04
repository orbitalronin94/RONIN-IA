import json
from pathlib import Path


def test_only_scoped_common_corpus_hkd_adapters_are_enabled():
    manifest = json.loads(
        Path("data/manifests/knowledge_dense_sources.json").read_text(encoding="utf-8")
    )
    audit = json.loads(
        Path("reports/license_audit.json").read_text(encoding="utf-8")
    )
    authorization = next(
        item for item in audit["candidate_intake_authorizations"]
        if item["source_id"] == "PleIAs/common_corpus"
    )
    enabled = [source for source in manifest["sources"] if source.get("enabled") is True]

    assert len(enabled) == 8
    assert {source["domain"] for source in enabled} == {
        "mathematics",
        "logic_epistemology",
        "philosophy",
        "physics",
        "chemistry",
        "biology_medicine",
        "computer_science",
        "law_economics_social_sciences",
    }
    for source in enabled:
        assert source["dataset_id"] == "PleIAs/common_corpus"
        assert source["revision"] == authorization["dataset_revision"]
        assert set(source["allowed_licenses"]).issubset(
            set(authorization["allowed_licenses"])
        )
        assert source["license_audit"] == "reports/license_audit.json"
        assert source["candidate_authorization"] == "LIMITED_PASS"
        assert source["training_eligible"] is False
        assert source["admitted"] is False


def test_non_common_corpus_hkd_sources_remain_disabled():
    manifest = json.loads(
        Path("data/manifests/knowledge_dense_sources.json").read_text(encoding="utf-8")
    )
    for source in manifest["sources"]:
        if source.get("dataset_id") != "PleIAs/common_corpus":
            assert source.get("enabled") is False


def test_hkd_metric_weights_remain_normalized():
    manifest = json.loads(
        Path("data/manifests/knowledge_dense_sources.json").read_text(encoding="utf-8")
    )
    weights = manifest["metric"]["weights"]
    assert set(weights) == {
        "domain_relevance",
        "knowledge_density",
        "specificity",
        "information_content",
        "structure",
    }
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert manifest["metric"]["id"] == "RONIN-HKD-0.1"
