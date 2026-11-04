# Plan de aceleración de evaluación CPU de RONIN

## Diagnóstico verificado del código actual

El cuello de botella descrito es plausible, pero la implementación actual no es NumPy puro: `scripts/evaluate_mmlu_pro.py` usa **PyTorch CPU** (`torch.no_grad`, `RoninLM`, `F.log_softmax`). El bucle actual evalúa cada pregunta individualmente: crea un tensor de batch 1 y ejecuta `model(input_ids)` una vez por pregunta. Por tanto, la hipótesis prioritaria a medir es el coste de esos 12.032 forwards secuenciales, no la tokenización.

El evaluador ya implementa `select_stratified()`: baraja de forma determinista cada categoría y selecciona en rondas round-robin. Así que no debe sustituirse por un `--limit` que tome las primeras filas. La limitación actual es que la selección equilibrada por categoría no garantiza que la accuracy simple del subset estime sin sesgo la accuracy global si los tamaños de las categorías son diferentes.

## Objetivo: dos carriles separados

1. **Desarrollo rápido:** subset estratificado congelado y versionado, para comparar cambios de harness/inferencia. Nunca se presenta como el resultado oficial.
2. **Auditoría externa final:** mantener MMLU-Pro test completo, revisión inmutable y cobertura explícita. Ejecutar al cerrar una tanda de cambios, no en cada iteración. No usar sus resultados para escoger hiperparámetros.

La ejecución oficial actualmente en curso no se modifica ni se cancela.

## Orden propuesto por impacto, coste y riesgo

### P0 — Medir antes de optimizar

- Añadir profiling por fases: carga del dataset, construcción de prompts, forward, postproceso y escritura.
- Registrar número de forwards, tokens/bytes procesados, distribución de longitudes, tiempo total de forward, ejemplos/segundo y memoria pico.
- Capturar `torch.__config__.show()`, `torch.get_num_threads()`, `torch.get_num_interop_threads()` y variables OMP/MKL. En este repo `np.show_config()` no diagnostica el backend real del modelo.
- Benchmark reproducible en subset congelado; warm-up, al menos 3 repeticiones y mediana/p95. No inferir aceleraciones antes de medir.

### P1 — Subset estratificado congelado

- Crear un manifiesto con IDs, revisión del dataset, hash del dataset normalizado, algoritmo, semilla y asignación por categoría.
- Evaluar inicialmente 100 por categoría (aprox. 1.400 si hay 14 categorías) para iteraciones rápidas, siempre verificando el número real de categorías.
- Guardar `n_h` y `N_h` por categoría y reportar tanto macro-accuracy como estimación ponderada `sum_h (N_h/N) * accuracy_h`. No afirmar automáticamente ±2,6 pp: el intervalo depende del diseño, pesos, varianza por categoría y tamaño finito.
- El subset queda congelado; no regenerarlo al cambiar de checkpoint. No mezclar sus métricas con el resultado de test completo.

### P2 — Caché exacta de predicciones

- Caché opcional de scores/log-probabilidades por pregunta, no de una predicción sin procedencia.
- Clave mínima: SHA-256 del checkpoint, prompt serializado, revisión/hash del dataset, protocolo/formato de prompt, tokenizer y versión del evaluador.
- Cache hit solo si todas las partes coinciden. Invalidar al cambiar pesos, prompt o código que afecte la inferencia.
- Útil cuando cambia el reporter/harness sin cambiar el checkpoint; no acelera un entrenamiento nuevo ni una evaluación de pesos distintos.
- No guardar ni publicar el corpus completo dentro del artefacto de Actions.

### P3 — Batching en PyTorch

- El bucle actual usa batch=1. Prototipar batch 4/8/16 con agrupación por longitud (bucketing) para reducir padding.
- Antes de activar: confirmar que `RoninLM.forward` admite padding/attention mask correctamente. Si no, añadir máscara causal + padding con tests de equivalencia.
- Comparar batch=1 vs batch>1 sobre el mismo conjunto: logits/scores dentro de tolerancia, mismas predicciones, cobertura idéntica y mejora real de throughput.
- Medir `torch.set_num_threads` y evitar oversubscription en matriz de jobs.

### P4 — Paralelismo por categoría

- Solo después de medir batching: matrix de categorías, cada job procesa una partición disjunta del mismo manifiesto.
- Unir resultados por ID y validar que la unión sea exactamente el conjunto seleccionado, sin duplicados ni omisiones.
- No descargar/normalizar el dataset 14 veces: preparar una vez y compartir un artefacto inmutable o cache versionada por revisión + hash + manifiesto.
- No asumir cuotas fijas de concurrencia/minutos de Actions: dependen del plan, repositorio y límites vigentes. 14 jobs reducen wall-clock potencial, pero multiplican consumo y overhead.
- Timeout ajustado tras medir p95, no un valor arbitrario de 30 min por subject.

### P5 — Kernels y runtimes alternativos

- Numba: no es el primer paso porque la ruta activa es PyTorch, no kernels NumPy propios. Perfilador primero; compilar kernels aislados solo si se demuestra que dominan.
- ONNX Runtime CPU: experimento separado de exportación, validación numérica y throughput. No asumir 10–100×: medir este modelo, esta forma de entrada y este runner. Verificar soporte de operaciones, máscaras, dynamic axes y paridad.
- BF16/INT8: medir soporte real del CPU del runner y calidad frente a FP32. No introducir casts manuales en NumPy para un modelo PyTorch.
- Mantener un backend de referencia PyTorch FP32 para regresiones.

### P6 — Cachés de CI y entrenamiento

- `setup-python cache: pip` ya está configurado en el workflow oficial.
- Añadir caché de dataset/preprocesado solo tras definir clave inmutable que incluya revisión y hash; no cachear outputs no verificables.
- Pesos del modelo no se descargan de un registro externo en este flujo: el checkpoint se genera dentro del job. Una caché de pesos entre jobs no aplica al ciclo actual salvo que se rediseñe la arquitectura de jobs.
- Gradient accumulation y gradient checkpointing afectan entrenamiento, no el coste de forward del evaluador. No son prioridades para este cuello de botella.

## Métricas de aceptación

- Speedup medido = tiempo mediano baseline / tiempo mediano optimizado, con runner, checkpoint, subset y número de hilos constantes.
- Throughput: preguntas/s y bytes de prompt/s.
- Exactitud funcional: mismos IDs evaluados; misma cobertura; predicciones idénticas en FP32 batch; tolerancia explícita para backend alternativo.
- Informe de distribución de longitudes y tiempos por fase.
- Para cambios aproximados (BF16/INT8/ONNX), delta de accuracy, matriz de cambios de predicción y errores por categoría.
- Full test final sin caché obsoleta y con cobertura 100% de los 12.032 ítems seleccionados; no sustituirlo por subset.

## Secuencia de experimentos

1. Perfilado de la implementación actual y fijación del subset de desarrollo.
2. Caché exacta para separar coste de inferencia de coste de harness.
3. Batching PyTorch con bucketing y prueba de paridad.
4. Matrix por categoría, solo si batching no logra el throughput requerido.
5. ONNX y/o precisión reducida como benchmarks opcionales, cada uno con su propio resultado A/B.
6. Evaluación completa final una vez cerrada la tanda de optimizaciones.

## Advertencias sobre las estimaciones aportadas

- 1.400/12.032 equivale a ~11,6% del número de preguntas, no a una garantía de 8,6× en tiempo: longitud de prompts, padding, descarga y setup alteran la escala.
- Un muestreo de 100 por categoría no implica por sí mismo ±2,6 puntos porcentuales para el estimador global, especialmente con pesos desiguales y heterogeneidad entre categorías.
- El speedup de batching, paralelismo y ONNX es hardware/modelo/runtime dependiente. Los rangos propuestos se tratan como hipótesis que deben verificarse, no como promesas.
- El holdout público completo sigue siendo útil como auditoría externa, pero no es secreto. Para evitar adaptación indirecta, se usa solo al final de una tanda y nunca para selección iterativa.
