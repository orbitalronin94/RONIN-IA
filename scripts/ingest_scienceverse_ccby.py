#!/usr/bin/env python3
"""Acquire fixed ScienceVerse full-text paperlists with per-article CC-BY audit."""
import csv, hashlib, json, pathlib, urllib.request, shutil

ROOT = pathlib.Path("data/datasets/candidates/scienceverse-fulltext")
CORPORA = {
    "bmcmed": {"tag":"bmcmed-2026-06-19","expected":1000,"target":"medicine_health_general","release":"https://github.com/scienceverse/papers/releases/download/bmcmed-2026-06-19/bmcmed.rds"},
    "jdm": {"tag":"jdm-2026-06-21","expected":855,"target":"social_sciences_general","release":"https://github.com/scienceverse/papers/releases/download/jdm-2026-06-21/jdm.rds"},
    "joc": {"tag":"joc-2026-06-20","expected":447,"target":"social_sciences_general","release":"https://github.com/scienceverse/papers/releases/download/joc-2026-06-20/joc.rds"},
    "openmind": {"tag":"openmind-2026-06-21","expected":293,"target":"philosophy_general","release":"https://github.com/scienceverse/papers/releases/download/openmind-2026-06-21/openmind.rds"},
}
UPSTREAM_REVISION = "3a6ac0125e576423300a8996e9ad4c5d65ef9fe2"
BASE = f"https://raw.githubusercontent.com/scienceverse/papers/{UPSTREAM_REVISION}"

def get(url, path):
    req = urllib.request.Request(url, headers={"User-Agent":"RONIN-IA-dataset-ingestion/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response, open(path,"wb") as out:
        while True:
            block=response.read(1024*1024)
            if not block: break
            out.write(block)

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def main():
    total=0
    for name, meta in CORPORA.items():
        dest=ROOT/name
        dest.mkdir(parents=True,exist_ok=True)
        manifest=dest/"manifest.csv"
        payload=dest/(name+".rds")
        get(f"{BASE}/{name}/manifest.csv",manifest)
        with manifest.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        # Some upstream manifests retain failed/inaccessible source rows.
        # Only rows with successful PDF+XML conversion are eligible when
        # those fields exist; other corpora already contain converted rows.
        converted=[]
        for row in rows:
            if row.get("license","").strip().upper()!="CC-BY 4.0":
                continue
            if "pdf_exists" in row and row["pdf_exists"].strip().upper()!="TRUE":
                continue
            if "xml_exists" in row and row["xml_exists"].strip().upper()!="TRUE":
                continue
            converted.append(row)
        if len(converted)!=meta["expected"]:
            raise SystemExit(f"{name}: expected {meta['expected']} converted CC-BY 4.0 papers, got {len(converted)} from {len(rows)} manifest rows")
        eligible=dest/"eligible-manifest.csv"
        with eligible.open("w",encoding="utf-8",newline="") as out:
            writer=csv.DictWriter(out,fieldnames=list(converted[0].keys()))
            writer.writeheader()
            writer.writerows(converted)
        get(meta["release"],payload)
        if payload.stat().st_size < 1_000_000:
            raise SystemExit(f"{name}: release payload unexpectedly small")
        record={
            "dataset_id":f"scienceverse-{name}-v1",
            "upstream":"https://github.com/scienceverse/papers",
            "upstream_manifest_revision":UPSTREAM_REVISION,
            "release_tag":meta["tag"],
            "manifest_url":f"{BASE}/{name}/manifest.csv",
            "fulltext_payload_url":meta["release"],
            "documents_in_manifest":len(rows),
            "documents_converted_and_license_verified":len(converted),
            "eligible_manifest_file":eligible.name,
            "license_filter":"every manifest row explicitly declares CC-BY 4.0",
            "target_library":meta["target"],
            "payload_file":payload.name,
            "payload_bytes":payload.stat().st_size,
            "payload_sha256":digest(payload),
            "manifest_sha256":digest(manifest),
            "eligible_manifest_sha256":digest(eligible),
            "status":"candidate_fulltext_acquired_pending_global_validation",
            "training_eligible":False,
            "admission_scope":"fixed upstream release paperlist; individual DOI/title/license provenance retained in manifest.csv",
            "caveats":["RDS is the upstream full-text paperlist format, not a plain-text export.",
                       "Recheck upstream retractions/corrections before each training snapshot.",
                       "Deduplicate by DOI and normalized full text against all existing RONIN corpora.",
                       "Keep all derived train/validation/test partitions document-grouped by DOI."]
        }
        (dest/"provenance.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        total+=len(rows)
        print(f"{name}: {len(rows)} docs; payload {payload.stat().st_size} bytes; sha256 {record['payload_sha256']}")
    # Remove any prior misplaced copy from the admitted tree after the candidate\n    # payload has been downloaded and verified successfully.\n    old=pathlib.Path("data/datasets/admitted/scienceverse")\n    if old.exists(): shutil.rmtree(old)\n    print(f"VERIFIED_CANDIDATE_DOCS={total}")
if __name__=="__main__": main()
