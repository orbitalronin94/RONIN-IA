import hashlib
import json
from pathlib import Path

import pytest

from scripts.aggregate_pmc_candidate_shards import ALLOW, REVISION, SOURCE, aggregate


def write_library(root: Path, library_id: str, text: str) -> dict:
    library_root = root / library_id
    library_root.mkdir(parents=True)
    payloads = {
        "train": (text + "\n\n").encode("utf-8"),
        "validation": b"",
        "test": b"",
    }
    split_bytes = {}
    split_sha256 = {}
    document_count = {"train": 1, "validation": 0, "test": 0}
    for split, payload in payloads.items():
        (library_root / f"{split}.txt").write_bytes(payload)
        split_bytes[split] = len(payload)
        split_sha256[split] = hashlib.sha256(payload).hexdigest()

    sidecar_row = {
        "document_id": library_id + "-doc-1",
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "partition": "train",
    }
    sidecar = (json.dumps(sidecar_row, sort_keys=True) + "\n").encode("utf-8")
    (library_root / "documents.jsonl").write_bytes(sidecar)
    return {
        "id": library_id,
        "train_bytes": split_bytes["train"],
        "document_count": document_count,
        "split_bytes": split_bytes,
        "split_sha256": split_sha256,
        "documents_manifest_sha256": hashlib.sha256(sidecar).hexdigest(),
    }


def write_domain_shard(root: Path, domain: str, texts: tuple[str, str]) -> None:
    domain_root = root / f"ronin-pmc-oa-{domain}-candidates"
    domain_root.mkdir(parents=True)
    libraries = [
        write_library(domain_root, f"{domain}_general", texts[0]),
        write_library(domain_root, f"{domain}_hkd", texts[1]),
    ]
    report = {
        "source": {
            "dataset_id": SOURCE,
            "revision": REVISION,
            "document_license_allowlist": sorted(ALLOW),
        },
        "training_eligible": False,
        "admitted": False,
        "ingestion": {
            "accepted_documents": 2,
            "accepted_text_bytes": sum(len(item.encode("utf-8")) for item in texts),
            "source_counters": {},
        },
        "libraries": libraries,
        "ready_for_human_review": True,
    }
    (domain_root / "run5-candidate-manifest.json").write_text(
        json.dumps(report), encoding="utf-8"
    )


def test_aggregates_nested_artifact_layout_and_reports_missing_domain(tmp_path):
    input_root = tmp_path / "incoming"
    write_domain_shard(input_root, "chemistry", ("copper chemistry", "polymer chemistry"))

    report = aggregate(
        input_root,
        tmp_path / "report",
        "12345",
        minimum=2,
        expected_domains={"biology_medicine", "chemistry"},
    )

    assert report["domain_count"] == 1
    assert report["library_count"] == 2
    assert report["unique_document_texts"] == 2
    assert report["verified_train_text_bytes"] > 0
    assert report["missing_expected_domains"] == ["biology_medicine"]
    assert report["complete_general_hkd_pairing"] is False
    assert report["status"] == "partial_candidate_pending_human_review"


def test_refuses_to_publish_an_empty_success(tmp_path):
    with pytest.raises(SystemExit, match="No PMC candidate manifests"):
        aggregate(
            tmp_path / "empty",
            tmp_path / "report",
            "12345",
            minimum=1,
        )


def test_flags_exact_duplicates_across_general_and_hkd(tmp_path):
    input_root = tmp_path / "incoming"
    write_domain_shard(input_root, "chemistry", ("same exact text", "same exact text"))

    report = aggregate(
        input_root,
        tmp_path / "report",
        "12345",
        minimum=1,
        expected_domains={"chemistry"},
    )

    assert report["cross_domain_or_library_exact_duplicates"] == 1
    assert report["minimum_target_met"] is False
    assert report["status"] == "blocked_exact_duplicates"


def test_rejects_modified_split_payload_even_when_manifest_exists(tmp_path):
    input_root = tmp_path / "incoming"
    write_domain_shard(input_root, "chemistry", ("valid general text", "valid hkd text"))
    payload = (
        input_root
        / "ronin-pmc-oa-candidates"
        / "chemistry"
        / "chemistry_general"
        / "train.txt"
    )
    payload.write_text("tampered\n\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="payload SHA-256 mismatch"):
        aggregate(
            input_root,
            tmp_path / "report",
            "12345",
            minimum=1,
            expected_domains={"chemistry"},
        )
