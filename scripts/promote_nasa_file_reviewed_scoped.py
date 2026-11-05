#!/usr/bin/env python3
"""Promote only the six individually reviewed NASA files after scoped gates pass."""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.parse, urllib.request
import numpy as np
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from collections import Counter

EMAIL = re.compile(rb"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
SSN = re.compile(rb"\b\d{3}-\d{2}-\d{4}\b")
TOKEN = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_+.-]{1,}|\d+(?:[.,]\d+)?|[=<>≤≥∑∫√∞→↔]")

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def tokens(text: str) -> list[str]: return [x.lower() for x in TOKEN.findall(text)]
def simhash(text: str) -> int:
    hashes=np.fromiter(
        (int.from_bytes(hashlib.blake2b(token.lower().encode(),digest_size=8).digest(),"big")
         for token in set(tokens(text))),
        dtype=np.uint64,
    )
    if not len(hashes): return 0
    bits=(hashes[:,None] >> np.arange(64,dtype=np.uint64)) & 1
    weights=bits.sum(axis=0,dtype=np.int64)*2-len(hashes)
    return sum(1<<i for i,value in enumerate(weights.tolist()) if value>=0)

def fetch_json(url: str) -> dict:
    req=urllib.request.Request(url,headers={"User-Agent":"RONIN-IA-corpus-recheck/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=45) as r: return json.loads(r.read().decode("utf-8"))
def api_recheck(ids: set[str]) -> dict:
    since=(date.today()-timedelta(days=7)).isoformat()
    query=urllib.parse.urlencode({"redistributedDate.gt":since,"page.size":100,"page.from":0})
    payload=fetch_json("https://ntrs.nasa.gov/api/citations/redistributions?"+query)
    rows=payload.get("results",payload.get("items",payload.get("redistributions",[])))
    if not isinstance(rows,list): raise RuntimeError("Unexpected NASA redistribution response schema")
    changed={str(x.get("id","")) for x in rows if isinstance(x,dict)}
    blocked=sorted(ids & changed)
    if blocked: raise RuntimeError(f"NASA records redistributed in last 7 days: {blocked}")
    checked=[]
    for doc_id in sorted(ids):
        item=fetch_json(f"https://ntrs.nasa.gov/api/citations/{doc_id}")
        copyright=item.get("copyright") or {}
        export=item.get("exportControl") or {}
        checks={
          "distribution_public": item.get("distribution")=="PUBLIC",
          "public_use_permitted": copyright.get("determinationType") in {"PUBLIC_USE_PERMITTED","GOV_PUBLIC_USE_PERMITTED"},
          "license_type_no": copyright.get("licenseType")=="NO",
          "no_third_party": copyright.get("containsThirdPartyMaterial") is False,
          "third_party_condition_clear": copyright.get("thirdPartyContentCondition")=="NOT_SET",
          "sensitive_information_none": str(item.get("sensitiveInformation"))=="2",
          "export_controls_no": export.get("ear")=="NO" and export.get("itar")=="NO",
        }
        if not all(checks.values()):
            raise RuntimeError(f"NASA current rights recheck failed for {doc_id}: {checks}")
        checked.append({"document_id":doc_id,"checks":checks})
    return {"checked_at_utc":datetime.now(timezone.utc).isoformat(),"redistribution_window_start":since,"redistributed_ids_checked":len(rows),"affected_ids":[],"records":checked}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--legacy-train-dir",type=Path,required=True)
    p.add_argument("--root",type=Path,default=Path("data/datasets/admitted/nasa-ntrs-file-reviewed-v1"))
    p.add_argument("--review",type=Path,default=Path("data/datasets/reviews/nasa-ntrs-file-review-2026-11-05.json"))
    p.add_argument("--source-manifest",type=Path,default=Path("data/datasets/admitted/nasa-ntrs-public-use-v1/manifest.json"))
    args=p.parse_args()
    manifest=json.loads((args.root/"manifest.json").read_text(encoding="utf-8"))
    records=[json.loads(x) for x in (args.root/"documents.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    review=json.loads(args.review.read_text(encoding="utf-8"))
    source=json.loads(args.source_manifest.read_text(encoding="utf-8"))
    review_by={str(x["document_id"]):x for x in review["decisions"]}
    source_by={str(x["document_id"]):x for x in source.get("decisions",[])}
    if len(records)!=6 or len(review_by)!=10: raise RuntimeError("Unexpected file-review inventory")
    # Re-verify the pinned 608-document train artifact and calculate comparison signatures.
    train=(args.legacy_train_dir/"train.txt").read_text(encoding="utf-8")
    sidecar=[json.loads(x) for x in (args.legacy_train_dir/"documents.train.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(sidecar)!=608: raise RuntimeError("Legacy train artifact is not the expected 608-document partition")
    legacy_hashes=set(); legacy_sigs=[]; cursor=0
    for row in sidecar:
        count=int(row.get("character_count",0))
        if count<=0: raise RuntimeError("Legacy train sidecar has invalid character_count")
        chunk=train[cursor:cursor+count]
        digest=sha(chunk.encode("utf-8"))
        if digest!=row.get("text_sha256"): raise RuntimeError("Legacy train document hash mismatch")
        legacy_hashes.add(digest)
        legacy_sigs.append((simhash(chunk),row.get("record_id")))
        cursor += count
        if train[cursor:cursor+2]=="\n\n": cursor += 2
    if cursor not in {len(train),len(train)-1}: raise RuntimeError("Legacy train payload has unindexed trailing content")
    selected=[]
    held_review_payload_mismatch=[]
    for row in records:
        doc_id=str(row["document_id"]); review_row=review_by.get(doc_id,{}); source_row=source_by.get(doc_id,{})
        if review_row.get("disposition")!="file_review_pass_candidate_only": raise RuntimeError(f"{doc_id}: not individually file-reviewed PASS")
        if review_row.get("content_review") not in {"PASS_WITH_OCR_NOISE","PASS_WITH_LAYOUT_NOISE"}: raise RuntimeError(f"{doc_id}: quality review not pass")
        if source_row.get("rights_allowlist_pass") is not True: raise RuntimeError(f"{doc_id}: source rights allowlist failed")
        payload=(args.root/"documents"/f"{doc_id}.txt").read_bytes()
        if sha(payload)!=row.get("sha256") or len(payload)!=row.get("bytes"): raise RuntimeError(f"{doc_id}: payload integrity mismatch")
        if sha(payload)!=review_row.get("text_sha256") or len(payload)!=review_row.get("text_bytes"):
            held_review_payload_mismatch.append({"document_id":doc_id,"reason":"Review attestation hash/byte count does not match the exact payload; excluded from training promotion."})
            continue
        if EMAIL.search(payload) or SSN.search(payload): raise RuntimeError(f"{doc_id}: sensitive pattern detected")
        digest=sha(payload)
        if digest in legacy_hashes: raise RuntimeError(f"{doc_id}: exact duplicate of legacy train")
        text=payload.decode("utf-8")
        signature=simhash(text)
        near=[other for other,_ in legacy_sigs if (signature^other).bit_count()<=3]
        if near: raise RuntimeError(f"{doc_id}: near-duplicate signature collision with legacy train")
        selected.append((doc_id,payload,row,review_row))
    if len(selected) < 2:
        raise RuntimeError(f"Fewer than two payloads exactly match their individual review attestations: {len(selected)}")
    ids={x[0] for x in selected}
    recheck=api_recheck(ids)
    # Stable train-only partition: all six are individually reviewed and remain outside validation/test.
    selected.sort(key=lambda x:x[0])
    train_payload=b"\n\n".join(x[1].rstrip(b"\n") for x in selected)+b"\n"
    docs=[]
    for doc_id,payload,row,review_row in selected:
        docs.append({"document_id":doc_id,"partition":"train","text_sha256":sha(payload),"bytes":len(payload),
          "title":review_row.get("verified_metadata",{}).get("title"),"source_url":review_row.get("ntrs_record"),
          "rights":"NASA NTRS record-level Public Use Permitted","content_review":review_row.get("content_review"),
          "source_revision":"NTRS live record rechecked at promotion"})
    (args.root/"train.txt").write_bytes(train_payload)
    (args.root/"documents.train.jsonl").write_text("".join(json.dumps(x,ensure_ascii=False,sort_keys=True)+"\n" for x in docs),encoding="utf-8")
    manifest.update({
      "status":"admitted_scoped_training_partition",
      "training_eligible":True,
      "counted_toward_level_a_minimum":False,
      "source_reviewed_documents":len(records),
      "documents":len(selected),
      "held_documents":len(held_review_payload_mismatch),
      "held_review_payload_mismatch":held_review_payload_mismatch,
      "utf8_bytes":sum(len(x[1]) for x in selected),
      "partitions":{"train":{"documents":len(selected),"bytes":len(train_payload),"sha256":sha(train_payload),"training_eligible":True},"validation":{"documents":0,"training_eligible":False},"test":{"documents":0,"training_eligible":False}},
      "global_gates":{"cross_source_exact_and_near_duplicate":"PASS_AGAINST_CURRENT_LEGACY_TRAIN_608","nasa_redistribution_recheck":"PASS","partition_isolation":"PASS_TRAIN_ONLY","global_g0":"FAIL"},
      "promotion_checks":{"legacy_train_documents_compared":len(sidecar),"exact_duplicates":0,"near_duplicate_hamming_le_3":0,"sensitive_patterns":0,"individually_reviewed_documents":len(selected),"review_payload_mismatches_held":len(held_review_payload_mismatch),"nasa_live_recheck":recheck},
      "scope_note":"Source-scoped train partition. This does not claim global G-0, does not enter the 64-library Level A inventory, and does not supersede NASA citation URLs."
    })
    (args.root/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"training_eligible_documents_added":len(selected),"utf8_bytes":sum(len(x[1]) for x in selected),"legacy_train_compared":len(chunks),"nasa_live_recheck":"PASS","global_g0":"FAIL"},indent=2))
if __name__=="__main__": main()
