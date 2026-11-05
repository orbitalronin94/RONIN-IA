# Derecho — HKD — alta densidad de conocimiento

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- GPLSI CAS/VAL: 17 textos candidatos; 2 textos BOE con base Art. 13 en nivel B (firma jurídica y limpieza pendientes); el resto requiere derechos de origen
- ParlaIbero-ES: solo preflight de metadatos

El ensamblador asigna únicamente documentos con señal temática suficiente. Los textos sin asignación clara permanecen en el pool transversal; no se fuerzan a este dominio.

## Reparto

- **General:** material temáticamente pertinente que no queda en el tramo HKD.
- **HKD:** tramo de mayor densidad semántica, seleccionado con la puntuación RONIN-HKD.
- Reparto objetivo: 50 % del peso en bytes para cada lado, sin duplicar documentos.
- Las particiones train/validation/test se generan por identificador estable.

## Comprobaciones pendientes

- Revisar derechos y atribución del documento/versión exactos.
- Revisar calidad, idioma, privacidad y contenido sensible.
- Comprobar duplicados exactos y aproximados frente a las otras 31 bibliotecas.
- Revisar muestras humanas y la separación de particiones.
- Superar el gate global G-0.

**Estado de entrenamiento: bloqueado.** La presencia de un texto en un artefacto candidato no lo convierte en material admitido. Los recuentos y hashes de cada ejecución se conservan en `library-pack-manifest.json`.


## Candidato transversal: Naciones Unidas v1.0

- Fuente oficial con alcance de derechos de la colección verificado: documentos de Naciones Unidas de 1990–2014, seis idiomas, incluido español.
- Se conserva en el pool transversal de candidatos; **no se asigna todavía a esta biblioteca** hasta clasificar cada documento por tema y densidad.
- Payload, hashes, controles de privacidad/calidad, deduplicación, particiones y revisión humana pendientes. No entrenable.
- Expediente: `data/datasets/candidates/un-parallel-corpus-v1/README.md`.
