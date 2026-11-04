#!/usr/bin/env python3
"""Generate a seeded, structured algorithmic curriculum without external corpora.

The examples have mechanically checkable answers. This is useful for warm-start
and pipeline validation, but it is not a substitute for licensed real-world data.
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Callable

DOMAINS = (
    "mathematics",
    "logic_epistemology",
    "computer_science",
    "physics",
    "chemistry",
    "biology_medicine",
    "philosophy",
    "law_economics_social_sciences",
)


def is_prime(number: int) -> bool:
    if number < 2:
        return False
    return all(number % divisor for divisor in range(2, math.isqrt(number) + 1))


def math_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    operation = rng.choice(("add", "subtract", "multiply", "divide", "gcd", "mod", "prime"))
    if operation == "add":
        left, right = rng.randint(1, 99), rng.randint(1, 99)
        question = f"Calcula {left} + {right}." if language == "es" else f"Compute {left} + {right}."
        answer = str(left + right)
        explanation = f"La suma es {left + right}." if language == "es" else f"The sum is {left + right}."
    elif operation == "subtract":
        left, right = sorted((rng.randint(1, 99), rng.randint(1, 99)), reverse=True)
        question = f"Calcula {left} - {right}." if language == "es" else f"Compute {left} - {right}."
        answer = str(left - right)
        explanation = f"La diferencia es {left - right}." if language == "es" else f"The difference is {left - right}."
    elif operation == "multiply":
        left, right = rng.randint(2, 12), rng.randint(2, 12)
        question = f"Calcula {left} × {right}." if language == "es" else f"Compute {left} × {right}."
        answer = str(left * right)
        explanation = f"El producto es {left * right}." if language == "es" else f"The product is {left * right}."
    elif operation == "divide":
        divisor, quotient = rng.randint(2, 12), rng.randint(2, 30)
        dividend = divisor * quotient
        question = f"Calcula {dividend} ÷ {divisor}." if language == "es" else f"Compute {dividend} ÷ {divisor}."
        answer = str(quotient)
        explanation = f"La división es exacta: {dividend} = {divisor} × {quotient}." if language == "es" else f"The division is exact: {dividend} = {divisor} × {quotient}."
    elif operation == "gcd":
        left, right = rng.randint(12, 180), rng.randint(12, 180)
        answer = str(math.gcd(left, right))
        question = f"Calcula el máximo común divisor de {left} y {right}." if language == "es" else f"Find the greatest common divisor of {left} and {right}."
        explanation = f"El MCD es {answer}." if language == "es" else f"The GCD is {answer}."
    elif operation == "mod":
        modulus, value = rng.randint(2, 17), rng.randint(10, 300)
        answer = str(value % modulus)
        question = f"Calcula {value} módulo {modulus}." if language == "es" else f"Compute {value} modulo {modulus}."
        explanation = f"El resto de {value} entre {modulus} es {answer}." if language == "es" else f"The remainder of {value} divided by {modulus} is {answer}."
    else:
        value = rng.randint(1, 100)
        answer = "sí" if is_prime(value) else "no"
        if language == "en":
            answer = "yes" if is_prime(value) else "no"
        question = f"¿Es {value} un número primo?" if language == "es" else f"Is {value} a prime number?"
        explanation = (
            f"{value} es primo si solo tiene dos divisores positivos." if language == "es"
            else f"{value} is prime exactly when it has two positive divisors."
        )
    return question, answer, explanation


def logic_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    kind = rng.choice(("modus_ponens", "modus_tollens", "affirming_consequent", "conjunction"))
    if language == "es":
        p, q = "el sensor está activo", "la alarma está encendida"
        if kind == "modus_ponens":
            return (
                f"Si {p}, entonces {q}. {p}. ¿Qué se deduce?",
                q,
                "Es modus ponens: se afirma el antecedente y se deduce el consecuente.",
            )
        if kind == "modus_tollens":
            return (
                f"Si {p}, entonces {q}. No ocurre que {q}. ¿Qué se deduce?",
                f"No ocurre que {p}",
                "Es modus tollens: negar el consecuente permite negar el antecedente.",
            )
        if kind == "affirming_consequent":
            return (
                f"Si {p}, entonces {q}. {q}. ¿Se puede concluir que {p}?",
                "No",
                "Afirmar el consecuente es inválido: puede haber otras causas de la alarma.",
            )
        left, right = rng.choice(((True, True), (True, False), (False, True), (False, False)))
        answer = "verdadero" if left and right else "falso"
        return (
            f"Una conjunción P ∧ Q tiene P={left} y Q={right}. ¿Cuál es su valor?",
            answer,
            "Una conjunción solo es verdadera cuando ambos componentes son verdaderos.",
        )
    p, q = "the sensor is active", "the alarm is on"
    if kind == "modus_ponens":
        return (
            f"If {p}, then {q}. {p}. What follows?",
            q,
            "Modus ponens affirms the antecedent and derives the consequent.",
        )
    if kind == "modus_tollens":
        return (
            f"If {p}, then {q}. It is not the case that {q}. What follows?",
            f"It is not the case that {p}",
            "Modus tollens denies the consequent and derives the negation of the antecedent.",
        )
    if kind == "affirming_consequent":
        return (
            f"If {p}, then {q}. {q}. Can we conclude that {p}?",
            "No",
            "Affirming the consequent is invalid because other causes may explain the alarm.",
        )
    left, right = rng.choice(((True, True), (True, False), (False, True), (False, False)))
    answer = "true" if left and right else "false"
    return (
        f"A conjunction P AND Q has P={left} and Q={right}. What is its value?",
        answer,
        "A conjunction is true only when both components are true.",
    )


def computer_science_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    kind = rng.choice(("sort", "sum", "max", "binary_search", "complexity"))
    values = [rng.randint(0, 30) for _ in range(rng.randint(4, 7))]
    if kind == "sort":
        answer = str(sorted(values))
        if language == "es":
            return f"¿Qué devuelve sorted({values}) en Python?", answer, "sorted crea una nueva lista ordenada de menor a mayor."
        return f"What does sorted({values}) return in Python?", answer, "sorted creates a new list ordered from smallest to largest."
    if kind == "sum":
        answer = str(sum(values))
        if language == "es":
            return f"¿Qué devuelve sum({values}) en Python?", answer, "sum agrega todos los elementos numéricos de la lista."
        return f"What does sum({values}) return in Python?", answer, "sum adds all numeric elements in the list."
    if kind == "max":
        answer = str(max(values))
        if language == "es":
            return f"¿Qué devuelve max({values}) en Python?", answer, "max devuelve el elemento mayor."
        return f"What does max({values}) return in Python?", answer, "max returns the largest element."
    if kind == "binary_search":
        ordered = sorted(set(values))
        target = rng.choice(ordered)
        answer = str(ordered.index(target))
        if language == "es":
            return f"En {ordered}, ¿qué índice tiene {target} mediante búsqueda binaria?", answer, "La búsqueda binaria divide el intervalo ordenado hasta localizar el valor."
        return f"In {ordered}, what index contains {target} using binary search?", answer, "Binary search halves the sorted search interval until it finds the value."
    if language == "es":
        return "¿Cuál es la complejidad temporal de la búsqueda binaria en una lista ordenada?", "O(log n)", "Cada paso reduce a la mitad el intervalo de búsqueda."
    return "What is the time complexity of binary search on a sorted list?", "O(log n)", "Each step halves the remaining search interval."


def physics_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    kind = rng.choice(("force", "speed", "ohm", "density"))
    if kind == "force":
        mass, acceleration = rng.randint(1, 25), rng.randint(1, 12)
        result = mass * acceleration
        question = f"Una masa de {mass} kg acelera a {acceleration} m/s². ¿Qué fuerza neta actúa?" if language == "es" else f"A {mass} kg mass accelerates at {acceleration} m/s². What net force acts?"
        return question, f"{result} N", f"Por F=ma, {mass} × {acceleration} = {result} N." if language == "es" else f"By F=ma, {mass} × {acceleration} = {result} N."
    if kind == "speed":
        time = rng.randint(2, 20)
        speed = rng.randint(2, 30)
        distance = time * speed
        question = f"Un móvil recorre {distance} m en {time} s. ¿Cuál es su rapidez media?" if language == "es" else f"An object travels {distance} m in {time} s. What is its average speed?"
        return question, f"{speed} m/s", f"La rapidez es distancia/tiempo: {distance}/{time} = {speed} m/s." if language == "es" else f"Speed is distance/time: {distance}/{time} = {speed} m/s."
    if kind == "ohm":
        current, resistance = rng.randint(1, 10), rng.randint(2, 30)
        voltage = current * resistance
        question = f"Con I={current} A y R={resistance} Ω, ¿qué tensión V predice la ley de Ohm?" if language == "es" else f"With I={current} A and R={resistance} Ω, what voltage V follows from Ohm's law?"
        return question, f"{voltage} V", f"V=IR={current}×{resistance}={voltage} V." if language == "es" else f"V=IR={current}×{resistance}={voltage} V."
    volume, density = rng.randint(1, 20), rng.randint(1, 15)
    mass = volume * density
    question = f"Un material tiene volumen {volume} cm³ y densidad {density} g/cm³. ¿Qué masa tiene?" if language == "es" else f"A material has volume {volume} cm³ and density {density} g/cm³. What is its mass?"
    return question, f"{mass} g", f"m=ρV={density}×{volume}={mass} g." if language == "es" else f"m=ρV={density}×{volume}={mass} g."


def chemistry_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    formulae = {
        "H2O": 3, "CO2": 3, "CH4": 5, "NH3": 4,
        "C6H12O6": 24, "H2SO4": 7, "NaCl": 2, "O2": 2,
    }
    formula = rng.choice(tuple(formulae))
    atoms = formulae[formula]
    if rng.choice((True, False)):
        question = f"¿Cuántos átomos totales representa una molécula de {formula}?" if language == "es" else f"How many total atoms are in one molecule of {formula}?"
        answer = str(atoms)
        explanation = f"Se suman los subíndices de la fórmula: {atoms} átomos en total." if language == "es" else f"Add the formula subscripts: {atoms} atoms in total."
        return question, answer, explanation
    reactions = (
        ("2 H2 + O2 → 2 H2O", "2:1:2"),
        ("CH4 + 2 O2 → CO2 + 2 H2O", "1:2:1:2"),
        ("N2 + 3 H2 → 2 NH3", "1:3:2"),
        ("2 Na + Cl2 → 2 NaCl", "2:1:2"),
    )
    reaction, coefficients = rng.choice(reactions)
    question = f"¿Cuáles son los coeficientes mínimos de {reaction}?" if language == "es" else f"What are the smallest whole-number coefficients for {reaction}?"
    explanation = "Los coeficientes conservan el número de átomos de cada elemento." if language == "es" else "The coefficients conserve the number of atoms of each element."
    return question, coefficients, explanation


def biology_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    facts = (
        ("¿Qué orgánulo produce la mayor parte del ATP en células eucariotas?", "mitocondria", "La respiración celular mitocondrial produce gran parte del ATP.", "Which organelle produces most ATP in eukaryotic cells?", "mitochondrion", "Mitochondrial cellular respiration produces much of the cell's ATP."),
        ("¿Qué bases se aparean en el ADN?", "A-T y C-G", "En el ADN, adenina se aparea con timina y citosina con guanina.", "Which bases pair in DNA?", "A-T and C-G", "In DNA, adenine pairs with thymine and cytosine pairs with guanine."),
        ("¿Qué base del ARN ocupa el lugar de la timina?", "uracilo", "El ARN utiliza uracilo en lugar de timina.", "Which RNA base replaces thymine?", "uracil", "RNA uses uracil instead of thymine."),
        ("¿Cuántas células hijas produce normalmente la mitosis?", "2", "La mitosis produce dos células hijas genéticamente muy similares.", "How many daughter cells does mitosis normally produce?", "2", "Mitosis produces two genetically similar daughter cells."),
        ("¿Cuántas células haploides produce normalmente la meiosis?", "4", "La meiosis comprende dos divisiones y suele producir cuatro células haploides.", "How many haploid cells does meiosis normally produce?", "4", "Meiosis has two divisions and normally produces four haploid cells."),
    )
    es_question, es_answer, es_reason, en_question, en_answer, en_reason = rng.choice(facts)
    return (es_question, es_answer, es_reason) if language == "es" else (en_question, en_answer, en_reason)


def philosophy_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    facts = (
        ("¿Qué exige el criterio de falsabilidad asociado a Popper?", "Que una hipótesis pueda entrar en conflicto con alguna observación posible.", "Una afirmación falsable especifica qué evidencia podría mostrar que es falsa.", "What does the falsifiability criterion associated with Popper require?", "A hypothesis must be capable of conflicting with some possible observation.", "A falsifiable claim specifies evidence that could show it to be false."),
        ("¿Qué distingue una inferencia deductiva válida?", "Si las premisas son verdaderas, la conclusión se sigue necesariamente.", "La validez depende de la forma lógica del argumento.", "What distinguishes a valid deductive inference?", "If the premises are true, the conclusion follows necessarily.", "Validity depends on the logical form of the argument."),
        ("¿Qué obtiene normalmente una inferencia inductiva?", "Una conclusión probable basada en observaciones, no una garantía lógica.", "La inducción generaliza desde casos observados y puede revisarse con nueva evidencia.", "What does an inductive inference normally produce?", "A probable conclusion based on observations, not a logical guarantee.", "Induction generalizes from observed cases and can be revised by new evidence."),
        ("¿La correlación demuestra por sí sola causalidad?", "No.", "Una asociación puede deberse a confusión, causalidad inversa o coincidencia.", "Does correlation alone establish causation?", "No.", "An association may arise from confounding, reverse causality, or coincidence."),
    )
    es_question, es_answer, es_reason, en_question, en_answer, en_reason = rng.choice(facts)
    return (es_question, es_answer, es_reason) if language == "es" else (en_question, en_answer, en_reason)


def social_science_record(rng: random.Random, language: str) -> tuple[str, str, str]:
    facts = (
        ("¿Qué es el coste de oportunidad?", "El valor de la mejor alternativa a la que se renuncia.", "Elegir una opción implica renunciar a la mejor alternativa disponible.", "What is opportunity cost?", "The value of the best alternative that is forgone.", "Choosing one option means giving up the best available alternative."),
        ("¿Qué mide el producto interior bruto (PIB)?", "El valor de mercado de los bienes y servicios finales producidos dentro de un territorio durante un periodo.", "El PIB mide producción final dentro de una economía en un intervalo temporal.", "What does gross domestic product (GDP) measure?", "The market value of final goods and services produced within a territory over a period.", "GDP measures final production within an economy over a time interval."),
        ("¿Qué significa inflación sostenida?", "Un aumento general y persistente del nivel de precios.", "Cuando el nivel general de precios aumenta, el poder adquisitivo de una unidad monetaria disminuye.", "What is sustained inflation?", "A general and persistent increase in the price level.", "When the general price level rises, the purchasing power of a unit of money falls."),
        ("¿Qué define la ventaja comparativa?", "Producir un bien con menor coste de oportunidad que otro productor.", "La ventaja comparativa depende del coste de oportunidad relativo, no solo de la productividad absoluta.", "What defines comparative advantage?", "Producing a good at a lower opportunity cost than another producer.", "Comparative advantage depends on relative opportunity cost, not only absolute productivity."),
        ("¿Qué expresa el principio del Estado de derecho?", "Que los poderes públicos están sujetos a normas jurídicas públicas y aplicables.", "La aplicación concreta varía por jurisdicción, pero el poder público no queda fuera del derecho.", "What does the rule-of-law principle express?", "Public authorities are subject to public and applicable legal rules.", "Its implementation varies by jurisdiction, but public power is not outside the law."),
    )
    es_question, es_answer, es_reason, en_question, en_answer, en_reason = rng.choice(facts)
    return (es_question, es_answer, es_reason) if language == "es" else (en_question, en_answer, en_reason)


GENERATORS: dict[str, Callable[[random.Random, str], tuple[str, str, str]]] = {
    "mathematics": math_record,
    "logic_epistemology": logic_record,
    "computer_science": computer_science_record,
    "physics": physics_record,
    "chemistry": chemistry_record,
    "biology_medicine": biology_record,
    "philosophy": philosophy_record,
    "law_economics_social_sciences": social_science_record,
}


def make_text(seed: int, sentences: int) -> str:
    if sentences < 1:
        raise ValueError("sentences must be positive")
    rng = random.Random(seed)
    schedule = list(DOMAINS) * ((sentences + len(DOMAINS) - 1) // len(DOMAINS))
    rng.shuffle(schedule)
    rows = []
    for index in range(sentences):
        domain = schedule[index]
        language = rng.choice(("es", "en"))
        question, answer, explanation = GENERATORS[domain](rng, language)
        rows.append(
            f"[Registro {index:06d} | dominio={domain} | idioma={language}]\n"
            f"Pregunta: {question}\n"
            f"Respuesta: {answer}\n"
            f"Explicación: {explanation}\n"
        )
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-sentences", type=int, default=12000)
    parser.add_argument("--validation-sentences", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=8675309)
    args = parser.parse_args()
    if args.train_sentences < 100 or args.validation_sentences < 100:
        parser.error("cada partición necesita al menos 100 registros")
    args.output.mkdir(parents=True, exist_ok=True)
    train = make_text(args.seed, args.train_sentences)
    validation = make_text(args.seed + 1, args.validation_sentences)
    (args.output / "train.txt").write_text(train, encoding="utf-8")
    (args.output / "validation.txt").write_text(validation, encoding="utf-8")
    print(
        f"Currículo sintético estructurado: train={len(train)} bytes, "
        f"validation={len(validation)} bytes; semilla={args.seed}; "
        f"dominios={len(DOMAINS)}"
    )


if __name__ == "__main__":
    main()
