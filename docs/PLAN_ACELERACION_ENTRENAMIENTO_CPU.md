# Plan de aceleración del entrenamiento CPU RONIN

Actualizado: 4 de noviembre de 2026. No se declara ningún speedup hasta medirlo en el mismo runner.

## Estado actual verificado

- Entrenamiento PyTorch CPU, perfil tiny de aproximadamente 9,9M parámetros.
- Corpus UTF-8 codificado con ByteTokenizer y cargado completo en memoria; no hay DataLoader ni cuello de botella de workers.
- Muestreador NextTokenBatches ya vectorizado.
- Atención usa scaled_dot_product_attention causal.
- GQA expande K/V con repeat_interleave antes de SDPA.
- RoPE calcula posiciones, frecuencias, cosenos y senos dentro de cada llamada; se ejecuta para Q y K en cada bloque. Repite trabajo determinista en todas las capas.
- Proyección Q, K y V usa tres Linear separados; SwiGLU usa tres Linear separados.
- Cross entropy materializa logits para todos los tokens del batch.
- AdamW se ejecuta cada paso; clipping global de gradiente también.
- Ya se registran latencia/step, p50/p95, tokens/s, tiempo de checkpoint e hilos efectivos.

## Prioridad de optimizaciones con mejor relación impacto/riesgo

### P0 — Benchmark reproducible

Crear microbenchmark en el mismo runner con warm-up y 3-5 repeticiones, perfil tiny, mismo seed, corpus hash, batch, contexto y pasos. Comparar mediana de tokens/s, pérdida final, memoria y predicciones. Probar hilos 1, 2 y 4 (y más solo si el runner tiene cores efectivos). Guardar torch.__config__, CPU flags, versión PyTorch, OMP/MKL y tiempo por fase.

### P1 — Evitar trabajo repetido en RoPE

Precalcular cos/sin para el contexto y compartirlos entre capas; no recalcularlos por separado para Q y K. Cachear por (device, dtype, length, head_dim, theta), sin gradiente. Mantener prueba de equivalencia numérica contra la implementación actual. Es el candidato de código más claro porque hoy el cálculo trigonométrico se repite en cada capa y batch.

### P2 — Fusionar proyecciones lineales

Sustituir q_proj/k_proj/v_proj por una proyección conjunta con partición de salidas; fusionar gate_proj y up_proj de SwiGLU en una sola Linear de 2*d_ff. Mantener el mapeo de pesos y una prueba de equivalencia de forward/gradientes. Puede reducir llamadas a BLAS y overhead Python, especialmente en modelos pequeños; no prometer un porcentaje antes del A/B.

### P3 — Eliminar expansión GQA si el backend lo soporta

Probar SDPA con enable_gqa=True en la versión exacta de PyTorch CPU del runner. Comparar con repeat_interleave: misma salida dentro de tolerancia, sin fallback lento y mejora real. Si no está soportado o no es rápido en CPU, conservar el camino actual.

### P4 — AdamW y gradientes

Medir AdamW foreach=True frente al default; probar fused solo si el backend CPU de la versión lo soporta. Comparar clip_grad_norm_ con implementación equivalente y evitar sincronizaciones innecesarias. No eliminar clipping ni cambiar optimizer sin experimento de calidad separado.

### P5 — torch.compile como experimento aislado

Probar torch.compile(model, backend="inductor") en CPU tras warm-up; separar compilación del tiempo de entrenamiento y amortizarla en suficientes pasos. En 1.000 pasos puede que el coste inicial no compense. No activarlo por defecto sin speedup neto y paridad.

### P6 — BF16 CPU solo si hardware lo soporta

Detectar AVX512-BF16/AMX o soporte real del backend. Ejecutar autocast CPU BF16 como experimento separado, vigilar NaN/Inf y medir delta de loss/benchmark. No asumir que BF16 CPU es más rápido: depende de la CPU de Actions. FP32 seguirá siendo referencia.

## Cambios de sistema que pueden ahorrar más tiempo de pared

- Separar preparación del corpus y entrenamiento. Preparar shards/índices una vez, con cache key por revisión, configuración de filtros y hashes; no descargar, normalizar y tokenizar en cada repetición.
- Pre-tokenizar a shards compactos (uint8 para ByteTokenizer) y mapearlos desde disco; el tokenizador de bytes no necesita una tabla de vocabulario. Medir RAM y tiempo de carga frente a memoria mapeada.
- Ejecutar tests y microbenchmarks en PR; reservar entrenamiento completo y MMLU-Pro completo para después del gate de datos.
- Evaluación: el plan existente detecta 12.032 forwards secuenciales; batching por longitud y cache exacta de predicciones puede reducir mucho la evaluación, pero no acelera el entrenamiento.
- Gradient accumulation mantiene memoria baja, pero puede añadir overhead; no es aceleración gratuita.
- No usar más procesos de Actions por defecto: puede bajar wall-clock a costa de multiplicar minutos y descargas. Medir coste total.

## Orden de ejecución propuesto

1. Registrar baseline del runner con 1/2/4 hilos y 100 pasos.
2. Implementar cache de RoPE y medir.
3. Fusionar QKV y gate/up, con pruebas de paridad.
4. Probar GQA nativo en SDPA.
5. Medir AdamW foreach.
6. Probar compile y BF16 CPU de forma independiente.
7. Elegir solo cambios con mejora de tokens/s y sin regresión de loss/calidad.
8. Repetir la auditoría de rendimiento con el corpus de ocho bibliotecas y el presupuesto de tokens definitivo.

El objetivo es reducir tiempo por paso y tiempo de preparación, no simplemente reducir pasos o evaluar menos. Ninguna optimización se considera válida si altera el protocolo o empeora la capacidad medida.

## Perfilado real del RUN #4 (4 de noviembre de 2026)

Se inspeccionó el log del job 126652067687, ejecución 41852455682. El job completo duró aproximadamente 46 min 51 s:

| Fase | Duración observada | Peso del total |
|---|---:|---:|
| Evaluación inicial MMLU-Pro (12.032 preguntas seleccionadas) | 22 min 07 s | 47,2 % |
| Entrenamiento (1.000 pasos) | 2 min 26 s | 5,2 % |
| Evaluación final MMLU-Pro | 20 min 45 s | 44,3 % |
| Preparación, dependencias y consolidación | ~1 min 33 s | 3,3 % |

Las dos evaluaciones consumieron aproximadamente **42 min 52 s (91,5 % del wall-clock)**. El entrenamiento real consumió alrededor del 5,2 %. Por tanto, la mejora más dramática del tiempo total no vendrá primero de optimizar AdamW o el Transformer: vendrá de acelerar la evaluación, que hoy hace un forward por pregunta y se ejecuta dos veces.

### Prioridad corregida

1. **P0 evaluación batched**: implementar batching con bucketing por longitud y padding/attention mask correcto, primero con un subset fijo y equivalencia de logits/predicciones. El test completo sigue siendo la auditoría final, no se elimina.
2. **P1 evitar repetir evaluación completa en cada experimento**: durante iteración usar un subset estratificado congelado; ejecutar full MMLU-Pro al cerrar una tanda. No usar full test para seleccionar hiperparámetros ni reportar el subset como resultado completo.
3. **P2 entrenamiento**: cache RoPE y fusionar QKV/SwiGLU; medir hilos 1/2/4.
4. **P3**: GQA nativo, AdamW foreach, torch.compile y BF16 CPU como A/B independientes.

El resultado de este perfilado cambia la prioridad: el pipeline actual no tarda 47 minutos en aprender; tarda unos 2,5 minutos en entrenar y más de 42 minutos en evaluar dos veces. Reducir evaluación puede recortar radicalmente el tiempo de pared sin cambiar el número de pasos ni la cantidad de datos entrenados.



## P0 implementado: evaluación MMLU-Pro por lotes (4 de noviembre de 2026)

Se implementó en `scripts/evaluate_mmlu_pro.py` un camino de inferencia por lotes con estas garantías:

- Ordenación temporal por longitud de prompt para reducir padding.
- Padding exclusivamente a la derecha. Como el modelo usa atención causal, las posiciones añadidas después del prompt no pueden influir en el logit de su último byte real.
- Extracción del logit en `length - 1` por elemento, no del último índice padded.
- Presupuesto configurable de tokens padded por lote (`--batch-token-budget`, valor inicial 8192); el límite se puede ajustar en el workflow oficial entre 512 y 32768.
- Los resultados vuelven al orden original del dataset; se conservan IDs, cobertura, preguntas omitidas, desglose por dominio y protocolo.
- El test compara la ruta por lotes con la ruta secuencial, incluyendo predicciones, exactitud y log-probabilidades dentro de tolerancia.

Se añade `scripts/benchmark_mmlu_evaluator.py` y el workflow `.github/workflows/mmlu-evaluator-performance.yml`. En cada actualización relevante de PR ejecuta una comparación secuencial (presupuesto 1) frente a lotes (8192), sobre los mismos 140 ítems estratificados y el mismo checkpoint aleatorio. Publica tiempos, speedup, paridad y cobertura como artefacto. Este microbenchmark mide solo el coste del evaluador; no mide inteligencia ni constituye entrenamiento.

**Estado inicial:** optimización implementada; speedup todavía no declarado hasta que termine el workflow en Actions. El entrenamiento oficial reutilizará el presupuesto configurable en sus evaluaciones inicial y final, pero sigue bloqueado por el gate de 16 bibliotecas.
