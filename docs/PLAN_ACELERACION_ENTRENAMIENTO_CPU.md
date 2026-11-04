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
