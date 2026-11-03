"""Small deterministic Spanish curriculum for the first tutor-generated corpus."""

from __future__ import annotations

TOPICS = (
    "la diferencia entre una variable y una constante en programación",
    "cómo funciona el ciclo del agua y por qué es importante",
    "qué es una fracción y cómo se suma con un ejemplo",
    "la diferencia entre correlación y causalidad",
    "cómo funciona una búsqueda binaria y cuándo usarla",
    "qué significa que un algoritmo tenga complejidad O(n)",
    "por qué las estaciones del año no se deben principalmente a la distancia al Sol",
    "cómo identificar la idea principal de un texto",
    "qué es una célula y cuáles son sus partes básicas",
    "cómo resolver una ecuación lineal sencilla paso a paso",
    "qué diferencia hay entre memoria RAM y almacenamiento",
    "cómo funciona la fotosíntesis de forma sencilla",
    "qué es una función matemática y cómo interpretar su gráfica",
    "cómo escribir una hipótesis comprobable para un experimento",
    "qué es una API y para qué sirve en un programa",
    "cómo detectar una falacia de falsa causa en un argumento",
    "qué diferencia hay entre cifrado y codificación",
    "cómo se calcula un porcentaje con un ejemplo cotidiano",
    "qué es una base de datos relacional y qué es una tabla",
    "cómo explicar un concepto técnico a una persona principiante",
)


def build_prompts(count: int) -> list[str]:
    """Return a deterministic set of varied prompts in Spanish."""
    if count < 1 or count > 500:
        raise ValueError("count must be between 1 and 500")
    prompts = []
    for index in range(count):
        topic = TOPICS[index % len(TOPICS)]
        prompts.append(
            f"Ejercicio educativo {index + 1}. Explica {topic}. "
            "Organiza la respuesta en: explicación, ejemplo concreto y una advertencia "
            "sobre un error común. Usa lenguaje natural, evita afirmaciones dudosas "
            "y mantén la respuesta entre 80 y 160 palabras."
        )
    return prompts
