# Bibliotecas de datos de RONIN

Este directorio es el registro operativo de adquisición, revisión, admisión y preparación de corpus para RONIN. **Los recuentos distinguen documentos admitidos a nivel de fuente, documentos listos para entrenamiento y candidatos. No deben sumarse categorías que puedan solaparse ni confundirse con el inventario Level A de las 64 bibliotecas.**

> Corte documental: 5 de noviembre de 2026. Los manifiestos enlazados son la fuente de verdad; esta página resume su estado y no sustituye sus hashes ni decisiones por documento.

## Estado actual — cifras verificadas

| Fuente / corpus | Documentos | Estado documental | ¿Entrenable ahora? |
|---|---:|---|---|
| Literatura española legacy (`literature-es-v1`) | 608 train (+18 validation y 18 test aislados) | Admitido Level A scoped; 140.295.523 bytes train | Sí, bajo su alcance de corpus y controles; G-0 global sigue bloqueando la elegibilidad de las 64 bibliotecas |
| Lean mathlib4 (`mathlib4-v1`) | 8.697 admitidos (8.498 train, 91 validation, 108 test; 2 retenidos) | Admitido scoped; 97.629.252 bytes train; Apache-2.0; 8.650 matemáticas + 47 lógica | Sí, solo la partición train de este manifiesto; G-0 global sigue FAIL |
| NASA NTRS public-use | 813 de 824 | Admisión scoped con revisión del propietario; 11 retenidos; 32.313.859 bytes | No: recheck de redistribución, deduplicación cruzada y controles globales pendientes |
| Papers propios | 9 Markdown (README excluido) | Incorporados con autorización del propietario; 750.857 bytes, 93.499 palabras | No: deduplicación global y gates de calidad/privacidad/particionado pendientes |
| NASA file-reviewed | 6 | Revisión documental acotada; 701.871 bytes | No; no sumar a NASA NTRS sin resolver posible solapamiento |
| ScienceVerse | 7.403 textos en 13 colecciones; 7.365 admitidos scoped, 38 retenidos | Derechos por DOI y atribución auditados; 446.092.799 bytes admitidos | No: particiones y gates globales pendientes |

**Cómo leer los totales:** hay **10.127 registros admitidos scoped** en los cuatro manifiestos principales (608 literatura + 8.697 mathlib4 + 813 NASA + 9 Papers). La cifra **entrenable por partición** es **9.106 documentos**: 608 literatura + 8.498 mathlib4; validation/test permanecen aislados. No es un recuento global de documentos únicos ni un G-0 global PASS. Los seis NASA file-reviewed se muestran aparte por posible solapamiento. ScienceVerse registra 7.365 admitidos scoped, pero aún no entrenables; no se suman al total principal de entrenamiento.

### ScienceVerse: calidad automática no equivale a permiso

La auditoría consolidada registra 13 colecciones y 7.403 documentos; 7.365 pasan la admisión scoped por DOI/licencia/atribución y 38 quedan retenidos. Estos documentos todavía no son entrenables: faltan deduplicación near-duplicate global, particionado y gates globales. La admisión scoped no autoriza redistribución irrestricta.

| Colección | Textos examinados | Admitidos scoped | Retenidos |
|---|---:|---:|---:|
| BMC Medicine | 946 | 946 | 0 |
| Collabra | 666 | 666 | 0 |
| ECE3 | 26 | 25 | 1 |
| eLife | 654 | 648 | 6 |
| Frontiers | 155 | 155 | 0 |
| i-Perception | 489 | 489 | 0 |
| Judgment and Decision Making | 710 | 709 | 1 |
| Journal of Cognition | 427 | 423 | 4 |
| Open Mind | 293 | 291 | 2 |
| PLOS Biology | 970 | 970 | 0 |
| PLOS Medicine | 822 | 813 | 9 |
| PLOS ONE | 946 | 931 | 15 |
| Science Advances (SCAN) | 299 | 299 | 0 |
| **Total** | **7.403** | **7.365** | **38** |

Fuente de estos recuentos: `admitted/scienceverse-ccby-v1/manifest.json`. No confundir documentos admitidos scoped con documentos habilitados para entrenamiento.

## Bibliotecas objetivo: 32 dominios × General/HKD

El objetivo canónico es **64 bibliotecas**. General y HKD deben ser disjuntas globalmente, sin duplicados exactos ni near-duplicates compartidos. HKD se selecciona por densidad semántica RONIN, con desempate estable por identificador documental, y el reparto se equilibra por bytes UTF-8.

- Mínimo Level A: **1 MiB de texto admitido por biblioteca** (64 MiB en total).
- Objetivo de escala: 10 GiB por biblioteca (640 GiB en total).
- Estado del inventario Level A: **608 documentos / 140.295.523 bytes**, todos contabilizados en `humanities_general`; **1/64** bibliotecas alcanza el mínimo, 63 están por debajo.
- Bibliotecas training-eligible en el manifiesto de 64: **0/64**.
- Gate global G-0: **FAIL**.

El manifiesto `libraries/manifest-64.json` cuenta únicamente el corpus legacy Level A incorporado al inventario de bibliotecas. Los corpus NASA y Papers tienen admisión documental scoped en manifiestos separados, pero **no se han incorporado al contador Level A de 64 bibliotecas**. Esta distinción es intencional, no una omisión.

## Qué significa cada estado

| Estado | Significado | ¿Puede entrenar? |
|---|---|---|
| Admitido scoped | Documento aceptado dentro del alcance de su manifiesto de fuente, con procedencia y decisión registradas | Solo si el manifiesto de ese corpus y los gates aplicables autorizan la partición train |
| Level A en biblioteca | Payload incorporado al inventario de bibliotecas y contado tras superar el estándar Level A | Sujeto también a G-0 |
| Candidato | Texto descargado/localizado o extraído, pendiente de alguna comprobación | No |
| Calidad automática pass | Supera filtros mecánicos de integridad/estructura/calidad; no es admisión legal | No |
| Cuarentena / retenido | Derechos, privacidad, calidad, integridad o procedencia sin resolver | No |
| Solo metadatos | DOI, catálogo, índice o registro sin permiso verificado para usar el texto enlazado | No |

## Fuentes admitidas y sus límites

### Literatura española — `admitted/literature-es-v1/`

- 608 documentos de train, 140.295.523 bytes.
- 18 documentos de validation y 18 de test, aislados y nunca usados para entrenamiento.
- Procedencia fijada en CLiGS Textbox, CLiGS CONSSA y ELTeC-ESP; hashes, revisión y particiones documentados.
- Fue la base del entrenamiento legacy ya ejecutado. La reducción de BPB observada en ese experimento mide aprendizaje de patrones del corpus; no demuestra por sí sola razonamiento general.

### NASA NTRS — `admitted/nasa-ntrs-public-use-v1/`

- 824 textos completos en la adquisición original; el manifiesto vigente registra 813 admitidos scoped y 11 retenidos.
- 32.313.859 bytes de texto admitido; SHA-256 único dentro de la fuente.
- Se exige evidencia por documento de public-use, ausencia de material de terceros no autorizado, controles de exportación y revisión de información sensible.
- No entrenable todavía: falta recheck de redistribución en el snapshot de entrenamiento, deduplicación exacta/aproximada contra otras fuentes, revisión final y particionado General/HKD con train/validation/test disjuntos.

### Papers propios — `admitted/ronin-authored-papers-v1/`

- Se incorporan los nueve archivos Markdown de `orbitalronin94/Papers`; `README.md` está excluido expresamente.
- Revisión de origen fijada en `d7bf3ae446f666ce3be73b11aab7090e1605a889`; los blobs Git de origen coinciden con las copias.
- 9 documentos, 750.857 bytes UTF-8, 93.499 palabras; SHA-256 por documento.
- Autorización del propietario para el corpus interno de investigación/entrenamiento de RONIN. No implica permiso de redistribución externa ni derechos sobre contenido de terceros.
- No entrenable hasta completar deduplicación global, calidad/privacidad/citas, asignación y particionado y los gates globales.

### Lean mathlib4 — `admitted/mathlib4-v1/`

- 8.697 archivos Lean 4 admitidos desde `leanprover-community/mathlib4`, revisión inmutable `a84939a26903163e1b98ee002bc94e9563e75c12`.
- Licencia de repositorio Apache-2.0; SHA-256 por archivo y de LICENSE, autoría/cabeceras conservadas. 8.555 archivos contienen cabecera explícita Apache 2.0; los restantes quedan cubiertos por la licencia de repositorio fijada.
- 8.498 train (97.629.252 bytes), 91 validation (925.844 bytes) y 108 test (1.177.979 bytes). Dos módulos de reenvío menores de 100 caracteres quedaron retenidos.
- Dominios: 8.650 matemáticas y 47 lógica/epistemología. Cero duplicados exactos internos o contra los payloads admitidos existentes revisados; cero hallazgos de claves/tokens de alta confianza.
- Train es entrenable solo bajo este manifiesto scoped. Near-duplicate global, revisión humana línea por línea y G-0 global no se declaran superados.
- Artefacto de admisión: [run 42026633643](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42026633643); payload `ronin-admitted-mathlib4-v1`.

### NASA file-reviewed — `admitted/nasa-ntrs-file-reviewed-v1/`

- Seis documentos revisados individualmente, 701.871 bytes.
- Registro separado y acotado; `training_eligible=false` y no cuenta hacia el mínimo Level A.
- No sumarlo a los 807 NASA sin comprobar solapamiento documental.

## Candidatos y líneas de adquisición

Los números siguientes son **inventarios de candidatos**, no admisiones. Hay snapshots y exportaciones que pueden solaparse; no se suman entre sí sin deduplicación por hash/DOI.

### Payloads adquiridos y pendientes de revisión

| Línea | Adquisición comprobada | Estado y límites |
|---|---:|---|
| ScienceVerse / papers (RDS) | 3.087 DOI elegibles en cinco assets RDS; 95.948.088 bytes comprimidos | Exportación textual, derechos por artículo/versión, terceros, privacidad y calidad pendientes. No son bytes de texto admitido. |
| ScienceVerse (exportaciones de texto) | 9.153 documentos en 13 colecciones; 9.129 pases automáticos y 24 holds | Auditoría separada del lote RDS; posible solapamiento. 0 admitidos por derechos editoriales/terceros y revisión final pendientes. No sumar 3.087 + 9.153. |
| NASA NTRS | 824 textos completos; 39.262.382 bytes | 807 admitidos scoped en su manifiesto, 17 retenidos; además, seis revisados en un manifiesto separado. Los paquetes por biblioteca son candidatos y no deben sumarse de nuevo. |
| NASA NTRS — snapshot de expansión | 189 textos completos; 15.417.212 bytes | Lote candidato adicional registrado en el README de adquisición; reconciliar IDs/hashes contra los 824 antes de contarlo como incremento neto. |
| CoVoST 2 | Run posterior: 432.475 filas de traducción, 86.874.752 bytes | Solo campo `translation`; excluir audio, rutas, IDs de cliente y fuentes de oración. Un snapshot anterior registró 337.973 traducciones únicas repartidas en train/validation/test; reconciliar ambos snapshots antes de declarar un total único. |
| PleIAs Common Corpus | 2.159 filas, 5.971.320 bytes | 2.149 CC0, 4 CC BY 3.0 y 6 CC BY 4.0; 17.472 filas con licencias no permitidas, 311 con patrones básicos de email/teléfono y 8 inválidas/sobredimensionadas excluidas. Revisión humana, privacidad, calidad y splits pendientes. |
| GPLSI ClearText CAS/VAL | 17 documentos candidatos (11 CAS y 6 VAL) | Derechos de los documentos originales pendientes; un documento NC-ND en cuarentena. |
| UN Parallel Corpus | Workflow de ingestión en-es y validador incorporados | No atribuir un recuento de textos hasta que exista un run/artefacto verificado. La fuente declara dominio público para UN Parallel Corpus v1.0; siguen pendientes hashes, calidad, privacidad, deduplicación y particiones. |

**No existe un total global fiable de candidatos únicos.** El ledger de ingestión registra runs, artefactos y hashes por fuente; el número de filas de un snapshot no debe sumarse con otra exportación de la misma familia sin reconciliación.

### Fuentes adicionales de alta prioridad

- **NIST Technical Series / Public Data Repository:** línea favorable para informes y datos creados por NIST cuando el registro identifica autoría/titularidad NIST y se conserva la atribución. NIST advierte de material de terceros; no se admite el catálogo completo. Preflight por registro y payload pendiente.
- **USGS Publications Warehouse:** fuente de alto valor para geología, geografía, agua, riesgos naturales y ciencias de la Tierra. USGS confirma que sus informes publicados son generalmente de dominio público, pero advierte que algunas imágenes, ilustraciones y fotografías son de terceros. Seleccionar solo publicaciones USGS propias y excluir material mixto no aclarado.
- **NOAA Institutional Repository:** repositorio científico con texto completo; su política distingue obras gubernamentales CC0 de artículos y proceedings cuyos titulares conservan derechos. No usar el repositorio entero como corpus libre: selección por documento y revisión de copyright obligatorias.
- **BNE/BDH — Documentos en dominio público:** fuente oficial con distribuciones TXT y JSON; BNE describe el conjunto como obras en dominio público reutilizables bajo sus condiciones CC BY 4.0. El catálogo declara última actualización de distribución 2024-12-04. Nuevo workflow `ingest-bne-bdh-public-domain.yml` descarga ambos ZIP, fija SHA-256, extrae el TXT y ejecuta filtros de calidad/PII; hasta completar el enlace registro-texto, revisión de contenido/terceros, deduplicación global y splits, todo sigue como candidato y suma **0 entrenables**. No confundir licencia del catálogo con permiso de obras ajenas a este conjunto.
- **Project Gutenberg:** fuente de descubrimiento; verificar estado de dominio público aplicable en España/UE y derechos de traducción/edición concretos.
- **ParlaIbero-ES, DReaM-es-open, VoxPopuli y otras colecciones lingüísticas:** mantener en preflight hasta resolver licencia de cada documento/segmento, derechos de voz, privacidad y condiciones de redistribución.



## Objetivo operativo inmediato: ampliar el corpus realmente entrenable

No se considerará progreso el crecimiento de `candidates/`, el número de filas con licencia aparente ni los pases de filtros automáticos. El contador que importa es el de documentos con `training_eligible=true` en una partición `train` reproducible y con hashes comprobados.

- **Único corpus con partición train actualmente habilitada:** `literature-es-v1`, 608 documentos / 140.295.523 bytes. Sus 18 validation y 18 test permanecen excluidos.
- **NASA NTRS (809 scoped) y Papers propios (9):** no se contabilizan como entrenables mientras sus manifiestos mantengan `training_eligible=false`.
- **Siguiente fuente prioritaria:** conjunto oficial BNE *Biblioteca Digital. Documentos en dominio público*, que ofrece distribución TXT/XML de obras declaradas en dominio público y reutilización CC BY 4.0. Se debe adquirir el snapshot, fijar hashes, comprobar cada obra/edición y OCR, retirar aparato editorial/terceros dudosos, deduplicar globalmente y generar splits antes de promover. No se contará ni entrenará hasta superar esos controles.
- La política de adquisición queda así: primero fuentes con texto completo y permiso explícito sobre la obra, luego calidad verificable, y solo entonces admisión y entrenamiento. Los candidatos que no puedan cerrar los gates no desplazan este objetivo.

## Controles obligatorios antes de admitir y entrenar

1. Descarga pública anónima, sin credenciales, acuerdos privados ni condiciones de acceso restringidas.
2. Derechos/licencia del documento y versión exactos; no basta la licencia del catálogo o del repositorio.
3. Autoría, atribución, fuente, URL y revisión inmutable.
4. SHA-256 del payload y del texto normalizado.
5. Deduplicación exacta y aproximada contra todas las fuentes admitidas y los corpus de evaluación.
6. Revisión de PII, secretos, datos sensibles y contenido de terceros.
7. Calidad, idioma, codificación, OCR, ruido y relevancia temática.
8. Particiones deterministas y disjuntas; validation/test/holdout nunca se usan en entrenamiento.
9. Revisión humana y decisión por documento registradas.
10. Validación de manifiestos, separación General/HKD y gate global G-0.

Una licencia CC0/CC BY de metadatos no convierte automáticamente en reutilizable el contenido enlazado. Se mantienen separados textos, metadatos, código, voz, transcripciones y materiales de terceros.

## Estructura

- `admitted/`: corpus aceptados dentro del alcance explícito de sus manifiestos.
- `candidates/`: descargas, muestras y artefactos que aún no han superado todas las comprobaciones.
- `quarantine/`: material bloqueado o incompatible.
- `rights_registry/`: evidencia de derechos por fuente, versión y payload.
- `libraries/`: inventario canónico de 32 dominios × General/HKD.
- `reviews/`: auditorías, decisiones y attestations.

Los payloads grandes pueden publicarse como artefactos versionados de GitHub Actions. Cada artefacto debe acompañarse de hashes, manifiesto, revisión de fuente y decisión.

## Referencias canónicas

- [Inventario 32 dominios / 64 bibliotecas](libraries/manifest-64.json)
- [Auditoría de documentos candidatos — 2026-11-05](reviews/candidate-document-audit-2026-11-05.json)
- [Attestation de revisión del propietario](reviews/human-review-attestation-2026-11-05.json)
- [Revisión documental NASA](reviews/nasa-ntrs-file-review-2026-11-05.json)
- [Manifiesto literatura española](admitted/literature-es-v1/manifest.json)
- [Manifiesto NASA public-use](admitted/nasa-ntrs-public-use-v1/manifest.json)
- [Manifiesto Papers propios](admitted/ronin-authored-papers-v1/manifest.json)

## Decisión operativa

El corpus legacy de **608 documentos** continúa siendo la única fuente contabilizada en los mínimos Level A del inventario de 64 bibliotecas. Los corpus siguientes ya están admitidos en alcance documental propio, pero **no son entrenables ni se suman a esos mínimos** hasta cerrar G-0, deduplicación global y particionado:

- **NASA NTRS:** 813/824 admitidos; 32.313.859 bytes normalizados; 11 retenidos.
- **ScienceVerse:** 7.365/7.403 admitidos en 13 colecciones; 446.092.799 bytes de texto; 38 retenidos.
- **Papers propio:** 9/9 Markdown admitidos con autorización del propietario; README excluido; 750.857 bytes.

Los 7.365 ScienceVerse tienen DOI único, SHA-256 de texto único dentro de las 13 exportaciones, licencia por documento CC-BY-4.0 o CC0, atribución presente, filtro básico de PII superado y calidad textual suficiente. Se retienen 15 por autoría ausente, tres por anomalías de metadatos/privacidad/ruta temática y 20 por calidad. La attestation del propietario cubre la revisión humana de las fuentes mapeadas; el manifiesto mantiene trazabilidad por documento.

**No iniciar entrenamiento con estos corpus.** Siguen bloqueados por comparación exacta/aproximada contra todas las demás fuentes y holdouts, revalidación semanal de redistribución NASA, separación General/HKD y particiones deterministas train/validation/test. G-0 global continúa FAIL.

## Auditoría integral de candidatos (2026-11-05)

El workflow \`Audit and admit scoped candidate documents\` ejecutó correctamente la auditoría y materialización:

- NASA: [813 documentos admitidos en alcance acotado](admitted/nasa-ntrs-public-use-v1/manifest.json), 11 retenidos.
- ScienceVerse: [7.365 documentos admitidos en alcance acotado](admitted/scienceverse-ccby-v1/manifest.json), 38 retenidos.
- Papers: [9 documentos propios admitidos](admitted/ronin-authored-papers-v1/manifest.json), README excluido.
- Informe global por fuente y documento: [candidate-document-audit-2026-11-05.json](reviews/candidate-document-audit-2026-11-05.json).

Los payloads NASA y ScienceVerse preservan hashes del origen y del contenido admitido; los manifiestos marcan explícitamente \`training_eligible:false\`. La incorporación documental no implica promoción a entrenamiento ni altera los contadores Level A actuales.
