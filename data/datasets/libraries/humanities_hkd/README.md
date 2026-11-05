# Humanidades — HKD — alta densidad de conocimiento

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- Literatura española admitida: 608 documentos train-only, integrada en Humanidades y repartida entre General/HKD tras verificar cada hash
- CoVoST 2: fragmentos con señal temática
- Common Corpus Open Culture: candidato

El ensamblador asigna únicamente documentos con señal temática suficiente. Los textos sin asignación clara permanecen en el pool transversal; no se fuerzan a este dominio.

## Reparto

- General: material pertinente que no queda en el tramo HKD.
- HKD: tramo de mayor densidad semántica, seleccionado con la puntuación RONIN-HKD.
- Objetivo: 50 % del peso en bytes para cada lado, sin duplicar documentos.
- Train/validation/test se generan por identificador estable.

## Comprobaciones pendientes

- Derechos y atribución del documento/versión exactos.
- Calidad, idioma, privacidad y contenido sensible.
- Duplicados exactos y aproximados frente a las otras 31 bibliotecas.
- Revisión humana de muestras e integridad de particiones.
- Gate global G-0.

**Entrenamiento bloqueado.** La presencia de un texto en un artefacto candidato no lo convierte en material admitido. Los recuentos y hashes de cada ejecución se conservan en `library-pack-manifest.json`.


## Candidato transversal: Naciones Unidas v1.0

- Fuente oficial con alcance de derechos de la colección verificado: documentos de Naciones Unidas de 1990–2014, seis idiomas, incluido español.
- Se conserva en el pool transversal de candidatos; **no se asigna todavía a esta biblioteca** hasta clasificar cada documento por tema y densidad.
- Payload, hashes, controles de privacidad/calidad, deduplicación, particiones y revisión humana pendientes. No entrenable.
- Expediente: `data/datasets/candidates/un-parallel-corpus-v1/README.md`.


## Candidatos de patrimonio textual

- **Biblioteca Digital Hispánica (BNE):** catálogo CC BY 4.0 verificado; el OCR solo se incorpora cuando los derechos de la obra, traducción y edición concretas estén verificados. Expediente: `data/datasets/candidates/bne-bdh-ocr/README.md`.
- **Project Gutenberg:** fuente de descubrimiento con revisión individual por obra y jurisdicción; no se presume que el dominio público estadounidense aplique en España/UE. Expediente: `data/datasets/candidates/project-gutenberg/README.md`.
- Ninguna de estas dos fuentes añade todavía textos admitidos; el OCR/ebook pendiente de derechos queda fuera de entrenamiento.
