# Inventario de las 32 bibliotecas

El inventario operativo se compone de 16 dominios y dos bibliotecas por dominio: `General` y `HKD` (alta densidad de conocimiento). Cada directorio contiene su estado, fuentes localizadas y controles pendientes. Todos parten como **implementados parcialmente**; el manifiesto del artefacto de ensamblado aporta los recuentos y hashes exactos de cada ejecución.

La selección HKD prioriza densidad semántica y la separación General/HKD es disjunta, equilibrada por peso textual. No se fuerza material sin señal temática a una biblioteca: permanece en el pool transversal.

El estado de cada biblioteca se actualiza en su README y en `manifest-32.json`. Ninguna biblioteca de este inventario queda habilitada para entrenamiento hasta superar G-0.


## Nuevos bloques de fuentes revisadas (2026-11-05)

- **Naciones Unidas v1.0:** alcance de derechos de la colección verificado por el proveedor; pool transversal pendiente de descarga, hashes, clasificación temática, privacidad y deduplicación. Expediente: `../candidates/un-parallel-corpus-v1/README.md`.
- **ScienceVerse / papers:** siete corpus científicos declarados CC BY 4.0 por el catálogo upstream, 5.091 artículos de catálogo en total; falta auditoría DOI/artículo y descarga de payload. Expediente: `../candidates/scienceverse-expanded-corpora/README.md`.

Estos bloques amplían las fuentes localizadas, no el contador de bibliotecas admitidas. Las 32 siguen en implementación parcial y G-0 continúa bloqueado hasta completar los controles y la distribución equilibrada.


- **NASA NTRS:** candidato técnico-científico con más de 200.000 documentos completos en catálogo; solo pasan registros con copyright público explícito y sin partes de terceros no autorizadas. Expediente: `../candidates/nasa-ntrs-public-use/README.md`.
- **NIST Technical Series/PDR:** candidato para informes y datos propios de NIST con política oficial de reutilización y atribución; se excluyen trabajos de terceros y se exige revisión por registro. Expediente: `../candidates/nist-technical-series/README.md`.

- **BNE / Biblioteca Digital Hispánica:** metadatos de catálogo CC BY 4.0; OCR condicionado a derechos por obra y edición. **Project Gutenberg:** revisión territorial e individual, sin admisión global. Expedientes en `../candidates/bne-bdh-ocr/README.md` y `../candidates/project-gutenberg/README.md`.
