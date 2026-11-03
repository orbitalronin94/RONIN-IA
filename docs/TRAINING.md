# Operaciones de entrenamiento

El entrenador es compartido por todos los perfiles. La configuración cambia las dimensiones del modelo y los recursos; no debe seleccionar una implementación de entrenamiento diferente.

## Comportamiento inicial implementado

- Optimizador AdamW.
- Calentamiento lineal seguido de una reducción coseno hasta la tasa de aprendizaje mínima configurada.
- Acumulación de gradientes y recorte global.
- Selección de precisión en tiempo de ejecución: BF16 en CUDA compatible, en otro caso FP16 en CUDA y FP32 en CPU. Las solicitudes explícitas de una precisión no compatible deben fallar claramente.
- Detección de pérdidas y normas de gradiente no finitas.
- Escritura atómica y periódica de checkpoints que contienen modelo, optimizador, escalador, paso, estados aleatorios de Python/NumPy/CPU/CUDA y estado del generador del muestreador de siguiente token.
- Reanudación desde checkpoint con igualdad estricta de configuración de entrenamiento; la tasa de aprendizaje se reconstruye a partir del paso global.

La reanudación actual admite el muestreador determinista de lotes de siguiente token. Un futuro cargador de datos en streaming o distribuido deberá proporcionar un cursor/estado serializable antes de poder afirmar que la reanudación es exacta.

## Próximos pasos obligatorios

- Añadir bucle de validación y selección del mejor checkpoint.
- Añadir telemetría de desbordamientos y pasos omitidos del GradScaler.
- Añadir checkpointing de activaciones y estrategias distribuidas de datos/modelo.
- Añadir detección de picos de pérdida, diagnóstico y recuperación acotada. Nunca revertir pesos en silencio sin registrar el evento.
- Añadir parada temprana solo a experimentos de datos finitos configurados expresamente; no debe detener de forma silenciosa ejecuciones largas de preentrenamiento.
- Añadir rotación de checkpoints, protección de espacio en disco y cierre seguro ante señales.
- Registrar tokens vistos, tokens por segundo, pasos del optimizador, lote efectivo, norma de gradiente, tasa de aprendizaje, precisión y hardware.
- Guardar la configuración resuelta exacta y las huellas de datos/tokenizador en cada ejecución.

## Seguridad operativa

Los cálculos de adecuación al hardware y coste se etiquetan como estimaciones hasta que se contrasten con benchmarks en el equipo de destino. Incluir parámetros, gradientes, estados del optimizador, activaciones, búferes temporales de atención, fragmentación y comunicación distribuida. Una estimación simple basada solo en parámetros no garantiza que el modelo quepa.
