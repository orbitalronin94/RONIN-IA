# Programa bibliográfico y glosario técnico RONIN

Documento curricular de referencia. **No constituye autorización de descarga ni de entrenamiento**: cada obra, edición, traducción y material complementario requiere revisión individual de derechos y procedencia.

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

## Uso dentro del proyecto

Este programa sirve para localizar y priorizar obras, no para declarar corpus admitidos. La única puerta de admisión vigente es `data/manifests/sixteen_libraries.json` junto con `scripts/validate_sixteen_libraries.py --require-ready`. La bibliografía no modifica `training_eligible`, no rellena tamaños mínimos y no autoriza a descargar traducciones, ediciones críticas ni materiales de terceros. Portfolio/Papers sigue reservado a RAG experto.

Las referencias modernas o con derechos vigentes se conservan como metadatos curriculares hasta disponer de una licencia o autorización específica. Los originales históricos también requieren verificar edición, digitalización, jurisdicción y procedencia.
