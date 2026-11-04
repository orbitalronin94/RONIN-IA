#!/usr/bin/env python3
"""Fetch pinned GPLSI ClearText CAS/VAL JSON files into a rights-review candidate.

The BOE declares the dataset collections CC BY 4.0 and identifies UA-GPLSI,
but individual embedded source documents can carry separate rights. This
adapter verifies Git blob hashes, extracts page text, and quarantines explicit
NC/ND/all-rights-reserved notices. Nothing is admitted automatically.
"""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ADAPTER_VERSION = "1.0.1"
SOURCES = {
    "cas": {
        "repo": "gplsi/corpus-cleartext-cas-v1.0",
        "commit": "fdab13b97a8e6be1dae09f41d7082dd6eb61004e",
        "language": "es",
    },
    "val": {
        "repo": "gplsi/corpus-cleartext-val-v1.0",
        "commit": "860507c8cd4f134f0f67a44dffba0f32eee7fef7",
        "language": "ca",
    },
}
BOE = "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-12053"
UA = "RONIN-IA-GPLSI-ClearText-auditor/1.0"
RESTRICTIVE = [
    "cc by-nc", "cc-by-nc", "cc by-nd", "cc-by-nd",
    "non-commercial", "noncommercial", "sin obra derivada",
    "no comercial", "all rights reserved", "todos los derechos reservados",
]
COPYRIGHT = re.compile(r"(?i)(?:©|copyright|derechos reservados)")

def fetch(url: str, limit: int = 8 * 1024 * 1024) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"file exceeds limit: {url}")
    return data

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def get_field(obj, *keys):
    for key in keys:
        if key in obj:
            return obj[key]
    return None

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("artifacts/gplsi-cleartext"))
    p.add_argument("--max-file-mib", type=int, default=8)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()
    summaries, review = {}, []
    for name, src in SOURCES.items():
        repo, commit = src["repo"], src["commit"]
        tree_url = f"https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1"
        tree_raw = fetch(tree_url, 8 * 1024 * 1024)
        tree = json.loads(tree_raw)
        if tree.get("truncated"):
            raise RuntimeError(f"Git tree truncated for {repo}")
        files = [x for x in tree.get("tree", []) if x.get("type") == "blob" and x.get("path", "").startswith("data/") and x.get("path", "").endswith(".json")]
        out = a.out / f"gplsi-cleartext-{name}.jsonl"
        seen = set()
        exported = excluded = 0
        with out.open("w", encoding="utf-8") as dst:
            for item in files:
                path = item["path"]
                raw_url = f"https://raw.githubusercontent.com/{repo}/{commit}/" + urllib.parse.quote(path, safe="/")
                raw = fetch(raw_url, a.max_file_mib * 1024 * 1024)
                actual_blob = git_blob_sha(raw)
                if actual_blob != item["sha"]:
                    raise ValueError(f"Git blob SHA mismatch for {repo}/{path}: {actual_blob} != {item['sha']}")
                obj = json.loads(raw)
                title = get_field(obj, "title", "Títol", "titulo", "title")
                version = get_field(obj, "version", "Versió", "version")
                source_url = get_field(obj, "url", "Url", "URL")
                easy_read = bool(get_field(obj, "lf", "LF"))
                pages = get_field(obj, "document", "Document", "pages") or []
                page_texts = []
                for page in pages:
                    if isinstance(page, dict):
                        value = get_field(page, "text", "Text", "content", "Content", "Texto", "texto", "Contenido", "Contingut")
                        if value:
                            page_texts.append(str(value))
                text = "\n".join(page_texts).strip()
                low = text.lower()
                markers = [m for m in RESTRICTIVE if m in low]
                if markers:
                    excluded += 1
                    review.append({"repo": repo, "commit": commit, "path": path, "title": title, "source_url": source_url, "decision": "quarantine_explicit_restrictive_notice", "markers": markers, "file_git_blob_sha1": actual_blob, "file_sha256": sha(raw)})
                    continue
                if not text:
                    review.append({"repo": repo, "commit": commit, "path": path, "title": title, "source_url": source_url, "decision": "quarantine_empty_text", "file_git_blob_sha1": actual_blob, "file_sha256": sha(raw)})
                    excluded += 1
                    continue
                text_sha = sha(text.encode("utf-8"))
                if text_sha in seen:
                    continue
                seen.add(text_sha)
                dst.write(json.dumps({
                    "text": text,
                    "language": src["language"],
                    "title": title,
                    "version": version,
                    "easy_read": easy_read,
                    "source_url": source_url,
                    "source_repo": repo,
                    "source_commit": commit,
                    "source_path": path,
                    "source_file_git_blob_sha1": actual_blob,
                    "source_file_sha256": sha(raw),
                    "text_sha256": text_sha,
                    "copyright_notice_present": bool(COPYRIGHT.search(text)),
                    "license_id_claimed_for_collection": "CC-BY-4.0",
                }, ensure_ascii=False, sort_keys=True) + "\n")
                exported += 1
                review.append({"repo": repo, "commit": commit, "path": path, "title": title, "source_url": source_url, "decision": "candidate_pending_item_level_rights_review", "copyright_notice_present": bool(COPYRIGHT.search(text)), "file_git_blob_sha1": actual_blob, "file_sha256": sha(raw)})
        summaries[name] = {
            "repo": repo, "commit": commit, "tree_sha": tree.get("sha"),
            "tree_response_sha256": sha(tree_raw), "files_scanned": len(files),
            "candidate_documents": exported, "quarantined_documents": excluded,
            "payload_path": out.name, "payload_bytes": out.stat().st_size,
            "payload_sha256": sha(out.read_bytes()), "language": src["language"],
            "collection_license_claim": "CC-BY-4.0",
            "rights_evidence": BOE,
        }
    manifest = {
        "retrieved_at": retrieved,
        "status": "candidate_only",
        "training_eligible": False,
        "admission_eligible": False,
        "rights_policy": "BOE collection declaration is not treated as a substitute for per-document source-rights review",
        "sources": summaries,
        "rights_evidence": BOE,
    }
    (a.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (a.out / "rights-review-queue.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": summaries, "review_items": len(review), "status": "candidate_only"}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
