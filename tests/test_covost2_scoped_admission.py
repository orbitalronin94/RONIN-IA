import json
from pathlib import Path

from scripts.audit_covost2_candidate import partition_for
from scripts.ingest_covost2_translation_only import (
    EXPECTED_ARCHIVE_SHA256,
    is_known_split,
    is_training_split,
)

ROOT = Path(__file__).parents[1]


def test_covost2_uses_only_pinned_archives_and_upstream_train_families():
    assert len(EXPECTED_ARCHIVE_SHA256) == 3
    assert all(len(value) == 64 for value in EXPECTED_ARCHIVE_SHA256.values())
    assert is_known_split("train")
    assert is_known_split("train_covost")
    assert is_known_split("dev")
    assert not is_known_split("train_unreviewed")
    assert is_training_split("train")
    assert is_training_split("train_covost")
    assert not is_training_split("dev")
    assert not is_training_split("test")
    assert not is_training_split("train_dup")


def test_covost2_partition_is_deterministic_and_disjoint_by_source_coordinate():
    first = partition_for("covost_v2.es_en.tsv.tar.gz", 26728)
    assert first == partition_for("covost_v2.es_en.tsv.tar.gz", 26728)
    assert first in {"train", "validation", "test"}
    assert partition_for("covost_v2.es_en.tsv.tar.gz", 26729) in {
        "train", "validation", "test"
    }


def test_covost2_manual_review_covers_all_three_pairs_and_phone_flags():
    report = json.loads(
        (ROOT / "data/datasets/reviews/covost2-manual-review-2026-11-05.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["review_status"] == "PASS_WITH_TRANSLATION_NOISE"
    assert report["sample_design"]["total_records"] == 36
    assert len(report["sampled_records"]) == 36
    counts = {}
    for row in report["sampled_records"]:
        counts[row["pair"]] = counts.get(row["pair"], 0) + 1
    assert counts == {"es_en": 12, "ca_en": 12, "en_ca": 12}
    assert report["phone_like_review"]["flagged_records"] == 3
    assert report["sample_review"]["pii_or_sensitive_content_found"] == 0


def test_covost2_exact_payload_has_a_level_a_rights_record_and_scoped_policy():
    registry = [
        json.loads(line)
        for line in (
            ROOT / "data/datasets/rights_registry/records.jsonl"
        ).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    matches = [
        row for row in registry
        if row["record_id"] == "covost2-cc0-translation-only-d3a235f41906e78d"
    ]
    assert len(matches) == 1
    assert matches[0]["license_id"] == "CC0-1.0"
    assert matches[0]["rights_level"] == "A"
    assert matches[0]["payload_sha256"] == (
        "d3a235f41906e78da12aa286eea57d51a71e4a3ec03b3d712f53c97f24b77fe9"
    )
    policy = json.loads(
        (ROOT / "data/datasets/rights_registry/policy.json").read_text(encoding="utf-8")
    )
    assert policy["source_scoped_training_allowed"] is True
    assert policy["global_training_allowed_only_if_global_g0_passes"] is True
