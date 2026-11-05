#!/usr/bin/env python3
"""Adaptive staged 50-seed tournament; no checkpoint is promoted by this script."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from evaluate_mmlu_pro import DATASET_REVISION, evaluate_rows, load_external_dataset, rows_sha256, select_stratified

def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def save(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n"); t.replace(p)

def train(seed,base,text,out,stop,resume=None):
    d=out/f"seed-{seed}"; d.mkdir(parents=True,exist_ok=True)
    cmd=[sys.executable,"scripts/train_text.py","--text",str(text),"--profile","tiny","--steps","500","--seed",str(seed),"--learning-rate","0.00001","--min-learning-rate","0.000001","--device","cpu","--num-threads","1","--interop-threads","1","--checkpoints",str(d)]
    cmd += ["--learning-rate","0.00001","--min-learning-rate","0.000001","--metrics-out",str(d/"training-metrics.json")]\n    cmd += ["--resume-from",str(resume)] if resume else ["--init-checkpoint",str(base),"--stop-after-step",str(stop)]
    env=os.environ.copy(); env.update(OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1")
    subprocess.run(cmd,check=True,env=env)
    step=100 if resume is None else 500
    p=d/f"step-{step:08d}.pt"
    if not p.is_file() or p.stat().st_size==0: raise RuntimeError(f"checkpoint missing for seed {seed}")
    return p

def score(checkpoint,rows,all_hash,args,total):
    return evaluate_rows(checkpoint=checkpoint,rows=rows,all_rows_sha256=all_hash,profile="tiny",context_length=args.context_length,device="cpu",batch_token_budget=args.batch_token_budget,dataset_split="test",dataset_split_size=total)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--text",type=Path,required=True); ap.add_argument("--base-checkpoint",type=Path,required=True)
    ap.add_argument("--seeds",default=",".join(str(20261108+i) for i in range(50)))
    ap.add_argument("--revision",default=DATASET_REVISION); ap.add_argument("--context-length",type=int,default=4096)
    ap.add_argument("--batch-token-budget",type=int,default=8192); ap.add_argument("--output-dir",type=Path,default=Path("reports/seed-tournament"))
    a=ap.parse_args(); seeds=[int(x) for x in a.seeds.split(",")]
    if len(seeds)!=50 or len(set(seeds))!=50: raise ValueError("exactly 50 unique seeds required")
    if not a.base_checkpoint.is_file() or not a.text.is_file(): raise FileNotFoundError("training input missing")
    out=a.output_dir; out.mkdir(parents=True,exist_ok=True); base=a.base_checkpoint.resolve(); base_sha=digest(base)
    all_rows=load_external_dataset(a.revision,split="test"); all_hash=rows_sha256(all_rows); total=len(all_rows)
    r8=select_stratified(all_rows,8,seed=2026); r32=select_stratified(all_rows,32,seed=2026)
    r64=select_stratified(all_rows,64,seed=2026); r1024=select_stratified(all_rows,1024,seed=2026)
    b1024=score(base,r1024,all_hash,a,total); save(out/"main-1024.json",b1024)
    stage1={}
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs={ex.submit(train,s,base,a.text,out,100):s for s in seeds}
        for f in as_completed(fs): stage1[fs[f]]=f.result()
    q8={s:score(stage1[s],r8,all_hash,a,total) for s in seeds}
    for s,v in q8.items(): save(out/f"seed-{s}-8.json",v)
    sorted8=sorted(seeds,key=lambda s:q8[s]["overall"]["correct"],reverse=True)
    cut=q8[sorted8[3]]["overall"]["correct"]
    tied=[s for s in seeds if q8[s]["overall"]["correct"]==cut]
    q32={s:score(stage1[s],r32,all_hash,a,total) for s in tied} if len(tied)>1 else {}
    for s,v in q32.items(): save(out/f"seed-{s}-32-tiebreak.json",v)
    order=sorted(seeds,key=lambda s:(q8[s]["overall"]["correct"], q32[s]["overall"]["correct"] if s in q32 else -1),reverse=True)
    top4=order[:4]; stage2={}
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs={ex.submit(train,s,base,a.text,out,100,stage1[s]):s for s in top4}
        for f in as_completed(fs): stage2[fs[f]]=f.result()
    q64={s:score(stage2[s],r64,all_hash,a,total) for s in top4}
    top2=sorted(top4,key=lambda s:q64[s]["overall"]["correct"],reverse=True)[:2]
    qf={s:score(stage2[s],r1024,all_hash,a,total) for s in top2}
    eligible=[]
    for s,v in qf.items():
        same=[x["id"] for x in v["details"]]==[x["id"] for x in b1024["details"]]
        good=(same and v["dataset_sha256"]==b1024["dataset_sha256"] and v["selected_items"]==1024 and v["evaluated_items"]==1024 and v["skipped_context_items"]==0 and v["coverage"]==1.0 and v["overall"]["correct"]>b1024["overall"]["correct"] and v["checkpoint_sha256"]==digest(stage2[s]))
        if good: eligible.append(s)
    eligible.sort(key=lambda s:qf[s]["overall"]["correct"],reverse=True)
    winner=eligible[0] if eligible and (len(eligible)==1 or qf[eligible[0]]["overall"]["correct"]>qf[eligible[1]]["overall"]["correct"]) else None
    summary={"experiment":"ronin-adaptive-50-seed-tournament-v1","base_sha256":base_sha,"dataset_revision":a.revision,"dataset_sha256":all_hash,"seed_count":50,"workers":4,"threads_per_worker":1,"phase1_steps":100,"final_steps":500,"questions":{"screen":8,"adaptive_tiebreak":32,"finalist":64,"final":1024},"top4":top4,"top2":top2,"main_correct":b1024["overall"]["correct"],"finalists":{str(s):qf[s]["overall"] for s in top2},"eligible":eligible,"winner":winner,"winner_checkpoint":str(stage2[winner]) if winner is not None else None,"promotion":"requires separate validated publication step","test_set_exposure":"MMLU-Pro test is reused for adaptive selection; not an untouched scientific test"}
    save(out/"tournament-summary.json",summary); print(json.dumps(summary,indent=2,ensure_ascii=False))
if __name__=="__main__": main()
