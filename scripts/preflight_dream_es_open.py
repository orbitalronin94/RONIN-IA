#!/usr/bin/env python3
"""Credential-free access preflight for Språkbanken DReaM-es-open via public Korp API.

This is a bounded access/shape check only. It does not bulk-harvest or admit the
corpus. If the endpoint requires BasicAuth, the workflow fails closed.
"""
from __future__ import annotations
import argparse, hashlib, json, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

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
    query_raw = get("/query", {
        "corpus": CORPUS,
        "cqp": '[word=".*"]',
        "start": 0,
        "end": max(0, a.sample_hits - 1),
        "default_context": "1 sentence",
        "default_within": "sentence",
        "show": "word",
        "show_struct": "text_author,text_title",
    })
    query = json.loads(query_raw)
    kwic = query.get("kwic", [])
    (a.out / "corpus-info.json").write_bytes(info_raw)
    (a.out / "sample-query.json").write_bytes(query_raw)
    manifest = {
        "source_id": "dream-es-open",
        "source_url": "https://spraakbanken.gu.se/en/resources/dream-es-open",
        "license_claim": "CC-BY-4.0",
        "license_evidence_url": "https://spraakbanken.gu.se/en/resources/dream-es-open",
        "api": BASE,
        "corpus_id": CORPUS,
        "corpus_info_sha256": sha(info_raw),
        "sample_query_sha256": sha(query_raw),
        "reported_corpus_info": match,
        "sample_hits_requested": a.sample_hits,
        "sample_hits_returned": len(kwic),
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
