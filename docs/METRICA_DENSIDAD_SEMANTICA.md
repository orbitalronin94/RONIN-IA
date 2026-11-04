# Selección de conocimiento de alta densidad — RONIN-HKD

Fecha: 4 de noviembre de 2026. Estado: prototipo de selección; todavía no validado como predictor de mejora del modelo.

## Objetivo

Crear ocho bibliotecas adicionales a las ocho bibliotecas base. Cada una conserva el dominio correspondiente, pero se deriva de fuentes de volumen muy grande seleccionando documentos y fragmentos con alta concentración de conocimiento, no simplemente textos largos o keyword stuffing.

Las 16 bibliotecas deben alcanzar al menos 256 MiB de texto train deduplicado cada una (objetivo 1 GiB). La biblioteca adicional de cada dominio se denomina `<dominio>_hkd`. Portfolio/Papers sigue siendo un índice de recuperación RAG de experto, no una fuente de pesos ni una de las 16.

## Base científica

1. Duan et al. (2025), *Enhancing LLMs via High-Knowledge Data Selection*, AAAI 39(22), 23832–23840, DOI [10.1609/aaai.v39i22.34555](https://doi.org/10.1609/aaai.v39i22.34555). Propone High-Knowledge Scorer, con elementos de conocimiento, densidad y cobertura. RONIN adopta la idea de medir conocimiento y cobertura, pero no afirma reproducir su modelo.
2. Xie et al. (2023), *Data Selection for Language Models via Importance Resampling*, NeurIPS 36, DOI [10.52202/075280-1482](https://doi.org/10.52202/075280-1482). DSIR selecciona según distribución objetivo mediante features n-gram hashed y reducción KL; el paper informa de 100M documentos en 4,5 horas. RONIN adopta relevancia del dominio y selección trazable, no implementa el algoritmo DSIR completo.
3. Lai et al. (2020), *Diversity, Density, and Homogeneity: Quantitative Characteristic Metrics for Text Collections*, LREC, pp. 1739–1746. Motiva medir densidad junto con diversidad/homogeneidad para evitar una colección repetitiva.

## Métrica inicial RONIN-HKD-0.1

`semantic_density = 100 × (0.25 R + 0.30 K + 0.15 S + 0.15 I + 0.15 C)`

Cada componente se normaliza al intervalo [0,1]:

- **R — Domain relevance (25%)**: coincidencia de vocabulario y señales específicas del dominio.
- **K — Knowledge-unit density (30%)**: definiciones, relaciones causales, condicionales, teoremas/pruebas, procedimientos, ecuaciones y unidades informativas por longitud.
- **S — Specificity (15%)**: magnitudes, relaciones explícitas, símbolos/ecuaciones y entidades concretas.
- **I — Information content (15%)**: IDF del vocabulario frente al conjunto candidato; reduce el peso de palabras genéricas.
- **C — Structure/coherence proxy (15%)**: longitud útil, estructura de oraciones y legibilidad estructural.

La puntuación no mide verdad. Una frase falsa puede parecer densa; por eso se exige revisión humana, procedencia y evidencia. Tampoco sustituye las licencias. El filtro legal se ejecuta antes de puntuar y rechaza cualquier licencia ausente o no incluida en la allowlist.

## Pipeline y reproducibilidad

- `data/manifests/knowledge_dense_sources.json`: inventario de adaptadores por fuente, dominio, campos y allowlists.
- `scripts/select_knowledge_dense_corpus.py`: selector de una fuente/dominio. Admite JSONL local y Hugging Face streaming. Usa SQLite temporal en disco para no acumular el corpus completo en RAM; calcula IDF del lote y escribe `train.txt` y un informe con SHA-256.
- `scripts/harvest_knowledge_dense_libraries.py`: orquesta las ocho bibliotecas derivadas y escribe un índice.
- `data/manifests/sixteen_libraries.json`: gate oficial de las 16 bibliotecas.
- `scripts/validate_sixteen_libraries.py --require-ready --corpus-root <ruta>`: exige las 16 admitidas, tamaño mínimo, hashes, auditoría, y para las ocho HKD también hash del informe de selección y revisión humana.

Todos los adaptadores están desactivados por defecto. Para habilitar una fuente se exige: revisión inmutable, esquema real inspeccionado, campo de licencia o prueba jurídica de licencia a nivel de repositorio/archivo, allowlist compatible, procedencia estable y auditoría registrada. Un dataset que carece de metadatos de licencia por documento no se habilita por comodidad.

El selector no publica corpus ni los incluye en Git. Los cuerpos se almacenan como artefactos/datasets externos con manifiestos y hashes. No se aceptan tokens, secretos, credenciales, datos personales sensibles ni contenido con malware.

## Cómo validar la métrica

Antes de incorporarla al entrenamiento:

1. Muestrear al menos 200 fragmentos por dominio, estratificados por deciles de puntuación.
2. Revisión ciega por dos evaluadores: pertinencia, densidad de conocimiento, corrección aparente, contexto suficiente, duplicación y utilidad didáctica.
3. Calcular correlación de Spearman entre HKD y valoración humana, además de acuerdo interevaluador.
4. Comparar contra selección aleatoria, filtro de longitud, filtro de keywords y baseline de calidad simple.
5. Construir subset de entrenamiento de igual número de bytes/tokens por brazo.
6. Hacer ablación controlada con mismo modelo, seed, tokens, pasos y holdout fijo. Reportar mejora por dominio y regresiones.
7. Si HKD no supera baselines o crea sesgo/repetición, cambiar pesos/umbrales y versionar la métrica; no forzar su admisión.

## Fuentes de alta escala previstas

| Dominio | Fuentes candidatas para extracción HKD | Restricción dominante |
|---|---|---|
| Matemáticas | OpenWebMath; MathPile por shard | ODC-By/condiciones upstream; licencias heredadas de MathPile |
| Lógica/epistemología | ProofPile-2 por fuente; Lean mathlib | Licencias heredadas; Apache-2.0 y dependencias |
| Filosofía | PleIAs Spanish-PD-Books; Common Corpus OpenCulture | Derechos por obra, edición y traducción; licencia documental |
| Física | arXiv por artículo; Common Corpus OpenScience | Licencia individual y contenido de terceros |
| Química/materiales | PMC OA; PatentsView | CC0/CC-BY por artículo; términos y material de terceros en patentes |
| Biología/medicina | PMC OA; Europe PMC OA | Licencia por artículo; deduplicación cruzada |
| Informática/software | The Stack v2; Common Corpus OpenSource | SPDX por archivo, opt-outs, secretos y blobs SWHID |
| Derecho/economía/social | Common Corpus OpenGovernment; Harvard CAP | Derechos por documento, jurisdicción, PII y vigencia legal |

La inclusión en la tabla no significa que una fuente esté aprobada. En esta revisión todos los adaptadores están `enabled=false` hasta verificar sus campos y licencias reales.

## Estado actual

- 8 bibliotecas base: candidatas; aún no admitidas.
- 8 bibliotecas HKD: manifiesto creado; cero bytes admitidos.
- Portfolio: RAG de experto; no training.
- RUN #5 / entrenamiento oficial: bloqueado. No ejecutar ni mergear la PR hasta que el gate de 16 bibliotecas esté completo y CI valide el protocolo.
