# Medicina y salud — General

**Estado: IMPLEMENTADO PARCIALMENTE.**

Esta biblioteca forma parte del inventario operativo de **32 bibliotecas (16 dominios × General/HKD)**.

## Contenido localizado

- CoVoST 2: fragmentos con señal temática
- PMC OA: privacidad reforzada y licencia por versión pendientes

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

- BMC Medicine (1.000) y eLife (1.000): candidatos ScienceVerse declarados CC BY 4.0 en el catálogo upstream; falta auditoría DOI/artículo y extracción.
- El catálogo declara 15.179 artículos en 18 corpus y conserva manifiestos por DOI y procedencia. Estos documentos aún no están admitidos ni son entrenables.
- Expediente: `data/datasets/candidates/scienceverse-expanded-corpora/README.md`.

## Adquisición ScienceVerse

- BMC Medicine: **1.000 artículos esperados** en el manifiesto upstream, todos declarados CC-BY 4.0 en el catálogo.
- RONIN descarga el paperlist completo y conserva manifiesto DOI/licencia y SHA-256 en `data/datasets/candidates/scienceverse-fulltext/bmcmed/`.
- Estado: adquisición automatizada añadida; no contabilizar como admitido hasta que el workflow complete y se compruebe el payload. Pendientes privacidad clínica, retractaciones, deduplicación y particionado.
