# Física — HKD — alta densidad de conocimiento

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- Common Corpus Open Science y arXiv: candidatos

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


## Candidatos de documentación técnica pública

- NASA NTRS y NIST Technical Series: candidatos de alta prioridad para informes técnicos; requieren filtro por documento, autoría/titularidad, descarga y SHA-256.
- No se admite el catálogo completo. Payload, hashes, revisión de PII/calidad, deduplicación y particiones siguen pendientes.
- Expedientes: `data/datasets/candidates/nasa-ntrs-public-use/README.md` y `data/datasets/candidates/nist-technical-series/README.md`.
