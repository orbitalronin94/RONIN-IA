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


## Línea base reproducible para tiny

El evaluador `scripts/evaluate_text.py` mide un checkpoint sobre un archivo de validación separado del corpus de entrenamiento. No crea particiones automáticamente: el operador debe reservar documentos completos y comprobar que no hay solapamiento ni duplicados entre entrenamiento y validación.

Ejemplo, una vez entrenado el perfil tiny:

```bash
python scripts/evaluate_text.py \
  --checkpoint checkpoints/tiny/step-00000100.pt \
  --validation-text /ruta/validacion-reservada.txt \
  --profile tiny \
  --batches 128 \
  --batch-size 2 \
  --seed 2026 \
  --device cpu \
  --output reports/tiny-baseline.json
```

El informe JSON registra las huellas SHA-256 del checkpoint y del archivo de validación, paso de entrenamiento, perfil, tokenizador, semilla, dimensiones de evaluación, cantidad de tokens, parámetros, entropía cruzada, perplejidad y BPB. Como el tokenizador provisional es de bytes, cada token evaluado representa un byte y BPB se calcula como entropía cruzada en nats dividida por ln(2).

Para comparar dos ejecuciones, mantener idénticos el archivo reservado, su SHA-256, el perfil, el tokenizador, el número de lotes, el tamaño de lote, la longitud de secuencia, la semilla y el dispositivo/precisión. Una reducción de pérdida de entrenamiento no cuenta como mejora. No cambiar ni reutilizar el conjunto reservado para ajustar hiperparámetros.

**Estado:** el evaluador y el formato del informe están implementados; todavía no hay corpus autorizado reservado ni resultados reales versionados. Por tanto, no existe aún una línea base de calidad de RONIN ni una mejora demostrada. Los informes experimentales deben publicarse como artefactos o adjuntos de ejecución, no junto con corpus, datos privados ni checkpoints en Git.


## Rendimiento del pipeline y conservación de memoria

Las optimizaciones se aceptan por tiempo total de pared de cada fase y del pipeline, manteniendo iguales los hashes de datos, el número de ejemplos, la cobertura y el protocolo de evaluación. No se considera mejora una ejecución más rápida que omita comprobaciones.

- El entrenamiento permite configurar `--checkpoint-every`; el checkpoint final siempre se guarda. En el workflow oficial se usa un intervalo de 250 pasos, frente al intervalo de 50 del perfil tiny, para reducir escrituras de estados completos del optimizador. La reanudación desde el último checkpoint conserva el estado completo; el intervalo implica una ventana de recuperación mayor y debe reflejarse en las métricas.
- El entrenamiento publica `training-metrics.json` con duración total, throughput y segundos dedicados a checkpoints.
- El evaluador multidominio agrupa prompts por longitud y evalúa solo los logits de la última posición válida. El orden de los resultados se restaura al del dataset; la prueba de regresión compara puntuaciones individuales y agrupadas.
- MMLU-Pro ya usa lotes por presupuesto de tokens, padding a la derecha y logits de última posición. No se reduce el test ni se truncan preguntas para acelerar.
- Las bibliotecas marcadas como `candidate` o con `global_g0=FAIL` no se incorporan automáticamente. La admisión de una partición concreta no equivale a aprobar el corpus completo.

Toda comparación de velocidad debe registrar runner, CPU visible, versión de PyTorch, hilos intra/inter-op, duración de preparación, entrenamiento, checkpoint, evaluación y publicación de artefactos. El tiempo total de GitHub Actions se compara con el mismo conjunto de jobs y dependencias.
