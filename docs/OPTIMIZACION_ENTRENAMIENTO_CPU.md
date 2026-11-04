# Optimización y observabilidad del entrenamiento CPU

## Alcance

Este cambio prepara el siguiente ciclo pequeño de RONIN. No promete una aceleración antes de medirla y no altera la arquitectura, el objetivo de pérdida, el corpus ni la semilla. El entrenamiento sigue siendo PyTorch CPU; no es NumPy puro.

## Cambios implementados

### Muestreador vectorizado

`NextTokenBatches` genera los índices de las ventanas con una única operación de indexación avanzada:

- Genera los mismos inicios aleatorios con el mismo `torch.Generator`.
- Reutiliza el vector de offsets de secuencia.
- Construye los tensores de entrada y objetivo sin recorrer cada inicio en Python ni ejecutar `torch.stack` por ventana.
- Una prueba compara batch por batch contra la implementación de referencia anterior.

La optimización reduce trabajo Python en el muestreador. Su impacto total depende de cuánto pese el muestreo frente al forward/backward del Transformer.

### Control de paralelismo CPU

`scripts/train_text.py` admite:

- `--num-threads`: hilos intra-op de PyTorch.
- `--interop-threads`: hilos inter-op de PyTorch.
- Variables OpenMP/MKL/OpenBLAS fijadas en el workflow para evitar sobreasignación accidental.

El experimento reducido usa 4 hilos intra-op, 1 inter-op y 1 hilo OpenBLAS como punto de partida. Es una configuración de prueba, no un óptimo universal. Los registros guardan el número de hilos efectivo de PyTorch.

### Métricas del bucle

Cuando se pasa `--metrics-out`, el entrenador escribe un JSON atómico con:

- pasos completados y objetivo de pasos;
- tiempo total dentro del bucle;
- latencia media, mediana y p95 por paso;
- mediana de estado estable, excluyendo los primeros diez pasos de calentamiento;
- tiempo acumulado de escritura de checkpoints;
- ejemplos y posiciones de token procesadas;
- ejemplos/s y tokens/s;
- batch, longitud de secuencia, acumulación de gradiente, dispositivo e hilos efectivos.

La latencia por paso incluye el muestreo, forward/backward, optimizador y, cuando corresponda, el checkpoint. El tiempo de checkpoint se informa aparte, pero no se resta de la latencia total.

### Caché de datasets

El workflow reducido conserva las descargas de Hugging Face con una clave que incluye el sistema operativo, la revisión inmutable de MMLU-Pro y los hashes de los scripts/manifiestos de preparación. No cachea checkpoints ni mezcla corpus con datos de evaluación.

## Diseño del workflow reducido

1. Recuperar el corpus Portfolio en revisión autorizada e inmutable.
2. Preparar la literatura abierta usando solo train.
3. Verificar revisiones, licencias, particiones y SHA-256.
4. Construir y hashear la mezcla de entrenamiento.
5. Guardar el estado inicial del modelo y evaluarlo en una muestra estratificada fija de MMLU-Pro.
6. Entrenar desde inicialización aleatoria con 1.000 pasos por defecto.
7. Guardar métricas de rendimiento y checkpoint hash.
8. Evaluar el mismo conjunto de preguntas después del entrenamiento.
9. Consolidar accuracy, delta, cobertura, resultados por dominio, procedencia y métricas de rendimiento.
10. Publicar informes y manifiestos; no publicar corpus ni pesos.

MMLU-Pro test no interviene en los gradientes. El evaluador de RONIN puntúa la probabilidad del siguiente byte A-J y no es el protocolo oficial CoT ni comparable con el leaderboard.

## Cómo interpretar la aceleración

La ejecución nueva registra throughput real, pero no permite atribuir automáticamente un speedup al cambio. Para cuantificarlo se necesita una referencia A/B con:

- mismo runner/hardware y configuración de hilos;
- mismo corpus y SHA-256 de la mezcla;
- mismo perfil, batch, longitud de secuencia y pasos;
- misma semilla;
- mismo intervalo de medición, incluyendo o excluyendo checkpoints de forma consistente.

Speedup de entrenamiento = mediana del tiempo por paso de la referencia / mediana del tiempo por paso optimizado.

Se debe informar también el throughput y la pérdida final. Una mejora de velocidad que cambie el orden de muestras, el presupuesto efectivo o la pérdida no es una comparación equivalente.

## Siguiente fase de perfilado

Si el sampler vectorizado no representa una parte significativa del tiempo, no se seguirá optimizando esa ruta por intuición. El siguiente paso será perfilar CPU por operador y comparar hilos 1/2/4 en el mismo runner. Solo después se estudiarán `torch.compile`, exportación ONNX o precisión reducida, cada uno con paridad numérica y evaluación A/B.

## Restricciones de publicación

Los artefactos de Actions contienen informes, métricas y manifiestos. Los corpus privados, datos de terceros no autorizados y checkpoints no se publican.
