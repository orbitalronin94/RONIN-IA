"""Pruebas del contrato de la biblioteca de opacidad."""
from ronin.epistemic.obfuscation import validate_obfuscation_case


def caso(**changes):
    item = {
        "record_id": "poe-goldbug-001",
        "case_type": "A",
        "label": "CONFIRMED_MESSAGE",
        "evidence_status": "fictional_solved_in_narrative",
        "text": "Texto cifrado de muestra.",
        "source_id": "poe-gold-bug",
        "source_sha256": "a" * 64,
        "source_license": "dominio público",
        "evidence_refs": ["https://www.gutenberg.org/ebooks/2147"],
        "mechanism": "Sustitución monoalfabética",
        "solution_summary": "La narración explica la sustitución y el texto en claro.",
        "reproduction_steps": ["Aplicar la clave descrita en el relato."],
        "confidence": 1.0,
        "split": "train",
        "synthetic": False,
        "annotator": "RONIN-curation",
        "policy_version": "opacidad-v1",
    }
    item.update(changes)
    return item


def test_acepta_criptograma_ficcional_resuelto():
    assert validate_obfuscation_case(caso()) == []


def test_no_convierte_voynich_en_negativo_por_no_estar_resuelto():
    item = caso(
        case_type="D",
        label="UNRESOLVED",
        evidence_status="unresolved",
        source_id="voynich-transcription-pending-rights",
        source_license="no verificada; excluida de entrenamiento",
        mechanism="Transcripción opaca sin descifrado consensuado",
        evidence_refs=["https://www.voynich.nu/transcr.html"],
        confidence=0.5,
    )
    assert validate_obfuscation_case(item) == []


def test_negativo_solo_para_control_sintetico_reproducible():
    item = caso(
        case_type="B",
        label="NO_MESSAGE_IN_CONTROL",
        evidence_status="reproduced",
        synthetic=True,
        generator="random-bytes-v1",
        generator_seed=42,
        mechanism="Bytes aleatorios uniformes sin canal de mensaje diseñado",
        solution_summary=None,
        reproduction_steps=None,
    )
    assert validate_obfuscation_case(item) == []
    item["synthetic"] = False
    assert any("solo se admite" in error for error in validate_obfuscation_case(item))


def test_rechaza_solucion_confirmada_sin_reproduccion():
    item = caso(solution_summary="", reproduction_steps=[])
    assert any("reproduction_steps" in error for error in validate_obfuscation_case(item))


def test_falso_positivo_requiere_refutacion_documentada():
    item = caso(
        case_type="D",
        label="UNSUPPORTED_CLAIM",
        evidence_status="rejected_by_evidence",
        rejected_claim="Atribución criptográfica baconiana concreta",
    )
    assert validate_obfuscation_case(item) == []
    item["evidence_status"] = "unresolved"
    assert any("rechace" in error for error in validate_obfuscation_case(item))


def test_holdout_no_puede_alimentar_entrenamiento():
    item = caso(split="holdout", used_for_training=True)
    assert any("Holdout" in error for error in validate_obfuscation_case(item))


def test_exige_hash_y_referencias():
    item = caso(source_sha256="xyz", evidence_refs=[])
    errors = validate_obfuscation_case(item)
    assert any("SHA-256" in error for error in errors)
    assert any("referencia" in error for error in errors)
