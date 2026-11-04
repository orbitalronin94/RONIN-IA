# Lógica, falacias y frases filosóficas: referencia operativa REF

## Estado y propósito

Este anexo convierte la propuesta de catálogo en una especificación de calibración para REF. Distingue entre (1) validez formal, (2) calidad/verdad de las premisas, (3) falacias argumentativas y (4) interpretación de frases filosóficas. Son tareas relacionadas, pero no intercambiables.

**No es un corpus de preentrenamiento ni una prueba suficiente de razonamiento general.** Los ejemplos creados para pruebas son fixtures sintéticos; no se incorporan al corpus de lenguaje ni al entrenamiento del modelo. Las frases atribuidas a autores requieren comprobación de texto, obra, sección, traducción y edición antes de convertirse en anotaciones de fuente. La lista bibliográfica mínima es una guía de verificación, no evidencia de que cada atribución del borrador esté confirmada.

## Contrato REF y discrepancias que se resuelven

El esquema ejecutable actual usa `encoding_status`, no `encoding_state`. Se conserva el nombre del esquema para evitar una segunda taxonomía. Los vocabularios válidos se importan de `ronin/epistemic/schema.py`; no se inventan etiquetas libres como `technical` si no están admitidas por el contrato.

Cada anotación debe incluir procedencia, SHA-256, licencia, anotador, versión de política y confianza. Si `epistemic_class=falsifiable`, debe incluir `potential_falsifier`; si `encoding_status=decoded`, debe incluir `decoding_evidence`. El validador solo comprueba estructura: no certifica la corrección filosófica ni lógica de una etiqueta.

## Ejes de evaluación

- **Validez formal:** comprobar si la conclusión se sigue de las premisas bajo una interpretación declarada. No equivale a que las premisas sean verdaderas.
- **Solidez:** validez más premisas verdaderas/justificadas.
- **Falacia formal:** patrón inválido por su forma (p. ej., afirmación del consecuente).
- **Falacia informal:** defecto de relevancia, presunción, ambigüedad o soporte probatorio; depende del contexto y puede no ser concluyente por una etiqueta superficial.
- **Causalidad y estadística:** exigir mecanismo, diseño, tasas base, incertidumbre, selección y comparaciones múltiples cuando proceda.
- **Frase filosófica:** separar cita literal, paráfrasis, interpretación y uso polémico. Una frase no debe etiquetarse como falsable solo por ser atribuible a un filósofo.

## Taxonomía de referencia

### Lógica proposicional y de predicados

Incluir como patrones positivos de validez: modus ponens, modus tollens, silogismo hipotético, silogismo disyuntivo, dilema constructivo, reducción al absurdo clásica, De Morgan, contraposición, conjunción, simplificación, adición, prueba condicional, exportación, absorción, distribución, conmutación, asociación, doble negación clásica, ex falso clásico y tercero excluido clásico.

Incluir condiciones de aplicación: distinguir condicional material de causalidad; disyunción inclusiva de exclusiva; lógica clásica de intuicionista/paraconsistente; alcance y existencia en cuantificadores; variables libres/ligadas; y restricciones de generalización. En silogística aristotélica, marcar explícitamente la presuposición existencial en modos como Darapti y Felapton.

### Falacias formales

Afirmación del consecuente; negación del antecedente; disyuntivo falaz; cuatro términos; término medio no distribuido; ilícitos mayor/menor; dos premisas negativas con conclusión afirmativa; y cambio de forma durante el argumento.

### Falacias informales

- **Relevancia:** ad hominem (abusivo/circunstancial/tu quoque), ad populum, ad baculum, ad misericordiam, ad verecundiam, ad ignorantiam, ad antiquitatem, ad novitatem, ad consequentiam, envenenar el pozo, hombre de paja, red herring, apelación al ridículo, repetición ad nauseam, intimidación, culpabilidad, deseo, incredulidad, falso prestigio y autoridad múltiple.
- **Ambigüedad:** equivocación, anfibología, énfasis, composición, división, accidente, accidente inverso, definición persuasiva/circular, definición demasiado amplia/estrecha, vaguedad y ambigüedad referencial, gramatical, semántica o pragmática.
- **Presunción:** petición de principio, círculo vicioso, premisa implícita, inversión de carga de prueba, falso dilema/dicotomía, perfeccionismo, nirvana, continuum, pendiente resbaladiza, conclusión desproporcionada y pregunta compleja/cargada.
- **Causalidad y evidencia:** post hoc, cum hoc, causa falsa/común/única, efecto conjuntivo, regresión a la media, selección y muestra sesgadas, sobregeneralización, supervivencia, confirmación, disponibilidad, anclaje, francotirador, profecía autocumplida y placebo.
- **Estadística:** tasa base, falacia del fiscal, divisor, media, ley de grandes números, jugador/apostador inverso, muestra pequeña, comparación múltiple, falacia ecológica/atomística, numerología, datos fabricados, p-hacking y HARKing.

No se debe marcar una falacia por coincidencia de palabras. Por ejemplo, una apelación a autoridad experta puede ser evidencia pertinente si la autoridad tiene competencia específica, el consenso es relevante y se ofrecen fuentes comprobables.

### Lógicas no clásicas y epistemología

Distinguir lógica intuicionista, paraconsistente, modal, epistémica, deóntica y temporal. No reducir sus diferencias a “errores”: evaluar cada argumento dentro del sistema declarado. Separar falsabilidad, verificabilidad, confirmacionismo, holismo Duhem–Quine, subdeterminación, carga teórica, inconmensurabilidad, programas de investigación, racionalidad limitada, heurísticas, calibración y actualización bayesiana.

### Frases filosóficas

El conjunto propuesto incluye atribuciones a Heráclito, Parménides, Sócrates/Platón, Aristóteles, Maquiavelo, Descartes, Spinoza, Hegel, Nietzsche, Wittgenstein, Heidegger, Sartre, Camus, Popper, Kuhn, Hanson, Duhem/Quine, Derrida, Foucault, Habermas, Rawls, Hobbes, Rousseau, Proudhon y Marx/Engels.

**Gate de atribución:** las formulaciones populares (“solo sé que no sé nada”, “el fin justifica los medios”, “la libertad es la consciencia de la necesidad”, etc.) pueden ser paráfrasis, traducciones libres o atribuciones apócrifas. No se registran como citas literales sin localización primaria. La interpretación y el “mal uso” son anotaciones editoriales, no propiedades objetivas de la cita.

## Diseño del experimento de calibración

1. Validar sintaxis JSONL y el contrato de `ronin/epistemic/schema.py`.
2. Mantener fixtures de desarrollo separados de corpus y de cualquier holdout.
3. Evaluar por familias (forma válida, falacia formal, relevancia, ambigüedad, presunción, causal/estadística, no clásica y cita/paráfrasis).
4. Añadir pares mínimos: mismo contenido con forma válida/inválida; misma autoridad dentro/fuera de competencia; correlación con/sin mecanismo; cita literal/paráfrasis/no verificada.
5. Mantener un pequeño conjunto adversarial oculto a la iteración de reglas. No usar el mismo catálogo para desarrollar y declarar generalización.
6. Reportar precisión, recall, F1 por clase/familia, matriz de confusión, cobertura, abstenciones y acuerdo entre anotadores. No reportar solo accuracy agregada.
7. Requerir doble anotación humana y adjudicación para el holdout. Las etiquetas de holdout no guían gradientes ni selección de hiperparámetros.
8. Solo después de una evaluación estable se considera una tarea auxiliar REF. Este experimento inicial no entrena ni modifica pesos.

## Criterio de aceptación inicial

La PR debe demostrar que los fixtures son válidos según el esquema y que las pruebas automatizadas detectan etiquetas/estructuras inválidas. **No** se declara que REF “está listo para el corpus grande” por acertar este catálogo. La generalización requiere ejemplos nuevos, composicionales y adversariales, evaluación humana independiente y resultados por familia.

## Fuentes para verificación

Aristóteles, *Organon* y *Metafísica*; Platón, *Apología*; Descartes, *Meditaciones metafísicas*; Spinoza, *Ética*; Hume, *Investigación sobre el entendimiento humano*; Kant, *Crítica de la razón pura*; Popper, *La lógica de la investigación científica*; Kuhn, *La estructura de las revoluciones científicas*; Wittgenstein, *Tractatus* e *Investigaciones filosóficas*; Kahneman, *Pensar rápido, pensar despacio*; Tversky y Kahneman (1974), “Judgment under Uncertainty”; NIST/SEMATECH, *e-Handbook of Statistical Methods*; Walton, *Informal Logic*; Hurley, *A Concise Introduction to Logic*.

Las referencias bibliográficas no sustituyen la verificación de página/sección, edición y derechos de cada cita.
