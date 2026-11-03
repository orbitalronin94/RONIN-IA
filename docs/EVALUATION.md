# Evaluación

La evaluación debe ser reproducible y estar vinculada a versiones exactas del modelo, tokenizador, corpus y configuración.

## Mediciones obligatorias

- Entropía cruzada y perplejidad sobre datos de validación.
- Bits por byte (BPB) para comparaciones entre tokenizadores o esquemas de tokenización.
- Tokens procesados, ejemplos de validación e incertidumbre/variabilidad cuando tenga sentido.
- Pruebas de generación: forma de la salida, comportamiento de EOS/parada, muestreo determinista y límites de contexto.
- Pruebas de regresión para prompts conocidos y detección de filtraciones de datos.
- Referencias entrenadas bajo condiciones documentadas.

La perplejidad depende del tokenizador y del corpus. No se deben comparar valores brutos de perplejidad entre tokenizadores distintos como si fueran equivalentes; se debe informar BPB u otra métrica normalizada justificada. Una prueba con datos sintéticos o el sobreajuste de un único lote solo valida la mecánica; no demuestra competencia lingüística ni generalización.

## Criterios de aceptación

Una ejecución de entrenamiento solo es válida si:

1. Los manifiestos y licencias de los conjuntos de datos están completos.
2. La separación entre entrenamiento, validación y prueba está verificada.
3. Los vocabularios del modelo y del tokenizador coinciden.
4. Las pérdidas y los gradientes permanecen finitos.
5. Guardar y volver a cargar un checkpoint reproduce las salidas dentro de una tolerancia numérica documentada.
6. La evaluación se realiza sobre datos no vistos y sus resultados se guardan con los metadatos de la ejecución.

No se inventarán puntuaciones de benchmarks, afirmaciones de calidad ni indicadores de preparación.
