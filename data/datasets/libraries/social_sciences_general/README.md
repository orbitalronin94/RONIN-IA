# Ciencias sociales — General

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- ScienceVerse Collabra: 748 licencias por DOI, 747 textos extraíbles; privacidad/calidad pendientes

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
