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

- **ScienceVerse:** 13 colecciones con payloads de texto y manifiestos por artículo. El filtro de calidad automática no resuelve derechos editoriales, titularidad, material de terceros ni privacidad. Admisiones actuales: cero.
- **NASA NTRS candidate packs:** cuatro bibliotecas General (astronomía/ciencias de la Tierra, química/materiales, ingeniería/robótica y física) fueron generadas como paquetes candidatos. No confundir estos paquetes con los 807 documentos ya admitidos scoped del manifiesto NASA; verificar hashes/solapamientos antes de consolidar.
- **CoVoST 2:** exportación limitada al campo `translation`; 337.973 traducciones únicas tras filtros (270.244 train, 34.051 validation, 33.678 test). Sigue como candidato; revisión humana final de muestras pendiente.
- **Common Corpus:** muestra acotada de 20.000 filas; derechos por documento, privacidad multilingüe, procedencia y calidad siguen pendientes. No promocionar automáticamente datos estructurados ni voz/transcripciones a prosa.
- **GPLSI ClearText:** documentos CAS/VAL candidatos. La licencia de la colección no resuelve derechos de los documentos originales; dos textos BOE permanecen en nivel B y un documento NC-ND en cuarentena.
- **ParlaIbero-ES, DReaM-es-open, VoxPopuli, BNE/BDH y Project Gutenberg:** líneas de preflight/adquisición; ninguna añade documentos Level A hasta verificar derechos del texto/edición, privacidad, calidad, hashes y particiones.
- **UN Parallel Corpus:** fuente oficial de interés y candidata a ingestión; todavía sin admisión documental completa, hashes de payload y controles finales.

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
