import json
import subprocess
import sys

from scripts.select_knowledge_dense_corpus import DOMAIN_TERMS, score_record


def test_high_knowledge_score_rewards_domain_specific_definitions_and_relations():
    text = (
        "In mathematics, a theorem is defined as a proposition proven from axioms. "
        "If a matrix is invertible, then its determinant is nonzero. "
        "The proof follows by contradiction and uses the equation det(A) != 0."
    )
    scores = score_record(text, "mathematics", {}, 100)
    assert scores["domain_relevance"] > 0
    assert scores["knowledge_density"] > 0
    assert scores["specificity"] > 0
    assert 0 <= scores["semantic_density"] <= 100


def test_unknown_domain_is_not_silently_accepted():
    assert len(DOMAIN_TERMS) == 16


def test_selector_rejects_sources_without_explicit_legal_approval(tmp_path):
    source = tmp_path / "source.jsonl"
    text = (
        "In physics, energy is defined as the capacity to do work. "
        "If a force acts over a displacement, then work equals force times displacement. "
        "The equation W = F times d describes this relation. "
    ) * 5
    source.write_text(json.dumps({
        "text": text,
        "license": "UNKNOWN",
        "document_id": "paper-001",
    }) + "\n", encoding="utf-8")
    audit = tmp_path / "license-audit.json"
    audit.write_text(json.dumps({
        "candidate_intake_authorizations": [{
            "source_id": "fixture",
            "dataset_revision": "fixture-rev",
            "status": "LIMITED_PASS",
            "candidate_text_downloads_authorized": True,
            "training_eligible": False,
            "admitted": False,
            "allowed_licenses": ["CC-BY-4.0"],
        }]
    }), encoding="utf-8")
    spec = tmp_path / "sources.json"
    spec.write_text(json.dumps({
        "sources": [{
            "id": "fixture",
            "domain": "physics",
            "adapter": "jsonl",
            "path": str(source),
            "revision": "fixture-rev",
            "license_audit": str(audit),
            "allowed_licenses": ["CC-BY-4.0"],
            "license_field": "license",
            "text_field": "text",
            "provenance_field": "document_id",
            "enabled": True,
        }]
    }), encoding="utf-8")
    output = tmp_path / "physics" / "train.txt"
    report = tmp_path / "physics" / "report.json"
    result = subprocess.run([
        sys.executable, "scripts/select_knowledge_dense_corpus.py",
        "--source-spec", str(spec), "--domain", "physics",
        "--output", str(output), "--report", str(report),
    ], capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert not output.exists()
    assert json.loads(report.read_text(encoding="utf-8"))["status"] == "blocked_no_admitted_sources"

def test_selector_keeps_document_level_license_provenance_and_scores(tmp_path):
    source = tmp_path / "source.jsonl"
    text = (
        "In physics, energy is defined as the capacity to do work. "
        "If a force acts over a displacement, then work equals force times displacement. "
        "The equation W = F times d describes this relation. "
    ) * 5
    source.write_text(json.dumps({
        "text": text,
        "license": "CC-BY-4.0",
        "document_id": "paper-002",
    }) + "\n", encoding="utf-8")
    audit = tmp_path / "license-audit.json"
    audit.write_text(json.dumps({
        "candidate_intake_authorizations": [{
            "source_id": "fixture",
            "dataset_revision": "fixture-rev",
            "status": "LIMITED_PASS",
            "candidate_text_downloads_authorized": True,
            "training_eligible": False,
            "admitted": False,
            "allowed_licenses": ["CC-BY-4.0"],
        }]
    }), encoding="utf-8")
    spec = tmp_path / "sources.json"
    spec.write_text(json.dumps({
        "sources": [{
            "id": "fixture",
            "domain": "physics",
            "adapter": "jsonl",
            "path": str(source),
            "revision": "fixture-rev",
            "license_audit": str(audit),
            "allowed_licenses": ["CC-BY-4.0"],
            "license_field": "license",
            "text_field": "text",
            "provenance_field": "document_id",
            "enabled": True,
        }]
    }), encoding="utf-8")
    output = tmp_path / "physics" / "train.txt"
    report = tmp_path / "physics" / "report.json"
    result = subprocess.run([
        sys.executable, "scripts/select_knowledge_dense_corpus.py",
        "--source-spec", str(spec), "--domain", "physics",
        "--output", str(output), "--report", str(report),
        "--min-score", "0", "--top-percent", "100",
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    selected = json.loads(report.read_text(encoding="utf-8"))
    assert selected["selected_documents"] == 1
    assert selected["selected_bytes_utf8"] == output.stat().st_size
    sidecar = output.with_suffix(".manifest.jsonl")
    entry = json.loads(sidecar.read_text(encoding="utf-8").splitlines()[0])
    assert entry["license"] == "CC-BY-4.0"
    assert entry["provenance"] == "paper-002"
    assert entry["component_scores"]["semantic_density"] >= 0
