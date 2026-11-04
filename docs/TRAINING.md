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


## Ciclo sintético recurrente con warm-start

El workflow `synthetic-training-cycles.yml` puede ejecutarse manualmente, al modificar el pipeline en `main` y cada seis horas. La primera semilla de cada ciclo recupera los últimos pesos sintéticos aceptados desde la caché de Actions; las demás semillas siguen siendo controles independientes desde inicialización reproducible.

La promoción del warm-start exige simultáneamente:
- menor bits-per-byte en la validación sintética fija;
- exactitud no inferior en el piloto multidominio de 23 preguntas.

Si cualquiera de las dos condiciones falla, no se guarda el checkpoint nuevo y la siguiente iteración conserva el último estado aceptado. El optimizador se reinicia entre ciclos; solo se transfieren los pesos. Esto es un experimento de currículo sintético y continuidad técnica, no aprendizaje de conocimiento externo ni una evaluación de razonamiento general. La caché de Actions es almacenamiento experimental, no un release del modelo.


## Ciclos rápidos con corpus abierto y promoción por validación

El workflow `rapid-open-training-cycles.yml` ejecuta hasta tres ciclos cortos consecutivos y, cuando una ejecución termina correctamente, GitHub Actions dispara automáticamente la siguiente mediante `workflow_run`. No requiere activación manual entre ciclos. Un `cron` cada seis horas sirve solo como arranque/recuperación si la cadena se detiene. Usa el corpus público fijado por `prepare_open_corpora.py`, con partición por obra; conserva el último checkpoint aceptado y hace warm-start del siguiente ciclo.

**Gate obligatorio:** el workflow llama a `assert_g0_passed.py` antes de descargar textos o entrenar. Si G-0 no está en PASS, la ejecución falla de forma cerrada, no descarga textos ni modifica pesos y corta la cadena; el arranque periódico vuelve a intentarlo más tarde. Una etiqueta de licencia o la disponibilidad pública no sustituyen la revisión humana.

**Regla de promoción:** solo acepta el checkpoint si mejora estrictamente la accuracy de MMLU-Pro `validation` y no empeora bits-per-byte en el split de validación textual. Si no cumple ambas condiciones, restaura el checkpoint anterior y continúa desde él. El test de MMLU-Pro permanece fuera de este bucle y se reserva para evaluación final no usada en selección.

La referencia operativa del último modelo aceptado por estos ciclos es la caché `ronin-open-warmstart` de GitHub Actions; no es todavía un release descargable ni una referencia inmutable a largo plazo. Cada ejecución publica el informe de ciclos, hashes, split y checkpoint. La promoción a versión pública exige después el test completo y actualización explícita del model card/README.

La validación recurrente puede sobreajustarse con el tiempo; por ello, una subida en validation no se presenta como mejora general ni como aprobación de release. El test final intacto sigue siendo la barrera de publicación.
