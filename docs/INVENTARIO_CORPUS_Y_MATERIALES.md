# Inventario de corpus y materiales de RONIN-IA

**Corte de auditoría:** 4 de noviembre de 2026, aproximadamente 12:04 UTC.  
**Rama con la integración más reciente:** `ronin/integrate-all-corpora-phi4-cycle`, [PR #39](https://github.com/orbitalronin94/RONIN-IA/pull/39).  
**Estado:** la PR sigue abierta; los resultados de esta ficha no implican que todo esté fusionado en `main`.

Este documento es el índice maestro para preparar mezclas reproducibles. No contiene textos de terceros ni pesos: apunta a manifiestos y artefactos temporales de Actions. Su espejo estructurado para herramientas es [data/manifests/corpus_inventory.json](../data/manifests/corpus_inventory.json). La regla central es no mezclar corpus de entrenamiento, holdouts de evaluación, material auxiliar y benchmarks.

## Resumen ejecutivo

| Material | Inventario observado | Uso permitido en el flujo actual | Estado |
|---|---:|---|---|
| Portfolio/Papers | 48 documentos utilizables | Entrenamiento únicamente | Autorización expresa del titular registrada; revisión de terceros pendiente por documento |
| CLiGS Textbox | 364 documentos preparados | Parte de los 608 train totales; reparto por fuente no publicado en el resumen | Integrado y auditado |
| CoNSSA | 184 documentos preparados | Train dentro del total de literatura | Integrado y auditado |
| ELTeC-spa | 96 documentos preparados | Train dentro del total de literatura | Integrado y auditado |
| Literatura abierta conjunta | 644 documentos: 608 train, 18 validation, 18 test | Preentrenamiento + validación/test literarios separados | Descarga verificada en Actions |
| Salidas opcionales de Phi-4 | Tamaño variable, generado durante el ciclo | Augmentación candidata, no conocimiento certificado | Tutor MIT verificado; salida sin licencia presumida y con auditoría REF |
| Biblioteca de codificación/opacidad | 6 fuentes originales; 506 registros estructurados | Investigación auxiliar separada | Excluida del preentrenamiento general hasta revisión manual |
| Corpus sintético de pseudopalabras | 12.000 train + 2.000 validation en el smoke documentado | Smoke técnico exclusivamente | Excluido del entrenamiento general |
| MMLU-Pro | 140 preguntas por defecto en el ciclo | Evaluación externa; nunca entrenamiento | Holdout de benchmark |
| Benchmark multidominio RONIN | 23 preguntas piloto | Smoke de evaluación | Demasiado pequeño para afirmar capacidad general |
| Fuentes históricas candidatas | Catálogo de autores/obras, sin ingesta masiva | Investigación y catalogación | Pendiente de derechos, OCR y hashes |
| PleIAs Spanish Public Domain Books | 302.640 obras declaradas por la ficha | Candidata de adquisición por fragmentos | PR #13 abierta; no integrada en el ciclo actual |

**Importante:** 364 + 184 + 96 = 644 documentos. Los 608 registros de train no se suman otra vez a esos 644: son su partición de entrenamiento. Los 18 validation y 18 test quedan fuera del entrenamiento.

## 1. Corpus de entrenamiento principal

### 1.1 Portfolio/Papers — material propio autorizado

- Origen: [orbitalronin94/Portfolio/Papers](https://github.com/orbitalronin94/Portfolio/tree/main/Papers).
- Revisión fijada: `fffc234fdf3f82b6a90d56ae9b190d1c0de79690`.
- Inventario de origen: 49 elementos; el preparador informa 48 documentos utilizables.
- Formatos procesables: Markdown/MDX, TXT, RST, HTML, TeX, PDF y miembros textuales de ZIP.
- Preparación: omite binarios no textuales, duplicados exactos, documentos demasiado cortos y coincidencias con patrones de credenciales; genera `train.txt` y `manifest.json` con SHA-256 por documento y corpus.
- Partición: **solo train**. No dividir aleatoriamente este conjunto en validation/test porque los documentos pueden compartir pasajes o compendiarse entre sí.
- Autorización: el titular del repositorio autorizó expresamente el uso de sus aportaciones originales. Esa autorización no cubre automáticamente citas, imágenes, tablas, código, traducciones ni otros materiales de terceros incluidos dentro de los documentos.
- Riesgo de calidad: el contenido mezcla hipótesis, propuestas, experimentos, manuales y opiniones. La ingesta no certifica la verdad de sus afirmaciones.

Guía: [Corpus propio Portfolio/Papers](CORPUS_PROPIO_PORTFOLIO.md). Workflow: [Preparar corpus propio de Portfolio](../.github/workflows/prepare-portfolio-corpus.yml).

### 1.2 Literatura de dominio público: tres fuentes integradas

Las revisiones de los repositorios se fijan en el preparador. Las licencias de los textos se declaran como dominio público; el marcado/metadatos TEI se declara CC BY 4.0. La verificación jurídica se refiere a las obras admitidas, no convierte automáticamente cualquier material futuro del repositorio en dominio público.

| Fuente | Repositorio | Revisión fijada | Documentos preparados |
|---|---|---|---:|
| CLiGS Textbox | [cligs/textbox](https://github.com/cligs/textbox) | `1b91e940475c8a7e866457a3953fed5edb0a29f1` | 364 |
| CoNSSA | [cligs/conssa](https://github.com/cligs/conssa) | `8fccf669ed1bdbad309ff190f5afb0d6066d70a3` | 184 |
| ELTeC-spa | [COST-ELTeC/ELTeC-spa](https://github.com/COST-ELTeC/ELTeC-spa) | `83e2a22d5ef66f96e59f47f7ef810358c4236322` | 96 |
| **Total** | | | **644** |

Particiones medidas por Actions:
- `train`: 608 documentos.
- `validation`: 18 documentos.
- `test`: 18 documentos.
- 40 archivos/fragmentos omitidos por filtros de calidad, duplicación o seguridad, según la auditoría de adquisición previa documentada en [Fuentes abiertas](FUENTES_CORPUS_ABIERTOS.md).

El preparador extrae XML TEI, separa relatos individuales cuando procede, deduplica por contenido y mantiene en una misma partición los fragmentos del mismo archivo de origen para reducir fuga de información. Registra revisión, licencia, procedencia, SHA-256 de archivos originales y SHA-256 de las salidas.

**Artefactos auditados:** [Actions — auditoría de descargas run #145](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41825919840). Incluye:
- `ronin-corpus-v2-particiones`: corpus preparado y particiones; ZIP de 58.181.685 bytes.
- `ronin-bibliotecas-adquiridas`: manifiestos y biblioteca auxiliar; ZIP de 92.503 bytes.
- `ronin-biblioteca-opacidad-v1`: fuentes y registros auxiliares; ZIP de 203.231.066 bytes.

Los artefactos de Actions son temporales y sujetos a su retención; no son parte de Git ni checkpoints distribuibles.

## 2. Tutores locales y texto generado

### 2.1 Modelos auxiliares

El caché de tutores incorpora:
- `openai-community/gpt2` (`gpt2`).
- `EleutherAI/gpt-neo-125m` (`gpt-neo-125m`).
- `microsoft/Phi-4-mini-instruct` (`phi-4-mini-instruct`, aproximadamente 3,8B parámetros).

El workflow fija Transformers **4.53.3** para compatibilidad con Phi-4. La descarga exige licencia MIT verificada, revisión inmutable y hashes SHA-256 de todos los archivos/shards. La verificación de integridad del caché no equivale a una auditoría de seguridad del código remoto: Phi-4 usa `trust_remote_code=True`, por lo que se debe mantener aislado y revisar el código y su procedencia.

Workflow: [Preparar caché de tutores](../.github/workflows/cache-teachers.yml). Guía: [Teacher workflow](TEACHER_WORKFLOW.md).

### 2.2 Salidas de tutor

Phi-4 se usa como generador local opcional de propuestas de texto para augmentación. El manifiesto debe conservar modelo, revisión, URL de licencia, licencia del modelo, procedencia, hash y estado REF. La salida generada se etiqueta `not_asserted`: **no se le atribuye automáticamente la licencia MIT del modelo ni se considera verdad verificada**.

La PR #39 diseña el fallback para que, si Phi-4 falla, el ciclo base continúe con Portfolio + literatura y deje constancia de que no hubo augmentación. Las salidas requieren revisión humana, deduplicación, filtrado de seguridad y decisión jurídica antes de incorporarse a un corpus estable.

## 3. Material especializado de codificación y opacidad

La auditoría de adquisición descargó seis fuentes, todas con SHA-256:
1. Poe, *The Gold-Bug* (texto de la obra; criptograma ficticio resuelto dentro del relato).
2. Verne, *La Jangada* en francés (criptograma ficticio; no atribuir al autor la invención histórica del método).
3. Conan Doyle, *The Adventure of the Dancing Men* (cifrado ficticio).
4. *Hypnerotomachia Poliphili* (1499; acróstico observable, interpretación de autoría no concluyente).
5. Trithemius, *Steganographia* (edición/fuente histórica; distinguir los libros y las soluciones documentadas).
6. Selenus, *Cryptomenytices et Cryptographiae libri IX* (1624; testimonio histórico).

Tamaño de descargas registrado: aprox. 236 MB en total. El generador construyó **506 registros** con particiones **404 train / 50 validation / 52 test**; la validación estructural REF terminó sin errores. Esto es una biblioteca de casos especializada, no texto de preentrenamiento general.

**Estado de entrenamiento:** todos los seis originales llevan `excluded_pending_manual_review`. El paso siguiente es OCR/revisión de edición, licencia, correspondencia entre transcripción y fuente, evidencia de solución y gate de admisión. No mezclar con Portfolio ni con literatura general mientras siga ese estado.

Guías: [Casos de codificación documentada](CASOS_CODIFICACION_DOCUMENTADA.md), [Auditoría REF](AUDITORIA_REF.md), [esquema REF](REF_SCHEMA_MAPPING.md).

## 4. Corpus sintético

El generador `scripts/prepare_synthetic_corpus.py` crea pseudopalabras reproducibles. El smoke del workflow produce 12.000 frases train y 2.000 validation con semilla `8675309`. Su manifiesto lo marca `excluded_from_general_training` y declara explícitamente que no aporta conocimiento lingüístico.

Uso: probar tokenización, batches, pérdida, checkpoints y determinismo. No mezclarlo con el corpus lingüístico real ni usarlo para justificar conocimiento o generalización.

## 5. Evaluación: mantenerla fuera del entrenamiento

| Conjunto | Tamaño | Papel | Regla |
|---|---:|---|---|
| MMLU-Pro | 140 preguntas por defecto; el workflow permite ampliar al test completo | Evaluación externa antes/después | No gradientes, no selección de prompts ni ajuste sobre el test |
| Literatura validation | 18 documentos | Medición de modelado de lenguaje | Solo validación |
| Literatura test | 18 documentos | Holdout literario | No tocar durante entrenamiento/selección |
| Piloto multidominio `domains_v1.jsonl` | 23 preguntas en 15 dominios | Smoke de capacidades | No es benchmark robusto ni corpus de entrenamiento |
| Casos opacidad validation/test | 50/52 registros | Evaluación especializada futura | Separados de train; el conjunto entero sigue sujeto a revisión de admisión |

MMLU-Pro tiene revisión inmutable documentada en [Benchmark MMLU-Pro](BENCHMARK_MMLU_PRO.md). El piloto de 23 preguntas tiene azar uniforme del 25 % y no mide razonamiento abierto.

## 6. Fuentes candidatas, bloqueadas o en cuarentena

### 6.1 G-0 bloquea las cuatro colecciones auditadas

`reports/license_audit.json` cubre cuatro fuentes propuestas y no autoriza su adquisición:
- Project Gutenberg: revisar derechos por ebook y jurisdicción; no asumir dominio público en España por ser PD-US.
- Internet Archive: revisar derechos por ítem y distinguir obra, escaneo y transcripción.
- PleIAs Common Corpus: multilicencia; filtrar por documento y jurisdicción.
- BookCorpusOpen: no se acredita una licencia general de reutilización.

Estado general G-0: no descargar ni entrenar con estas colecciones hasta que exista evidencia suficiente y el gate sea aprobado. Informe: [license_audit.json](../reports/license_audit.json).

### 6.2 Otras candidatas catalogadas, no integradas

El catálogo [Fuentes abiertas de corpus](FUENTES_CORPUS_ABIERTOS.md) menciona, entre otras:
- PleIAs Spanish Public Domain Books y Spanish Public Domain Newspapers: grandes; adquisición por fragmentos y revisión de derechos/OCR. La PR #13 está abierta y no equivale a integración.
- BNE / Biblioteca Digital Hispánica: usar solo obras concretas con derechos y OCR comprobados.
- Corpus Adela Zamudio y colección de estilometría: candidatas pequeñas; verificar fuente y licencia por obra.
- Maria Silvia v1 (CC0): posible ajuste instructivo posterior, no mezclar directamente con preentrenamiento.
- Common Voice español (CC0 según espejo): solo transcripciones, revisar el espejo y la fuente.
- BOE: candidata jurídica, revisar condiciones de reutilización.
- Congreso: derechos de intervenciones y condiciones por aclarar.
- Wikipedia español / ELG: compatibilidad de licencia pendiente.
- HPLT español: volumen excesivo para la iteración CPU y necesita auditoría de procedencia.
- DReaM-es-open: falta una vía de descarga textual directa verificada.
- Mozilla Finance Sentences: requiere cuenta, aceptación de términos y API key; no es parte del flujo anónimo de adquisición ni del ciclo integrado.

### 6.3 Biblioteca histórica de autores y obras

`CORPUS_HISTORICO.md` lista BNE, BDH, BVPH, Europeana, Project Gutenberg y Wikisource como catálogos para localizar obras. No es un corpus descargado. Cada obra requiere autoría, fecha de fallecimiento, traducción, edición, derechos del objeto digital, OCR, revisión y SHA-256 propios.

## 7. Mezcla reproducible: reglas para el artefacto conjunto

El script `scripts/prepare_training_mixture.py` construye una mezcla a partir de entradas nombradas y genera un manifiesto con procedencia y hashes. Reglas:
1. Incluir únicamente archivos train aprobados; el script rechaza rutas que indiquen `validation`, `test`, `eval` o `benchmark`.
2. Portfolio y literatura se mantienen como fuentes identificables, no se sobrescriben sus manifiestos originales.
3. No volver a concatenar el artefacto corpus-v2 si sus tres SHA-256 coinciden con las particiones actuales: se duplicaría el material.
4. Las salidas de Phi-4 se incorporan solo si se generaron, se auditaron y pasaron los gates; si no, registrar augmentación ausente.
5. La biblioteca de codificación, los pseudodatos sintéticos, los benchmarks y los holdouts no entran en el preentrenamiento general.
6. Guardar SHA-256 de cada entrada y de la mezcla final, revisiones, proporciones y semilla del mezclador.
7. Publicar manifiestos e informes; mantener textos completos y checkpoints como artefactos temporales, no en Git.

### Artefactos de Actions relevantes

- [Auditoría de adquisición, run #145](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41825919840) — corpus literario y biblioteca especializada.
- [CI, run #351](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41825919819) — 100 tests, smoke CPU y Ruff en verde.
- [Primera iteración/benchmark, run #126](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41825919786) — smoke tiny completado.
- [Ciclo de entrenamiento y MMLU-Pro, run #59](https://github.com/orbitalronin94/RONIN-IA/actions/runs/41825919709) — terminó con fallo: Phi-4 no pudo generar texto porque `generator` no es un argumento aceptado por el modelo; después MMLU-Pro no pudo importar `BucketNotFoundError` desde `huggingface_hub.errors`. No se generó el informe final ni el artefacto `ronin-portfolio-mmlu-training-cycle`.
- [PR #39: integración de corpus + Phi-4](https://github.com/orbitalronin94/RONIN-IA/pull/39).

## 8. Decisión de uso resumida

- **Entrenar ahora en el ciclo integrado:** Portfolio/Papers autorizado (train únicamente) + train de las tres fuentes literarias integradas, sujeto a los manifiestos y checks de la PR #39.
- **Augmentación opcional:** propuestas de Phi-4, solo con procedencia y auditoría; no atribuir licencia automática a la salida.
- **Mantener separado:** biblioteca de codificación, corpus sintético, validation/test literarios, MMLU-Pro y piloto multidominio.
- **No descargar/no entrenar:** cuatro colecciones G-0 bloqueadas.
- **No considerar integrado:** PleIAs PD Books, Mozilla Finance Sentences y las demás candidatas hasta completar su propio gate.

La PR #39 debe corregir la compatibilidad de generación Phi-4 y fijar una combinación compatible de `datasets`/`huggingface_hub`, repetir el ciclo y generar el manifiesto final antes de describir la mezcla Portfolio + literatura + Phi-4 como pipeline estable de `main`. Los artefactos de adquisición separados sí existen; el artefacto consolidado del ciclo no se produjo.
