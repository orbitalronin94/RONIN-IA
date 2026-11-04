> **Estado actualizado (4 de noviembre de 2026):** este documento conserva la propuesta bibliográfica y el validador preparatorio de ocho bibliotecas de una iteración anterior. El gate oficial vigente es el de **16 bibliotecas** descrito en `data/manifests/sixteen_libraries.json`; este manifiesto de ocho no autoriza RUN #5 ni sustituye el gate oficial. El validador de este documento es auxiliar y no debe conectarse al workflow oficial.

# Ocho bibliotecas técnicas balanceadas y Portfolio experto

## Decisión experimental

No se crea ni se ejecuta RUN #5 hasta que existan **ocho bibliotecas de conocimiento independientes**, cada una con un corpus de entrenamiento aprobado de tamaño comparable, más **Portfolio/Papers como corpus experto adicional**. Portfolio no cuenta como una de las ocho.

El presupuesto inicial se fija en 8.118.117 bytes UTF-8 por biblioteca, referencia del corpus Portfolio medido en la auditoría previa. Cada biblioteca debe quedar dentro de ±10 % de ese objetivo. Se mide el `train.txt` normalizado y deduplicado, no el ZIP ni el artefacto comprimido. El manifiesto `data/manifests/balanced_technical_libraries.json` es la fuente de verdad.

El gate exige ocho de ocho bibliotecas admitidas, tamaño dentro del presupuesto, derechos verificados por documento, SHA-256, deduplicación, split independiente y Portfolio presente como extra. Ninguna biblioteca puede rellenarse con validación, test, benchmarks, texto sintético de humo ni salidas de tutor no verificadas.

## Las ocho bibliotecas

1. **Matemáticas**: álgebra, geometría, análisis, teoría de números, combinatoria, probabilidad, estadística, optimización y métodos numéricos.
2. **Lógica y razonamiento**: lógica proposicional y de predicados, pruebas, silogística, falacias formales e informales, lógica modal, intuicionista, paraconsistente, epistémica, deóntica y temporal.
3. **Filosofía y epistemología**: falsabilidad, inducción, causalidad, filosofía de la ciencia, ética, metafísica y argumentación.
4. **Física**: mecánica, electromagnetismo, termodinámica, física estadística, cuántica, relatividad, óptica y medición.
5. **Química y materiales**: química general, orgánica, inorgánica, física, analítica, ciencia de materiales e historia de la química.
6. **Biología y medicina**: genética, evolución, fisiología, medicina, salud pública, farmacología y neurociencia.
7. **Informática e ingeniería**: algoritmos, estructuras de datos, lenguajes, ingeniería de software, arquitectura, ciberseguridad, control y electrónica.
8. **Derecho, economía y ciencias sociales**: jurisprudencia, economía, teoría de juegos, política pública, inferencia causal y metodología social.

Los dominios que retrocedieron en el último ciclo se convierten en prioridades explícitas: informática, matemáticas y filosofía. No se asumirá que añadir más texto de un dominio garantiza mejorar; se medirán retención, transferencia y regresión por dominio.

## Programa bibliográfico: matemáticas y lógica

La lista es un mapa de localización, no una declaración de que cualquier edición o traducción esté libre de derechos. Se priorizarán originales de dominio público y ediciones digitales cuya situación jurídica en España esté acreditada. Cada traducción, prólogo, notas, aparato crítico y digitalización se revisará por separado.

### Matemáticas
- Euclides — *Elementos*.
- Diofanto — *Arithmetica*.
- Al-Juarismi — tratados algebraicos, con traducción/edición revisada.
- René Descartes — *La Géométrie*.
- Isaac Newton — *Philosophiæ Naturalis Principia Mathematica*.
- Leonhard Euler — *Introductio in analysin infinitorum*; *Institutiones calculi differentialis*.
- Joseph-Louis Lagrange — *Mécanique analytique*.
- Pierre-Simon Laplace — *Mécanique céleste*.
- Carl Friedrich Gauss — *Disquisitiones Arithmeticae*.
- Augustin-Louis Cauchy — *Cours d'Analyse*.
- Bernhard Riemann — *Über die Hypothesen, welche der Geometrie zu Grunde liegen*.
- Richard Dedekind — *Was sind und was sollen die Zahlen?*.
- Georg Cantor — trabajos sobre teoría de conjuntos.
- Henri Poincaré — *Science et méthode* y trabajos matemáticos.
- David Hilbert — *Grundlagen der Geometrie*.
- Emmy Noether — trabajos originales, con publicación y derechos verificados.
- George Pólya — *How to Solve It*: referencia curricular; no descargar texto moderno sin permiso.
- Nicolas Bourbaki y manuales contemporáneos: bibliografía/metadatos únicamente salvo licencia expresa.

### Lógica, demostración y argumentación
- Aristóteles — *Organon*, *Analíticos primeros* y *Analíticos posteriores*.
- George Boole — *The Mathematical Analysis of Logic* y *The Laws of Thought*.
- Augustus De Morgan — *Formal Logic*.
- Gottlob Frege — *Begriffsschrift* (edición y traducción concretas).
- Charles S. Peirce — escritos lógicos publicados en dominio público, seleccionados por documento.
- Bertrand Russell — *The Principles of Mathematics* (verificar edición y derechos).
- Alfred Tarski — *Introduction to Logic* (solo edición con derechos compatibles).
- Stephen Kleene — *Introduction to Metamathematics* (no asumir dominio público).
- Irving Copi, Patrick Hurley y textos modernos de lógica informal: referencias bibliográficas; no descargar sin licencia.
- Douglas Walton — lógica informal y esquemas argumentativos: referencias/metadatos hasta verificar derechos.

## Glosario confirmado que se incorpora al currículo

El currículo existente en `ronin/data/prompts.py` ya contiene **16 dominios y 64 temas (cuatro por dominio)**: matemáticas; física; química; biología y salud pública; informática y programación; inteligencia artificial; historia; filosofía y lógica; economía; derecho e instituciones; lingüística y literatura; criptografía y seguridad; estadística y método científico; geografía y clima; arte y cultura; ingeniería y sistemas. Se preservan los 64 temas existentes y se amplían con las subáreas bibliográficas de este documento. No se reemplaza el currículo ni se pierde su cobertura.

Se conserva la taxonomía ejecutable REF; no se inventan etiquetas incompatibles con `ronin/epistemic/schema.py`.

- **Lógica formal**: modus ponens, modus tollens, silogismo hipotético/disyuntivo, dilema constructivo, reducción al absurdo, De Morgan, contraposición, cuantificadores, variables libres/ligadas y restricciones de generalización.
- **Falacias formales**: afirmación del consecuente, negación del antecedente, término medio no distribuido, cuatro términos, ilícitos mayor/menor y errores de distribución.
- **Falacias informales**: relevancia, ambigüedad, presunción, causalidad/evidencia y estadística; ad hominem, hombre de paja, falso dilema, petición de principio, carga de prueba, post hoc, muestra sesgada, supervivencia, tasa base, falacia ecológica, p-hacking y HARKing.
- **Lógicas no clásicas**: intuicionista, paraconsistente, modal, epistémica, deóntica y temporal.
- **Epistemología**: falsabilidad, verificabilidad, confirmacionismo, Duhem–Quine, subdeterminación, carga teórica, inconmensurabilidad, programas de investigación, racionalidad limitada, heurísticas, calibración y actualización bayesiana.
- **Criptografía y opacidad**: cifrado frente a codificación, hash y esteganografía; análisis de frecuencia; criptoanálisis; acrósticos; nomenclatura alquímica; hipótesis de descifrado y evidencia documental. La biblioteca existente de 506 registros (400 sintéticos y solo 6 casos históricos en el conjunto original) permanece en cuarentena: no se cuenta como biblioteca técnica admitida hasta ampliar casos históricos verificados y revisar OCR, edición, derechos y hashes.
- **REF**: `epistemic_class` = falsifiable/non_falsifiable/mixed/undetermined; `claim_type` = empirical/causal/metaphysical/normative/metaphorical/fictional/mathematical/procedural/descriptive/mixed/unknown; `genre` y `encoding_status` se mantienen en sus vocabularios versionados.

El glosario de frases filosóficas no se convierte en citas literales sin localizar obra, sección, edición y traducción. Las atribuciones apócrifas quedan fuera de entrenamiento.

## Stack de software propuesto

Las dependencias nuevas se agrupan como extras opcionales; no se cargan en el núcleo ni se instalan todas en cada runner. Esto conserva el arranque CPU ligero y permite instalar solo el módulo utilizado.

- Matemáticas simbólicas y numéricas: SymPy, SciPy, mpmath.
- Restricciones y lógica: Z3 Solver, NetworkX.
- Estadística y evaluación: scikit-learn, statsmodels, evaluate.
- Datos y formatos: datasets, Hugging Face Hub, PyArrow, Polars.
- Libros y extracción: pypdf, PyMuPDF, lxml, BeautifulSoup.
- Tokenización: tokenizers y SentencePiece.
- Entrenamiento: Accelerate (sin asumir GPU ni entrenamiento distribuido disponible).
- Serialización: safetensors y orjson.

Cada dependencia debe tener versión acotada, licencia revisada, prueba de importación y justificación de uso. No se añadirá una librería solo por aparecer en una lista.

## Admisión y medición

Para cada documento: URL/origen, edición, autoría y colaboradores, licencia o fundamento de dominio público, jurisdicción, fecha de recuperación, SHA-256 del original, extractor/OCR y versión, calidad de texto, SHA-256 normalizado y partición. El corpus de Portfolio mantiene su autorización y revisión de terceros separadas.

La preparación por biblioteca debe:
1. filtrar derechos por documento;
2. extraer y normalizar texto conservando fórmulas, tablas y estructura matemática;
3. deduplicar entre bibliotecas y contra los corpus existentes;
4. asignar particiones por obra/fuente, nunca por fragmentos aleatorios;
5. limitar el train a 8.118.117 bytes ±10 % por biblioteca;
6. registrar bytes antes/después, descartes, cobertura temática y hashes;
7. mantener el holdout externo MMLU-Pro intacto.

Comprobación del inventario: `python scripts/validate_balanced_libraries.py`.
Gate estricto para RUN #5: `python scripts/validate_balanced_libraries.py --require-ready`.

Estado inicial: 0/8 bibliotecas admitidas; gate cerrado. La biblioteca criptográfica y los casos de opacidad no se usan como relleno de bytes ni se confunden con datos históricos verificados. La documentación y el inventario no equivalen a datos descargados ni autorizados.
