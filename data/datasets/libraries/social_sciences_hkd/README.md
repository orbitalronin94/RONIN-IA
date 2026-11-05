# Ciencias sociales — HKD — alta densidad de conocimiento

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- ScienceVerse Collabra: 748 licencias CC BY 4.0 por DOI, 747 cuerpos extraídos; 70 con correos/contacto retirados, 677 candidatos restantes (541 train)

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


## Candidatos científicos ScienceVerse

- Frontiers in Psychology (1.000), i-Perception (496), Judgment and Decision Making (855) y Journal of Cognition (447): candidatos ScienceVerse declarados CC BY 4.0 en el catálogo upstream; falta auditoría DOI/artículo y extracción.
- El catálogo declara 15.179 artículos en 18 corpus y conserva manifiestos por DOI y procedencia. Estos documentos aún no están admitidos ni son entrenables.
- Expediente: `data/datasets/candidates/scienceverse-expanded-corpora/README.md`.
