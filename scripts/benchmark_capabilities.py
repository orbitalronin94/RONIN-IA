#!/usr/bin/env python3
"""Reproducible CPU screening of Qwen3-0.6B variants on Spanish, math, code and instruction following.

Heuristic rubric only; this is not a substitute for exact-match benchmarks or human review.
"""
import json
import os
import re
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

MODELS = {
    "base": "Qwen/Qwen3-0.6B",
    "coding": "rohitnagareddy/Qwen3-0.6B-Coding-Finetuned-v1",
    "math_expert": "suayptalha/Qwen3-0.6B-Math-Expert",
    "code_expert": "suayptalha/Qwen3-0.6B-Code-Expert",
    "instruction_following": "suayptalha/Qwen3-0.6B-IF-Expert",
}
CASES = [
    {"id":"ES1","category":"spanish","prompt":"Responde en español con exactamente tres viñetas sobre estudiar por la mañana.","checks":["three_bullets","spanish"]},
    {"id":"ES2","category":"spanish","prompt":"Resume en una sola frase: La app descarga el modelo una vez y luego puede funcionar sin conexión.","checks":["one_sentence","spanish"]},
    {"id":"ES3","category":"spanish","prompt":"Explica en español la diferencia entre energía renovable y no renovable en dos frases.","checks":["spanish","renewable"]},
    {"id":"ES4","category":"spanish","prompt":"Di claramente que no puedes conocer el precio exacto de un producto que aún no se ha anunciado.","checks":["uncertainty","spanish"]},
    {"id":"MATH1","category":"math","prompt":"Una batería está al 80%. Consume 15 puntos porcentuales y recupera 7. ¿Qué porcentaje queda? Explica.","checks":["math72"]},
    {"id":"MATH2","category":"math","prompt":"Tres trabajadores tardan seis horas. Si trabajan seis al mismo ritmo, ¿cuánto tardan? Explica.","checks":["three_hours"]},
    {"id":"MATH3","category":"math","prompt":"Calcula 17 × 19 y muestra una comprobación breve.","checks":["math323"]},
    {"id":"MATH4","category":"math","prompt":"Resuelve: 3x + 5 = 20. Da el valor de x y compruébalo.","checks":["x5"]},
    {"id":"CODE1","category":"code","prompt":"Escribe una función Python sum_even(nums) que sume los pares. Incluye pruebas con lista vacía y negativos.","checks":["function","assert","even_filter"]},
    {"id":"CODE2","category":"code","prompt":"Explica por qué eval() con entrada de usuario es peligroso y muestra la alternativa json.loads.","checks":["json_loads","mentions_eval"]},
    {"id":"CODE3","category":"code","prompt":"Escribe una función Python para comprobar si una cadena es palíndromo, ignorando mayúsculas y espacios. Incluye una prueba.","checks":["function","assert","palindrome"]},
    {"id":"CODE4","category":"code","prompt":"¿Qué complejidad temporal tiene la búsqueda binaria en una lista ordenada? Responde con explicación breve.","checks":["log_complexity"]},
    {"id":"IF1","category":"instruction_following","prompt":"Responde con exactamente la palabra: LISTO","checks":["exact_listo"]},
    {"id":"IF2","category":"instruction_following","prompt":"Devuelve exactamente tres líneas, cada una con una fruta distinta y sin numeración.","checks":["three_lines"]},
    {"id":"IF3","category":"instruction_following","prompt":"Responde en español con exactamente dos viñetas, cada una de máximo ocho palabras, sobre dormir bien.","checks":["two_bullets","spanish"]},
    {"id":"IF4","category":"instruction_following","prompt":"Si no sabes la respuesta, reconoce la incertidumbre. ¿Cuál será el número ganador de la lotería de mañana?","checks":["uncertainty"]},
]
MAX_NEW_TOKENS = 128

def render_prompt(tokenizer, prompt):
    try:
        return tokenizer.apply_chat_template(
            [{"role":"user","content":prompt}], tokenize=False,
            add_generation_prompt=True, enable_thinking=False)
    except (TypeError, ValueError):
        try:
            return tokenizer.apply_chat_template([{"role":"user","content":prompt}],
                tokenize=False, add_generation_prompt=True)
        except Exception:
            return prompt

def score(case, response):
    text = response.strip()
    low = text.lower()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    bullets = [line for line in lines if line.startswith(("-", "*", "•"))]
    checks = {}
    for check in case["checks"]:
        if check == "three_bullets": checks[check] = len(bullets) == 3
        elif check == "two_bullets": checks[check] = len(bullets) == 2
        elif check == "three_lines": checks[check] = len(lines) == 3 and not any(x.startswith(("-", "*", "•", "1.", "2.", "3.")) for x in lines)
        elif check == "spanish": checks[check] = any(w in f" {low} " for w in (" que ", " de ", " la ", " el ", " para ", " por ", " una ", " es "))
        elif check == "one_sentence": checks[check] = len([x for x in re.split(r"[.!?]+", text) if x.strip()]) <= 2
        elif check == "renewable": checks[check] = "renovable" in low and ("no renovable" in low or "no-renovable" in low)
        elif check == "uncertainty": checks[check] = any(x in low for x in ("no puedo saber", "no se puede saber", "no dispongo", "no está anunciado", "no tengo información", "no es posible determinar", "no puedo predecir", "imposible saber"))
        elif check == "math72": checks[check] = bool(re.search(r"\b72\b", text))
        elif check == "three_hours": checks[check] = bool(re.search(r"\b3 horas\b|\btres horas\b", low))
        elif check == "math323": checks[check] = bool(re.search(r"\b323\b", text))
        elif check == "x5": checks[check] = bool(re.search(r"x\s*=\s*5\b|x\s+es\s+5\b", low))
        elif check == "function": checks[check] = "def " in text
        elif check == "assert": checks[check] = "assert" in low or "unittest" in low
        elif check == "even_filter": checks[check] = "%" in text and ("== 0" in text or "not in" in text)
        elif check == "json_loads": checks[check] = "json.loads" in text
        elif check == "mentions_eval": checks[check] = "eval" in low
        elif check == "palindrome": checks[check] = "palindrom" in low or "[::-1]" in text
        elif check == "log_complexity": checks[check] = bool(re.search(r"o\s*\(\s*log\s*n\s*\)", low)) or "logarítmica" in low
        elif check == "exact_listo": checks[check] = text == "LISTO"
    return {"passed":sum(checks.values()),"total":len(checks),"details":checks}

def main():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    report = {
        "schema_version":1, "generated_at":datetime.now(timezone.utc).isoformat(),
        "method":"Greedy CPU inference, fixed 16-prompt heuristic suite; no sampling. Heuristic scores may misjudge correctness.",
        "seed":42, "max_new_tokens":MAX_NEW_TOKENS, "models":{}, "summary":[],
    }
    for label, repo in MODELS.items():
        item={"repo":repo,"cases":[],"errors":[]}
        report["models"][label]=item
        model=tokenizer=None
        try:
            start=time.monotonic()
            tokenizer=AutoTokenizer.from_pretrained(repo, trust_remote_code=False)
            model=AutoModelForCausalLM.from_pretrained(repo, torch_dtype=torch.float32,
                low_cpu_mem_usage=True, trust_remote_code=False)
            model.eval()
            item["load_seconds"]=round(time.monotonic()-start,2)
            for case in CASES:
                encoded=tokenizer(render_prompt(tokenizer,case["prompt"]),return_tensors="pt",
                    truncation=True,max_length=1024)
                start=time.monotonic()
                with torch.inference_mode():
                    output=model.generate(**encoded,max_new_tokens=MAX_NEW_TOKENS,
                        do_sample=False,pad_token_id=tokenizer.eos_token_id)
                answer=tokenizer.decode(output[0][encoded["input_ids"].shape[1]:],
                    skip_special_tokens=True).strip()
                item["cases"].append({"id":case["id"],"category":case["category"],
                    "response":answer,"latency_seconds":round(time.monotonic()-start,2),
                    "score":score(case,answer)})
            item["passed"]=sum(x["score"]["passed"] for x in item["cases"])
            item["checks"]=sum(x["score"]["total"] for x in item["cases"])
            item["score_pct"]=round(100*item["passed"]/max(1,item["checks"]),2)
            item["mean_latency_seconds"]=round(sum(x["latency_seconds"] for x in item["cases"])/len(item["cases"]),2)
            item["category_scores"]={}
            for category in sorted({x["category"] for x in item["cases"]}):
                cases=[x for x in item["cases"] if x["category"]==category]
                p=sum(x["score"]["passed"] for x in cases); n=sum(x["score"]["total"] for x in cases)
                item["category_scores"][category]={"passed":p,"total":n,"pct":round(100*p/max(1,n),2)}
        except Exception as exc:
            item["errors"].append(f"{type(exc).__name__}: {exc}")
            item["traceback"]=traceback.format_exc()[-3000:]
        finally:
            del model, tokenizer
        if item.get("checks"):
            report["summary"].append({"model":label,"repo":repo,"passed":item["passed"],
                "checks":item["checks"],"score_pct":item["score_pct"],
                "mean_latency_seconds":item["mean_latency_seconds"],
                "category_scores":item["category_scores"]})
            print(f'{label}: {item["passed"]}/{item["checks"]} ({item["score_pct"]}%), latency={item["mean_latency_seconds"]}s',flush=True)
        else:
            print(f'{label}: FAILED {item["errors"]}',flush=True)
    report["interpretation"]="Highest heuristic score is only a screening lead. Confirm with exact-match tests, independent benchmark sets and human review before selecting a model."
    out=Path("capability-benchmark-report.json")
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("Report:",out,flush=True)
    return 0 if any(x.get("checks") for x in report["models"].values()) else 1

if __name__=="__main__":
    raise SystemExit(main())
