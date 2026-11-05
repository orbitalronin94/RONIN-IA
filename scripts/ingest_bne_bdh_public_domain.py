#!/usr/bin/env python3
"""Acquire and audit the BNE public-domain TXT distribution; candidate-only."""
from __future__ import annotations
import hashlib, io, json, re, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import PurePosixPath
from pathlib import Path

ROOT=Path("data/datasets/candidates/bne-bdh-ocr")
URLS={
 "txt":"https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_txt.zip",
 "json":"https://www.bne.es/media/datosgob/bdh/dominiopublico/dominiopublico_json.zip",
}
UA="RONIN-IA/1.0 (open research dataset acquisition)"
EMAIL=re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
PHONE=re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{7,}\d)(?!\w)")
WORD=re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]{2,}")
def get(url):
 headers={
  "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
  "Accept":"application/zip,application/octet-stream,*/*",
  "Referer":"https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-documentos-en-dominio-publico1",
  "Origin":"https://www.bne.es",
 }
 req=urllib.request.Request(url,headers=headers)
 try:
  with urllib.request.urlopen(req,timeout=120) as r: return r.read()
 except Exception as exc:
  raise RuntimeError(f"BNE distribution download failed for {url}: {type(exc).__name__}: {exc}") from exc
def sha(b): return hashlib.sha256(b).hexdigest()
def safe_name(n):
 p=PurePosixPath(n)
 return not p.is_absolute() and ".." not in p.parts
def inspect_text(data):
 try: t=data.decode("utf-8-sig")
 except UnicodeDecodeError: t=data.decode("cp1252",errors="replace")
 n=max(1,len(t)); words=WORD.findall(t); tokens=re.findall(r"\S+",t)
 return {"encoding":"utf-8-sig_or_cp1252","characters":len(t),"words":len(words),
  "letter_ratio":round(sum(c.isalpha() for c in t)/n,4),
  "replacement_ratio":round(t.count("\ufffd")/n,6),
  "email_pattern":bool(EMAIL.search(t)),"phone_pattern":bool(PHONE.search(t)),
  "machine_quality_pass":len(t)>=1500 and len(words)>=150 and
   sum(c.isalpha() for c in t)/n>=.25 and t.count("\ufffd")/n<=.002 and
   not EMAIL.search(t) and not PHONE.search(t)}
def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 report={"schema_version":"1.0","dataset_id":"bne-bdh-public-domain-v1",
  "source_url":"https://datos.gob.es/es/catalogo/ea0019768-biblioteca-digital-documentos-en-dominio-publico1",
  "source_claim":"BNE describes the collection as works in the public domain, reusable under BNE CC-BY terms; metadata licence does not alone establish rights in any unrelated edition or third-party insert.",
  "acquired_at":datetime.now(timezone.utc).isoformat(),"distributions":{},"documents":[]}
 archives={}
 for kind,url in URLS.items():
  blob=get(url); report["distributions"][kind]={"url":url,"sha256":sha(blob),"bytes":len(blob)}
  z=zipfile.ZipFile(io.BytesIO(blob))
  entries=[]
  for info in z.infolist():
   if info.is_dir(): continue
   if not safe_name(info.filename): raise RuntimeError("Unsafe archive path: "+info.filename)
   entries.append(info)
  archives[kind]=(z,entries,blob)
  report["distributions"][kind]["archive_entries"]=len(entries)
  report["distributions"][kind]["archive_uncompressed_bytes"]=sum(x.file_size for x in entries)
 txtz,txt_entries,_=archives["txt"]
 out=ROOT/"payload"
 if out.exists():
  import shutil; shutil.rmtree(out)
 out.mkdir(parents=True)
 seen=set()
 for info in txt_entries:
  if not info.filename.lower().endswith((".txt",".text")): continue
  raw=txtz.read(info)
  digest=sha(raw)
  if digest in seen: continue
  seen.add(digest)
  q=inspect_text(raw)
  name=Path(info.filename).name
  target=out/name
  if target.exists(): target=out/(digest[:12]+"_"+name)
  target.write_bytes(raw)
  report["documents"].append({"archive_path":info.filename,"stored_path":str(target.relative_to(ROOT)),
    "source_archive_sha256":digest,"bytes":len(raw),**q,"status":"candidate_machine_quality_pass" if q["machine_quality_pass"] else "hold_machine_quality",
    "training_eligible":False})
 report["aggregate"]={"text_files":len(report["documents"]),
  "unique_exact_texts":len(seen),"machine_quality_pass":sum(x["machine_quality_pass"] for x in report["documents"]),
  "machine_quality_hold":sum(not x["machine_quality_pass"] for x in report["documents"]),
  "text_bytes":sum(x["bytes"] for x in report["documents"]),
  "training_eligible_documents":0,"global_dedup":"PENDING","content_and_third_party_review":"PENDING",
  "partitions":"PENDING","note":"All files remain candidates until record-to-text metadata linkage, exact and near-duplicate checks against every admitted source, full-document rights/content review, privacy review and deterministic split isolation pass."}
 (ROOT/"acquisition-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report["aggregate"],ensure_ascii=False))
if __name__=="__main__": main()
