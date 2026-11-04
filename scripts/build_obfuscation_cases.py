"""Construye pares de opacidad a partir de fuentes descargadas y controles sintéticos.

No descarga ni redistribuye transcripciones con licencias no verificadas. Las
fuentes primarias deben existir en el manifiesto de adquisición.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from ronin.epistemic.obfuscation import validate_obfuscation_case

POE_CIPHER = (
    "53‡‡†305))6*;4826)4‡.)4‡);806*;48†8¶60))85;1‡(;:‡*8†83(88)"
    "5*†;46(;88*96*?;8)*‡(;485);5*†2:*‡(;4956*2(5*—4)8¶8*;40692"
    "85);)6†8)4‡‡;1(‡9;48081;8:8‡1;48†85;4)485†528806*81(‡9;48;"
    "(88;4(‡?34;48)4‡;161;:188;‡?;"
)
POE_PLAINTEXT = (
    "A good glass in the bishop's hostel in the devil's seat forty-one "
    "degrees and thirteen minutes northeast and by north main branch "
    "seventh limb east side shoot from the left eye of the death's-head "
    "a bee-line from the tree through the shot fifty feet out."
)
VERNE_CIPHER = (
    "Phyjslyddqfdzxgasgzzqqehxgkfndrxujugiocytdxvksbxhhuypo "
    "hdvyrymhuhpuydkjoxphetozsletnpmvffovpdpajxhyynojyggayme "
    "qynfuqlnmvlyfgsuzmqiztlbqgyugsqeubvnrcredgruzblrmxyuhqhp "
    "zdrrgcrohepqxufivvrplphonthvddqfhqsntzhhhnfepmqkyuuexktog "
    "zgkyuumfvijdqdpzjqsykrplxhxqrymvklohhhotozvdksppsuvjhd"
)
VERNE_PLAINTEXT = (
    "Le véritable auteur du vol des diamants et de l’assassinat des soldats "
    "qui escortaient le convoi, commis dans la nuit du vingt-deux janvier "
    "mil huit cent vingt-six, n’est donc pas Joam Dacosta, injustement "
    "condamné à mort; c’est moi, le misérable employé de l’administration "
    "du district diamantin; oui, moi seul, qui signe de mon vrai nom, Ortega."
)
HYPNEROTOMACHIA_ACROSTIC = (
    "POLIAM FRATER FRANCISCVS COLVMNA PERAMAVIT"
)
BACONIAN_CLAIM = (
    "La clave biliteral atribuida a Elizabeth Wells Gallup demuestra que "
    "Francis Bacon escribió las obras publicadas bajo el nombre de Shakespeare."
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_hash(manifest: dict[str, Any], source_id: str) -> str:
    for source in manifest["sources"]:
        if source["id"] == source_id:
            return source["sha256"]
    raise ValueError(f"Fuente ausente en manifiesto: {source_id}")


def record(**values: Any) -> dict[str, Any]:
    return {
        "confidence": 1.0,
        "split": "train",
        "synthetic": False,
        "annotator": "RONIN-curation-v1",
        "policy_version": "opacidad-v1",
        **values,
    }


def build(manifest_path: Path, output_path: Path, noise_count: int = 500) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    common = {
        "source_license": "Dominio público; ejemplar primario registrado en manifiesto",
    }

    rows.append(record(
        record_id="poe-goldbug-cipher-001",
        case_type="A",
        label="CONFIRMED_MESSAGE",
        evidence_status="fictional_solved_in_narrative",
        text=POE_CIPHER,
        source_id="poe-gold-bug",
        source_sha256=source_hash(manifest, "poe-gold-bug"),
        source_license=common["source_license"],
        evidence_refs=[
            "https://www.gutenberg.org/ebooks/2147",
            "https://www.eapoe.org/works/tales/goldbgc.htm",
        ],
        mechanism="Sustitución monoalfabética; análisis de frecuencias y patrones",
        solution_summary=POE_PLAINTEXT,
        reproduction_steps=[
            "Contar frecuencias de símbolos.",
            "Inferir correspondencias por frecuencia y patrones de palabras.",
            "Comprobar que la sustitución recupera el texto en claro completo.",
        ],
    ))
    rows.append(record(
        record_id="verne-jangada-gronsfeld-001",
        case_type="A",
        label="CONFIRMED_MESSAGE",
        evidence_status="fictional_solved_in_narrative",
        text=VERNE_CIPHER,
        source_id="verne-la-jangada-fr",
        source_sha256=source_hash(manifest, "verne-la-jangada-fr"),
        source_license=common["source_license"],
        evidence_refs=[
            "https://www.gutenberg.org/ebooks/14806",
            "https://culturacientifica.com/2021/01/20/el-cifrado-de-gronsfeld-en-la-jangada/",
            "https://www.futilitycloset.com/2020/11/18/another-first/",
        ],
        mechanism="Cifrado de Gronsfeld con clave numérica; palabra probable ORTEGA",
        solution_summary=VERNE_PLAINTEXT,
        reproduction_steps=[
            "Usar ORTEGA como palabra probable final.",
            "Derivar la clave numérica 432513 descrita en el análisis.",
            "Descifrar con alfabeto latino de 25 letras sin W y verificar el párrafo.",
        ],
    ))
    rows.append(record(
        record_id="hypnerotomachia-acrostic-001",
        case_type="C",
        label="CONFIRMED_STRUCTURE",
        evidence_status="documented",
        text="Iniciales ornamentales de los capítulos: " + " ".join(HYPNEROTOMACHIA_ACROSTIC.replace(" ", "")),
        source_id="hypnerotomachia-poliphili-1499",
        source_sha256=source_hash(manifest, "hypnerotomachia-poliphili-1499"),
        source_license="Public Domain Mark 1.0; ejemplar digital de 1499",
        evidence_refs=[
            "https://www.themorgan.org/morganmobile/in-disguise/colonna",
            "https://www.otago.ac.nz/library/exhibitions/authorship/cabinet8-1.html",
            "https://fondazionecerruti.org/en/artworks/hypnerotomachia-poliphili",
        ],
        mechanism="Acróstico estructural formado por iniciales ornamentales de capítulos",
        solution_summary=(
            "POLIAM FRATER FRANCISCVS COLVMNA PERAMAVIT. El patrón es observable; "
            "la interpretación como prueba de autoría sigue siendo un indicio, "
            "no una demostración definitiva."
        ),
    ))
    rows.append(record(
        record_id="shakespeare-gallup-claim-001",
        case_type="D",
        label="UNSUPPORTED_CLAIM",
        evidence_status="rejected_by_evidence",
        text=BACONIAN_CLAIM,
        source_id="ronin-authored-claim-paraphrase",
        source_sha256=digest(BACONIAN_CLAIM),
        source_license="Redacción propia; no se reproduce texto protegido",
        evidence_refs=[
            "https://catalog.folger.edu/record/52477",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5419462/",
            "https://www.newyorker.com/magazine/1958/02/22/ciphers-everywhere",
        ],
        mechanism=(
            "Atribución basada en selección retrospectiva de variantes tipográficas "
            "y reglas de lectura no invariantes; las pruebas de Friedman no "
            "encontraron un sistema reproducible que sostuviera la afirmación."
        ),
        rejected_claim=(
            "La clave biliteral propuesta por Gallup prueba que Bacon escribió "
            "las obras de Shakespeare."
        ),
        confidence=0.95,
    ))

    # Controles sintéticos: no contienen carga útil ni mensaje insertado.
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789!?#%&"
    for index in range(noise_count):
        seed = 20261104 + index
        rng = random.Random(seed)
        length = rng.randint(48, 180)
        sample = "".join(rng.choice(alphabet) for _ in range(length))
        rows.append(record(
            record_id=f"control-ruido-uniforme-{index:04d}",
            case_type="B",
            label="NO_MESSAGE_IN_CONTROL",
            evidence_status="reproduced",
            text=sample,
            source_id="synthetic-random-symbols-v1",
            source_sha256=digest(sample),
            source_license="CC0; generado por RONIN sin carga útil externa",
            evidence_refs=[f"generator://ronin/random-symbols-v1/seed/{seed}"],
            mechanism="Control pseudoaleatorio uniforme sin mensaje ni carga útil insertados",
            generator="random.Random + alfabeto fijo v1",
            generator_seed=seed,
            synthetic=True,
            confidence=1.0,
            split=("train" if index % 10 < 8 else "validation" if index % 10 == 8 else "test"),
        ))

    validation_errors = [
        (row["record_id"], validate_obfuscation_case(row))
        for row in rows
    ]
    validation_errors = [
        (record_id, error)
        for record_id, messages in validation_errors
        for error in messages
    ]
    if validation_errors:
        raise ValueError(f"Anotaciones no válidas: {validation_errors[:10]}")

    # Se fija una partición por caso fuente, no por fragmento, para evitar fuga.
    fixed_splits = {
        "poe-goldbug-cipher-001": "train",
        "verne-jangada-gronsfeld-001": "train",
        "hypnerotomachia-acrostic-001": "validation",
        "shakespeare-gallup-claim-001": "train",
    }
    for row in rows:
        if row["record_id"] in fixed_splits:
            row["split"] = fixed_splits[row["record_id"]]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "schema_version": 1,
        "dataset_id": "ronin-obfuscation-patterns-v1",
        "record_count": len(rows),
        "counts_by_type": {
            kind: sum(row["case_type"] == kind for row in rows)
            for kind in ("A", "B", "C", "D")
        },
        "counts_by_label": {
            label: sum(row["label"] == label for row in rows)
            for label in sorted({row["label"] for row in rows})
        },
        "counts_by_split": {
            split: sum(row["split"] == split for row in rows)
            for split in ("train", "validation", "test", "holdout")
        },
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "dataset_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "policy": (
            "Los negativos son solo controles sintéticos sin carga útil insertada. "
            "Los casos históricos no resueltos no se etiquetan como negativos. "
            "Los holdout permanecen fuera del entrenamiento."
        ),
    }
    (output_path.parent / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--noise-count", type=int, default=500)
    args = parser.parse_args()
    if args.noise_count < 1 or args.noise_count > 10000:
        raise ValueError("--noise-count debe estar entre 1 y 10000")
    print(json.dumps(build(args.source_manifest, args.output, args.noise_count), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
