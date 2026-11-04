import hashlib
import json
from pathlib import Path

from ronin.retrieval import PortfolioRetriever
from scripts.build_portfolio_rag_index import build


def test_portfolio_index_is_retrieval_only_and_cites_source(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "index"
    source.mkdir()
    text = (
        "La epistemología estudia el conocimiento, sus fuentes y sus límites. "
        "Una afirmación falsable permite especificar qué observación podría refutarla. "
    ) * 8
    document = {
        "source_path": "Papers/epistemologia.md",
        "source_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source_revision": "a" * 40,
        "text": text,
    }
    documents_path = source / "documents.jsonl"
    documents_path.write_text(json.dumps(document, ensure_ascii=False) + "\n", encoding="utf-8")
    source_manifest = {
        "retrieval_only": True,
        "training_eligible": False,
        "source_repository": "orbitalronin94/Portfolio",
        "source_revision": "a" * 40,
        "documents_jsonl_sha256": hashlib.sha256(documents_path.read_bytes()).hexdigest(),
    }
    (source / "manifest.json").write_text(json.dumps(source_manifest), encoding="utf-8")

    manifest = build(source, output)
    assert manifest["role"] == "retrieval_only_fallback"
    assert manifest["training_eligible"] is False
    retriever = PortfolioRetriever(output / "portfolio.sqlite3")
    assert retriever.retrieve_if_uncertain("falsable conocimiento", 0.2) == []
    hits = retriever.retrieve_if_uncertain("afirmación falsable", 0.9)
    assert hits
    assert hits[0]["source_path"] == "Papers/epistemologia.md"
    assert hits[0]["source_sha256"] == document["source_sha256"]
