# Bibliotecas de datos de RONIN

Este directorio es el registro operativo de adquisición, revisión, admisión y preparación de corpus para RONIN. **Los recuentos distinguen documentos admitidos a nivel de fuente, documentos listos para entrenamiento y candidatos. No deben sumarse categorías que puedan solaparse. Esta es la única raíz canónica de datos: `data/datasets/`.**

> Corte documental: 6 de noviembre de 2026. Los manifiestos enlazados son la fuente de verdad; esta página resume su estado y no sustituye sus hashes ni decisiones por documento.

## Estado actual — cifras verificadas

| Fuente / corpus | Documentos | Estado documental | ¿Entrenable ahora? |
|---|---:|---|---|
| Literatura española legacy (`literature-es-v1`) | 608 train (+18 validation y 18 test aislados) | Admitido Level A scoped; 140.295.523 bytes train | Sí, bajo su alcance de corpus y controles; la validación global del inventario de bibliotecas sigue pendiente |
| Lean mathlib4 (`mathlib4-v1`) | 8.697 admitidos (8.498 train, 91 validation, 108 test; 2 retenidos) | Admitido scoped; 97.629.252 bytes train; Apache-2.0; 8.650 matemáticas + 47 lógica | Sí, solo la partición train de este manifiesto; la validación global del inventario sigue pendiente |
| NASA NTRS public-use | 813 de 824 scoped; 6 train file-reviewed; 807 aún no train | 6 documentos / 701.870 bytes en dos manifiestos file-reviewed; 4 OCR/rights holds | Sí, solo los 6 archivos revisados; recheck semanal y near-duplicate global pendientes |
| Papers propios | 9 Markdown (README excluido) | 750.857 bytes; hashes/bytes verificados; dedup exacta contra 9.108 documentos train existentes; auditoría de estructura y privacidad PASS | Sí, train scoped interno; near-duplicate global y holdout siguen pendientes |
| NASA file-reviewed | 6 train + 4 retenidos (subconjunto de NASA NTRS) | 701.870 bytes train; 4 nuevos promovidos tras verificar Git blob SHA-1, candidate pack y bytes; 4 OCR/rights holds | Sí, train scoped de los 6 archivos aprobados; near-duplicate global pendiente |
| ScienceVerse | 7.403 registros fuente; 7.365 admitidos scoped; 7.103 train; 262 retenidos | 426.975.945 bytes train; CC BY/CC0 por DOI; hashes y dedup exacta cruzada PASS | Sí, train scoped en 4 bibliotecas General; near-duplicate global y holdout pendientes |
| CoVoST 2 translation-only | 270.244 train; 34.051 validation y 33.678 test aislados | 18.385.485 bytes UTF-8 de texto train; 77.509.998 bytes JSONL; CC0-1.0; inglés y catalán | Sí, train scoped tras materialización verificable; solo traducciones; near-duplicate global y holdout pendientes |

**Cómo leer los totales:** los cuatro manifiestos base registran 10.163 entradas (literatura, Mathlib4, NASA y Papers), más 7.403 registros fuente de ScienceVerse. CoVoST es una fuente independiente: 350.705 filas originales, 337.973 traducciones únicas tras filtros y 270.244 documentos en train. La cifra **entrenable por partición** pasa a **286.468 documentos y 684.738.932 bytes UTF-8**: 608 literatura + 8.498 Mathlib4 + 6 NASA file-reviewed + 9 Papers propios + 7.103 ScienceVerse + 270.244 CoVoST. Validation/test permanecen aislados. No es una afirmación de G-0 global ni de ausencia de near-duplicates; el estado train scoped se limita a cada manifiesto y sus controles.

### ScienceVerse: 7.103 documentos train scoped; 262 retenidos

La auditoría por documento registra 13 colecciones y 7.365 documentos admitidos scoped. De ellos, 7.103 documentos (426.975.945 bytes UTF-8) pasan integridad de payload, SHA-256/bytes, CC BY/CC0 por DOI, atribución, mínimos de calidad, filtros de email/SSN y deduplicación exacta interna y contra el train actual. Se retienen 262 por exceso de caracteres de reemplazo; no se retuvieron títulos no sustantivos en el artefacto verificado. La promoción es train scoped; near-duplicates globales, contaminación de benchmarks/holdouts y G-0 siguen pendientes.

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

Fuente de la admisión scoped: `admitted/scienceverse-ccby-v1/manifest.json`. La partición train verificada y sus hashes están en `admitted/scienceverse-ccby-v1/train-eligibility-manifest.json`; auditoría: [run 42110130695](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42110130695).

### CoVoST 2 translation-only: 270.244 documentos train scoped

- Upstream inmutable: `facebookresearch/covost` en `4cddf32dedd6bfef86ca3a40f49b27e252650f3f`; tres archivos TSV con SHA-256 fijado.
- Derechos: CC0-1.0 para los datos CoVoST. Se excluyen Tatoeba, audio, frases fuente de Common Voice, IDs de hablante/cliente, rutas y código del repositorio.
- Exportación solo del campo de traducción: 350.705 filas originales; 337.973 únicas tras filtros; 12.732 descartadas (12.684 demasiado cortas, 43 duplicados exactos, 1 contacto/email y 4 URLs).
- Train: **270.244 documentos / 18.385.485 bytes UTF-8 de texto** (77.509.998 bytes JSONL; gzip persistido tras el workflow). Inglés: 88.916; catalán: 181.328. Pares: es→en 48.998, ca→en 39.918, en→ca 181.328.
- Validation: 34.051; test: 33.678. Ambos permanecen fuera de entrenamiento.
- Revisión humana estratificada: 36/36 muestras (12 por par); texto interpretable y coherente con el idioma; se registró ruido de traducción en tres ejemplos. Los tres falsos positivos del detector de teléfono son rangos de años, no teléfonos.
- Deduplicación exacta: 0 duplicados internos y 0 frente a ScienceVerse, Mathlib4, NASA file-reviewed y Papers; 0 coincidencias de línea frente a las 449.939 líneas del train literario español. El chequeo de ScienceVerse y su manifiesto train se han reconciliado: ambos registran 7.103 documentos y los mismos hashes de payload.
- **Límites explícitos:** train scoped interno; G-0 global sigue FAIL; near-duplicates globales y contaminación de benchmarks/holdouts siguen PENDING. No presentar el corpus como gold-standard de traducción.

Manifiesto de materialización: [CoVoST 2 train scoped](admitted/covost2-cc0-translation-only/manifest.json). Revisión: [muestra manual y deduplicación](reviews/covost2-manual-review-2026-11-05.json).

## Bibliotecas objetivo: 32 dominios × General/HKD

El objetivo canónico es **64 bibliotecas**. General y HKD deben ser disjuntas globalmente, sin duplicados exactos ni near-duplicates compartidos. HKD se selecciona por densidad semántica RONIN, con desempate estable por identificador documental, y el reparto se equilibra por bytes UTF-8.

- Mínimo Level A: **1 MiB de texto admitido por biblioteca** (64 MiB en total).
- Objetivo de escala: 10 GiB por biblioteca (640 GiB en total).
- Estado del inventario Level A scoped: **7.249 documentos / 539.887.336 bytes**; **5/64** bibliotecas alcanzan el mínimo de 1 MiB, 59 están por debajo. Cuatro bibliotecas nuevas proceden de ScienceVerse: `social_sciences_general`, `biology_general`, `medicine_health_general` y `philosophy_general`.
- Bibliotecas globalmente training-eligible en el manifiesto de 64: **0/64** por G-0; bibliotecas con train scoped habilitado: **4/64** (ScienceVerse).
- validación global validación global: **FAIL**.

El manifiesto `libraries/manifest-64.json` cuenta el corpus legacy y ScienceVerse en sus cuatro bibliotecas General. NASA y Papers conservan admisión train scoped en manifiestos propios, pero no se suman a los contadores Level A de esas bibliotecas.

## Qué significa cada estado

| Estado | Significado | ¿Puede entrenar? |
|---|---|---|
| Admitido scoped | Documento aceptado dentro del alcance de su manifiesto de fuente, con procedencia y decisión registradas | Solo si el manifiesto de ese corpus y las validaciones aplicables autorizan la partición train |
| Level A en biblioteca | Payload incorporado al inventario de bibliotecas y contado tras superar el estándar Level A | Sujeto también a validación global |
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
- **Train scoped habilitado** tras verificar los nueve SHA-256 y tamaños, estructura sustantiva, ausencia de patrones de email y deduplicación exacta contra 608 literatura + 8.498 Mathlib4 + 2 NASA file-reviewed. Auditoría: [run 42106428381](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42106428381).
- La promoción no equivale a G-0 global: near-duplicates, contaminación de holdouts y General/HKD global siguen pendientes. Uso autorizado solo para entrenamiento/investigación interna; no redistribuir externamente.

### Lean mathlib4 — `admitted/mathlib4-v1/`

- 8.697 archivos Lean 4 admitidos desde `leanprover-community/mathlib4`, revisión inmutable `a84939a26903163e1b98ee002bc94e9563e75c12`.
- Licencia de repositorio Apache-2.0; SHA-256 por archivo y de LICENSE, autoría/cabeceras conservadas. 8.555 archivos contienen cabecera explícita Apache 2.0; los restantes quedan cubiertos por la licencia de repositorio fijada.
- 8.498 train (97.629.252 bytes), 91 validation (925.844 bytes) y 108 test (1.177.979 bytes). Dos módulos de reenvío menores de 100 caracteres quedaron retenidos.
- Dominios: 8.650 matemáticas y 47 lógica/epistemología. Cero duplicados exactos internos o contra los payloads admitidos existentes revisados; cero hallazgos de claves/tokens de alta confianza.
- Train es entrenable solo bajo este manifiesto scoped. Near-duplicate global, revisión humana línea por línea y validación global global no se declaran superados.
- Artefacto de admisión: [run 42026633643](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42026633643); payload `ronin-admitted-mathlib4-v1`.

### NASA file-reviewed — `admitted/nasa-ntrs-file-reviewed-v1/`

- Seis documentos revisados individualmente; **dos** (32.409 bytes) ya estaban en train y **cuatro adicionales** (669.461 bytes) se promovieron tras verificar Git blob SHA-1, payload del candidate pack, derechos public-use, privacidad y deduplicación exacta cruzada. Total NASA file-reviewed train: **6 documentos / 701.870 bytes**.
- **Cuatro retenidos**: las atestaciones de revisión no coinciden con el payload exacto; no se han corregido hashes a ciegas ni se han admitido.
- Los seis NASA file-reviewed son un subconjunto revisado de los 813 NASA NTRS, no una nueva adquisición. No sumarlos de nuevo al total documental ni al mínimo Level A.
- Ejecución de promoción y recheck NASA: [run 42028138060](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42028138060). Validador del manifiesto actualizado: [run 42028588708](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42028588708).

## Candidatos y líneas de adquisición

Los números siguientes son **inventarios de candidatos**, no admisiones. Hay snapshots y exportaciones que pueden solaparse; no se suman entre sí sin deduplicación por hash/DOI.

### Payloads adquiridos y pendientes de revisión

| Línea | Adquisición comprobada | Estado y límites |
|---|---:|---|
| ScienceVerse / papers (RDS) | 3.087 DOI elegibles en cinco assets RDS; 95.948.088 bytes comprimidos | Exportación textual, derechos por artículo/versión, terceros, privacidad y calidad pendientes. No son bytes de texto admitido. |
| ScienceVerse (exportaciones de texto) | 7.403 documentos en 13 colecciones; 7.365 admitidos scoped; 7.103 train y 262 retenidos | Train scoped verificado: 426.975.945 bytes UTF-8; no sumar 3.087 + 7.403 con el lote RDS. Near-duplicate global y holdout pendientes. |
| NASA NTRS | 824 textos completos; 39.262.382 bytes | 813 admitidos scoped en su manifiesto, 11 retenidos; además, seis revisados en un manifiesto separado. Los paquetes por biblioteca son candidatos y no deben sumarse de nuevo. |
| NASA NTRS — snapshot de expansión | 189 textos completos; 15.417.212 bytes | Lote candidato adicional registrado en el README de adquisición; reconciliar IDs/hashes contra los 824 antes de contarlo como incremento neto. |
| CoVoST 2 | 350.705 filas originales; 337.973 únicas; 270.244 train, 34.051 validation y 33.678 test | **Admitido train scoped**: 18.385.485 bytes UTF-8 de texto; CC0-1.0; solo traducciones; audio, fuentes, IDs, rutas y Tatoeba excluidos. Near-duplicate global y holdout pendientes. |
| PleIAs Common Corpus | 2.159 filas, 5.971.320 bytes | 2.149 CC0, 4 CC BY 3.0 y 6 CC BY 4.0; 17.472 filas con licencias no permitidas, 311 con patrones básicos de email/teléfono y 8 inválidas/sobredimensionadas excluidas. Revisión humana, privacidad, calidad y splits pendientes. |
| GPLSI ClearText CAS/VAL | 17 documentos candidatos (11 CAS y 6 VAL) | Derechos de los documentos originales pendientes; un documento NC-ND en cuarentena. |
| UN Parallel Corpus | Workflow de ingestión en-es y validador incorporados | No atribuir un recuento de textos hasta que exista un run/artefacto verificado. La fuente declara dominio público para UN Parallel Corpus v1.0; siguen pendientes hashes, calidad, privacidad, deduplicación y particiones. |

**No existe un total global fiable de candidatos únicos.** El ledger de ingestión registra runs, artefactos y hashes por fuente; el número de filas de un snapshot no debe sumarse con otra exportación de la misma familia sin reconciliación.

### Fuentes adicionales de alta prioridad

La auditoría de huecos del 5 de noviembre está documentada en [`acquisition/source-gap-review-2026-11-05.md`](acquisition/source-gap-review-2026-11-05.md). Ordena las fuentes sin representación en el train actual por volumen potencial, evidencia de derechos y trabajo pendiente. No convierte ningún candidato en entrenable.

- **NIST Technical Series / Public Data Repository:** línea favorable para informes y datos creados por NIST cuando el registro identifica autoría/titularidad NIST y se conserva la atribución. NIST advierte de material de terceros; no se admite el catálogo completo. Preflight por registro y payload pendiente.
- **USGS Publications Warehouse:** fuente de alto valor para geología, geografía, agua, riesgos naturales y ciencias de la Tierra. USGS confirma que sus informes publicados son generalmente de dominio público, pero advierte que algunas imágenes, ilustraciones y fotografías son de terceros. Seleccionar solo publicaciones USGS propias y excluir material mixto no aclarado.
- **NOAA Institutional Repository:** repositorio científico con texto completo; su política distingue obras gubernamentales CC0 de artículos y proceedings cuyos titulares conservan derechos. No usar el repositorio entero como corpus libre: selección por documento y revisión de copyright obligatorias.
- **BNE/BDH — Documentos en dominio público:** fuente oficial con distribuciones TXT, XML y metadatos; la ficha describe las obras incluidas como dominio público y declara reutilización CC BY 4.0. La distribución del catálogo se actualizó por última vez el 2024-12-04. **Estado en `main`: metadata/candidate, 0 entrenables; no existe todavía el workflow `ingest-bne-bdh-public-domain.yml`** (la mención anterior a ese workflow era prematura). La adquisición debe descargar el ZIP, fijar SHA-256, resolver cada enlace registro-texto, comprobar OCR/terceros y deduplicar antes de generar splits. No confundir la licencia de los registros con la de obras fuera del conjunto explícito de dominio público.
- **Project Gutenberg:** fuente de descubrimiento; verificar estado de dominio público aplicable en España/UE y derechos de traducción/edición concretos.
- **ParlaIbero-ES, DReaM-es-open, VoxPopuli y otras colecciones lingüísticas:** mantener en preflight hasta resolver licencia de cada documento/segmento, derechos de voz, privacidad y condiciones de redistribución.



## Objetivo operativo inmediato: ampliar el corpus realmente entrenable

No se considerará progreso el crecimiento de `candidates/`, el número de filas con licencia aparente ni los pases de filtros automáticos. El contador que importa es el de documentos con `training_eligible=true` en una partición `train` reproducible y con hashes comprobados.

- **Corpus con partición train actualmente habilitada:** literatura (608 / 140.295.523 bytes), Mathlib4 (8.498 / 97.629.252 bytes), NASA file-reviewed (6 / 701.870 bytes), Papers propios (9 / 750.857 bytes), ScienceVerse (7.103 / 426.975.945 bytes) y CoVoST 2 (270.244 / 18.385.485 bytes): **286.468 documentos y 684.738.932 bytes UTF-8**. Validation/test permanecen excluidos.
- **NASA NTRS restante (807 scoped) y NASA file-reviewed retenidos por OCR/derechos (4):** siguen excluidos de entrenamiento hasta superar sus comprobaciones específicas. ScienceVerse (7.103 train scoped de 7.365 admitidos) y Papers propios (9) ya están habilitados en train.
- **Siguiente fuente prioritaria:** conjunto oficial BNE *Biblioteca Digital. Documentos en dominio público*, que ofrece distribución TXT/XML de obras declaradas en dominio público y reutilización CC BY 4.0. Se debe adquirir el snapshot, fijar hashes, comprobar cada obra/edición y OCR, retirar aparato editorial/terceros dudosos, deduplicar globalmente y generar splits antes de promover. No se contará ni entrenará hasta superar esos controles.
- La política de adquisición queda así: primero fuentes con texto completo y permiso explícito sobre la obra, luego calidad verificable, y solo entonces admisión y entrenamiento. Los candidatos que no puedan cerrar los validaciones no desplazan este objetivo.

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
10. Validación de manifiestos, separación General/HKD y validación global del inventario.

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
- [Auditoría de fuentes sin representación entrenable — 2026-11-05](acquisition/source-gap-review-2026-11-05.md)
- [Manifiesto CoVoST 2 train scoped](admitted/covost2-cc0-translation-only/manifest.json)
- [Revisión manual CoVoST 2](reviews/covost2-manual-review-2026-11-05.json)

- [Inventario 32 dominios / 64 bibliotecas](libraries/manifest-64.json)
- [Auditoría de documentos candidatos — 2026-11-05](reviews/candidate-document-audit-2026-11-05.json)
- [Attestation de revisión del propietario](reviews/human-review-attestation-2026-11-05.json)
- [Revisión documental NASA](reviews/nasa-ntrs-file-review-2026-11-05.json)
- [Manifiesto literatura española](admitted/literature-es-v1/manifest.json)
- [Manifiesto NASA public-use](admitted/nasa-ntrs-public-use-v1/manifest.json)
- [Manifiesto Papers propios](admitted/ronin-authored-papers-v1/manifest.json)
- [Manifiesto train scoped ScienceVerse](admitted/scienceverse-ccby-v1/train-eligibility-manifest.json)

## Decisión operativa — estándar Level A estricto

El inventario de 64 bibliotecas aplica ahora el estándar explícito por ítem y versión: licencia canónica compatible o dominio público demostrado para la obra/edición; cobertura ES/EU/US; titular/proveedor y alcance; atribución; procedencia; snapshot de metadatos con SHA-256; hash del payload; revisión de terceros; calidad, privacidad, deduplicación exacta y near-duplicate global; separación General/HKD y splits verificables.

**Contabilidad estricta actual: 0 documentos / 0 bytes Level A admitidos en las 64 bibliotecas; 0/64 alcanzan 1 MiB; 0/64 están completas; 0/64 son training-eligible. G-0 global continúa FAIL.**

Los corpus scoped anteriores se conservan sin borrar datos ni cambiar sus artefactos, pero ya no se computan como Level A estricto:

- Literatura española: 608 documentos train / 140.295.523 bytes UTF-8.
- ScienceVerse: 7.103 documentos train / 426.975.945 bytes UTF-8; 262 retenidos en el filtro final. El manifiesto de fuente y el inventario fueron reconciliados contra el artefacto del run 42110130695. Sus asignaciones General son 2.741 Social Sciences, 2.377 Biology, 1.694 Medicine/Health y 291 Philosophy.
- Total scoped conservado: **7.711 documentos / 567.271.468 bytes**, reportados fuera de los contadores Level A.

CoVoST 2 sí dispone de evidencia de derechos Level A CC0-1.0 para el payload de traducciones: 270.244 segmentos / 18.385.485 bytes UTF-8. Aún no se asigna a ninguna biblioteca porque near-duplicate global y contaminación de benchmark/holdout siguen pendientes. No se confunde su elegibilidad scoped de origen con admisión global o de biblioteca.

El registro de derechos tiene 11 entradas: 9 A (seis exportaciones solo de metadatos y tres payloads/versiones CoVoST) y 2 B (BOE). Las entradas de metadatos no cuentan como texto. Los candidatos PMC y USGS tampoco cuentan como Level A admitido. BNE sigue bloqueada por HTTP 403.

El estado detallado, hashes, artefactos y bloqueos está en [el inventario 64](libraries/README.md), [el registro de derechos](rights_registry/README.md) y [docs/RUNS.md](../../docs/RUNS.md).
