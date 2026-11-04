"""Pruebas del esquema de anotacion del filtro REF."""

import pytest

from ronin.epistemic import validate_annotation


def anotacion(**cambios):
    registro = {
        "record_id": "ejemplo-001",
        "text": "Todos los metales se dilatan al calentarse.",
        "source_id": "ejemplos-propios-ref",
        "source_sha256": "a" * 64,
        "license": "CC0-1.0",
        "epistemic_class": "falsifiable",
        "claim_type": "empirical",
        "genre": "scientific",
        "encoding_status": "clear",
        "potential_falsifier": "Medir un metal bajo condiciones controladas y no observar dilatacion.",
        "evidence_required": "Mediciones con temperatura y material especificados.",
        "confidence": 0.95,
        "annotator": "ronin-project",
        "policy_version": "0.1.0",
    }
    registro.update(cambios)
    return registro


def test_acepta_afirmacion_falsable_con_posible_refutacion():
    validate_annotation(anotacion())


def test_no_confunde_genero_religioso_con_no_falsabilidad():
    registro = anotacion(
        text="El manuscrito afirma que el preparado cambia de color al calentarlo.",
        genre="religious",
        claim_type="procedural",
        potential_falsifier="Repetir el procedimiento y comprobar si cambia de color.",
    )
    validate_annotation(registro)


def test_un_texto_codificado_no_se_marca_como_descifrado_sin_evidencia():
    registro = anotacion(
        text="Toma el leon verde y abre la puerta de mercurio.",
        genre="technical",
        claim_type="procedural",
        epistemic_class="undetermined",
        encoding_status="possibly_encoded",
    )
    validate_annotation(registro)


def test_decodificado_exige_evidencia():
    with pytest.raises(ValueError, match="decoding_evidence"):
        validate_annotation(anotacion(encoding_status="decoded"))


def test_falsable_exige_criterio_de_refutacion():
    with pytest.raises(ValueError, match="criterio de refutacion"):
        validate_annotation(anotacion(potential_falsifier=""))


def test_rechaza_sha256_invalido():
    with pytest.raises(ValueError, match="source_sha256"):
        validate_annotation(anotacion(source_sha256="no-es-un-hash"))


def test_rechaza_confianza_fuera_de_rango():
    with pytest.raises(ValueError, match="confidence"):
        validate_annotation(anotacion(confidence=1.5))


def test_rechaza_campos_ausentes():
    registro = anotacion()
    del registro["license"]
    with pytest.raises(ValueError, match="license"):
        validate_annotation(registro)


def test_rechaza_intervalo_invalido():
    with pytest.raises(ValueError, match="intervalo"):
        validate_annotation(anotacion(span_start=4, span_end=400))
