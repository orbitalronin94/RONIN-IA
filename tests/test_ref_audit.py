import json

from ronin.data.ref import parse_ref_completion
from scripts.audit_ref_dataset import audit_records

VALID = """RESPUESTA: Una respuesta razonada.
CLASE_EPISTEMICA: falsifiable; se puede contrastar.
TIPO_DE_AFIRMACION: empirical
GENERO: scientific
ESTADO_DE_CODIFICACION: clear
EVIDENCIA: La fuente y la prueba experimental descritas permiten comprobarlo.
INCERTIDUMBRE: límites conocidos; confianza razonada: 0.75
POSIBLE_REFUTACION: Una observación contraria replicada.
REVISION: Cambiaría con nuevos datos reproducibles.
"""


def test_valid_ref_completion_is_accepted():
    result = parse_ref_completion(VALID)
    assert result.valid
    assert result.confidence == 0.75
    assert result.sections["RESPUESTA"] == "Una respuesta razonada."


def test_missing_section_and_invalid_enum_are_rejected():
    broken = VALID.replace("GENERO: scientific", "GENERO: science-fiction").replace(
        "REVISION: Cambiaría con nuevos datos reproducibles.\n", ""
    )
    result = parse_ref_completion(broken)
    assert not result.valid
    assert any("GENERO" in issue for issue in result.issues)
    assert any("REVISION" in issue for issue in result.issues)


def test_confidence_is_required_and_bounded():
    for invalid in ("1.4", "0,75", "-0.1", "+0.5", "10", "00.5"):
        result = parse_ref_completion(VALID.replace("0.75", invalid))
        assert not result.valid
        assert any("confianza" in issue for issue in result.issues)


def test_duplicate_headings_are_rejected():
    result = parse_ref_completion(VALID + "\nRESPUESTA: duplicada")
    assert not result.valid
    assert any("duplicado" in issue for issue in result.issues)


def test_decoded_requires_evidence_description():
    broken = VALID.replace("ESTADO_DE_CODIFICACION: clear", "ESTADO_DE_CODIFICACION: decoded")
    broken = broken.replace("EVIDENCIA: La fuente y la prueba experimental descritas permiten comprobarlo.", "EVIDENCIA: No tengo datos.")
    result = parse_ref_completion(broken)
    assert not result.valid
    assert any("decoded" in issue for issue in result.issues)


def test_audit_reports_structural_rate_without_claiming_truth():
    report, accepted = audit_records([
        {"id": "ok", "completion": VALID},
        {"id": "bad", "completion": "respuesta sin estructura"},
    ])
    assert report["records"] == 2
    assert report["valid_records"] == 1
    assert report["invalid_records"] == 1
    assert report["structural_validity_rate"] == 0.5
    assert [row["id"] for row in accepted] == ["ok"]
    assert "no demuestra verdad" in report["interpretation"]
    json.dumps(report)
