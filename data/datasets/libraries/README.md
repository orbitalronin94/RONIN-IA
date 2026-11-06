# Inventario canónico de las 64 bibliotecas

El objetivo es **32 dominios × General/HKD = 64 bibliotecas**. La fuente de verdad es [manifest-64.json](manifest-64.json). El estándar vigente es **Level A estricto por ítem y versión**; los corpus admitidos bajo políticas scoped anteriores se conservan, pero no se cuentan como Level A ni cubren el mínimo.

## Estado verificado — 6 de noviembre de 2026

- Dominios catalogados: **32**; IDs General/HKD: **64**.
- Texto Level A estricto admitido en las 64 bibliotecas: **0 documentos / 0 bytes**.
- Bibliotecas que alcanzan 1 MiB Level A estricto: **0/64**; por debajo: **64/64**.
- Bibliotecas plenamente completas (derechos, calidad, privacidad, near-duplicate global, General/HKD, splits y manifiestos): **0/64**.
- Bibliotecas training-eligible: **0/64**.
- G-0 global: **FAIL**.

No se han rebajado gates para conservar los contadores anteriores. Los datos scoped existentes se muestran aparte y siguen disponibles para reconciliación, pero no cuentan hacia los 64 MiB mínimos.

## Material scoped conservado — no computa como Level A estricto

| Biblioteca General | Documentos/segmentos scoped | Bytes UTF-8 | Fuente y bloqueo principal |
|---|---:|---:|---|
| humanities_general | 608 | 140.295.523 | CLiGS Textbox, CONSSA y ELTeC-spa; falta evidencia estricta por obra/edición, snapshot de metadatos y cobertura ES/EU/US |
| philosophy_general | 291 | 22.265.918 | ScienceVerse/Open Mind; falta reconciliación estricta de titular, snapshot y jurisdicciones |
| biology_general | 2.377 | 157.788.625 | ScienceVerse; mismos bloqueos, más near-duplicate global y pareja HKD |
| medicine_health_general | 1.694 | 82.340.385 | ScienceVerse; mismos bloqueos, más near-duplicate global y pareja HKD |
| social_sciences_general | 2.741 | 164.581.017 | ScienceVerse; mismos bloqueos, más near-duplicate global y pareja HKD |
| **Total scoped** | **7.711** | **567.271.468** | **0 bytes computan como Level A estricto** |

La auditoría verificable de ScienceVerse (run [42110130695](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42110130695), artefacto 13453391506) contiene 7.103 documentos train y 426.975.945 bytes UTF-8. Se reconciliaron el manifiesto de fuente y el inventario: 2.741 Social Sciences, 2.377 Biology, 1.694 Medicine/Health y 291 Philosophy; 262 documentos quedaron retenidos por exceso de caracteres de reemplazo. El artefacto ZIP SHA-256 verificado es `a55eed4a9165579d578ba110150b95c7bec7c312e476c8c744da8266350cd57f`; `documents.train.jsonl` SHA-256 `bc09ca772a9fc3b5c3be0de10d1ee83beea1bf29f2b403d1e56b36049afc49dc`. La elegibilidad de origen no equivale a Level A estricto de biblioteca: faltan snapshot SHA-256 por ítem en el registro, evidencia explícita de titular/proveedor y ES/EU/US, near-duplicate global, contaminación de benchmark/holdout y separación General/HKD.

El corpus de literatura española mantiene 608 train y 140.295.523 bytes, con validation/test separados. Se conserva bajo su manifiesto scoped anterior; no se convierte automáticamente en dominio público territorial ni en Level A estricto. Debe reconciliarse cada obra/edición y su evidencia jurídica antes de computarlo.

## Rights Level A que todavía no está asignado a una biblioteca

CoVoST 2 tiene una declaración CC0-1.0 por versión y un registro de derechos Level A para el payload de traducciones. El train contiene **270.244 segmentos / 18.385.485 bytes UTF-8**; su train gzip SHA-256 es `771e6845e0097554398de8d3416e3effeb3c173cff341f037ac5437ea6344623`. El run [42119196514](https://github.com/orbitalronin94/RONIN-IA/actions/runs/42119196514) y el artefacto 13457877574 se verificaron por SHA-256 `9e17ae5e0cd5f8a1e316ef767b6b1af34d34ab51ed33b18a010ff64c127c1f96`. No se asigna todavía a General/HKD: near-duplicate global y contaminación de benchmark/holdout siguen **PENDING**. Cada fila es un segmento de traducción, no un documento largo.

El registro de derechos contiene **9 registros A (6 solo de metadatos y 3 payloads/versiones CoVoST) y 2 registros B**. Los metadatos CC0 no son texto entrenable. Los dos registros BOE no son Level A: la base española por sí sola no acredita ES/EU/US.

## Otros candidatos y bloqueos

- PMC OA: 5.006 candidatos y 34.682.285 bytes UTF-8 en el último resumen; no admitidos, sin asignación a bibliotecas y con gates globales pendientes.
- USGS batch 001: 40 extracciones / 4.182.611 bytes candidatos; 29 rechazados por calidad y 11 en revisión de derechos. Siete se seleccionaron para revisión inicial (159.663 bytes); **0 Level A admitidos**. BNE respondió HTTP 403 y queda bloqueada.
- NASA NTRS y los nueve Papers propios siguen en corpus scoped separado; no cuentan al mínimo Level A.
- El catálogo de 64 IDs no significa que existan 64 payloads.

## Umbrales y gates

- Mínimo operativo: **1 MiB de texto Level A estricto por biblioteca** (64 MiB total).
- Escala posterior: **10 GiB por biblioteca** (640 GiB total), solo cuando existan fuentes y capacidad verificables.
- General/HKD deben ser disjuntos por documento y clúster near-duplicate. HKD requiere ranking RONIN reproducible por densidad semántica, con desempate estable.
- Deduplicación exacta y near-duplicate global contra todos los corpus y conjuntos de evaluación.
- PII, secretos, malware, idioma/calidad, atribución, splits y hashes se verifican sobre el payload exacto.
- Validation/test/holdout nunca pasan a train. MMLU-Pro test no se usa para entrenamiento ni selección.
- G-0 es independiente: mientras sea FAIL, las 64 bibliotecas permanecen `training_eligible=false`.

## Validación y trazabilidad

Ejecutar:

- `python scripts/validate_64_library_inventory.py`
- `python scripts/validate_rights_registry.py`
- `python -m pytest -q tests/test_64_library_inventory.py tests/test_rights_registry.py`

El libro de ejecuciones está en [docs/RUNS.md](../../docs/RUNS.md). Un workflow verde valida estructura y consistencia; no sustituye la evidencia jurídica ni declara completas las bibliotecas.
