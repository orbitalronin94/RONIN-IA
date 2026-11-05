#!/usr/bin/env python3
"""Acquire ScienceVerse eLife/Frontiers rows only when Crossref records CC-BY-4.0."""
from __future__ import annotations
import concurrent.futures
import csv
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT=pathlib.Path("data/datasets/candidates/scienceverse-crossref-verified")
REV="3a6ac0125e576423300a8996e9ad4c5d65ef9fe2"
BASE=f"https://raw.githubusercontent.com/scienceverse/papers/{REV}"
CORPORA={
 "elife":{"tag":"elife-2026-06-21","expected_catalog":1000,"target":"biology_general","release":"https://github.com/scienceverse/papers/releases/download/elife-2026-06-21/elife.rds"},
 "frontiers":{"tag":"frontiers-2026-06-21","expected_catalog":1000,"target":"social_sciences_general","release":"https://github.com/scienceverse/papers/releases/download/frontiers-2026-06-21/frontiers.rds"},
 "plosbio":{"tag":"plosbio-2026-06-19","expected_catalog":1000,"target":"biology_general","release":"https://github.com/scienceverse/papers/releases/download/plosbio-2026-06-19/plosbio.rds"},
 "plosmed":{"tag":"plosmed-2026-06-19","expected_catalog":1000,"target":"medicine_health_general","release":"https://github.com/scienceverse/papers/releases/download/plosmed-2026-06-19/plosmed.rds"},
 "plosone":{"tag":"plosone-2026-06-20","expected_catalog":1000,"target":"biology_general","release":"https://github.com/scienceverse/papers/releases/download/plosone-2026-06-20/plosone.rds"},
 "scan":{"tag":"scan-2026-06-21","expected_catalog":803,"target":"social_sciences_general","release":"https://github.com/scienceverse/papers/releases/download/scan-2026-06-21/scan.rds"},
 "ece3":{"tag":"ece3-2026-06-21","expected_catalog":1543,"target":"biology_general","release":"https://github.com/scienceverse/papers/releases/download/ece3-2026-06-21/ece3.rds"},
}
UA="RONIN-IA/1.0 dataset-rights-preflight (+https://github.com/orbitalronin94/RONIN-IA)"
def fetch(url, attempts=6):
 last=None
 for n in range(attempts):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json,text/csv,*/*"})
   with urllib.request.urlopen(req,timeout=90) as r:return r.read()
  except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
   last=e
   if isinstance(e,urllib.error.HTTPError) and e.code not in {429,500,502,503,504}:raise
   time.sleep(min(2**n,30))
 raise RuntimeError(f"request failed: {url}") from last
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def crossref_check(doi):
 url="https://api.crossref.org/works/"+urllib.parse.quote(doi,safe="")
 try:
  data=json.loads(fetch(url).decode("utf-8"))
  licenses=(data.get("message") or {}).get("license") or []
  urls=[str(x.get("URL") or x.get("url") or "") for x in licenses]
  approved_urls=[u for u in urls if u.rstrip("/").lower().endswith("/licenses/by/4.0") or "/publicdomain/zero/1.0" in u.rstrip("/").lower()]
  approved=bool(approved_urls)
  return doi,{"doi":doi,"crossref_url":url,"license_urls":urls,"confirmed_license_urls":approved_urls,"cc_by_4_0_or_cc0_confirmed":approved,"status":"confirmed" if approved else "not_confirmed"}
 except Exception as e:
  return doi,{"doi":doi,"crossref_url":url,"license_urls":[],"cc_by_4_0_confirmed":False,"status":"lookup_error","error":type(e).__name__}
def main():
 total=0
 for name,meta in CORPORA.items():
  dest=ROOT/name;dest.mkdir(parents=True,exist_ok=True)
  manifest=dest/"manifest.csv";geturl=f"{BASE}/{name}/manifest.csv"
  manifest.write_bytes(fetch(geturl))
  with manifest.open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
  base=[];excluded=[]
  for row in rows:
   doi=(row.get("doi") or "").strip()
   reasons=[]
   if not doi:reasons.append("missing_doi")
   source_license=(row.get("license") or "").strip().casefold()
   if name in {"elife","frontiers","scan","ece3"} and source_license!="cc-by":
    reasons.append("upstream_license_not_cc-by")
   if name.startswith("plos") and source_license!="cc-by 4.0 or cc0":
    reasons.append("upstream_license_scope_not_expected")
   for field in ("pdf_exists","xml_exists","in_rds"):
    if field in row and row[field].strip().upper()!="TRUE":reasons.append(field+"_false")
   if reasons:excluded.append({"doi":doi or None,"title":row.get("title"),"reasons":reasons})
   else:base.append(row)
  dois=list(dict.fromkeys(x["doi"].strip() for x in base))
  audit={}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   for doi,result in pool.map(crossref_check,dois):
    audit[doi]=result
  approved=[x for x in base if audit.get(x["doi"].strip(),{}).get("cc_by_4_0_or_cc0_confirmed")]
  rejected=[x for x in base if not audit.get(x["doi"].strip(),{}).get("cc_by_4_0_confirmed")]
  for x in rejected:
   excluded.append({"doi":x.get("doi"),"title":x.get("title"),"reasons":["crossref_does_not_confirm_CC-BY-4.0"]})
  groups={}
  for x in approved:
   x["crossref_verified_license"]=";".join(audit.get(x["doi"].strip(),{}).get("confirmed_license_urls",[]))
   groups.setdefault(x["doi"].strip().casefold(),[]).append(x)
  unique=[]
  for doi,group in groups.items():
   titles={str(x.get("title") or "").strip().casefold() for x in group}
   if len(titles)>1:
    for x in group:excluded.append({"doi":x.get("doi"),"title":x.get("title"),"reasons":["doi_maps_to_conflicting_titles"]})
   else:
    unique.append(group[0])
    for x in group[1:]:excluded.append({"doi":x.get("doi"),"title":x.get("title"),"reasons":["duplicate_manifest_row_same_doi_title"]})
  if not unique:raise SystemExit(f"{name}: no DOI had an exact Crossref CC-BY-4.0 license confirmation")
  eligible=dest/"eligible-manifest.csv"
  with eligible.open("w",encoding="utf-8",newline="") as out:
   writer=csv.DictWriter(out,fieldnames=list(unique[0].keys()));writer.writeheader();writer.writerows(unique)
  (dest/"crossref-license-audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
  (dest/"excluded.json").write_text(json.dumps(excluded,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  payload=dest/(name+".rds");payload.write_bytes(fetch(meta["release"]))
  if payload.stat().st_size<1_000_000:raise SystemExit(f"{name}: RDS payload unexpectedly small")
  record={
   "dataset_id":f"scienceverse-{name}-crossref-cc-by-4.0-v1","upstream":"https://github.com/scienceverse/papers",
   "upstream_revision":REV,"release_tag":meta["tag"],"manifest_url":geturl,"fulltext_payload_url":meta["release"],
   "manifest_rows":len(rows),"upstream_cc_by_rows":len(base),"crossref_confirmed_rows":len(approved),
   "unique_doi_documents":len(unique),"excluded_rows":len(excluded),"target_library":meta["target"],
   "crossref_audit_file":"crossref-license-audit.json","eligible_manifest_file":"eligible-manifest.csv",
   "payload_file":payload.name,"payload_bytes":payload.stat().st_size,"payload_sha256":sha(payload),
   "manifest_sha256":sha(manifest),"eligible_manifest_sha256":sha(eligible),
   "rights_scope":"Crossref deposit explicitly names CC BY 4.0 or CC0; still verify publisher page, attribution and third-party material before Level A",
   "status":"candidate_fulltext_acquired_pending_publisher_rights_privacy_quality_dedup",
   "training_eligible":False,
  }
  (dest/"provenance.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  total+=len(unique)
  print(f"{name}: manifest={len(rows)} upstream_cc_by={len(base)} crossref_confirmed={len(approved)} unique={len(unique)} excluded={len(excluded)} bytes={payload.stat().st_size}")
 print(f"VERIFIED_CANDIDATE_DOCS={total}")
if __name__=="__main__":main()
