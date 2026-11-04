#!/usr/bin/env python3
"""Deterministic, auditable high-knowledge-density selection for RONIN corpora.

No teacher model, network call, or opaque embedding model is required.
Input records are supplied by a source adapter and must carry explicit rights.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_+.-]{1,}|\d+(?:[.,]\d+)?|[=<>≤≥∑∫√∞→↔]")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
KNOWLEDGE_PATTERNS = {
    "definition": re.compile(r"\b(?:is defined as|means|denotes|se define como|se denomina|se define|consiste en)\b", re.I),
    "causal": re.compile(r"\b(?:because|therefore|thus|hence|causes?|leads? to|debido a|por tanto|por consiguiente|provoca|produce)\b", re.I),
    "conditional": re.compile(r"\b(?:if .* then|when .* then|si .* entonces|siempre que|necesario y suficiente|iff)\b", re.I),
    "proof": re.compile(r"\b(?:theorem|lemma|corollary|proof|proposition|axiom|demostración|teorema|lema|corolario|proposición|axioma)\b", re.I),
    "procedure": re.compile(r"\b(?:algorithm|procedure|步骤|algorithm|paso|iteración|complexity|complejidad|input|output|return)\b", re.I),
    "evidence": re.compile(r"\b(?:doi:|https?://|arxiv:|isbn|table \d|figure \d|eq\. \(?\d+|referencias|bibliography)\b", re.I),
}
DOMAIN_TERMS = {
    "mathematics": "theorem proof lemma corollary algebra calculus topology number theory probability statistics optimization equation matrix integral derivative vector espacio vectorial teorema demostración lema álgebra cálculo probabilidad estadística",
    "logic_epistemology": "logic inference proposition predicate quantifier entailment validity soundness proof epistemology falsifiability induction deduction bayesian modal epistemic deontic modus ponens falacia inferencia cuantificador validez",
    "philosophy": "philosophy ontology metaphysics ethics epistemology causality knowledge truth argumentation realism empiricism rationalism filosofía ontología metafísica ética epistemología causalidad conocimiento verdad",
    "physics": "physics quantum mechanics particle field energy momentum thermodynamics relativity electromagnetism spectroscopy force mass wave física cuántica mecánica energía momento termodinámica relatividad campo",
    "computer_science": "algorithm data structure complexity compiler operating system database protocol network type system program software code function memory concurrency algoritmo estructura de datos compilador sistema operativo base de datos",
    "chemistry_materials": "chemistry molecule compound reaction catalyst synthesis spectroscopy polymer material stoichiometry bond atom chemistry química molécula compuesto reacción catalizador síntesis polímero enlace átomo materials material",
    "biology": "biology cell gene protein genome organism pathway enzyme ecology evolution species genetics microbiology biología célula gen proteína genoma organismo enzima ecología evolución especie",
    "medicine_health": "medicine medical health clinical diagnosis treatment patient disease epidemiology pharmacology anatomy physiology medicine salud médico clínica diagnóstico tratamiento paciente enfermedad epidemiología farmacología anatomía fisiología",
    "software_engineering": "software engineering codebase repository testing debugging architecture API deployment version control compiler programming software ingeniería software código repositorio pruebas depuración arquitectura despliegue",
    "law": "law statute regulation court judgment contract liability jurisdiction jurisprudence legal rights legislation derecho ley tribunal sentencia contrato responsabilidad jurisdicción jurisprudencia legislación",
    "economics": "economics market elasticity inflation econometrics regression monetary fiscal trade finance production consumption economía mercado elasticidad inflación econometría regresión monetaria fiscal comercio finanzas producción consumo",
    "social_sciences": "sociology anthropology psychology political science institution society policy demographic culture social sciences sociología antropología psicología ciencia política institución sociedad política demografía cultura",
    "statistics_probability": "statistics probability stochastic distribution estimator hypothesis variance regression sampling statistical inference estadística probabilidad estocástico distribución estimador hipótesis varianza regresión muestreo",
    "astronomy_earth_science": "astronomy astrophysics cosmology planet star galaxy geology climate meteorology oceanography earth science astronomía astrofísica cosmología planeta estrella galaxia geología clima meteorología oceanografía",
    "engineering_robotics": "engineering robotics control systems circuit mechanical electrical materials design manufacturing robot automation ingeniería robótica control circuitos mecánica eléctrica diseño fabricación automatización",
    "humanities": "history linguistics literature language philology culture art historical text humanities historia lingüística literatura lengua filología cultura arte humanidades",
}
DOMAIN_ALIASES = {
    "chemistry": "chemistry_materials",
    "biology_medicine": "biology",
    "law_economics_social_sciences": "law",
}

STOP = set("the and for with that this from into over under about have has had are was were which whose where when what como para desde entre sobre una uno unos unas los las del por con sin que este esta estos estas".split())


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def normalized_hash(text: str) -> str:
    normalized = " ".join(tokens(text))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def simhash64(text: str) -> int:
    vector = [0] * 64
    for token in set(tokens(text)):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        for bit in range(64):
            vector[bit] += 1 if value & (1 << bit) else -1
    return sum((1 << bit) for bit, weight in enumerate(vector) if weight >= 0)


def score_record(text: str, domain: str, df: Counter[str], total_docs: int) -> dict[str, float]:
    words = tokens(text)
    if not words:
        return {k: 0.0 for k in ("domain_relevance", "knowledge_density", "specificity", "information_content", "structure", "semantic_density")}
    unique = set(words)
    domain_terms = set(tokens(DOMAIN_TERMS[DOMAIN_ALIASES.get(domain, domain)]))
    relevant = len(unique & domain_terms)
    relevance = min(1.0, relevant / 8.0)
    pattern_hits = sum(bool(pattern.search(text)) for pattern in KNOWLEDGE_PATTERNS.values())
    equations = len(re.findall(r"(?:=|≤|≥|∑|∫|√|\\frac|\\begin\{equation\})", text))
    numeric = len(re.findall(r"\b\d+(?:[.,]\d+)?(?:%|\s?(?:kg|mg|m|s|Hz|Pa|mol|°C|USD|EUR))?\b", text))
    relations = len(re.findall(r"\b(?:is a|consists of|depends on|defined by|causes|implies|equivalent to|es un|se compone de|depende de|implica|equivale a|produce)\b", text, re.I))
    units = pattern_hits + min(4, equations) + min(4, numeric / 2) + min(4, relations)
    density = min(1.0, units / max(2.0, len(words) / 45.0))
    specificity = min(1.0, (numeric + 2 * equations + 2 * relations) / max(4.0, len(words) / 20.0))
    idfs = [math.log((1 + total_docs) / (1 + df.get(t, 0))) for t in unique if t not in STOP and len(t) > 2]
    information = min(1.0, (sum(idfs) / max(1, len(idfs))) / 7.0) if idfs else 0.0
    sentence_count = max(1, len(SENTENCE_RE.split(text.strip())))
    avg_sentence = len(words) / sentence_count
    structure = min(1.0, (1.0 if 8 <= len(words) <= 900 else 0.5) * min(1.0, avg_sentence / 12.0))
    score = 100 * (
        0.25 * relevance
        + 0.30 * density
        + 0.15 * specificity
        + 0.15 * information
        + 0.15 * structure
    )
    return {
        "domain_relevance": round(relevance, 6),
        "knowledge_density": round(density, 6),
        "specificity": round(specificity, 6),
        "information_content": round(information, 6),
        "structure": round(structure, 6),
        "semantic_density": round(score, 6),
    }


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
                if isinstance(row, dict):
                    yield row


def load_hf(spec: dict[str, Any]) -> Iterable[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("Install the optional 'datasets' package to read Hugging Face sources") from exc
    dataset = load_dataset(
        spec["dataset_id"],
        spec.get("config"),
        split=spec.get("split", "train"),
        streaming=True,
        revision=spec["revision"],
    )
    return dataset


def source_rows(spec: dict[str, Any]) -> Iterable[dict[str, Any]]:
    kind = spec.get("adapter", "jsonl")
    if kind == "jsonl":
        return iter_jsonl(Path(spec["path"]))
    if kind == "huggingface":
        return load_hf(spec)
    raise ValueError(f"Unsupported adapter {kind!r}; use jsonl or huggingface")


def get_field(row: dict[str, Any], key: str | None, default: Any = None) -> Any:
    if not key:
        return default
    value: Any = row
    for part in key.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def passes_filters(row: dict[str, Any], filters: dict[str, Any]) -> bool:
    for field, expected in filters.get("equals", {}).items():
        if get_field(row, field) != expected:
            return False
    for field, allowed in filters.get("in", {}).items():
        if get_field(row, field) not in allowed:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-spec", type=Path, required=True)
    parser.add_argument("--domain", choices=sorted(set(DOMAIN_TERMS) | set(DOMAIN_ALIASES)), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--max-documents", type=int, default=2_000_000)
    parser.add_argument("--max-source-rows", type=int, default=5_000_000)
    parser.add_argument("--top-percent", type=float, default=20.0)
    parser.add_argument("--min-score", type=float, default=30.0)
    args = parser.parse_args()

    spec_doc = json.loads(args.source_spec.read_text(encoding="utf-8"))
    sources = [s for s in spec_doc["sources"] if s["domain"] == args.domain]
    if not sources:
        raise SystemExit(f"No source adapters configured for {args.domain}")
    with tempfile.NamedTemporaryFile(prefix="ronin-hkd-", suffix=".sqlite3", delete=False) as tmp:
        database_path = Path(tmp.name)
    db = sqlite3.connect(database_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE TABLE docs (id TEXT PRIMARY KEY, source TEXT, text TEXT, license TEXT, provenance TEXT, sha TEXT UNIQUE)")
    db.execute("CREATE TABLE df (term TEXT PRIMARY KEY, n INTEGER)")
    db.execute("CREATE TABLE ranked (score REAL, doc_id TEXT, scores TEXT)")
    rejected: Counter[str] = Counter()
    accepted = 0

    for spec in sources:
        if spec.get("enabled") is not True:
            rejected["source_disabled_pending_audit"] += 1
            continue
        audit_path = Path(spec.get("license_audit", ""))
        if not spec.get("revision") or not audit_path.is_file():
            rejected["missing_revision_or_license_audit"] += 1
            continue
        allowed = set(spec.get("allowed_licenses", []))
        if not allowed:
            rejected["empty_license_allowlist"] += 1
            continue

        # A source is eligible for candidate extraction only when the audit
        # contains a source-specific, revision-pinned LIMITED_PASS. Merely
        # enabling an adapter or pointing at an audit file is not approval.
        try:
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            rejected["invalid_license_audit"] += 1
            continue
        source_identifier = spec.get("dataset_id") or spec["id"]
        authorization = next(
            (
                item for item in audit.get("candidate_intake_authorizations", [])
                if item.get("source_id") == source_identifier
                and item.get("dataset_revision") == spec.get("revision")
                and item.get("status") == "LIMITED_PASS"
                and item.get("candidate_text_downloads_authorized") is True
                and item.get("training_eligible") is False
                and item.get("admitted") is False
            ),
            None,
        )
        authorized_licenses = set((authorization or {}).get("allowed_licenses", []))
        if authorization is None or not allowed.issubset(authorized_licenses):
            rejected["source_not_covered_by_scoped_authorization"] += 1
            continue
        for index, row in enumerate(source_rows(spec)):
            if accepted >= args.max_documents or index >= args.max_source_rows:
                break
            if not passes_filters(row, spec.get("filters", {})):
                rejected["domain_or_language_filter"] += 1
                continue
            license_value = get_field(row, spec.get("license_field"), spec.get("fixed_license"))
            if license_value not in allowed:
                rejected["license_not_allowlisted"] += 1
                continue
            text_value = get_field(row, spec.get("text_field"))
            if not isinstance(text_value, str) or len(text_value.strip()) < 300:
                rejected["missing_or_short_text"] += 1
                continue
            provenance = get_field(row, spec.get("provenance_field"), f"{spec['id']}:{index}")
            if not provenance:
                rejected["missing_provenance"] += 1
                continue
            clean = re.sub(r"\s+", " ", text_value).strip()
            digest = normalized_hash(clean)
            try:
                db.execute(
                    "INSERT INTO docs VALUES (?, ?, ?, ?, ?, ?)",
                    (f"{spec['id']}:{provenance}", spec["id"], clean, license_value, str(provenance), digest),
                )
            except sqlite3.IntegrityError:
                rejected["duplicate_document_or_content"] += 1
                continue
            for term in set(tokens(clean)):
                if len(term) > 2 and term not in STOP:
                    db.execute(
                        "INSERT INTO df VALUES (?, 1) ON CONFLICT(term) DO UPDATE SET n=n+1",
                        (term,),
                    )
            accepted += 1

    total = db.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
    if not total:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({"domain": args.domain, "accepted": 0, "rejected": dict(rejected), "status": "blocked_no_admitted_sources"}, indent=2) + "\n", encoding="utf-8")
        raise SystemExit("No source passed explicit license/revision gates; no library written.")

    df = Counter(dict(db.execute("SELECT term, n FROM df")))
    scored_count = 0
    for doc_id, text in db.execute("SELECT id, text FROM docs"):
        scores = score_record(text, args.domain, df, total)
        if scores["semantic_density"] >= args.min_score:
            db.execute(
                "INSERT INTO ranked VALUES (?, ?, ?)",
                (scores["semantic_density"], doc_id, json.dumps(scores)),
            )
            scored_count += 1
    db.commit()
    keep_n = max(1, int(scored_count * min(100.0, max(0.1, args.top_percent)) / 100.0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    hashes = hashlib.sha256()
    sidecar_hashes = hashlib.sha256()
    bytes_written = 0
    selected_count = 0
    score_total = 0.0
    score_min = float("inf")
    sidecar_path = args.output.with_suffix(".manifest.jsonl")
    with args.output.open("w", encoding="utf-8", newline="\n") as out, sidecar_path.open("w", encoding="utf-8", newline="\n") as sidecar:
        rows = db.execute(
            "SELECT docs.id, docs.source, docs.text, docs.license, docs.provenance, docs.sha, ranked.score, ranked.scores "
            "FROM ranked JOIN docs ON docs.id=ranked.doc_id "
            "ORDER BY ranked.score DESC, docs.id",
        )
        selected_bands: dict[int, dict[int, list[int]]] = {i: {} for i in range(4)}
        near_duplicate_removed = 0
        for doc_id, source_id, text, license_value, provenance, text_sha, score, score_json in rows:
            signature = simhash64(text)
            duplicate = False
            for band in range(4):
                key = (signature >> (band * 16)) & 0xFFFF
                for previous in selected_bands[band].get(key, []):
                    if (signature ^ previous).bit_count() <= 3:
                        duplicate = True
                        break
                if duplicate:
                    break
            if duplicate:
                near_duplicate_removed += 1
                continue
            line = text + "\n"
            out.write(line)
            encoded = line.encode("utf-8")
            hashes.update(encoded)
            bytes_written += len(encoded)
            sidecar_line = json.dumps({
                "document_id": doc_id,
                "source_id": source_id,
                "provenance": provenance,
                "license": license_value,
                "normalized_text_sha256": text_sha,
                "semantic_density": score,
                "component_scores": json.loads(score_json),
            }, ensure_ascii=False, sort_keys=True) + "\n"
            sidecar.write(sidecar_line)
            sidecar_hashes.update(sidecar_line.encode("utf-8"))
            selected_count += 1
            score_total += score
            score_min = min(score_min, score)
            for band in range(4):
                key = (signature >> (band * 16)) & 0xFFFF
                selected_bands[band].setdefault(key, []).append(signature)
            if selected_count >= keep_n:
                break

    report = {
        "schema_version": 1,
        "domain": args.domain,
        "metric": "RONIN-HKD-0.1",
        "formula": "100*(0.25*domain_relevance+0.30*knowledge_density+0.15*specificity+0.15*information_content+0.15*structure)",
        "method": "deterministic lexical/propositional scoring; corpus IDF; exact normalized deduplication; explicit document-level license allowlist",
        "papers": [
            "Duan et al. 2025, Enhancing LLMs via High-Knowledge Data Selection, AAAI, DOI 10.1609/aaai.v39i22.34555",
            "Xie et al. 2023, Data Selection for Language Models via Importance Resampling, NeurIPS, DOI 10.52202/075280-1482",
            "Lai et al. 2020, Diversity, Density, and Homogeneity, LREC"
        ],
        "sources": [s["id"] for s in sources if s.get("enabled") is True],
        "documents_seen": total,
        "candidates_above_threshold": scored_count,
        "selected_documents": selected_count,
        "near_duplicates_removed": near_duplicate_removed,
        "selected_bytes_utf8": bytes_written,
        "selected_sha256": hashes.hexdigest(),
        "selected_manifest_path": str(sidecar_path),
        "selected_manifest_sha256": sidecar_hashes.hexdigest(),
        "rejected": dict(rejected),
        "score_mean": round(score_total / max(1, selected_count), 4),
        "score_min": round(0 if selected_count == 0 else score_min, 4),
        "status": "candidate_not_admitted_until_human_license_and_quality_audit",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    db.close()
    database_path.unlink(missing_ok=True)
    Path(str(database_path) + "-wal").unlink(missing_ok=True)
    Path(str(database_path) + "-shm").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
