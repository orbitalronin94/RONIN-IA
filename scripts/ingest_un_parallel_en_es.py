#!/usr/bin/env python3
"""Acquire official UN Parallel Corpus v1.0 English-Spanish bitext; candidate-only."""
import argparse, gzip, hashlib, html.parser, itertools, json, re, tarfile, time, urllib.parse, urllib.request
from collections import Counter
from pathlib import Path

PAGE="https://www.un.org/dgacm/content/uncorpus/Download"
SOURCE="https://www.un.org/dgacm/en/content/uncorpus"
FILES=("UNv1.0.en-es.tar.gz.00","UNv1.0.en-es.tar.gz.01")
UA="RONIN-IA-corpus-acquisition/1.0 (research; UN attribution preserved)"
EMAIL=re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL=re.compile(r"(?i)(?:https?://|www\.)")
SYMBOL=re.compile(r"\b[A-Z]/(?:[A-Z]+/)?[A-Z0-9][A-Z0-9./-]{2,}\b")

class Parser(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag.lower()=="a":
            href=dict(attrs).get("href")
            if href: self.hrefs.append(href)

def request(url,target=None):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=180) as r:
        if target is None: return r.read()
        h=hashlib.sha256(); n=0
        with target.open("wb") as f:
            while True:
                b=r.read(1024*1024)
                if not b: break
                f.write(b); h.update(b); n+=len(b)
        return {"bytes":n,"sha256":h.hexdigest()}

def discover():
    p=Parser(); p.feed(request(PAGE).decode("utf-8","replace"))
    out={}
    for href in p.hrefs:
        name=urllib.parse.unquote(href).rsplit("/",1)[-1].split("?",1)[0]
        if name in FILES: out[name]=urllib.parse.urljoin(PAGE,href)
    if any(x not in out for x in FILES): raise RuntimeError("Official UN download page did not expose both en-es chunks")
    return out

def norm(s):
    import unicodedata
    return " ".join(unicodedata.normalize("NFC",s).split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,default=Path("artifacts/un-parallel-en-es"))
    ap.add_argument("--max-pairs",type=int,default=2_000_000)
    a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=True); work=a.out/"work"; work.mkdir(exist_ok=True)
    urls=discover(); chunks=[]; archive=work/"UNv1.0.en-es.tar.gz"
    with archive.open("wb") as dst:
        for name in FILES:
            part=work/name; meta=request(urls[name],part); chunks.append({"filename":name,"url":urls[name],**meta})
            with part.open("rb") as src:
                while True:
                    b=src.read(1024*1024)
                    if not b: break
                    dst.write(b)
    archive_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
    required={".en":"english.txt",".es":"spanish.txt",".ids":"ids.txt"}; extracted={}
    with tarfile.open(archive,"r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile(): continue
            base=Path(m.name).name
            for suffix,outname in required.items():
                if base.endswith(suffix) and suffix not in extracted:
                    src=tf.extractfile(m)
                    if src is None: raise RuntimeError("Unreadable archive member "+m.name)
                    dest=work/outname
                    with dest.open("wb") as f:
                        while True:
                            b=src.read(1024*1024)
                            if not b: break
                            f.write(b)
                    extracted[suffix]=dest
    if set(extracted)!=set(required): raise RuntimeError("Unexpected archive layout; expected .en, .es and .ids files")
    outputs={s:gzip.open(a.out/(s+".jsonl.gz"),"wt",encoding="utf-8",newline="") for s in ("train","validation","test")}
    counts=Counter(); sizes=Counter(); excluded=Counter(); seen=set(); langbytes=Counter(); n=0
    try:
        with extracted[".en"].open(encoding="utf-8") as en, extracted[".es"].open(encoding="utf-8") as es, extracted[".ids"].open(encoding="utf-8") as ids:
            for line_no,triple in enumerate(itertools.zip_longest(en,es,ids),1):
                if any(x is None for x in triple): raise RuntimeError("EN/ES/ID files have unequal line counts")
                en_text,es_text,identifier=(norm(x.rstrip("\r\n")) for x in triple)
                if not en_text or not es_text: excluded["empty_pair"]+=1; continue
                if len(en_text)<12 or len(es_text)<12: excluded["short_pair"]+=1; continue
                if EMAIL.search(en_text) or EMAIL.search(es_text): excluded["email_pattern"]+=1; continue
                if URL.search(en_text) or URL.search(es_text): excluded["url_pattern"]+=1; continue
                if "\ufffd" in en_text or "\ufffd" in es_text: excluded["replacement_character"]+=1; continue
                digest=hashlib.sha256((en_text+"\0"+es_text).encode()).hexdigest()
                if digest in seen: excluded["exact_duplicate_pair"]+=1; continue
                seen.add(digest)
                match=SYMBOL.search(identifier.upper()); doc=match.group(0) if match else identifier.strip()
                if not doc: doc="line-"+str(line_no)
                bucket=int.from_bytes(hashlib.sha256(("RONIN-UN-ENES-v1\0"+doc).encode()).digest()[:8],"big")%100
                split="train" if bucket<90 else ("validation" if bucket<95 else "test")
                row={"english":en_text,"spanish":es_text,"source_id":identifier.strip(),"document_key":doc,"source_line":line_no,"language_pair":"en-es","source_dataset":"United Nations Parallel Corpus v1.0","source_version":"1990-2014","text_sha256":digest}
                encoded=json.dumps(row,ensure_ascii=False,sort_keys=True)+"\n"
                outputs[split].write(encoded); counts[split]+=1; sizes[split]+=len(encoded.encode())
                langbytes["english"]+=len(en_text.encode()); langbytes["spanish"]+=len(es_text.encode()); n+=1
                if n>=a.max_pairs: break
    finally:
        for f in outputs.values(): f.close()
    if n==0: raise RuntimeError("No usable aligned en-es pairs")
    manifest={"schema_version":1,"dataset_id":"un-parallel-corpus-v1-en-es","status":"candidate_scoped_partitions_pending_review","source":SOURCE,"download_page":PAGE,"rights":"UN states that UN Parallel Corpus v1.0 contains official records and parliamentary documents in the public domain; preserve UN attribution and disclaimer.","attribution":"United Nations, Department for General Assembly and Conference Management, United Nations Parallel Corpus v1.0; Ziemski, Junczys-Dowmunt & Pouliquen (2016), LREC.","document_period":"1990-2014","excluded_source_data":["official 2015 development set","official 2015 test set","non-en-es bitext archives"],"archive_sha256":archive_hash,"chunks":chunks,"unique_aligned_pairs":n,"excluded":dict(excluded),"language_text_utf8_bytes":dict(langbytes),"partitions":{s:{"pairs":counts[s],"jsonl_utf8_bytes":sizes[s],"training_eligible":False} for s in outputs},"split_policy":"90/5/5 deterministic SHA-256 split grouped by UN document symbol extracted from source ID; full source ID fallback","training_eligible":False,"pending":["bilingual human sample review","document-key grouping audit","global exact/near deduplication","PII/privacy review","holdout contamination check","scoped admission"],"retrieved_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())}
    (a.out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pairs":n,"partitions":dict(counts),"excluded":dict(excluded),"language_text_utf8_bytes":dict(langbytes),"archive_sha256":archive_hash,"training_eligible":False},ensure_ascii=False,indent=2))
if __name__=="__main__": main()
