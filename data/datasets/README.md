# Bibliotecas de datos de RONIN

Este directorio es el registro operativo de adquisición, revisión, admisión y preparación de corpus para RONIN. **Los recuentos distinguen documentos admitidos a nivel de fuente, documentos listos para entrenamiento y candidatos. No deben sumarse categorías que puedan solaparse ni confundirse con el inventario Level A de las 64 bibliotecas.**

> Corte documental: 5 de noviembre de 2026. Los manifiestos enlazados son la fuente de verdad; esta página resume su estado y no sustituye sus hashes ni decisiones por documento.

## Estado actual — cifras verificadas

| Fuente / corpus | Documentos | Estado documental | ¿Entrenable ahora? |
|---|---:|---|---|
| Literatura española legacy (`literature-es-v1`) | 608 train (+18 validation y 18 test aislados) | Admitido Level A scoped; 140.295.523 bytes train | Sí, bajo su alcance de corpus y controles; G-0 global sigue bloqueando la elegibilidad de las 64 bibliotecas |
| NASA NTRS public-use | 807 de 824 | Admisión scoped con revisión del propietario; 17 retenidos; 32.211.588 bytes | No: recheck de redistribución, deduplicación cruzada y controles globales pendientes |
| Papers propios | 9 Markdown (README excluido) | Incorporados con autorización del propietario; 750.857 bytes, 93.499 palabras | No: deduplicación global y gates de calidad/privacidad/particionado pendientes |
| NASA file-reviewed | 6 | Revisión documental acotada; 701.871 bytes | No; no sumar a NASA NTRS sin resolver posible solapamiento |
| ScienceVerse | 9.153 textos en 13 colecciones auditadas | Candidatos; filtros automáticos de calidad ejecutados | No: 0 admitidos; derechos editoriales, terceros y revisión final pendientes |

**Cómo leer el total:** 608 + 807 + 9 = **1.424 registros en los tres corpus principales con admisión documental registrada**. No es un recuento global de documentos únicos: la deduplicación entre fuentes todavía no está cerrada. Los seis NASA file-reviewed se muestran aparte y no se añaden al total por posible solapamiento. Tampoco se cuentan los 9.153 textos de ScienceVerse como admitidos.

### ScienceVerse: calidad automática no equivale a permiso

La auditoría de contenido registra 13 colecciones, con 9.153 documentos examinados. El filtro automático marcó 9.129 como *machine quality pass* y retuvo 24 por calidad; esto **no** equivale a una aprobación legal ni a admisión. En todas las colecciones la admisión permanece en cero porque falta resolver derechos editoriales por artículo, material de terceros y revisión final de privacidad/calidad.

| Colección | Textos examinados | Calidad automática pass | Hold | Admitidos |
|---|---:|---:|---:|---:|
| BMC Medicine | 946 | 946 | 0 | 0 |
| Collabra | 666 | 666 | 0 | 0 |
| ECE3 | 26 | 26 | 0 | 0 |
| eLife | 654 | 654 | 0 | 0 |
| Frontiers | 155 | 155 | 0 | 0 |
| i-Perception | 489 | 489 | 0 | 0 |
| Judgment and Decision Making | 710 | 710 | 0 | 0 |
| Journal of Cognition | 427 | 427 | 0 | 0 |
| Open Mind | 293 | 293 | 0 | 0 |
| PLOS Biology | 970 | 970 | 0 | 0 |
| PLOS Medicine | 822 | 817 | 5 | 0 |
| PLOS ONE | 946 | 931 | 15 | 0 |
| Science Advances (SCAN) | 299 | 299 | 0 | 0 |
| **Total** | **9.153** | **9.129** | **24** | **0** |

Fuente de estos recuentos: `reviews/candidate-document-audit-2026-11-05.json`. No usar el total antiguo de 4.855 registros: correspondía a un corte anterior de adquisiciones y no representa el inventario actual de textos examinados.

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

- 824 textos completos en la adquisición original; 807 admitidos scoped y 17 retenidos.
- 32.211.588 bytes de texto admitido; SHA-256 único dentro de la fuente.
- Se exige evidencia por documento de public-use, ausencia de material de terceros no autorizado, controles de exportación y revisión de información sensible.
- No entrenable todavía: falta recheck de redistribución en el snapshot de entrenamiento, deduplicación exacta/aproximada contra otras fuentes, revisión final y particionado General/HKD con train/validation/test disjuntos.

### Papers propios — `admitted/ronin-authored-papers-v1/`

- Se incorporan los nueve archivos Markdown de `orbitalronin94/Papers`; `README.md` está excluido expresamente.
- Revisión de origen fijada en `d7bf3ae446f666ce3be73b11aab7090e1605a889`; los blobs Git de origen coinciden con las copias.
- 9 documentos, 750.857 bytes UTF-8, 93.499 palabras; SHA-256 por documento.
- Autorización del propietario para el corpus interno de investigación/entrenamiento de RONIN. No implica permiso de redistribución externa ni derechos sobre contenido de terceros.
- No entrenable hasta completar deduplicación global, calidad/privacidad/citas, asignación y particionado y los gates globales.

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
- **BNE/BDH y Project Gutenberg:** continúan como fuentes de descubrimiento. Las licencias de metadatos o la presencia en un catálogo no autorizan automáticamente el texto, la traducción ni la edición concreta; revisar obra/edición y situación en España/UE.
- **ParlaIbero-ES, DReaM-es-open, VoxPopuli y otras colecciones lingüísticas:** mantener en preflight hasta resolver licencia de cada documento/segmento, derechos de voz, privacidad y condiciones de redistribución.


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

El corpus legacy de 608 documentos continúa siendo la única fuente contabilizada en el inventario Level A de las 64 bibliotecas. NASA (807) y Papers (9) están admitidos en el alcance documental de sus propios manifiestos, pero no se suman todavía a ese inventario ni se consideran entrenables. ScienceVerse dispone de 9.153 textos auditados y 9.129 pases automáticos de calidad, pero cero admisiones.

**No se debe iniciar un nuevo entrenamiento con los corpus nuevos hasta que se cierren los gates aplicables y G-0.** La prioridad es resolver la admisión legal/técnica por documento, deduplicación global y particionado, y después incorporar el contenido válido a General/HKD sin contaminar validation/test/holdout.
