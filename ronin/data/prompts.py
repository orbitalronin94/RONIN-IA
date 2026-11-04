"""Currículo determinista y multidominio para tutores de RONIN."""

from __future__ import annotations

# Los dominios se equilibran por construcción: el orden recorre todos antes de
# repetirlos. Son temas de generación, no afirmaciones verificadas.
DOMAINS = {
    "matemáticas": (
        "demostrar por qué la suma de dos números impares es par",
        "distinguir una correlación de una relación causal en datos",
        "explicar límites y continuidad con un ejemplo intuitivo",
        "resolver un sistema lineal y comprobar la solución",
    ),
    "física": (
        "explicar conservación de energía en un péndulo real",
        "distinguir masa, peso y fuerza gravitatoria",
        "describir qué evidencia apoya la relatividad especial",
        "explicar por qué un modelo físico tiene un dominio de validez",
    ),
    "química": (
        "distinguir elemento, compuesto y mezcla",
        "explicar qué cambia y qué se conserva en una reacción química",
        "interpretar el pH y sus límites como medida",
        "diferenciar una observación experimental de una explicación molecular",
    ),
    "biología y salud pública": (
        "explicar selección natural sin confundirla con progreso",
        "distinguir virus, bacterias y tratamientos antibióticos",
        "explicar cómo se evalúa la eficacia de una intervención sanitaria",
        "distinguir riesgo relativo y riesgo absoluto",
    ),
    "informática y programación": (
        "explicar invariantes y pruebas de una función",
        "comparar búsqueda binaria y búsqueda lineal",
        "describir complejidad temporal y sus supuestos",
        "explicar una API y los límites de sus garantías",
    ),
    "inteligencia artificial": (
        "distinguir entrenamiento, validación y prueba",
        "explicar sobreajuste y cómo detectarlo",
        "comparar precisión, exhaustividad y calibración",
        "describir riesgos de contaminación de datos y evaluación",
    ),
    "historia": (
        "evaluar una afirmación histórica usando fuentes primarias y secundarias",
        "distinguir cronología, causalidad e interpretación histórica",
        "explicar cómo se contrasta la autenticidad de un documento",
        "analizar cómo sesgo y conservación afectan a un archivo histórico",
    ),
    "filosofía y lógica": (
        "distinguir validez lógica y verdad de las premisas",
        "explicar qué hace falsable a una hipótesis empírica",
        "identificar una falacia sin caricaturizar el argumento",
        "distinguir una afirmación normativa de una descriptiva",
    ),
    "economía": (
        "explicar coste de oportunidad con un ejemplo",
        "distinguir inflación, nivel de precios y coste de vida",
        "explicar límites de una inferencia causal observacional",
        "comparar una predicción económica con una identidad contable",
    ),
    "derecho e instituciones": (
        "distinguir una norma, una sentencia y una opinión jurídica",
        "explicar por qué jurisdicción y fecha cambian una interpretación legal",
        "describir cómo verificar una cita normativa",
        "distinguir texto legal vigente de una propuesta legislativa",
    ),
    "lingüística y literatura": (
        "distinguir significado literal, metáfora y alegoría",
        "explicar cómo cambia el significado de una palabra históricamente",
        "analizar la fiabilidad de un narrador sin confundir ficción y documento",
        "describir límites de una traducción entre lenguas",
    ),
    "criptografía y seguridad": (
        "distinguir cifrado, codificación, hash y esteganografía",
        "explicar qué demuestra y qué no demuestra un análisis de frecuencia",
        "describir cómo se valida una hipótesis de descifrado",
        "explicar por qué una implementación puede fallar aunque el algoritmo sea sólido",
    ),
    "estadística y método científico": (
        "explicar intervalo de confianza sin interpretarlo como probabilidad posterior",
        "distinguir significación estadística y relevancia práctica",
        "describir preregistro, replicación y sesgo de publicación",
        "explicar cómo una muestra sesgada altera una conclusión",
    ),
    "geografía y clima": (
        "distinguir tiempo meteorológico y clima",
        "explicar atribución climática y sus incertidumbres",
        "interpretar una proyección sin presentarla como predicción exacta",
        "describir cómo escala espacial y temporal cambian un análisis",
    ),
    "arte y cultura": (
        "distinguir procedencia, atribución y autenticidad de una obra",
        "explicar cómo el contexto cambia la interpretación de un símbolo",
        "analizar una hipótesis iconográfica sin presentarla como hecho",
        "distinguir documentación histórica y lectura contemporánea",
    ),
    "ingeniería y sistemas": (
        "explicar análisis de modos de fallo y sus límites",
        "distinguir requisito, hipótesis de diseño y resultado de prueba",
        "describir márgenes de seguridad y factores de incertidumbre",
        "explicar cómo validar un sistema antes de desplegarlo",
    ),
}

TASKS = (
    "Explica el tema a una persona competente pero no especialista.",
    "Evalúa qué afirmaciones del tema son comprobables y cuáles dependen de interpretación.",
    "Compara dos enfoques habituales y señala cuándo deja de ser válida cada comparación.",
    "Construye un ejemplo y un contraejemplo que ayuden a detectar una comprensión superficial.",
)


def build_prompts(count: int) -> list[str]:
    """Genera un currículo reproducible y equilibrado entre dominios."""
    if count < 1 or count > 500:
        raise ValueError("count debe estar entre 1 y 500")
    topics = [
        (domain, topic)
        for domain, domain_topics in DOMAINS.items()
        for topic in domain_topics
    ]
    prompts: list[str] = []
    for index in range(count):
        domain, topic = topics[index % len(topics)]
        task = TASKS[(index // len(topics)) % len(TASKS)]
        prompts.append(
            f"Ejercicio {index + 1} del dominio «{domain}». Tema: {topic}. {task}\n\n"
            "Responde en castellano claro y con rigor. No inventes referencias, datos, "
            "experimentos ni consenso. Si no sabes algo, dilo y concreta qué dato falta. "
            "Separa observación, evidencia, inferencia, hipótesis y opinión. No conviertas "
            "una correlación en causalidad ni una metáfora en una afirmación literal. "
            "No fuerces una conclusión cuando la evidencia no alcance.\n\n"
            "Usa exactamente estos apartados:\n"
            "RESPUESTA: explicación y razonamiento.\n"
            "CLASE_EPISTEMICA: falsifiable, non_falsifiable, mixed o undetermined; "
            "justifica la elección y separa afirmaciones si son mixtas.\n"
            "TIPO_DE_AFIRMACION: empirical, causal, metaphysical, normative, "
            "metaphorical, fictional, mathematical, procedural, descriptive, mixed "
            "o unknown.\n"
            "GENERO: scientific, historical, religious, literary, legal, technical, "
            "philosophical, other o unknown.\n"
            "ESTADO_DE_CODIFICACION: clear, possibly_encoded, decoded o unknown; "
            "no marques decoded sin evidencia documentada.\n"
            "EVIDENCIA: qué respalda la respuesta y qué habría que consultar o medir.\n"
            "INCERTIDUMBRE: límites, supuestos y confianza razonada (0 a 1), sin "
            "fingir calibración estadística.\n"
            "POSIBLE_REFUTACION: si la afirmación es falsable, indica qué observación "
            "la pondría en duda; si no procede, explica por qué.\n"
            "REVISION: qué nueva evidencia te haría cambiar de conclusión.\n"
            "No presentes la clasificación del tutor como verdad certificada: es una "
            "propuesta que debe poder auditarse."
        )
    return prompts
