#!/usr/bin/env python3
"""Run the four-way conservative checkpoint tournament with strict paired screening."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from dataclasses import replace
import torch
from ronin.config import get_profile
from ronin.data.batches import NextTokenBatches, encode_text_file
from ronin.data.source_batches import SourceBalancedBatches
from ronin.models.transformer import RoninLM
from ronin.training.loop import train
from ronin.training.checkpoint import load_checkpoint
from ronin.utils.repro import seed_everything
from evaluate_mmlu_pro import load_external_dataset, select_stratified, rows_sha256, evaluate_rows, DATASET_REVISION
from evaluate_text import evaluate_checkpoint

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def evaluate(checkpoint, rows, all_hash, args):
    result=evaluate_rows(checkpoint,rows,all_hash,profile="tiny",context_length=args.context_length,device="cpu",batch_token_budget=args.batch_token_budget,dataset_split="validation",dataset_split_size=args.dataset_size)
    result["dataset_revision"]=args.revision
    return result

def assert_gate(before, after):
    before_ids=[x["id"] for x in before["details"]]; after_ids=[x["id"] for x in after["details"]]
    for label,report in (("before",before),("after",after)):
        if report["selected_items"] != 50 or report["evaluated_items"] != 50 or report["coverage"] != 1.0 or report.get("skipped_items",0) != 0:
            raise RuntimeError(f"paired holdout gate failed for {label}: selected={report.get(chr(115)+chr(101)+chr(108)+chr(101)+chr(99)+chr(116)+chr(101)+chr(100)+chr(95)+chr(105)+chr(116)+chr(101)+chr(109)+chr(115))} evaluated={report.get(chr(101)+chr(118)+chr(97)+chr(108)+chr(117)+chr(97)+chr(116)+chr(101)+chr(100)+chr(95)+chr(105)+chr(116)+chr(101)+chr(109)+chr(115))} coverage={report.get(chr(99)+chr(111)+chr(118)+chr(101)+chr(114)+chr(97)+chr(103)+chr(101))}")
    if before_ids != after_ids or before["dataset_sha256"] != after["dataset_sha256"] or before["dataset_revision"] != after["dataset_revision"] or before["dataset_split"] != after["dataset_split"]:
        raise RuntimeError("paired holdout identity mismatch")

def train_candidate(name, base_path, batches, args, anchor_lambda=0.0):
    cfg_model,cfg_train=get_profile("tiny")
    cfg_train=replace(cfg_train,max_steps=100,warmup_steps=10,checkpoint_every=100,learning_rate=2.5e-6,min_learning_rate=2.5e-7,weight_decay=0.0,seed=2026)
    seed_everything(2026)
    model=RoninLM(cfg_model)
    load_checkpoint(base_path,model,map_location="cpu",restore_rng=False)
    anchor={n:p.detach().cpu().float().clone() for n,p in model.named_parameters()} if anchor_lambda else None
    out=Path(args.output_dir)/name
    metrics=out/"training.json"
    train(model,batches,cfg_train,device="cpu",checkpoint_dir=out/"checkpoints",metrics_path=metrics,anchor_reference=anchor,anchor_lambda=anchor_lambda)
    ckpt=out/"checkpoints"/"step-00000100.pt"
    if not ckpt.is_file(): raise RuntimeError(f"missing checkpoint for {name}")
    return ckpt, json.loads(metrics.read_text(encoding="utf-8"))

def interpolate(base_path, other_path, alpha, destination):
    base=torch.load(base_path,map_location="cpu",weights_only=False)
    other=torch.load(other_path,map_location="cpu",weights_only=False)
    bs=base.get("model",base); os=other.get("model",other)
    if set(bs)!=set(os): raise ValueError("checkpoint state keys differ")
    merged={}
    for key in bs:
        a,b=bs[key],os[key]
        if not isinstance(a,torch.Tensor) or not isinstance(b,torch.Tensor) or a.shape!=b.shape:
            raise ValueError(f"incompatible tensor for interpolation: {key}")
        if a.is_floating_point():
            value=a.float().mul(1.0-alpha).add(b.float(),alpha=alpha)
            if not torch.isfinite(value).all(): raise ValueError(f"non-finite interpolated tensor: {key}")
            merged[key]=value.to(dtype=a.dtype)
        elif torch.equal(a,b): merged[key]=a.clone()
        else: raise ValueError(f"non-floating checkpoint buffer differs: {key}")
    cfg,_=get_profile("tiny"); model=RoninLM(cfg); model.load_state_dict(merged,strict=True)
    destination.parent.mkdir(parents=True,exist_ok=True)
    torch.save({"model":model.state_dict(),"step":0,"tournament_interpolation_alpha":alpha},destination)
    return destination

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base-checkpoint","second-checkpoint","combined-text","literature-text","mathlib-text","nasa-text","validation-text"): p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--output-dir",type=Path,default=Path("tournament-results"))
    p.add_argument("--revision",default=DATASET_REVISION); p.add_argument("--context-length",type=int,default=4096); p.add_argument("--batch-token-budget",type=int,default=8192); p.add_argument("--num-threads",type=int,default=2)
    args=p.parse_args(); torch.set_num_threads(args.num_threads)
    for path in (args.base_checkpoint,args.second_checkpoint,args.combined_text,args.literature_text,args.mathlib_text,args.nasa_text,args.validation_text):
        if not path.is_file(): raise FileNotFoundError(path)
    base_sha=sha(args.base_checkpoint)
    if base_sha != "7cda8dacb0b61d7278ba9990285a6a7e47403de8a00d201da06f5f002224c1cf": raise RuntimeError(f"unexpected winner checkpoint SHA: {base_sha}")
    rows_all=load_external_dataset(args.revision,split="validation"); rows=select_stratified(rows_all,50,seed=2026); all_hash=rows_sha256(rows_all); args.dataset_size=len(rows_all)
    base_mmlu=evaluate(args.base_checkpoint,rows,all_hash,args)
    if base_mmlu["selected_items"]!=50 or base_mmlu["evaluated_items"]!=50 or base_mmlu["coverage"]!=1.0 or base_mmlu.get("skipped_items",0)!=0: raise RuntimeError("ABORT BEFORE TRAINING: base holdout did not achieve 50/50 coverage")
    base_language=evaluate_checkpoint(args.base_checkpoint,args.validation_text,"tiny",batches=128,batch_size=2,seed=2026,device="cpu")
    write(args.output_dir/"baseline-mmlu.json",base_mmlu); write(args.output_dir/"baseline-language.json",base_language)
    source_tensors=[encode_text_file(path) for path in (args.literature_text,args.mathlib_text,args.nasa_text)]
    cfg,_=get_profile("tiny")
    natural=NextTokenBatches(encode_text_file(args.combined_text),2,cfg.context_length,seed=2026)
    balanced=lambda seed: SourceBalancedBatches([("literature",source_tensors[0],0.50),("mathlib4",source_tensors[1],0.495),("nasa-reviewed",source_tensors[2],0.005)],2,cfg.context_length,seed=seed)
    candidates=[]
    for name,batches,lam in (("A-conservative-anchor",natural,1e-3),("B-balanced-replay",balanced(2026),0.0),("C-balanced-anchor",balanced(2026),1e-3)):
        ckpt,training=train_candidate(name,args.base_checkpoint,batches,args,lam)
        after=evaluate(ckpt,rows,all_hash,args); assert_gate(base_mmlu,after)
        language=evaluate_checkpoint(ckpt,args.validation_text,"tiny",batches=128,batch_size=2,seed=2026,device="cpu")
        write(args.output_dir/name/"mmlu-after.json",after); write(args.output_dir/name/"language-after.json",language)
        candidates.append({"name":name,"checkpoint":str(ckpt),"checkpoint_sha256":sha(ckpt),"before_correct":base_mmlu["overall"]["correct"],"after_correct":after["overall"]["correct"],"delta_pp":100*(after["overall"]["accuracy"]-base_mmlu["overall"]["accuracy"]),"new_correct":sum(x["correct"] and not y["correct"] for x,y in zip(after["details"],base_mmlu["details"])),"regressions":sum(y["correct"] and not x["correct"] for x,y in zip(after["details"],base_mmlu["details"])),"coverage":after["coverage"],"language_before_bpb":base_language["bits_per_byte"],"language_after_bpb":language["bits_per_byte"],"training":training,"source_sampling":batches.sampling_report() if hasattr(batches,"sampling_report") else None})
    for alpha in (0.10,0.25,0.50):
        name=f"D-interpolation-{alpha:.2f}"; ckpt=interpolate(args.base_checkpoint,args.second_checkpoint,alpha,args.output_dir/name/"interpolated.pt")
        after=evaluate(ckpt,rows,all_hash,args); assert_gate(base_mmlu,after)
        language=evaluate_checkpoint(ckpt,args.validation_text,"tiny",batches=128,batch_size=2,seed=2026,device="cpu")
        write(args.output_dir/name/"mmlu-after.json",after); write(args.output_dir/name/"language-after.json",language)
        candidates.append({"name":name,"checkpoint":str(ckpt),"checkpoint_sha256":sha(ckpt),"alpha":alpha,"before_correct":base_mmlu["overall"]["correct"],"after_correct":after["overall"]["correct"],"delta_pp":100*(after["overall"]["accuracy"]-base_mmlu["overall"]["accuracy"]),"new_correct":sum(x["correct"] and not y["correct"] for x,y in zip(after["details"],base_mmlu["details"])),"regressions":sum(y["correct"] and not x["correct"] for x,y in zip(after["details"],base_mmlu["details"])),"coverage":after["coverage"],"language_before_bpb":base_language["bits_per_byte"],"language_after_bpb":language["bits_per_byte"]})
    candidates.sort(key=lambda x:(x["regressions"]==0,x["after_correct"],-x["language_after_bpb"]),reverse=True)
    write(args.output_dir/"tournament-summary.json",{"experiment":"checkpoint-strategy-tournament-6of50","base_checkpoint_sha256":base_sha,"holdout_split":"validation","holdout_revision":args.revision,"holdout_dataset_sha256":all_hash,"holdout_ids":[x["id"] for x in base_mmlu["details"]],"coverage":1.0,"training_steps_per_trained_candidate":100,"automatic_promotion":False,"confirmation_required":"independent MMLU-Pro test split; validation sample is development-only","candidates_ranked":candidates})
    print(json.dumps(candidates,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
