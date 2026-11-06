#!/usr/bin/env python3
"""Acquire and classify candidate text from BNE/BDH and USGS, plus metadata preflights.

No document is made training-eligible here. The BNE payload is limited to the
official public-domain collection. USGS records are candidates only until
document-level authorship/third-party review. Outputs are JSONL + audit JSON.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, io, json, re, sys, time, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

UA = "RONIN-IA-corpus-acquisition/1.0 (open research corpus; contact via repository)"
BNE_TXT = "https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_txt.zip"
BNE_CSV = "https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_csv-utf8.zip"
USGS_API = "https://pubs.usgs.gov/pubs-services/publication/"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)

def get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def clean_text(raw: bytes) -> tuple[str, dict]:
    decoded = raw.decode("utf-8", errors="replace")
    replacement = decoded.count("\ufffd")
    text = decoded.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip()
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    alpha = sum(ch.isalpha() for ch in text)
    ratio = alpha / max(1, len(text))
    return text, {"characters":len(text), "words":len(words), "replacement_chars":replacement, "alpha_ratio":round(ratio,4)}

def pii_or_low_quality(text: str, stats: dict, minimum: int) -> list[str]:
    reasons=[]
    if len(text.encode("utf-8")) < minimum: reasons.append("too_short")
    if stats["replacement_chars"] > max(5, stats["characters"] // 500): reasons.append("encoding_corruption")
    if stats["alpha_ratio"] < 0.35: reasons.append("low_text_density")
    if EMAIL.search(text): reasons.append("email_pattern")
    if SSN.search(text): reasons.append("ssn_pattern")
    if len(re.findall(r"\b(?:lorem ipsum|page intentionally left blank|table of contents)\b", text, re.I)) > 20:
        reasons.append("boilerplate_heavy")
    return reasons

def record(source, source_id, title, url, license_name, evidence, raw, min_bytes, extra=None):
    text, stats = clean_text(raw)
    reasons = pii_or_low_quality(text, stats, min_bytes)
    payload = text.encode("utf-8")
    return {
        "schema_version":1, "source":source, "source_id":str(source_id),
        "title":str(title or source_id)[:1000], "source_url":url,
        "license":license_name, "rights_evidence":evidence,
        "retrieved_at":datetime.now(timezone.utc).isoformat(),
        "raw_sha256":sha(raw), "text_sha256":sha(payload),
        "text_bytes":len(payload), "quality":stats,
        "classification":"rejected_quality_or_privacy" if reasons else "candidate_rights_review",
        "rejection_reasons":reasons, "training_eligible":False,
        "partition":"unassigned_pending_global_dedup",
        "text":text, **(extra or {})
    }

def bne(out, limit, min_bytes):
    print("BNE: downloading official public-domain TXT distribution", flush=True)
    raw=get(BNE_TXT)
    z=zipfile.ZipFile(io.BytesIO(raw))
    rows=[]
    for info in z.infolist():
        if info.is_dir() or not info.filename.lower().endswith((".txt",".text")): continue
        if len(rows)>=limit: break
        try:
            data=z.read(info)
            if not data: continue
            rows.append(record("BNE-BDH-public-domain", info.filename, Path(info.filename).stem,
                BNE_TXT, "CC-BY-4.0; source collection explicitly limited to public-domain works",
                "Official Datos.gob.es BDH public-domain collection; CC-BY-4.0 attribution; per-item membership inherited from this restricted distribution",
                data, min_bytes, {"attribution":"Biblioteca Nacional de España (BNE)","distribution_updated":"2024-12-04"}))
        except Exception as exc:
            print(f"BNE skipped {info.filename}: {exc}", file=sys.stderr)
    return rows, {"archive_sha256":sha(raw),"archive_bytes":len(raw),"zip_entries":len(z.infolist()),"text_records":len(rows),"distribution":BNE_TXT}

def usgs(limit, min_bytes):
    rows=[]; page=1; seen=set(); pages=0
    while len(rows)<limit and pages<max(1,(limit+49)//50):
        params=urllib.parse.urlencode({"page_size":min(50,limit-len(rows)),"page_number":page,"mimeType":"json"})
        url=USGS_API+"?"+params
        try: payload=json.loads(get(url))
        except Exception as exc:
            print(f"USGS API stop at page {page}: {exc}",file=sys.stderr); break
        items=payload if isinstance(payload,list) else payload.get("publications",payload.get("results",payload.get("data",[])))
        if isinstance(items,dict): items=items.get("publications",[])
        if not isinstance(items,list) or not items: break
        pages+=1
        for item in items:
            if not isinstance(item,dict): continue
            ident=str(item.get("id") or item.get("publicationId") or item.get("doi") or item.get("title") or "")
            if not ident or ident in seen: continue
            seen.add(ident)
            title=item.get("title") or item.get("citation") or ident
            values=json.dumps(item,ensure_ascii=False)
            links=URL_RE.findall(values)
            pdf=next((u.rstrip(".,)") for u in links if "pubs.usgs.gov" in u.lower() and ".pdf" in u.lower()),None)
            authors=json.dumps(item.get("authors",item.get("author","")),ensure_ascii=False).lower()
            pubtype=str(item.get("publicationType") or item.get("type") or "").lower()
            publisher=str(item.get("publisher") or item.get("contributingOffice") or "").lower()
            # Require a USGS-hosted PDF and a USGS report/publication indicator.
            usgs_owned=("usgs" in publisher or "u.s. geological survey" in authors or
                        any(term in str(item.get("seriesTitle","")).lower() for term in ("scientific investigations","open-file report","professional paper","circular","water-resources")))
            reportish=any(term in (pubtype+" "+str(item.get("seriesTitle","")).lower()) for term in ("report","professional paper","circular","scientific investigations","open-file"))
            if not pdf or not usgs_owned or not reportish:
                continue
            try:
                data=get(pdf)
                # PDF extraction is delegated to pdftotext installed by the workflow.
                import subprocess, tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                    f.write(data); f.flush()
                    import os
                    result=subprocess.run(["pdftotext","-layout",f.name,"-"],capture_output=True,check=True)
                raw=result.stdout
                rows.append(record("USGS-Publications-Warehouse",ident,title,pdf,
                    "USGS public domain only; candidate pending third-party-content audit",
                    "Official USGS FAQ: USGS-authored/produced information is public domain; publication record must still be checked for third-party figures/text",
                    raw,min_bytes,{"metadata":item,"pdf_sha256":sha(data),"publisher_or_author_gate":"passed_heuristic_pending_human_review"}))
            except Exception as exc:
                print(f"USGS document skipped {ident}: {exc}",file=sys.stderr)
        page+=1
        time.sleep(0.4)
    return rows, {"pages":pages,"metadata_records_seen":len(seen),"text_records":len(rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="data/datasets/candidates/public-sources-2026-11-06")
    p.add_argument("--limit-per-source",type=int,default=250)
    p.add_argument("--min-text-bytes",type=int,default=1500)
    p.add_argument("--skip-bne",action="store_true")
    p.add_argument("--skip-usgs",action="store_true")
    a=p.parse_args()
    if not 1<=a.limit_per_source<=5000: raise SystemExit("--limit-per-source must be 1..5000")
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    manifest=out/"manifest.jsonl"
    existing=set()
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8").splitlines():
            try: existing.add(json.loads(line)["text_sha256"])
            except Exception: pass
    new=[]; audit={"generated_at":datetime.now(timezone.utc).isoformat(),"sources":{}}
    if not a.skip_bne:
        try:
            rows,meta=bne(out,a.limit_per_source,a.min_text_bytes); audit["sources"]["bne"]=meta; new.extend(rows)
        except Exception as exc: audit["sources"]["bne"]={"error":f"{type(exc).__name__}: {exc}"}
    if not a.skip_usgs:
        try:
            rows,meta=usgs(a.limit_per_source,a.min_text_bytes); audit["sources"]["usgs"]=meta; new.extend(rows)
        except Exception as exc: audit["sources"]["usgs"]={"error":f"{type(exc).__name__}: {exc}"}
    dedup=[]; seen=set(existing)
    for row in new:
        if row["text_sha256"] in seen: continue
        seen.add(row["text_sha256"]); dedup.append(row)
    with manifest.open("a",encoding="utf-8") as f:
        for row in dedup:
            f.write(json.dumps(row,ensure_ascii=False)+"\n")
    audit.update({"new_records":len(dedup),"new_candidate_text_bytes":sum(x["text_bytes"] for x in dedup),
        "quality_rejected":sum(x["classification"]=="rejected_quality_or_privacy" for x in dedup),
        "rights_review_pending":sum(x["classification"]=="candidate_rights_review" for x in dedup),
        "training_eligible":0,"deduplicated_against_existing":len(new)-len(dedup),
        "manifest":"manifest.jsonl"})
    (out/"acquisition-audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit,ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
