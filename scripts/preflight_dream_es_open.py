#!/usr/bin/env python3
"""Credential-free access preflight for Språkbanken DReaM-es-open via public Korp API.

This is a bounded access/shape check only. It does not bulk-harvest or admit the
corpus. If the endpoint requires BasicAuth, the workflow fails closed.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ADAPTER_VERSION = "1.0.1"
BASE = "https://ws.spraakbanken.gu.se/ws/korp/v8"
CORPUS = "dream-es-open"
UA = "RONIN-IA-DReaM-preflight/1.0"

def get(path: str, params: dict, limit: int = 8 * 1024 * 1024) -> bytes:
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise RuntimeError(f"Korp endpoint requires authentication (HTTP {exc.code}); no credentials will be used") from exc
        raise
    if len(raw) > limit:
        raise ValueError("Korp response exceeded size limit")
    return raw

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/dream-preflight"))
    p.add_argument("--sample-hits", type=int, default=100)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    info_raw = get("/corpus_info", {"corpus": CORPUS})
    info = json.loads(info_raw)
    corpora = info.get("corpora", {})
    match = next((v for k,v in corpora.items() if k.lower() == CORPUS.lower()), None)
    if match is None:
        raise RuntimeError(f"Korp does not expose corpus {CORPUS}; available matching keys: {list(corpora)[:30]}")
    query_raw = get("/query_sample", {
        "corpus": CORPUS,
        "cqp": '[]+',
        "start": 0,
        "end": max(0, a.sample_hits - 1),
        "default_context": "1 sentence",
        "default_within": "sentence",
        "show": "word",
        "show_struct": "doc_author,doc_title,doc_lgcode,doc_year,page_page_url",
    })
    query = json.loads(query_raw)
    doc_meta_raw = get("/attr_values", {
        "corpus": CORPUS,
        "attr": "doc_author>doc_title>doc_lgcode>doc_year",
        "count": "true",
    })
    doc_meta = json.loads(doc_meta_raw)
    kwic = query.get("kwic", [])
    doc_tree = doc_meta.get("corpora", {}).get(CORPUS.upper(), {}).get("doc_author>doc_title>doc_lgcode>doc_year", {})
    document_rows = []
    for author, titles in doc_tree.items():
        for title, languages in titles.items():
            for described_language, years in languages.items():
                for year, token_count in years.items():
                    document_rows.append({
                        "author": author,
                        "title": title,
                        "described_language": described_language,
                        "year": year,
                        "token_count": token_count,
                        "source_corpus": CORPUS,
                    })
    document_index = b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\\n").encode("utf-8") for row in document_rows)
    (a.out / "documents-index.jsonl").write_bytes(document_index)
    sample_languages = {}
    sample_documents = {}
    for hit in kwic:
        structs = hit.get("structs", {})
        lang = str(structs.get("doc_lgcode", "unknown"))
        sample_languages[lang] = sample_languages.get(lang, 0) + 1
        title = str(structs.get("doc_title", "unknown"))
        sample_documents[title] = structs.get("page_page_url", "")
    (a.out / "corpus-info.json").write_bytes(info_raw)
    (a.out / "sample-query.json").write_bytes(query_raw)
    (a.out / "document-attributes.json").write_bytes(doc_meta_raw)
    manifest = {
        "source_id": "dream-es-open",
        "source_url": "https://spraakbanken.gu.se/en/resources/dream-es-open",
        "license_claim": "CC-BY-4.0",
        "license_evidence_url": "https://spraakbanken.gu.se/en/resources/dream-es-open",
        "api": BASE,
        "corpus_id": CORPUS,
        "corpus_info_sha256": sha(info_raw),
        "sample_query_sha256": sha(query_raw),
        "document_attributes_sha256": sha(doc_meta_raw),
        "reported_corpus_info": match,
        "sample_hits_requested": a.sample_hits,
        "sample_hits_returned": len(kwic),
        "sample_document_language_counts": sample_languages,
        "sample_document_sources": sample_documents,
        "document_attributes_response_keys": list(doc_meta.keys()),
        "document_index_rows": len(document_rows),
        "document_index_sha256": sha(document_index),
        "total_query_hits": query.get("hits"),
        "reported_tokens": match.get("tokens"),
        "reported_sentences": match.get("sentences"),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "status": "access_preflight_only",
        "training_eligible": False,
        "admission_eligible": False,
        "notes": "No credentials used. This does not establish permission to bulk-download, source-level rights, or full corpus export."
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"corpus": CORPUS, "sample_hits": len(kwic), "status": "preflight_only"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
