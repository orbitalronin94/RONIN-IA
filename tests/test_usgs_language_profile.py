from scripts.acquire_public_sources import language_profile


def test_language_profile_detects_spanish_and_english():
    spanish = language_profile(
        ("El mapa muestra las zonas de riesgo durante las lluvias intensas. "
         "La evaluación se basa en datos de campo y análisis de terreno. ") * 3
    )
    english = language_profile(
        ("The map shows areas of risk during intense rainfall. "
         "The assessment is based on field data and terrain analysis. ") * 3
    )
    assert spanish["detected_language"] == "Spanish"
    assert english["detected_language"] == "English"
