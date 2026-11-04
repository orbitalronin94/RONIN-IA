# Almacén de datasets RONIN

Este directorio es el catálogo versionado y el punto lógico de entrada para los corpus de entrenamiento. Los corpus grandes de RUN 5 se conservan como artefactos independientes de GitHub Actions; no se versionan como blobs Git ni dependen de que un gate de entrenamiento pase.

## RUN 5

Cada ejecución del workflow **Preparar las 16 bibliotecas RUN 5** publica:

- Un artefacto por biblioteca, con nombre `ronin-datasets-run5-library-<id>`.
- Un índice/diagnóstico por dominio, incluso si el job falla parcialmente.
- Un artefacto `ronin-datasets-run5-master-index` con `datasets/run5/INDEX.json`.

El índice maestro enumera siempre las 16 bibliotecas previstas. Para cada una registra estado, tamaño train, SHA-256, revisión de origen, manifiesto y nombre del artefacto. Si una biblioteca no llegó a generarse, aparece con estado `missing_or_generation_failed`; no se omite.

Los artefactos de datos se suben con condición `always()`: una validación fallida, una deduplicación que detecte colisiones o el bloqueo de admisión no elimina el material candidato generado. El workflow oficial de entrenamiento es independiente y solo puede consumir bibliotecas después de superar sus gates.

## Retención y reproducibilidad

Los artefactos de Actions tienen retención limitada (configurada actualmente a 90 días). Para conservación a largo plazo, descarga los artefactos y archívalos en almacenamiento persistente externo con verificación SHA-256. El índice registra el run ID y commit para reconstruir la procedencia. No se debe interpretar un artefacto candidato como material legalmente admitido o elegible para entrenamiento.

## Pesos y parámetros

Los pesos de mezcla por biblioteca son metadatos de muestreo y controlan la proporción de ejemplos vistos durante el entrenamiento; no aumentan por sí mismos el número de parámetros entrenables. Cualquier crecimiento de parámetros debe reflejarse en el manifiesto de arquitectura y en un recuento explícito antes/después.
