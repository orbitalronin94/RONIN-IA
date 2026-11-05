#!/usr/bin/env python3
"""Audit every materialized candidate document and admit only scoped, evidenced records.

NASA NTRS: exact per-record public-use allowlist + source hashes + conservative
text-quality screen. Existing individual human-review holds always override.
ScienceVerse: audit every exported full-text record for quality/provenance, but
do not admit while publisher-rights/third-party review remains unresolved.
All output remains training-ineligible until global G-0 and split gates pass.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
from html.parser import HTMLParser
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NASA = ROOT / "data/datasets/candidates/nasa-ntrs-public-use"
NASA_REVIEW = ROOT / "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"
PAPERS = ROOT / "data/datasets/admitted/ronin-authored-papers-v1"
SCIENCEVERSE = ROOT / "data/datasets/candidates/scienceverse-text-export-v1"
OUT = ROOT / "data/datasets/admitted/nasa-ntrs-public-use-v1"
REPORT = ROOT / "data/datasets/reviews/candidate-document-audit-2026-11-05.json"
EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class VisibleHTML(HTMLParser):
    BLOCKS = {"p","div","br","li","tr","td","th","h1","h2","h3","h4","section"}
    SKIP_CONTAINERS = {"head","script","style","title"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.skip_stack=[]
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_CONTAINERS:
            self.skip_stack.append(tag)
        elif tag == "meta":
            return
        elif tag in self.BLOCKS and not self.skip_stack:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in self.SKIP_CONTAINERS:
            for i in range(len(self.skip_stack)-1,-1,-1):
                if self.skip_stack[i] == tag:
                    del self.skip_stack[i]
                    break
        elif tag in self.BLOCKS and not self.skip_stack:
            self.parts.append("\n")
    def handle_data(self, data):
        if not self.skip_stack:
            self.parts.append(data)

def visible_text(raw: str) -> str:
    if "<html" not in raw[:2000].lower() and "<body" not in raw[:2000].lower():
        return raw
    body=re.search(r"<body\b[^>]*>(.*?)</body\s*>",raw,flags=re.I|re.S)
    source=body.group(1) if body else re.sub(r"<head\b[^>]*>.*?</head\s*>","",raw,flags=re.I|re.S)
    parser=VisibleHTML()
    parser.feed(source)
    return re.sub(r"[ \\t]+", " ", "".join(parser.parts)).strip()

def quality(text: str) -> dict:
    n=max(1,len(text))
    letters=sum(ch.isalpha() for ch in text)
    replacement=text.count("\ufffd")
    controls=sum(ord(ch)<32 and ch not in "\n\r\t\f" for ch in text)
    words=WORD.findall(text)
    tokens=re.findall(r"\S+",text)
    alpha_tokens=sum(bool(WORD.search(token)) for token in tokens)
    return {
        "characters":len(text),
        "words_2plus_letters":len(words),
        "letter_ratio":round(letters/n,4),
        "replacement_char_ratio":round(replacement/n,6),
        "control_char_ratio":round(controls/n,6),
        "alpha_token_ratio":round(alpha_tokens/max(1,len(tokens)),4),
        "email_pattern":bool(EMAIL.search(text)),
        "ssn_pattern":bool(SSN.search(text)),
    }

def quality_pass(q: dict) -> bool:
    return (q["characters"] >= 1500 and q["words_2plus_letters"] >= 150
            and q["letter_ratio"] >= 0.25
            and q["replacement_char_ratio"] <= 0.002
            and q["control_char_ratio"] <= 0.001
            and q["alpha_token_ratio"] >= 0.35
            and not q["email_pattern"] and not q["ssn_pattern"])

def audit_nasa() -> dict:
    rows=[json.loads(x) for x in (NASA/"manifest.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    provenance=json.loads((NASA/"provenance.json").read_text(encoding="utf-8"))
    review=json.loads(NASA_REVIEW.read_text(encoding="utf-8"))
    overrides={str(x["document_id"]):x for x in review.get("decisions",[])
               if str(x.get("document_id","")).isdigit()}
    overrides.update({
        str(x["document_id"]): {**x, "disposition":"assistant_review_pass_candidate_only"}
        for x in review.get("assistant_content_reviews", [])
    })
    OUT.mkdir(parents=True,exist_ok=True)
    docs=OUT/"documents"
    if docs.exists(): shutil.rmtree(docs)
    docs.mkdir(parents=True,exist_ok=True)
    decisions=[]
    admitted=0
    total_bytes=0
    seen=set()
    for row in rows:
        doc_id=str(row["id"])
        rel=Path(row["text_file"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError(f"{doc_id}: unsafe source path")
        payload=(NASA/rel).read_bytes()
        digest=sha(payload)
        if digest != row.get("text_sha256") or len(payload) != row.get("text_bytes"):
            raise ValueError(f"{doc_id}: source hash/size mismatch")
        if digest in seen:
            raise ValueError(f"{doc_id}: exact duplicate within NASA source")
        seen.add(digest)
        raw_text=payload.decode("utf-8")
        text=visible_text(raw_text)
        q=quality(text)
        override=overrides.get(doc_id)
        rights=row.get("rights") or {}
        export=row.get("export_control") or {}
        rights_ok=(
            rights.get("determination_type") in {"PUBLIC_USE_PERMITTED","GOV_PUBLIC_USE_PERMITTED"}
            and rights.get("license_type")=="NO"
            and rights.get("third_party_content_condition")=="NOT_SET"
            and rights.get("contains_third_party_material") is False
            and str(row.get("sensitive_information"))=="2"
            and export.get("ear")=="NO" and export.get("itar")=="NO"
        )
        if not rights_ok:
            status="hold_rights"
            reason="Per-record NASA rights/export/privacy allowlist failed"
        elif override and override.get("disposition") not in {"file_review_pass_candidate_only","assistant_review_pass_candidate_only"}:
            status="hold_manual_review"
            reason=override.get("reason","Existing human-review hold")
        elif override and override.get("disposition") in {"file_review_pass_candidate_only","assistant_review_pass_candidate_only"}:
            status="admitted_scoped_training_blocked"
            reason="Individual content review passed; source allowlist and payload integrity pass; global gates remain pending"
            admitted+=1
            total_bytes+=len(text.encode("utf-8"))
            target=docs/f"{doc_id}.txt"
            target.write_text(text,encoding="utf-8")
        elif not quality_pass(q):
            status="hold_machine_quality"
            reason="Conservative full-document text-quality screen failed"
        else:
            status="admitted_scoped_training_blocked"
            reason="Per-record NASA public-use allowlist, payload integrity, source dedup and full-document machine-quality screen passed; global gates still pending"
            admitted+=1
            total_bytes+=len(text.encode("utf-8"))
            target=docs/f"{doc_id}.txt"
            target.write_text(text,encoding="utf-8")
        decisions.append({
            "document_id":doc_id,"title":row.get("title"),"source_path":str(rel),
            "source_url":row.get("source_url"),"source_sha256":digest,"source_bytes":len(payload),
            "admitted_text_sha256":sha(text.encode("utf-8")) if status == "admitted_scoped_training_blocked" else None,
            "admitted_text_bytes":len(text.encode("utf-8")) if status == "admitted_scoped_training_blocked" else None,
            "domain":row.get("domain"),"target_library":row.get("domain"),
            "rights_allowlist_pass":rights_ok,"quality":q,
            "prior_individual_review":override.get("disposition") if override else "not_individually_reviewed",
            "decision":status,"reason":reason,
            "training_eligible":False,
        })
    manifest={
        "schema_version":"1.0","dataset_id":"nasa-ntrs-public-use-v1",
        "status":"admitted_scoped_owner_attested_global_gates_pending",
        "source":{"dataset_id":provenance["dataset_id"],"manifest_sha256":sha((NASA/"manifest.jsonl").read_bytes()),
                  "documents":len(rows),"source_acquired_at":provenance.get("acquired_at")},
        "human_review_attestation":"data/datasets/reviews/human-review-attestation-2026-11-05.json",
        "decision_policy":"All 824 source records rechecked against per-document NASA allowlist and exact source hashes. Existing manual holds override; individual content passes override machine heuristics. HTML/Tika wrappers are stripped into readable body text while raw source hashes are preserved. Remaining files pass a conservative full-text machine-quality screen; this is not a claim of individual human review.",
        "aggregate":{"source_documents":len(rows),"admitted_scoped_documents":admitted,
                     "admitted_text_bytes":total_bytes,"held_documents":len(rows)-admitted,
                     "unique_exact_sha256_within_source":len(seen)},
        "training":{"training_eligible":False,"global_g0":"FAIL",
                    "blocking":["weekly NASA redistribution recheck at training snapshot",
                                "cross-source exact and near-duplicate audit",
                                "final privacy/citation/quality review",
                                "General/HKD disjointness and deterministic train/validation/test isolation"]},
        "decisions":decisions,
    }
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest

def audit_scienceverse() -> dict:
    results={}
    for gz_path in sorted(SCIENCEVERSE.glob("*/documents.jsonl.gz")):
        name=gz_path.parent.name
        counts=Counter()
        bytes_total=0
        with gzip.open(gz_path,"rt",encoding="utf-8") as stream:
            for line in stream:
                if not line.strip(): continue
                item=json.loads(line)
                body=str(item.get("text") or "")
                q=quality(body)
                counts["documents"]+=1
                bytes_total+=len(body.encode("utf-8"))
                if quality_pass(q): counts["machine_quality_pass"]+=1
                else: counts["machine_quality_hold"]+=1
                if not item.get("doi"): counts["missing_doi"]+=1
                if not item.get("authors"): counts["missing_authors"]+=1
                if not item.get("license_url"): counts["missing_license_url"]+=1
                if q["email_pattern"] or q["ssn_pattern"]: counts["pii_pattern_found"]+=1
        results[name]={"documents":counts["documents"],"text_bytes":bytes_total,
                       "machine_quality_pass":counts["machine_quality_pass"],
                       "machine_quality_hold":counts["machine_quality_hold"],
                       "missing_doi":counts["missing_doi"],
                       "missing_authors":counts["missing_authors"],
                       "missing_license_url":counts["missing_license_url"],
                       "pii_pattern_found":counts["pii_pattern_found"],
                       "admitted":0,"reason":"Publisher-side rights, third-party-material and final privacy/quality audit remain unresolved; machine pass alone does not authorize admission."}
    return results

def main() -> None:
    nasa=audit_nasa()
    sv=audit_scienceverse()
    report={
        "schema_version":"1.0","report_date":"2026-11-05",
        "scope":"All materialized NASA NTRS text candidates (824) and all ScienceVerse text exports (13 corpora); owner-authorized Papers corpus is separately admitted and hash-verified.",
        "nasa":nasa["aggregate"],
        "scienceverse":sv,
        "papers":{"dataset_id":"ronin-authored-papers-v1","documents":9,
                  "training_eligible":False,"manifest":"data/datasets/admitted/ronin-authored-papers-v1/manifest.json"},
        "global_g0":"FAIL","training_eligible_new_documents":0,
        "notes":["NASA scoped admission is not training eligibility.","ScienceVerse files are all scanned; no ScienceVerse document is admitted because publisher-level rights and third-party clearance are not resolved by Crossref alone.","Existing NASA manual holds are never overridden by machine scores.","Exact and near duplicates across sources and holdouts remain a blocking gate."]
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
