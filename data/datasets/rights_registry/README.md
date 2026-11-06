# Registro de derechos — admisión de nivel A

Este registro es el libro de evidencias de derechos por elemento y versión. Está separado del descubrimiento de fuentes y de la ingestión de candidatos.

## Niveles de evidencia

- **Nivel A:** evidencia completa y coherente para el texto/archivo y versión exactos, alcance de derechos explícito, proveedor/titular identificado, jurisdicciones objetivo cubiertas y contenido de terceros despejado o excluido. Es un requisito de derechos, no una admisión automática del corpus.
- **Nivel B:** hay una base jurídica concreta y una fuente oficial identificada, pero falta una comprobación o firma exigida por la política. No admite el texto ni autoriza entrenamiento.
- **Niveles C/D:** evidencia incompleta, contradictoria o insuficiente; el material sigue retenido.

Una declaración de derechos del proveedor no demuestra por sí sola que el proveedor sea titular de todos los contenidos. Cuando haya obras incorporadas, adaptaciones, traducciones, citas o autoría de terceros sin aclarar, el registro no puede ser A.

## Política conservadora

Licencias admitidas para nivel A:

- CC0-1.0
- CC-BY-2.0, CC-BY-3.0, CC-BY-4.0
- MIT, Apache-2.0, BSD-2-Clause y BSD-3-Clause

NC, ND, ShareAlike, desconocido, mixto y etiquetas genéricas de «abierto» no pasan el nivel A.

El identificador `PUBLIC-DOMAIN-ES-ART13` registra una base de dominio público española vinculada al artículo 13 del Real Decreto Legislativo 1/1996. **No equivale a una licencia ni pasa automáticamente a nivel A**: la política exige firma jurídica humana para las determinaciones de dominio público. Los registros BOE incorporados el 5 de noviembre de 2026 permanecen en nivel B y solo cubren España.

El dominio público nunca se infiere por antigüedad, muerte del autor, etiqueta de repositorio ni declaración limitada a Estados Unidos. Requiere evidencia por obra/edición y análisis de jurisdicción.

## Evidencia y límites

- SPDX: identifica licencias canónicas; no prueba que el proveedor sea titular.
- Europeana: el campo `edm:rights` es evidencia declarada por el proveedor, no una garantía sobre contenido incorporado.
- PMC OA: la licencia por artículo/versión no despeja automáticamente figuras, tablas, suplementos o citas de terceros.
- Crossref: los metadatos de licencia depositados por la editorial corroboran el alcance, pero no sustituyen el resto de la revisión.
- AWS Open Data Registry: sirve para descubrir datasets; no certifica los derechos de sus datos.

## Etapas de admisión

1. `candidate`: fuente localizada o payload descargado; nunca entrena.
2. `rights_level_A`: evidencia exacta validada por el registro.
3. `quality_pass`: idioma, codificación, OCR, privacidad, contenido sensible y duplicados revisados.
4. `admitted`: particiones inmutables, atribución, hashes, separación train/validation/test y revisión documentada.

G-0 es independiente. Ningún registro local de nivel A puede anular un G-0 fallido ni saltarse los controles de calidad, privacidad, deduplicación o particiones.

## Archivos

- `schema.json`: campos requeridos.
- `policy.json`: jurisdicciones, licencias y criterios.
- `records.jsonl`: libro append-only, un objeto JSON por línea.
- `scripts/validate_rights_registry.py`: validador determinista.

## Estado del libro — 6 de noviembre de 2026

- **11 registros en total: 9 A y 2 B.**
- Los nueve A se dividen en **seis snapshots/exportaciones de metadatos CC0** (dos versiones de snapshot OpenAlex y una cada una de ROR, Crossref, DataCite y OpenCitations) y **tres payloads/versiones CoVoST 2 CC0**.
- Los seis registros de metadatos solo cubren sus archivos de metadatos; no conceden derechos sobre los textos de las obras descritas.
- Los tres registros CoVoST cubren únicamente los TSV/versiones y hashes exactos descritos en cada fila. La partición train materializada contiene 270.244 segmentos y 18.385.485 bytes UTF-8, pero sigue fuera de las 64 bibliotecas mientras near-duplicate global y benchmark/holdout sigan pendientes.
- Los dos registros BOE (BOE-A-1983-6317 y BOE-A-2015-11430) permanecen en B y solo cubren España. La fecha de recuperación se conserva con precisión de día (`2026-11-05`); no se inventa una hora.

La base `PUBLIC-DOMAIN-ES-ART13` no es una licencia. Una promoción a A exige evidencia de la obra/edición exacta, URI probatoria, firma jurídica humana aprobada y cobertura explícita ES/EU/US. Ningún registro de derechos anula calidad, privacidad, deduplicación, splits o G-0.
