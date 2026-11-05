# Filosofía — General

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- Literatura española admitida: corpus separado hasta reparto documental

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


## Candidatos científicos ScienceVerse

- Open Mind (293): corpus ScienceVerse declarado CC BY 4.0 en el catálogo upstream, con orientación a filosofía y ciencias cognitivas; falta auditoría DOI/artículo y extracción.
- El catálogo declara 15.179 artículos en 18 corpus y conserva manifiestos por DOI y procedencia. Estos documentos aún no están admitidos ni son entrenables.
- Expediente: `data/datasets/candidates/scienceverse-expanded-corpora/README.md`.

## Adquisición ScienceVerse

- Open Mind: **293 artículos esperados**, con licencia CC-BY 4.0 declarada por DOI en el manifiesto upstream.
- Destino provisional: Filosofía General; se revisará la señal temática de cada artículo antes de su asignación definitiva.
- Estado: adquisición automatizada añadida; no contabilizar hasta workflow correcto. Pendientes privacidad, retractaciones/correcciones, deduplicación y particionado.
