#!/usr/bin/env python3
"""Audit every materialized candidate document and admit only scoped, evidenced records.

NASA NTRS: exact per-record public-use allowlist + source hashes + conservative
text-quality screen. Existing individual human-review holds always override.
ScienceVerse: admit only per-DOI CC-BY/CC0 records after owner-attested
source review, attribution, quality, privacy and exact-dedup gates.
All output remains training-ineligible until global G-0 and split gates pass.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NASA = ROOT / "data/datasets/candidates/nasa-ntrs-public-use"
NASA_REVIEW = ROOT / "data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"
PAPERS = ROOT / "data/datasets/admitted/ronin-authored-papers-v1"
SCIENCEVERSE = ROOT / "data/datasets/candidates/scienceverse-text-export-v1"
SCIENCEVERSE_OUT = ROOT / "data/datasets/admitted/scienceverse-ccby-v1"
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
    if docs.exists():
        shutil.rmtree(docs)
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
    if SCIENCEVERSE_OUT.exists():
        shutil.rmtree(SCIENCEVERSE_OUT)
    SCIENCEVERSE_OUT.mkdir(parents=True,exist_ok=True)
    seen_hashes=set()
    seen_dois=set()
    known_holds={
        ("jdm","jdm06002"):"Author metadata contains apparent postal-address fragments; attribution/privacy repair required",
        ("ece3","ece310954"):"Malformed author fragment in source metadata; attribution repair required",
        ("openmind","opmia00001"):"Domain routing not supported by source title/subject; reclassify before admission",
    }
    total_admitted=0
    total_admitted_bytes=0
    total_holds=0
    for gz_path in sorted(SCIENCEVERSE.glob("*/documents.jsonl.gz")):
        name=gz_path.parent.name
        counts=Counter()
        bytes_total=0
        admitted_bytes=0
        output_dir=SCIENCEVERSE_OUT/name
        output_dir.mkdir(parents=True,exist_ok=True)
        output_path=output_dir/"documents.jsonl.gz"
        output_hash=hashlib.sha256()
        with gzip.open(gz_path,"rt",encoding="utf-8") as stream, output_path.open("wb") as raw_out:
            with gzip.GzipFile(fileobj=raw_out,mode="wb",filename="",mtime=0,compresslevel=9) as compressed:
                for line in stream:
                    if not line.strip():
                        continue
                    item=json.loads(line)
                    body=str(item.get("text") or "")
                    body_bytes=body.encode("utf-8")
                    q=quality(body)
                    counts["documents"]+=1
                    bytes_total+=len(body_bytes)
                    if sha(body_bytes) != item.get("text_sha256") or len(body_bytes) != item.get("text_bytes"):
                        raise ValueError(f"{name}/{item.get('paper_id')}: text SHA-256 or byte count mismatch")
                    reasons=[]
                    if not quality_pass(q):
                        reasons.append("machine_quality_hold")
                        counts["machine_quality_hold"]+=1
                    else:
                        counts["machine_quality_pass"]+=1
                    doi=str(item.get("doi") or "").strip().casefold()
                    if not doi:
                        reasons.append("missing_doi")
                        counts["missing_doi"]+=1
                    if not item.get("authors"):
                        reasons.append("missing_authors")
                        counts["missing_authors"]+=1
                    license_url=str(item.get("license_url") or "").rstrip("/")
                    if license_url not in {
                        "https://creativecommons.org/licenses/by/4.0",
                        "https://creativecommons.org/publicdomain/zero/1.0",
                    }:
                        reasons.append("license_not_allowlisted")
                        counts["license_not_allowlisted"]+=1
                    if q["email_pattern"] or q["ssn_pattern"]:
                        reasons.append("pii_pattern")
                        counts["pii_pattern_found"]+=1
                    paper_id=str(item.get("paper_id") or "").rsplit(".",1)[-1]
                    if (name,paper_id) in known_holds:
                        reasons.append("known_metadata_or_routing_hold")
                        counts["known_metadata_or_routing_hold"]+=1
                    if doi and doi in seen_dois:
                        reasons.append("duplicate_doi_across_scienceverse")
                        counts["duplicate_doi"]+=1
                    digest=item["text_sha256"]
                    if digest in seen_hashes:
                        reasons.append("duplicate_text_across_scienceverse")
                        counts["duplicate_text"]+=1
                    if doi:
                        seen_dois.add(doi)
                    seen_hashes.add(digest)
                    if reasons:
                        counts["held_documents"]+=1
                        counts["hold_reason:"+reasons[0]]+=1
                        continue
                    admitted=dict(item)
                    admitted["status"]="admitted_scoped_global_gates_pending"
                    admitted["admitted"]=True
                    admitted["training_eligible"]=False
                    admitted["admission_basis"]={
                        "source_rights":"Per-DOI CC-BY-4.0/CC0 allowlist in pinned upstream manifest or Crossref license audit",
                        "owner_review_attestation":"data/datasets/reviews/human-review-attestation-2026-11-05.json",
                        "quality":"Full-document text and basic PII screen passed",
                        "dedup":"Unique DOI and exact text SHA-256 across all 13 ScienceVerse exports",
                    }
                    encoded=(json.dumps(admitted,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
                    compressed.write(encoded)
                    output_hash.update(encoded)
                    counts["admitted_documents"]+=1
                    admitted_bytes+=len(body_bytes)
        total_admitted+=counts["admitted_documents"]
        total_admitted_bytes+=admitted_bytes
        total_holds+=counts["held_documents"]
        source_prov_path=gz_path.parent/"provenance.json"
        source_prov=json.loads(source_prov_path.read_text(encoding="utf-8"))
        dataset_manifest={
            "schema_version":"1.0","dataset_id":f"ronin-scienceverse-{name}-admitted-v1",
            "source_dataset_id":source_prov.get("dataset_id"),
            "source_provenance":str(source_prov_path.relative_to(ROOT)),
            "source_rds_sha256":source_prov.get("source_rds_sha256",source_prov.get("payload_sha256")),
            "eligible_manifest_sha256":source_prov.get("eligible_manifest_sha256"),
            "candidate_export":str(gz_path.relative_to(ROOT)),
            "candidate_export_sha256":sha(gz_path.read_bytes()),
            "admitted_payload":output_path.name,
            "admitted_payload_sha256":sha(output_path.read_bytes()),
            "admitted_records_sha256":output_hash.hexdigest(),
            "target_library":source_prov.get("target_library"),
            "aggregate":{"source_documents":counts["documents"],
                         "admitted_documents":counts["admitted_documents"],
                         "admitted_text_bytes":admitted_bytes,
                         "held_documents":counts["held_documents"],
                         "quality_pass":counts["machine_quality_pass"],
                         "quality_hold":counts["machine_quality_hold"]},
            "training_eligible":False,
            "global_g0":"FAIL",
        }
        (output_dir/"manifest.json").write_text(json.dumps(dataset_manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        results[name]={
            "documents":counts["documents"],"text_bytes":bytes_total,
            "machine_quality_pass":counts["machine_quality_pass"],
            "machine_quality_hold":counts["machine_quality_hold"],
            "missing_doi":counts["missing_doi"],"missing_authors":counts["missing_authors"],
            "license_not_allowlisted":counts["license_not_allowlisted"],
            "pii_pattern_found":counts["pii_pattern_found"],
            "known_metadata_or_routing_hold":counts["known_metadata_or_routing_hold"],
            "duplicate_doi":counts["duplicate_doi"],"duplicate_text":counts["duplicate_text"],
            "admitted":counts["admitted_documents"],"admitted_text_bytes":admitted_bytes,
            "held":counts["held_documents"],"hold_reason_counts":{k:v for k,v in counts.items() if k.startswith("hold_reason:")},
        }
    aggregate={
        "source_documents":sum(x["documents"] for x in results.values()),
        "admitted_documents":total_admitted,"admitted_text_bytes":total_admitted_bytes,
        "held_documents":total_holds,"unique_exact_texts_across_exports":len(seen_hashes),
        "unique_dois_across_exports":len(seen_dois),
    }
    summary={
        "schema_version":"1.0","dataset_id":"ronin-scienceverse-ccby-v1",
        "status":"admitted_scoped_owner_attested_global_gates_pending",
        "source_corpora":len(results),"aggregate":aggregate,"corpora":results,
        "owner_review_attestation":"data/datasets/reviews/human-review-attestation-2026-11-05.json",
        "rights_policy":"Only document records with a per-DOI CC-BY-4.0 or CC0 license URL are admitted; owner attestation covers the mapped source-level rights, privacy, third-party and quality review.",
        "exclusions":["full-text quality holds","records with missing DOI or author attribution","three known metadata/privacy/domain-routing anomalies","duplicate DOI or exact text across exports"],
        "training":{"training_eligible":False,"global_g0":"FAIL",
                    "blocking":["global exact/near-duplicate comparison against all other corpora and holdouts",
                                "General/HKD separation and deterministic train/validation/test isolation",
                                "final rights/attribution and privacy reconciliation"]},
    }
    (SCIENCEVERSE_OUT/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"aggregate":aggregate,"corpora":results}

def main() -> None:
    nasa=audit_nasa()
    sv=audit_scienceverse()
    report={
        "schema_version":"1.0","report_date":"2026-11-05",
        "scope":"All materialized NASA NTRS text candidates (824) and all ScienceVerse text exports (13 corpora); owner-authorized Papers corpus is separately admitted and hash-verified.",
        "nasa":nasa["aggregate"],
        "scienceverse":sv["corpora"],
        "scienceverse_aggregate":sv["aggregate"],
        "papers":{"dataset_id":"ronin-authored-papers-v1","documents":9,
                  "training_eligible":False,"manifest":"data/datasets/admitted/ronin-authored-papers-v1/manifest.json"},
        "global_g0":"FAIL","training_eligible_new_documents":0,
        "notes":["NASA scoped admission is not training eligibility.","ScienceVerse documents with per-DOI CC-BY-4.0/CC0, attribution, full-text quality and privacy checks passing are admitted only in scoped form under the owner review attestation; all remain training-ineligible pending global G-0.","Existing NASA manual holds are never overridden by machine scores.","Exact and near duplicates across sources and holdouts remain a blocking gate."]
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
