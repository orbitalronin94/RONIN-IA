# Inventario canónico de las 64 bibliotecas

El objetivo de RONIN es **32 dominios × General/HKD = 64 bibliotecas**. El inventario canónico está en manifest-64.json y se valida con scripts/validate_64_library_inventory.py. El manifiesto manifest-32.json y sus 32 directorios describen el pipeline parcial legado RUN5 de 16 dominios; no son el objetivo final.

## Estado verificable a 5 de noviembre de 2026

- Dominios catalogados: **32**.
- Slots General/HKD: **64**.
- Documentos Level A admitidos en las 64 bibliotecas: **608**.
- Bytes de texto Level A admitidos: **140.295.523**.
- Bibliotecas que alcanzan el mínimo de 1 MiB Level A: **1/64** (Humanidades — General).
- Bibliotecas training-eligible: **0/64**.
- G-0 global: **FAIL**.

El catálogo no es una descarga y una descarga no es una admisión. Los contadores de manifest-64.json se mantienen a cero hasta que existan payloads de texto exactos, derechos por ítem/versión, calidad, privacidad, deduplicación, atribución, splits y hashes aprobados.

## Umbrales y reparto

- Mínimo operativo: **1 MiB de texto Level A por biblioteca**.
- Objetivo posterior: **10 GiB por biblioteca** cuando las fuentes y capacidad lo permitan.
- Mínimo total de 64 bibliotecas: **64 MiB**; objetivo de escala total: **640 GiB**.
- General/HKD: particiones disjuntas por documento y clúster near-duplicate.
- HKD: ranking RONIN por densidad semántica, descendente, con desempate estable por identificador documental.
- Balance: bytes UTF-8, no solo número de documentos.
- Deduplicación exacta y near-duplicate global entre las 64 bibliotecas, corpus admitidos y conjuntos de evaluación.
- Train/validation/test se separan de forma determinista y agrupada por documento/DOI; validation/test/holdout nunca pasan a train.

## Pool legacy que no se cuenta como Level A

El corpus admitted/literature-es-v1 conserva 608 documentos train y 140.295.523 bytes, con SHA-256 9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78. Sus 18 validation y 18 test permanecen aislados. Aporta **608 documentos train y 140.295.523 bytes** a `humanities_general` como Level A scoped-equivalent, con SHA-256 9cd5d7e83ed7690713add22c40fdf35eaf1fb88da3dafb748ca8201b08df9a78. Se aplica el estándar legacy: fuentes públicas fijadas, derechos/procedencia por documento, hashes, particiones disjuntas, cero duplicados exactos en train y auditorías previas registradas. No se exige nueva reconciliación territorial general.

La reconstrucción de esos 608 fragmentos se valida por character_count y SHA-256 individual en scripts/assemble_32_libraries.py. Los fragmentos se conservan exactamente; los conserva como material Level A scoped-equivalent. `humanities_hkd` queda pendiente de ranking semántico; no se inventa una división HKD.

## Candidatos de volumen relevantes

- ScienceVerse: cuatro RDS con 2.595 filas DOI elegibles y 83.524.872 bytes comprimidos. No son bytes de texto. Falta inspección RDS, extracción textual, verificación de derechos del editor, privacidad, retractaciones, deduplicación y splits. Expediente: ../candidates/scienceverse-expanded-corpora/README.md.
- Naciones Unidas Parallel Corpus: fuente con declaración de dominio público del proveedor; falta descarga, validación de payload/alineaciones, privacidad y revisión por documento. Expediente: ../candidates/un-parallel-corpus-v1/README.md.
- PMC OA: candidatos de texto completo condicionados a licencia por versión y a la consolidación/hash de shards. Nunca se promueven automáticamente.
- arXiv: metadatos CC0 no equivalen a licencia del artículo; el texto completo requiere licencia por versión CC BY 4.0/CC0 y comprobación de terceros.
- NASA NTRS / NIST: solo documentos o datos propios con declaración de reutilización inequívoca; excluir trabajos de terceros.
- BNE / Project Gutenberg: metadatos no transfieren derechos al OCR; dominio público estadounidense no prueba dominio público en España/UE.

## Derechos Level A

rights_registry/records.jsonl contiene 10 registros (8 A, 2 B). Los registros Level A incluyen seis exportaciones de metadatos y dos payloads candidatos CoVoST; ninguno se ha admitido como texto en las 64 bibliotecas. Los dos registros BOE están en Level B y no cuentan para el mínimo Level A. La evidencia de un proveedor, SPDX, Crossref, AWS Open Data Registry o una etiqueta genérica no sustituye la comprobación de derechos exactos y terceros.

## G-0 y entrenamiento

G-0 permanece independiente. Mientras sea FAIL, ninguna biblioteca puede ser training-eligible aunque supere el mínimo Level A. No se entrenará con candidatos, con datos de permisos privados, con chain-of-thought privado de tutores ni con validation/test/holdout.

Ejecutar:
- python scripts/validate_64_library_inventory.py
- pytest -q tests/test_64_library_inventory.py

El workflow .github/workflows/validate-64-library-inventory.yml publica los recuentos estructurales. Un PASS del inventario solo demuestra que los 32 pares General/HKD están bien catalogados y que no se ha habilitado entrenamiento; no demuestra que las bibliotecas estén completas.


## Estándar Level A actualizado — equivalencia legacy

Level A ya no exige una nueva auditoría territorial general ES/EU/US cuando el corpus cumple el estándar scoped de `literature-es-v1`: acceso anónimo público; revisión de fuente inmutable; derechos y procedencia por documento; hashes de payload/texto; train/validation/test deterministas y disjuntos; cero duplicados exactos en train; auditoría humana y de calidad registrada; y escaneo previo de PII/secretos. Se mantienen exclusiones de terceros, privacidad, atribución, integridad y calidad. Los registros de catálogo o licencias de metadatos no bastan para admitir texto.

El inventario registra 608 documentos y 140.295.523 bytes en `humanities_general` (1/64 bibliotecas sobre el mínimo). `humanities_hkd` queda pendiente de ranking. G-0 global sigue FAIL.
